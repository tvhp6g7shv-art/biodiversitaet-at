"""
Nadelholz, Laubholz und Freiflächen im Ertragswald — Österreichische Waldinventur.

WARUM DIESER ABSCHNITT: Der Waldbiodiversitätsbericht 2026 nennt den
sinkenden Nadelholzanteil als seinen ersten Befund — „1990er Jahre knapp
70 %, aktuell 60 %". Das ist die längste durchgehende Reihe, die die ÖWI
öffentlich hergibt: vier Erhebungsperioden über 27 Jahre, Bund und
Bundesländer.

DER FALLSTRICK, und diesmal ist er selbst die Aussage:

Die ÖWI hat zwischen den Perioden die Bezugsgröße ihrer Prozentangaben
gewechselt. Nachgerechnet aus den Flächen dieser Datei:

    Nadelholz 1992/96   2320 / 3352 (Ertragswald) = 69,2 %   so veröffentlicht
    Nadelholz 2018/23   2008 / 3356 (Ertragswald) = 59,8 %   NICHT veröffentlicht
    Nadelholz 2018/23   2008 / 4018 (Gesamtwald)  = 50,0 %   so veröffentlicht

Wer die veröffentlichten Prozentwerte der ersten und der letzten Periode
nebeneinanderstellt, zeigt einen Rückgang von 19 Prozentpunkten. Real sind
es 9,4. Gut die Hälfte des scheinbaren Einbruchs ist ein Nennerwechsel.
Dasselbe gilt spiegelbildlich für das Laubholz: veröffentlicht 22,3 → 21,6 %
(sieht nach Stillstand aus), gegen den Ertragswald gerechnet 22,3 → 25,8 %.

Dieses Modul rechnet deshalb ALLE Anteile selbst aus Fläche und `1_l`.
Das Feld `_Proz` der Quelle wird nur zur Gegenprobe gelesen, nie gezeigt.

DIE DRITTE REIHE: Ertragswald minus Nadelholz minus Laubholz ergibt die
Flächen, die die ÖWI als Blößen, Lücken, Sträucher im Bestand und
Strauchflächen führt. Gegengeprüft gegen Tab. 2 des Berichts:
1992/96 ergibt die Differenz 284, die Einzelposten summieren sich auf 285;
2018/23 ergibt sie 481 gegen 482. Die Abweichung ist Rundung.
Diese Reihe wächst von 8,5 auf 14,3 % — der Bericht nennt für 2018/23
wörtlich „einen Anteil von 14,3 % im österreichischen Ertragswald".

WAS DIESE REIHE NICHT SAGT: Ob die Zunahme Kalamität ist oder gewollte
Auflichtung, steht in keiner der Quellen. Der Bericht führt die Kategorie
neutral. Der Abschnitt darf sie nicht als Schaden benennen.

Abgerufen und nachgerechnet am 27.08.2026.
"""

from __future__ import annotations

import config
from gemeinsam import log, pflegepruefung, quelle_vermerken, warnen

# ---------------------------------------------------------------------------
# Rohwerte in Tausend Hektar, Quelle waldinventur.at, Feld `_Wert`
#   Nadelholz gesamt   Indikator 22_08_A
#   Laubholz gesamt    Indikator 22_34_A
#   Ertragswald        Indikator 1_l
# Perioden: erg5 = 1992/96, erg6 = 2000/02, erg7 = 2007/09,
#           erg9_10 = 2018/23 (Zwischenauswertung, aktuellster Stand)
#
# 2016/21 (erg9) fehlt hier bewusst: Zwischen- und Hauptauswertung teilen
# vier von sechs Jahrespaneln, ihre Differenz ist stark autokorreliert.
# Vier weit auseinanderliegende Perioden erzählen den Verlauf ehrlicher.
# ---------------------------------------------------------------------------
PERIODEN = ["1992/96", "2000/02", "2007/09", "2018/23"]

REGIONEN = ["Burgenland", "Kärnten", "Niederösterreich", "Oberösterreich",
            "Salzburg", "Steiermark", "Tirol", "Vorarlberg", "Wien"]

