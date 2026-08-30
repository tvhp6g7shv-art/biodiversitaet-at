"""
Gefährdete Waldarten — Rote Listen 1986, 1999 und 2022.

WARUM DIESER ABSCHNITT: Die Summe wächst von 200 auf 286 gefährdete
waldgebundene Gefäßpflanzen. Das ist die Zahl, die der Bericht in die
Überschrift stellt — und sie ist die uninteressantere Hälfte. Die Geschichte
steckt in der Verschiebung NACH OBEN: „vom Aussterben bedroht" geht von 11
über 13 auf 43, während die unterste Stufe „gefährdet" seit 1999 sogar wieder
zurückgeht. Es werden nicht nur mehr Arten gefährdet, die bereits gefährdeten
rutschen weiter ab.

Die Gegenprobe dazu steht in derselben Tabelle: die Kryptogamen (Moose und
Farne) liegen über alle drei Listen bei 96, 97, 96. Der Anstieg ist also kein
allgemeiner Trend, sondern einer der Gefäßpflanzen.

DIE FALLE IN DIESEM KAPITEL — eine Zahl, die um das Fünffache danebenliegt:

Der Bericht schreibt wörtlich, die Auswertung „umfasst insgesamt 1.803
waldabhängige Arten, die laut der Roten Liste ... als regional ausgestorben,
vom Aussterben bedroht, stark gefährdet oder gefährdet eingestuft sind".
Zwei Sätze später steht: „Unter den gefährdeten Waldarten befinden sich
insgesamt 382 Taxa, davon 286 Gefäßpflanzen ... und 96 Kryptogamen."

Beides kann nicht stimmen. Die Rechnung entscheidet:

    1341 (Gefäßpflanzen) + 462 (Kryptogamen) = 1803   bewertete Taxa
    1341 / 1803 = 74,4 %   der Bericht nennt „rund 75 %"
     462 / 1803 = 25,6 %   der Bericht nennt „etwa 25 %"

Die Prozentangaben passen zum BEWERTETEN Bestand, nicht zum gefährdeten.
1.803 ist der Nenner, 382 der Zähler. Wer „1.803 gefährdete Waldarten"
schreibt, ist um den Faktor 4,7 daneben — und der Satz im Bericht lädt
ausdrücklich dazu ein.

WAS DEN VERGLEICH ÜBER DIE LISTEN HINWEG TRÄGT: Die Gesamtzahl der Taxa ist
in allen drei Roten Listen dieselbe — 56 Bäume, 1.341 Gefäßpflanzen, 462
Kryptogamen. Es wird derselbe Artenbestand dreimal neu bewertet, nicht ein
wachsender. Anteile sind deshalb ohne Umbasierung vergleichbar. Das ist bei
Roten Listen nicht selbstverständlich und der Grund, warum diese Tabelle
überhaupt eine Zeitreihe hergibt.

WAS NICHT GEHT: Bäume sind eine Teilmenge der Gefäßpflanzen, keine eigene
Gruppe. Ihre 9 gefährdeten Taxa stecken in den 286 bereits drin. Nie
nebeneinanderstellen und schon gar nicht addieren.

Quelle: Waldbiodiversitätsbericht, BFW-Berichte 155/2026, Tab. 7 (S. 40),
dort ausgewiesen als „Quelle: BFW, 2025". Das Impressum des Berichts
gestattet den auszugsweisen Abdruck mit Quellenangabe — dieser Abschnitt
hängt NICHT an der offenen waldinventur.at-Freigabe.

Abgerufen und nachgerechnet am 28.08.2026.
"""

from __future__ import annotations

import config
from gemeinsam import log, pflegepruefung, quelle_vermerken, warnen

# ---------------------------------------------------------------------------
# Tab. 7, wörtlich übernommen. Reihenfolge der Stufen von leicht nach schwer.
# ---------------------------------------------------------------------------
STUFEN = ["gefährdet", "stark gefährdet", "vom Aussterben bedroht",
          "regional ausgestorben"]

LISTEN = ["RL 1986", "RL 1999", "RL 2022"]

