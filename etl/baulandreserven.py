"""
Baulandreserven — gewidmetes, aber unbebautes Bauland je Gemeinde.

ECHTE API. Anders als `boden.py`, wo die ÖROK-Bundeszahlen abgeschrieben im
Code stehen, wird diese Reihe bei jedem Lauf frisch geholt. Der Dienst ist
der OGD-FeatureServer des Umweltbundesamts, aus dem auch der öffentliche
GIS-Viewer der ÖROK gespeist wird.

  Quelle:    ÖROK-Monitoring Baulandreserven (2025),
             Berechnung: Umweltbundesamt im Auftrag der ÖROK
  Dienst:    services7.arcgis.com/JhrnFQUbVgiJfOG5 → Baulandreserven_2025_OGD
  Lizenz:    CC BY 4.0 (data.gv.at, Datensatz 6b03edb4-…, HVD nach
             Durchführungsverordnung (EU) 2023/138)
  Geprüft:   27.08.2026 — 538.541 Grundstücke, 2.086 Gemeinden

WAS DER ABSCHNITT ZEIGT und warum diese Kennzahl:

Baulandreserven sind Grundstücke, die als Bauland gewidmet, aber noch nicht
mit einem Hauptgebäude bebaut sind. Sie zählen bereits zur
Flächeninanspruchnahme — die rechtliche Zusage genügt.

Die ÖROK hat 2025 erstmals ausgewertet, WIE diese Flächen heute genutzt
werden („erstmalige Auswertungen zur Landnutzung von Baulandreserven",
Methodikseite). Genau darauf zielt der Abschnitt: Der Anteil der Reserve,
der heute noch landwirtschaftlich genutzt wird, ist Ackerland, das rechtlich
schon verloren ist, aber noch bestellt wird.

WARUM EIN ANTEIL UND KEINE HEKTARZAHL AUF DER KARTE: Absolute Hektar bilden
im Wesentlichen die Gemeindegröße ab — St. Pölten führt mit 289 ha, weil es
groß ist, nicht weil es besonders viel gewidmet hat. Der Anteil ist von der
Fläche unabhängig, zwischen 0 und 100 begrenzt und beantwortet die Frage des
Abschnitts direkt. Die Hektarzahl gehört in den Tooltip, nicht auf die Fläche.

WARUM KEIN NENNER VON AUSSEN: Naheliegend wären „je Einwohner" oder „am
Dauersiedlungsraum". Beides bräuchte einen zweiten Datensatz und damit einen
Join, der stillschweigend danebengehen kann; der Dauersiedlungsraum liegt je
Gemeinde ohnehin nicht offen vor. Der Anteil an der eigenen Reserve kommt
ohne Fremddaten aus.

ZWEI FALLEN, die hier bereits abgefangen sind:

1. `Shape__Area` NICHT verwenden. Der Dienst liefert in EPSG:102100
   (Web Mercator), Flächen sind dort um `1/cos²(Breite)` aufgebläht — in
   Österreich Faktor rund 2,2. Die Felder `FLAECHE_LW`, `FLAECHE_WALD` und
   `FLAECHE_SONSTIGE` sind dagegen echte Quadratmeter; die Gegenprobe am
   27.08.2026 traf an vier Grundstücken auf zwei Nachkommastellen.

2. `FLAECHE_SONSTIGE` führt den Wert **-1** (525 von 538.541 Datensätzen,
   Stand 27.08.2026). Wer stumpf summiert, zieht Quadratmeter ab. Deshalb
   läuft die Summe der sonstigen Flächen als eigene Abfrage mit
   `FLAECHE_SONSTIGE >= 0`. `FLAECHE_LW` und `FLAECHE_WALD` führen den Wert
   nicht (beide mit `= -1` geprüft: 0 Treffer) und werden in einem Zug
   mitgeholt.

   **-1 ist KEINE Fehlwert-Konvention.** Bis zum 04.09.2026 stand hier, der
   Wert bedeute „nicht ermittelt". Das Umweltbundesamt (Gebhard Banko) hat
   auf Nachfrage geantwortet: Die Anomalie ist **dem UBA selbst unbekannt**,
   vermutet wird das Datenformat. Der Rechenweg bleibt derselbe — die
   betroffenen Datensätze werden ausgeschlossen —, aber die Begründung ist
   „ungeklärte Anomalie", nicht „amtliche Fehlwertkennung". Der Unterschied
   zählt, sobald jemand den Wert anderswo als Fehlwert weiterverwendet.

WAS DIESER ABSCHNITT NICHT IST: Er beantwortet NICHT „wie viel Fläche wird
jährlich verbaut". Das ist Abschnitt `boden`. Baulandreserven sind eine
Nachbarfrage — der Vorrat, nicht der Verbrauch. Die Überschrift muss das
tragen, sonst liest sich der Abschnitt als Etikettenschwindel.

KEINE VERÄNDERUNGSREIHE. Es gibt Stände 2022 und 2025, aber die ÖROK nennt
für 2025 ausdrücklich eine „Präzisierung der Methodik zu Baulandreserven".
Die Differenz mischt echten Verbrauch mit einer Definitionsverschärfung und
ist deshalb nicht als Veränderung verwendbar. Der Abschnitt zeigt EIN
Stichjahr.
"""

