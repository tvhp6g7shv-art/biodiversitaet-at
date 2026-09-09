"""
Gemeindegrenzen für die Karte — einmalig gebaut, danach eingefroren.

  Quelle:  Statistik Austria, WFS-Dienst GEODATA
  Lizenz:  CC BY 4.0
  Nennung: „Datenquelle: Statistik Austria — data.statistik.gv.at"
  Geprüft: 27.08.2026 — Layer STATISTIK_AUSTRIA_GEM_20250101 liefert GeoJSON,
           Attribute `g_id` (Gemeindecode) und `g_name`, MultiPolygon,
           Projektion EPSG:31287 (MGI Austria Lambert)

WARUM NICHT BEI JEDEM LAUF: Der Rohabruf ist rund 45 MB. Gemeindegrenzen
ändern sich höchstens jährlich, die Datenreihe dagegen dreijährlich. Das
Modul baut die Datei deshalb nur, wenn sie fehlt oder auf einem anderen
Gebietsstand steht als angefordert. Der Gebietsstand steht in der Datei
selbst — sonst müsste man raten, welchen Stand die eingefrorene Datei hat.

WARUM DER GEBIETSSTAND ZUM STICHJAHR PASSEN MUSS: Die Baulandreserven sind
nach Gemeindekennziffer gruppiert. Wird die Karte gegen einen anderen
Gebietsstand gezeichnet, fallen zusammengelegte oder umnummerierte Gemeinden
lautlos aus der Einfärbung — sie bleiben grau, als hätten sie keine Daten.
Deshalb prüft `pruefe_deckung()` beide Richtungen und meldet jede Kennziffer,
die nur auf einer Seite vorkommt.

WARUM EPSG:31287 UND KEINE GEOGRAFISCHEN KOORDINATEN: Lambert ist für
Österreich flächentreu genug und in der Fläche unverzerrt. Rohe Länge/Breite
würde Österreich in der Karte spürbar in die Breite ziehen, weil ein
Längengrad hier nur rund zwei Drittel eines Breitengrads misst. ECharts
rechnet die Koordinaten ohnehin nur linear auf die Zeichenfläche — es ist
also gleichgültig, welche Einheit sie haben, solange sie projiziert sind.

WARUM TOPOLOGIEERHALTEND VEREINFACHT WIRD: Jedes Polygon für sich zu
vereinfachen ist der naheliegende Weg und der falsche. Zwei benachbarte
Gemeinden teilen sich eine Grenzlinie; werden beide unabhängig ausgedünnt,
entstehen dort weiße Risse und Überlappungen. `topojson` baut die geteilten
Kanten erst zusammen, vereinfacht sie EINMAL und setzt die Flächen danach
wieder zusammen.

NOCH NICHT AM ECHTEN DATENSATZ GEPRÜFT (Stand 27.08.2026): Der Sandkasten
erreicht weder statistik.at noch PyPI-fremde Dienste. Der erste CI-Lauf ist
zugleich die erste Erprobung. Die Prüfungen unten sind deshalb bewusst
gesprächig — sie sollen im Lauf-Protokoll zeigen, was herausgekommen ist,
statt still durchzulaufen.
"""

from __future__ import annotations

import json
from pathlib import Path

import requests

import config
from gemeinsam import abbruch, log, quelle_vermerken, warnen

ZIEL = Path(config.AUSGABE_ORDNER) / "gemeinden.json"


