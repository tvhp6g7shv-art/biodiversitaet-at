#!/usr/bin/env python3
"""
Datenpipeline für das Biodiversitäts-Dashboard Österreich — Orchestrator.

Was die Pipeline tut:
  1. Holt fünf Reihen frisch von der Eurostat-API
  2. Legt die gepflegten Reihen bei und prüft ihren Pflegestand
  3. Schreibt alles als kleine JSON-Dateien nach docs/data/

Aufruf:  python etl/build.py

Module:
    gemeinsam.py     Logging, Download, JSON-stat-Auswertung, Pflegeprüfung
    schutzgebiete.py Eurostat sdg_15_20 (API)
    vogel.py         Farmland Bird Index 1998–2025 (gepflegt) + EU-Reihe (API)
    boden.py         ÖROK-Flächeninanspruchnahme und Versiegelung (gepflegt)
    rotelisten.py    Stand der Aktualisierung der Roten Listen (gepflegt)
    erhaltung.py     Erhaltungszustand nach Artikel 17 FFH (gepflegt)
    biotoptypen.py   Rote Liste der Biotoptypen (gepflegt)
    wald.py          Waldfläche AT und Nachbarn, Eurostat for_area (API)
    biolandbau.py    Bio-Anteil im Ländervergleich, Eurostat sdg_02_40 (API)
    falter.py        Grünland-Schmetterlingsindex, Eurostat sdg_15_61 (API)
    rueckkehrer.py   Biber und Fischotter, Artikel-17-Spannen (gepflegt)
    vogelarten.py    Feld- und Wiesenvögel Art für Art (gepflegt)

Die drei zuletzt genannten bilden zusammen den Bereich Tiergruppen und
sind bewusst als Gegensatz gebaut — Verlust, Erholung, Stillstand. Sie
sollen zeigen, dass Rückgang kein Naturgesetz ist.

Österreich ist keine Insel: Fünf Abschnitte stellen die nationalen Zahlen
in einen europäischen Zusammenhang — die Vogelreihe gegen das EU-Aggregat,
Waldfläche und Bio-Anteil gegen die acht Nachbarn, und der
Erhaltungszustand ist ohnehin nach den grenzüberschreitenden
biogeografischen Regionen gegliedert. Der Falterindex ist der einzige
Abschnitt, der **gar keine** österreichische Zahl zeigt: Eurostat führt
für ihn nur das EU-Aggregat. Das steht in seiner Hinweiszeile und darf
dort nicht verschwinden.

Die Pipeline ist absichtlich gesprächig: sie schreibt mit, was sie tut, und
sammelt alle Auffälligkeiten in docs/data/meta.json unter "warnungen".

Zum Unterschied gegenüber der Schwesterpipeline arbeitsmarkt-at: Dort bricht
der Lauf ab, wenn eine Quelle ihr Format ändert. Hier kann nur die
Eurostat-Abfrage überhaupt scheitern — die übrigen Reihen stehen im Code.
Deren Risiko ist nicht der Formatbruch, sondern das stille Altern. Dagegen
läuft `pflegepruefung()`: sie meldet, wenn eine Reihe ihren erwarteten
Erscheinungsrhythmus überschreitet.
"""

from __future__ import annotations

import datetime as dt

import config
from gemeinsam import QUELLEN, WARNUNGEN, log, schreibe, warnen

from schutzgebiete import baue_schutzgebiete
from vogel import baue_vogel
from boden import baue_boden
from rotelisten import baue_rotelisten
from erhaltung import baue_erhaltung
from biotoptypen import baue_biotoptypen
from wald import baue_wald
from biolandbau import baue_biolandbau
from falter import baue_falter
from rueckkehrer import baue_rueckkehrer
from vogelarten import baue_vogelarten