from __future__ import annotations

import json

import requests

import config
from gemeinsam import abbruch, log, quelle_vermerken, warnen

STAND_JAHR = 2025


# --- Abruf ------------------------------------------------------------------

def _aggregieren(where: str, gruppiert: str, statistiken: list[dict]) -> list[dict]:
    """
    Holt eine serverseitig gruppierte Auswertung, seitenweise.

    Der Dienst deckelt bei 2.000 Zeilen je Antwort. Ohne Blättern kämen
    stillschweigend nur die ersten 2.000 Gemeinden zurück — bei 2.086
    Gemeinden wären das 86 fehlende, ohne jede Fehlermeldung. Deshalb wird
    geblättert, bis eine Seite kürzer als das Limit ist, und die Summe der
    Grundstücke am Ende gegen eine unabhängige Zählung gehalten
    (siehe `_gegenprobe_vollstaendigkeit`).
    """
    gesammelt: list[dict] = []
    versatz = 0
    for _ in range(config.BLR_MAX_SEITEN):
        nutzlast = {
            "f": "json",
            "where": where,
            "groupByFieldsForStatistics": gruppiert,
            "outStatistics": json.dumps(statistiken),
            "orderByFields": "GKZ",
            "resultOffset": versatz,
            "resultRecordCount": config.BLR_SEITENGROESSE,
        }
        try:
            antwort = requests.post(
                config.BLR_ABFRAGE_URL,
                data=nutzlast,
                timeout=config.TIMEOUT_SEKUNDEN,
                headers={"User-Agent": "biodiversitaet-at-dashboard/1.0"},
            )
        except requests.RequestException as fehler:
            abbruch(f"Baulandreserven: Abruf fehlgeschlagen\n         {fehler}")
        if antwort.status_code != 200:
            abbruch(
                f"Baulandreserven: HTTP {antwort.status_code} vom FeatureServer.\n"
                f"         Prüfen, ob der Dienst noch unter "
                f"{config.BLR_ABFRAGE_URL} liegt."
            )
        try:
            roh = antwort.json()
        except ValueError:
            abbruch(
                f"Baulandreserven: Antwort ist kein JSON.\n"
                f"         Erste 200 Zeichen: {antwort.text[:200]!r}"
            )
        # ArcGIS meldet Fehler mit HTTP 200 und einem "error"-Objekt.
        # Ohne diese Prüfung liefe der Lauf mit einer leeren Liste weiter.
        if "error" in roh:
            abbruch(f"Baulandreserven: Dienst meldet {roh['error']}")

        seite = [eintrag["attributes"] for eintrag in roh.get("features", [])]
        gesammelt.extend(seite)
        if len(seite) < config.BLR_SEITENGROESSE:
            return gesammelt
        versatz += config.BLR_SEITENGROESSE

    abbruch(
        f"Baulandreserven: mehr als {config.BLR_MAX_SEITEN} Seiten. "
        f"Entweder ist der Datenbestand stark gewachsen oder das Blättern "
        f"hängt — beides gehört angesehen, bevor die Zahl auf die Seite geht."
    )
    return []


