"""
Fichtenanteil an der Ertragswaldfläche — Österreichische Waldinventur.

WARUM DIESER ABSCHNITT: Die Fichte ist die Baumart, an der sich „Wald ist
nicht gleich Wald" am besten zeigen lässt. Sie steht auf knapp der Hälfte des
österreichischen Ertragswalds, aber nur auf einem Teil davon gehört sie
standörtlich hin. Der Rest ist gepflanzter Wald ausserhalb seines natürlichen
Areals.

DER FALLSTRICK, der diesen Abschnitt fast gekippt hätte:

Die ÖWI rechnet die Baumartenprozente in der Periode 2018/23 gegen den
GESAMTWALD, in 2016/21 dagegen gegen den ERTRAGSWALD. Nachgerechnet:

    2016/21   1.678 / 3.362 (Ertragswald) = 49,9 %   so veröffentlicht
    2018/23   1.598 / 3.356 (Ertragswald) = 47,6 %   NICHT veröffentlicht
    2018/23   1.598 / 4.018 (Gesamtwald)  = 39,8 %   so veröffentlicht

Wer die veröffentlichten Prozentwerte nebeneinanderstellt, zeigt einen
Einbruch von zehn Prozentpunkten in zwei Jahren, den es nicht gibt — die
Fläche selbst geht nur von 1.678 auf 1.598 Tsd ha zurück. Dieses Modul rechnet
die Anteile deshalb IMMER selbst aus Fichtenfläche und Ertragswaldfläche.
Das Feld `_Proz` der Quelle wird bewusst nicht verwendet.

WAS NICHT HOCHGERECHNET WERDEN DARF: Die Angabe, dass die Fichte „auf etwa
60 % ihrer derzeitigen Fläche" standortsgerecht steht, stammt aus einer
Auswertung von 2013 auf Basis ÖWI 2007/09, als die Fichtenfläche bei rund
2,17 Mio ha lag. Heute sind es 1,598 Mio ha. Das Verhältnis auf die heutige
Fläche anzuwenden wäre eine Erfindung. Der belegte Wert ist die absolute
Angabe: 1,3 Mio ha bzw. rund ein Drittel der nationalen Waldfläche.

Ebenfalls aus derselben Quelle stammt die Angabe „etwa 20 % der
Verbreitungsfläche standortsfremd". 60 + 20 ergibt nicht 100 — die beiden
Zahlen dürfen nie gemeinsam in einer Grafik stehen.

Abgerufen und nachgerechnet am 27.08.2026.
"""

from __future__ import annotations

import config
from gemeinsam import log, pflegepruefung, quelle_vermerken, warnen

# ---------------------------------------------------------------------------
# Rohwerte in Tausend Hektar, Quelle waldinventur.at
#   Fichtenfläche   Indikator 22_01_A, Feld `_Wert`
#   Ertragswald     Indikator 1_l,     Feld `_Wert`
# Die Prozentwerte werden daraus gerechnet, nicht abgeschrieben.
# ---------------------------------------------------------------------------
FICHTE_TSD_HA = {
    "2007/09": {"Österreich": 1709, "Burgenland": 19, "Kärnten": 302,
                "Niederösterreich": 271, "Oberösterreich": 237, "Salzburg": 153,
                "Steiermark": 498, "Tirol": 200, "Vorarlberg": 31, "Wien": 0},
    "2016/21": {"Österreich": 1678, "Burgenland": 16, "Kärnten": 296,
                "Niederösterreich": 256, "Oberösterreich": 221, "Salzburg": 157,
                "Steiermark": 494, "Tirol": 206, "Vorarlberg": 33, "Wien": 0},
    "2018/23": {"Österreich": 1598, "Burgenland": 16, "Kärnten": 284,
                "Niederösterreich": 243, "Oberösterreich": 215, "Salzburg": 149,
                "Steiermark": 475, "Tirol": 189, "Vorarlberg": 29, "Wien": 0},
}

ERTRAGSWALD_TSD_HA = {
    "2007/09": {"Österreich": 3367, "Burgenland": 131, "Kärnten": 505,
                "Niederösterreich": 733, "Oberösterreich": 444, "Salzburg": 276,
                "Steiermark": 862, "Tirol": 347, "Vorarlberg": 62, "Wien": 9},
    "2016/21": {"Österreich": 3362, "Burgenland": 131, "Kärnten": 500,
                "Niederösterreich": 736, "Oberösterreich": 444, "Salzburg": 272,
                "Steiermark": 862, "Tirol": 347, "Vorarlberg": 63, "Wien": 9},
    "2018/23": {"Österreich": 3356, "Burgenland": 130, "Kärnten": 499,
                "Niederösterreich": 735, "Oberösterreich": 444, "Salzburg": 271,
                "Steiermark": 860, "Tirol": 347, "Vorarlberg": 62, "Wien": 9},
}

PERIODEN = ["2007/09", "2016/21", "2018/23"]

