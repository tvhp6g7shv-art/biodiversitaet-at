"""
Flächeninanspruchnahme und Versiegelung — der Bodenverbrauch Österreichs.

GEPFLEGTE REIHE. Die ÖROK stellt Excel-Tabellen bereit, aber ohne stabilen
Dateinamen; ein automatischer Abruf würde beim nächsten Zyklus stillschweigend
ins Leere greifen. Die Zahlen sind deshalb aus dem Bericht abgeschrieben.

  Quelle:   ÖROK (2025): Flächeninanspruchnahme und Versiegelung in
            Österreich — Bericht zu den Ergebnissen 2022 und 2025.
            ÖROK-Schriftenreihe Nr. 220, Wien, Dezember 2025.
  PDF:      https://www.oerok.gv.at/fileadmin/user_upload/publikationen/
            Schriftenreihe/220/OEROK-Monitoring_Bericht_2025-12-01.pdf
  Downloads: https://www.oerok.gv.at/monitoring-flaecheninanspruchnahme/daten
  Abgerufen: 24.08.2026

Zwei Dinge, die beim Weiterpflegen leicht durcheinandergehen:

1. Flächeninanspruchnahme und Versiegelung haben UNTERSCHIEDLICHE Stichjahre.
   Die Inanspruchnahme liegt für 2025 vor, die Versiegelung nur für 2022 —
   sie wird aus Befliegungen abgeleitet und hinkt rund zwei Jahre nach.
   Wer beide Werte im selben Satz nennt, muss beide Jahre nennen.

2. Die Tageswerte sind PERIODENMITTEL, keine Jahreswerte. „6,5 ha/Tag" ist
   der Durchschnitt 2022–2025, nicht der Wert von 2025. Im Diagramm gehören
   sie deshalb an die Periode, nicht an einen Zeitpunkt.
"""

from __future__ import annotations

from gemeinsam import log, pflegepruefung, quelle_vermerken

STAND_JAHR = 2025            # Stichjahr der Flächeninanspruchnahme
BERICHT_JAHR = 2025          # Erscheinungsjahr des Berichts
VERSIEGELUNG_STAND = 2022    # Stichjahr der Versiegelung (hinkt nach)

# Bestand der Flächeninanspruchnahme je Stichjahr, in km²
BESTAND = {
    2022: 5610.0,
    2025: 5681.2,
}

ANTEIL_LANDESFLAECHE = 6.8       # % der Bundesfläche, Stichjahr 2025
ANTEIL_DAUERSIEDLUNGSRAUM = 17.4  # % des Dauersiedlungsraums, Stichjahr 2025
DAUERSIEDLUNGSRAUM_KM2 = 32707.0
DAUERSIEDLUNGSRAUM_ANTEIL = 39.0  # % der Landesfläche

# Versiegelung, Stichjahr 2022
VERSIEGELUNG_KM2 = 2961.0
VERSIEGELUNG_ANTEIL_INANSPRUCHNAHME = 52.8  # % der beanspruchten Fläche
VERSIEGELUNG_ANTEIL_LANDESFLAECHE = 3.5     # % der Bundesfläche

# Tageswerte je Periode, in Hektar pro Tag. Periodenmittel, keine Jahreswerte.
# Ältere Perioden als 2013–2016 nennt der Bericht nicht; frühere Medienwerte
# („rund 11 ha/Tag", „16 Fußballfelder") beruhen auf der alten DKM-Methode
# und sind mit dieser Reihe nicht vergleichbar — deshalb nicht aufgenommen.
TAGESWERTE = [
    {"periode": "2013–2016", "von": 2013, "bis": 2016, "ha_pro_tag": 14.7},
    {"periode": "2016–2019", "von": 2016, "bis": 2019, "ha_pro_tag": 12.0},
    {"periode": "2019–2022", "von": 2019, "bis": 2022, "ha_pro_tag": 10.9},
    {"periode": "2022–2025", "von": 2022, "bis": 2025, "ha_pro_tag": 6.5},
]

# Aufteilung des Bestands 2025 nach Hauptkategorien.
# Der Bericht nennt bei zwei Kategorien leicht abweichende km²-Werte an
# verschiedenen Stellen (Rundung); hier steht jeweils der niedrigere.
KATEGORIEN = [
    {"name": "Siedlung im Bauland",      "prozent": 49.2, "km2": 2797.0},
    {"name": "Verkehr",                  "prozent": 30.4, "km2": 1725.0},
    {"name": "Siedlung außerhalb",       "prozent": 11.9, "km2": 677.0},
    {"name": "Freizeit und Erholung",    "prozent": 5.6,  "km2": 320.0},
    {"name": "Ver- und Entsorgung",      "prozent": 2.6,  "km2": 151.0},
    {"name": "Energie",                  "prozent": 0.2,  "km2": 9.3},
]