def _abrufen() -> dict:
    log(f"  ↓ Gemeindegrenzen {config.GRENZEN_LAYER} (rund 45 MB)")
    try:
        antwort = requests.get(
            config.GRENZEN_WFS_URL,
            params={
                "service": "WFS",
                "version": "1.0.0",
                "request": "GetFeature",
                "typeName": f"GEODATA:{config.GRENZEN_LAYER}",
                "outputFormat": "application/json",
            },
            timeout=config.GRENZEN_TIMEOUT_SEKUNDEN,
            headers={"User-Agent": "biodiversitaet-at-dashboard/1.0"},
        )
    except requests.RequestException as fehler:
        abbruch(f"Gemeindegrenzen: Abruf fehlgeschlagen\n         {fehler}")
    if antwort.status_code != 200:
        abbruch(
            f"Gemeindegrenzen: HTTP {antwort.status_code}.\n"
            f"         Prüfen, ob der Layer {config.GRENZEN_LAYER} noch "
            f"existiert — die Layernamen tragen das Stichdatum im Namen."
        )
    try:
        roh = antwort.json()
    except ValueError:
        abbruch(
            f"Gemeindegrenzen: Antwort ist kein JSON.\n"
            f"         Erste 200 Zeichen: {antwort.text[:200]!r}"
        )
    anzahl = len(roh.get("features", []))
    log(f"    {anzahl:,} Gemeinden geladen "
        f"({len(antwort.content) / 1_048_576:.1f} MB roh)")
    if anzahl < config.GRENZEN_MIN_GEMEINDEN:
        abbruch(
            f"Gemeindegrenzen: nur {anzahl} Gemeinden. Der Dienst deckelt "
            f"womöglich still bei einer Höchstzahl — `maxFeatures` prüfen."
        )
    return roh


def _wien_zusammenfassen(roh: dict) -> dict:
    """
    Vereinigt die 23 Wiener Bezirke zu einer Fläche mit der Kennziffer 90001.

    WARUM: Die Baulandreserven führen Wien als EINE Gemeinde (90001), der
    Gebietsstand als 23 Bezirke (90101–92301). Ohne diesen Schritt hat die
    Datenzeile keinen Umriss und die 23 Umrisse haben keinen Wert — die
    Bundeshauptstadt bleibt auf der Karte als 23 graue Flecken stehen. Am
    08.09.2026 im ersten echten Lauf genau so gemessen.

    WARUM VOR DEM VEREINFACHEN: Die Rohpolygone der Nachbarbezirke teilen
    exakte Stützpunkte; `unary_union` schließt dort sauber. Nach dem
    Ausdünnen und dem Runden auf ganze Meter liegen die Ränder um bis zu
    einen Meter auseinander, und die Vereinigung hinterließe Schlitze mitten
    in der Stadt. Danach vereinfacht `topojson` Wien wie jede andere Fläche,
    und die Außengrenze bleibt mit Niederösterreich topologisch geteilt.

    WARUM NICHT EINFACH ALS MULTIPOLYGON SAMMELN: Ein MultiPolygon aus 23
    Teilen behält die Bezirksgrenzen als Ränder — sie würden als Striche
    quer durch Wien gezeichnet. Die Vereinigung löst die inneren Kanten auf.
    """
    bezirke = [
        m for m in roh.get("features", [])
        if str((m.get("properties") or {}).get("g_id", ""))
        .startswith(config.GRENZEN_WIEN_ZIFFER)
    ]
    if not bezirke:
        warnen(
            f"Gemeindegrenzen: keine Kennziffer beginnt mit "
            f"{config.GRENZEN_WIEN_ZIFFER!r} — Wien fehlt im Gebietsstand?"
        )
        return roh

    kennziffern = {str(m["properties"]["g_id"]) for m in bezirke}
    if kennziffern == {config.GRENZEN_WIEN_GKZ}:
        log("    Wien liegt bereits als eine Fläche vor — nichts zu tun")
        return roh

    try:
        from shapely.geometry import mapping, shape
        from shapely.ops import unary_union
    except ImportError:
        abbruch(
            "Gemeindegrenzen: Paket `shapely` fehlt. "
            "In etl/requirements.txt eintragen und neu installieren."
        )

    formen = [shape(m["geometry"]) for m in bezirke]
    vereint = unary_union(formen)

    # Gegenprobe: Die Vereinigung darf nur die inneren Grenzlinien schlucken,
    # keine Fläche. Überlappen sich die Bezirke oder klafft eine Lücke, weicht
    # die Summe der Einzelflächen von der Gesamtfläche ab.
    summe = sum(f.area for f in formen)
    if summe > 0:
        abweichung = 100 * abs(summe - vereint.area) / summe
        log(f"    Wien: {len(bezirke)} Bezirke vereinigt, "
            f"{vereint.area / 1_000_000:,.1f} km², "
            f"Flächenabweichung {abweichung:.3f} %")
        if abweichung > 0.5:
            warnen(
                f"Gemeindegrenzen: Wiens Bezirke ergeben vereinigt "
                f"{abweichung:.2f} % weniger oder mehr Fläche als ihre Summe "
                f"— sie überlappen sich oder es klafft eine Lücke."
            )

    geometrie = mapping(vereint)
    if geometrie["type"] == "Polygon":
        # Die übrigen Umrisse sind MultiPolygon; einheitlich halten, damit
        # nachgelagerte Prüfungen nicht zwei Fälle unterscheiden müssen.
        geometrie = {"type": "MultiPolygon",
                     "coordinates": [geometrie["coordinates"]]}

    # Über die Kennziffer filtern, nicht über `m not in bezirke`: Ein
    # `in`-Vergleich auf Feature-Wörterbüchern zieht jedes Mal die ganze
    # Geometrie durch — bei 2.100 Umrissen mal 23 Bezirken ist das minutenlang.
    uebrige = [
        m for m in roh.get("features", [])
        if str((m.get("properties") or {}).get("g_id", "")) not in kennziffern
    ]
    uebrige.append({
        "type": "Feature",
        "properties": {"g_id": config.GRENZEN_WIEN_GKZ, "g_name": "Wien"},
        "geometry": geometrie,
    })
    return {**roh, "features": uebrige}


