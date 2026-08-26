"""
Biber und Fischotter — zwei Arten, die zurückgekommen sind.

GEPFLEGTE REIHE. Die Zahlen sind die offiziellen österreichischen
Meldungen nach Artikel 17 der FFH-Richtlinie, abgelesen im
Berichtswerkzeug der Europäischen Umweltagentur. Ein stabiler
Direktlink auf die Zahlen existiert nicht; das Webtool baut die Tabelle
je Land und Periode zur Laufzeit auf.

  Quelle:    Eionet, Article 17 Web Tool — Austria, Mammals
  URL:       https://nature-art17.eionet.europa.eu/article17/species/report/
             ?period=6&group=Mammals&country=AT&region=
             (period 1 = 2001–2006, 3 = 2007–2012, 5 = 2013–2018,
              6 = 2019–2024)
  Gegenprobe Biber:      BOKU, Institut für Wildbiologie und Jagdwirtschaft
  Gegenprobe Fischotter: Land Niederösterreich, Fischotter-Kartierung 2022/23
  Abgerufen: 26.08.2026

WARUM DIESER ABSCHNITT DER GEGENPOL IST

Die übrigen Abschnitte dieses Dashboards zeigen Rückgang. Dieser zeigt,
dass Rückgang kein Naturgesetz ist: Der Biber war in Österreich
ausgerottet — 1869 erlosch der letzte heimische Bestand. Zwischen 1976
und 1982 wurden an drei Stellen Tiere ausgesetzt, an der Donau bei Wien,
in der Ettenau und in den Salzachauen. Der Fischotter war nie ganz weg,
stand aber in den 1970er- und 1980er-Jahren auf seinem Tiefstand und
besiedelte im Jahr 2000 noch rund ein Fünftel der Bundesfläche.

DREI DINGE, DIE BEIM WEITERPFLEGEN AUFFALLEN WERDEN

1. Die Werte sind Spannen, keine Zählungen. Beide Arten werden über
   Reviere und Nachweise erhoben und auf Individuen hochgerechnet. Genau
   deshalb steht im Diagramm die Spanne und nicht ein Mittelwert: eine
   einzelne Zahl wäre eine Genauigkeit, die die Erhebung nicht hergibt.

2. Beim Fischotter fehlt die Periode 2013–2018. Das ist keine Lücke in
   der Natur, sondern ein Einheitenwechsel: Österreich meldete für diese
   Periode keine Individuen, sondern besetzte Rasterzellen zu einem
   Quadratkilometer (alpin 1.555, kontinental 1.354). Diese Zahlen sind
   mit den Individuenzahlen davor und danach nicht vergleichbar und
   werden deshalb NICHT umgerechnet, sondern ausgelassen. Wer sie
   trotzdem einsetzt, erzeugt einen Einbruch, den es nicht gab.

3. Ein Teil des Zuwachses kann bessere Erfassung sein, nicht mehr Tiere.
   Nachgeprüft am 26.08.2026, und der Befund fiel günstiger aus als
   zunächst notiert: In der Meldung 2019–2024 tragen **beide** Arten in
   der **alpinen** Region den Vermerk `genuine` — die Verbesserung des
   Erhaltungszustands von U1 auf FV ist dort als tatsächliche
   Verbesserung gemeldet, nicht als Ergebnis besseren Wissens.
   Kontinental steht `noChange` (Biber) beziehungsweise
   `noChange`/`unknown` (Fischotter).

   Wichtig für die Formulierung: Der Vermerk hängt an der **Bewertung
   des Erhaltungszustands**, nicht an der einzelnen Bestandszahl. Der
   Sprung von rund 8.900 Bibern im Winter 2020/21 (BOKU) auf 13.833 bis
   16.654 bleibt deshalb vorsichtig zu lesen — belegt ist, dass sich der
   Zustand im Alpenraum wirklich verbessert hat, nicht dass jede Zahl
   eins zu eins mehr Tiere bedeutet.

DIE GEGENBEWEGUNG GEHÖRT DAZU

Erholung ist hier nicht das Ende der Geschichte. Seit 2019 gibt es in
mehreren Bundesländern Verordnungen, die eine Entnahme erlauben: beim
Fischotter Niederösterreich höchstens 50 Tiere im Kalenderjahr, die
Steiermark 40, Oberösterreich seit Mitte 2022 im ersten vollen Jahr 64;
beim Biber regelt Niederösterreich seit 2019 Dammentfernung, Lebendfang
und in bestimmten Fällen die Tötung. Das steht in der Hinweiszeile,
damit der Abschnitt nicht als Entwarnung gelesen wird.
"""

from __future__ import annotations

from gemeinsam import log, pflegepruefung, quelle_vermerken, warnen

STAND_JAHR = 2025          # Erscheinungsjahr der Meldung 2019–2024
PERIODE = "2019–2024"

# Das Jahr, in dem der letzte heimische Biberbestand erlosch. Es steht
# nicht auf der Achse — der Abstand zu 2001 wäre auf einer Kategorie-
# achse gleich breit wie sechs Jahre und damit eine Zeitlüge. Es trägt
# stattdessen die Kachel und den Vorspann.
BIBER_AUSGEROTTET = 1869
BIBER_AUSSETZUNG = "1976–1982"

PERIODEN = ["2001–2006", "2007–2012", "2013–2018", "2019–2024"]

