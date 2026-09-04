"""
Woher der Schutz kommt — Natura 2000 gegen nationale Ausweisung.

Der Abschnitt darüber (`schutzgebiete`) nennt EINE Zahl: 29,3 % der
Landesfläche stehen unter Schutz. Diese Zahl ist eine Summe aus zwei sehr
verschiedenen Vorgängen — der eine folgt einer EU-Richtlinie, der andere
einer Entscheidung des Landes. Dieses Modul trennt sie und stellt Österreich
dem EU-Schnitt gegenüber.

QUELLE: EEA-Indikator „Designated terrestrial protected areas in Europe",
Datenpaket der Abbildung 2 (`FIG2-290046-SEBI007-v3`). Das Paket ist ein ZIP
mit mehreren Dateien; gebraucht wird `…-Data.xlsx`, Blatt „Original Data".
Stichjahr Ende 2023, zusammengesetzt aus Natura 2000 (Stand Ende 2023) und
den national ausgewiesenen Gebieten (CDDA, Mai 2024).

KEIN openpyxl. Eine .xlsx ist ein ZIP aus XML-Dateien, und dieses Blatt
enthält nur Text und Zahlen — keine Formeln, keine Datumswerte, keine
Formate, auf die es ankäme. Das lässt sich mit `zipfile` und
`xml.etree` aus der Standardbibliothek lesen. Eine neue Abhängigkeit für
40 Zeilen Parser wäre der teurere Weg, und sie müsste in der CI mitlaufen.

DER VORBEHALT, der in die Hinweiszeile gehört: Die 30 % der EU-Biodiversitäts-
strategie sind ein Ziel für die EU ALS GANZES, nicht für jeden Mitgliedstaat.
Die EU steht bei 26,4 %. „Österreich verfehlt sein Ziel" wäre eine Aussage,
die diese Daten nicht hergeben — deshalb steht in diesem Abschnitt keine
Zielmarke.
"""

from __future__ import annotations

import io
import re
import zipfile
import xml.etree.ElementTree as ET

import requests

import config
from gemeinsam import log, quelle_vermerken, warnen

XL = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"


def _hole_paket(url: str) -> bytes | None:
    """Das ZIP der Abbildung holen. Ein Ausfall überspringt den Abschnitt."""
    try:
        antwort = requests.get(url, timeout=config.SH_TIMEOUT_SEKUNDEN)
        antwort.raise_for_status()
        return antwort.content
    except requests.RequestException as fehler:
        warnen(f"Schutzherkunft: Abruf fehlgeschlagen ({fehler}) — Abschnitt bleibt aus")
        return None


def _blatt_zeilen(xlsx: bytes, blattname: str) -> list[list[str]]:
    """
    Ein Blatt einer .xlsx als Liste von Zeilen, jede Zeile eine Liste von
    Zellwerten als Text. Leere Zellen werden zu "".

    Zwei Fallen, beide hier abgefangen:
    1. Texte stehen nicht in der Zelle, sondern als Index in
       `sharedStrings.xml` — Zellen mit `t="s"` müssen dort nachschlagen.
    2. Die Spalte einer Zelle steht in ihrem `r`-Attribut („C7"), nicht in
       ihrer Position. Fehlende Zellen werden übersprungen, nicht als leer
       geschrieben — wer stumpf durchzählt, verschiebt ganze Zeilen.
    """
    with zipfile.ZipFile(io.BytesIO(xlsx)) as paket:
        wurzel = ET.fromstring(paket.read("xl/workbook.xml"))
        rels = ET.fromstring(paket.read("xl/_rels/workbook.xml.rels"))
        ziel = {
            r.get("Id"): r.get("Target")
            for r in rels
        }
        datei = None
        for blatt in wurzel.iter(f"{XL}sheet"):
            if blatt.get("name") == blattname:
                rid = blatt.get(
                    "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
                )
                datei = "xl/" + ziel[rid].lstrip("/")
                break
        if datei is None:
            raise KeyError(f"Blatt {blattname!r} fehlt in der Arbeitsmappe")

        texte: list[str] = []
        if "xl/sharedStrings.xml" in paket.namelist():
            sst = ET.fromstring(paket.read("xl/sharedStrings.xml"))
            for si in sst.iter(f"{XL}si"):
                texte.append("".join(t.text or "" for t in si.iter(f"{XL}t")))

        blatt_xml = ET.fromstring(paket.read(datei))

    zeilen: list[list[str]] = []
    for zeile in blatt_xml.iter(f"{XL}row"):
        felder: dict[int, str] = {}
        for zelle in zeile.iter(f"{XL}c"):
            spalte = _spaltennummer(zelle.get("r", ""))
            v = zelle.find(f"{XL}v")
            wert = "" if v is None or v.text is None else v.text
            if zelle.get("t") == "s" and wert != "":
                wert = texte[int(wert)]
            elif zelle.get("t") == "inlineStr":
                wert = "".join(t.text or "" for t in zelle.iter(f"{XL}t"))
            felder[spalte] = wert
        breite = max(felder) + 1 if felder else 0
        zeilen.append([felder.get(i, "") for i in range(breite)])
    return zeilen


