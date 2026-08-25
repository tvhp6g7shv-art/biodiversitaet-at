"""
Gemeinsames Fundament der ETL-Pipeline: Logging, Download, geteilter
Zustand (Warnungen, Quellenverzeichnis) und das Schreiben der JSON-Ausgaben.

Übernommen aus arbeitsmarkt-at/etl/gemeinsam.py und dort gekürzt, wo die
pandas-Helfer für CSV-Tabellen nur mitgeschleppt worden wären. Neu ist
`pflegepruefung()` — das Gegenstück zur Schemaprüfung der Schwesterpipeline:
Dort wacht die Pipeline darüber, dass sich das Format der Quelle nicht
ändert, hier darüber, dass eine abgeschriebene Zahl nicht unbemerkt altert.
"""

from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

import requests

import config

# --- Geteilter Zustand ------------------------------------------------------
# Diese Objekte werden von den Strang-Modulen befüllt (append / Schlüssel
# setzen), nie neu zugewiesen — sonst verlieren die Importe die Verbindung.

WARNUNGEN: list[str] = []
QUELLEN: list[dict] = []

# Das Repo-Wurzelverzeichnis (eine Ebene über etl/)
WURZEL = Path(__file__).resolve().parent.parent
AUSGABE = WURZEL / config.AUSGABE_ORDNER


def log(text: str) -> None:
    print(text, flush=True)


def warnen(text: str) -> None:
    WARNUNGEN.append(text)
    log(f"  ⚠  {text}")


def abbruch(text: str) -> None:
    """Harter Abbruch mit klarer Meldung — erscheint im GitHub-Actions-Log."""
    log("")
    log("=" * 70)
    log("ABBRUCH: " + text)
    log("=" * 70)
    sys.exit(1)


# --- Download ---------------------------------------------------------------

def lade_json(url: str, params: dict | None = None) -> dict:
    log(f"  ↓ {url.split('/')[-1][:60]}")
    try:
        antwort = requests.get(
            url,
            params=params,
            timeout=config.TIMEOUT_SEKUNDEN,
            headers={"User-Agent": "biodiversitaet-at-dashboard/1.0"},
        )
    except requests.RequestException as fehler:
        abbruch(f"Download fehlgeschlagen: {url}\n         {fehler}")
    if antwort.status_code != 200:
        abbruch(
            f"Download lieferte HTTP {antwort.status_code}: {url}\n"
            f"         Prüfen, ob die Quelle noch unter dieser Adresse liegt."
        )
    try:
        return antwort.json()
    except ValueError:
        abbruch(
            f"Antwort ist kein JSON: {url}\n"
            f"         Erste 200 Zeichen: {antwort.text[:200]!r}"
        )


def jsonstat_tabelle(rohdaten: dict, quelle: str) -> dict[tuple, float]:
    """
    Dekodiert eine JSON-stat-2.0-Antwort von Eurostat vollständig.

    Liefert {(kat_dim1, kat_dim2, …): wert}, die Reihenfolge der Dimensionen
    entspricht `rohdaten["id"]`.

    WARUM DAS NÖTIG IST — die Falle, die zweimal zugeschnappt hat:
    Eurostat liefert die Werte als flaches Objekt mit LAUFENDEN NUMMERN als
    Schlüssel. Solange nur eine Dimension mehr als eine Kategorie hat, ist
    die Nummer schlicht der Zeitindex, und man kommt mit einer einfachen
    Zuordnung durch. Sobald aber eine zweite Dimension mehrfach besetzt
    ist — bei `sdg_15_60` etwa die Einheit mit „Index 2000=100" UND
    „Index 1990=100" —, laufen zwei komplette Reihen hintereinander im
    selben Wertefeld. Wer dann weiter nach Zeitindex zuordnet, liest die
    zweite Reihe als die erste und bekommt eine Kurve, die plausibel
    aussieht und falsch ist.

    Die Dekodierung ist zeilenweise (row-major): die LETZTE Dimension
    läuft am schnellsten. Für Position p von hinten nach vorn jeweils
    `p % groesse` nehmen und `p //= groesse`.

    Fehlende Werte fehlen im value-Objekt einfach, sie stehen nicht als
    null drin — deshalb wird über die vorhandenen Schlüssel gelaufen und
    nicht über das Kreuzprodukt.
    """
    werte = rohdaten.get("value") or {}
    if not werte:
        warnen(f"{quelle}: Antwort enthält keine Werte")
        return {}

    ids = rohdaten.get("id") or []
    groessen = rohdaten.get("size") or []
    if not ids or len(ids) != len(groessen):
        abbruch(f"{quelle}: Antwort ohne brauchbares id/size — Format hat sich geändert.")

    # Je Dimension: Position -> Kategoriecode
    nach_position: list[dict[int, str]] = []
    for name in ids:
        index = (rohdaten.get("dimension", {}).get(name, {})
                 .get("category", {}).get("index", {}))
        if isinstance(index, dict):
            nach_position.append({int(pos): kat for kat, pos in index.items()})
        else:  # Liste statt Objekt — bei Eurostat selten, aber erlaubt
            nach_position.append(dict(enumerate(index)))

    tabelle: dict[tuple, float] = {}
    for pos_text, wert in werte.items():
        if wert is None:
            continue
        rest = int(pos_text)
        schluessel: list[str] = []
        for tiefe in range(len(ids) - 1, -1, -1):
            rest, teil = divmod(rest, groessen[tiefe]) if groessen[tiefe] else (0, 0)
            schluessel.append(nach_position[tiefe].get(teil, str(teil)))
        tabelle[tuple(reversed(schluessel))] = float(wert)

    return tabelle


