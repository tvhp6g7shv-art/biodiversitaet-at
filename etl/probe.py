#!/usr/bin/env python3
"""
Trockenlauf der Pipeline mit gespeicherten Eurostat-Antworten.

Warum es das gibt: Die Entwicklungsumgebung kommt nicht an ec.europa.eu
heran (Proxy blockt), der GitHub-Actions-Runner schon. Ohne diesen
Trockenlauf ließe sich die Auswertungslogik lokal überhaupt nicht prüfen —
man würde jede Änderung blind pushen und im Actions-Log nachsehen.

Alle Zahlen unten sind ECHT, abgerufen am 24.08.2026. Die Fixtures sind
AUSSCHNITTE: für Waldfläche und Bio-Anteil stehen die vollständigen
österreichischen Reihen drin, für die Vergleichsländer nur die Jahre, für
die ich echte Werte geprüft habe. Wo ein Wert fehlt, fehlt er auch im
Fixture — erfunden wird nichts. Dass die Module das aushalten und die
Lücke MELDEN statt sie zu verschlucken, ist selbst Teil der Prüfung.

Die Fixtures werden aus diesen Wertetabellen programmatisch in das
JSON-stat-Format gebaut. Der Aufbau läuft über verschachtelte Schleifen in
Dimensionsreihenfolge, die Auswertung in gemeinsam.jsonstat_tabelle() über
divmod — zwei verschiedene Wege zur selben Nummerierung. Stimmen sie
überein, ist die Positionsrechnung belegt und nicht nur behauptet.

Aufruf:  python etl/probe.py
"""

from __future__ import annotations

import itertools
import sys

import gemeinsam

# --- Fixture-Baukasten ------------------------------------------------------

def baue_jsonstat(dimensionen: list[tuple[str, list[str]]],
                  werte: dict[tuple, float]) -> dict:
    """
    Baut eine JSON-stat-2.0-Antwort aus {(kat1, kat2, …): wert}.

    Die Positionsnummer entsteht hier über die Aufzählung des Kreuzprodukts
    in Dimensionsreihenfolge — bewusst anders gerechnet als im Dekoder.
    """
    ids = [name for name, _ in dimensionen]
    groessen = [len(kats) for _, kats in dimensionen]
    reihenfolge = list(itertools.product(*[kats for _, kats in dimensionen]))
    value = {}
    for position, schluessel in enumerate(reihenfolge):
        if schluessel in werte:
            value[str(position)] = werte[schluessel]
    return {
        "value": value,
        "id": ids,
        "size": groessen,
        "dimension": {
            name: {"category": {
                "index": {kat: i for i, kat in enumerate(kats)},
                "label": {kat: NAMEN.get(kat, kat) for kat in kats},
            }}
            for name, kats in dimensionen
        },
    }


NAMEN = {
    "AT": "Österreich", "DE": "Deutschland", "CZ": "Tschechien",
    "SK": "Slowakei", "HU": "Ungarn", "SI": "Slowenien", "IT": "Italien",
    "CH": "Schweiz", "LI": "Liechtenstein", "EE": "Estland",
    "SE": "Schweden", "EU27_2020": "Europäische Union - 27 Länder",
}

# --- Echte Werte, 24.08.2026 ------------------------------------------------

SCHUTZ_JAHRE = [str(j) for j in range(2011, 2024)]
SCHUTZ_PC = [27.5, 27.9, 28, 28, 28.1, 28.1, 28.1, 28.2, 28.9, 29, 29.3, 29.3, 29.3]
SCHUTZ_KM2 = [23109, 23456, 23498, 23544, 23576, 23579, 23581, 23654,
              24219, 24380, 24593, 24593, 24609]

# sdg_15_60, comspec=CO_FARM, unit=I00 (2000=100), EU27. Vollständig.
VOGEL_EU_JAHRE = [str(j) for j in range(1990, 2025)]
VOGEL_EU_I00 = [115.35, 113.99, 112.61, 111.1, 109.5, 107.91, 106.32, 104.74,
                103.16, 101.58, 100, 98.39, 96.77, 95.18, 93.61, 92.1, 90.66,
                89.28, 87.95, 86.64, 85.35, 84.06, 82.75, 81.44, 80.16, 78.88,
                77.62, 76.36, 75.12, 73.89, 72.66, 71.45, 70.25, 69.06, 67.88]
