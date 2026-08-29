"""
Feld- und Wiesenvögel, Art für Art — wer verliert, wer hält, wer gewinnt.

GEPFLEGTE REIHE. Die Werte stehen in Tabelle 3 des Jahresberichts und
sind hier abgeschrieben, nicht abgerufen: BirdLife veröffentlicht die
Artentrends als PDF ohne Datenanhang.

  Quelle:    Teufelbauer, N. & Seaman, B. (2026): Monitoring der Brutvögel
             Österreichs — Bericht über die Saison 2025. BirdLife
             Österreich, Wien, Juli 2026, Tab. 3, S. 11–13;
             Streckenzahlen Tab. 1, S. 5–6.
  PDF:       https://assets.ctfassets.net/2oszne1tuxgg/4nfQvAgWo1jvQMzcWbp8Lp/
             f015b57c1d72385bf71dab93f399321e/BVM_Bericht_2025__3_.pdf
  Gegenprobe: Presseaussendung BirdLife Österreich, 10.08.2026 — nennt
             dieselbe Verteilung 14 / 4 / 2 und dieselben Artennamen je Gruppe.
  Abgerufen: 26.08.2026

WARUM DIE QUELLE GEWECHSELT HAT

Bis 26.08.2026 stand hier Tab. 4 des FBI-Berichts „Indikator 2023"
(Juni 2024). Der war beim Bau des Moduls bereits **zwei Berichte alt**:
Indikator 2024 erschien am 31.07.2025, Indikator 2025 am **10.08.2026**
— sechzehn Tage vorher. Der Bericht 2025 selbst liegt nur in der
Pressemappe (ZIP, 48 MB); die Artentrends bis 2025 stehen aber offen im
Brutvogel-Monitoring-Bericht derselben Autoren, und der ist die Quelle,
aus der der FBI ohnehin gerechnet wird.

**Rhythmus, damit das nicht wieder passiert:** BirdLife veröffentlicht
Ende Juli / Anfang August. Vor jedem Anfassen dieses Moduls
`birdlife.at/vogelschutz/forschung-und-monitoring/monitoring-der-
brutvoegel-oesterreichs/` nachsehen — dort hängen beide Berichtsreihen
als Direkt-PDF.

WAS DIESER ABSCHNITT NEBEN vogel.py TUT

vogel.py zeigt den Index — eine Linie, das Mittel aus allen Arten. Diese
Linie sagt, wie groß der Rückgang insgesamt ist. Sie sagt nicht, dass er
sehr ungleich verteilt ist: Die Grauammer hat 97 Prozent ihres Bestands
verloren, der Stieglitz hat seinen mehr als verdoppelt. Ein Mittelwert
verdeckt genau das. Deshalb hier dieselben Vögel einzeln.

DREI DINGE, DIE BEIM WEITERPFLEGEN AUFFALLEN WERDEN

1. Es sind 24 Indikatorarten definiert, aber nur 23 werden ausgewertet.
   Der Zitronenzeisig fehlt dauerhaft wegen zu kleiner Stichprobe.

2. Von den 23 haben nur 20 eine Reihe ab 1998. Heidelerche,
   Steinschmätzer und Bergpieper werden erst ab 2008 gerechnet. Ihre
   Werte stehen hier mit `beginn: 2008` und gehören NICHT in denselben
   Balken wie die übrigen — siebzehn Jahre neben siebenundzwanzig zu
   stellen wäre ein stiller Vergleich zweier verschiedener Dinge.
   Nebenbei: zwei der drei sind mit dem Stand 2025 **nicht mehr
   „Zunahme", sondern stabil** — wer sie als Aufsteiger einführt, hätte
   den Nachsatz aus dem alten Bericht abgeschrieben.

3. Die Prozentzahl allein trägt nicht. Die Stichprobe steht daneben,
   weil sie extrem schwankt: Der Stieglitz wird auf 210 Zählstrecken
   erfasst, die Grauammer auf **sechs — mit zehn gezählten Individuen im
   ganzen Jahr**. Beide Trends sind statistisch gesichert, aber der eine
   ruht auf deutlich mehr Boden als der andere.

ZUR EINSTUFUNG

Der Bericht unterscheidet sechs Stufen. Hier werden vier gebraucht:

  abnahme_stark  ↓↓  gesichert, mehr als 5 Prozent Verlust im Jahr
  abnahme        ↓   gesichert, bis 5 Prozent im Jahr
  stabil         –   nicht gesichert und unter 5 Prozent im Jahr
  zunahme        ↑   gesichert, Zunahme

„Stabil" heißt also nicht „gemessen unverändert", sondern „die Messung
zeigt keine gesicherte Richtung". Das steht so in der Hinweiszeile.
"""