def _zaehle(where: str) -> int:
    """Unabhängige Zählung über `returnCountOnly` — die Gegenprobe zum Blättern."""
    antwort = requests.get(
        config.BLR_ABFRAGE_URL,
        params={"f": "json", "where": where, "returnCountOnly": "true"},
        timeout=config.TIMEOUT_SEKUNDEN,
        headers={"User-Agent": "biodiversitaet-at-dashboard/1.0"},
    )
    return int(antwort.json().get("count", -1))


# --- Gegenproben ------------------------------------------------------------

def _gegenprobe_vollstaendigkeit(zeilen: list[dict]) -> None:
    """
    Prüft, ob das Blättern alles erwischt hat.

    Die Summe der je Gemeinde gezählten Grundstücke muss der unabhängigen
    Gesamtzählung entsprechen. Weicht sie ab, fehlt eine Seite — und zwar
    lautlos, weil eine kurze Antwort für den Aufrufer wie ein Ende aussieht.
    """
    summe = sum(int(z.get("n") or 0) for z in zeilen)
    gesamt = _zaehle("1=1")
    if gesamt < 0:
        warnen("Baulandreserven: Gegenzählung lieferte keine Zahl — nicht geprüft.")
        return
    if summe != gesamt:
        abbruch(
            f"Baulandreserven: {summe:,} Grundstücke aufsummiert, der Dienst "
            f"zählt {gesamt:,}. Es fehlt vermutlich eine Seite beim Blättern."
        )
    log(f"    Gegenprobe Blättern: {summe:,} Grundstücke, Zählung stimmt")

    if not (config.BLR_GEMEINDEN_MIN <= len(zeilen) <= config.BLR_GEMEINDEN_MAX):
        warnen(
            f"Baulandreserven: {len(zeilen)} Gemeinden — erwartet waren "
            f"{config.BLR_GEMEINDEN_MIN}–{config.BLR_GEMEINDEN_MAX}. "
            f"Gemeindezusammenlegung oder ein Fehler in der Gruppierung?"
        )

    kennziffern = [z.get("GKZ") for z in zeilen]
    if len(set(kennziffern)) != len(kennziffern):
        abbruch("Baulandreserven: doppelte Gemeindekennziffern in der Gruppierung.")
    krumm = [k for k in kennziffern if not (isinstance(k, str) and len(k) == 5)]
    if krumm:
        warnen(f"Baulandreserven: Kennziffern ohne fünf Stellen: {krumm[:5]}")


def _gegenprobe_sentinel() -> None:
    """
    Meldet, wenn der Sentinel -1 deutlich häufiger wird.

    Am 27.08.2026 waren es 525 von 538.541 Datensätzen (0,1 %) — vernachlässigbar,
    aber nur solange es so bleibt. Wächst der Anteil, ist die Aussage über die
    sonstigen Flächen und damit der Nenner des Anteils betroffen.
    """
    ohne_wert = _zaehle("FLAECHE_SONSTIGE=-1")
    gesamt = _zaehle("1=1")
    if ohne_wert < 0 or gesamt <= 0:
        return
    anteil = 100 * ohne_wert / gesamt
    log(f"    Sentinel -1 bei sonstigen Flächen: {ohne_wert:,} ({anteil:.2f} %)")
    if anteil > config.BLR_SENTINEL_GRENZE:
        warnen(
            f"Baulandreserven: {anteil:.1f} % der Grundstücke haben "
            f"FLAECHE_SONSTIGE = -1 (Grenze {config.BLR_SENTINEL_GRENZE} %). "
            f"Der Nenner des Anteils wird dadurch unsicher."
        )


# --- Klassengrenzen ---------------------------------------------------------

