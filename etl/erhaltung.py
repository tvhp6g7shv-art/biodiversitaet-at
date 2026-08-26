"""
Erhaltungszustand der Lebensraumtypen und Arten — Artikel 17 FFH-Richtlinie.

GEPFLEGTE REIHE. Die EU-Datenbank hält die Meldungen zwar als CSV bereit,
aber nur über eine Landingpage mit JavaScript-Download; ein stabiler
Direktlink existiert nicht. Die Kennzahlen sind deshalb aus dem nationalen
Bericht abgeschrieben.

  Quelle:    Umweltbundesamt (2020): Bericht nach Artikel 17 FFH-Richtlinie
             — Zusammenfassung. REP-0734, Band 2, Wien, S. 6–7 (Abbildung I).
  PDF:       https://www.verwaltung.steiermark.at/cms/dokumente/12812743_123331268/
             bb1de298/REP0734_Band%202_Bericht.pdf
  Gegenprobe: https://www.umweltdachverband.at/themen/naturschutz/natura-2000/
             themen/artikel-17-bericht (identische Werte)
  Abgerufen: 24.08.2026

ZWEI DINGE, DIE BEIM WEITERPFLEGEN AUFFALLEN WERDEN:

1. Die Arten-Anteile summieren sich auf 99 %, nicht auf 100. Das ist kein
   Abschreibfehler, sondern die Rundung der Quelle — sie rundet jede der
   vier Kategorien auf ganze Prozent. Nicht „glattziehen": eine korrigierte
   Zahl wäre erfunden.

2. Gezählt werden BEWERTUNGEN, nicht Schutzgüter. Österreich liegt in zwei
   biogeografischen Regionen, alpin und kontinental, und jeder Lebensraumtyp
   wird in jeder Region, in der er vorkommt, einzeln bewertet. Deshalb
   stehen 71 Lebensraumtypen für 117 Bewertungen und 211 Arten für 345.
   Genau diese Zweiteilung ist auch der Grund, warum Österreich hier kein
   Einzelfall ist: Die alpine Region reicht über Deutschland, Italien,
   Slowenien und Frankreich, die kontinentale über halb Mitteleuropa.

NÄCHSTE PERIODE: Die Meldung für 2019–2024 war bis 31.12.2025 fällig. Am
24.08.2026 ist sie öffentlich nicht auffindbar — weder beim Umweltbundesamt
noch im EEA-Datahub, und die EU-weite Auswertung der biogeografischen
Bewertungen läuft noch (öffentliche Konsultation bis 16.08.2026). Sobald
sie da ist, wird aus diesem Abschnitt ein Vergleich zweier Perioden statt
einer Momentaufnahme.
"""

from __future__ import annotations

from gemeinsam import log, pflegepruefung, quelle_vermerken, warnen

STAND_JAHR = 2020          # Erscheinungsjahr des Berichts
PERIODE = "2013–2018"

# Reihenfolge ist die Leserichtung des gestapelten Balkens: von gut nach
# schlecht, „unbekannt" ganz hinten. Nicht umsortieren — die Farbzuordnung
# im Frontend hängt an der Position.
KATEGORIEN = [
    {"kuerzel": "FV", "name": "günstig"},
    {"kuerzel": "U1", "name": "unzureichend"},
    {"kuerzel": "U2", "name": "schlecht"},
    {"kuerzel": "XX", "name": "unbekannt"},
]

GRUPPEN = [
    {
        "name": "Lebensraumtypen",
        "anteile": [18.0, 35.0, 44.0, 3.0],
        "schutzgueter": 71,
        "bewertungen": 117,
        "regionen": {"alpin": 63, "kontinental": 54},
    },
    {
        "name": "Arten",
        "anteile": [14.0, 48.0, 34.0, 3.0],
        "schutzgueter": 211,
        "bewertungen": 345,
        "regionen": {"alpin": 171, "kontinental": 174},
    },
]


def baue_erhaltung() -> dict:
    log("\n[5/11] Erhaltungszustand — Artikel 17 FFH (gepflegt)")

    gruppen = []
    for gruppe in GRUPPEN:
        summe = round(sum(gruppe["anteile"]), 1)
        # Nur melden, wenn die Rundung mehr als einen Punkt ausmacht — bei
        # vier auf ganze Prozent gerundeten Werten sind 99 oder 101 normal.
        if abs(summe - 100) > 1.5:
            warnen(
                f"Erhaltungszustand ({gruppe['name']}): Anteile summieren sich "
                f"auf {summe} % — das ist mehr als Rundung erklärt"
            )
        guenstig = gruppe["anteile"][0]
        schlecht = gruppe["anteile"][2]
        gruppen.append({**gruppe, "summe": summe,
                        "guenstig": guenstig, "schlecht": schlecht})
        log(f"    {gruppe['name']}: {guenstig} % günstig, {schlecht} % schlecht "
            f"({gruppe['bewertungen']} Bewertungen aus "
            f"{gruppe['schutzgueter']} Schutzgütern, Summe {summe} %)")

    pflegepruefung("erhaltung", STAND_JAHR, "Artikel-17-Bericht")

    quelle_vermerken(
        name=("Umweltbundesamt (2020) — Bericht nach Artikel 17 "
              "FFH-Richtlinie, REP-0734"),
        url=("https://www.umweltbundesamt.at/umweltthemen/naturschutz/"
             "biologischevielfalt/nationaleberichte"),
        lizenz="siehe Publikation",
        stand=PERIODE,
        art="gepflegt",
    )

    return {
        "gruppen": gruppen,
        "kategorien": KATEGORIEN,
        "periode": PERIODE,
        "stand": STAND_JAHR,
        "naechste_periode": "2019–2024",
        "naechste_faellig": "31.12.2025",
        "naechste_vorhanden": False,
        "pflege": {
            "art": "gepflegt",
            "quelle": ("Umweltbundesamt (2020): Bericht nach Artikel 17 "
                       "FFH-Richtlinie — Zusammenfassung. REP-0734 Band 2, "
                       "Wien, S. 6–7."),
            "bericht_jahr": STAND_JAHR,
            "abgerufen": "2026-08-24",
        },
        "hinweis": (
            "Gezählt werden Bewertungen, nicht Schutzgüter: Österreich liegt "
            "in zwei biogeografischen Regionen, und jeder Lebensraumtyp wird "
            "in jeder einzeln beurteilt. Beide Regionen reichen weit über die "
            "Staatsgrenze hinaus."
        ),
    }