# Die zweite Einheit (1990=100) steht im echten Datensatz HINTER der ersten
# im selben Wertefeld. Sie ist hier absichtlich mit drin: genau an ihr
# scheitert eine Auswertung, die nur nach Zeitindex zuordnet.
VOGEL_EU_I90 = [round(w / 115.35 * 100, 2) for w in VOGEL_EU_I00]

# for_area, indic_fo=FOR, THS_HA. Österreich vollständig; für die Nachbarn
# ist nur 2025 geprüft, deshalb steht auch nur 2025 drin.
WALD_JAHRE = ["1990", "2000", "2010", "2015", "2020", "2025"]
WALD_AT = {"1990": 3775.67, "2000": 3838.14, "2010": 3861.64,
           "2015": 3875.73, "2020": 3889.82, "2025": 3903.91}
WALD_2025 = {"DE": 11481.40, "CZ": 2968.36, "SK": 1940.49, "HU": 2087.37,
             "SI": 1243.55, "IT": 9421.96, "CH": 1267.02, "LI": 5.98}

# sdg_02_40, PC_UAA. Österreich vollständig 2000–2020; für die übrigen
# Länder nur der geprüfte Querschnitt 2020.
BIO_JAHRE = [str(j) for j in range(2000, 2025)]
BIO_AT = [13.8, 14.0, 14.5, 15.4, 16.0, 16.7, 16.7, 17.0, 17.4, 18.5, 19.5,
          19.6, 18.62, 18.40, 19.35, 20.30, 21.25, 23.37, 24.08, 25.33, 25.69]
BIO_2020 = {"EE": 22.41, "SE": 20.31, "CH": 16.98, "IT": 15.96, "CZ": 15.33,
            "SK": 11.67, "SI": 10.29, "DE": 9.59, "HU": 6.03,
            "EU27_2020": 9.10}


def fixture_schutzgebiete(einheit: str) -> dict:
    reihe = SCHUTZ_PC if einheit == "PC" else SCHUTZ_KM2
    return baue_jsonstat(
        [("freq", ["A"]), ("areaprot", ["TPA"]), ("unit", [einheit]),
         ("geo", ["AT"]), ("time", SCHUTZ_JAHRE)],
        {("A", "TPA", einheit, "AT", j): w for j, w in zip(SCHUTZ_JAHRE, reihe)},
    )


def fixture_vogel_eu() -> dict:
    werte = {}
    for j, w in zip(VOGEL_EU_JAHRE, VOGEL_EU_I00):
        werte[("A", "SME", "EU27_2020", "CO_FARM", "I00", j)] = w
    for j, w in zip(VOGEL_EU_JAHRE, VOGEL_EU_I90):
        werte[("A", "SME", "EU27_2020", "CO_FARM", "I90", j)] = w
    return baue_jsonstat(
        [("freq", ["A"]), ("statinfo", ["SME"]), ("geo", ["EU27_2020"]),
         ("comspec", ["CO_FARM"]), ("unit", ["I00", "I90"]),
         ("time", VOGEL_EU_JAHRE)],
        werte,
    )


def fixture_wald() -> dict:
    laender = ["AT"] + list(WALD_2025)
    werte = {("A", "THS_HA", "FOR", "AT", j): w for j, w in WALD_AT.items()}
    for code, w in WALD_2025.items():
        werte[("A", "THS_HA", "FOR", code, "2025")] = w
    return baue_jsonstat(
        [("freq", ["A"]), ("unit", ["THS_HA"]), ("indic_fo", ["FOR"]),
         ("geo", laender), ("time", WALD_JAHRE)],
        werte,
    )


def fixture_biolandbau() -> dict:
    laender = ["AT"] + list(BIO_2020)
    werte = {("A", "PC_UAA", "UAAXK0000", "TOTAL", "AT", j): w
             for j, w in zip(BIO_JAHRE, BIO_AT)}
    for code, w in BIO_2020.items():
        werte[("A", "PC_UAA", "UAAXK0000", "TOTAL", code, "2020")] = w
    return baue_jsonstat(
        [("freq", ["A"]), ("unit", ["PC_UAA"]), ("crops", ["UAAXK0000"]),
         ("agprdmet", ["TOTAL"]), ("geo", laender), ("time", BIO_JAHRE)],
        werte,
    )


