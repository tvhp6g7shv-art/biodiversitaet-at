"""
Flächeninanspruchnahme je Gemeinde — ÖROK-Monitoring 2025, OGD-Geodaten.

  Quelle:    ÖROK-Monitoring Flächeninanspruchnahme 2025 (Stand
             Berechnungsjahr 2025), Berechnung: Umweltbundesamt
  Datensatz: data.gv.at, 46f43f1c-1f8e-47eb-8526-bb0e683361b5
  Verteilung: Nextcloud-Freigabe des Umweltbundesamts (config.FI_FREIGABE)
  Lizenz:    CC BY 4.0, HighValueDataset
  Stand:     01.12.2025, GeoPackage erzeugt 2025-11-26
  Erhoben:   09.09.2026 am Datensatz selbst (Range-Abrufe im Browsertab),
             nicht aus der Datensatzbeschreibung abgeschrieben

WARUM DIESE KARTE ÜBERHAUPT ERLAUBT IST: Die amtliche Gemeindestatistik der
ÖROK erscheint erst voraussichtlich 2027. Die Eigenberechnung aus den offenen
GIS-Daten hat das Umweltbundesamt (Gebhard Banko) am 04.09.2026 ausdrücklich
freigegeben — mit einer Auflage, die hier bindend ist:

    Es darf eine ZUSTANDSkarte sein, keine VERÄNDERUNGSkarte. Unsicher sind
    laut UBA die CHANGES 22–25 (Ermittlung der Straßenveränderungen), die auf
    Gemeindeebene stark durchschlagen — nicht die Status-Layer 2022 und 2025.
    Dass die Veränderungen je Gemeinde derzeit nicht valide sind, muss im Text
    stehen. Dieses Modul rechnet deshalb NUR den Stand 2025 und keine
    Differenz zu 2022, auch wenn der 2022er Layer offen daneben liegt.

WARUM KEINE VERSCHNEIDUNG MIT DEN GEMEINDEGRENZEN: Weil sie nicht nötig ist.
Die Tabelle `FI_OGD_2025` trägt `GKZ` als Attribut je Polygon, dazu KG_NR,
KG, PG, BKZ, PB, BL_KZ und BL. Die Zuordnung zur Gemeinde ist damit ein
GROUP BY und keine Geometrieoperation. Das war die teuerste Annahme im Plan
und sie war falsch — die Akte vom 27.08. ging von einer Verschneidung aus,
weil der ArcGIS-Dienst `FI_OGD_Detail` nur `OGD_FI` und `Shape__Area` führt.
Das GeoPackage ist reicher als der Dienst.

WOFÜR SHAPELY DOCH GEBRAUCHT WIRD: Eine `Shape_Area`-Spalte gibt es NICHT.
Die Fläche muss aus der Geometrie gerechnet werden. EPSG:31287 ist metrisch,
die Fläche fällt also direkt in m² an.

WARUM DER NENNER AUS `gemeinden.json` KOMMT: Die Kennzahl ist der Anteil an
der Gemeindefläche (User-Entscheid 09.09.2026). `gemeindegrenzen.py` legt
`flaeche_m2` seit Aufbau 3 in die Umrissdatei — gerechnet aus den ROHEN
Polygonen, vor dem Ausdünnen. Wer den Nenner aus der ausgedünnten Karte
nimmt, misst ihn um Prozente falsch.

WAS DIESER NENNER VERZERRT, UND WARUM ES TROTZDEM SO BLEIBT: Im Bund stehen
6,8 % der Landesfläche gegen 17,4 % des Dauersiedlungsraums — Faktor 2,6.
Je Gemeinde streut der Faktor mit dem Relief: Fels, Gletscher und Steilwald
stehen im Gemeindenenner, eine Alpengemeinde wirkt dadurch makellos. Die
Karte zeigt am Gemeindenenner streckenweise die Topografie und nicht die
Bautätigkeit. Der Dauersiedlungsraum liegt als Polygonlayer offen vor
(Statistik Austria OGDEXT_DSR_1, EPSG:31287, derselbe WFS wie die
Gemeindegrenzen) — die Gegenprobe gehört in einen eigenen Schritt und ist
hier bewusst noch nicht drin, damit dieser Lauf ohne zweiten Datenweg
auskommt. Bis sie steht, muss die Einordnung den Nenner benennen.

WARUM DAS MODUL NICHT BEI JEDEM LAUF ARBEITET: Der Abruf ist 1,27 GiB und
entpackt 3,86 GiB. Das Monitoring läuft dreijährlich. Das Modul baut die
Ausgabe deshalb nur, wenn sie fehlt oder auf einem anderen Stand bzw. einer
anderen Aufbauzählung steht — dieselbe Mechanik wie bei den Gemeindegrenzen.
"""