def _vereinfachen(roh: dict) -> dict:
    """
    Dünnt die Umrisse aus, ohne die gemeinsamen Grenzen aufzureißen.

    Die Toleranz ist in Metern (EPSG:31287). 150 m sind bei einer Karte, die
    ganz Österreich auf gut 1.000 Bildpunkte bringt, deutlich unter einem
    Pixel — sichtbar wird davon nichts, die Datei schrumpft aber um mehr als
    das Zwanzigfache.
    """
    try:
        import topojson
    except ImportError:
        abbruch(
            "Gemeindegrenzen: Paket `topojson` fehlt. "
            "In etl/requirements.txt eintragen und neu installieren."
        )

    topo = topojson.Topology(roh, prequantize=False)
    vereinfacht = topo.toposimplify(config.GRENZEN_TOLERANZ_METER)
    ergebnis = json.loads(vereinfacht.to_geojson())

    # Koordinaten auf ganze Meter runden. Nachkommastellen in einer Karte,
    # die auf 150 m ausgedünnt ist, sind reine Dateigröße.
    def runden(knoten):
        if isinstance(knoten, list):
            if knoten and isinstance(knoten[0], (int, float)):
                return [round(x) for x in knoten]
            return [runden(k) for k in knoten]
        return knoten

    for merkmal in ergebnis.get("features", []):
        geo = merkmal.get("geometry")
        if geo and "coordinates" in geo:
            geo["coordinates"] = runden(geo["coordinates"])
    return ergebnis


