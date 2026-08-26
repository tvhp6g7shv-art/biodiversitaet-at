"""
Stand der Roten Listen Österreichs — wie alt das Wissen über die
Gefährdung der Tiergruppen ist.

GEPFLEGTE REIHE. Quelle ist die Übersichtstabelle des Umweltbundesamtes
„Übersicht über den Stand der Aktualisierung der Roten Listen".

  Quelle:    Umweltbundesamt — Rote Listen gefährdeter Tierarten,
             Übersichtstabelle Stand Oktober 2025
  URL:       https://www.umweltbundesamt.at/umweltthemen/naturschutz/
             rotelisten/rote-listen-gefaehrdeter-tierarten
  Abgerufen: 24.08.2026 (die Seite rendert clientseitig; ein einfacher
             HTTP-Abruf liefert nur das Navigationsmenü — deshalb
             abgeschrieben statt abgerufen)

Der Clou dieser Quelle: Das Umweltbundesamt nennt je Gruppe nicht nur das
Jahr der letzten Einstufung, sondern auch den Zeitraum, in dem es selbst
eine Neuauflage für nötig hält — sechs oder zwölf Jahre. Damit muss das
Dashboard keine eigene Schwelle erfinden. Der Überzug ist der Abstand
zwischen tatsächlichem Alter und dem Soll der Fachbehörde.

Vier Gruppen haben ÜBERHAUPT keine Rote Liste. Sie haben deshalb kein
Alter und dürfen nicht als Balken der Länge null erscheinen — das läse
sich als „gerade erst aktualisiert". Sie stehen separat.
"""

from __future__ import annotations

import datetime as dt

from gemeinsam import log, pflegepruefung, quelle_vermerken, warnen

STAND_JAHR = 2025
STAND_TEXT = "Oktober 2025"

# (Gruppe, letzte Einstufung oder None, Soll-Zeitraum in Jahren, Status)
# Status ist die Einstufung des Umweltbundesamtes selbst, nicht meine.
GRUPPEN = [
    ("Wanzen",                    2024, 12, "aktuell"),
    ("Ameisen",                   2024, 12, "aktuell"),
    ("Hummeln",                   2024, 12, "aktuell"),
    ("Säugetiere (ohne Fledermäuse)", 2005, 6, "in Arbeit"),
    ("Fledermäuse",               2005,  6, "in Arbeit"),
    ("Amphibien und Reptilien",   2007,  6, "in Arbeit"),
    ("Fische",                    2007,  6, "in Arbeit"),
    ("Zikaden",                   2007, 12, "in Arbeit"),
    ("Wildbienen",                None, 12, "in Arbeit"),
    ("Libellen",                  2006,  6, "in Arbeit"),
    ("Tagfalter",                 2005,  6, "in Arbeit"),
    ("Heuschrecken",              2005,  6, "in Arbeit"),
    ("Regenwürmer",               None, 12, "in Arbeit"),
    ("Blatthornkäfer",            None, 12, "in Arbeit"),
    ("Vögel",                     2017,  6, "überfällig"),
    ("Nachtfalter",               2007, 12, "überfällig"),
    ("Spinnen",                   None, 12, "überfällig"),
    ("Flusskrebse",               2009, 12, "überfällig"),
    ("Weberknechte",              2009, 12, "überfällig"),
    ("Schnecken",                 2007, 12, "überfällig"),
    ("Urzeitkrebse",              2002, 12, "überfällig"),
    ("Köcherfliegen",             2009, 12, "überfällig"),
    ("Netzflügler",               2005, 12, "überfällig"),
    ("Schnabelfliegen",           2005, 12, "überfällig"),
    ("Skorpione",                 2009, 12, "überfällig"),
    ("Käfer",                     1994, 12, "überfällig"),
    ("Wasserkäfer",               2005, 12, "überfällig"),
]

# Zum Vergleich, aus derselben Quellfamilie: Die Rote Liste der Farn- und
# Blütenpflanzen wurde 2022 neu aufgelegt (1.274 Arten, davon 66 vergeblich
# gesucht). Sie steht nicht in der Tiergruppentabelle und zählt hier nicht
# mit — sie dient nur als Beleg, dass Neuauflagen möglich sind.
PFLANZEN_JAHR = 2022
PFLANZEN_ARTEN = 1274


