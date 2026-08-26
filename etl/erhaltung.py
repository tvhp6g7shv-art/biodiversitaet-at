"""
Erhaltungszustand der Lebensraumtypen und Arten — Artikel 17 FFH-Richtlinie.

GEPFLEGTE REIHE, ausgezählt aus dem Eionet-Berichtswerkzeug.

  Quelle:    Eionet, Article 17 Web Tool — Österreich, Berichtsperiode 6
             (2019–2024), alle neun Arten- und alle neun Lebensraumgruppen.
  URL:       https://nature-art17.eionet.europa.eu/article17/species/report/
             ?period=6&group=<GRUPPE>&country=AT&region=
             (und .../habitat/report/ mit denselben Parametern)
  Gegenprobe: Umweltbundesamt (2020), REP-0734 Band 2, S. 6–7 — die
             Vorperiode 2013–2018. Ihre Anteile werden unten gegen die
             Vorwerte gerechnet, die der neue Bericht selbst wiedergibt.
  Abgerufen: 26.08.2026

WARUM DIESES MODUL AM 26.08.2026 NEU GESCHRIEBEN WURDE

Bis dahin stand hier die Periode **2013–2018**, mit dem Vermerk, die
Meldung für 2019–2024 sei „öffentlich nicht auffindbar". Das galt für den
nationalen Bericht des Umweltbundesamts — **nicht für das Eionet-Werkzeug**,
in dem die Meldung vollständig liegt: alle 18 Gruppen befüllt, Spalte
„Curr. CS" durchgehend belegt. Gesucht wurde an der falschen Tür.

Aufgefallen ist es beim Lesen von `kpi.json`, wo `erhaltung_periode` noch
auf 2013–2018 stand, während `rueckkehrer` am selben Tag Zahlen aus
genau derselben Periode-6-Tabelle zog.

VIER DINGE, DIE BEIM WEITERPFLEGEN AUFFALLEN WERDEN

1. Gezählt werden BEWERTUNGEN, nicht Schutzgüter. Österreich liegt in
   zwei biogeografischen Regionen, alpin und kontinental, und jedes
   Schutzgut wird in jeder Region, in der es vorkommt, einzeln bewertet.
   71 Lebensraumtypen ergeben 114 Bewertungen, 211 Arten ergeben 338.

2. Der Nenner ist nicht die Zeilenzahl. Das Werkzeug führt Zeilen mit
   `Curr. CS = N/A` und `% MS = 0` kursiv und kennzeichnet sie selbst als
   „not taken into account" — 21 bei den Arten, 13 bei den Lebensraum-
   typen. Sie gehören heraus, sonst sinkt jeder Anteil.

3. Die Vorperiode kommt aus DEMSELBEN Bericht (Spalte „Prev. CS"), nicht
   aus der alten Publikation. Zwei Berichtsjahrgänge nebeneinander zu
   legen ist genau der Fehler, der bei den Vogelzahlen aufgefallen ist:
   Jeder Bericht rechnet die Vorperiode neu. `_vorperiode_pruefen()`
   hält die Prev-CS-Anteile trotzdem gegen die alte Veröffentlichung —
   nicht um sie zu ersetzen, sondern um zu belegen, dass beide dasselbe
   meinen. Größte Abweichung derzeit 1,2 Punkte.

4. Beim Parsen ist die Spalte unmittelbar VOR „Curr. CS" der
   Zukunftsaussichten-Status, nicht dessen Kopie. Sie weicht in etlichen
   Zeilen ab.

DER EIGENTLICHE BEFUND STEHT NICHT IM BALKEN

„Günstig" steigt, „schlecht" fällt — und das heißt fast nichts. Artikel 17
führt für jede Änderung eine eigene Spalte („Status Nature of change"):
`genuine` für eine tatsächliche Veränderung, `knowledge` und `method`
für besseres Wissen und geänderte Verfahren. Rechnet man nur die echten:
bei den Arten 23 Verbesserungen gegen 18 Verschlechterungen, netto fünf
von 338. Bei den Lebensraumtypen sind von zehn Verbesserungen vier echt,
und die fünf neuen „günstig"-Fälle beruhen überwiegend auf geänderter
Methode. Gleichzeitig rutschen 21 Bewertungen nach „unbekannt".

Ohne diese Aufschlüsselung wäre „es wird besser" eine unverdiente
Aussage. Sie steht deshalb als Notiz unter der Grafik.
"""

from __future__ import annotations

from gemeinsam import log, pflegepruefung, quelle_vermerken, warnen

STAND_JAHR = 2026          # Jahr, in dem die Meldung im Werkzeug lag
PERIODE = "2019–2024"
VORPERIODE = "2013–2018"

# Reihenfolge ist die Leserichtung des gestapelten Balkens: von gut nach
# schlecht, „unbekannt" ganz hinten. Nicht umsortieren — die Farbzuordnung
# im Frontend hängt an der Position.
KATEGORIEN = [
    {"kuerzel": "FV", "name": "günstig"},
    {"kuerzel": "U1", "name": "unzureichend"},
    {"kuerzel": "U2", "name": "schlecht"},
    {"kuerzel": "XX", "name": "unbekannt"},
]

