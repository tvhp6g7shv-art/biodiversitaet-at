"""
Ökologischer Zustand der Fließgewässer — einmal nach Wasserkörpern, einmal
nach Flusskilometern.

WARUM DIESER ABSCHNITT: Dieselbe Meldung, dieselben 8.116 Wasserkörper,
dasselbe Jahr — und zwei verschiedene Antworten auf die Frage, wie es
Österreichs Flüssen geht.

    nach Wasserkörpern   49,1 % gut oder besser
    nach Flusskilometern 42,5 % gut oder besser

Beide Zahlen sind richtig. Der Abstand von 6,6 Punkten ist kein Rundungsrest
und keine Methodenfrage, sondern ein Befund: **die Wasserkörper in schlechtem
Zustand sind die längeren.**

    sehr gut         2,97 km im Mittel
    gut              3,71 km
    mäßig            4,36 km
    unbefriedigend   4,46 km
    schlecht         6,10 km

Von der besten zur schlechtesten Klasse verdoppelt sich die mittlere Länge.
Das ist keine Laune der Abgrenzung: Ein Wasserkörper wird dort geteilt, wo
sich Typ oder Belastung ändern. Kurze Körper stehen im Oberlauf, wo wenig
passiert; lange Körper sind die durchgehend verbauten Tal- und Flachstrecken.
Wer nach Kilometern misst, gewichtet die belasteten Strecken so, wie sie im
Gelände liegen — nicht so, wie sie gezählt werden.

DER FEHLER, DEN DIESER ABSCHNITT VERHINDERN SOLL: „Fast die Hälfte ist in
gutem Zustand" als Aussage über das Gewässernetz zu lesen. Über das Netz
gerechnet sind es 42,5 %, und die 49,1 % gelten für eine Zähleinheit, deren
Größe selbst mit dem Zustand zusammenhängt.

WAS DIESER ABSCHNITT NICHT ZEIGT — bewusst:

Die drei Bewertungszyklen (2010: 41,5 %, 2016: 46,2 %, 2022: 49,1 %) sähen
nach stetiger Verbesserung aus. Sie stehen in der Tabelle und in der Notiz,
aber NICHT im Bild. Zwischen den Zyklen haben sich sowohl die Abgrenzung der
Wasserkörper als auch die Bewertungsmethodik geändert — 2010 zählte die
Meldung 7.339 Wasserkörper, 2022 sind es 8.116. Eine Dreipunktreihe daraus
wäre ein Trend, den die Quelle nicht hergibt.

Ebenso wenig ein Europavergleich: Österreich liegt mit 49,1 % auf Rang 8 von
27 Meldeländern. Die Zahl steht in der Notiz. Als Balkengrafik wäre sie der
fünfte Ländervergleich des Dashboards — dieselbe Bauform mit anderer
Beschriftung.

ZWEI GEGENPROBEN GEGEN EINE UNABHÄNGIGE QUELLE, die die ganze Auszählung
tragen. Beide gegen den Nationalen Gewässerbewirtschaftungsplan 2021, also
gegen Österreichs eigene Veröffentlichung statt gegen die EU-Meldung:

  1. Bestand. Der NGP berichtet über Fließgewässer mit Einzugsgebiet über
     10 km², teilt sie in **8.116 Oberflächenwasserkörper** und beziffert das
     Netz mit **32.101 km** (NGP 2021, Abschnitt 1.2.1.1). Discodata liefert
     dieselben 8.116 und 32.135 km.
  2. Wasserkörperarten. Der NGP nennt **12,3 % erheblich veränderte** und
     **1,8 % künstliche** Fließgewässer, längenbezogen. Aus Discodata
     gerechnet: 12,26 % und 1,85 %.

WAS DAMIT WIDERLEGT IST: Die Planungsakte hielt bis 31.08.2026 fest, der NGP
verwende „einen engeren Nenner (oft nur Einzugsgebiete über 10 km²)", die
Zahlen seien deshalb möglicherweise nicht vergleichbar. Das trifft nicht zu.
Das 10-km²-Netz IST der Bestand, den Discodata führt — es gibt keinen
zweiten, weiteren Nenner, gegen den 49,1 % zu relativieren wäre. Die
Einschränkung, die bleibt, ist eine andere und steht unten im Hinweis: unter
10 km² Einzugsgebiet gibt es überhaupt keine flächendeckende Bewertung.

EINE UNSCHÄRFE, DIE DAS FELD SELBST TRÄGT: `swEcologicalStatusOrPotentialValue`
mischt zwei Maßstäbe. Für natürliche Gewässer ist „gut" der gute ZUSTAND, für
erheblich veränderte und künstliche das gute POTENZIAL — ein weicherer
Maßstab, der sich am technisch Möglichen misst. Das Modul rechnet die drei
Arten deshalb getrennt mit und legt sie in die Daten:

    natürlich (7.138 WK)          53,7 % gut oder besser
    erheblich verändert (880)     10,3 %
    künstlich (98)                63,3 %

Zusammengefasst zu einer Zahl bleibt es dabei richtig, dass 49,1 % ihr
jeweiliges Ziel erreichen — nur ist das Ziel nicht für alle dasselbe.

Quelle: EEA Discodata, WISE_WFD, Tabelle SWB_SurfaceWaterBody
(https://discodata.eea.europa.eu/sql), CC BY 4.0. Meldezyklus 2022.
Gegenprobe: Nationaler Gewässerbewirtschaftungsplan 2021, BML.

Abgerufen am 31.08.2026.
"""

