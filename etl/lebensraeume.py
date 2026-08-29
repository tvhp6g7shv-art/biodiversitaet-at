"""
Erhaltungszustand nach Lebensraumgruppen — Artikel 17 FFH, Periode 6.

GEPFLEGTE REIHE, eigene Auszählung aus dem Eionet-Berichtswerkzeug.

  Quelle:    Eionet, Article 17 Web Tool — Österreich, Berichtsperiode 6
             (2019–2024), alle neun Lebensraumgruppen einzeln abgerufen.
  URL:       https://nature-art17.eionet.europa.eu/article17/habitat/report/
             ?period=6&group=<GRUPPE>&country=AT&region=
  Abgerufen: 29.08.2026

WARUM DIESER ABSCHNITT NEBEN ZWEI BESTEHENDEN STEHT

Drei Abschnitte ziehen aus derselben Meldung, und keiner ersetzt den
anderen:

    erhaltung.py    Lebensraumtypen GESAMT gegen Arten gesamt
    natura2000.py   nur der Wald, dort Fläche gegen Bewertung
    dieses Modul    die Lebensraumtypen aufgeschlüsselt nach Gruppen

`erhaltung` sagt, dass 22,8 % der Bewertungen günstig sind. Diese Zahl
gibt es in der Wirklichkeit nirgends: Sie ist der Mittelwert über
Lebensräume, denen es sehr unterschiedlich geht. Fels und Höhlen liegen
bei 75 % günstig, Moore und Grünland bei 0 bzw. 8 %. Der Durchschnitt
verdeckt genau das Gefälle, das die Aussage trägt.

DIE REIHENFOLGE IST DIE AUSSAGE

Sortiert wird nach dem Anteil „günstig", absteigend — und heraus kommt
eine Rangfolge nach Nutzungsintensität. Oben steht, was niemand
bewirtschaftet (Fels, Höhlen, Gletscher, alpine Zwergstrauchheiden),
unten die Wiesen, Weiden und Moore der Kulturlandschaft. Das ist kein
Zufallsbefund und keine Deutung von außen: Es ist die Sortierung der
Zahlen selbst.

DIE ZWEI GÜNSTIGEN GRÜNLANDBEWERTUNGEN LIEGEN BEIDE IM HOCHGEBIRGE

6150 (Silikat-Alpinrasen, alpin) und 6430 (feuchte Hochstaudenfluren,
alpin). Von den bewirtschafteten Wiesentypen — 6210 Trockenrasen, 6410
Pfeifengraswiesen, 6510 Flachland-Mähwiesen, 6520 Bergmähwiesen — ist in
BEIDEN Naturräumen keine einzige Bewertung günstig; alle acht stehen auf
„schlecht". Ohne diesen Satz liest sich „8 % günstig" so, als gäbe es im
bewirtschafteten Grünland wenigstens einen guten Fall. Es gibt keinen.

DREI FALLEN BEIM NACHZÄHLEN — dieselben wie in erhaltung.py

1. Gezählt werden BEWERTUNGEN, nicht Lebensraumtypen. Eine Zeile ist
   Typ × Region; Österreich hat zwei (alpin und kontinental). 71 Typen
   ergeben 114 Bewertungen in 127 Tabellenzeilen.
2. Zeilen mit `Curr. CS = N/A` und `% MS = 0` führt das Werkzeug kursiv
   und kennzeichnet sie selbst als „not taken into account" — 13 Stück.
   Sie gehören aus dem Nenner.
3. Die Spalte unmittelbar VOR „Curr. CS" ist der Zukunftsaussichten-
   Status, nicht dessen Kopie.

WAS DIE GEGENPROBEN UNTEN TRAGEN

Die neun Gruppen sind einzeln ausgezählt worden, ohne Blick auf das
Gesamtergebnis. Ihre Summen müssen die Zahlen von `erhaltung.py`
ergeben: 114 Bewertungen, 26/33/45/10 nach Klassen, 13 ausgeschlossene
Zeilen, 71 Schutzgüter. Sie tun es exakt. Das ist der Beleg, dass die
Aufschlüsselung dieselbe Meldung meint und nicht eine zweite Lesart —
und er ist mehr wert als jede feste Sollzahl im Modul, weil beide Seiten
unabhängig voneinander entstanden sind.

Zusätzlich muss der Waldwert mit `natura2000.py` übereinstimmen; die
Prüfung dazu steht in build.py, weil sie zwei Module braucht.
"""