from __future__ import annotations

import json
import shutil
import sqlite3
import tempfile
import zipfile
from pathlib import Path

import requests

import config
from gemeinsam import abbruch, log, quelle_vermerken, schreibe, warnen

ZIEL = Path(config.AUSGABE_ORDNER) / "flaecheninanspruchnahme.json"
GRENZEN = Path(config.AUSGABE_ORDNER) / "gemeinden.json"

# Größe des GPKG-Binärkopfes je Hüllkörper-Kennung (Bit 1–3 der Flags).
_HUELLE_BYTE = {0: 0, 1: 32, 2: 48, 3: 48, 4: 64}


# --- Abruf ------------------------------------------------------------------

def _download_url() -> str:
    """
    Einzeldatei aus der Nextcloud-Freigabe.

    Der Weg ist die öffentliche Share-Adresse mit `download`, nicht ein
    direkter Dateipfad — einen solchen gibt es bei Nextcloud nicht.
    """
    return (f"{config.FI_FREIGABE}/download"
            f"?path=%2F&files={config.FI_DATEI}")


def _herunterladen(ziel: Path) -> None:
    log(f"  ↓ {config.FI_DATEI} "
        f"({config.FI_ZIP_BYTE / 1024**3:,.2f} GiB)")
    try:
        antwort = requests.get(
            _download_url(),
            stream=True,
            timeout=config.FI_TIMEOUT_SEKUNDEN,
            headers={"User-Agent": "biodiversitaet-at-dashboard/1.0"},
        )
    except requests.RequestException as fehler:
        abbruch(f"Flächeninanspruchnahme: Abruf fehlgeschlagen\n         {fehler}")
    if antwort.status_code != 200:
        abbruch(
            f"Flächeninanspruchnahme: HTTP {antwort.status_code} von der "
            f"Freigabe. Prüfen, ob {config.FI_FREIGABE} noch gilt — "
            f"Nextcloud-Freigaben können ablaufen."
        )
    gelesen = 0
    with ziel.open("wb") as datei:
        for stueck in antwort.iter_content(chunk_size=1024 * 1024):
            datei.write(stueck)
            gelesen += len(stueck)
    log(f"    {gelesen:,} Byte geladen")

    # Die Länge ist am 09.09.2026 gemessen. Weicht sie ab, ist der Datensatz
    # neu aufgelegt worden — dann stimmen Stichjahr und Schema hier womöglich
    # nicht mehr, und ein stiller Weiterlauf wäre das Schlechteste.
    if gelesen != config.FI_ZIP_BYTE:
        warnen(
            f"Flächeninanspruchnahme: {gelesen:,} Byte statt erwarteter "
            f"{config.FI_ZIP_BYTE:,}. Der Datensatz wurde vermutlich neu "
            f"aufgelegt — Stichjahr, Spalten und FI-Codes gegenprüfen."
        )


