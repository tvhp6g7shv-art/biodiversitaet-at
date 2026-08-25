"""
Farmland Bird Index Österreich — Bestandsindex der Feld- und Wiesenvögel.

GEPFLEGTE REIHE. Die Werte stammen aus Tabelle 5 des Jahresberichts und
sind hier abgeschrieben, nicht abgerufen: BirdLife veröffentlicht den
Index als PDF ohne Datenanhang.

  Quelle:   Teufelbauer, N. & Seaman, B. (2024): Farmland Bird Index für
            Österreich — Indikator 2023. BirdLife Österreich im Auftrag
            des BMLUK, Wien, Juni 2024, Tab. 5, S. 10–11.
  PDF:      https://assets.ctfassets.net/2oszne1tuxgg/17MCMmQOSsxbYx1QhJMbOI/
            c46a08bb5031187124ddafdbeccc43fc/2024_Bericht_Farmland_Bird_Index_2023.pdf
  Abgerufen: 24.08.2026
  Basis:    1998 = 100, geometrisches Mittel, Verkettung nach Marchant et al. (1990)

Wenn ein neuer Bericht erscheint: unten die Jahre ergänzen, STAND_JAHR
hochsetzen, sonst nichts. Die Pipeline meldet von selbst, wenn die Reihe
älter wird als der erwartete Rhythmus.

Zu den drei Arten mit spätem Beginn (Heidelerche, Bergpieper, Steinschmätzer,
Datenlage erst ab 2008) siehe Bericht — sie sind im Gesamtindex enthalten,
ihre Teilreihen beginnen aber bei 2008 = 100. Für den Gesamtindex ist das
bereits verrechnet; hier steht nur das Ergebnis.
"""

from __future__ import annotations

import config
from gemeinsam import (jsonstat_reihe, lade_json, log, pflegepruefung,
                       quelle_vermerken, warnen)

STAND_JAHR = 2023          # letztes Jahr mit Indexwert
BERICHT_JAHR = 2024        # Erscheinungsjahr des Berichts

# Jahr -> Indexwert (Basis 1998 = 100)
REIHE: dict[int, float] = {
    1998: 100.0, 1999: 102.5, 2000: 98.5, 2001: 91.5, 2002: 93.0,
    2003: 88.1,  2004: 90.7,  2005: 92.8, 2006: 85.2, 2007: 82.6,
    2008: 79.8,  2009: 73.9,  2010: 71.0, 2011: 68.5, 2012: 69.5,
    2013: 63.6,  2014: 60.3,  2015: 63.5, 2016: 58.9, 2017: 61.8,
    2018: 56.2,  2019: 62.4,  2020: 62.7, 2021: 61.5, 2022: 54.3,
    2023: 56.8,
}

# 23 Indikatorarten. Ursprünglich 24 ausgewählt; der Zitronenzeisig wird
# wegen zu geringer Stichprobe nie einbezogen und fehlt deshalb hier.
ARTEN = [
    "Rebhuhn", "Turteltaube", "Kiebitz", "Wendehals", "Turmfalke",
    "Neuntöter", "Heidelerche", "Feldlerche", "Sumpfrohrsänger",
    "Dorngrasmücke", "Star", "Wacholderdrossel", "Braunkehlchen",
    "Schwarzkehlchen", "Steinschmätzer", "Feldsperling", "Baumpieper",
    "Bergpieper", "Bluthänfling", "Stieglitz", "Girlitz", "Grauammer",
    "Goldammer",
]

# Langzeittrend 1998–2023, ausgewertet für die 20 Arten mit durchgehender
# Datenreihe (Bericht, Tab. 6): 15 rückläufig, 3 stabil, 2 zunehmend.
TREND = {"rueckgang": 15, "stabil": 3, "zunahme": 2, "bewertet": 20}


