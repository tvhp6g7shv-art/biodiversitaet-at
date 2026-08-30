"""
Waldlebensraumtypen: Fläche gegen Bewertung — Artikel 17 FFH, Periode 6.

WARUM DIESER ABSCHNITT: Dieselben Wälder, zwei amtliche Messweisen, zwei
gegenläufige Eindrücke.

    nach Fläche      92,8 % der Fläche in gutem Zustand
    nach Bewertung   28,1 % der Bewertungen günstig

Beide Zahlen stammen aus derselben Meldung Österreichs an die EU. Keine ist
falsch. Sie messen nur nicht dasselbe.

WARUM SIE AUSEINANDERGEHEN — das ist der eigentliche Inhalt des Abschnitts:

Artikel 17 bewertet je Lebensraumtyp vier Parameter (Verbreitungsgebiet,
Fläche, Struktur und Funktion, Zukunftsaussichten). Die Gesamtbewertung folgt
einer Alles-oder-nichts-Regel: **ein einziger ungünstiger Parameter macht den
ganzen Typ ungünstig.** Ein Wald, dessen Fläche zu 99 % in gutem Zustand ist,
zählt als „ungünstig", sobald die Zukunftsaussichten schlecht sind.

Dazu kommt eine zweite Schwelle: Der Parameter Struktur und Funktion gilt nur
dann als günstig, wenn **mehr als 90 %** der Fläche gut sind; sobald mehr als
25 % nicht gut sind, ist er automatisch „ungünstig-schlecht", unabhängig vom
Rest. Die Regel ist so gebaut, dass „ungünstig" der wahrscheinlichere Ausgang
ist — der Bericht sagt das selbst.

DER FEHLER, DEN DIESER ABSCHNITT VERHINDERN SOLL: Die 93 % als „Österreichs
Wäldern geht es gut" zu lesen, oder die 28 % als „Österreichs Wäldern geht es
schlecht". Beides wäre aus derselben Meldung belegbar und beides wäre falsch.

EIGENE AUSZÄHLUNG, nicht abgeschrieben. Zwei Zählregeln, wie in
`erhaltung.py` — dieses Modul ist dessen Wald-Ausschnitt, nicht sein Ersatz:

  1. Gezählt werden BEWERTUNGEN, nicht Schutzgüter. Österreich liegt in zwei
     biogeografischen Regionen; 20 Waldlebensraumtypen ergeben 36 Zeilen.
  2. Zeilen mit `Curr. CS = N/A` gehören heraus — vier Stück (9140 CON,
     91K0 CON, 91M0 ALP, 9530 CON). Bleiben 32 Bewertungen. Bei den
     Waldlebensraumtypen fällt diese Regel mit `% MS = 0` zusammen; bei den
     Artengruppen tut sie das NICHT, siehe unten.

GEGENPROBE, DIE DIE AUSZÄHLUNG TRÄGT: Die Flächensumme der Kategorie `good`
ergibt 92,8 %. Der Waldbiodiversitätsbericht nennt unabhängig davon 93 %.
Zwei Wege, dieselbe Zahl — das belegt, dass die richtigen Spalten summiert
wurden. Weicht das künftig ab, ist die Auszählung zu prüfen, nicht der Text.

WAS NICHT SELBST NACHGERECHNET WERDEN KONNTE: Der Anteil günstig bewerteter
WALDARTEN. Das Eionet-Werkzeug kennt kein Merkmal „waldgebunden"; der Bericht
filtert danach mit der Methode des WWF Österreich (2023). Die eigene
Auszählung über alle Arten der vier genannten Gruppen ergibt 51 von 230
Bewertungen günstig = 22,2 % und stützt die 23 % des Berichts, ersetzt sie
aber nicht. Übernommen wird deshalb die Berichtszahl, mit Quellenangabe.

WIDERSPRUCH IM BERICHT, nicht auflösbar: Die Indikatorenübersicht (Tab. 1)
schreibt „nur 20% der Waldarten erreichen den Zielzustand", das Kapitel
selbst „nur 23 Prozent". Die eigene Auszählung liegt bei 22,2 % und damit
näher an 23. Verwendet wird 23 %, der Widerspruch steht in der Quellennotiz.

Quellen: Reportnet3, Article 17 Web Tool (EEA, 2026) —
https://nature-art17.eionet.europa.eu/article17/habitat/report/
?period=6&group=Forests&country=AT&region=
sowie Waldbiodiversitätsbericht, BFW-Berichte 155/2026, S. 50–53.

Ausgezählt am 28.08.2026.
"""