def _klassen(werte: list[float]) -> list[int]:
    """
    Fünf Klassen für die Karte, aus den Daten gerechnet und auf Zehner gerundet.

    WARUM NICHT FEST VERDRAHTET: Die Grenzen müssen zur Verteilung passen, und
    die Verteilung ändert sich mit jedem Monitoringzyklus. Fest eingetragene
    Grenzen würden beim nächsten Stand stillschweigend unpassend.

    WARUM GERUNDET UND NICHT REINE QUANTILE: Eine Legende mit „37,4 – 52,1 %"
    liest niemand. Gerundete Stufen sind ablesbar; dass die Klassen dadurch
    unterschiedlich stark besetzt sind, ist bei einer Karte der geringere Preis.
    """
    sortiert = sorted(werte)
    if not sortiert:
        return [20, 40, 60, 80]

    def quantil(anteil: float) -> float:
        return sortiert[min(int(anteil * (len(sortiert) - 1)), len(sortiert) - 1)]

    roh = [quantil(p) for p in (0.2, 0.4, 0.6, 0.8)]
    grenzen: list[int] = []
    for wert in roh:
        gerundet = int(round(wert / 10.0) * 10)
        # Unten auf 10 begrenzen: eine Grenze bei 0 erzeugt eine Klasse, in
        # die nichts fallen kann — Anteile sind nie negativ. Aufgefallen im
        # Trockenlauf am 27.08.2026, als das 20-%-Quantil auf 0 rundete.
        gerundet = max(10, min(90, gerundet))
        # Gleiche Grenzen zweimal ergäben ebenfalls eine leere Klasse und
        # eine Legende mit zwei identischen Zeilen.
        if grenzen and gerundet <= grenzen[-1]:
            gerundet = grenzen[-1] + 10
        grenzen.append(gerundet)

    # Stößt die Leiter oben an, wird sie von 90 aus zurückgeschoben, statt
    # bei 90 zu verklumpen. Tritt ein, wenn fast alle Gemeinden hohe Anteile
    # haben — dann liegt der Informationsgehalt ohnehin im oberen Bereich.
    if grenzen[-1] > 90:
        grenzen = [90 - 10 * (len(grenzen) - 1 - i) for i in range(len(grenzen))]
    return grenzen


# --- Aufbau -----------------------------------------------------------------

def baue_baulandreserven(ha_pro_tag: float | None = None) -> dict:
    """
    `ha_pro_tag` kommt aus dem Abschnitt `boden` und dient nur der
    Hinweiszeile. Bewusst als Argument und nicht als Konstante: Sonst stünde
    der Tageswert an zwei Stellen im Code und würde beim nächsten
    Monitoringzyklus an einer davon vergessen.
    """
    log("\n[15/15] Baulandreserven — Landnutzung je Gemeinde (API)")

    haupt = _aggregieren(
        where="1=1",
        gruppiert="GKZ,PG,BL",
        statistiken=[
            {"statisticType": "sum", "onStatisticField": "FLAECHE_LW",
             "outStatisticFieldName": "lw"},
            {"statisticType": "sum", "onStatisticField": "FLAECHE_WALD",
             "outStatisticFieldName": "wald"},
            {"statisticType": "count", "onStatisticField": "OBJECTID",
             "outStatisticFieldName": "n"},
        ],
    )
    sonstige = _aggregieren(
        where="FLAECHE_SONSTIGE>=0",
        gruppiert="GKZ",
        statistiken=[
            {"statisticType": "sum", "onStatisticField": "FLAECHE_SONSTIGE",
             "outStatisticFieldName": "so"},
        ],
    )

    _gegenprobe_vollstaendigkeit(haupt)
    _gegenprobe_sentinel()

    sonst_je_gemeinde = {z["GKZ"]: (z.get("so") or 0) for z in sonstige}

    gemeinden = []
    for zeile in haupt:
        lw = zeile.get("lw") or 0
        wald = zeile.get("wald") or 0
        sonst = sonst_je_gemeinde.get(zeile["GKZ"], 0)
        gesamt = lw + wald + sonst
        gemeinden.append({
            "gkz": zeile["GKZ"],
            "name": zeile.get("PG"),
            "bl": zeile.get("BL"),
            "lw_ha": round(lw / 10_000, 1),
            "wald_ha": round(wald / 10_000, 1),
            "gesamt_ha": round(gesamt / 10_000, 1),
            # None statt 0, wenn es gar keine Reserve gibt: eine Gemeinde ohne
            # Bauland-Reserve hat keinen Anteil, sie hat keinen Nenner. Die
            # Karte muss sie grau lassen, nicht als "0 %" einfärben.
            "anteil": round(100 * lw / gesamt, 1) if gesamt > 0 else None,
            "grundstuecke": int(zeile.get("n") or 0),
        })

    summe_lw = sum(z.get("lw") or 0 for z in haupt)
    summe_wald = sum(z.get("wald") or 0 for z in haupt)
    summe_sonst = sum(sonst_je_gemeinde.values())
    summe_gesamt = summe_lw + summe_wald + summe_sonst
    if summe_gesamt <= 0:
        abbruch("Baulandreserven: Gesamtfläche ist null — Abfrage prüfen.")

    anteil_bund = round(100 * summe_lw / summe_gesamt, 1)
    lw_ha = round(summe_lw / 10_000)
    gesamt_ha = round(summe_gesamt / 10_000)

    mit_reserve = [g for g in gemeinden if g["anteil"] is not None]
    grenzen = _klassen([g["anteil"] for g in mit_reserve])

    log(f"    {len(gemeinden):,} Gemeinden, {gesamt_ha:,} ha Reserve gesamt")
    log(f"    davon landwirtschaftlich genutzt: {lw_ha:,} ha ({anteil_bund} %)")
    log(f"    Klassengrenzen der Karte: {grenzen}")

    # Gegenprobe gegen den Bodenabschnitt: Die Reserven sind laut ÖROK-Definition
    # Teil der Flächeninanspruchnahme. Sie können sie also nicht übersteigen.
    if gesamt_ha > config.BLR_FI_BESTAND_HA:
        warnen(
            f"Baulandreserven: {gesamt_ha:,} ha übersteigen die gesamte "
            f"Flächeninanspruchnahme ({config.BLR_FI_BESTAND_HA:,} ha). "
            f"Reserven sind deren Teilmenge — eine der beiden Zahlen ist falsch."
        )

    quelle_vermerken(
        name=("ÖROK-Monitoring Baulandreserven (2025) — "
              "Berechnung: Umweltbundesamt"),
        url="https://www.oerok.gv.at/monitoring-flaecheninanspruchnahme/daten",
        lizenz="CC BY 4.0",
        stand=str(STAND_JAHR),
        art="api",
    )

    _lw_de = f"{lw_ha:,}".replace(",", ".")

    return {
        "stand": STAND_JAHR,
        "gemeinden": gemeinden,
        "klassengrenzen": grenzen,
        "oesterreich": {
            "lw_ha": lw_ha,
            "wald_ha": round(summe_wald / 10_000),
            "gesamt_ha": gesamt_ha,
            "anteil_lw": anteil_bund,
            "grundstuecke": sum(g["grundstuecke"] for g in gemeinden),
        },
        "hinweis": _hinweis(lw_ha, _lw_de, ha_pro_tag),
    }