def falscher_download(url: str, params: dict | None = None) -> dict:
    p = params or {}
    if "sdg_15_20" in url:
        gemeinsam.log(f"  ↓ [Probe] sdg_15_20 {p.get('unit')}")
        return fixture_schutzgebiete(p.get("unit", "PC"))
    if "sdg_15_60" in url:
        gemeinsam.log("  ↓ [Probe] sdg_15_60")
        return fixture_vogel_eu()
    if "for_area" in url:
        gemeinsam.log("  ↓ [Probe] for_area")
        return fixture_wald()
    if "sdg_02_40" in url:
        gemeinsam.log("  ↓ [Probe] sdg_02_40")
        return fixture_biolandbau()
    raise AssertionError(f"Probe kennt diese Quelle nicht: {url}")


def main() -> None:
    gemeinsam.lade_json = falscher_download
    for modul in ("schutzgebiete", "vogel", "wald", "biolandbau"):
        __import__(modul)
        sys.modules[modul].lade_json = falscher_download

    import build
    build.main()

    # --- Erwartungen ------------------------------------------------------
    import json
    from pathlib import Path

    ordner = Path(gemeinsam.AUSGABE)
    lade = lambda name: json.loads((ordner / f"{name}.json").read_text("utf-8"))

    fehler: list[str] = []
    pruefe = lambda bedingung, text: None if bedingung else fehler.append(text)

    # --- Dekoder: die Zwei-Einheiten-Falle --------------------------------
    tab = gemeinsam.jsonstat_tabelle(fixture_vogel_eu(), "Probe")
    pruefe(len(tab) == 70, f"Dekoder: {len(tab)} Werte statt 70")
    pruefe(tab.get(("A", "SME", "EU27_2020", "CO_FARM", "I00", "2000")) == 100,
           "Dekoder: I00/2000 ist nicht 100 — Positionsrechnung falsch")
    pruefe(tab.get(("A", "SME", "EU27_2020", "CO_FARM", "I90", "1990")) == 100,
           "Dekoder: I90/1990 ist nicht 100 — die zweite Reihe sitzt falsch")
    pruefe(tab.get(("A", "SME", "EU27_2020", "CO_FARM", "I00", "2024")) == 67.88,
           "Dekoder: I00/2024 falsch")

    sg = lade("schutzgebiete")
    pruefe(len(sg["punkte"]) == 13, f"Schutzgebiete: {len(sg['punkte'])} Punkte statt 13")
    pruefe(sg["aktuell"] == 29.3, f"Schutzgebiete: aktuell {sg['aktuell']}")
    pruefe(sg["stillstand_seit"] == 2021, "Schutzgebiete: Stillstand nicht ab 2021")
    pruefe(sg["luecke"] == 0.7, f"Schutzgebiete: Lücke {sg['luecke']} statt 0.7")

    vo = lade("vogel")
    pruefe(vo["aktuell"] == 56.8, f"Vögel: aktuell {vo['aktuell']}")
    pruefe(vo["verlust"] == 43.2, f"Vögel: Verlust {vo['verlust']}")
    pruefe(vo["arten_anzahl"] == 23, "Vögel: nicht 23 Arten")
    pruefe(vo["eu_vorhanden"], "Vögel: EU-Reihe fehlt")
    # Umbasierung: EU 1998 = 103.16 -> muss nach der Umrechnung 100 sein
    eu1998 = next(p["eu"] for p in vo["punkte"] if p["jahr"] == 1998)
    pruefe(eu1998 == 100.0, f"Vögel: EU-Basisjahr 1998 ergibt {eu1998} statt 100")
    eu2023 = next(p["eu"] for p in vo["punkte"] if p["jahr"] == 2023)
    pruefe(abs(eu2023 - 66.9) < 0.2, f"Vögel: EU 2023 = {eu2023}, erwartet ~66.9")
    pruefe(vo["eu_vergleich"]["differenz"] < 0,
           "Vögel: Österreich müsste unter der EU-Linie liegen")
    # Die AT-Reihe endet 2023, die EU-Reihe 2024 — die Achse muss beides tragen
    pruefe(vo["punkte"][-1]["jahr"] == 2024, "Vögel: Achse endet nicht 2024")
    pruefe(vo["punkte"][-1]["index"] is None,
           "Vögel: AT hat 2024 einen Wert, den es nicht geben darf")
    pruefe(vo["punkte"][0]["jahr"] == 1990, "Vögel: Achse beginnt nicht 1990")
    pruefe(vo["punkte"][0]["index"] is None, "Vögel: AT hat 1990 einen Wert")

    bo = lade("boden")
    pruefe(bo["aktuell_ha_pro_tag"] == 6.5, "Boden: Tageswert falsch")

    rl = lade("rotelisten")
    pruefe(rl["gruppen_gesamt"] == 27, "Rote Listen: nicht 27 Gruppen")
    pruefe(rl["aktuell"] == 3, "Rote Listen: nicht 3 aktuell")
    pruefe(rl["aeltester"]["jahr"] == 1994, "Rote Listen: Käfer nicht 1994")

    er = lade("erhaltung")
    pruefe(len(er["gruppen"]) == 2, "Erhaltung: nicht zwei Gruppen")
    lrt = er["gruppen"][0]
    pruefe(lrt["anteile"] == [18.0, 35.0, 44.0, 3.0], "Erhaltung: LRT-Anteile falsch")
    pruefe(lrt["bewertungen"] == 117, "Erhaltung: nicht 117 LRT-Bewertungen")
    pruefe(er["gruppen"][1]["summe"] == 99.0,
           "Erhaltung: Artensumme ist nicht 99 % — die Rundung der Quelle fehlt")
    pruefe(er["naechste_vorhanden"] is False, "Erhaltung: nächste Periode falsch gemeldet")

    bt = lade("biotoptypen")
    pruefe(bt["bewertet"] == 383, "Biotoptypen: nicht 383 bewertet")
    pruefe(bt["gefaehrdet"] == 284, f"Biotoptypen: {bt['gefaehrdet']} gefährdet statt 284")
    pruefe(bt["anteil_gefaehrdet"] == 74.2,
           f"Biotoptypen: {bt['anteil_gefaehrdet']} % statt 74.2")
    pruefe(bt["ohne_angabe"] == 6, f"Biotoptypen: {bt['ohne_angabe']} ohne Angabe statt 6")
    pruefe(sum(s["anzahl"] for s in bt["stufen"]) == 383,
           "Biotoptypen: Stufen summieren sich nicht auf 383")

    wa = lade("wald")
    at = wa["oesterreich"]
    pruefe(at["veraenderung"] == 3.4, f"Wald: AT {at['veraenderung']} % statt 3.4")
    pruefe(at["von"] == 1990 and at["bis"] == 2025, "Wald: AT-Zeitraum falsch")
    # Die Nachbarn haben im Fixture NUR 2025 — ihre Veränderung ist dann 0.
    # Genau das soll sichtbar bleiben statt als echter Befund durchzugehen.
    li = next((e for e in wa["eintraege"] if e["code"] == "LI"), None)
    pruefe(li is not None, "Wald: Liechtenstein fehlt — der einzige Datensatz, der es führt")
    pruefe(wa["eintraege"][0]["veraenderung"] >= at["veraenderung"],
           "Wald: Rangliste ist nicht absteigend sortiert")

    bl = lade("biolandbau")
    pruefe(bl["vergleichsjahr"] == 2020,
           f"Biolandbau: Vergleichsjahr {bl['vergleichsjahr']} statt 2020")
    pruefe(bl["oesterreich"]["wert"] == 25.7,
           f"Biolandbau: AT {bl['oesterreich']['wert']} statt 25.7")
    pruefe(bl["rang"] == 1, f"Biolandbau: AT auf Platz {bl['rang']} statt 1")
    pruefe(bl["eu_wert"] == 9.1, f"Biolandbau: EU {bl['eu_wert']} statt 9.1")
    pruefe(all(e["code"] != "EU27_2020" for e in bl["rangliste"]),
           "Biolandbau: EU-Aggregat steht in der Rangliste und verschiebt den Platz")
    pruefe(len(bl["verlauf"]) == 21, f"Biolandbau: {len(bl['verlauf'])} Jahre statt 21")

    kpi = lade("kpi")
    for feld in ("schutzgebiete_prozent", "vogel_index", "boden_ha_pro_tag",
                 "rotelisten_aktuell", "erhaltung_guenstig",
                 "biotoptypen_anteil", "bio_anteil", "wald_veraenderung"):
        pruefe(feld in kpi, f"kpi.json: Feld {feld} fehlt")

    meta = lade("meta")
    arten = {q["art"] for q in meta["quellen"]}
    pruefe(arten == {"api", "gepflegt"},
           f"meta.json: Quellenarten {arten} statt api und gepflegt")

    print()
    print("=" * 70)
    if fehler:
        print(f"PROBE FEHLGESCHLAGEN — {len(fehler)} Abweichung(en):")
        for text in fehler:
            print(f"  ✗ {text}")
        print("=" * 70)
        sys.exit(1)
    print("PROBE BESTANDEN — alle Erwartungen erfüllt.")
    print("=" * 70)


if __name__ == "__main__":
    main()