def hole_eu_reihe(basisjahr: int) -> tuple[dict[int, float], int | None]:
    """
    EU-Vergleichsreihe (sdg_15_60, gemeine Feldvogelarten), umbasiert auf
    dasselbe Basisjahr wie die österreichische Reihe.

    WARUM UMBASIERT WERDEN MUSS: Eurostat liefert die EU-Reihe mit
    Basis 2000 = 100, BirdLife die österreichische mit 1998 = 100. Beide
    Kurven unverändert in ein Diagramm zu legen wäre der klassische
    stille Fehler — sie sähen vergleichbar aus und wären es nicht. Die
    Umbasierung teilt jeden EU-Wert durch den EU-Wert des österreichischen
    Basisjahres. Das ist zulässig, weil ein Kettenindex bezugsjahrfrei ist:
    das Verhältnis zweier Jahre bleibt gleich, egal welches auf 100 steht.

    Der Vergleich bleibt trotzdem einer mit Vorbehalt, und der Hinweistext
    sagt das: Die EU-Reihe umfasst 39 Arten aus 26 Mitgliedstaaten, die
    österreichische 23 Arten. Gleiche Richtung, nicht gleiche Messgröße.
    """
    log("    EU-Vergleichsreihe holen")
    url = f"{config.EUROSTAT_BASIS}/{config.VOGEL_EU_CODE}"
    # `unit="I00"` steht schon in den Abfrageparametern. Hier trotzdem noch
    # einmal als Filter: Verlässt sich der Code allein auf den Server und der
    # ignoriert den Parameter, liegen zwei Reihen hintereinander im selben
    # Wertefeld — und die Kurve sähe plausibel aus, wäre aber falsch. Der
    # doppelte Riegel kostet nichts.
    roh = jsonstat_reihe(
        lade_json(url, config.VOGEL_EU_PARAMS), "sdg_15_60 (EU, Feldvögel)",
        unit="I00",
    )
    if not roh:
        warnen("EU-Vogelreihe leer — der Abschnitt zeigt nur Österreich")
        return {}, None

    reihe = {int(j): w for j, w in roh.items()}
    anker = reihe.get(basisjahr)
    if not anker:
        warnen(
            f"EU-Vogelreihe hat keinen Wert für {basisjahr} — ohne gemeinsames "
            f"Basisjahr wäre der Vergleich irreführend, die EU-Linie entfällt"
        )
        return {}, None

    umbasiert = {j: round(w / anker * 100, 1) for j, w in reihe.items()}
    log(f"    EU umbasiert auf {basisjahr} = 100 (Anker war {anker})")
    return umbasiert, max(umbasiert)