# Aus der Meldung 2019–2024, Spalte „Status Nature of change": In der
# alpinen Region tragen beide Arten `genuine` bei Wechsel U1 → FV. Das
# ist der einzige Satz dieses Abschnitts, der die Erholung nicht nur
# zeigt, sondern belegt — und er gehört deshalb in die Hinweiszeile.
ECHTE_ERHOLUNG = {
    "region": "Alpenraum",
    "arten": ["Biber", "Fischotter"],
    "von": "U1", "auf": "FV",
    "vermerk": "genuine",
}

# Untergrenze und Obergrenze der gemeldeten Individuenzahl, je Periode.
# None heißt: für diese Periode wurde keine Individuenzahl gemeldet.
ARTEN = [
    {
        "name": "Biber",
        "lateinisch": "Castor fiber",
        "spannen": [(2575, 2890), (4650, 4950), (7100, 7800), (13833, 16654)],
        "tiefpunkt": (
            f"{BIBER_AUSGEROTTET} war der Biber in Österreich ausgerottet. "
            f"Zwischen {BIBER_AUSSETZUNG} wurden an drei Stellen wieder "
            f"Tiere ausgesetzt."
        ),
    },
    {
        "name": "Fischotter",
        "lateinisch": "Lutra lutra",
        "spannen": [(430, 800), (950, 1350), (None, None), (3100, 4700)],
        "tiefpunkt": (
            "Der Fischotter war nie ganz verschwunden, erreichte aber in den "
            "1970er- und 1980er-Jahren seinen Tiefstand und lebte im Jahr "
            "2000 noch auf rund einem Fünftel der Bundesfläche."
        ),
    },
]


def baue_rueckkehrer() -> dict:
    log("\n[10/11] Biber und Fischotter — Rückkehrer (gepflegt)")

    arten = []
    for art in ARTEN:
        werte = []
        for periode, (unten, oben) in zip(PERIODEN, art["spannen"]):
            if unten is None or oben is None:
                werte.append({"periode": periode, "unten": None,
                              "oben": None, "spanne": None})
                continue
            if oben < unten:
                warnen(
                    f"{art['name']} {periode}: Obergrenze {oben} liegt unter "
                    f"der Untergrenze {unten} — Zahlen vertauscht?"
                )
            werte.append({"periode": periode, "unten": unten, "oben": oben,
                          "spanne": oben - unten})

        besetzt = [w for w in werte if w["unten"] is not None]
        erste, letzte = besetzt[0], besetzt[-1]
        # Faktor auf der Untergrenze gerechnet, nicht auf der Mitte: das
        # ist die vorsichtigste Lesart des Zuwachses.
        faktor = round(letzte["unten"] / erste["unten"], 1)

        arten.append({
            **{k: v for k, v in art.items() if k != "spannen"},
            "werte": werte,
            "erste_periode": erste["periode"],
            "letzte_periode": letzte["periode"],
            "erste_unten": erste["unten"], "erste_oben": erste["oben"],
            "letzte_unten": letzte["unten"], "letzte_oben": letzte["oben"],
            "faktor": faktor,
            "luecken": [w["periode"] for w in werte if w["unten"] is None],
        })
        log(f"    {art['name']}: {erste['unten']}–{erste['oben']} "
            f"({erste['periode']}) auf {letzte['unten']}–{letzte['oben']} "
            f"({letzte['periode']}) · Faktor {faktor}")

    pflegepruefung("rueckkehrer", STAND_JAHR, "Artikel-17-Meldung Säugetiere")

    quelle_vermerken(
        name="Eionet Artikel-17-Berichtswerkzeug — Österreich, Säugetiere",
        url=("https://nature-art17.eionet.europa.eu/article17/species/report/"
             "?period=6&group=Mammals&country=AT&region="),
        lizenz="Europäische Umweltagentur, Weiterverwendung erlaubt",
        stand=PERIODE,
        art="gepflegt",
    )

    return {
        "arten": arten,
        "perioden": PERIODEN,
        "periode": PERIODE,
        "stand": STAND_JAHR,
        "biber_ausgerottet": BIBER_AUSGEROTTET,
        "biber_aussetzung": BIBER_AUSSETZUNG,
        "echte_erholung": ECHTE_ERHOLUNG,
        "pflege": {
            "art": "gepflegt",
            "quelle": (
                "Eionet, Article 17 Web Tool: Meldungen Österreichs nach "
                "Artikel 17 FFH-Richtlinie, Säugetiere, Berichtsperioden "
                "2001–2006 bis 2019–2024. Gegenproben: BOKU Wildbiologie "
                "(Biber), Land Niederösterreich, Fischotter-Kartierung "
                "2022/23."
            ),
            "bericht_jahr": STAND_JAHR,
            "abgerufen": "2026-08-26",
        },
        "hinweis": (
            # 230 Zeichen, Fenster 150–234. Die Lücke beim Fischotter steht
            # bewusst nicht hier, sondern an der leeren Periode im Diagramm.
            "Die Zahlen sind Hochrechnungen aus Revierkartierungen, keine "
            "Zählungen — deshalb die Spanne. Im Alpenraum meldet Österreich "
            "für beide Arten eine echte Erholung, nicht bloß besseres Wissen. "
            "Seit 2019 ist begrenzte Entnahme erlaubt."
        ),
    }