from __future__ import annotations

from gemeinsam import log, pflegepruefung, quelle_vermerken, warnen

STAND_JAHR = 2025          # letztes Jahr der Trendrechnung
BERICHT_JAHR = 2026        # Erscheinungsjahr des Berichts
BEGINN = 1998
BEGINN_SPAET = 2008

# (Name, Gesamtveränderung %, pro Jahr %, Einstufung, Zählstrecken 2025,
#  Beginn). Aufsteigend sortiert: von der stärksten Abnahme zur stärksten
#  Zunahme. Nicht umsortieren — das Frontend verlässt sich darauf, dass
#  die Liste bereits geordnet ist; `baue_vogelarten()` prüft es nach.
ARTEN = [
    ("Grauammer",       -97, -12, "abnahme_stark",   6, BEGINN),
    ("Girlitz",         -90,  -8, "abnahme_stark",  49, BEGINN),
    ("Turteltaube",     -75,  -5, "abnahme",        45, BEGINN),
    ("Schwarzkehlchen", -72,  -5, "abnahme",        30, BEGINN),
    ("Braunkehlchen",   -70,  -4, "abnahme",        14, BEGINN),
    ("Rebhuhn",         -69,  -4, "abnahme",        18, BEGINN),
    ("Baumpieper",      -59,  -3, "abnahme",        69, BEGINN),
    ("Kiebitz",         -58,  -3, "abnahme",        36, BEGINN),
    ("Sumpfrohrsänger", -58,  -3, "abnahme",        60, BEGINN),
    ("Wacholderdrossel", -54, -3, "abnahme",        44, BEGINN),
    ("Feldlerche",      -53,  -3, "abnahme",        85, BEGINN),
    ("Goldammer",       -47,  -2, "abnahme",       146, BEGINN),
    ("Bluthänfling",    -41,  -2, "abnahme",        48, BEGINN),
    ("Dorngrasmücke",   -31,  -1, "abnahme",        52, BEGINN),
    ("Neuntöter",       -10,   0, "stabil",         92, BEGINN),
    ("Feldsperling",     -3,   0, "stabil",        123, BEGINN),
    ("Star",              3,   0, "stabil",        168, BEGINN),
    ("Wendehals",         7,   0, "stabil",         33, BEGINN),
    ("Turmfalke",        33,   1, "zunahme",       176, BEGINN),
    ("Stieglitz",       122,   3, "zunahme",       210, BEGINN),
    ("Bergpieper",        8,   0, "stabil",         37, BEGINN_SPAET),
    ("Steinschmätzer",   14,   1, "stabil",         25, BEGINN_SPAET),
    ("Heidelerche",      69,   3, "zunahme",        28, BEGINN_SPAET),
]

# Die Verteilung, die der Bericht in der Zusammenfassung nennt — und die
# die Presseaussendung wörtlich wiederholt. Sie steht hier NICHT als
# beruhigende Konstante, sondern zusammen mit dem Jahr, aus dem sie
# stammt: eine Gegenprobe, deren Sollwert aus derselben Ausgabe kommt wie
# die Daten, kann nur die Abschrift prüfen, nie die Aktualität.
ERWARTET = {"rueckgang": 14, "stabil": 4, "zunahme": 2}
ERWARTET_STAND = STAND_JAHR

# Der Bericht wertet zusätzlich 24 Arten aus, von denen eine — der
# Zitronenzeisig — nie eine ausreichende Stichprobe erreicht.
OHNE_AUSWERTUNG = ["Zitronenzeisig"]


