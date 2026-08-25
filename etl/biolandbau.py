"""
Anteil der biologisch bewirtschafteten Fläche — Eurostat sdg_02_40.

ECHTE API. Rund 35 Meldeländer, 2000–2024, inklusive Schweiz und Norwegen.

WARUM DIESER ABSCHNITT ANDERS GEBAUT IST ALS DIE SCHUTZGEBIETE:
Beide Kennzahlen haben eine Zielmarke aus der Biodiversitäts-Strategie
2030+ (30 % Schutzgebiete, 35 % Bio). Beide als Linie mit Zielmarke und
Abstandserzählung zu zeigen wäre zweimal dieselbe Grafik — der Leser sieht
die Wiederholung, nicht den Inhalt. Hier trägt deshalb der LÄNDERVERGLEICH
die Aussage: Österreich liegt an der europäischen Spitze, und das ist ein
anderer Befund als „Ziel noch nicht erreicht".

EINE FALLE IN DEN DATEN, die man nicht sieht, wenn man nur AT abfragt:
Der Datensatz reicht bis 2024, aber Österreich meldet zuletzt für 2020.
Ein Ranking auf „das jeweils neueste Jahr je Land" würde also Österreichs
Wert von 2020 gegen die 2024er-Werte anderer stellen. Deshalb wird hier
ein GEMEINSAMES Vergleichsjahr gesucht: das jüngste Jahr, für das
Österreich einen Wert hat.
"""

from __future__ import annotations

import config
from gemeinsam import (jsonstat_laender, lade_json, laender_namen, log,
                       quelle_vermerken, warnen)


def baue_biolandbau() -> dict | None:
    log("\n[8/8] Biologische Landwirtschaft — EU-Vergleich (Eurostat sdg_02_40)")

    url = f"{config.EUROSTAT_BASIS}/{config.BIOLANDBAU_CODE}"
    roh = lade_json(url, config.BIOLANDBAU_PARAMS)
    laender = jsonstat_laender(roh, "sdg_02_40")
    namen = laender_namen(roh)

    at = laender.get("AT")
    if not at:
        warnen("Biolandbau: keine Werte für Österreich — Abschnitt entfällt")
        return None

    # Gemeinsames Vergleichsjahr: das jüngste, das Österreich führt.
    vergleichsjahr = max(at)
    log(f"    Vergleichsjahr {vergleichsjahr} (jüngster Wert für Österreich)")

    # Aggregate und Nicht-Staaten aus der Rangliste halten. EU27 wird als
    # Bezugslinie getrennt geführt, sonst stünde die Union als „Land" im
    # Ranking und verschöbe Österreichs Platz.
    AGGREGATE = {"EU27_2020", "EU", "EA19", "EA20", "EA21"}

    rangliste = []
    ohne_wert = []
    for code, reihe in laender.items():
        if code in AGGREGATE:
            continue
        wert = reihe.get(vergleichsjahr)
        if wert is None:
            ohne_wert.append(code)
            continue
        rangliste.append({
            "code": code,
            "name": namen.get(code, code),
            "wert": round(wert, 1),
            "hervorgehoben": code == config.HERVORHEBUNG,
            "nachbar": code in config.NACHBARN,
        })

    if not rangliste:
        warnen("Biolandbau: keine Länderwerte im Vergleichsjahr")
        return None

    rangliste.sort(key=lambda e: e["wert"], reverse=True)
    oesterreich = next(e for e in rangliste if e["code"] == "AT")
    rang = rangliste.index(oesterreich) + 1

    eu_wert = (laender.get(config.EU_AGGREGAT) or {}).get(vergleichsjahr)
    eu_wert = round(eu_wert, 1) if eu_wert is not None else None

    # Zeitreihe Österreich, für die Tabelle und den Verlaufshinweis
    jahre = sorted(at)
    verlauf = [{"jahr": int(j), "wert": round(at[j], 1)} for j in jahre]

    log(f"    Österreich {oesterreich['wert']} % — Platz {rang} von "
        f"{len(rangliste)}" + (f", EU-Schnitt {eu_wert} %" if eu_wert else ""))
    if ohne_wert:
        log(f"    Ohne Wert für {vergleichsjahr}: {len(ohne_wert)} Gebiete")

    # Meldet Österreich noch? Wenn die Reihe deutlich vor dem Ende des
    # Datensatzes abbricht, ist das erwähnenswert und kein Programmfehler.
    letztes_im_satz = max(
        (max(r) for r in laender.values() if r), default=vergleichsjahr
    )
    veraltet = int(letztes_im_satz) - int(vergleichsjahr)
    if veraltet >= 2:
        log(f"    Hinweis: Der Datensatz reicht bis {letztes_im_satz}, "
            f"Österreich meldet zuletzt {vergleichsjahr}")

    quelle_vermerken(
        name=("Eurostat — sdg_02_40, Anteil der ökologisch bewirtschafteten "
              "Fläche an der landwirtschaftlich genutzten Fläche"),
        url="https://ec.europa.eu/eurostat/databrowser/view/sdg_02_40",
        lizenz="Eurostat-Nutzungsbedingungen",
        stand=str(vergleichsjahr),
        art="api",
    )

    return {
        "rangliste": rangliste,
        "verlauf": verlauf,
        "oesterreich": oesterreich,
        "rang": rang,
        "anzahl": len(rangliste),
        "vergleichsjahr": int(vergleichsjahr),
        "eu_wert": eu_wert,
        "eu_name": "EU-27",
        "ziel": config.BIOLANDBAU_ZIEL,
        "luecke": round(config.BIOLANDBAU_ZIEL - oesterreich["wert"], 1),
        "datensatz_bis": int(letztes_im_satz),
        "meldeluecke": veraltet,
        "hinweis": (
            f"Umgestellte Flächen und Flächen in Umstellung zusammen, Anteil "
            f"an der landwirtschaftlich genutzten Fläche. Alle Länder im "
            f"selben Jahr {vergleichsjahr} verglichen — der Datensatz reicht "
            f"weiter, Österreich meldet zuletzt für dieses Jahr."
        ),
    }