from __future__ import annotations

from gemeinsam import log, pflegepruefung, quelle_vermerken, warnen

PERIODE = "2019–2024"
STAND_JAHR = 2026

# Reihenfolge ist die Leserichtung des gestapelten Balkens: gut nach schlecht.
# Nicht umsortieren — die Farbzuordnung im Frontend hängt an der Position.
KATEGORIEN = [
    {"kuerzel": "FV", "name": "günstig"},
    {"kuerzel": "U1", "name": "unzureichend"},
    {"kuerzel": "U2", "name": "schlecht"},
    {"kuerzel": "XX", "name": "unbekannt"},
]

# --- Messweise 1: Gesamtbewertung, ausgezählt --------------------------------
# Reihenfolge wie KATEGORIEN.
BEWERTUNGEN = {
    "Österreich": [9, 14, 9, 0],
    "Alpine Region": [7, 8, 5, 0],
    "Kontinentale Region": [2, 6, 4, 0],
}
SCHUTZGUETER = 20          # Waldlebensraumtypen
ZEILEN_GESAMT = 36
OHNE_BEWERTUNG = 4         # Curr. CS = N/A, herausgerechnet

# --- Messweise 2: Struktur und Funktion, flächenbezogen ----------------------
# km², Mittelwerte der vom Werkzeug gemeldeten Spannweiten, über die
# 32 gezählten Zeilen summiert. Die vier ausgeschlossenen Zeilen sind hier
# ohnehin durchgehend N/A.
FLAECHE_KM2 = {
    "gut": 12858.62,
    "nicht gut": 977.78,
    "unbekannt": 22.00,
}

# Was der Bericht unabhängig davon nennt — Gegenprobe der Auszählung.
KONTROLLE_BERICHT_GUT_PROZENT = 92.8
TOLERANZ_PUNKTE = 0.6

# --- Dritte Messweise, nur als Kontext: Parameter Fläche (Area) --------------
# Aus dem Bericht übernommen, nicht selbst ausgezählt. Deshalb getrennt
# gehalten und im Frontend als Berichtszahl zu kennzeichnen.
AREA_GUENSTIG_PROZENT = 76

# --- Waldarten ---------------------------------------------------------------
# Die Waldbindung ist im Eionet-Werkzeug nicht abgebildet. Übernommen aus dem
# Bericht; die eigene ungefilterte Auszählung steht daneben als Stütze.
WALDARTEN = {
    "guenstig_prozent": 23,
    "quelle": "Waldbiodiversitätsbericht S. 53, Methode WWF Österreich (2023)",
    "eigene_gegenprobe": {
        "guenstig": 51,
        "bewertungen": 230,
        "hinweis": "alle Arten der vier Gruppen, ohne Filter auf Waldbindung",
    },
    "widerspruch": (
        "Die Indikatorenübersicht desselben Berichts nennt 20 %, das Kapitel "
        "23 %. Die eigene Auszählung liegt bei 22,2 %."
    ),
}