# ---------------------------------------------------------------------------
# Fichte am natürlichen Standort — eigene Bezugsgrösse, eigener Datenstand.
# Quelle: FichtePLUS (BFW), wörtlich wiederholt in BFW-Praxisinfo 58 (2025),
# Datengrundlage ÖWI 2007/09.
# ---------------------------------------------------------------------------
NATUERLICHER_STANDORT = {
    "flaeche_mio_ha": 1.3,
    "anteil_waldflaeche": "rund ein Drittel",
    "datenstand": "ÖWI 2007/09, Auswertung 2013",
}

# Die veröffentlichten Prozentwerte der Quelle, nur zur Gegenprobe.
# Stimmen sie nicht mehr mit der eigenen Rechnung überein, hat sich die
# Bezugsgrösse der Quelle geändert — dann ist dieses Modul zu prüfen.
KONTROLLE_VEROEFFENTLICHT = {"2007/09": 50.7, "2016/21": 49.9}


def _anteil(periode: str, region: str) -> float | None:
    """Fichtenanteil am Ertragswald in Prozent, selbst gerechnet."""
    nenner = ERTRAGSWALD_TSD_HA[periode].get(region)
    zaehler = FICHTE_TSD_HA[periode].get(region)
    if not nenner or zaehler is None:
        return None
    return zaehler / nenner * 100


def baue_fichte() -> dict | None:
    log("\n[13/13] Fichte — ÖWI, Anteil am Ertragswald (gepflegt)")

    pflegepruefung("fichte", 2025, "ÖWI-Zwischenauswertung 2018/23")

    # Gegenprobe: eigene Rechnung gegen die veröffentlichten Prozentwerte.
    # Toleranz 0,15 Punkte, weil die Quelle auf eine Nachkommastelle rundet
    # und die Flächen selbst schon gerundet vorliegen.
    for periode, veroeffentlicht in KONTROLLE_VEROEFFENTLICHT.items():
        eigen = _anteil(periode, "Österreich")
        if eigen is None or abs(eigen - veroeffentlicht) > 0.15:
            warnen(
                f"Fichte: eigene Rechnung {eigen:.1f} % weicht für {periode} von "
                f"den veröffentlichten {veroeffentlicht} % ab — Bezugsgrösse der "
                f"Quelle prüfen"
            )

    aktuell, frueher = PERIODEN[-1], PERIODEN[0]

    regionen = [r for r in ERTRAGSWALD_TSD_HA[aktuell] if r != "Österreich"]
    eintraege = []
    for region in regionen:
        jetzt = _anteil(aktuell, region)
        damals = _anteil(frueher, region)
        if jetzt is None:
            continue
        eintraege.append({
            "name": region,
            "anteil": round(jetzt, 1),
            "anteil_frueher": round(damals, 1) if damals is not None else None,
            "veraenderung": round(jetzt - damals, 1) if damals is not None else None,
            "flaeche_tsd_ha": FICHTE_TSD_HA[aktuell][region],
            # Wien hat keinen messbaren Fichtenbestand. Ein Nullbalken neben
            # acht echten Werten sieht nach fehlenden Daten aus, ist aber ein
            # Befund — das Frontend soll ihn kennzeichnen können.
            "ohne_bestand": FICHTE_TSD_HA[aktuell][region] == 0,
        })
    eintraege.sort(key=lambda e: -e["anteil"])

    bund_jetzt = _anteil(aktuell, "Österreich")
    bund_damals = _anteil(frueher, "Österreich")

    reihe_bund = [
        {"periode": p, "anteil": round(_anteil(p, "Österreich"), 1),
         "flaeche_tsd_ha": FICHTE_TSD_HA[p]["Österreich"]}
        for p in PERIODEN
    ]

    daten = {
        "stand": f"ÖWI {aktuell}",
        "abgerufen": "2026-08-27",
        "perioden": PERIODEN,
        "reihe_bund": reihe_bund,
        "bund_anteil": round(bund_jetzt, 1),
        "bund_anteil_frueher": round(bund_damals, 1),
        "bund_veraenderung": round(bund_jetzt - bund_damals, 1),
        "bund_flaeche_tsd_ha": FICHTE_TSD_HA[aktuell]["Österreich"],
        "flaeche_rueckgang_prozent": round(
            (FICHTE_TSD_HA[aktuell]["Österreich"] / FICHTE_TSD_HA[frueher]["Österreich"] - 1) * 100, 1),
        "eintraege": eintraege,
        "natuerlicher_standort": NATUERLICHER_STANDORT,
        # Einordnung unter der Grafik, Konvention 150–234 Zeichen. Gemessen: 196.
        "hinweis": (
            "Anteile gegen den bewirtschafteten Wald gerechnet, nicht gegen die "
            "gesamte Waldfläche — nur so sind die Perioden vergleichbar. Wo die "
            "Fichte hingehört, stammt aus einer Auswertung von 2007/09."
        ),
    }

    quelle_vermerken(
        "Fichtenanteil am Ertragswald",
        "https://www.waldinventur.at/",
        "BFW — Verwendung mit Quellenangabe, Zustimmung des BFW vom 30.09.2026",
        f"ÖWI {aktuell}",
        "gepflegt",
    )

    log(f"  Bund {daten['bund_anteil']} % ({daten['bund_veraenderung']:+} Pkt seit "
        f"{frueher}) · {len(eintraege)} Regionen")

    return daten