from __future__ import annotations

from gemeinsam import log, pflegepruefung, quelle_vermerken, warnen

STAND_JAHR = 2026
PERIODE = "2019–2024"

# Reihenfolge ist die Leserichtung des gestapelten Balkens: von gut nach
# schlecht, „unbekannt" ganz hinten. Nicht umsortieren — die Farbzuordnung
# im Frontend hängt an der Position.
KATEGORIEN = [
    {"kuerzel": "FV", "name": "günstig"},
    {"kuerzel": "U1", "name": "unzureichend"},
    {"kuerzel": "U2", "name": "schlecht"},
    {"kuerzel": "XX", "name": "unbekannt"},
]

# Anzahl der Bewertungen je Klasse, ausgezählt — Reihenfolge wie KATEGORIEN.
#
# `name` ist die Kurzform für die Achsenbeschriftung, `name_lang` die
# ausführliche für Tooltip und Tabelle, `gruppe` der Filterwert des
# Werkzeugs. Wer nachzählen will, hängt `gruppe` an die URL im Kopf
# dieser Datei; die Schreibweise muss exakt stimmen, sonst kommt nur das
# leere Filterformular zurück.
#
# WARUM ZWEI NAMEN: Der Achsenrand gehört dem längsten Namen. „Moore,
# Sümpfe & Quellen" bräuchte rund 200 px links — die nimmt der Balken
# der Zeichenfläche weg, und auf dem Handy bleibt nichts übrig. Die
# Kurzformen kommen mit 140 px aus. Die Genauigkeit geht dabei nicht
# verloren, sie wandert nur eine Ebene tiefer: in Tooltip und Tabelle.
#
# `zeigen: False` heißt: fließt in alle Gegenproben ein, steht aber nicht
# im Balken. Bei ein bis zwei Bewertungen ist ein Prozentbalken keine
# Information, sondern eine Behauptung — 100 % bei n = 1.
GRUPPEN = [
    {
        "name": "Fels & Höhlen",
        "name_lang": "Fels, Schutt, Höhlen & Gletscher",
        "gruppe": "Rocky habitats",
        "jetzt": [12, 1, 2, 1], "vorher": [12, 2, 2, 0],
        "ausgeschlossen": 0, "schutzgueter": 10, "genuine": 0,
        "zeigen": True,
    },
    {
        "name": "Heide & Gebüsch",
        "name_lang": "Heiden & Gebüsche",
        "gruppe": "Heath & scrub",
        "jetzt": [3, 1, 0, 2], "vorher": [3, 1, 2, 0],
        "ausgeschlossen": 3, "schutzgueter": 5, "genuine": 0,
        "zeigen": True,
    },
    {
        "name": "Wald",
        "name_lang": "Waldlebensräume",
        "gruppe": "Forests",
        "jetzt": [9, 14, 9, 0], "vorher": [4, 15, 12, 1],
        "ausgeschlossen": 4, "schutzgueter": 20, "genuine": 4,
        "zeigen": True,
    },
    {
        "name": "Grünland",
        "name_lang": "Grünland & Hochstaudenfluren",
        "gruppe": "Grasslands",
        "jetzt": [2, 9, 13, 0], "vorher": [2, 9, 12, 1],
        "ausgeschlossen": 4, "schutzgueter": 15, "genuine": 0,
        "zeigen": True,
    },
    {
        "name": "Gewässer",
        "name_lang": "Fließ- & Stillgewässer",
        "gruppe": "Freshwater habitats",
        "jetzt": [0, 3, 6, 7], "vorher": [0, 7, 7, 2],
        "ausgeschlossen": 1, "schutzgueter": 9, "genuine": 1,
        "zeigen": True,
    },
    {
        "name": "Moore & Sümpfe",
        "name_lang": "Moore, Sümpfe & Quellen",
        "gruppe": "Bogs, mires & fens",
        "jetzt": [0, 5, 11, 0], "vorher": [0, 5, 11, 0],
        "ausgeschlossen": 1, "schutzgueter": 9, "genuine": 0,
        "zeigen": True,
    },
    # --- ab hier nicht im Balken, nur in den Gegenproben ------------------
    {
        "name": "Salzsteppen",
        "name_lang": "Pannonische Salzsteppen",
        "gruppe": "Coastal habitats",
        "jetzt": [0, 0, 1, 0], "vorher": [0, 0, 1, 0],
        "ausgeschlossen": 0, "schutzgueter": 1, "genuine": 0,
        "zeigen": False,
    },
    {
        "name": "Binnendünen",
        "name_lang": "Pannonische Binnendünen",
        "gruppe": "Dunes habitats",
        "jetzt": [0, 0, 1, 0], "vorher": [0, 0, 1, 0],
        "ausgeschlossen": 0, "schutzgueter": 1, "genuine": 0,
        "zeigen": False,
    },
    {
        "name": "Wacholderheiden",
        "name_lang": "Wacholderheiden",
        "gruppe": "Sclerophyllous scrubs",
        "jetzt": [0, 0, 2, 0], "vorher": [0, 0, 2, 0],
        "ausgeschlossen": 0, "schutzgueter": 1, "genuine": 0,
        "zeigen": False,   # zwei Bewertungen — für einen Balken zu wenig
    },
]