def _entpacken(archiv: Path, ordner: Path) -> Path:
    with zipfile.ZipFile(archiv) as zipdatei:
        namen = zipdatei.namelist()
        if config.FI_GPKG_NAME not in namen:
            abbruch(
                f"Flächeninanspruchnahme: {config.FI_GPKG_NAME} fehlt im "
                f"Archiv. Enthalten: {namen}"
            )
        log(f"  ⇱ {config.FI_GPKG_NAME} "
            f"({config.FI_GPKG_BYTE / 1024**3:,.2f} GiB entpackt)")
        zipdatei.extract(config.FI_GPKG_NAME, ordner)
    # Das Archiv wird sofort gelöscht: 1,27 GiB plus 3,86 GiB liegen sonst
    # gleichzeitig auf einer Platte, die im CI-Lauf knapp bemessen ist.
    archiv.unlink(missing_ok=True)
    return ordner / config.FI_GPKG_NAME


# --- Geometrie --------------------------------------------------------------

def _wkb(blob: bytes) -> bytes | None:
    """
    Schält den WKB-Körper aus einem GPKG-Geometrieblob.

    Aufbau laut GeoPackage-Norm: 'GP', Version, Flags, SRS-Id (8 Byte), dann
    optional der Hüllkörper, dann WKB. Bit 1–3 der Flags sagen, wie groß der
    Hüllkörper ist; Bit 5 markiert eine leere Geometrie.
    """
    if not blob or len(blob) < 8 or blob[0:2] != b"GP":
        return None
    flags = blob[3]
    if flags & 0x10:                      # leere Geometrie
        return None
    huelle = _HUELLE_BYTE.get((flags >> 1) & 0x07)
    if huelle is None:
        return None
    return blob[8 + huelle:]


def _aggregieren(gpkg: Path) -> tuple[dict[str, dict[int, float]], dict[int, float]]:
    """
    Summiert die Fläche je (Gemeinde, Aggregatklasse) und je Detailklasse.

    Gelesen wird in Blöcken, weil die Tabelle mehrere Millionen Polygone
    führt und `shapely.from_wkb` auf einer Liste deutlich schneller ist als
    Zeile für Zeile.
    """
    try:
        from shapely import area, from_wkb
    except ImportError:
        abbruch(
            "Flächeninanspruchnahme: Paket `shapely` (>=2.0) fehlt — ohne es "
            "gibt es keine Fläche, weil das GeoPackage keine Spalte dafür hat."
        )

    je_gemeinde: dict[str, dict[int, float]] = {}
    je_detail: dict[int, float] = {}
    ohne_gkz = 0
    ohne_geometrie = 0
    zeilen = 0

    verbindung = sqlite3.connect(f"file:{gpkg}?mode=ro", uri=True)
    try:
        _pruefe_schema(verbindung)
        zeiger = verbindung.cursor()
        zeiger.execute(
            f'SELECT "GKZ", "OGD_FI", "OGD_FI_agg", "{config.FI_GEOMETRIE_SPALTE}" '
            f'FROM "{config.FI_TABELLE}"'
        )
        while True:
            block = zeiger.fetchmany(config.FI_BATCH)
            if not block:
                break
            koerper = []
            merkmale = []
            for kennziffer, detail, aggregat, blob in block:
                zeilen += 1
                if not kennziffer:
                    ohne_gkz += 1
                    continue
                roh = _wkb(blob)
                if roh is None:
                    ohne_geometrie += 1
                    continue
                koerper.append(roh)
                merkmale.append((str(kennziffer), detail, aggregat))
            if not koerper:
                continue
            flaechen = area(from_wkb(koerper))
            for (kennziffer, detail, aggregat), flaeche in zip(merkmale, flaechen):
                wert = float(flaeche)
                if wert <= 0:
                    continue
                # Fällt das Aggregat aus, trägt der Detailcode die Klasse:
                # 2112 gehört zu 210, 101 zu 100. Ohne diesen Rückfall
                # verschwänden solche Zeilen lautlos aus der Summe.
                klasse = int(aggregat) if aggregat else _klasse_aus_detail(detail)
                if klasse is None:
                    continue
                je_gemeinde.setdefault(kennziffer, {})
                je_gemeinde[kennziffer][klasse] = (
                    je_gemeinde[kennziffer].get(klasse, 0.0) + wert)
                if detail:
                    je_detail[int(detail)] = je_detail.get(int(detail), 0.0) + wert
            if zeilen % (config.FI_BATCH * 20) == 0:
                log(f"    … {zeilen:,} Polygone gelesen")
    finally:
        verbindung.close()

    log(f"    {zeilen:,} Polygone, {len(je_gemeinde):,} Gemeinden")
    if ohne_gkz:
        warnen(f"Flächeninanspruchnahme: {ohne_gkz:,} Polygone ohne GKZ — "
               f"sie fallen aus der Karte und aus der Summe.")
    if ohne_geometrie:
        warnen(f"Flächeninanspruchnahme: {ohne_geometrie:,} Polygone ohne "
               f"lesbare Geometrie.")
    return je_gemeinde, je_detail