NADELHOLZ_TSD_HA = {
    "1992/96": {"Österreich": 2320, "Burgenland": 53, "Kärnten": 392,
                "Niederösterreich": 408, "Oberösterreich": 284, "Salzburg": 200,
                "Steiermark": 665, "Tirol": 276, "Vorarlberg": 42, "Wien": 0},
    "2000/02": {"Österreich": 2255, "Burgenland": 49, "Kärnten": 381,
                "Niederösterreich": 396, "Oberösterreich": 280, "Salzburg": 193,
                "Steiermark": 650, "Tirol": 268, "Vorarlberg": 39, "Wien": 0},
    "2007/09": {"Österreich": 2139, "Burgenland": 46, "Kärnten": 362,
                "Niederösterreich": 381, "Oberösterreich": 267, "Salzburg": 181,
                "Steiermark": 606, "Tirol": 259, "Vorarlberg": 39, "Wien": 0},
    "2018/23": {"Österreich": 2008, "Burgenland": 40, "Kärnten": 342,
                "Niederösterreich": 344, "Oberösterreich": 248, "Salzburg": 175,
                "Steiermark": 579, "Tirol": 246, "Vorarlberg": 35, "Wien": 0},
}

LAUBHOLZ_TSD_HA = {
    "1992/96": {"Österreich": 748, "Burgenland": 67, "Kärnten": 65,
                "Niederösterreich": 259, "Oberösterreich": 130, "Salzburg": 47,
                "Steiermark": 131, "Tirol": 30, "Vorarlberg": 13, "Wien": 6},
    "2000/02": {"Österreich": 802, "Burgenland": 72, "Kärnten": 70,
                "Niederösterreich": 272, "Oberösterreich": 137, "Salzburg": 50,
                "Steiermark": 144, "Tirol": 35, "Vorarlberg": 15, "Wien": 6},
    "2007/09": {"Österreich": 821, "Burgenland": 74, "Kärnten": 77,
                "Niederösterreich": 273, "Oberösterreich": 140, "Salzburg": 46,
                "Steiermark": 149, "Tirol": 39, "Vorarlberg": 16, "Wien": 6},
    "2018/23": {"Österreich": 867, "Burgenland": 80, "Kärnten": 78,
                "Niederösterreich": 288, "Oberösterreich": 146, "Salzburg": 49,
                "Steiermark": 162, "Tirol": 40, "Vorarlberg": 16, "Wien": 7},
}

ERTRAGSWALD_TSD_HA = {
    "1992/96": {"Österreich": 3352, "Burgenland": 128, "Kärnten": 505,
                "Niederösterreich": 722, "Oberösterreich": 441, "Salzburg": 275,
                "Steiermark": 868, "Tirol": 344, "Vorarlberg": 62, "Wien": 8},
    "2000/02": {"Österreich": 3371, "Burgenland": 129, "Kärnten": 507,
                "Niederösterreich": 728, "Oberösterreich": 443, "Salzburg": 280,
                "Steiermark": 869, "Tirol": 346, "Vorarlberg": 62, "Wien": 9},
    "2007/09": {"Österreich": 3367, "Burgenland": 131, "Kärnten": 505,
                "Niederösterreich": 733, "Oberösterreich": 444, "Salzburg": 276,
                "Steiermark": 862, "Tirol": 347, "Vorarlberg": 62, "Wien": 9},
    "2018/23": {"Österreich": 3356, "Burgenland": 130, "Kärnten": 499,
                "Niederösterreich": 735, "Oberösterreich": 444, "Salzburg": 271,
                "Steiermark": 860, "Tirol": 347, "Vorarlberg": 62, "Wien": 9},
}

# Gesamtwald Österreich 2018/23 — der Nenner, gegen den die Quelle ihre
# aktuellen Prozentwerte rechnet. Steht so auch hinter den 39,8 % der Fichte
# in fichte.py. Wird nur gebraucht, um den Nennerwechsel zu BELEGEN.
GESAMTWALD_2018_23 = 4018

# Veröffentlichte Prozentwerte des Bundes, Feld `_Proz`, nur zur Gegenprobe.
# Für die ersten drei Perioden müssen sie zur eigenen Rechnung passen.
KONTROLLE_ERTRAGSWALD = {
    "nadelholz": {"1992/96": 69.2, "2000/02": 66.9, "2007/09": 63.5},
    "laubholz":  {"1992/96": 22.3, "2000/02": 23.8, "2007/09": 24.4},
}

