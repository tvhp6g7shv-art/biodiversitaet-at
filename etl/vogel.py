"""
Farmland Bird Index Österreich — Bestandsindex der Feld- und Wiesenvögel.

GEPFLEGTE REIHE. Die Werte stammen aus Tabelle 5 des Jahresberichts und
sind hier abgeschrieben, nicht abgerufen: BirdLife veröffentlicht den
Index als PDF ohne Datenanhang.

  Quelle 1998–2024: Teufelbauer, N. & Seaman, B. (2025): Farmland Bird
            Index für Österreich: Indikator 2023 bis 2029 — Teilbericht
            Indikator 2024. BirdLife Österreich im Auftrag des BMLUK,
            Wien, Juni 2025, Tab. 5, S. 11.
  PDF:      https://assets.ctfassets.net/2oszne1tuxgg/1VXG9IG1FC9Xr8QY7v4ikd/
            6b6bf8bbaa8760acab8bae5d2cd25bc5/BirdLife_Österreich_Bericht_
            Farmland_Bird_Index_2024.pdf
  Quelle 2025: Presseaussendung BirdLife Österreich vom 10.08.2026 zum
            Bericht Indikator 2025 („Der Indexwert für das Jahr 2025 ist
            mit 53,3 Prozent der niedrigste seit 1998").
  URL:      https://www.birdlife.at/artikel/oesterreichs-feld-und-
            wiesenvoegel-im-tiefflug-weiteres-hoffen-auf-trendumkehr/
  Abgerufen: 26.08.2026
  Basis:    1998 = 100, geometrisches Mittel, Verkettung nach Marchant et al. (1990)

DIE REIHE IST EINE MISCHREIHE — UND DAS HAT EINE FOLGE

BirdLife rechnet den Index jedes Jahr komplett neu; ältere Jahre
verschieben sich dabei um Zehntel. Hier stehen 1998–2024 aus dem Bericht
2024 und 2025 aus der Aussendung von 2026 nebeneinander. Der Bericht
2025 selbst liegt nur in der Pressemappe (ZIP, 48 MB) und ist noch nicht
eingearbeitet.

Konkret gefährlich ist genau eine Aussage: 2025 steht bei 53,3 und 2022
bei 53,6 — **drei Zehntel Abstand über zwei Berichtsjahrgänge hinweg**.
„Niedrigster Wert seit 1998" ist deshalb als **Aussage von BirdLife** zu
führen, nicht als eigene Rechnung. `_tiefpunkt_pruefen()` meldet die Lage
bei jedem Lauf.

Wenn ein neuer Bericht erscheint: unten die Jahre ergänzen, STAND_JAHR
hochsetzen, sonst nichts. **Der Bericht erscheint jährlich Ende Juli /
Anfang August** als Presseaussendung auf birdlife.at/artikel/ — die
Pipeline meldet von selbst, wenn die Reihe älter wird als der Rhythmus.

Zu den drei Arten mit spätem Beginn (Heidelerche, Bergpieper, Steinschmätzer,
Datenlage erst ab 2008) siehe Bericht — sie sind im Gesamtindex enthalten,
ihre Teilreihen beginnen aber bei 2008 = 100. Für den Gesamtindex ist das
bereits verrechnet; hier steht nur das Ergebnis.
"""

from __future__ import annotations

import config
from gemeinsam import (jsonstat_reihe, lade_json, log, pflegepruefung,
                       quelle_vermerken, warnen)

STAND_JAHR = 2025          # letztes Jahr mit Indexwert
BERICHT_JAHR = 2026        # Erscheinungsjahr der jüngsten Veröffentlichung

# Jahr, ab dem die Werte aus einer anderen Veröffentlichung stammen als
# der Rest der Reihe. Siehe Docstring, Abschnitt „Mischreihe".
MISCHREIHE_AB = 2025