# --- Kontext: Natura-2000-Gebiete, Tab. 10 des Berichts ----------------------
# „n.a." bleibt leer statt fortgeschrieben zu werden.
GEBIETE = [
    {"jahr": 2010, "anzahl": 202, "flaeche_km2": 12550, "anteil_land": 14.96,
     "waldflaeche_km2": 5275, "anteil_wald": 13.22},
    {"jahr": 2013, "anzahl": 239, "flaeche_km2": 12562, "anteil_land": 14.98,
     "waldflaeche_km2": 5550, "anteil_wald": 13.91},
    {"jahr": 2015, "anzahl": 294, "flaeche_km2": 12691, "anteil_land": 15.13,
     "waldflaeche_km2": 5700, "anteil_wald": 14.28},
    {"jahr": 2019, "anzahl": 352, "flaeche_km2": 12895, "anteil_land": 15.37,
     "waldflaeche_km2": 5852, "anteil_wald": 14.58},
    {"jahr": 2024, "anzahl": 353, "flaeche_km2": 12901, "anteil_land": 15.38,
     "waldflaeche_km2": None, "anteil_wald": None},
]

# Reichweite der Waldlebensraumtypen, Bericht S. 51.
REICHWEITE = {
    "flaeche_mio_ha": 1.4,
    "anteil_waldflaeche": 34.5,
    "davon_in_natura2000_anteil_waldflaeche": 5.4,
}


def _anteile(zahlen: list[float]) -> tuple[list[float], float]:
    nenner = sum(zahlen)
    return [round(z / nenner * 100, 1) for z in zahlen], nenner


