"""
Wiesenfalter in Europa — Grünland-Schmetterlingsindex, 1991 = 100.

API-REIHE. Eurostat sdg_15_61 wird bei jedem Lauf frisch geholt. Die
Werte darin stammen von Butterfly Conservation Europe und dem European
Butterfly Monitoring Scheme; die EEA führt denselben Indikator als
SEBI 028.

  Code:      sdg_15_61 — Grassland butterfly index
  Quelle:    European Environment Agency; Butterfly Conservation Europe
  Bericht:   EU Grassland Butterfly Index 1991–2024 (VS2025.023)
  PDF:       https://butterfly-monitoring.net/sites/default/files/Publications/
             VS2025.023%20EU%20Grassland%20Butterfly%20Index%201991-2024.pdf
  Abgerufen: 26.08.2026

WARUM DIESE REIHE HIER EUROPÄISCH IST UND NICHT ÖSTERREICHISCH

Die Tabelle kennt genau ein Gebiet: `geo = EU_V`. Länderwerte gibt es
nicht — auch nicht auf Umwegen. Österreich ist am Monitoring beteiligt
(Viel-Falter, Universität Innsbruck, nationaler eBMS-Partner seit 2020,
seit 2023 rund 480 Standorte), aber die österreichische Reihe ist erst
wenige Jahre lang. Für einen Verlauf ab 1991 taugt sie nicht.

Das gehört in die Hinweiszeile und steht dort auch. Eine europäische Zahl
als österreichische auszugeben wäre der stillste und schwerste Fehler,
den dieser Abschnitt machen könnte.

ZWEI FALLEN IN DER ABFRAGE

1. `statinfo` hat zwei Kategorien: NSME (ungeglättet) und SME (geglättet).
   Ohne Filter liegen beide Reihen im selben Wertefeld. Wir nehmen SME.
   Die ungeglättete Reihe schwankt wetterbedingt um bis zu zwanzig Punkte
   im Jahr (2002 steht bei 103,6, 2024 bei 44,3) — als Dashboard-Linie
   erzählt sie Wetter, nicht Bestand.

2. `unit` hat ebenfalls zwei Kategorien: I91 (1991 = 100) und I00
   (2000 = 100). Wir nehmen I91, weil 1991 der Beginn der Reihe ist und
   die Achse dann bei ihrem eigenen Anfang verankert ist.

Zusammen sind das vier Reihen in einer Antwort. `jsonstat_reihe` bricht
ab, wenn der Filter mehr als eine übrig lässt — das ist hier die
eigentliche Schutzvorrichtung, nicht die Sorgfalt beim Schreiben.
"""

from __future__ import annotations

import config
from gemeinsam import (jsonstat_reihe, lade_json, log, quelle_vermerken,
                       warnen)

BASIS_JAHR = 1991
BERICHT_JAHR = 2025        # Erscheinungsjahr des technischen Berichts

# Notreihe. Sie wird NUR benutzt, wenn die Eurostat-Abfrage scheitert —
# dann steht der Abschnitt mit einem belegten, aber womöglich veralteten
# Stand da, statt zu verschwinden. Abgerufen 26.08.2026, geglättet,
# 1991 = 100. Wird die Reihe benutzt, meldet das Modul es laut.
NOTREIHE: dict[int, float] = {
    1991: 100.00, 1992: 97.88, 1993: 95.83, 1994: 93.83, 1995: 91.89,
    1996: 90.01, 1997: 88.16, 1998: 86.35, 1999: 84.59, 2000: 82.93,
    2001: 81.37, 2002: 79.83, 2003: 78.22, 2004: 76.23, 2005: 73.94,
    2006: 71.79, 2007: 70.15, 2008: 69.18, 2009: 68.67, 2010: 68.41,
    2011: 68.18, 2012: 67.80, 2013: 67.39, 2014: 67.05, 2015: 66.56,
    2016: 65.72, 2017: 64.60, 2018: 63.35, 2019: 61.96, 2020: 60.38,
    2021: 58.63, 2022: 56.74, 2023: 54.74, 2024: 52.65,
}