def _zeitachse(rohdaten: dict) -> int | None:
    ids = rohdaten.get("id") or []
    return ids.index("time") if "time" in ids else None


def jsonstat_reihe(rohdaten: dict, quelle: str, **filter_) -> dict[str, float]:
    """
    Eine Zeitreihe {Jahr: Wert} aus einer JSON-stat-Antwort.

    `filter_` grenzt auf Kategorien ein, etwa `unit="I00"` oder `geo="AT"`.
    Bleiben nach dem Filtern mehrere Reihen übrig, bricht die Funktion ab —
    lieber eine klare Meldung als eine stillschweigend vermischte Kurve.
    """
    tabelle = jsonstat_tabelle(rohdaten, quelle)
    if not tabelle:
        return {}
    ids = rohdaten.get("id") or []
    zeit = _zeitachse(rohdaten)
    if zeit is None:
        abbruch(f"{quelle}: Antwort ohne Zeitdimension — Format hat sich geändert.")

    reihe: dict[str, float] = {}
    uebrige: set[tuple] = set()
    for schluessel, wert in tabelle.items():
        if any(schluessel[ids.index(d)] != k for d, k in filter_.items() if d in ids):
            continue
        reihe[schluessel[zeit]] = wert
        uebrige.add(tuple(t for i, t in enumerate(schluessel) if i != zeit))

    if len(uebrige) > 1:
        abbruch(
            f"{quelle}: Der Filter lässt {len(uebrige)} Reihen übrig "
            f"({sorted(uebrige)[:3]} …). So würden mehrere Kurven zu einer "
            f"verschmelzen — bitte enger filtern."
        )

    log(f"    {len(reihe)} Jahreswerte · {min(reihe)}–{max(reihe)}" if reihe else "    leer")
    return reihe


def jsonstat_laender(rohdaten: dict, quelle: str, **filter_) -> dict[str, dict[str, float]]:
    """Länderweise Zeitreihen: {geo: {Jahr: Wert}}."""
    tabelle = jsonstat_tabelle(rohdaten, quelle)
    if not tabelle:
        return {}
    ids = rohdaten.get("id") or []
    zeit, geo = _zeitachse(rohdaten), (ids.index("geo") if "geo" in ids else None)
    if zeit is None or geo is None:
        abbruch(f"{quelle}: Antwort ohne Zeit- oder Geodimension.")

    ergebnis: dict[str, dict[str, float]] = {}
    for schluessel, wert in tabelle.items():
        if any(schluessel[ids.index(d)] != k for d, k in filter_.items() if d in ids):
            continue
        ergebnis.setdefault(schluessel[geo], {})[schluessel[zeit]] = wert

    log(f"    {len(ergebnis)} Gebiete")
    return ergebnis


def laender_namen(rohdaten: dict) -> dict[str, str]:
    """Ländercode -> ausgeschriebener Name, wie ihn Eurostat mitliefert."""
    return (rohdaten.get("dimension", {}).get("geo", {})
            .get("category", {}).get("label", {})) or {}


# --- Quellen und Pflege -----------------------------------------------------

def quelle_vermerken(name: str, url: str, lizenz: str, stand: str, art: str) -> None:
    """
    Sammelt die Quellenangaben für meta.json und damit für den Fuß der Seite.
    `art` ist "api" oder "gepflegt" — das Frontend zeigt gepflegte Reihen mit
    ihrem Stand an, damit niemand eine dreijährige Zahl für tagesaktuell hält.
    """
    QUELLEN.append({
        "name": name, "url": url, "lizenz": lizenz,
        "stand": stand, "art": art,
    })


def pflegepruefung(schluessel: str, stand_jahr: int, was: str) -> None:
    """
    Meldet, wenn eine abgeschriebene Reihe älter ist als ihr erwarteter
    Erscheinungsrhythmus. Kein Abbruch — die Zahl bleibt richtig, sie ist
    nur womöglich nicht mehr die neueste.
    """
    rhythmus = config.PFLEGE_RHYTHMUS.get(schluessel)
    if not rhythmus:
        return
    alter = dt.date.today().year - stand_jahr
    if alter > rhythmus:
        warnen(
            f"{was}: Stand {stand_jahr}, also {alter} Jahre alt — erwartet wird "
            f"alle {rhythmus} Jahre eine neue Ausgabe. Bitte nachsehen, ob es "
            f"inzwischen eine gibt, und das Modul nachziehen."
        )
    else:
        log(f"    Pflegestand {stand_jahr} ({alter} Jahre) — im Rhythmus")


# --- Schreiben --------------------------------------------------------------

def schreibe(name: str, inhalt) -> None:
    AUSGABE.mkdir(parents=True, exist_ok=True)
    ziel = AUSGABE / f"{name}.json"
    with ziel.open("w", encoding="utf-8") as datei:
        json.dump(inhalt, datei, ensure_ascii=False, separators=(",", ":"))
    groesse = ziel.stat().st_size / 1024
    log(f"    {name}.json  ({groesse:,.1f} KB)")