def _klasse_aus_detail(detail) -> int | None:
    """Level-3-Code auf sein Aggregat zurückführen (2112 → 210, 101 → 100)."""
    if not detail:
        return None
    code = int(detail)
    for aggregat in sorted(config.FI_KLASSEN, reverse=True):
        if code == aggregat:
            return aggregat
    if 100 <= code < 200:
        return 100
    if 210 <= code < 220 or code == 2112:
        return 210
    if code == 220:
        return 220
    if 300 <= code < 400:
        return 300
    if 400 <= code < 500:
        return 400
    if 500 <= code < 600:
        return 500
    return None


def _pruefe_schema(verbindung: sqlite3.Connection) -> None:
    """
    Hält das Schema gegen das, was am 09.09.2026 gemessen wurde.

    Nicht aus Misstrauen gegen die Quelle, sondern weil ein umbenanntes Feld
    hier sonst eine leere Karte erzeugt statt einer Fehlermeldung.
    """
    vorhanden = {
        zeile[1] for zeile in
        verbindung.execute(f'PRAGMA table_info("{config.FI_TABELLE}")')
    }
    if not vorhanden:
        abbruch(
            f"Flächeninanspruchnahme: Tabelle {config.FI_TABELLE} fehlt im "
            f"GeoPackage. Der Layer wurde umbenannt."
        )
    fehlend = {"GKZ", "OGD_FI", "OGD_FI_agg", config.FI_GEOMETRIE_SPALTE} - vorhanden
    if fehlend:
        abbruch(
            f"Flächeninanspruchnahme: Spalten fehlen: {sorted(fehlend)}. "
            f"Vorhanden: {sorted(vorhanden)}"
        )


# --- Klassen und Text -------------------------------------------------------

def _klassen(werte: list[float]) -> list[float]:
    """
    Fünf Klassen aus der Verteilung, auf halbe Prozentpunkte gerundet.

    WARUM FEINER ALS BEI DEN BAULANDRESERVEN: Dort laufen die Anteile über
    die ganze Skala, hier drängt sich fast alles unter 20 % — der Bundeswert
    liegt bei 6,8 %. Zehnerstufen ergäben eine Karte mit zwei besetzten
    Klassen.
    """
    sortiert = sorted(werte)
    if not sortiert:
        return [2.0, 4.0, 8.0, 15.0]

    def quantil(anteil: float) -> float:
        return sortiert[min(int(anteil * (len(sortiert) - 1)), len(sortiert) - 1)]

    grenzen: list[float] = []
    for anteil in (0.2, 0.4, 0.6, 0.8):
        gerundet = round(quantil(anteil) * 2) / 2
        if grenzen and gerundet <= grenzen[-1]:
            gerundet = grenzen[-1] + 0.5
        grenzen.append(max(0.5, gerundet))
    return grenzen