def baue_vogel() -> dict:
    log("\n[2/8] Feld- und Wiesenvögel — Farmland Bird Index (gepflegt + EU-API)")

    jahre = sorted(REIHE)
    start, ende = jahre[0], jahre[-1]

    eu, eu_ende = hole_eu_reihe(start)
    # Die EU-Reihe reicht weiter als die österreichische. Beide über die
    # gemeinsame Achse führen, aber jede nur so weit, wie sie Werte hat —
    # `None` lässt ECharts die Linie enden statt sie auf null zu ziehen.
    alle_jahre = sorted(set(jahre) | set(eu)) if eu else jahre
    punkte = [
        {
            "jahr": jahr,
            "index": REIHE.get(jahr),
            "eu": eu.get(jahr) if eu else None,
        }
        for jahr in alle_jahre
    ]
    aktuell = REIHE[ende]
    verlust = round(100 - aktuell, 1)

    # Der Bericht beschreibt zwei Phasen: starker Rückgang in den ersten
    # rund 15 Jahren, danach flach auf niedrigem Niveau. Den Knickpunkt
    # nicht behaupten, sondern suchen: das Jahr, ab dem der Index seinen
    # Tiefbereich nicht mehr verlässt. Operationalisiert als das erste Jahr,
    # ab dem kein Wert mehr über dem Mittel der zweiten Hälfte + 5 Punkte liegt.
    mitte = len(jahre) // 2
    niveau_spaet = sum(REIHE[j] for j in jahre[mitte:]) / len(jahre[mitte:])
    schwelle = niveau_spaet + 5
    knick = ende
    for i, jahr in enumerate(jahre):
        if all(REIHE[j] <= schwelle for j in jahre[i:]):
            knick = jahr
            break

    tiefstwert = min(REIHE.values())
    tiefstjahr = min(REIHE, key=REIHE.get)

    log(f"    {start}: {REIHE[start]:.1f}  →  {ende}: {aktuell:.1f}  "
        f"({verlust:.1f} Punkte Verlust)")
    log(f"    Tiefpunkt {tiefstjahr}: {tiefstwert:.1f}")
    log(f"    Ab {knick} bleibt der Index im Tiefbereich (Schwelle {schwelle:.1f})")
    pflegepruefung("vogel", BERICHT_JAHR, "Farmland Bird Index")

    quelle_vermerken(
        name=("BirdLife Österreich / BMLUK — Farmland Bird Index für "
              "Österreich, Indikator 2023"),
        url=("https://www.bmluk.gv.at/themen/landwirtschaft/bildung-forschung/"
             "Online-Fachzeitschrift-Laendlicher-Raum/archiv/2010/Teufelbauer.html"),
        lizenz="Quellenangabe laut Bericht",
        stand=str(STAND_JAHR),
        art="gepflegt",
    )
    if eu:
        quelle_vermerken(
            name=("Eurostat — sdg_15_60, Index weit verbreiteter Vogelarten "
                  "(gemeine Feldvogelarten, EU-Aggregat)"),
            url="https://ec.europa.eu/eurostat/databrowser/view/sdg_15_60",
            lizenz="Eurostat-Nutzungsbedingungen",
            stand=str(eu_ende),
            art="api",
        )

    # Wie steht Österreich zur EU? Nur für ein Jahr, das beide führen.
    eu_vergleich = None
    if eu:
        gemeinsam = sorted(set(REIHE) & set(eu))
        if gemeinsam:
            jahr = gemeinsam[-1]
            eu_vergleich = {
                "jahr": jahr,
                "at": REIHE[jahr],
                "eu": eu[jahr],
                "differenz": round(REIHE[jahr] - eu[jahr], 1),
            }
            log(f"    {jahr}: Österreich {REIHE[jahr]:.1f} · EU {eu[jahr]:.1f} "
                f"({eu_vergleich['differenz']:+.1f} Punkte)")

    return {
        "punkte": punkte,
        "beginn": start,
        "stand": ende,
        "aktuell": aktuell,
        "verlust": verlust,
        "knick": knick,
        "tiefstwert": tiefstwert,
        "tiefstjahr": tiefstjahr,
        "arten_anzahl": len(ARTEN),
        "arten": ARTEN,
        "trend": TREND,
        "eu_vorhanden": bool(eu),
        "eu_stand": eu_ende,
        "eu_arten": 39,
        "eu_vergleich": eu_vergleich,
        "pflege": {
            "art": "gepflegt",
            "quelle": ("Teufelbauer, N. & Seaman, B. (2024): Farmland Bird Index "
                       "für Österreich — Indikator 2023. BirdLife Österreich "
                       "im Auftrag des BMLUK, Wien, Juni 2024, Tab. 5."),
            "bericht_jahr": BERICHT_JAHR,
            "abgerufen": "2026-08-24",
        },
        "hinweis": (
            f"Bestandsindex von {len(ARTEN)} Vogelarten des Offenlands, "
            f"{start} = 100. Er misst Häufigkeit, nicht Artenzahl. Die "
            f"EU-Linie zählt 39 Arten aus 26 Staaten, auf dasselbe Basisjahr "
            f"umgerechnet — gleiche Richtung, nicht dieselbe Messgröße."
        ) if eu else (
            f"Bestandsindex von {len(ARTEN)} Vogelarten des Offenlands, "
            f"{start} = 100. Er misst Häufigkeit, nicht Artenzahl: eine Art "
            f"kann seltener werden, ohne zu verschwinden."
        ),
    }
