"""
Schutzstufen — wie viel von dem, was geschützt ist, ist streng geschützt.

Die beiden Abschnitte darüber nennen EINE Zahl: rund 29 % der Landesfläche
stehen unter Schutz. `schutzherkunft` trennt sie nach dem, WER sie ausgewiesen
hat. Dieses Modul trennt sie nach dem, WIE STRENG der Schutz ist — und das
ist der Befund: streng geschützt sind 2,9 %, ein Zehntel des Schutzes.

QUELLE: Umweltbundesamt, Seite „Schutzgebiete", zweite Tabelle „Kumulative
Summe der geschützten Flächen in Österreich (2025)". Stand Jänner 2025,
Quellenangabe des UBA: „Ämter der Landesregierungen, Umweltbundesamt".

WARUM EIN HTML-PARSER UND KEINE ABSCHRIFT: Die Zahlen stehen in einer
HTML-Tabelle, es gibt keine Datei und keine Schnittstelle. Eine Abschrift in
config.py wäre der kürzere Weg — aber sie altert still. Der Parser holt die
Seite und liest die Tabelle; die abgeschriebenen Werte stehen als SOLLWERTE
daneben und melden sich, wenn das UBA die Tabelle fortschreibt. Feste
Sollwerte prüfen die Abschrift, nicht die Aktualität — deshalb beides.

WARUM `html.parser` UND NICHT BeautifulSoup: Standardbibliothek, keine neue
Abhängigkeit, die in der CI mitlaufen müsste. Gebraucht werden vier Zeilen
aus einer Tabelle, kein Selektorbaum.

DER NENNER IST EIGENE RECHNUNG. Die UBA-Seite nennt ausschließlich km²,
keinen einzigen Prozentwert. Jeder Anteil dieses Abschnitts wird hier gegen
83.879 km² gerechnet (Eurostat `demo_r_d3area`, `landuse=TOTAL`, konstant
seit 2008). Das gehört so in die Methodik und steht deshalb auch im
Quellenvermerk.

DER VORBEHALT FÜR DIE HINWEISZEILE: Die 10 % streng geschützter Fläche der
EU-Biodiversitätsstrategie sind ein Ziel für die EU ALS GANZES, nicht für
jeden Mitgliedstaat — dieselbe Lage wie bei den 30 % in `schutzherkunft`.
Deshalb zeichnet dieser Abschnitt KEINE Zielmarke. Und einen Europavergleich
gibt es ohnehin nicht: Das JRC-Dashboard führt zu Target 2 „Indicator under
development".
"""

from __future__ import annotations

import re
from html.parser import HTMLParser

import requests

import config
from gemeinsam import log, pflegepruefung, quelle_vermerken, warnen