# Jahr -> Indexwert (Basis 1998 = 100)
REIHE: dict[int, float] = {
    1998: 100.0, 1999: 102.2, 2000: 98.4, 2001: 91.3, 2002: 92.7,
    2003: 87.8,  2004: 90.5,  2005: 92.6, 2006: 85.2, 2007: 82.4,
    2008: 79.5,  2009: 73.8,  2010: 70.9, 2011: 68.3, 2012: 69.4,
    2013: 63.5,  2014: 60.2,  2015: 63.3, 2016: 58.8, 2017: 61.6,
    2018: 56.0,  2019: 62.1,  2020: 62.4, 2021: 61.2, 2022: 53.6,
    2023: 56.8,  2024: 56.1,
    2025: 53.3,   # Presseaussendung 10.08.2026, nicht aus Tab. 5
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

# Langzeittrend 1998–2025, ausgewertet für die 20 Arten mit durchgehender
# Datenreihe: 14 rückläufig, 4 stabil, 2 zunehmend. Gegenüber dem Stand
# 1998–2023 ist der Neuntöter von „Abnahme" zu „stabil" gewandert.
# Beleg: Teufelbauer & Seaman (2026), BVM-Bericht Saison 2025, Tab. 3;
# gleichlautend die Presseaussendung vom 10.08.2026.
TREND = {"rueckgang": 14, "stabil": 4, "zunahme": 2, "bewertet": 20}


def _tiefpunkt_pruefen(reihe: dict[int, float], tiefstjahr: int) -> None:
    """
    Meldet, wenn der Tiefpunkt nur knapp vor dem zweitniedrigsten Jahr
    liegt und die beiden aus verschiedenen Veröffentlichungen stammen.

    Ohne diese Prüfung würde die Aussage „niedrigster Wert seit 1998" auf
    einem Abstand ruhen, der kleiner ist als die Verschiebung, die eine
    Neuberechnung ohnehin erzeugt.
    """
    sortiert = sorted(reihe.values())
    if len(sortiert) < 2:
        return
    abstand = round(sortiert[1] - sortiert[0], 1)
    gemischt = (tiefstjahr >= MISCHREIHE_AB) != (
        min(reihe, key=lambda j: abs(reihe[j] - sortiert[1])) >= MISCHREIHE_AB
    )
    if abstand < 1.0 and gemischt:
        warnen(
            f"Farmland Bird Index: Der Tiefpunkt {tiefstjahr} liegt nur "
            f"{abstand} Punkte unter dem zweitniedrigsten Jahr, und beide "
            f"stammen aus verschiedenen Berichtsjahrgängen. „Niedrigster "
            f"Wert seit 1998\" nur als Aussage von BirdLife führen, nicht "
            f"als eigene Rechnung."
        )


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
    log("\n[2/11] Feld- und Wiesenvögel — Farmland Bird Index (gepflegt + EU-API)")

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
    _tiefpunkt_pruefen(REIHE, tiefstjahr)

    log(f"    {start}: {REIHE[start]:.1f}  →  {ende}: {aktuell:.1f}  "
        f"({verlust:.1f} Punkte Verlust)")
    log(f"    Tiefpunkt {tiefstjahr}: {tiefstwert:.1f}")
    log(f"    Ab {knick} bleibt der Index im Tiefbereich (Schwelle {schwelle:.1f})")
    pflegepruefung("vogel", BERICHT_JAHR, "Farmland Bird Index")

    quelle_vermerken(
        name=("BirdLife Österreich / BMLUK — Farmland Bird Index für "
              "Österreich, Indikator 2024 und Aussendung Indikator 2025"),
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
        "mischreihe_ab": MISCHREIHE_AB,
        "pflege": {
            "art": "gepflegt",
            "quelle": ("1998–2024: Teufelbauer, N. & Seaman, B. (2025): Farmland "
                       "Bird Index für Österreich — Teilbericht Indikator 2024. "
                       "BirdLife Österreich im Auftrag des BMLUK, Wien, Juni "
                       "2025, Tab. 5, S. 11. — 2025: Presseaussendung BirdLife "
                       "Österreich vom 10.08.2026 zum Bericht Indikator 2025. "
                       "Der Index wird jährlich neu gerechnet; ältere Jahre "
                       "können sich um Zehntel verschieben."),
            "bericht_jahr": BERICHT_JAHR,
            "abgerufen": "2026-08-26",
        },
        # 28.08.2026 — der erste Satz stand fast wörtlich schon in der
        # Unterzeile („23 Vogelarten … 1998 = 100"), und mit ihm die zwei
        # Fachbegriffe, die am 25.08. aus eben dieser Unterzeile entfernt
        # wurden: „Bestandsindex" und „Offenland". Was hier bleibt, ist
        # das, was NICHT anderswo steht.
        "hinweis": (
            "Gezählt wird Häufigkeit, nicht Artenzahl — ein Rückgang heißt "
            "weniger Vögel, nicht weniger Arten. Die EU-Linie zählt 39 Arten "
            "aus 26 Staaten, auf dasselbe Basisjahr umgerechnet: gleiche "
            "Richtung, nicht dieselbe Messgröße."
        ) if eu else (
            "Gezählt wird Häufigkeit, nicht Artenzahl — eine Art kann "
            "seltener werden, ohne zu verschwinden. Der Wert sagt also, wie "
            "viele Vögel unterwegs sind, nicht wie viele Arten es noch gibt."
        ),
    }
