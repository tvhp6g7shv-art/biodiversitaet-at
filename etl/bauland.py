"""
Baulandbilanz — was gebaut wurde und was neu gewidmet wurde, je Bundesland.

QUELLE: ÖROK-Monitoring Baulandreserven, Datei
`OEROK-Monitoring_Baulandreserven_Stand_2025-12-01.xlsx` (README-Version 7.0),
Blätter „Übersicht Ö+BL 2022“ und „Übersicht Ö+BL 2025“. CC BY 4.0,
Berechnung: Umweltbundesamt im Auftrag der ÖROK.

WARUM NICHT DIE GEMEINDEKARTE: `baulandreserven.py` liegt daneben und rechnet
aus derselben Erhebung eine Gemeindekarte (Anteil der Reserve, der heute
landwirtschaftlich genutzt wird). Entscheid des Users vom 09.09.2026: Für
diesen Abschnitt trägt der Bundesländervergleich. Das Kartenmodul bleibt
unangetastet im Repo — es ist die Vorarbeit eines möglichen späteren
Abschnitts, kein toter Code.

WAS DER ABSCHNITT ZEIGT und warum ausgerechnet das:

Die naheliegende Zahl wäre der Anteil unbebauten Baulands — 19,6 Prozent,
„jeder fünfte Quadratmeter“. Der Anteil ist zwischen 2022 und 2025 in JEDEM
Bundesland gesunken, und genau daran hängt die Falle: Er sinkt nicht, weil
weniger gewidmet würde, sondern weil der Nenner mitwächst.

Die Zerlegung für Österreich geht exakt auf (Stand 2025-12-01, in Hektar):

    bebaute Grundstücke        248.580,8 → 253.400,2   +4.819,4
    nicht bebaubare Grundstücke  4.872,4 →   4.831,2      −41,2
    Baulandreserve              65.374,1 →  63.070,0   −2.304,1
    gewidmetes Bauland gesamt  318.827,3 → 321.301,4   +2.474,1

    Probe: 4.819,4 − 41,2 − 2.304,1 = 2.474,1

In drei Jahren kamen 4.819 ha bebaute Fläche dazu. Die Reserve fiel dabei nur
um 2.304 ha, weil gleichzeitig 2.474 ha neu gewidmet wurden. Das ist die
Aussage des Abschnitts, und sie steht als Balkenlänge im Bild — nicht als
Anteil, den man erst gegen einen wandernden Nenner lesen müsste.

DIE BESCHRIFTUNG IST BEWUSST VORSICHTIG: „Zuwachs an bebauter Fläche“ und
„Zuwachs an gewidmetem Bauland (netto)“. NICHT „verbaute Reserve“ — ein
Grundstück kann auch aus neu gewidmetem Land heraus bebaut werden. Die
Zerlegung belegt die Bilanz, nicht den Weg des einzelnen Hektars.

ZWEI EINSCHRÄNKUNGEN, beide aus dem README der Quelle:

1. Sechs Kärntner Gemeinden führen keinen digitalen Flächenwidmungsplan
   (Poggersdorf, Deutsch-Griffen, Heiligenblut am Großglockner, Oberdrauburg,
   Trebesing, Fresach). Sie fehlen in beiden Jahren — das trifft Kärntens
   Werte, nicht den Vergleich.
2. Vier Gemeinden haben erst ab 2025 einen digitalen Plan (Eberstein,
   Glödnitz, Keutschach am See, Sachsenburg); für sie werden die 2025er Daten
   auch für 2022 herangezogen. Ihre Veränderung ist per Konstruktion null.
   Gehört in die Methodik, nicht in die Hinweiszeile.

KEIN openpyxl — dieselbe Begründung wie in `schutzherkunft.py`: Eine .xlsx ist
ein ZIP aus XML, das Blatt trägt nur Text und Zahlen. Der Leser dort ist
erprobt, deshalb wird er hier importiert statt kopiert.
"""

from __future__ import annotations

import requests

import config
from gemeinsam import log, pflegepruefung, quelle_vermerken, warnen
from schutzherkunft import _blatt_zeilen

# Spalte 4 ist Österreich, danach die neun Länder in fester Reihenfolge.
# Die Kopfzeile trägt Trennstriche und harte Umbrüche („Ober-\r\nösterreich“),
# deshalb werden die Namen hier gesetzt und nicht aus dem Blatt gelesen.
LAENDER = [
    "Burgenland", "Kärnten", "Niederösterreich", "Oberösterreich",
    "Salzburg", "Steiermark", "Tirol", "Vorarlberg", "Wien",
]
SPALTE_OESTERREICH = 4