# Für 2018/23 müssen sie es GERADE NICHT — das ist der Befund.
KONTROLLE_NENNERWECHSEL = {"nadelholz": 50.0, "laubholz": 21.6}

TOLERANZ_PUNKTE = 0.15   # Quelle rundet auf eine Stelle, Flächen sind gerundet


def _anteil(zaehler: int, nenner: int) -> float | None:
    return zaehler / nenner * 100 if nenner else None


def _reihe(quelle: dict, region: str) -> list[dict]:
    return [
        {
            "periode": p,
            "flaeche_tsd_ha": quelle[p][region],
            "anteil": round(_anteil(quelle[p][region],
                                    ERTRAGSWALD_TSD_HA[p][region]), 1),
        }
        for p in PERIODEN
    ]


def _gegenprobe() -> None:
    """
    Zwei Prüfungen, die in entgegengesetzte Richtung laufen.

    Die erste stellt sicher, dass die eigene Rechnung für die drei älteren
    Perioden mit der Quelle übereinstimmt — dort ist der Nenner der
    Ertragswald, also muss sie passen.

    Die zweite stellt sicher, dass sie für 2018/23 NICHT übereinstimmt und
    stattdessen der Gesamtwald-Nenner trifft. Wenn diese Prüfung eines
    Tages anschlägt, hat die Quelle ihre Systematik erneut geändert — dann
    ist die Aussage dieses Abschnitts zu überdenken, nicht nur die Zahl.
    """
    for name, quelle in (("nadelholz", NADELHOLZ_TSD_HA),
                         ("laubholz", LAUBHOLZ_TSD_HA)):
        for periode, veroeffentlicht in KONTROLLE_ERTRAGSWALD[name].items():
            eigen = _anteil(quelle[periode]["Österreich"],
                            ERTRAGSWALD_TSD_HA[periode]["Österreich"])
            if eigen is None or abs(eigen - veroeffentlicht) > TOLERANZ_PUNKTE:
                warnen(
                    f"Baumarten: eigene Rechnung {eigen:.1f} % weicht für "
                    f"{name} {periode} von den veröffentlichten "
                    f"{veroeffentlicht} % ab — Bezugsgröße der Quelle prüfen"
                )

        flaeche = quelle["2018/23"]["Österreich"]
        gegen_ertragswald = _anteil(flaeche, ERTRAGSWALD_TSD_HA["2018/23"]["Österreich"])
        gegen_gesamtwald = _anteil(flaeche, GESAMTWALD_2018_23)
        veroeffentlicht = KONTROLLE_NENNERWECHSEL[name]

        if abs(gegen_ertragswald - veroeffentlicht) <= TOLERANZ_PUNKTE:
            warnen(
                f"Baumarten: der veröffentlichte Wert {veroeffentlicht} % für "
                f"{name} 2018/23 passt jetzt zum Ertragswald. Der Nennerwechsel, "
                f"auf dem dieser Abschnitt aufbaut, ist damit aufgehoben — "
                f"Text und Hinweiszeile prüfen."
            )
        elif abs(gegen_gesamtwald - veroeffentlicht) > TOLERANZ_PUNKTE:
            warnen(
                f"Baumarten: der veröffentlichte Wert {veroeffentlicht} % für "
                f"{name} 2018/23 passt weder zum Ertragswald "
                f"({gegen_ertragswald:.1f} %) noch zum Gesamtwald "
                f"({gegen_gesamtwald:.1f} %) — dritte Bezugsgröße im Spiel?"
            )