# name -> (Gesamtzahl der Taxa, {Liste: (gefährdet, stark, aussterben, ausgestorben)})
GRUPPEN = {
    "Gefäßpflanzen": (1341, {
        "RL 1986": (120, 67, 11, 2),
        "RL 1999": (170, 67, 13, 3),
        "RL 2022": (157, 83, 43, 3),
    }),
    "Moose und Farne": (462, {
        "RL 1986": (47, 29, 12, 8),
        "RL 1999": (61, 21, 6, 9),
        "RL 2022": (61, 19, 7, 9),
    }),
}

# Teilmenge der Gefäßpflanzen — nur für den Aufklapper, nie in der Grafik.
BAEUME = (56, {
    "RL 1986": (6, 3, 0, 0),
    "RL 1999": (6, 4, 0, 0),
    "RL 2022": (4, 4, 1, 0),
})

# Die Sollwerte, die der Bericht im Fließtext nennt. Gegenprobe der Abschrift.
KONTROLLE = {
    "gefaehrdet_gesamt_2022": 382,
    "gefaesspflanzen_2022": 286,
    "kryptogamen_2022": 96,
    "gefaesspflanzen_1986": 200,
    "bewertet_gesamt": 1803,
}

# Baumarten, die der Bericht namentlich nennt. Für den Aufklapper.
NAMENTLICH = {
    "vom Aussterben bedroht": ["Flaum-Mehlbeere"],
    "stark gefährdet": ["Europäischer Wildapfel", "Schwarzpappel",
                        "Lorbeerweide", "Speierling"],
    "gefährdet": ["Edelkastanie", "Donauschmalblättrige Esche",
                  "mehrere Mehlbeer-Arten"],
}


def _summe(werte: tuple[int, ...]) -> int:
    return sum(werte)


def _gegenprobe() -> None:
    """
    Prüft die Abschrift gegen die Zahlen, die der Bericht im Fließtext nennt.

    Diese Prüfung sagt NICHTS über die Aktualität — sie vergleicht gegen
    Sollwerte aus derselben Ausgabe wie die Daten. Sie fängt Tippfehler,
    nicht einen verpassten Berichtsjahrgang. Für den zweiten Fall läuft
    `pflegepruefung()`.
    """
    gp_2022 = _summe(GRUPPEN["Gefäßpflanzen"][1]["RL 2022"])
    kr_2022 = _summe(GRUPPEN["Moose und Farne"][1]["RL 2022"])
    gp_1986 = _summe(GRUPPEN["Gefäßpflanzen"][1]["RL 1986"])
    bewertet = sum(taxa for taxa, _ in GRUPPEN.values())

    proben = {
        "gefaesspflanzen_2022": gp_2022,
        "kryptogamen_2022": kr_2022,
        "gefaesspflanzen_1986": gp_1986,
        "gefaehrdet_gesamt_2022": gp_2022 + kr_2022,
        "bewertet_gesamt": bewertet,
    }
    for name, eigen in proben.items():
        soll = KONTROLLE[name]
        if eigen != soll:
            warnen(
                f"Waldarten: eigene Summe {eigen} weicht bei `{name}` vom "
                f"im Bericht genannten Wert {soll} ab — Tab. 7 nachlesen"
            )

    # Die Verwechslung, vor der die Modulbeschreibung warnt, hier hart geprüft:
    # 1.803 ist der bewertete Bestand, nicht der gefährdete. Wenn beide je
    # gleich groß würden, wäre eine der beiden Zahlen falsch abgeschrieben.
    if proben["gefaehrdet_gesamt_2022"] >= bewertet:
        warnen(
            "Waldarten: die Zahl der gefährdeten Taxa erreicht den bewerteten "
            "Bestand — Zähler und Nenner sind vertauscht."
        )

    # Bäume müssen eine echte Teilmenge der Gefäßpflanzen bleiben.
    for liste in LISTEN:
        if _summe(BAEUME[1][liste]) > _summe(GRUPPEN["Gefäßpflanzen"][1][liste]):
            warnen(f"Waldarten: Bäume übersteigen die Gefäßpflanzen in {liste}")