def baue_rotelisten() -> dict:
    log("\n[4/11] Rote Listen — Stand der Aktualisierung (gepflegt)")

    heute = dt.date.today().year

    eintraege = []
    for name, jahr, soll, status in GRUPPEN:
        eintrag = {
            "gruppe": name,
            "jahr": jahr,
            "soll_jahre": soll,
            "status": status,
        }
        if jahr is not None:
            alter = heute - jahr
            eintrag["alter"] = alter
            # Überzug: um wie viele Jahre die Liste ihr eigenes Soll reißt.
            # Negativ heißt: noch innerhalb des Intervalls.
            eintrag["ueberzug"] = alter - soll
        else:
            eintrag["alter"] = None
            eintrag["ueberzug"] = None
        eintraege.append(eintrag)

    mit_liste = [e for e in eintraege if e["jahr"] is not None]
    ohne_liste = [e for e in eintraege if e["jahr"] is None]

    if not mit_liste:
        warnen("Rote Listen: keine Gruppe mit Jahresangabe — Abschnitt bleibt leer")
        return {}

    # Gegenprobe gegen die Statusspalte der Quelle: Was das Umweltbundesamt
    # „aktuell" nennt, sollte auch rechnerisch im Intervall liegen. Weicht
    # das ab, ist entweder die Tabelle älter als ihr Stand oder ich habe
    # mich verschrieben.
    for e in mit_liste:
        if e["status"] == "aktuell" and e["ueberzug"] > 0:
            warnen(
                f"Rote Listen: {e['gruppe']} gilt als „aktuell“, reißt das "
                f"eigene Soll aber um {e['ueberzug']} Jahre — Tabelle prüfen"
            )

    aeltester = max(mit_liste, key=lambda e: e["alter"])
    groesster_ueberzug = max(mit_liste, key=lambda e: e["ueberzug"])

    zaehlung = {}
    for e in eintraege:
        zaehlung[e["status"]] = zaehlung.get(e["status"], 0) + 1

    log(f"    {len(eintraege)} Gruppen · "
        + " · ".join(f"{k}: {v}" for k, v in zaehlung.items()))
    log(f"    Ohne jede Rote Liste: {len(ohne_liste)} "
        f"({', '.join(e['gruppe'] for e in ohne_liste)})")
    log(f"    Älteste: {aeltester['gruppe']} von {aeltester['jahr']} "
        f"({aeltester['alter']} Jahre)")
    log(f"    Größter Überzug: {groesster_ueberzug['gruppe']} "
        f"(+{groesster_ueberzug['ueberzug']} Jahre über dem Soll)")
    pflegepruefung("rotelisten", STAND_JAHR, "Rote-Listen-Übersicht")

    quelle_vermerken(
        name=("Umweltbundesamt — Rote Listen gefährdeter Tierarten, "
              f"Stand der Aktualisierung ({STAND_TEXT})"),
        url=("https://www.umweltbundesamt.at/umweltthemen/naturschutz/"
             "rotelisten/rote-listen-gefaehrdeter-tierarten"),
        lizenz="siehe Publikation",
        stand=str(STAND_JAHR),
        art="gepflegt",
    )

    return {
        "eintraege": eintraege,
        "bezugsjahr": heute,
        "gruppen_gesamt": len(eintraege),
        "ohne_liste": len(ohne_liste),
        "ohne_liste_namen": [e["gruppe"] for e in ohne_liste],
        "zaehlung": zaehlung,
        "aktuell": zaehlung.get("aktuell", 0),
        "aeltester": aeltester,
        "groesster_ueberzug": groesster_ueberzug,
        "pflanzen": {"jahr": PFLANZEN_JAHR, "arten": PFLANZEN_ARTEN},
        "pflege": {
            "art": "gepflegt",
            "quelle": ("Umweltbundesamt: Übersicht über den Stand der "
                       f"Aktualisierung der Roten Listen, {STAND_TEXT}."),
            "bericht_jahr": STAND_JAHR,
            "abgerufen": "2026-08-24",
        },
        "hinweis": (
            "Der helle Teil des Balkens ist der Zeitraum, in dem das "
            "Umweltbundesamt selbst eine Neuauflage vorsieht — sechs Jahre "
            "bei Wirbeltieren, zwölf bei den übrigen. Der dunkle Teil ist "
            "das, was darüber hinausgeht."
        ),
    }