# Die Zahlen, die `erhaltung.py` unabhängig davon für die Gesamtheit der
# Lebensraumtypen führt. Sie sind KEIN Sollwert aus einer Publikation,
# sondern das Ergebnis einer zweiten, getrennten Auszählung derselben
# Quelle — deshalb taugen sie als Gegenprobe (vgl. den Hinweis in
# vogelarten.py, wo ein Sollwert aus derselben Ausgabe wie die Daten den
# Fehler nicht finden konnte).
SOLL_GESAMT = {
    "jetzt": [26, 33, 45, 10],
    "vorher": [21, 39, 50, 4],
    "bewertungen": 114,
    "zeilen": 127,
    "schutzgueter": 71,
    "genuine": 5,
}

# Grünlandtypen der bewirtschafteten Kulturlandschaft, für die Notiz.
# Alle acht Bewertungen (vier Typen × zwei Naturräume) stehen auf U2.
WIESENTYPEN = ["6210", "6410", "6510", "6520"]
WIESEN_BEWERTUNGEN = 8


# Zahlwörter für die Notiz. Die Zählwerte dort sind einstellig, und
# „keine einzige der 8 Bewertungen“ liest sich falsch. Über zwölf hinaus
# bleibt die Ziffer stehen — dann ist sie auch im Fließtext richtig.
_WORTE = ["null", "eine", "zwei", "drei", "vier", "fünf", "sechs", "sieben",
          "acht", "neun", "zehn", "elf", "zwölf"]


def _wort(n: int) -> str:
    return _WORTE[n] if 0 <= n < len(_WORTE) else str(n)


def _anteile(zahlen: list[int]) -> tuple[list[float], int]:
    """Anteile in Prozent, eine Nachkommastelle, plus Nenner."""
    nenner = sum(zahlen)
    if not nenner:
        return [0.0, 0.0, 0.0, 0.0], 0
    return [round(z / nenner * 100, 1) for z in zahlen], nenner