def _flaechen(roh: dict) -> dict[str, float]:
    """
    Gemeindefläche in m², aus den ROHEN Umrissen gerechnet.

    WARUM HIER UND NICHT SPÄTER: Die Karte wird mit 150 m Toleranz
    ausgedünnt. Eine Fläche aus der ausgedünnten Geometrie wäre um Prozente
    daneben und damit als Nenner unbrauchbar — und genau als Nenner braucht
    sie `flaecheninanspruchnahme.py`. Gerechnet wird deshalb vor
    `_vereinfachen()`, aber nach `_wien_zusammenfassen()`, damit Wien mit
    einer Fläche und nicht mit 23 dasteht.

    WARUM OHNE FREMDDATENSATZ: EPSG:31287 ist metrisch und für Österreich
    flächentreu genug; die Fläche fällt aus der Geometrie ab, die ohnehin
    heruntergeladen wird. Eine zweite Quelle für Gemeindeflächen wäre ein
    zweiter Datenweg, der bei jedem Gebietsstand nachgezogen werden müsste.
    """
    try:
        from shapely.geometry import shape
    except ImportError:
        abbruch(
            "Gemeindegrenzen: Paket `shapely` fehlt — ohne es gibt es keine "
            "Gemeindefläche und damit keinen Nenner für die FI-Karte."
        )
    flaechen: dict[str, float] = {}
    for merkmal in roh.get("features", []):
        kennziffer = str((merkmal.get("properties") or {}).get("g_id", ""))
        if not kennziffer:
            continue
        try:
            flaechen[kennziffer] = float(shape(merkmal["geometry"]).area)
        except Exception as fehler:          # noqa: BLE001
            warnen(f"Gemeindegrenzen: Fläche für {kennziffer} nicht "
                   f"berechenbar ({fehler})")
    log(f"    Gemeindeflächen aus den Rohumrissen: {len(flaechen):,} Werte, "
        f"Summe {sum(flaechen.values()) / 1e6:,.0f} km²")
    return flaechen


def _eigenschaften(kennziffer: str, name: str,
                   flaechen: dict[str, float] | None) -> dict:
    """
    `name` und `gkz` wie bisher, dazu `flaeche_m2`, wo sie vorliegt.

    Die Fläche wird auf ganze Quadratmeter gerundet — Nachkommastellen einer
    Gemeindefläche blähen die Kartendatei auf und sagen nichts.
    """
    eigenschaften = {"name": name, "gkz": kennziffer}
    wert = (flaechen or {}).get(kennziffer)
    if wert:
        eigenschaften["flaeche_m2"] = round(wert)
    return eigenschaften


def _aufraeumen(daten: dict, flaechen: dict[str, float] | None = None) -> dict:
    """
    Behält nur, was die Karte braucht: Kennziffer, Name, Umriss.

    ECharts erwartet den Namen, unter dem eingefärbt wird, in
    `properties.name`. Die Kennziffer bleibt als `gkz` daneben, weil die
    Verknüpfung mit den Daten über sie läuft und nicht über den Namen —
    Gemeindenamen sind in Österreich nicht eindeutig.
    """
    merkmale = []
    for m in daten.get("features", []):
        eigenschaften = m.get("properties") or {}
        kennziffer = eigenschaften.get("g_id")
        name = eigenschaften.get("g_name")
        if not kennziffer or not name:
            warnen(f"Gemeindegrenzen: Umriss ohne g_id/g_name: {eigenschaften}")
            continue
        merkmale.append({
            "type": "Feature",
            "properties": _eigenschaften(str(kennziffer), name, flaechen),
            "geometry": m.get("geometry"),
        })
    return {
        "type": "FeatureCollection",
        "gebietsstand": config.GRENZEN_LAYER,
        "aufbau": config.GRENZEN_AUFBAU,
        "quelle": "Statistik Austria — data.statistik.gv.at",
        "lizenz": "CC BY 4.0",
        "projektion": "EPSG:31287",
        "features": merkmale,
    }