def _hinweis(bund_prozent: float, hoechste: dict) -> str:
    """
    Hinweiszeile im Hausmaß 150–234 Zeichen.

    Die Auflage des UBA steht ausdrücklich drin: Stand, nicht Entwicklung.
    Sie ist Bedingung der Freigabe und keine Fußnote.
    """
    # Dezimalkomma, nicht Punkt: Die Zeile steht im deutschen Fließtext der
    # Seite, nicht in einer Tabelle.
    bund = f"{bund_prozent:.1f}".replace(".", ",")
    spitze = f"{hoechste['anteil']:.1f}".replace(".", ",")
    # Zwei Fassungen, weil der Spitzenreiter den Satz mitbestimmt:
    # „Wien" kostet vier Zeichen, „Sankt Martin am Grimming" vierundzwanzig.
    # Ohne die kurze Fassung risse ein langer Gemeindename das Hausmaß.
    lang = (
        f"{bund} % der Fläche Österreichs sind verbaut oder als Verkehrsweg "
        f"beansprucht, in {hoechste['name']} {spitze} %. Die Karte zeigt den "
        f"Stand, nicht die Entwicklung — wie stark eine Gemeinde zuletzt "
        f"zugelegt hat, ist derzeit nicht verlässlich zu sagen."
    )
    kurz = (
        f"{bund} % der Fläche Österreichs sind verbaut oder als Verkehrsweg "
        f"beansprucht, in {hoechste['name']} {spitze} %. Die Karte zeigt den "
        f"Stand, nicht die Entwicklung — die Veränderung je Gemeinde ist "
        f"derzeit nicht belastbar."
    )
    zeile = lang if len(lang) <= 234 else kurz
    if not 150 <= len(zeile) <= 234:
        warnen(f"Flächeninanspruchnahme: Hinweiszeile {len(zeile)} Zeichen, "
               f"Hausmaß ist 150–234.")
    return zeile


# --- Aufbau -----------------------------------------------------------------

def _gemeindeflaechen() -> dict[str, tuple[str, float]]:
    if not GRENZEN.exists():
        abbruch(
            "Flächeninanspruchnahme: gemeinden.json fehlt. `gemeindegrenzen` "
            "muss vor diesem Modul laufen — von dort kommt der Nenner."
        )
    daten = json.loads(GRENZEN.read_text(encoding="utf-8"))
    if daten.get("aufbau", 0) < 3:
        abbruch(
            f"Flächeninanspruchnahme: gemeinden.json steht auf Aufbau "
            f"{daten.get('aufbau')} und führt kein `flaeche_m2`. "
            f"GRENZEN_AUFBAU hochzählen und die Umrisse neu bauen lassen."
        )
    flaechen: dict[str, tuple[str, float]] = {}
    for merkmal in daten.get("features", []):
        eigenschaften = merkmal.get("properties") or {}
        kennziffer = str(eigenschaften.get("gkz", ""))
        flaeche = eigenschaften.get("flaeche_m2")
        if kennziffer and flaeche:
            flaechen[kennziffer] = (eigenschaften.get("name", ""), float(flaeche))
    return flaechen


