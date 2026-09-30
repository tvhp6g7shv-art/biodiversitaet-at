"""
Stehendes Totholz im Ertragswald — Österreichische Waldinventur.

WARUM DIESER ABSCHNITT: Totholz ist der am besten belegte Einzeltreiber der
Waldbiodiversität. Ein Viertel der Waldarten lebt von zerfallendem Holz.
Waldfläche allein sagt darüber nichts — Österreich hat viel Wald, die Frage
ist, wie viel totes Holz darin stehen bleibt.

DREI FALLSTRICKE, die in dieser Datei vermieden werden:

1. STEHEND IST NICHT GESAMT. Die ÖWI veröffentlicht ausschliesslich stehendes
   Totholz (ab BHD 5 cm). Liegendes Totholz und Stöcke werden gemessen, sind
   aber laut Glossar „nicht Teil der Standardergebnisse". Die
   Naturwald-Referenzwerte beziehen sich dagegen auf GESAMTtotholz. Deshalb
   stehen die Bundeslandwerte (stehend) und die Naturwald-Einordnung (gesamt)
   hier in getrennten Feldern und dürfen in der Grafik nicht gegeneinander
   gestellt werden.

2. HOHE WERTE SIND NICHT AUTOMATISCH GUTE WERTE. Über acht Bundesländer ohne
   Wien korreliert das stehende Totholz mit dem Fichtenanteil zu r = +0,66.
   Salzburg, Tirol und Vorarlberg haben viel Fichte UND viel Totholz — weil
   Steilhänge die Nutzung erschweren und der Borkenkäfer stehende tote
   Fichten hinterlässt. Wer die Karte als Naturnähe-Rangliste liest, liegt
   falsch. Das Feld `doppeldeutig` trägt diesen Hinweis in die Grafik.

3. WIEN IST UNBRAUCHBAR. 28,9 ± 11,2 Vfm/ha, also ±38,8 % Stichprobenfehler
   auf 9.000 ha Wald. Der Wert wird mitgeliefert, aber als `belastbar: False`
   gekennzeichnet, damit die Karte ihn nicht gleichrangig einfärbt.

WARUM GEPFLEGT UND NICHT AUS DER API: waldinventur.at hat keine dokumentierte
Schnittstelle. Die Werte liegen zwar als statisches JSON unter
`/data/{periode}/datajson/{id}.json`, das sind aber interne Pfade der Web-App
ohne Zusage der Stabilität. Ausserdem bindet das BFW-Impressum die
Weiterverwendung an eine schriftliche Zustimmung — ein Abruf bei jedem Lauf
wäre auch deshalb unpassend. Die Zahlen stehen hier abgeschrieben, mit
Quelle und Abrufdatum, wie bei den übrigen gepflegten Reihen.

Abgerufen und gegen die Bundeswerte gegengeprüft am 27.08.2026.
"""

from __future__ import annotations

import json

import config
from gemeinsam import log, pflegepruefung, quelle_vermerken, warnen

# ---------------------------------------------------------------------------
# Zeitreihe Bund — stehendes Totholz im Ertragswald, Vfm/ha
# Quelle: waldinventur.at, Indikator 378_l_A, Regionscode Lbfi=0
# ---------------------------------------------------------------------------
REIHE_BUND = [
    {"periode": "1992/96", "wert": 4.5, "fehler": 0.2},
    {"periode": "2000/02", "wert": 6.1, "fehler": 0.2},
    {"periode": "2007/09", "wert": 8.4, "fehler": 0.3},
    {"periode": "2016/21", "wert": 9.7, "fehler": 0.3},
    {"periode": "2018/23", "wert": 10.5, "fehler": 0.4},
]

# ---------------------------------------------------------------------------
# Bundesländer — ÖWI 2018/23
# Der Name muss exakt dem `bundesland`-Attribut der Geometrie entsprechen,
# sonst bleibt die Fläche grau. Die Zuordnung wird unten geprüft.
# ---------------------------------------------------------------------------
BUNDESLAENDER = [
    {"name": "Burgenland", "wert": 6.3, "fehler": 1.0},
    {"name": "Kärnten", "wert": 9.1, "fehler": 0.8},
    {"name": "Niederösterreich", "wert": 10.4, "fehler": 0.9},
    {"name": "Oberösterreich", "wert": 9.9, "fehler": 0.9},
    {"name": "Salzburg", "wert": 13.0, "fehler": 2.0},
    {"name": "Steiermark", "wert": 10.4, "fehler": 0.7},
    {"name": "Tirol", "wert": 12.9, "fehler": 1.1},
    {"name": "Vorarlberg", "wert": 13.6, "fehler": 3.0},
    {"name": "Wien", "wert": 28.9, "fehler": 11.2},
]

# Ab diesem relativen Stichprobenfehler gilt ein Wert als nicht belastbar.
# 25 % ist gesetzt, nicht abgeleitet: Vorarlberg liegt mit 22,1 % gerade
# darunter und bleibt drin, Wien mit 38,8 % fällt heraus.
FEHLERSCHWELLE_PROZENT = 25.0