class _Tabellenleser(HTMLParser):
    """
    Liest alle <table> einer Seite als Listen von Zeilen, Zeilen als Listen
    von Zellentexten. Verschachtelte Tabellen kommen auf dieser Seite nicht
    vor und werden bewusst nicht behandelt — sie würden hier als eine
    einzige Tabelle erscheinen, und genau das meldet die Gegenprobe.
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tabellen: list[list[list[str]]] = []
        self._tab: list[list[str]] | None = None
        self._zeile: list[str] | None = None
        self._zelle: list[str] | None = None

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self._tab = []
        elif tag == "tr" and self._tab is not None:
            self._zeile = []
        elif tag in ("td", "th") and self._zeile is not None:
            self._zelle = []

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self._zelle is not None:
            self._zeile.append(" ".join("".join(self._zelle).split()))
            self._zelle = None
        elif tag == "tr" and self._zeile is not None:
            self._tab.append(self._zeile)
            self._zeile = None
        elif tag == "table" and self._tab is not None:
            self.tabellen.append(self._tab)
            self._tab = None

    def handle_data(self, daten):
        if self._zelle is not None:
            self._zelle.append(daten)


def _zahl(text: str) -> float | None:
    """
    „12.275,31" → 12275.31. Deutsches Format: Punkt gruppiert, Komma trennt.
    Alles andere (leere Zellen, „x", Fußnotenzeichen) gibt None.
    """
    t = text.replace("\xa0", " ").strip()
    if not re.fullmatch(r"[\d.]+,\d+|[\d.]+", t):
        return None
    return float(t.replace(".", "").replace(",", "."))


def _hole_seite(url: str) -> str | None:
    try:
        antwort = requests.get(
            url,
            timeout=config.SST_TIMEOUT_SEKUNDEN,
            headers={"User-Agent": config.SST_USER_AGENT},
        )
        antwort.raise_for_status()
        antwort.encoding = antwort.apparent_encoding or "utf-8"
        return antwort.text
    except requests.RequestException as fehler:
        warnen(f"Schutzstufen: Abruf fehlgeschlagen ({fehler}) — Abschnitt bleibt aus")
        return None


def _finde_kaskade(tabellen: list[list[list[str]]]) -> list[list[str]] | None:
    """
    Die gesuchte Tabelle daran erkennen, dass irgendeine ihrer Zellen das
    Wort „Kumulative" trägt — nicht an ihrer Position. Die Seite führt zwei
    Tabellen; welche zuerst kommt, ist eine Frage des Redaktionssystems.
    """
    for tab in tabellen:
        for zeile in tab:
            if any("Kumulative" in z for z in zeile):
                return tab
    return None


def baue_schutzstufen() -> dict | None:
    log("\n[21/21] Schutzstufen — wie streng der Schutz ist")

    html = _hole_seite(config.SST_SEITE_URL)
    if html is None:
        return None

    leser = _Tabellenleser()
    leser.feed(html)
    tabelle = _finde_kaskade(leser.tabellen)
    if tabelle is None:
        warnen(
            "Schutzstufen: keine Tabelle mit dem Wort Kumulative auf der Seite — "
            "Aufbau geändert? Abschnitt bleibt aus"
        )
        return None

    # --- Die vier Stufen einlesen ------------------------------------------
    # Je Zeile: erste Zelle ist der Name der Stufe, die LETZTE Zahl der Zeile
    # ist der kumulative Wert. In der ersten Zeile gibt es nur eine Zahl —
    # dort ist Zuwachs gleich Summe, und das ist richtig so.
    gelesen: dict[str, float] = {}
    for zeile in tabelle:
        if not zeile:
            continue
        name = zeile[0].replace("*", "").strip()
        zahlen = [z for z in (_zahl(feld) for feld in zeile[1:]) if z is not None]
        if name and zahlen:
            gelesen[name] = zahlen[-1]

    fehlend = [s for s in config.SST_STUFEN if s not in gelesen]
    if fehlend:
        warnen(
            f"Schutzstufen: Stufen {', '.join(fehlend)} nicht gefunden "
            f"(gelesen: {', '.join(gelesen) or '—'}) — Abschnitt bleibt aus"
        )
        return None

    km2 = [gelesen[s] for s in config.SST_STUFEN]

    # --- Gegenprobe 1: die Reihe muss monoton wachsen ----------------------
    # Eine kumulative Summe kann nicht schrumpfen. Tut sie es, habe ich
    # Zuwachs- und Summenspalte verwechselt.
    if any(b < a for a, b in zip(km2, km2[1:])):
        warnen(
            f"Schutzstufen: kumulative Reihe fällt ({km2}) — "
            "Spaltenzuordnung prüfen. Abschnitt bleibt aus"
        )
        return None

    # --- Gegenprobe 2: gegen die Abschrift vom 07.09.2026 ------------------
    # Kein Abbruch: Wenn das UBA fortschreibt, sollen die neuen Zahlen
    # durchgehen — aber nicht unbemerkt.
    for stufe, ist, soll in zip(config.SST_STUFEN, km2, config.SST_SOLL_KM2):
        if abs(ist - soll) > config.SST_TOLERANZ_KM2:
            warnen(
                f"Schutzstufen: {stufe} steht bei {ist:,.2f} km², abgeschrieben "
                f"waren {soll:,.2f} km² (Stand {config.SST_STAND}). Neue Zahlen? "
                f"Dann Stand und Sollwerte in config.py nachziehen."
            )

    # --- Gegenprobe 3: Anteile im sinnvollen Bereich -----------------------
    if not 0 < km2[-1] < config.SST_FLAECHE_KM2:
        warnen(
            f"Schutzstufen: Gesamtsumme {km2[-1]:,.2f} km² liegt nicht zwischen "
            f"0 und der Staatsfläche — Abschnitt bleibt aus"
        )
        return None

    anteile = [round(w / config.SST_FLAECHE_KM2 * 100, 1) for w in km2]

    # Der Befund in einer Zahl: nicht der Anteil an der Landesfläche, sondern
    # der Anteil am Schutz selbst. Wie viel von dem, was geschützt ist, ist
    # streng geschützt?
    anteil_streng_am_schutz = round(km2[0] / km2[-1] * 100, 1)

    # --- Die Segmente: dieselbe Tabelle, anderer Nenner --------------------
    #
    # UMBAU AM 07.09.2026, einen Tag nach dem Live-Gang. Der User hat die
    # Kaskade zweimal verworfen — erst die Farbe, dann, nach der Korrektur,
    # das Bild als Ganzes: „Ich sehe weiterhin das hier."
    #
    # Er hatte recht, und der Fehler saß tiefer als in den Farbtönen. Die
    # Kaskade zeigte VIER ANTEILE AN DER LANDESFLÄCHE (29,6 / 29,0 / 17,6 /
    # 2,9). Die Überschrift behauptet aber ein VERHÄLTNIS ZWISCHEN ZWEIEN
    # davon: 2,9 zu 29,6, also die 9,9 %. Dieses Verhältnis stand nirgends im
    # Bild — es musste im Kopf gerechnet werden. Solange die Achse an der
    # Landesfläche hängt, gewinnt optisch „viel geschützt", in jeder Farbe.
    #
    # Deshalb hier der Nennerwechsel: nicht mehr die Zuwächse gegen die
    # Staatsfläche, sondern gegen das GESCHÜTZTE GEBIET (km2[-1]). Dann ist
    # das erste Segment sichtbar ein Zehntel des Balkens, und die Überschrift
    # ist ablesbar statt behauptet. Vgl. den festgehaltenen Grundsatz, dass
    # der Nennerwechsel die Aussage trägt.
    #
    # NICHT KUMULATIV, sondern die Zuwächse: Ein gestapelter Balken zeigt
    # Teile eines Ganzen. Kumulierte Werte ergäben 9,9 + 59,3 + 97,9 + 100
    # und damit Unsinn.
    #
    # Der Bezug zur Landesfläche verschwindet nicht, er wandert in die
    # Fußzeile — und der Nachbarabschnitt `schutzgebiete` beantwortet „wie
    # viel ist geschützt" ohnehin schon. Zwei Fragen, zwei Bilder, jeweils
    # der passende Nenner.
    zuwaechse = [km2[0]] + [b - a for a, b in zip(km2, km2[1:])]

    # RUNDUNG NACH GRÖSSTEN RESTEN, nicht kaufmännisch je Wert. Einzeln
    # gerundet ergeben die vier Anteile 9,9 + 49,5 + 38,6 + 2,1 = 100,1 —
    # eine Summe über 100 in einem Bild, das ein Ganzes zeigt. Das Verfahren
    # rundet erst alle ab und verteilt die fehlenden Zehntel an die größten
    # Reste; die Summe ist danach exakt 100,0.
    roh = [w / km2[-1] * 1000 for w in zuwaechse]
    unten = [int(x) for x in roh]
    fehlend = 1000 - sum(unten)
    reste = sorted(range(len(roh)), key=lambda i: roh[i] - unten[i], reverse=True)
    for i in reste[:fehlend]:
        unten[i] += 1
    segment_anteile = [x / 10 for x in unten]

    if abs(sum(segment_anteile) - 100.0) > 0.001:
        warnen(
            f"Schutzstufen: Segmente summieren auf {sum(segment_anteile):.1f} % "
            "statt 100,0 — Rundung prüfen"
        )

    # 11.09.2026 — Entscheid E6: Hier stand, was auf 10 % streng geschützter
    # Staatsfläche fehlt, als Fläche und als Vielfaches. Beides ist eine
    # nationale Fehlmenge gegen eine Marke, die der EU als Ganzes gilt —
    # dieselbe Rechnung, die bei `schutzgebiete` entfallen ist. Die Marke
    # selbst bleibt in der Notiz, die Fehlmenge nicht.

    for stufe, w, a in zip(config.SST_BESCHRIFTUNG, km2, anteile):
        log(f"    {stufe:32s} {w:12,.2f} km²   {a:5.1f} %")
    log(f"    streng am Schutz selbst: {anteil_streng_am_schutz} %")
    log(f"    EU-weite Marke streng: {config.SST_EU_ZIEL_STRENG:.0f} %")

    pflegepruefung("schutzstufen", config.SST_STAND_JAHR, "Schutzstufen")

    quelle_vermerken(
        name="Umweltbundesamt — Schutzgebiete, kumulative Summe der geschützten Flächen",
        url=config.SST_SEITE_URL,
        lizenz="Zitat mit Quellen- und Standangabe",
        stand=config.SST_STAND,
        art="api",
    )

    # Die Balken laufen im Bild von oben (alles) nach unten (streng), die
    # Quelle listet umgekehrt. Gedreht wird hier, nicht im Chart-Modul —
    # dort stünde sonst ein `reverse()` ohne erkennbaren Grund.
    #
    # SEIT DEM UMBAU VOM 07.09.2026 zeichnet das Modul `segmente`, nicht
    # mehr `balken`. Die kumulative Reihe bleibt trotzdem hier: Sie trägt
    # die Tabelle unter der Grafik, die Gegenprobe in `build.py` liest
    # `gesamt_anteil` aus ihr, und die KPI-Kachel hängt an `streng_anteil`.
    balken = [
        {"stufe": b, "km2": round(w, 2), "anteil": a}
        for b, w, a in zip(config.SST_BESCHRIFTUNG, km2, anteile)
    ][::-1]

    # Was das Modul zeichnet: die Zuwächse als Teile des Schutzes. Reihenfolge
    # von STRENG nach schwach — der gestapelte Balken läuft von links, und
    # links steht der Befund. Kein `[::-1]` wie bei `balken`.
    segmente = [
        {"stufe": b, "km2": round(w, 2), "anteil": a}
        for b, w, a in zip(config.SST_BESCHRIFTUNG, zuwaechse, segment_anteile)
    ]

    return {
        "stand": config.SST_STAND,
        "stand_jahr": config.SST_STAND_JAHR,
        "flaeche_km2": config.SST_FLAECHE_KM2,
        "balken": balken,
        "segmente": segmente,
        "streng_anteil": anteile[0],
        "streng_km2": round(km2[0], 2),
        "gesamt_anteil": anteile[-1],
        "gesamt_km2": round(km2[-1], 2),
        "anteil_streng_am_schutz": anteil_streng_am_schutz,
        "eu_ziel_streng": config.SST_EU_ZIEL_STRENG,
        # Die Notiz baut das Chart-Modul aus diesen Zahlen — dort steht der
        # Formatierer, der 2,9 schreibt und nicht 2.9.
        #
        # NEU GEFASST AM 07.09.2026 mit dem Nennerwechsel. Die alte Fassung
        # erklärte die IUCN-Stufen, weil die Achse sie in römischen Ziffern
        # führte. Seit der Umbenennung stehen die Gebietstypen im Bild; hier
        # gehört jetzt der Satz hin, den das Bild NICHT mehr zeigt — dass der
        # ganze Balken nur nicht einmal ein Drittel des Landes ist.
        # Die Prüfung misst Hinweiszeilen gegen 150–234 Zeichen.
        # DEZIMALKOMMA, nicht Punkt: Diese Zeichenkette geht fertig ins
        # Dashboard, der Formatierer des Chart-Moduls sieht sie nicht mehr.
        # Ein `f"{x:.1f}"` schreibt hier „29.6" und fällt erst am
        # ausgelieferten Stand auf.
        "hinweis": (
            # 11.09.2026 — Entscheid E3/E4: Diese 29,6 Prozent sind NICHT
            # die Leitzahl des Dashboards (das ist Eurostat mit 29,3 % für
            # 2023), sondern eine andere Erhebung zu einem späteren
            # Stichtag. Sie bleiben hier stehen, weil Zähler und Nenner der
            # Strengschutz-Rechnung aus derselben Erhebung kommen müssen —
            # aber nur mit Quelle und Stichtag im selben Satz.
            # Länge: 230 Zeichen bei zweistelligen Werten, Soll 150–234.
            # Wird eine der beiden Zahlen dreistellig, reißt das Soll.
            "Der ganze Balken ist die geschützte Fläche Österreichs — "
            f"{anteile[-1]:.1f}".replace(".", ",")
            + " Prozent des Landes, erhoben vom Umweltbundesamt im "
            "Jänner 2025. Die Stufen folgen der Weltnaturschutzunion "
            "(IUCN). Das EU-Ziel von "
            f"{config.SST_EU_ZIEL_STRENG:.0f} Prozent gilt der Union als "
            "Ganzes."
        ),
    }