def _hole(url: str) -> bytes | None:
    try:
        antwort = requests.get(url, timeout=config.BLB_TIMEOUT_SEKUNDEN)
        antwort.raise_for_status()
        return antwort.content
    except requests.RequestException as fehler:
        warnen(f"Bauland: Abruf fehlgeschlagen ({fehler}) — Abschnitt bleibt aus")
        return None


def _zahl(text: str) -> float | None:
    try:
        return float(text)
    except (TypeError, ValueError):
        return None


def _block(zeilen: list[list[str]]) -> dict[str, list[float | None]] | None:
    """
    Die vier Mengenzeilen und die Anteilszeile eines Übersichtsblatts.

    Der Block wird über die Hauptkategorie gefunden, nicht über feste
    Zeilennummern: Unter „Monitoring-BAULAND …“ stehen Gesamt, bebaute,
    nicht bebaubare und Reserve in dieser Reihenfolge. Weiter unten
    wiederholen sich dieselben Detailnamen je Widmungskategorie — wer nach
    dem Namen allein sucht, greift den falschen Block.
    """
    start = None
    for i, zeile in enumerate(zeilen):
        kopf = (zeile[0] if zeile else "").strip()
        if kopf.startswith("Monitoring-BAULAND"):
            start = i
            break
    if start is None:
        warnen("Bauland: Block „Monitoring-BAULAND“ nicht gefunden")
        return None

    ERWARTET = ["Gesamt", "bebaute Grundstücke",
                "nicht bebaubare Grundstücke", "Baulandreserve"]
    werte: dict[str, list[float | None]] = {}
    for versatz, name in enumerate(ERWARTET):
        zeile = zeilen[start + versatz] if start + versatz < len(zeilen) else []
        detail = (zeile[2] if len(zeile) > 2 else "").strip()
        if detail != name:
            warnen(f"Bauland: Zeile {start + versatz} heißt {detail!r}, erwartet {name!r}")
            return None
        werte[name] = [_zahl(zeile[s]) if len(zeile) > s else None
                       for s in range(SPALTE_OESTERREICH, SPALTE_OESTERREICH + 10)]

    for zeile in zeilen[start:]:
        detail = (zeile[2] if len(zeile) > 2 else "").strip()
        if detail.startswith("Anteil Baulandreserven"):
            werte["Anteil"] = [_zahl(zeile[s]) if len(zeile) > s else None
                               for s in range(SPALTE_OESTERREICH, SPALTE_OESTERREICH + 10)]
            break
    if "Anteil" not in werte:
        warnen("Bauland: Zeile „Anteil Baulandreserven“ fehlt")
        return None

    return werte