# ---------------------------------------------------------------------------
# Einordnung — GESAMTtotholz, nicht stehend. Andere Bezugsgrösse!
# Quelle Ertragswald: Waldbiodiversitätsbericht, BFW-Bericht 155/2026,
# Ertragswald ab 10 cm Durchmesser: 9,8 stehend + 13,4 liegend.
# Quelle Naturwaldreservate: Oettel et al. 2020, Forest Ecology and
# Management 463:118016 — Spanne der MITTELWERTE JE WALDTYP, nicht die
# Spanne einzelner Reservate.
# ---------------------------------------------------------------------------
EINORDNUNG = {
    "ertragswald_stehend": 9.8,
    "ertragswald_liegend": 13.4,
    "naturwald_von": 23,
    "naturwald_bis": 109,
    "urwald_rothwald": 300,
}


# Teile unter diesem Anteil an der Landesfläche gelten als Verschmelzungs-
# splitter und fliegen raus. Siehe Begründung in _geometrie_bundeslaender.
ANTEIL_MINDEST = 0.001          # 0,1 %

# Vereinfachungstoleranz in Grad. 0,002 entspricht rund 150 m — auf einer
# Übersichtskarte Österreichs weniger als ein Bildpunkt.
VEREINFACHUNG = 0.002


def _splitter_entfernen(flaeche, anteil_mindest: float):
    """
    Kleinstteile aus einem MultiPolygon werfen, gemessen am Anteil an der
    Gesamtfläche des Landes. Einzelne Polygone bleiben unberührt.
    """
    if not hasattr(flaeche, "geoms"):
        return flaeche
    from shapely.geometry import MultiPolygon

    teile = list(flaeche.geoms)
    gesamt = sum(t.area for t in teile)
    if not gesamt:
        return flaeche
    behalten = [t for t in teile if t.area / gesamt >= anteil_mindest]
    if not behalten:
        return flaeche
    return behalten[0] if len(behalten) == 1 else MultiPolygon(behalten)


def _geometrie_bundeslaender(bezirke_geo: dict) -> dict | None:
    """
    Bezirksgeometrie zu neun Bundesländern verschmelzen.

    Die Quelle ist die bereits im Repo liegende Bezirkskarte des
    Schwesterprojekts (80 Regionen aus dem Statistik-Austria-WFS, CC BY 4.0).
    Jedes Feature trägt ein `bundesland`-Attribut — daraus lassen sich die
    neun Flächen ohne zweiten Download gewinnen.

    WARUM VERSCHMELZEN UND NICHT NUR SAMMELN: Ein MultiPolygon aus 21
    niederösterreichischen Bezirken behält alle Innengrenzen. ECharts zeichnet
    jede davon als Rand — die Karte sähe nach Bezirken aus, obwohl die Daten
    nur je Bundesland vorliegen. Das wäre eine Genauigkeit, die die Zahlen
    nicht hergeben.
    """
    try:
        from shapely.geometry import shape, mapping as geo_mapping
        from shapely.ops import unary_union
        from shapely.validation import make_valid
    except ImportError:
        warnen("Totholz: shapely fehlt — Karte entfällt, die Tabelle bleibt")
        return None

    nach_land: dict[str, list] = {}
    for merkmal in bezirke_geo.get("features", []):
        land = (merkmal.get("properties") or {}).get("bundesland")
        if not land:
            continue
        geometrie = shape(merkmal["geometry"])
        if not geometrie.is_valid:
            # Selbstberührende Ränder lassen unary_union scheitern.
            # make_valid repariert sie, ohne die Fläche zu verschieben.
            geometrie = make_valid(geometrie)
        nach_land.setdefault(land, []).append(geometrie)

    merkmale = []
    for land, teile in sorted(nach_land.items()):
        flaeche = unary_union(teile)
        # Nach dem Verschmelzen bleiben oft haarfeine Schlitze zwischen
        # Bezirken übrig, weil die Ränder nicht bitgleich sind. Ein winziger
        # Puffer hin und zurück schliesst sie, ohne die Form sichtbar zu
        # verändern (0,0001 Grad sind rund 10 m).
        flaeche = flaeche.buffer(0.0001).buffer(-0.0001)
        if flaeche.is_empty:
            warnen(f"Totholz: {land} ergibt nach dem Verschmelzen keine Fläche")
            continue

        # Der Puffer lässt Splitter zurück: Burgenland zerfällt in drei Teile,
        # Oberösterreich in sechs, obwohl beide zusammenhängen. Gemessen
        # tragen diese Reste 0,000 % der Landesfläche. Echte Exklaven sind
        # deutlich grösser — Osttirol macht 15,9 % von Tirol aus. Die Schwelle
        # von 0,1 % trennt beides sicher; der grösste gemessene Splitter lag
        # bei 0,056 %.
        flaeche = _splitter_entfernen(flaeche, ANTEIL_MINDEST)

        # Für neun Übersichtsflächen ist die Bezirksauflösung Verschwendung:
        # ungekürzt sind es 3,7 MB. Vereinfachen bringt das auf rund ein
        # Zehntel, ohne dass sich der Umriss auf Kartengrösse ändert.
        flaeche = flaeche.simplify(VEREINFACHUNG, preserve_topology=True)

        merkmale.append({
            "type": "Feature",
            "properties": {"name": land},
            "geometry": geo_mapping(flaeche),
        })

    if len(merkmale) != 9:
        warnen(f"Totholz: {len(merkmale)} Bundesländer statt 9 in der Geometrie")

    return {"type": "FeatureCollection", "features": merkmale}