from __future__ import annotations

import config
from gemeinsam import log, quelle_vermerken, warnen

# Reihenfolge ist die Leserichtung des gestapelten Balkens: gut nach schlecht.
# Nicht umsortieren — die Farbzuordnung im Frontend hängt an der Position.
# Die Schlüssel sind die Werte, die das Feld liefert; "Unknown" ist einer
# davon und kein Fehlerfall.
KATEGORIEN = [
    {"kuerzel": "1", "name": "sehr gut"},
    {"kuerzel": "2", "name": "gut"},
    {"kuerzel": "3", "name": "mäßig"},
    {"kuerzel": "4", "name": "unbefriedigend"},
    {"kuerzel": "5", "name": "schlecht"},
    {"kuerzel": "Unknown", "name": "unbekannt"},
]

# Die beiden ersten Klassen sind „gut oder besser". Das ist die Schwelle der
# Wasserrahmenrichtlinie, nicht meine Setzung.
ZIEL_KLASSEN = ("1", "2")

# Klartext für die drei Werte des Feldes `naturalAWBHMWB`.
ARTEN = {
    "Natural water body": "natürlich",
    "Heavily modified water body": "erheblich verändert",
    "Artificial water body": "künstlich",
}


def _abfrage(sql: str) -> list[dict] | None:
    """
    Eine Discodata-Abfrage. Zu den vier Fallen der Schnittstelle siehe den
    Block in config.py — die wichtigste steckt schon in den SQL-Zeilen
    unten: die erste Spalte trägt immer einen Alias, und kein ORDER BY
    steht neben einem GROUP BY.

    ABSICHTLICH NICHT `lade_json()`. Der gemeinsame Helfer ruft bei jedem
    Fehlschlag `abbruch()` und beendet damit die GANZE Pipeline — kein
    einziger Abschnitt würde mehr geschrieben. Für Eurostat ist das
    vertretbar; für Discodata nicht:

      * Der Dienst antwortet messbar langsam. Am 31.08.2026 lief ein Abruf
        über ein URL-Werkzeug selbst bei kurzer Abfrage in einen
        180-Sekunden-Zeitablauf. `config.TIMEOUT_SEKUNDEN` steht auf 60 —
        damit wäre ein langsamer Tag bei Discodata ein toter Tag für die
        gesamte Datenaktualisierung.
      * Fällt der Abruf aus, ist der richtige Ausgang nicht „nichts
        schreiben", sondern „diesen einen Abschnitt auslassen". Die zuletzt
        gebaute `fliessgewaesser.json` liegt im Repo und wird weiter
        ausgeliefert; der Rest des Dashboards zieht frisch nach.

    Meldet also `None` statt abzubrechen — und meldet es laut, damit der
    Ausfall im Actions-Log steht und nicht still bleibt.
    """
    import requests

    try:
        antwort = requests.get(
            config.FG_ABFRAGE_URL,
            params={"query": " ".join(sql.split()), "p": 1, "nrOfHits": 2000},
            timeout=config.FG_TIMEOUT_SEKUNDEN,
            headers={"User-Agent": "biodiversitaet-at-dashboard/1.0"},
        )
    except requests.RequestException as fehler:
        warnen(f"Fließgewässer: Discodata nicht erreichbar — {fehler}")
        return None

    if antwort.status_code != 200:
        warnen(
            f"Fließgewässer: Discodata liefert HTTP {antwort.status_code}. "
            f"Erste 200 Zeichen: {antwort.text[:200]!r}"
        )
        return None

    try:
        rohdaten = antwort.json()
    except ValueError:
        warnen(
            f"Fließgewässer: Antwort ist kein JSON. Erste 200 Zeichen: "
            f"{antwort.text[:200]!r}"
        )
        return None

    zeilen = rohdaten.get("results")
    if zeilen is None:
        warnen(
            "Fließgewässer: Antwort ohne Feld `results` — die Schnittstelle "
            f"meldet vermutlich einen Fehler: {str(rohdaten)[:200]}"
        )
        return None
    log(f"  ↓ Discodata: {len(zeilen)} Zeilen")
    return zeilen