def baue_boden() -> dict:
    log("\n[3/8] Bodenverbrauch — ÖROK-Monitoring (gepflegt)")

    erst, letzt = TAGESWERTE[0], TAGESWERTE[-1]
    rueckgang = round(
        (erst["ha_pro_tag"] - letzt["ha_pro_tag"]) / erst["ha_pro_tag"] * 100, 1
    )

    # Gegenprobe: Summieren sich die Kategorienanteile auf rund 100?
    # Gerundete Quellprozente ergeben fast nie exakt 100 — erst ab einem
    # Prozentpunkt Abweichung ist etwas faul.
    summe = round(sum(k["prozent"] for k in KATEGORIEN), 1)
    if abs(summe - 100) > 1.0:
        from gemeinsam import warnen
        warnen(
            f"Bodenverbrauch: Kategorienanteile summieren sich auf {summe} % "
            f"statt 100 % — vermutlich fehlt eine Kategorie oder ein Wert ist "
            f"falsch abgeschrieben"
        )
    else:
        log(f"    Gegenprobe Kategorien: {summe} % (Rundung der Quelle)")

    zuwachs = round(BESTAND[2025] - BESTAND[2022], 1)

    log(f"    Bestand {STAND_JAHR}: {BESTAND[2025]:,.1f} km² "
        f"({ANTEIL_LANDESFLAECHE} % der Landesfläche)")
    log(f"    Versiegelt {VERSIEGELUNG_STAND}: {VERSIEGELUNG_KM2:,.0f} km²")
    log(f"    Tageswert {erst['periode']}: {erst['ha_pro_tag']} ha  →  "
        f"{letzt['periode']}: {letzt['ha_pro_tag']} ha  (−{rueckgang} %)")
    pflegepruefung("boden", BERICHT_JAHR, "ÖROK-Bodenmonitoring")

    quelle_vermerken(
        name=("ÖROK (2025) — Flächeninanspruchnahme und Versiegelung in "
              "Österreich, Schriftenreihe Nr. 220"),
        url="https://www.oerok.gv.at/monitoring-flaecheninanspruchnahme",
        lizenz="Open Government Data",
        stand=str(STAND_JAHR),
        art="gepflegt",
    )

    _bestand_de = f"{BESTAND[2025]:,.0f}".replace(",", ".")
    _versiegelt_de = str(VERSIEGELUNG_ANTEIL_INANSPRUCHNAHME).replace(".", ",")

    return {
        "tageswerte": TAGESWERTE,
        "aktuell_ha_pro_tag": letzt["ha_pro_tag"],
        "aktuell_periode": letzt["periode"],
        "erste_periode": erst["periode"],
        "erster_ha_pro_tag": erst["ha_pro_tag"],
        "rueckgang_prozent": rueckgang,
        "bestand_km2": BESTAND[2025],
        "bestand_zuwachs_km2": zuwachs,
        "stand": STAND_JAHR,
        "anteil_landesflaeche": ANTEIL_LANDESFLAECHE,
        "anteil_dauersiedlungsraum": ANTEIL_DAUERSIEDLUNGSRAUM,
        "dauersiedlungsraum_km2": DAUERSIEDLUNGSRAUM_KM2,
        "versiegelung": {
            "stand": VERSIEGELUNG_STAND,
            "km2": VERSIEGELUNG_KM2,
            "anteil_inanspruchnahme": VERSIEGELUNG_ANTEIL_INANSPRUCHNAHME,
            "anteil_landesflaeche": VERSIEGELUNG_ANTEIL_LANDESFLAECHE,
        },
        "kategorien": KATEGORIEN,
        "pflege": {
            "art": "gepflegt",
            "quelle": ("ÖROK (2025): Flächeninanspruchnahme und Versiegelung "
                       "in Österreich — Bericht zu den Ergebnissen 2022 und "
                       "2025. ÖROK-Schriftenreihe Nr. 220, Dezember 2025."),
            "bericht_jahr": BERICHT_JAHR,
            "abgerufen": "2026-08-24",
        },
        # Zahlen einzeln nach deutscher Schreibweise drehen, NICHT ueber
        # den fertigen Satz. Ein .replace(",", ".") am Satzende traf auch
        # das Satzkomma ("Periodenmittel. keine Jahreswerte") und machte
        # aus 52,8 % ein 52.8 % — benachbarte Literale werden vor dem
        # Methodenaufruf zusammengefuegt.
        "hinweis": (
            "Die Tageswerte sind Periodenmittel, keine Jahreswerte. "
            "Beanspruchte Fläche ist nicht dasselbe wie versiegelte: von "
            f"{_bestand_de} km² Inanspruchnahme waren "
            f"{VERSIEGELUNG_STAND} rund {_versiegelt_de} % tatsächlich "
            "versiegelt."
        ),
    }