def pruefe_deckung(grenzen: dict, kennziffern_daten: set[str]) -> None:
    """
    Hält Karte und Daten gegeneinander — in BEIDEN Richtungen.

    Nur zu prüfen, ob jede Gemeinde der Daten einen Umriss hat, übersieht den
    häufigeren Fall: ein Umriss ohne Daten bleibt grau und sieht aus wie ein
    Messwert („hier gibt es keine Reserven"), ist aber ein Verknüpfungsfehler.
    """
    kennziffern_karte = {m["properties"]["gkz"] for m in grenzen["features"]}
    ohne_umriss = sorted(kennziffern_daten - kennziffern_karte)
    ohne_daten = sorted(kennziffern_karte - kennziffern_daten)

    log(f"    Deckung: {len(kennziffern_karte):,} Umrisse, "
        f"{len(kennziffern_daten):,} Gemeinden mit Daten")
    if ohne_umriss:
        warnen(
            f"Gemeindegrenzen: {len(ohne_umriss)} Gemeinden haben Daten, aber "
            f"keinen Umriss: {ohne_umriss[:8]}. Gebietsstand "
            f"({config.GRENZEN_LAYER}) passt womöglich nicht zum Stichjahr."
        )
    if ohne_daten:
        # Wien ist der bekannte Sonderfall: die Baulandreserven führen Wien als
        # EINE Gemeinde (90001), manche Grenzdatensätze als 23 Bezirke.
        warnen(
            f"Gemeindegrenzen: {len(ohne_daten)} Umrisse ohne Daten — sie "
            f"bleiben grau: {ohne_daten[:8]}"
        )


def baue_gemeindegrenzen(kennziffern_daten: set[str] | None = None) -> None:
    log("\n[Karte] Gemeindegrenzen — Statistik Austria")

    if ZIEL.exists():
        try:
            vorhanden = json.loads(ZIEL.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            vorhanden = {}
        # BEIDE Bedingungen, nicht nur der Gebietsstand: Eine Änderung am
        # Aufbau der Datei (etwa das Zusammenfassen Wiens am 08.09.2026) käme
        # sonst nie an — der Gebietsstand heißt ja weiter gleich, und das
        # Modul würde die alte Datei zufrieden liegen lassen.
        if (vorhanden.get("gebietsstand") == config.GRENZEN_LAYER
                and vorhanden.get("aufbau") == config.GRENZEN_AUFBAU):
            log(f"    {ZIEL.name} liegt auf {config.GRENZEN_LAYER} "
                f"(Aufbau {config.GRENZEN_AUFBAU}) vor — nichts zu tun "
                f"({ZIEL.stat().st_size / 1024:,.0f} KB)")
            if kennziffern_daten:
                pruefe_deckung(vorhanden, kennziffern_daten)
            return
        log(f"    Neubau nötig: Gebietsstand {vorhanden.get('gebietsstand')} "
            f"→ {config.GRENZEN_LAYER}, Aufbau {vorhanden.get('aufbau')} "
            f"→ {config.GRENZEN_AUFBAU}")

    # Reihenfolge ist Absicht: Wien vereinigen, DANN die Flächen aus den
    # rohen Umrissen rechnen, ERST DANN ausdünnen. Wer die Fläche aus der
    # ausgedünnten Geometrie nimmt, misst den Nenner falsch.
    roh = _wien_zusammenfassen(_abrufen())
    flaechen = _flaechen(roh)
    fertig = _aufraeumen(_vereinfachen(roh), flaechen)

    ZIEL.parent.mkdir(parents=True, exist_ok=True)
    with ZIEL.open("w", encoding="utf-8") as datei:
        json.dump(fertig, datei, ensure_ascii=False, separators=(",", ":"))
    groesse = ZIEL.stat().st_size / 1024
    log(f"    {ZIEL.name}  ({groesse:,.0f} KB, "
        f"{len(fertig['features']):,} Umrisse)")

    if groesse > config.GRENZEN_MAX_KB:
        warnen(
            f"Gemeindegrenzen: {groesse:,.0f} KB überschreiten die Grenze von "
            f"{config.GRENZEN_MAX_KB:,} KB. Die Karte lädt dann spürbar "
            f"langsam — Toleranz in config.GRENZEN_TOLERANZ_METER erhöhen."
        )

    if kennziffern_daten:
        pruefe_deckung(fertig, kennziffern_daten)

    quelle_vermerken(
        name="Gemeindegrenzen — Statistik Austria",
        url="https://data.statistik.gv.at/web/meta.jsp?dataset=OGDEXT_GEM_1",
        lizenz="CC BY 4.0",
        stand=config.GRENZEN_LAYER[-8:-4],
        art="api",
    )