def baue_baumarten() -> dict | None:
    log("\n[14/14] Baumarten — ÖWI, Nadel- und Laubholz im Ertragswald (gepflegt)")

    pflegepruefung("baumarten", 2025, "ÖWI-Zwischenauswertung 2018/23")
    _gegenprobe()

    erste, letzte = PERIODEN[0], PERIODEN[-1]

    nadel = _reihe(NADELHOLZ_TSD_HA, "Österreich")
    laub = _reihe(LAUBHOLZ_TSD_HA, "Österreich")

    # Dritte Reihe als Rest, damit die drei Anteile je Periode auf 100 kommen.
    frei = []
    for p in PERIODEN:
        gesamt = ERTRAGSWALD_TSD_HA[p]["Österreich"]
        rest = gesamt - NADELHOLZ_TSD_HA[p]["Österreich"] - LAUBHOLZ_TSD_HA[p]["Österreich"]
        frei.append({
            "periode": p,
            "flaeche_tsd_ha": rest,
            "anteil": round(_anteil(rest, gesamt), 1),
        })

    # Selbstkontrolle: die drei Anteile müssen je Periode 100 ergeben.
    for i, p in enumerate(PERIODEN):
        summe = nadel[i]["anteil"] + laub[i]["anteil"] + frei[i]["anteil"]
        if abs(summe - 100) > 0.3:
            warnen(f"Baumarten: Anteile {p} summieren auf {summe:.1f} statt 100")

    eintraege = []
    for region in REGIONEN:
        jetzt = _anteil(NADELHOLZ_TSD_HA[letzte][region],
                        ERTRAGSWALD_TSD_HA[letzte][region])
        damals = _anteil(NADELHOLZ_TSD_HA[erste][region],
                         ERTRAGSWALD_TSD_HA[erste][region])
        eintraege.append({
            "name": region,
            "nadelholz": round(jetzt, 1),
            "nadelholz_frueher": round(damals, 1),
            "veraenderung": round(jetzt - damals, 1),
            "laubholz": round(_anteil(LAUBHOLZ_TSD_HA[letzte][region],
                                      ERTRAGSWALD_TSD_HA[letzte][region]), 1),
            # Wien trägt keinen messbaren Nadelholzbestand. Ein Nullbalken
            # neben acht echten Werten sieht nach fehlenden Daten aus, ist
            # aber ein Befund — das Frontend soll ihn kennzeichnen können.
            "ohne_bestand": NADELHOLZ_TSD_HA[letzte][region] == 0,
        })
    eintraege.sort(key=lambda e: -e["nadelholz"])

    daten = {
        "stand": f"ÖWI {letzte}",
        "abgerufen": "2026-08-27",
        "perioden": PERIODEN,
        "reihen": [
            {"name": "Nadelholz", "werte": nadel},
            {"name": "Laubholz", "werte": laub},
            {"name": "Blößen, Lücken und Sträucher", "werte": frei},
        ],
        "nadel_jetzt": nadel[-1]["anteil"],
        "nadel_frueher": nadel[0]["anteil"],
        "nadel_veraenderung": round(nadel[-1]["anteil"] - nadel[0]["anteil"], 1),
        "laub_jetzt": laub[-1]["anteil"],
        "laub_frueher": laub[0]["anteil"],
        "frei_jetzt": frei[-1]["anteil"],
        "frei_frueher": frei[0]["anteil"],
        # Der Nennerwechsel als eigene Größe — damit die Methodik-Seite und
        # der Aufklapper dieselbe Zahl nennen und nicht auseinanderlaufen.
        "nennerwechsel": {
            "veroeffentlicht_erste": KONTROLLE_ERTRAGSWALD["nadelholz"][erste],
            "veroeffentlicht_letzte": KONTROLLE_NENNERWECHSEL["nadelholz"],
            "scheinbarer_rueckgang": round(
                KONTROLLE_ERTRAGSWALD["nadelholz"][erste]
                - KONTROLLE_NENNERWECHSEL["nadelholz"], 1),
            "tatsaechlicher_rueckgang": round(
                nadel[0]["anteil"] - nadel[-1]["anteil"], 1),
        },
        "eintraege": eintraege,
        # Einordnung unter der Grafik, Konvention 150–234 Zeichen. Gemessen: 213.
        "hinweis": (
            "Alle Anteile gegen den bewirtschafteten Wald gerechnet, nicht gegen "
            "die gesamte Waldfläche — die Waldinventur hat diesen Nenner zwischen "
            "den Erhebungen gewechselt und macht den Rückgang dadurch doppelt so "
            "groß, wie er ist."
        ),
    }

    quelle_vermerken(
        "Nadel- und Laubholz im Ertragswald",
        "https://www.waldinventur.at/",
        "BFW — Verwendung mit Quellenangabe, Freigabe angefragt",
        f"ÖWI {letzte}",
        "gepflegt",
    )

    log(f"  Nadelholz {daten['nadel_frueher']} → {daten['nadel_jetzt']} % "
        f"({daten['nadel_veraenderung']:+} Pkt) · Laubholz "
        f"{daten['laub_frueher']} → {daten['laub_jetzt']} % · "
        f"{len(eintraege)} Regionen")

    return daten