def _summen_pruefen() -> None:
    """
    Hält die neun einzeln ausgezählten Gruppen gegen die Gesamtauszählung.

    Fünf Summen müssen stimmen. Jede von ihnen kann für sich durchfallen,
    und jede zeigt auf einen anderen Fehler: eine falsche Klasse, eine
    vergessene Zeile, eine doppelt gezählte Region.
    """
    for feld in ("jetzt", "vorher"):
        summe = [sum(g[feld][k] for g in GRUPPEN) for k in range(4)]
        if summe != SOLL_GESAMT[feld]:
            warnen(
                f"Lebensraumgruppen: Die Klassensummen ({feld}) ergeben "
                f"{summe}, die Gesamtauszählung in erhaltung.py nennt "
                f"{SOLL_GESAMT[feld]}. Eine der beiden Zählungen ist falsch."
            )

    bewertungen = sum(sum(g["jetzt"]) for g in GRUPPEN)
    if bewertungen != SOLL_GESAMT["bewertungen"]:
        warnen(
            f"Lebensraumgruppen: {bewertungen} Bewertungen statt "
            f"{SOLL_GESAMT['bewertungen']}."
        )

    zeilen = bewertungen + sum(g["ausgeschlossen"] for g in GRUPPEN)
    if zeilen != SOLL_GESAMT["zeilen"]:
        warnen(
            f"Lebensraumgruppen: {zeilen} Tabellenzeilen statt "
            f"{SOLL_GESAMT['zeilen']} — die Zahl der kursiven Zeilen "
            f"(„not taken into account\") weicht ab."
        )

    schutzgueter = sum(g["schutzgueter"] for g in GRUPPEN)
    if schutzgueter != SOLL_GESAMT["schutzgueter"]:
        warnen(
            f"Lebensraumgruppen: {schutzgueter} Lebensraumtypen statt "
            f"{SOLL_GESAMT['schutzgueter']}."
        )

    genuine = sum(g["genuine"] for g in GRUPPEN)
    if genuine != SOLL_GESAMT["genuine"]:
        warnen(
            f"Lebensraumgruppen: {genuine} als „genuine\" gemeldete "
            f"Änderungen statt {SOLL_GESAMT['genuine']}."
        )