def _tabelle() -> str:
    return "[WISE_WFD].[latest].[SWB_SurfaceWaterBody]"


def _anteile(werte: list[float]) -> list[float]:
    nenner = sum(werte)
    if not nenner:
        return [0.0 for _ in werte]
    return [round(w / nenner * 100, 1) for w in werte]


def _summe_ziel(paare: dict[str, float]) -> float:
    return sum(paare.get(k, 0) for k in ZIEL_KLASSEN)


def baue_fliessgewaesser() -> dict | None:
    # Zur Zählung im Kopf: die Schrittzähler dieser Pipeline sind seit der
    # Ausklinkung vom 29.08.2026 uneinheitlich (zwei Module melden [15/15],
    # `lebensraeume` [17/17], `natura2000` [16/16]). Sie einmal geschlossen
    # durchzuzählen ist ein eigener Durchgang und steht im Backlog — hier
    # wird die Reihe nur fortgesetzt, nicht repariert.
    log("\n[18/18] Fließgewässer — Zustand nach Wasserkörpern und nach Länge")

    # --- 1. Der Zyklus, den der Abschnitt zeigt ----------------------------
    zeilen = _abfrage(f"""
        SELECT swEcologicalStatusOrPotentialValue AS v,
               COUNT(*) AS n, SUM(cLength) AS km
        FROM {_tabelle()}
        WHERE countryCode = 'AT'
          AND cYear = {config.FG_ZYKLUS}
          AND surfaceWaterBodyCategory = '{config.FG_KATEGORIE}'
        GROUP BY swEcologicalStatusOrPotentialValue
    """)
    if not zeilen:
        warnen("Fließgewässer: keine Zeilen — Abschnitt wird übersprungen. "
               "Die zuletzt gebaute fliessgewaesser.json bleibt in Kraft.")
        return None

    anzahl = {z["v"]: int(z["n"]) for z in zeilen}
    laenge = {z["v"]: float(z["km"] or 0) for z in zeilen}

    reihenfolge = [k["kuerzel"] for k in KATEGORIEN]
    unbekannte = sorted(set(anzahl) - set(reihenfolge))
    if unbekannte:
        warnen(
            f"Fließgewässer: unerwartete Zustandswerte {unbekannte} — die "
            f"Kategorienliste im Modul ist nicht mehr vollständig"
        )

    zahlen = [anzahl.get(k, 0) for k in reihenfolge]
    kilometer = [round(laenge.get(k, 0.0), 1) for k in reihenfolge]

    wk_gesamt = sum(zahlen)
    km_gesamt = sum(kilometer)

    # --- Gegenprobe 1: der Bestand muss der des NGP sein -------------------
    if wk_gesamt != config.FG_ERWARTET_WASSERKOERPER:
        warnen(
            f"Fließgewässer: {wk_gesamt} Wasserkörper gezählt, der NGP 2021 "
            f"nennt {config.FG_ERWARTET_WASSERKOERPER}. Entweder hat die EEA "
            f"neu gemeldete Daten eingespielt, oder die Abfrage schneidet "
            f"anders zu als gedacht — nachsehen, bevor die Zahl live geht."
        )
    else:
        log(f"    Bestand deckt sich mit dem NGP 2021 ({wk_gesamt} "
            f"Wasserkörper)")

    if abs(km_gesamt - config.FG_ERWARTET_LAENGE_KM) > config.FG_TOLERANZ_LAENGE_KM:
        warnen(
            f"Fließgewässer: Netzlänge {km_gesamt:.0f} km weicht um mehr als "
            f"{config.FG_TOLERANZ_LAENGE_KM} km vom NGP-Wert "
            f"({config.FG_ERWARTET_LAENGE_KM} km) ab"
        )
    else:
        log(f"    Netzlänge deckt sich mit dem NGP 2021 "
            f"({km_gesamt:.0f} gegen {config.FG_ERWARTET_LAENGE_KM} km)")

    anteile_anzahl = _anteile([float(z) for z in zahlen])
    anteile_laenge = _anteile(kilometer)

    gut_anzahl = round(_summe_ziel(
        {k: v for k, v in zip(reihenfolge, anteile_anzahl)}), 1)
    gut_laenge = round(_summe_ziel(
        {k: v for k, v in zip(reihenfolge, anteile_laenge)}), 1)

    # --- Der Befund hinter dem Abstand: mittlere Länge je Klasse -----------
    # Er trägt die Überschrift und gehört deshalb gerechnet, nicht behauptet.
    mittlere_laenge = [
        {
            "klasse": kat["name"],
            "km": round(laenge.get(kat["kuerzel"], 0.0)
                        / anzahl[kat["kuerzel"]], 2),
        }
        for kat in KATEGORIEN
        if anzahl.get(kat["kuerzel"])
    ]

    bewertet = [m for m in mittlere_laenge if m["klasse"] != "unbekannt"]
    steigt = all(
        bewertet[i]["km"] <= bewertet[i + 1]["km"]
        for i in range(len(bewertet) - 1)
    )
    if not steigt:
        warnen(
            "Fließgewässer: die mittlere Wasserkörperlänge steigt nicht mehr "
            "monoton von „sehr gut\" zu „schlecht\". Die Überschrift des "
            "Abschnitts hängt an diesem Zusammenhang — Text prüfen."
        )
    else:
        log(f"    mittlere Länge steigt monoton "
            f"{bewertet[0]['km']} → {bewertet[-1]['km']} km je Wasserkörper")

    # --- Gegenprobe 2: Anteil erheblich veränderter und künstlicher --------
    arten_zeilen = _abfrage(f"""
        SELECT naturalAWBHMWB AS art,
               swEcologicalStatusOrPotentialValue AS v,
               COUNT(*) AS n, SUM(cLength) AS km
        FROM {_tabelle()}
        WHERE countryCode = 'AT'
          AND cYear = {config.FG_ZYKLUS}
          AND surfaceWaterBodyCategory = '{config.FG_KATEGORIE}'
        GROUP BY naturalAWBHMWB, swEcologicalStatusOrPotentialValue
    """)
    if arten_zeilen is None:
        warnen("Fließgewässer: Abfrage der Wasserkörperarten ausgefallen — "
               "Abschnitt wird übersprungen, statt ihn ohne die zweite "
               "NGP-Gegenprobe auszuliefern.")
        return None

    arten: dict[str, dict] = {}
    for zeile in arten_zeilen:
        eintrag = arten.setdefault(
            zeile["art"], {"n": 0, "km": 0.0, "gut_n": 0, "gut_km": 0.0})
        eintrag["n"] += int(zeile["n"])
        eintrag["km"] += float(zeile["km"] or 0)
        if zeile["v"] in ZIEL_KLASSEN:
            eintrag["gut_n"] += int(zeile["n"])
            eintrag["gut_km"] += float(zeile["km"] or 0)

    wasserkoerperarten = []
    for schluessel, name in ARTEN.items():
        e = arten.get(schluessel)
        if not e:
            warnen(f"Fließgewässer: keine Wasserkörper der Art „{name}\"")
            continue
        wasserkoerperarten.append({
            "art": name,
            "wasserkoerper": e["n"],
            "km": round(e["km"], 1),
            "anteil_netz": round(e["km"] / km_gesamt * 100, 2),
            "gut_prozent": round(e["gut_n"] / e["n"] * 100, 1),
            "gut_prozent_laenge": round(e["gut_km"] / e["km"] * 100, 1),
        })

    def _netzanteil(name: str) -> float:
        treffer = [a for a in wasserkoerperarten if a["art"] == name]
        return treffer[0]["anteil_netz"] if treffer else 0.0

    for name, erwartet in (
        ("erheblich verändert", config.FG_ERWARTET_HMWB_PROZENT),
        ("künstlich", config.FG_ERWARTET_AWB_PROZENT),
    ):
        ist = _netzanteil(name)
        if abs(ist - erwartet) > config.FG_TOLERANZ_PUNKTE:
            warnen(
                f"Fließgewässer: Anteil „{name}\" liegt bei {ist} % des "
                f"Netzes, der NGP 2021 nennt {erwartet} %"
            )
        else:
            log(f"    Anteil „{name}\" deckt sich mit dem NGP "
                f"({ist} gegen {erwartet} %)")

    # --- Zeitkontext: die drei Zyklen, ausdrücklich nicht als Reihe --------
    zyklus_zeilen = _abfrage(f"""
        SELECT cYear AS y, swEcologicalStatusOrPotentialValue AS v,
               COUNT(*) AS n, SUM(cLength) AS km
        FROM {_tabelle()}
        WHERE countryCode = 'AT'
          AND surfaceWaterBodyCategory = '{config.FG_KATEGORIE}'
        GROUP BY cYear, swEcologicalStatusOrPotentialValue
    """) or []
    if not zyklus_zeilen:
        warnen("Fließgewässer: Zyklusabfrage ausgefallen — Tabelle und Notiz "
               "kommen ohne den Zeitkontext aus, das Bild ist davon "
               "unberührt.")

    je_zyklus: dict[int, dict] = {}
    for zeile in zyklus_zeilen:
        e = je_zyklus.setdefault(
            int(zeile["y"]), {"n": 0, "km": 0.0, "gut_n": 0, "gut_km": 0.0})
        e["n"] += int(zeile["n"])
        e["km"] += float(zeile["km"] or 0)
        if zeile["v"] in ZIEL_KLASSEN:
            e["gut_n"] += int(zeile["n"])
            e["gut_km"] += float(zeile["km"] or 0)

    zyklen = [
        {
            "jahr": jahr,
            "wasserkoerper": je_zyklus[jahr]["n"],
            "km": round(je_zyklus[jahr]["km"], 1),
            "gut_prozent": round(
                je_zyklus[jahr]["gut_n"] / je_zyklus[jahr]["n"] * 100, 1),
            "gut_prozent_laenge": round(
                je_zyklus[jahr]["gut_km"] / je_zyklus[jahr]["km"] * 100, 1),
        }
        for jahr in config.FG_ZYKLEN if jahr in je_zyklus
    ]

    # --- Europavergleich, nur als Einordnung in der Notiz ------------------
    europa_zeilen = _abfrage(f"""
        SELECT countryCode AS c, swEcologicalStatusOrPotentialValue AS v,
               COUNT(*) AS n
        FROM {_tabelle()}
        WHERE cYear = {config.FG_ZYKLUS}
          AND surfaceWaterBodyCategory = '{config.FG_KATEGORIE}'
        GROUP BY countryCode, swEcologicalStatusOrPotentialValue
    """) or []
    if not europa_zeilen:
        warnen("Fließgewässer: Europaabfrage ausgefallen — die Einordnung "
               "fällt aus der Notiz, der Rest steht.")

    je_land: dict[str, dict] = {}
    for zeile in europa_zeilen:
        e = je_land.setdefault(zeile["c"], {"n": 0, "gut": 0})
        e["n"] += int(zeile["n"])
        if zeile["v"] in ZIEL_KLASSEN:
            e["gut"] += int(zeile["n"])

    europa = sorted(
        (
            {"land": land, "wasserkoerper": e["n"],
             "gut_prozent": round(e["gut"] / e["n"] * 100, 1)}
            for land, e in je_land.items()
        ),
        key=lambda z: z["gut_prozent"],
        reverse=True,
    )
    codes = [z["land"] for z in europa]
    rang = codes.index("AT") + 1 if "AT" in codes else None
    if rang is None and europa:
        warnen("Fließgewässer: Österreich fehlt im Europavergleich")

    daten = {
        "stand": f"Meldezyklus {config.FG_ZYKLUS}",
        "zyklus": config.FG_ZYKLUS,
        "abgerufen": "2026-08-31",
        "kategorien": KATEGORIEN,
        "nach_anzahl": {
            "zahlen": zahlen,
            "anteile": anteile_anzahl,
            "gesamt": wk_gesamt,
            "gut_prozent": gut_anzahl,
        },
        "nach_laenge": {
            "km": kilometer,
            "anteile": anteile_laenge,
            "gesamt_km": round(km_gesamt, 1),
            "gut_prozent": gut_laenge,
        },
        "abstand_punkte": round(gut_anzahl - gut_laenge, 1),
        # Die zwei Messweisen auf dieselben Fächer gebracht — ohne das trüge
        # jede Zeile ihre eigene Legende und der Vergleich wäre keiner.
        "vergleich": {
            "faecher": [k["name"] for k in KATEGORIEN],
            "zeilen": [
                {
                    "name": "Nach Wasserkörpern",
                    "werte": anteile_anzahl,
                    "grundlage": f"{wk_gesamt:,} Wasserkörper"
                                 .replace(",", "."),
                },
                {
                    "name": "Nach Flusskilometern",
                    "werte": anteile_laenge,
                    "grundlage": f"{km_gesamt:,.0f} km Gewässernetz"
                                 .replace(",", "."),
                },
            ],
        },
        "mittlere_laenge": mittlere_laenge,
        "wasserkoerperarten": wasserkoerperarten,
        "zyklen": zyklen,
        "europa": europa,
        "rang": rang,
        "laender_gesamt": len(europa),
        "kachel_wert": gut_laenge,
        # Einordnung unter der Grafik, Konvention 150–234 Zeichen.
        # Gemessen am 31.08.2026: 231.
        "hinweis": (
            "Bewertet wird nur, was ein Einzugsgebiet über 10 Quadratkilometer "
            "hat; für kleinere Gewässer gibt es keine flächendeckende "
            "Beurteilung. Für verbaute und künstliche Gewässer gilt das "
            "gute Potenzial als Ziel, nicht der gute Zustand."
        ),
    }

    quelle_vermerken(
        "Ökologischer Zustand der Fließgewässer",
        "https://discodata.eea.europa.eu/sql",
        "EEA Discodata, WISE_WFD (SWB_SurfaceWaterBody), CC BY 4.0; "
        "Gegenprobe: Nationaler Gewässerbewirtschaftungsplan 2021, BML",
        f"Meldezyklus {config.FG_ZYKLUS}",
        "api",
    )

    log(f"  nach Wasserkörpern {gut_anzahl} % · nach Länge {gut_laenge} % · "
        f"Abstand {daten['abstand_punkte']} Punkte · Rang {rang} von "
        f"{len(europa)}")

    return daten