def baue_totholz(bezirke_geo: dict | None = None) -> tuple[dict | None, dict | None]:
    """
    Liefert (daten, geometrie). Die Geometrie ist None, wenn shapely fehlt
    oder keine Bezirksdatei übergeben wurde — der Abschnitt zeigt dann nur
    die Tabelle.
    """
    log("\n[12/13] Totholz — ÖWI 2018/23 (gepflegt)")

    pflegepruefung("totholz", 2025, "ÖWI-Zwischenauswertung 2018/23")

    aktuell = REIHE_BUND[-1]
    erstes = REIHE_BUND[0]

    eintraege = []
    for land in BUNDESLAENDER:
        rel = land["fehler"] / land["wert"] * 100 if land["wert"] else 100.0
        eintraege.append({
            "name": land["name"],
            "wert": land["wert"],
            "fehler": land["fehler"],
            "fehler_relativ": round(rel, 1),
            "belastbar": rel <= FEHLERSCHWELLE_PROZENT,
        })

    belastbare = [e for e in eintraege if e["belastbar"]]
    if not belastbare:
        warnen("Totholz: kein belastbarer Bundeslandwert — Abschnitt entfällt")
        return None, None

    niedrigster = min(belastbare, key=lambda e: e["wert"])
    hoechster = max(belastbare, key=lambda e: e["wert"])
    unbelastbar = [e["name"] for e in eintraege if not e["belastbar"]]

    gesamt = EINORDNUNG["ertragswald_stehend"] + EINORDNUNG["ertragswald_liegend"]

    daten = {
        "stand": "ÖWI 2018/23",
        "abgerufen": "2026-08-27",
        "reihe": REIHE_BUND,
        "bund": aktuell["wert"],
        "bund_fehler": aktuell["fehler"],
        "seit": erstes["periode"],
        "seit_wert": erstes["wert"],
        "faktor_seit_1992": round(aktuell["wert"] / erstes["wert"], 1),
        "eintraege": eintraege,
        "niedrigster": niedrigster,
        "hoechster": hoechster,
        "spanne_faktor": round(hoechster["wert"] / niedrigster["wert"], 1),
        "unbelastbar": unbelastbar,
        "einordnung": {
            **EINORDNUNG,
            "ertragswald_gesamt": round(gesamt, 1),
            "faktor_bis_naturwald_oben": round(EINORDNUNG["naturwald_bis"] / gesamt, 1),
            "faktor_bis_urwald": round(EINORDNUNG["urwald_rothwald"] / gesamt, 1),
        },
        # Diese Zeile ist nicht Schmuck. Ohne sie liest die Karte sich als
        # Naturnähe-Rangliste, und das gibt die Zahl nicht her.
        # Diese Zeile geht als Einordnung unter die Karte und muss die
        # Konvention von 150–234 Zeichen einhalten. Gemessen: 218.
        "doppeldeutig": (
            "Viel totes Holz ist nicht automatisch ein gutes Zeichen: Wo viel "
            "Fichte steht, bleiben oft käferbefallene Bäume stehen, die nicht "
            "aufgearbeitet wurden. Gezählt wird nur stehendes Holz ab 5 cm "
            "Stammdurchmesser."
        ),
        "hinweis": (
            f"Die Waldinventur zählt nur stehendes Totholz ab 5 cm Stammdurchmesser. "
            f"Liegendes Holz wird gemessen, aber nicht veröffentlicht. "
            f"Zwischen dem niedrigsten und dem höchsten Landeswert liegt Faktor "
            f"{round(hoechster['wert'] / niedrigster['wert'], 1)}."
        ),
    }

    quelle_vermerken(
        "Totholz (stehend, Ertragswald)",
        "https://www.waldinventur.at/",
        "BFW — Verwendung mit Quellenangabe, Zustimmung des BFW vom 30.09.2026",
        "ÖWI 2018/23",
        "gepflegt",
    )

    geometrie = _geometrie_bundeslaender(bezirke_geo) if bezirke_geo else None
    if geometrie:
        namen_geo = {f["properties"]["name"] for f in geometrie["features"]}
        namen_daten = {e["name"] for e in eintraege}
        fehlend = namen_daten - namen_geo
        if fehlend:
            warnen(f"Totholz: ohne Geometrie: {', '.join(sorted(fehlend))}")

    log(f"  Bund {aktuell['wert']} Vfm/ha · {len(eintraege)} Bundesländer · "
        f"{len(unbelastbar)} nicht belastbar")

    return daten, geometrie
