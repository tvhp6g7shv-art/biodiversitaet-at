#!/usr/bin/env python3
"""
Datenpipeline für das Biodiversitäts-Dashboard Österreich — Orchestrator.

Was die Pipeline tut:
  1. Holt die Schutzgebietsreihe frisch von der Eurostat-API
  2. Legt die drei gepflegten Reihen bei und prüft ihren Pflegestand
  3. Schreibt alles als kleine JSON-Dateien nach docs/data/

Aufruf:  python etl/build.py

Module:
    gemeinsam.py     Logging, Download, JSON-stat-Auswertung, Pflegeprüfung
    schutzgebiete.py Eurostat sdg_15_20 (API)
    vogel.py         Farmland Bird Index 1998–2023 (gepflegt) + EU-Reihe (API)
    boden.py         ÖROK-Flächeninanspruchnahme und Versiegelung (gepflegt)
    rotelisten.py    Stand der Aktualisierung der Roten Listen (gepflegt)
    erhaltung.py     Erhaltungszustand nach Artikel 17 FFH (gepflegt)
    biotoptypen.py   Rote Liste der Biotoptypen (gepflegt)
    wald.py          Waldfläche AT und Nachbarn, Eurostat for_area (API)
    biolandbau.py    Bio-Anteil im Ländervergleich, Eurostat sdg_02_40 (API)

Österreich ist keine Insel: Vier der acht Abschnitte stellen die
nationalen Zahlen in einen europäischen Zusammenhang — die Vogelreihe
gegen das EU-Aggregat, Waldfläche und Bio-Anteil gegen die acht Nachbarn,
und der Erhaltungszustand ist ohnehin nach den grenzüberschreitenden
biogeografischen Regionen gegliedert.

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
from gemeinsam import QUELLEN, WARNUNGEN, log, schreibe

from schutzgebiete import baue_schutzgebiete
from vogel import baue_vogel
from boden import baue_boden
from rotelisten import baue_rotelisten
from erhaltung import baue_erhaltung
from biotoptypen import baue_biotoptypen
from wald import baue_wald
from biolandbau import baue_biolandbau


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
            "Vier Reihen kommen bei jedem Lauf frisch von der Eurostat-API "
            "(Schutzgebiete, EU-Vogelindex, Waldfläche, Bio-Anteil). Die "
            "übrigen sind aus Publikationen abgeschrieben und tragen ihren "
            "Stand im Feld \"pflege\" — Österreich veröffentlicht seine "
            "Biodiversitätsdaten überwiegend als PDF ohne Datenanhang."
        ),
        "hinweis_definitionen": (
            "Die Abschnitte messen Verschiedenes und lassen sich nicht "
            "gegeneinander aufrechnen: Fläche unter Schutz, Häufigkeit von "
            "Vogelbeständen, neu beanspruchter Boden, das Alter des "
            "Fachwissens, der Erhaltungszustand von Lebensräumen, die "
            "Gefährdung von Biotoptypen, Waldfläche und Bio-Anteil."
        ),
        "hinweis_europa": (
            "Österreich ist keine Insel: Vogelindex, Waldfläche und "
            "Bio-Anteil stehen im europäischen Vergleich, und der "
            "Erhaltungszustand ist nach den grenzüberschreitenden "
            "biogeografischen Regionen alpin und kontinental gegliedert."
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