def baue_flaecheninanspruchnahme() -> dict | None:
    log("\n[Karte] Flächeninanspruchnahme je Gemeinde — ÖROK/Umweltbundesamt")

    if ZIEL.exists():
        try:
            vorhanden = json.loads(ZIEL.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            vorhanden = {}
        if (vorhanden.get("stand") == config.FI_STAND_JAHR
                and vorhanden.get("aufbau") == config.FI_AUFBAU):
            log(f"    {ZIEL.name} liegt auf Stand {config.FI_STAND_JAHR} "
                f"(Aufbau {config.FI_AUFBAU}) vor — kein 1,27-GiB-Abruf")
            return vorhanden

    nenner = _gemeindeflaechen()
    ordner = Path(tempfile.mkdtemp(prefix="fi-ogd-"))
    try:
        archiv = ordner / config.FI_DATEI
        _herunterladen(archiv)
        gpkg = _entpacken(archiv, ordner)
        je_gemeinde, je_detail = _aggregieren(gpkg)
    finally:
        shutil.rmtree(ordner, ignore_errors=True)

    gemeinden = []
    summe_m2 = 0.0
    ohne_nenner = []
    for kennziffer, klassen in sorted(je_gemeinde.items()):
        gesamt = sum(klassen.values())
        summe_m2 += gesamt
        if kennziffer not in nenner:
            ohne_nenner.append(kennziffer)
            continue
        name, flaeche = nenner[kennziffer]
        gemeinden.append({
            "gkz": kennziffer,
            "name": name,
            "fi_ha": round(gesamt / 10_000, 1),
            "flaeche_ha": round(flaeche / 10_000, 1),
            "anteil": round(100 * gesamt / flaeche, 2) if flaeche else None,
            "klassen": {str(k): round(v / 10_000, 1)
                        for k, v in sorted(klassen.items())},
        })

    if ohne_nenner:
        warnen(
            f"Flächeninanspruchnahme: {len(ohne_nenner)} Kennziffern ohne "
            f"Umriss — sie bleiben grau: {sorted(ohne_nenner)[:12]}"
        )
    if not config.FI_GEMEINDEN_MIN <= len(gemeinden) <= config.FI_GEMEINDEN_MAX:
        warnen(
            f"Flächeninanspruchnahme: {len(gemeinden)} Gemeinden, erwartet "
            f"waren {config.FI_GEMEINDEN_MIN}–{config.FI_GEMEINDEN_MAX}."
        )

    summe_km2 = summe_m2 / 1e6
    abweichung = 100 * (summe_km2 - config.FI_BUND_KM2) / config.FI_BUND_KM2
    log(f"    Summe über alle Gemeinden: {summe_km2:,.1f} km² gegen "
        f"{config.FI_BUND_KM2:,.1f} km² laut Bericht ({abweichung:+.2f} %)")
    if abs(abweichung) > config.FI_ABWEICHUNG_PROZENT:
        warnen(
            f"Flächeninanspruchnahme: Die Eigenaggregation weicht um "
            f"{abweichung:+.2f} % vom veröffentlichten Bundeswert ab. Die "
            f"Abweichung gehört beziffert in die Methodik, nicht geglättet."
        )

    mit_anteil = [g for g in gemeinden if g["anteil"] is not None]
    hoechste = max(mit_anteil, key=lambda g: g["anteil"])
    bund_prozent = 100 * summe_m2 / sum(f for _, f in nenner.values())

    quelle_vermerken(
        name=("ÖROK-Monitoring Flächeninanspruchnahme 2025 — "
              "Berechnung: Umweltbundesamt, Aggregation je Gemeinde: eigene"),
        url="https://www.data.gv.at/datasets/46f43f1c-1f8e-47eb-8526-bb0e683361b5",
        lizenz="CC BY 4.0",
        stand=str(config.FI_STAND_JAHR),
        art="api",
    )

    ergebnis = {
        "stand": config.FI_STAND_JAHR,
        "aufbau": config.FI_AUFBAU,
        "gemeinden": gemeinden,
        "klassengrenzen": _klassen([g["anteil"] for g in mit_anteil]),
        "klassennamen": {str(k): v for k, v in config.FI_KLASSEN.items()},
        "oesterreich": {
            "fi_km2": round(summe_km2, 1),
            "anteil": round(bund_prozent, 2),
            "bericht_km2": config.FI_BUND_KM2,
            "abweichung_prozent": round(abweichung, 2),
            "detail_ha": {str(k): round(v / 10_000, 1)
                          for k, v in sorted(je_detail.items())},
        },
        "auflage": (
            "Zustandskarte. Die Veränderungen 2022–2025 sind auf "
            "Gemeindeebene laut Umweltbundesamt derzeit nicht valide."
        ),
        "hinweis": _hinweis(bund_prozent, hoechste),
    }
    schreibe("flaecheninanspruchnahme", ergebnis)
    return ergebnis