def _hinweis(lw_ha: int, lw_de: str, ha_pro_tag: float | None) -> str:
    """
    Baut die Hinweiszeile und rechnet den Vergleich, statt ihn zu behaupten.

    Der Vergleich läuft über den Tageswert aus `boden`, weil das die einzige
    Größe derselben Art ist, die auf derselben Seite steht. Bewusst als
    Größenordnung formuliert: Nicht jede Reserve wird bebaut, und der
    Tageswert misst die gesamte Neuinanspruchnahme, nicht nur jene auf
    Reserveflächen. Die Zahl ordnet die Größe ein, sie sagt nichts voraus.

    Ohne Tageswert entfällt der zweite Satz ersatzlos — lieber eine kürzere
    Zeile als ein Vergleich mit einer Zahl, die nicht da ist.
    """
    erster = (f"{lw_de} Hektar Bauland werden heute noch als Acker oder Wiese "
              f"genutzt — gewidmet ist die Fläche längst.")
    if not ha_pro_tag or ha_pro_tag <= 0:
        return erster
    jahre = lw_ha / (ha_pro_tag * 365.25)
    if jahre < 1:
        return erster
    zeile = (f"{erster} Beim Tempo der letzten Jahre entspricht das gut "
             f"{round(jahre)} Jahren Bodenverbrauch, die rechtlich bereits "
             f"vergeben sind.")
    # Hausmaß für Hinweiszeilen: 150–234 Zeichen. Kürzere wirken abgeschnitten,
    # längere brechen auf dem Handy in eine vierte Zeile um.
    if not 150 <= len(zeile) <= 234:
        warnen(
            f"Baulandreserven: Hinweiszeile ist {len(zeile)} Zeichen lang "
            f"(Hausmaß 150–234). Formulierung nachziehen."
        )
    return zeile