# Anzahl der Bewertungen je Klasse, ausgezählt — nicht Prozente aus einer
# Publikation. Reihenfolge wie KATEGORIEN.
GRUPPEN = [
    {
        "name": "Lebensraumtypen",
        "jetzt":  [26, 33, 45, 10],
        "vorher": [21, 39, 50, 4],
        "ohne_vorwert": 0,
        "schutzgueter": 71,
        "zeilen_gesamt": 127,
        "wechsel": {
            "unveraendert": 87,
            "verbessert": 10, "verbessert_echt": 4,
            "verschlechtert": 3, "verschlechtert_echt": 0,
            "nach_unbekannt": 10, "aus_unbekannt": 4,
        },
        # Häufigkeit der Spalte „Status Nature of change", alle Bewertungen
        "natur": {"noChange": 86, "genuine": 5, "knowledge": 6,
                  "method": 5, "unknown": 11, "other": 1},
    },
    {
        "name": "Arten",
        "jetzt":  [65, 126, 129, 18],
        "vorher": [47, 165, 117, 6],
        "ohne_vorwert": 3,
        "schutzgueter": 211,
        "zeilen_gesamt": 359,
        "wechsel": {
            "unveraendert": 256,
            "verbessert": 39, "verbessert_echt": 23,
            "verschlechtert": 28, "verschlechtert_echt": 18,
            "nach_unbekannt": 11, "aus_unbekannt": 1,
        },
        "natur": {"noChange": 254, "genuine": 41, "knowledge": 14,
                  "method": 11, "unknown": 8, "other": 7,
                  "erstmals_gemeldet": 3},
    },
]

# Die alte Veröffentlichung, gegen die die Vorwerte geprüft werden.
# Umweltbundesamt (2020), REP-0734 Band 2, S. 6–7 — auf ganze Prozent
# gerundet, deshalb summieren die Arten dort auf 99.
UBA_VORPERIODE = {
    "Lebensraumtypen": [18.0, 35.0, 44.0, 3.0],
    "Arten": [14.0, 48.0, 34.0, 3.0],
}
ABWEICHUNG_GRENZE = 2.0    # Prozentpunkte


def _anteile(zahlen: list[int]) -> tuple[list[float], int]:
    """Anteile in Prozent, eine Nachkommastelle, plus Nenner."""
    nenner = sum(zahlen)
    return [round(z / nenner * 100, 1) for z in zahlen], nenner


def _vorperiode_pruefen(name: str, vorher_anteile: list[float]) -> None:
    """
    Hält die Vorwerte des neuen Berichts gegen die alte Veröffentlichung.

    Das ersetzt die alte Quelle nicht — es belegt, dass beide dieselbe
    Periode meinen. Laufen sie auseinander, hat entweder das Werkzeug
    seine Zählweise geändert oder beim Auszählen ist etwas verrutscht;
    in beiden Fällen wäre der Periodenvergleich wertlos.
    """
    alt = UBA_VORPERIODE.get(name)
    if not alt:
        return
    abweichungen = [round(abs(neu - a), 1) for neu, a in zip(vorher_anteile, alt)]
    groesste = max(abweichungen)
    if groesste > ABWEICHUNG_GRENZE:
        warnen(
            f"Erhaltungszustand ({name}): Die Vorwerte des Berichts "
            f"{PERIODE} weichen um bis zu {groesste} Punkte von der "
            f"Veröffentlichung zur Periode {VORPERIODE} ab "
            f"({vorher_anteile} gegen {alt}) — der Periodenvergleich ruht "
            f"dann nicht mehr auf derselben Grundlage."
        )
    else:
        log(f"    {name}: Vorwerte decken sich mit der Publikation zu "
            f"{VORPERIODE} (größte Abweichung {groesste} Punkte)")