def baue_bauland() -> dict | None:
    log("\n[21/21] Baulandbilanz — bebaut gegen neu gewidmet, je Bundesland")

    roh = _hole(config.BLB_URL)
    if roh is None:
        return None
    log(f"    Datei geholt: {len(roh)} Byte")

    try:
        alt = _block(_blatt_zeilen(roh, config.BLB_BLATT_FRUEH))
        neu = _block(_blatt_zeilen(roh, config.BLB_BLATT_SPAET))
    except (KeyError, ValueError) as fehler:
        warnen(f"Bauland: Blatt nicht lesbar ({fehler}) — Abschnitt bleibt aus")
        return None
    if alt is None or neu is None:
        return None

    def paar(schluessel: str, spalte: int) -> tuple[float, float] | None:
        a, n = alt[schluessel][spalte], neu[schluessel][spalte]
        return None if a is None or n is None else (a, n)

    laender = []
    for i, name in enumerate(LAENDER, start=1):
        gesamt = paar("Gesamt", i)
        bebaut = paar("bebaute Grundstücke", i)
        reserve = paar("Baulandreserve", i)
        anteil = paar("Anteil", i)
        if not (gesamt and bebaut and reserve and anteil):
            warnen(f"Bauland: {name} unvollständig — Abschnitt bleibt aus")
            return None
        laender.append({
            "name": name,
            "bebaut_zuwachs": round(bebaut[1] - bebaut[0], 1),
            "bauland_zuwachs": round(gesamt[1] - gesamt[0], 1),
            "reserve": round(reserve[1], 1),
            "reserve_rueckgang": round(reserve[0] - reserve[1], 1),
            "anteil": round(anteil[1], 1),
            "anteil_frueher": round(anteil[0], 1),
        })

    g = paar("Gesamt", 0)
    b = paar("bebaute Grundstücke", 0)
    r = paar("Baulandreserve", 0)
    nb = paar("nicht bebaubare Grundstücke", 0)
    a = paar("Anteil", 0)
    if not (g and b and r and nb and a):
        warnen("Bauland: Österreich-Spalte unvollständig — Abschnitt bleibt aus")
        return None

    bebaut_zu = b[1] - b[0]
    bauland_zu = g[1] - g[0]
    reserve_ab = r[0] - r[1]
    nichtbebaubar_ab = nb[0] - nb[1]

    # GEGENPROBE 1 — die Zerlegung muss aufgehen. Sie ist eine Identität der
    # Erhebung, kein Sollwert von aussen: Gesamt ist die Summe der drei
    # Teilmengen, also muss die Veränderung des Gesamts gleich der Summe der
    # drei Veränderungen sein. Geht das nicht auf, sind Zeilen verrutscht.
    probe = bebaut_zu - nichtbebaubar_ab - reserve_ab
    if abs(probe - bauland_zu) > 1.0:
        warnen(f"Bauland: Zerlegung geht nicht auf ({probe:.1f} gegen "
               f"{bauland_zu:.1f} ha) — Abschnitt bleibt aus")
        return None
    log(f"    Zerlegung geprüft: {probe:.1f} ha gegen {bauland_zu:.1f} ha")

    # GEGENPROBE 2 — die Summe der neun Länder gegen die Österreich-Spalte.
    summe_bebaut = sum(l["bebaut_zuwachs"] for l in laender)
    summe_bauland = sum(l["bauland_zuwachs"] for l in laender)
    if abs(summe_bebaut - bebaut_zu) > 1.0 or abs(summe_bauland - bauland_zu) > 1.0:
        warnen(f"Bauland: Ländersummen weichen ab ({summe_bebaut:.1f}/"
               f"{summe_bauland:.1f} gegen {bebaut_zu:.1f}/{bauland_zu:.1f} ha)")
        return None
    log(f"    Ländersummen geprüft: {summe_bebaut:.1f} und {summe_bauland:.1f} ha")

    # GEGENPROBE 3 — der Anteil aus der Quelle gegen den selbst gerechneten.
    # Die Quelle liefert ihn fertig; nachzurechnen prüft, ob Reserve und
    # Gesamt aus demselben Blatt und derselben Spalte stammen.
    gerechnet = r[1] / g[1] * 100
    if abs(gerechnet - a[1]) > 0.2:
        warnen(f"Bauland: Anteil stimmt nicht ({gerechnet:.2f} gegen {a[1]:.2f} %)")
        return None

    # Die Reihenfolge der Balken: nach bebautem Zuwachs, absteigend. Nicht
    # alphabetisch — die Rangfolge IST hier eine Aussage.
    laender.sort(key=lambda l: l["bebaut_zuwachs"], reverse=True)

    quelle_vermerken(
        name=("ÖROK-Monitoring Baulandreserven — Berechnung: "
              "Umweltbundesamt im Auftrag der ÖROK"),
        url=config.BLB_QUELLE_SEITE,
        lizenz="CC BY 4.0",
        stand=str(config.BLB_JAHR_SPAET),
        art="api",
    )
    pflegepruefung("bauland", config.BLB_JAHR_SPAET, "ÖROK-Baulandmonitoring")

    return {
        "laender": laender,
        "frueh": config.BLB_JAHR_FRUEH,
        "spaet": config.BLB_JAHR_SPAET,
        "bebaut_zuwachs": round(bebaut_zu, 1),
        "bauland_zuwachs": round(bauland_zu, 1),
        "reserve_rueckgang": round(reserve_ab, 1),
        "reserve": round(r[1], 1),
        "bauland": round(g[1], 1),
        "anteil": round(a[1], 1),
        "anteil_frueher": round(a[0], 1),
        "ersatzquote": round(bauland_zu / bebaut_zu * 100, 1) if bebaut_zu else None,
        "hoechster_anteil": max(laender, key=lambda l: l["anteil"])["name"],
        "niedrigster_anteil": min(laender, key=lambda l: l["anteil"])["name"],
        # 11.09.2026 — Entscheid E1 (a): Der ÖROK-Methodenwechsel 2025
        # qualifiziert die Überschrift und gehört deshalb in die
        # Hinweiszeile. Die sechs Kärntner Gemeinden sind dafür in die Notiz
        # gewandert — beides zusammen sprengt die 234 Zeichen, und die
        # Gemeindelücke qualifiziert die Überschrift nicht.
        # Länge: 218 Zeichen, Soll 150–234.
        "hinweis": (
            "Gewidmetes Bauland ohne Verkehrsflächen und innere "
            "Erschließung. Die ÖROK hat 2025 die Methode präzisiert: Wie "
            "viel der Veränderung gegenüber 2022 daher aus der Definition "
            "stammt und nicht aus dem Verbrauch, ist offen."
        ),
    }