def baue_lebensraeume() -> dict:
    log("\n[17/17] Erhaltungszustand nach Lebensraumgruppen (gepflegt)")

    _summen_pruefen()

    alle = []
    for gruppe in GRUPPEN:
        anteile, bewertungen = _anteile(gruppe["jetzt"])
        alle.append({
            "name": gruppe["name"],
            "name_lang": gruppe["name_lang"],
            "gruppe_quelle": gruppe["gruppe"],
            "anteile": anteile,
            "anzahl": gruppe["jetzt"],
            "bewertungen": bewertungen,
            "schutzgueter": gruppe["schutzgueter"],
            "genuine": gruppe["genuine"],
            "guenstig": anteile[0],
            "schlecht": anteile[2],
            "unbekannt": anteile[3],
            "zeigen": gruppe["zeigen"],
        })

    # Sortiert nach „günstig" absteigend. Bei Gleichstand entscheidet der
    # kleinere Anteil „schlecht" — sonst stünde bei zwei Gruppen mit 0 %
    # günstig die schlechtere zufällig oben, je nach Eingabereihenfolge.
    gezeigt = sorted(
        (g for g in alle if g["zeigen"]),
        key=lambda g: (-g["guenstig"], g["schlecht"]),
    )
    verborgen = [g for g in alle if not g["zeigen"]]

    for g in gezeigt:
        log(f"    {g['name']}: {g['guenstig']} % günstig, "
            f"{g['schlecht']} % schlecht "
            f"({g['bewertungen']} Bewertungen, {g['schutzgueter']} Typen)")

    rest_bewertungen = sum(g["bewertungen"] for g in verborgen)
    rest_typen = sum(g["schutzgueter"] for g in verborgen)
    log(f"    nicht im Balken: {rest_bewertungen} Bewertungen aus "
        f"{rest_typen} Typen ({', '.join(g['name'] for g in verborgen)})")

    bester, schlechtester = gezeigt[0], gezeigt[-1]
    wald = next(g for g in gezeigt if g["gruppe_quelle"] == "Forests")
    gruenland = next(g for g in gezeigt if g["gruppe_quelle"] == "Grasslands")
    gewaesser = next(g for g in gezeigt
                     if g["gruppe_quelle"] == "Freshwater habitats")
    genuine_gesamt = sum(g["genuine"] for g in alle)

    pflegepruefung("lebensraeume", STAND_JAHR, "Artikel-17-Bericht")

    quelle_vermerken(
        name=("Eionet Artikel-17-Berichtswerkzeug — Österreich, "
              "Lebensraumtypen nach Gruppen"),
        url=("https://nature-art17.eionet.europa.eu/article17/habitat/report/"
             "?period=6&group=Forests&country=AT&region="),
        lizenz="Europäische Umweltagentur, Weiterverwendung erlaubt",
        stand=PERIODE,
        art="gepflegt",
    )

    return {
        "gruppen": gezeigt,
        "nicht_gezeigt": verborgen,
        "kategorien": KATEGORIEN,
        "periode": PERIODE,
        "stand": STAND_JAHR,
        "bewertungen_gesamt": sum(g["bewertungen"] for g in alle),
        "schutzgueter_gesamt": sum(g["schutzgueter"] for g in alle),
        "wald_guenstig": wald["guenstig"],
        "gruenland_guenstig": gruenland["guenstig"],
        "pflege": {
            "art": "gepflegt",
            "quelle": (
                "Eionet, Article 17 Web Tool: Meldung Österreichs nach "
                "Artikel 17 FFH-Richtlinie, Berichtsperiode 2019–2024, alle "
                "neun Lebensraumgruppen einzeln ausgezählt am 29.08.2026. "
                "Die Gruppensummen sind gegen die unabhängige "
                "Gesamtauszählung im Abschnitt Erhaltungszustand geprüft."
            ),
            "bericht_jahr": STAND_JAHR,
            "abgerufen": "2026-08-29",
        },
        "notiz": (
            f"Die Reihenfolge folgt der Nutzung: Oben steht, was niemand "
            f"bewirtschaftet — Fels, Gletscher und Höhlen, "
            f"{bester['guenstig']:.0f} % davon in gutem Zustand. Unten die "
            f"Kulturlandschaft. Von den vier bewirtschafteten Wiesentypen "
            f"ist in <strong>beiden</strong> Naturräumen keine einzige der "
            f"{_wort(WIESEN_BEWERTUNGEN)} Bewertungen günstig; die zwei "
            f"guten Grünlandwerte liegen im Hochgebirge. Bei den Gewässern "
            f"sind {gewaesser['unbekannt']:.0f} % „unbekannt“ — das ist "
            f"eine Lücke im Wissen, keine gute Lage. Und von den "
            f"{_wort(genuine_gesamt)} Änderungen, die der Bericht als "
            f"<strong>tatsächlich</strong> meldet und nicht als Folge "
            f"besseren Wissens, entfallen {_wort(wald['genuine'])} auf den "
            f"Wald und keine einzige auf das Grünland."
        ),
        # 29.08.2026 — der erste Satz erklärte dasselbe wie der erste Satz
        # im Abschnitt „erhaltung" direkt darüber, und die Unterzeile hier
        # trägt die Unterscheidung ohnehin als Zahl („114 Bewertungen aus
        # 71 Lebensraumtypen"). Die Erklärung steht jetzt einmal, oben;
        # hier bleibt der Verweis und das, was nur hier gilt.
        "hinweis": (
            "Salzsteppen, Binnendünen und Wacholderheiden fehlen im Balken — "
            f"zusammen {_wort(rest_bewertungen)} Bewertungen. Gezählt wird "
            "wie im Abschnitt darüber: jede Bewertung einzeln, nicht jeder "
            "Lebensraumtyp."
        ),
    }