def _spaltennummer(bezug: str) -> int:
    """„C7" → 2. Rein die Buchstaben, Basis 26, nullbasiert."""
    buchstaben = re.match(r"[A-Z]+", bezug)
    if not buchstaben:
        return 0
    n = 0
    for z in buchstaben.group(0):
        n = n * 26 + (ord(z) - 64)
    return n - 1


def baue_schutzherkunft() -> dict | None:
    log("\n[20/20] Schutzherkunft — Natura 2000 gegen nationale Ausweisung")

    roh = _hole_paket(config.SH_PAKET_URL)
    if roh is None:
        return None

    try:
        with zipfile.ZipFile(io.BytesIO(roh)) as paket:
            treffer = [n for n in paket.namelist() if n.endswith("-Data.xlsx")]
            if not treffer:
                warnen("Schutzherkunft: keine …-Data.xlsx im Paket — Abschnitt bleibt aus")
                return None
            xlsx = paket.read(treffer[0])
        zeilen = _blatt_zeilen(xlsx, config.SH_BLATT)
    except (zipfile.BadZipFile, KeyError, ET.ParseError) as fehler:
        warnen(f"Schutzherkunft: Paket nicht lesbar ({fehler}) — Abschnitt bleibt aus")
        return None

    # Zeile 1 ist die Kopfzeile, danach je Land eine Zeile. Zwischen den
    # EU-Staaten und den übrigen steht eine leere Zeile; sie fällt hier
    # heraus, weil ohne Landesnamen nichts übernommen wird.
    laender: dict[str, dict] = {}
    for zeile in zeilen[1:]:
        if len(zeile) < 4 or not zeile[0].strip():
            continue
        name = zeile[0].strip()
        try:
            laender[name] = {
                "natura": float(zeile[1]) * 100,
                "national": float(zeile[2]) * 100,
                "gesamt": float(zeile[3]) * 100,
                "km2": round(float(zeile[4])) if len(zeile) > 4 and zeile[4] else None,
            }
        except ValueError:
            continue

    fehlend = [n for n in (config.SH_OESTERREICH, config.SH_EU) if n not in laender]
    if fehlend:
        warnen(f"Schutzherkunft: {', '.join(fehlend)} fehlt im Blatt — Abschnitt bleibt aus")
        return None

    # --- Gegenprobe 1: die beiden Teile müssen die Summe ergeben ------------
    # Die Quelle liefert alle drei Werte getrennt und rundet die Summe auf
    # drei Nachkommastellen. Weichen sie um mehr als 0,1 Punkte voneinander
    # ab, sind die Spalten nicht die, für die ich sie halte.
    for name, w in laender.items():
        if abs(w["natura"] + w["national"] - w["gesamt"]) > 0.1:
            warnen(
                f"Schutzherkunft: {name} — {w['natura']:.1f} + {w['national']:.1f} "
                f"ergibt nicht {w['gesamt']:.1f}. Spaltenzuordnung prüfen."
            )
            return None

    # --- Gegenprobe 2: alle 27 Mitgliedstaaten da? --------------------------
    # Nach Namen, nicht nach Zeilenzahl: Die Reihenfolge im Blatt ist nach
    # Anteil sortiert und ändert sich mit jedem Jahrgang, die Namensliste
    # nicht. Ein umbenanntes Land meldet sich hier, statt still zu fehlen.
    vermisst = [n for n in config.SH_MITGLIEDSTAATEN if n not in laender]
    if vermisst:
        warnen(
            f"Schutzherkunft: {len(vermisst)} Mitgliedstaaten fehlen "
            f"({', '.join(vermisst[:4])}…) — Abschnitt bleibt aus"
        )
        return None

    # --- Gegenprobe 3: Anteile im sinnvollen Bereich ------------------------
    ausreisser = [
        n for n, w in laender.items()
        if not (0 <= w["natura"] <= 100 and 0 <= w["national"] <= 100 and 0 <= w["gesamt"] <= 100)
    ]
    if ausreisser:
        warnen(f"Schutzherkunft: Anteile außerhalb 0–100 % bei {', '.join(ausreisser)}")
        return None

    at = laender[config.SH_OESTERREICH]
    eu = laender[config.SH_EU]

    mitglieder = {n: laender[n] for n in config.SH_MITGLIEDSTAATEN}
    rang = sorted(mitglieder, key=lambda n: -mitglieder[n]["gesamt"]).index(
        config.SH_OESTERREICH
    ) + 1
    ueber_ziel = [n for n, w in mitglieder.items() if w["gesamt"] > config.SH_EU_ZIEL]

    # Der Befund in einer Zahl: Wie viel von dem, was geschützt ist, ist es
    # nicht wegen einer EU-Richtlinie? Nicht der Anteil an der Landesfläche —
    # der Anteil am eigenen Schutz.
    anteil_national_at = round(at["national"] / at["gesamt"] * 100, 1)
    anteil_national_eu = round(eu["national"] / eu["gesamt"] * 100, 1)

    log(
        f"    Österreich {at['gesamt']:.1f} % = {at['natura']:.1f} Natura 2000 "
        f"+ {at['national']:.1f} national ({anteil_national_at:.1f} % des Schutzes)"
    )
    log(
        f"    EU-27      {eu['gesamt']:.1f} % = {eu['natura']:.1f} Natura 2000 "
        f"+ {eu['national']:.1f} national ({anteil_national_eu:.1f} % des Schutzes)"
    )
    log(f"    Rang Österreich {rang} von {len(mitglieder)}, "
        f"{len(ueber_ziel)} Staaten über {config.SH_EU_ZIEL:.0f} %")

    quelle_vermerken(
        name="EEA — Designated terrestrial protected areas in Europe (SEBI 007)",
        url=("https://www.eea.europa.eu/en/analysis/indicators/"
             "terrestrial-protected-areas-in-europe"),
        lizenz="EEA standard re-use policy",
        stand=str(config.SH_STICHJAHR),
        art="api",
    )

    return {
        "stichjahr": config.SH_STICHJAHR,
        "balken": [
            {
                "gebiet": "Österreich",
                "natura": round(at["natura"], 1),
                "national": round(at["national"], 1),
                "gesamt": round(at["gesamt"], 1),
                "anteil_national": anteil_national_at,
            },
            {
                "gebiet": "EU-27",
                "natura": round(eu["natura"], 1),
                "national": round(eu["national"], 1),
                "gesamt": round(eu["gesamt"], 1),
                "anteil_national": anteil_national_eu,
            },
        ],
        "kachel_wert": anteil_national_at,
        "rang": rang,
        "mitgliedstaaten": len(mitglieder),
        "ueber_ziel": len(ueber_ziel),
        "eu_ziel": config.SH_EU_ZIEL,
        "at_km2": at["km2"],
        # Die Notiz baut das Chart-Modul aus diesen Zahlen — dort steht der
        # Formatierer, der 29,3 schreibt und nicht 29.3. Hier stünde sonst
        # ein Punkt als Dezimaltrennzeichen fest im Text.
        "hinweis": (
            "Überschneidungen sind herausgerechnet: Fläche, die zugleich Natura 2000 "
            "und national ausgewiesen ist, zählt nur einmal. Die "
            f"{config.SH_EU_ZIEL:.0f} Prozent der EU-Biodiversitätsstrategie gelten für "
            "die EU als Ganzes, nicht je Mitgliedstaat."
        ),
    }
