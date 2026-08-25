"""
Rote Liste der gefährdeten Biotoptypen Österreichs.

GEPFLEGTE REIHE. Die Rote Liste erschien in Teilbänden über sechs Jahre
verteilt und liegt nur als PDF vor.

  Quelle:    Umweltbundesamt — Rote Listen gefährdeter Biotoptypen,
             Gesamtbilanz über die Teilbände M-155 bis M-174 und Folgeband
  URL:       https://www.umweltbundesamt.at/umweltthemen/naturschutz/
             rotelisten/biotoptypen
  Teilbände: M-155 Konzept (2002), M-156 Wälder (2002), M-167 Grünland
             (2004), M-174 Moore/Hochgebirge/Äcker (2005), Binnengewässer
             und Siedlungsbiotope (2008)
  Abgerufen: 24.08.2026

WAS DIESER ABSCHNITT NEBEN DEM ROTE-LISTEN-ABSCHNITT SOLL:
Der andere zeigt, wie ALT das Wissen über gefährdete Tiere ist. Dieser
zeigt, was das Wissen über Lebensräume SAGT. Die beiden gehören zusammen
und dürfen nicht verwechselt werden — hier geht es um Biotoptypen, dort um
Tiergruppen.

DREI STELLEN, AN DENEN MAN SICH VERRECHNEN KANN:

1. 488 Biotoptypen gibt es, aber nur 383 wurden BEWERTET. Die übrigen 105
   galten als nicht besonders schutzwürdig und bekamen gar keine Kategorie.
   Prozentangaben beziehen sich immer auf die 383, nie auf die 488.

2. Die belegten Kategorien ergeben zusammen 377, nicht 383. Sechs
   Biotoptypen ließen sich keiner Kategorie zuordnen — vermutlich NT
   („Vorwarnstufe"), belegen konnte ich das nicht. Sie stehen deshalb als
   „ohne Angabe" da und werden NICHT auf NT umgedeutet.

3. „Gefährdet" im Sinne der Bilanz sind RE, CR, EN und VU zusammen: 284 von
   383, also 74,2 %. Die gerundeten „rund 75 %" der Quelle bestätigen das.
"""

from __future__ import annotations

from gemeinsam import log, pflegepruefung, quelle_vermerken, warnen

STAND_JAHR = 2008          # letzter Teilband
ERSTER_BAND = 2002

BIOTOPTYPEN_GESAMT = 488
BIOTOPTYPEN_BEWERTET = 383

# Reihenfolge von schlecht nach gut — so liest sich der gestapelte Balken
# von links, und die Farbrampe läuft mit.
STUFEN = [
    {"kuerzel": "RE", "name": "völlig vernichtet",   "anzahl": 5,   "gefaehrdet": True},
    {"kuerzel": "CR", "name": "von Vernichtung bedroht", "anzahl": 33, "gefaehrdet": True},
    {"kuerzel": "EN", "name": "stark gefährdet",     "anzahl": 123, "gefaehrdet": True},
    {"kuerzel": "VU", "name": "gefährdet",           "anzahl": 123, "gefaehrdet": True},
    {"kuerzel": "LC", "name": "nicht gefährdet",     "anzahl": 93,  "gefaehrdet": False},
]

TEILBAENDE = [
    {"band": "M-155", "jahr": 2002, "inhalt": "Konzept"},
    {"band": "M-156", "jahr": 2002, "inhalt": "Wälder, Forste, Vorwälder"},
    {"band": "M-167", "jahr": 2004, "inhalt": "Grünland, Trockenrasen, Gehölze"},
    {"band": "M-174", "jahr": 2005, "inhalt": "Moore, Hochgebirge, Äcker, Heiden"},
    {"band": "—",     "jahr": 2008, "inhalt": "Binnengewässer, Siedlungsbiotope"},
]


def baue_biotoptypen() -> dict:
    log("\n[6/8] Biotoptypen — Rote Liste (gepflegt)")

    belegt = sum(s["anzahl"] for s in STUFEN)
    ohne_angabe = BIOTOPTYPEN_BEWERTET - belegt
    if ohne_angabe < 0:
        warnen(
            f"Biotoptypen: die Kategorien summieren sich auf {belegt} und damit "
            f"über die {BIOTOPTYPEN_BEWERTET} bewerteten Typen hinaus — "
            f"eine Zahl ist falsch abgeschrieben"
        )
        ohne_angabe = 0

    gefaehrdet = sum(s["anzahl"] for s in STUFEN if s["gefaehrdet"])
    anteil = round(gefaehrdet / BIOTOPTYPEN_BEWERTET * 100, 1)

    stufen = [
        {**s, "anteil": round(s["anzahl"] / BIOTOPTYPEN_BEWERTET * 100, 1)}
        for s in STUFEN
    ]
    if ohne_angabe:
        stufen.append({
            "kuerzel": "—", "name": "ohne Angabe", "anzahl": ohne_angabe,
            "gefaehrdet": False,
            "anteil": round(ohne_angabe / BIOTOPTYPEN_BEWERTET * 100, 1),
        })

    log(f"    {BIOTOPTYPEN_BEWERTET} von {BIOTOPTYPEN_GESAMT} Biotoptypen bewertet")
    log(f"    Gefährdet (RE+CR+EN+VU): {gefaehrdet} = {anteil} %")
    log(f"    Ohne Angabe: {ohne_angabe}")
    pflegepruefung("biotoptypen", STAND_JAHR, "Rote Liste Biotoptypen")

    quelle_vermerken(
        name="Umweltbundesamt — Rote Liste gefährdeter Biotoptypen Österreichs",
        url=("https://www.umweltbundesamt.at/umweltthemen/naturschutz/"
             "rotelisten/biotoptypen"),
        lizenz="siehe Publikation",
        stand=f"{ERSTER_BAND}–{STAND_JAHR}",
        art="gepflegt",
    )

    return {
        "stufen": stufen,
        "gesamt": BIOTOPTYPEN_GESAMT,
        "bewertet": BIOTOPTYPEN_BEWERTET,
        "nicht_bewertet": BIOTOPTYPEN_GESAMT - BIOTOPTYPEN_BEWERTET,
        "gefaehrdet": gefaehrdet,
        "anteil_gefaehrdet": anteil,
        "vernichtet": STUFEN[0]["anzahl"],
        "ohne_angabe": ohne_angabe,
        "teilbaende": TEILBAENDE,
        "stand": STAND_JAHR,
        "erster_band": ERSTER_BAND,
        "pflege": {
            "art": "gepflegt",
            "quelle": ("Umweltbundesamt: Rote Listen gefährdeter Biotoptypen "
                       "Österreichs, Teilbände M-155 bis M-174 (2002–2008)."),
            "bericht_jahr": STAND_JAHR,
            "abgerufen": "2026-08-24",
        },
        "hinweis": (
            f"Von {BIOTOPTYPEN_GESAMT} Biotoptypen wurden {BIOTOPTYPEN_BEWERTET} "
            f"als schutzwürdig eingestuft und bewertet; alle Anteile beziehen "
            f"sich auf diese {BIOTOPTYPEN_BEWERTET}. Die Teilbände erschienen "
            f"zwischen {ERSTER_BAND} und {STAND_JAHR} — eine Neuauflage steht aus."
        ),
    }