def _vogel_abgleichen(vogel: dict, vogelarten: dict) -> None:
    """
    Prüft, ob die beiden Vogelabschnitte denselben Bericht abbilden.

    WARUM ES DIESE PRÜFUNG GIBT: Am 26.08.2026 stand `vogelarten` auf dem
    Bericht von Juni 2024, während zwei neuere erschienen waren. Die
    modulinterne Gegenprobe hat das nicht gemerkt — sie vergleicht gegen
    einen Sollwert aus derselben Ausgabe wie die Daten und prüft damit
    die Abschrift, nicht die Aktualität. Ein Abgleich ÜBER die Abschnitte
    hinweg merkt es: sobald einer gehoben wird und der andere nicht,
    laufen Verteilung oder Artenliste auseinander.
    """
    trend_index = {k: v for k, v in vogel["trend"].items() if k != "bewertet"}
    trend_arten = vogelarten["zaehlung"]
    if trend_index != trend_arten:
        warnen(
            f"Vogelabschnitte uneins: `vogel` nennt {trend_index}, "
            f"`vogelarten` {trend_arten} — vermutlich wurde nur einer der "
            f"beiden auf einen neuen Bericht gehoben."
        )

    namen_a = sorted(vogel["arten"])
    namen_b = sorted(eintrag["name"] for eintrag in
                     vogelarten["arten"] + vogelarten["spaete_arten"])
    if namen_a != namen_b:
        fehlt = sorted(set(namen_a) ^ set(namen_b))
        warnen(f"Vogelabschnitte uneins: Artenlisten weichen ab bei {fehlt}.")

    if vogel["stand"] != vogelarten["stand"]:
        warnen(
            f"Vogelabschnitte uneins: `vogel` steht auf {vogel['stand']}, "
            f"`vogelarten` auf {vogelarten['stand']}."
        )