def baue_vogelarten() -> dict:
    log("\n[11/11] Feld- und Wiesenvögel je Art (gepflegt)")

    arten = [
        {"name": name, "wert": wert, "pro_jahr": pro_jahr,
         "einstufung": einstufung, "strecken": strecken, "beginn": beginn}
        for name, wert, pro_jahr, einstufung, strecken, beginn in ARTEN
    ]

    lang = [a for a in arten if a["beginn"] == BEGINN]
    spaet = [a for a in arten if a["beginn"] != BEGINN]

    # Gegenprobe an der Zusammenfassung des Berichts: von den 20 ab 1998
    # gerechneten Arten sind 14 rückläufig, 4 stabil, 2 zunehmend. Weicht
    # die Liste davon ab, ist beim Nachtragen etwas verrutscht.
    zaehlung = {
        "rueckgang": sum(1 for a in lang if a["einstufung"].startswith("abnahme")),
        "stabil": sum(1 for a in lang if a["einstufung"] == "stabil"),
        "zunahme": sum(1 for a in lang if a["einstufung"] == "zunahme"),
    }
    if len(lang) != 20 or zaehlung != ERWARTET:
        warnen(
            f"Feld- und Wiesenvögel je Art: {len(lang)} Arten ab {BEGINN} "
            f"mit der Verteilung {zaehlung} — der Bericht nennt 20 Arten "
            f"mit {ERWARTET}."
        )
    if ERWARTET_STAND != STAND_JAHR:
        warnen(
            f"Feld- und Wiesenvögel je Art: Die Gegenprobe {ERWARTET} stammt "
            f"aus dem Stand {ERWARTET_STAND}, die Artenwerte aus "
            f"{STAND_JAHR} — sie prüft dann nichts mehr."
        )

    # Reihenfolge prüfen, statt sie vorauszusetzen.
    werte = [a["wert"] for a in lang]
    if werte != sorted(werte):
        warnen("Feld- und Wiesenvögel je Art: Die Liste ist nicht aufsteigend "
               "sortiert — das Frontend zeichnet sie dann in falscher Ordnung.")

    schlechteste = lang[0]
    beste = lang[-1]
    anteil_rueckgang = round(zaehlung["rueckgang"] / len(lang) * 100)

    log(f"    {len(lang)} Arten ab {BEGINN}: {zaehlung['rueckgang']} weniger, "
        f"{zaehlung['stabil']} gleich, {zaehlung['zunahme']} mehr")
    log(f"    Spannweite: {schlechteste['name']} {schlechteste['wert']} % bis "
        f"{beste['name']} +{beste['wert']} %")
    log(f"    Zusätzlich {len(spaet)} Arten erst ab {BEGINN_SPAET}")

    pflegepruefung("vogelarten", BERICHT_JAHR, "Artentrends Farmland Bird Index")

    quelle_vermerken(
        name=("BirdLife Österreich — Monitoring der Brutvögel Österreichs, "
              f"Artentrends {BEGINN}–{STAND_JAHR}"),
        url=("https://www.birdlife.at/vogelschutz/forschung-und-monitoring/"
             "monitoring-der-brutvoegel-oesterreichs/"),
        lizenz="siehe Publikation",
        stand=str(STAND_JAHR),
        art="gepflegt",
    )

    return {
        "arten": lang,
        "spaete_arten": spaet,
        "ohne_auswertung": OHNE_AUSWERTUNG,
        "beginn": BEGINN,
        "beginn_spaet": BEGINN_SPAET,
        "stand": STAND_JAHR,
        "bewertet": len(lang),
        "zaehlung": zaehlung,
        "anteil_rueckgang": anteil_rueckgang,
        "schlechteste": schlechteste,
        "beste": beste,
        "pflege": {
            "art": "gepflegt",
            "quelle": (
                "Teufelbauer, N. & Seaman, B. (2026): Monitoring der Brutvögel "
                "Österreichs — Bericht über die Saison 2025. BirdLife "
                "Österreich, Wien, Tab. 3, S. 11–13; Streckenzahlen Tab. 1. "
                "Gegenprobe: Presseaussendung vom 10.08.2026."
            ),
            "bericht_jahr": BERICHT_JAHR,
            "abgerufen": "2026-08-26",
        },
        "hinweis": (
            # 198 Zeichen, Fenster 150–234.
            # 28.08.2026: Satz 1 beschrieb, was der Balken zeigt — das
            # steht als Angabe schon in der Unterzeile („Bestandsveränderung
            # je Art · 1998 bis 2025") und ist am Balken selbst zu sehen.
            "„Gleich geblieben“ heißt nicht Stillstand, sondern: die Zählung "
            "zeigt keine gesicherte Richtung. Wie sicher eine Art gezählt "
            "ist, hängt an den Strecken — sechs bei der Grauammer, 210 beim "
            "Stieglitz."
        ),
    }