def baue_waldarten() -> dict | None:
    log("\n[15/15] Gefährdete Waldarten — Rote Listen 1986/1999/2022 (gepflegt)")

    # Die Rote Liste der Gefäßpflanzen erschien 1986, 1999, 2022 — rund
    # zwei Jahrzehnte Abstand. Ein Fünfjahresfenster wäre sinnlos eng.
    pflegepruefung("waldarten", 2022, "Rote Liste Gefäßpflanzen 2022")
    _gegenprobe()

    gruppen = []
    for name, (taxa, listen) in GRUPPEN.items():
        eintraege = []
        for liste in LISTEN:
            werte = listen[liste]
            gesamt = _summe(werte)
            eintraege.append({
                "liste": liste,
                "jahr": int(liste.split()[1]),
                "stufen": dict(zip(STUFEN, werte)),
                "gefaehrdet_gesamt": gesamt,
                "anteil": round(gesamt / taxa * 100, 1),
            })
        gruppen.append({
            "name": name,
            "taxa_bewertet": taxa,
            "eintraege": eintraege,
            "veraenderung": eintraege[-1]["gefaehrdet_gesamt"]
                            - eintraege[0]["gefaehrdet_gesamt"],
        })

    gp = gruppen[0]["eintraege"]
    schwerste = STUFEN[2]   # vom Aussterben bedroht

    daten = {
        "stand": "Rote Liste 2022",
        "abgerufen": "2026-08-28",
        "listen": LISTEN,
        "stufen": STUFEN,
        "gruppen": gruppen,
        "bewertet_gesamt": KONTROLLE["bewertet_gesamt"],
        "gefaehrdet_gesamt": KONTROLLE["gefaehrdet_gesamt_2022"],
        # Die Kennzahl der Kachel: Stand, kein Verlauf.
        "kachel_wert": gp[-1]["gefaehrdet_gesamt"],
        "kachel_anteil": gp[-1]["anteil"],
        # Die eigentliche Aussage des Abschnitts.
        "schwerste_stufe": {
            "name": schwerste,
            "frueher": gp[0]["stufen"][schwerste],
            "jetzt": gp[-1]["stufen"][schwerste],
            "faktor": round(gp[-1]["stufen"][schwerste]
                            / gp[0]["stufen"][schwerste], 1),
        },
        # Die Gegenprobe, die zeigt, dass es kein allgemeiner Trend ist.
        "unveraendert": {
            "name": gruppen[1]["name"],
            "frueher": gruppen[1]["eintraege"][0]["gefaehrdet_gesamt"],
            "jetzt": gruppen[1]["eintraege"][-1]["gefaehrdet_gesamt"],
        },
        "baeume": {
            "taxa_bewertet": BAEUME[0],
            "gefaehrdet_2022": _summe(BAEUME[1]["RL 2022"]),
            "gefaehrdet_1986": _summe(BAEUME[1]["RL 1986"]),
            "namentlich": NAMENTLICH,
        },
        # Einordnung unter der Grafik, Konvention 150–234 Zeichen. Gemessen: 208.
        "hinweis": (
            "Alle drei Listen bewerten denselben Artenbestand neu, nicht einen "
            "wachsenden — die Balken sind deshalb direkt vergleichbar. Moose und "
            "Farne stehen daneben, weil sich bei ihnen seit 1986 fast nichts "
            "verändert hat."
        ),
    }

    quelle_vermerken(
        "Gefährdete Waldarten",
        "https://fprn.info/wp-content/uploads/2026/05/"
        "Waldbiodiversitaetsbericht_Final_May-2026.pdf",
        "Waldbiodiversitätsbericht, BFW-Berichte 155/2026, Tab. 7",
        "Rote Liste 2022",
        "gepflegt",
    )

    log(f"  Gefäßpflanzen {gp[0]['gefaehrdet_gesamt']} → "
        f"{gp[-1]['gefaehrdet_gesamt']} von {gruppen[0]['taxa_bewertet']} · "
        f"„{schwerste}\" {daten['schwerste_stufe']['frueher']} → "
        f"{daten['schwerste_stufe']['jetzt']} "
        f"({daten['schwerste_stufe']['faktor']}×) · Moose und Farne "
        f"{daten['unveraendert']['frueher']} → {daten['unveraendert']['jetzt']}")

    return daten