def baue_erhaltung() -> dict:
    log("\n[5/11] Erhaltungszustand — Artikel 17 FFH (gepflegt)")

    gruppen = []
    for gruppe in GRUPPEN:
        anteile, bewertungen = _anteile(gruppe["jetzt"])
        vorher_anteile, vorher_bewertungen = _anteile(gruppe["vorher"])

        # Der Nenner muss in beiden Perioden derselbe sein: „Prev. CS"
        # steht in denselben Zeilen wie „Curr. CS". Weicht er ab, sind es
        # die Zeilen ohne Vorwert — und nur die.
        erwartet = bewertungen - gruppe["ohne_vorwert"]
        if vorher_bewertungen != erwartet:
            warnen(
                f"Erhaltungszustand ({gruppe['name']}): {vorher_bewertungen} "
                f"Vorwerte bei {bewertungen} Bewertungen und "
                f"{gruppe['ohne_vorwert']} Zeilen ohne Vorwert — erwartet "
                f"waren {erwartet}."
            )

        _vorperiode_pruefen(gruppe["name"], vorher_anteile)

        w = gruppe["wechsel"]
        # Die Summe der Wechselarten muss die Bewertungen mit Vorwert
        # ergeben. Ohne diese Prüfung könnte eine Kategorie fehlen, ohne
        # dass es auffiele.
        summe_wechsel = (w["unveraendert"] + w["verbessert"]
                         + w["verschlechtert"] + w["nach_unbekannt"]
                         + w["aus_unbekannt"])
        if summe_wechsel != vorher_bewertungen:
            warnen(
                f"Erhaltungszustand ({gruppe['name']}): Die Wechselarten "
                f"summieren auf {summe_wechsel}, es gibt aber "
                f"{vorher_bewertungen} Bewertungen mit Vorwert."
            )

        netto_echt = w["verbessert_echt"] - w["verschlechtert_echt"]

        gruppen.append({
            "name": gruppe["name"],
            "anteile": anteile,
            "anzahl": gruppe["jetzt"],
            "vorher_anteile": vorher_anteile,
            "vorher_anzahl": gruppe["vorher"],
            "bewertungen": bewertungen,
            "schutzgueter": gruppe["schutzgueter"],
            "wechsel": {**w, "netto_echt": netto_echt},
            "natur": gruppe["natur"],
            "guenstig": anteile[0],
            "schlecht": anteile[2],
            "guenstig_vorher": vorher_anteile[0],
            "schlecht_vorher": vorher_anteile[2],
        })

        log(f"    {gruppe['name']}: {anteile[0]} % günstig, {anteile[2]} % "
            f"schlecht ({bewertungen} Bewertungen aus "
            f"{gruppe['schutzgueter']} Schutzgütern)")
        log(f"      Vorperiode {VORPERIODE}: {vorher_anteile[0]} % günstig, "
            f"{vorher_anteile[2]} % schlecht")
        log(f"      echte Änderungen: +{w['verbessert_echt']} / "
            f"−{w['verschlechtert_echt']} → netto {netto_echt:+d} von "
            f"{bewertungen}")

    pflegepruefung("erhaltung", STAND_JAHR, "Artikel-17-Bericht")

    quelle_vermerken(
        name=("Eionet Artikel-17-Berichtswerkzeug — Österreich, "
              "Lebensraumtypen und Arten"),
        url=("https://nature-art17.eionet.europa.eu/article17/species/report/"
             "?period=6&group=Mammals&country=AT&region="),
        lizenz="Europäische Umweltagentur, Weiterverwendung erlaubt",
        stand=PERIODE,
        art="gepflegt",
    )

    arten = next(g for g in gruppen if g["name"] == "Arten")
    lrt = next(g for g in gruppen if g["name"] == "Lebensraumtypen")
    nach_unbekannt = (arten["wechsel"]["nach_unbekannt"]
                      + lrt["wechsel"]["nach_unbekannt"])

    return {
        "gruppen": gruppen,
        "kategorien": KATEGORIEN,
        "periode": PERIODE,
        "vorperiode": VORPERIODE,
        "stand": STAND_JAHR,
        # Der Vermerk der Vorgängerfassung. Die Folgeperiode IST da —
        # das Feld bleibt, weil das Frontend es abfragt.
        "naechste_vorhanden": True,
        "pflege": {
            "art": "gepflegt",
            "quelle": (
                "Eionet, Article 17 Web Tool: Meldung Österreichs nach "
                "Artikel 17 FFH-Richtlinie, Berichtsperiode 2019–2024, alle "
                "neun Arten- und neun Lebensraumgruppen, ausgezählt am "
                '26.08.2026. Vorperiode aus der Spalte „Prev. CS“ desselben '
                "Berichts. Gegenprobe: Umweltbundesamt (2020), REP-0734 "
                "Band 2, S. 6–7."
            ),
            "bericht_jahr": STAND_JAHR,
            "abgerufen": "2026-08-26",
        },
        "notiz": (
            f"Dass „günstig“ zunimmt, heißt weniger, als es aussieht. Der "
            f"Bericht vermerkt bei jeder Änderung, ob sie <strong>echt</strong> "
            f"ist oder nur auf besserem Wissen beruht. Bei den Arten wurden "
            f"{arten['wechsel']['verbessert']} Bewertungen besser und "
            f"{arten['wechsel']['verschlechtert']} schlechter — als "
            f"tatsächliche Veränderung gemeldet sind davon "
            f"{arten['wechsel']['verbessert_echt']} und "
            f"{arten['wechsel']['verschlechtert_echt']}. Netto bleiben "
            f"{arten['wechsel']['netto_echt']} von {arten['bewertungen']}. "
            f"Bei den Lebensraumtypen sind von "
            f"{lrt['wechsel']['verbessert']} Verbesserungen "
            f"{lrt['wechsel']['verbessert_echt']} echt. Gleichzeitig "
            f"rutschten {nach_unbekannt} Bewertungen nach „unbekannt“."
        ),
        "hinweis": (
            "Gezählt werden Bewertungen, nicht Schutzgüter: Österreich liegt "
            "in zwei Naturräumen, und jede Art wird in jedem einzeln "
            "beurteilt. Beide reichen weit über die Staatsgrenze hinaus — "
            "der Alpenraum bis nach Frankreich."
        ),
    }