def _reihe_holen() -> tuple[dict[int, float], str]:
    """Liefert (Reihe, Art). Art ist "api" oder "notreihe"."""
    try:
        roh = lade_json(
            f"{config.EUROSTAT_BASIS}/{config.FALTER_CODE}",
            config.FALTER_PARAMS,
        )
        reihe = jsonstat_reihe(
            roh, "Wiesenfalter (sdg_15_61)",
            **{k: v for k, v in config.FALTER_FILTER.items()},
        )
        werte = {int(j): round(float(w), 2) for j, w in reihe.items()}
        if werte:
            return werte, "api"
        warnen("Wiesenfalter: Eurostat lieferte eine leere Reihe.")
    except SystemExit:
        raise
    except Exception as fehler:      # noqa: BLE001 — bewusst breit
        warnen(f"Wiesenfalter: Eurostat nicht erreichbar ({fehler}).")

    warnen(
        "Wiesenfalter: Es wird die abgeschriebene Notreihe mit Stand 2024 "
        "gezeigt. Bitte nachsehen, ob sdg_15_61 sich geändert hat."
    )
    return dict(NOTREIHE), "notreihe"


def baue_falter() -> dict:
    log("\n[9/11] Wiesenfalter — Grünland-Schmetterlingsindex (Eurostat API)")

    werte, art = _reihe_holen()

    # Die Basis muss 100 sein. Ist sie es nicht, hat die Abfrage die
    # falsche `unit` erwischt — das wäre eine stille Verschiebung der
    # ganzen Kurve und darf nicht unbemerkt durchgehen.
    start = werte.get(BASIS_JAHR)
    if start is None:
        warnen(f"Wiesenfalter: Kein Wert für das Basisjahr {BASIS_JAHR}.")
    elif abs(start - 100.0) > 0.5:
        warnen(
            f"Wiesenfalter: {BASIS_JAHR} steht bei {start} statt bei 100 — "
            f"vermutlich wurde die Reihe mit Basis 2000 (unit=I00) geholt."
        )

    jahre = sorted(werte)
    stand = jahre[-1]
    aktuell = werte[stand]
    verlust = round(100.0 - aktuell, 1)

    # Halbierungsjahr: das erste Jahr, ab dem der Index 50 oder weniger
    # zeigt. Aus den Daten gelesen, nicht gesetzt — solange er darüber
    # liegt, bleibt das Feld leer und die Marke im Diagramm aus.
    halbiert = next((j for j in jahre if werte[j] <= 50.0), None)

    # Lücken melden, statt sie zu überbrücken.
    fehlend = [j for j in range(jahre[0], stand + 1) if j not in werte]
    if fehlend:
        warnen(f"Wiesenfalter: Jahre ohne Wert: {fehlend}")

    log(f"    {jahre[0]}–{stand}: {aktuell} (−{verlust} Punkte seit "
        f"{BASIS_JAHR}) · Quelle: {art}")

    quelle_vermerken(
        name="Eurostat sdg_15_61 — Grünland-Schmetterlingsindex (EEA/BCE)",
        url="https://ec.europa.eu/eurostat/databrowser/view/sdg_15_61",
        lizenz="Eurostat, Weiterverwendung erlaubt",
        stand=str(stand),
        art="api" if art == "api" else "gepflegt",
    )

    return {
        "punkte": [{"jahr": j, "index": werte[j]} for j in jahre],
        "basis": BASIS_JAHR,
        "beginn": jahre[0],
        "stand": stand,
        "aktuell": aktuell,
        "verlust": verlust,
        "halbiert": halbiert,
        # Beides aus den Eurostat-Metadaten zum Datensatz, wörtlich: „integrates
        # the population trends of 17 butterfly species monitored across the EU
        # and is calculated from data from all 27 EU Member States". Die
        # Länderzahl stand hier bis 26.08.2026 auf 20 — unbelegt.
        "arten_anzahl": 17,
        "laender_anzahl": 27,
        "notreihe": art == "notreihe",
        "pflege": {
            "art": "api" if art == "api" else "gepflegt",
            "quelle": (
                "Eurostat sdg_15_61, geglättete Reihe (statinfo=SME), "
                "1991 = 100. Erhebung: Butterfly Conservation Europe und "
                "European Butterfly Monitoring Scheme; Indikator der "
                "Europäischen Umweltagentur (SEBI 028)."
            ),
            "bericht_jahr": BERICHT_JAHR,
            "abgerufen": "2026-08-26",
        },
        "hinweis": (
            # 159 Zeichen, Fenster 150–234.
            # 28.08.2026: Satz 1 ist entfallen. „Europa, nicht Österreich"
            # steht in der Unterzeile UND in der Notiz darüber, dort mit
            # dem Grund (die österreichische Reihe beginnt erst 2020).
            "Die Linie ist geglättet, weil einzelne Jahre stark vom Wetter "
            "abhängen — ein einzelner Jahreswert sagt hier wenig, die "
            "Richtung über drei Jahrzehnte umso mehr."
        ),
    }