def main() -> None:
    start = dt.datetime.now(dt.timezone.utc)
    log("=" * 70)
    log("Biodiversitäts-Dashboard Österreich — Datenaktualisierung")
    log(f"Start: {start:%Y-%m-%d %H:%M} UTC")
    log("=" * 70)

    ausgaben: dict[str, dict] = {}

    schutzgebiete = baue_schutzgebiete()
    if schutzgebiete:
        ausgaben["schutzgebiete"] = schutzgebiete

    ausgaben["vogel"] = baue_vogel()
    ausgaben["boden"] = baue_boden()

    rote = baue_rotelisten()
    if rote:
        ausgaben["rotelisten"] = rote

    ausgaben["erhaltung"] = baue_erhaltung()
    ausgaben["biotoptypen"] = baue_biotoptypen()

    wald = baue_wald()
    if wald:
        ausgaben["wald"] = wald

    bio = baue_biolandbau()
    if bio:
        ausgaben["biolandbau"] = bio

    # --- Tiergruppen: Verlust, Erholung, Stillstand ------------------------
    # `falter` holt seine Reihe von Eurostat und fällt bei einem Ausfall auf
    # eine abgeschriebene Notreihe zurück, statt zu verschwinden — der
    # Abschnitt meldet das dann selbst laut. Deshalb steht er hier ohne
    # `if`, anders als die übrigen API-Abschnitte.
    ausgaben["falter"] = baue_falter()
    ausgaben["rueckkehrer"] = baue_rueckkehrer()
    ausgaben["vogelarten"] = baue_vogelarten()

    # Gegenprobe über zwei Abschnitte hinweg: `vogel` und `vogelarten`
    # stammen aus derselben Erhebung und müssen dieselbe Verteilung und
    # dieselben Arten nennen. Laufen sie auseinander, wurde einer der
    # beiden auf einen neuen Bericht gehoben und der andere nicht — genau
    # der Fehler, der am 26.08.2026 aufgefallen ist.
    _vogel_abgleichen(ausgaben["vogel"], ausgaben["vogelarten"])

    # --- Kennzahlen für den Kopf des Dashboards ----------------------------
    # Vier Zahlen, jede aus einem anderen Abschnitt. Bewusst KEINE
    # Gesamtnote: es gibt keinen sinnvollen Index, der Schutzgebietsfläche,
    # Vogelbestand, Bodenverbrauch und Datenlage zu einer Zahl verrechnet.
    kpi: dict = {"stand": start.strftime("%Y-%m-%d")}
    if schutzgebiete:
        kpi["schutzgebiete_prozent"] = schutzgebiete["aktuell"]
        kpi["schutzgebiete_jahr"] = schutzgebiete["stand"]
        kpi["schutzgebiete_luecke"] = schutzgebiete["luecke"]
    kpi["vogel_index"] = ausgaben["vogel"]["aktuell"]
    kpi["vogel_jahr"] = ausgaben["vogel"]["stand"]
    # Die Kachel zeigt seit 25.08.2026 den Verlust, nicht den Indexstand:
    # „56,8" ist ohne die Basiszeile nicht lesbar, „−43 %" ist es.
    kpi["vogel_verlust"] = ausgaben["vogel"]["verlust"]
    kpi["vogel_beginn"] = ausgaben["vogel"]["beginn"]
    kpi["vogel_arten"] = ausgaben["vogel"]["arten_anzahl"]
    kpi["boden_ha_pro_tag"] = ausgaben["boden"]["aktuell_ha_pro_tag"]
    kpi["boden_periode"] = ausgaben["boden"]["aktuell_periode"]
    if rote:
        kpi["rotelisten_aktuell"] = rote["aktuell"]
        kpi["rotelisten_gesamt"] = rote["gruppen_gesamt"]
        # Wie alt die übrigen sind. Ohne diese Spanne sagt „3 von 27" nicht,
        # woran „aktuell" gemessen ist — der Rückstand kann ein Jahr oder
        # drei Jahrzehnte betragen. Gruppen ohne Liste haben kein Alter und
        # werden getrennt gezählt, nicht als 0 eingerechnet.
        alter = [e["alter"] for e in rote["eintraege"]
                 if e["status"] != "aktuell" and e.get("alter") is not None]
        if alter:
            kpi["rotelisten_rest_min"] = min(alter)
            kpi["rotelisten_rest_max"] = max(alter)
        kpi["rotelisten_ohne"] = rote["ohne_liste"]
    kpi["erhaltung_guenstig"] = ausgaben["erhaltung"]["gruppen"][0]["guenstig"]
    kpi["erhaltung_periode"] = ausgaben["erhaltung"]["periode"]
    kpi["biotoptypen_anteil"] = ausgaben["biotoptypen"]["anteil_gefaehrdet"]
    kpi["biotoptypen_bewertet"] = ausgaben["biotoptypen"]["bewertet"]
    if bio:
        kpi["bio_anteil"] = bio["oesterreich"]["wert"]
        kpi["bio_rang"] = bio["rang"]
        kpi["bio_anzahl"] = bio["anzahl"]
        kpi["bio_jahr"] = bio["vergleichsjahr"]
    if wald and wald["oesterreich"]:
        kpi["wald_veraenderung"] = wald["oesterreich"]["veraenderung"]
        kpi["wald_von"] = wald["von"]
        kpi["wald_bis"] = wald["bis"]
    ausgaben["kpi"] = kpi

    # --- Schreiben ---------------------------------------------------------
    log("\nSchreiben")
    for name, inhalt in ausgaben.items():
        schreibe(name, inhalt)

    schreibe("meta", {
        "generiert_am": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "stand_daten": kpi["stand"],
        "quellen": QUELLEN,
        "hinweis_beschaffung": (
            "Fünf Reihen kommen bei jedem Lauf frisch von der Eurostat-API "
            "(Schutzgebiete, EU-Vogelindex, Waldfläche, Bio-Anteil, "
            "Falterindex). Die übrigen sind aus Publikationen abgeschrieben "
            "und tragen ihren Stand im Feld \"pflege\" — Österreich "
            "veröffentlicht seine Biodiversitätsdaten überwiegend als PDF "
            "ohne Datenanhang."
        ),
        "hinweis_definitionen": (
            "Die Abschnitte messen Verschiedenes und lassen sich nicht "
            "gegeneinander aufrechnen: Fläche unter Schutz, Häufigkeit von "
            "Vogelbeständen, neu beanspruchter Boden, das Alter des "
            "Fachwissens, der Erhaltungszustand von Lebensräumen, die "
            "Gefährdung von Biotoptypen, Waldfläche, Bio-Anteil, Falter auf "
            "festen Strecken und hochgerechnete Bestände zweier Säugetiere."
        ),
        "hinweis_europa": (
            "Österreich ist keine Insel: Vogelindex, Waldfläche und "
            "Bio-Anteil stehen im europäischen Vergleich, und der "
            "Erhaltungszustand ist nach den grenzüberschreitenden "
            "biogeografischen Regionen alpin und kontinental gegliedert. "
            "Der Falterindex zeigt als einziger Abschnitt ausschließlich "
            "europäische Zahlen — eine österreichische Reihe ab 1991 gibt "
            "es nicht."
        ),
        "einbettung": config.EINBETTUNG,
        "warnungen": WARNUNGEN,
    })

    dauer = (dt.datetime.now(dt.timezone.utc) - start).total_seconds()
    log("\n" + "=" * 70)
    if WARNUNGEN:
        log(f"Fertig in {dauer:.0f}s — mit {len(WARNUNGEN)} Hinweis(en):")
        for eintrag in WARNUNGEN:
            log(f"  · {eintrag}")
    else:
        log(f"Fertig in {dauer:.0f}s — keine Auffälligkeiten.")
    log("=" * 70)


if __name__ == "__main__":
    main()