def baue_natura2000() -> dict:
    log("\n[16/16] Waldlebensraumtypen — Fläche gegen Bewertung (gepflegt)")

    pflegepruefung("natura2000", STAND_JAHR, f"Artikel 17, Periode {PERIODE}")

    # Selbstkontrolle 1: die Zeilenrechnung muss aufgehen.
    gezaehlt = sum(BEWERTUNGEN["Österreich"])
    if gezaehlt + OHNE_BEWERTUNG != ZEILEN_GESAMT:
        warnen(
            f"Natura 2000: {gezaehlt} gezählte plus {OHNE_BEWERTUNG} "
            f"ausgeschlossene Bewertungen ergeben nicht die {ZEILEN_GESAMT} "
            f"Zeilen des Werkzeugs"
        )

    # Selbstkontrolle 2: die Regionen müssen den Bundeswert ergeben.
    summe_regionen = [
        BEWERTUNGEN["Alpine Region"][i] + BEWERTUNGEN["Kontinentale Region"][i]
        for i in range(len(KATEGORIEN))
    ]
    if summe_regionen != BEWERTUNGEN["Österreich"]:
        warnen(
            f"Natura 2000: Regionen summieren auf {summe_regionen}, "
            f"Bundeswert ist {BEWERTUNGEN['Österreich']}"
        )

    flaechen_anteile, flaeche_gesamt = _anteile(list(FLAECHE_KM2.values()))
    gut_prozent = flaechen_anteile[0]

    # Die Gegenprobe, die die ganze Auszählung trägt: zwei unabhängige Wege
    # zur selben Zahl. Der Bericht nennt 93 %, gerundet aus seiner eigenen
    # Rechnung; die eigene Summe ergibt 92,8 %.
    if abs(gut_prozent - KONTROLLE_BERICHT_GUT_PROZENT) > TOLERANZ_PUNKTE:
        warnen(
            f"Natura 2000: eigene Flächensumme ergibt {gut_prozent} % gut, "
            f"der Bericht nennt {KONTROLLE_BERICHT_GUT_PROZENT} % — es wurden "
            f"vermutlich die falschen Spalten summiert"
        )
    else:
        log(f"    Flächensumme deckt sich mit dem Bericht "
            f"({gut_prozent} % gegen {KONTROLLE_BERICHT_GUT_PROZENT} %)")

    bewertungs_anteile, _ = _anteile([float(z) for z in BEWERTUNGEN["Österreich"]])
    guenstig_prozent = bewertungs_anteile[0]

    regionen = []
    for name in ("Alpine Region", "Kontinentale Region"):
        anteile, nenner = _anteile([float(z) for z in BEWERTUNGEN[name]])
        regionen.append({
            "name": name,
            "zahlen": BEWERTUNGEN[name],
            "anteile": anteile,
            "bewertungen": int(nenner),
            "guenstig": anteile[0],
        })

    daten = {
        "stand": f"Artikel 17, Periode {PERIODE}",
        "periode": PERIODE,
        "abgerufen": "2026-08-28",
        "kategorien": KATEGORIEN,
        # Die zwei Messweisen, die den Abschnitt tragen.
        "nach_flaeche": {
            "kategorien": list(FLAECHE_KM2.keys()),
            "km2": list(FLAECHE_KM2.values()),
            "anteile": flaechen_anteile,
            "gesamt_km2": round(flaeche_gesamt, 2),
            "gut_prozent": gut_prozent,
        },
        "nach_bewertung": {
            "zahlen": BEWERTUNGEN["Österreich"],
            "anteile": bewertungs_anteile,
            "bewertungen": gezaehlt,
            "schutzgueter": SCHUTZGUETER,
            "ohne_bewertung": OHNE_BEWERTUNG,
            "guenstig_prozent": guenstig_prozent,
        },
        "abstand_punkte": round(gut_prozent - guenstig_prozent, 1),
        # Beide Messweisen auf DIESELBEN drei Fächer gebracht, damit sie
        # in einer Grafik nebeneinander stehen können. Ohne das trüge jede
        # Zeile ihre eigene Legende, und der Vergleich wäre keiner.
        #
        # „unzureichend" und „schlecht" werden dabei zu „ungünstig"
        # zusammengefasst. Das ist keine Vereinfachung von mir, sondern
        # genau die Zusammenfassung, die die FFH-Richtlinie selbst
        # vornimmt: U1 und U2 sind beide „unfavourable". Die
        # Vierteilung bleibt in der Tabelle erhalten.
        "vergleich": {
            "faecher": ["gut", "nicht gut", "unbekannt"],
            "zeilen": [
                {
                    "name": "Nach Fläche gemessen",
                    "werte": flaechen_anteile,
                    "grundlage": f"{round(flaeche_gesamt):,} km² Waldlebensraum"
                                 .replace(",", "."),
                },
                {
                    "name": "Nach Gesamtbewertung",
                    "werte": [
                        bewertungs_anteile[0],
                        round(bewertungs_anteile[1] + bewertungs_anteile[2], 1),
                        bewertungs_anteile[3],
                    ],
                    "grundlage": f"{gezaehlt} Bewertungen über "
                                 f"{SCHUTZGUETER} Lebensraumtypen",
                },
            ],
        },
        "regionen": regionen,
        "area_guenstig_prozent": AREA_GUENSTIG_PROZENT,
        "waldarten": WALDARTEN,
        "gebiete": GEBIETE,
        "reichweite": REICHWEITE,
        # Einordnung unter der Grafik, Konvention 150–234 Zeichen. Gemessen: 223.
        # Die Spanne ist hier fast ausgereizt — beim Umformulieren nachmessen.
        "hinweis": (
            "Beide Werte stammen aus derselben Meldung an die EU. Für die "
            "Gesamtbewertung genügt ein schlechter Teilwert von vier, damit ein "
            "Wald als ungünstig gilt: Die Fläche misst den Zustand, die "
            "Bewertung fasst ihn streng zusammen."
        ),
    }

    quelle_vermerken(
        "Waldlebensraumtypen nach Artikel 17",
        "https://nature-art17.eionet.europa.eu/article17/habitat/report/"
        "?period=6&group=Forests&country=AT&region=",
        "Reportnet3, Article 17 Web Tool (EEA, 2026); Einordnung "
        "Waldbiodiversitätsbericht, BFW-Berichte 155/2026",
        f"Periode {PERIODE}",
        "gepflegt",
    )

    log(f"  nach Fläche {gut_prozent} % gut · nach Bewertung "
        f"{guenstig_prozent} % günstig · Abstand "
        f"{daten['abstand_punkte']} Punkte · {gezaehlt} Bewertungen über "
        f"{SCHUTZGUETER} Lebensraumtypen")

    return daten
