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
    schutzherkunft.py EEA SEBI 007, Abbildung 2 — ZIP mit .xlsx (API)
    vogel.py         Farmland Bird Index 1998–2025 (gepflegt) + EU-Reihe (API)
    boden.py         ÖROK-Flächeninanspruchnahme und Versiegelung (gepflegt)
    baulandreserven.py  Landnutzung der Baulandreserven je Gemeinde (API)
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
import json
from pathlib import Path

import config
from gemeinsam import QUELLEN, WARNUNGEN, log, schreibe, warnen

from schutzgebiete import baue_schutzgebiete
from schutzherkunft import baue_schutzherkunft
from vogel import baue_vogel
from boden import baue_boden
from rotelisten import baue_rotelisten
from erhaltung import baue_erhaltung
from lebensraeume import baue_lebensraeume
from biotoptypen import baue_biotoptypen
from wald import baue_wald
from biolandbau import baue_biolandbau
from falter import baue_falter
from rueckkehrer import baue_rueckkehrer
from vogelarten import baue_vogelarten
from baumarten import baue_baumarten
from waldarten import baue_waldarten
from natura2000 import baue_natura2000
from fliessgewaesser import baue_fliessgewaesser
from querbauwerke import baue_querbauwerke

# WIEDER AUFGENOMMEN 31.08.2026 — `baumarten`, `waldarten` und `natura2000`
# sind am 30.08. committet und live gegangen, ihre Importe und Aufrufe waren
# aber ausgeklinkt geblieben. Folge, am selben Tag an der ausgelieferten
# `data/meta.json` nachgemessen: Die Pipeline hat die drei Abschnitte nicht
# mehr gebaut, ihre Datendateien lagen eingefroren im Repo — und weil
# `quelle_vermerken()` nie lief, führte der Quellenblock im Fuß der Seite
# 13 Quellen statt 16. Für den Waldbiodiversitätsbericht ist die
# Quellenangabe die BEDINGUNG, unter der der Abdruck erlaubt ist.
#
# AUSGEKLINKT BLEIBEN vier Module, die tatsächlich nicht im Repo liegen —
# ein Import einer fehlenden Datei bricht die Pipeline in GitHub Actions mit
# ImportError ab, bevor eine einzige Zahl gerechnet wird:
#
# from totholz import baue_totholz            # wartet auf BFW-Freigabe
# from fichte import baue_fichte              # wartet auf BFW-Freigabe
# from baulandreserven import baue_baulandreserven
# from gemeindegrenzen import baue_gemeindegrenzen


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

    # `schutzherkunft` zerlegt genau die Zahl, die `schutzgebiete` als Summe
    # zeigt. Die beiden kommen von verschiedenen Stellen — Eurostat sdg_15_20
    # dort, das EEA-Datenpaket hier — und müssen trotzdem dasselbe sagen.
    schutzherkunft = baue_schutzherkunft()
    if schutzherkunft:
        ausgaben["schutzherkunft"] = schutzherkunft

        # Gegenprobe über zwei Module und zwei Herausgeber hinweg. Toleranz
        # 0,2 Punkte: beide runden auf eine Nachkommastelle, und die Stichjahre
        # können um einen Jahrgang auseinanderliegen. Weicht es weiter ab,
        # widersprechen sich zwei Abschnitte, die direkt untereinander stehen.
        if schutzgebiete:
            at = schutzherkunft["balken"][0]["gesamt"]
            if abs(at - schutzgebiete["aktuell"]) > 0.2:
                warnen(
                    f"Schutzgebiete und Schutzherkunft uneins: Eurostat meldet "
                    f"{schutzgebiete['aktuell']:.1f} % für {schutzgebiete['stand']}, "
                    f"die EEA {at:.1f} % für {schutzherkunft['stichjahr']}."
                )

    ausgaben["vogel"] = baue_vogel()
    ausgaben["boden"] = baue_boden()

    rote = baue_rotelisten()
    if rote:
        ausgaben["rotelisten"] = rote

    ausgaben["erhaltung"] = baue_erhaltung()
    # Dieselbe Meldung, nach Lebensraumgruppen aufgeschlüsselt. Steht
    # unmittelbar hinter `erhaltung`, weil sie dessen Durchschnitt auflöst:
    # 22,8 % günstig ist ein Mittelwert über Gruppen, die zwischen 0 und
    # 75 % liegen.
    ausgaben["lebensraeume"] = baue_lebensraeume()
    ausgaben["biotoptypen"] = baue_biotoptypen()

    wald = baue_wald()
    if wald:
        ausgaben["wald"] = wald

    bio = baue_biolandbau()
    if bio:
        ausgaben["biolandbau"] = bio

    # --- Gegenprobe über die Artikel-17-Abschnitte -------------------------
    # `erhaltung` zählt die Lebensraumtypen als Ganzes, `lebensraeume`
    # gliedert dieselbe Meldung nach Gruppen. Wird einer nachgezogen und der
    # andere nicht, stehen zwei Berichtsstände nebeneinander.
    # Die drei Wald-Abschnitte, seit 31.08.2026 wieder in der Pipeline.
    # Reihenfolge wie im Frontend: Baumarten, Waldarten, Waldzustand.
    ausgaben["baumarten"] = baue_baumarten()
    ausgaben["waldarten"] = baue_waldarten()
    ausgaben["natura2000"] = baue_natura2000()

    fliessgewaesser = baue_fliessgewaesser()
    if fliessgewaesser:
        ausgaben["fliessgewaesser"] = fliessgewaesser

    # `querbauwerke` teilt den Nenner mit `fliessgewaesser`: dort die 4.031
    # Wasserkörper, die das Ziel verfehlen, hier die Gründe dafür. Fällt der
    # eine aus, ist der andere nicht falsch, aber unbelegt — beide holen ihn
    # deshalb selbst aus derselben Tabelle, statt ihn sich zu reichen.
    querbauwerke = baue_querbauwerke()
    if querbauwerke:
        ausgaben["querbauwerke"] = querbauwerke

        # Gegenprobe über zwei Module hinweg: `fliessgewaesser` zählt die
        # Wasserkörper, die das Ziel ERREICHEN, `querbauwerke` die, die es
        # verfehlen. Zusammen mit den unbewerteten müssen sie den Bestand
        # ergeben. Beide zählen unabhängig aus — das ist mehr wert als ein
        # fester Sollwert, der nur die Abschrift prüft.
        if fliessgewaesser:
            gut = fliessgewaesser["nach_anzahl"]["zahlen"]
            unbekannt = gut[-1]          # letzte Kategorie ist „unbekannt"
            erreichend = gut[0] + gut[1]
            summe = erreichend + querbauwerke["verfehlend"] + unbekannt
            if summe != fliessgewaesser["nach_anzahl"]["gesamt"]:
                warnen(
                    f"Fließgewässer und Querbauwerke uneins: "
                    f"{erreichend} erreichend + "
                    f"{querbauwerke['verfehlend']} verfehlend + "
                    f"{unbekannt} unbewertet = {summe}, der Bestand ist "
                    f"{fliessgewaesser['nach_anzahl']['gesamt']}."
                )

    perioden = {name: ausgaben[name]["periode"]
                for name in ("erhaltung", "lebensraeume", "natura2000")}
    if len(set(perioden.values())) > 1:
        warnen(
            "Artikel-17-Abschnitte uneins: "
            + ", ".join(f"`{n}` auf {p}" for n, p in perioden.items())
        )

    # Dieselbe Meldung, zwei Module: `lebensraeume` gliedert die Artikel-17-
    # Bewertungen nach Gruppen, `natura2000` zählt die Gruppe Forests noch
    # einmal für sich aus. Beide müssen auf dieselben 32 Bewertungen kommen.
    # Der Vergleich stand am 28.08.2026 auf 28,1 gegen 28,1.
    wald_lr = ausgaben["lebensraeume"]["wald_guenstig"]
    wald_n2k = ausgaben["natura2000"]["nach_bewertung"]["guenstig_prozent"]
    if abs(wald_lr - wald_n2k) > 0.05:
        warnen(
            f"Waldwerte uneins: `lebensraeume` nennt {wald_lr} % günstig, "
            f"`natura2000` {wald_n2k} % — beide zählen dieselbe Gruppe "
            f"Forests aus, einer der beiden zählt anders als gedacht."
        )

    # AUSGEKLINKT 29.08.2026 — alles Folgende hängt an Modulen, die im Ordner
    # liegen, aber nicht im Repo sind; in GitHub Actions bräche die Pipeline
    # daran ab. Wieder aufnehmen, sobald `totholz.py`, `fichte.py`,
    # `baulandreserven.py` und `gemeindegrenzen.py` committet sind —
    # zusammen mit ihren Importen oben.
    #
    #   bezirke_geo = None
    #   bezirke_pfad = (Path(__file__).resolve().parent.parent.parent
    #                   / "arbeitsmarkt-at" / "docs" / "data" / "karte_geo.json")
    #   if bezirke_pfad.exists():
    #       with bezirke_pfad.open(encoding="utf-8") as datei:
    #           bezirke_geo = json.load(datei)
    #   else:
    #       warnen(f"Bezirksgeometrie nicht gefunden ({bezirke_pfad}) — die "
    #              f"Totholzkarte entfällt, die Tabelle bleibt.")
    #
    #   totholz, totholz_geo = baue_totholz(bezirke_geo)
    #   if totholz:     ausgaben["totholz"] = totholz
    #   if totholz_geo: ausgaben["totholz_geo"] = totholz_geo
    #   ausgaben["fichte"]     = baue_fichte()
    #
    # `baumarten`, `waldarten` und `natura2000` standen bis 31.08.2026 hier
    # und laufen jetzt oben mit den übrigen Abschnitten.
    #
    #   wald_staende = {name: ausgaben[name]["stand"]
    #                   for name in ("totholz", "fichte", "baumarten")
    #                   if ausgaben.get(name)}
    #   if len(set(wald_staende.values())) > 1:
    #       warnen("Waldabschnitte uneins: " + ", ".join(
    #           f"`{n}` auf {s}" for n, s in wald_staende.items()))
    #
    #   ausgaben["baulandreserven"] = baue_baulandreserven(
    #       (ausgaben.get("boden") or {}).get("aktuell_ha_pro_tag"))
    #   if ausgaben.get("baulandreserven") and ausgaben.get("boden"):
    #       bestand_ha = round(ausgaben["boden"]["bestand_km2"] * 100)
    #       if abs(bestand_ha - config.BLR_FI_BESTAND_HA) > 1_000:
    #           warnen(f"Bodenabschnitte uneins: `boden` nennt {bestand_ha:,} ha "
    #                  f"…, config.BLR_FI_BESTAND_HA steht auf "
    #                  f"{config.BLR_FI_BESTAND_HA:,} ha.")
    #   if ausgaben.get("baulandreserven"):
    #       baue_gemeindegrenzen(
    #           {g["gkz"] for g in ausgaben["baulandreserven"]["gemeinden"]})

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
