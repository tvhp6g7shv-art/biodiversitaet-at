"""
Waldfläche Österreichs und seiner Nachbarn — Eurostat for_area (FAO).

ECHTE API. Der einzige geprüfte Biodiversitätsdatensatz, der auch die
Nicht-EU-Nachbarn Schweiz UND Liechtenstein mit Werten führt — bei den
Schutzgebieten (`sdg_15_20`) sind beide zwar als Dimension gelistet, aber
ohne Daten. Wer das übersieht, baut eine Nachbarschaftsgrafik mit zwei
stillen Lücken.

Nur sechs Stützjahre (1990, 2000, 2010, 2015, 2020, 2025), dafür über 35
Jahre. Gezeigt wird die VERÄNDERUNG seit 1990 in Prozent, nicht die
absolute Fläche: Deutschland hat dreimal so viel Wald wie Österreich, das
sagt über die Entwicklung nichts.

WAS DIE ZAHL NICHT SAGT — und der Hinweistext muss es tragen:
Waldfläche ist eine Mengenangabe, kein Zustandsmaß. Eine Fichtenmonokultur
zählt so viel wie ein Auwald. Der eigentliche Biodiversitätsindikator im
Wald ist das Totholz, und dessen Anteil am Holzvorrat liegt in Österreich
laut Waldinventur 2018–2023 bei rund 3 % — abrufbar ist diese Reihe nur
über das interaktive Werkzeug des BFW, nicht über eine Schnittstelle.
"""

from __future__ import annotations

import config
from gemeinsam import (jsonstat_laender, lade_json, laender_namen, log,
                       quelle_vermerken, warnen)

# Anteil des stehenden Totholzes am Holzvorrat, Österreichische Waldinventur
# 2018–2023. Von waldinventur.at abgelesen (24.08.2026); die Reihe selbst
# gibt das Werkzeug nicht als Datei heraus.
TOTHOLZ_ANTEIL = 3.0
TOTHOLZ_PERIODE = "2018–2023"


def baue_wald() -> dict | None:
    log("\n[7/8] Waldfläche — Österreich und Nachbarn (Eurostat for_area)")

    url = f"{config.EUROSTAT_BASIS}/{config.WALD_CODE}"
    roh = lade_json(url, config.WALD_PARAMS)
    laender = jsonstat_laender(roh, "for_area")
    namen = laender_namen(roh)

    if not laender:
        warnen("Waldfläche: keine Werte — Abschnitt bleibt ausgeblendet")
        return None

    # KEIN EU-Aggregat: `for_area` führt ausschließlich einzelne Staaten,
    # eine EU-Summe gibt es in diesem Datensatz nicht (geprüft 24.08.2026).
    # Sie mitanzufordern erzeugte bei jedem Lauf eine Warnung über eine
    # Lücke, die gar keine ist.
    gesucht = list(config.NACHBARN)
    fehlend = [code for code in gesucht if code not in laender]
    if fehlend:
        # Melden statt still weglassen: eine fehlende Zeile in der Grafik
        # sieht aus wie „kein Wald", nicht wie „keine Meldung".
        warnen(
            f"Waldfläche: keine Werte für {', '.join(fehlend)} — "
            f"diese Gebiete fehlen im Vergleich"
        )

    eintraege = []
    for code in gesucht:
        reihe = laender.get(code)
        if not reihe:
            continue
        jahre = sorted(reihe)
        erst, letzt = jahre[0], jahre[-1]
        basis, jetzt = reihe[erst], reihe[letzt]
        if not basis:
            continue
        eintraege.append({
            "code": code,
            "name": namen.get(code, code),
            "von": int(erst),
            "bis": int(letzt),
            "flaeche_von": round(basis, 1),
            "flaeche_bis": round(jetzt, 1),
            "veraenderung": round((jetzt - basis) / basis * 100, 1),
            "hervorgehoben": code == config.HERVORHEBUNG,
            "nur_ein_jahr": len(jahre) < 2,
            "reihe": [{"jahr": int(j), "wert": round(reihe[j], 1)} for j in jahre],
        })

    if not eintraege:
        warnen("Waldfläche: keiner der gesuchten Staaten hat Werte")
        return None

    eintraege.sort(key=lambda e: e["veraenderung"], reverse=True)
    oesterreich = next((e for e in eintraege if e["code"] == "AT"), None)

    if oesterreich:
        rang = eintraege.index(oesterreich) + 1
        log(f"    Österreich: {oesterreich['flaeche_von']:,.0f} → "
            f"{oesterreich['flaeche_bis']:,.0f} Tsd. ha "
            f"({oesterreich['veraenderung']:+.1f} %), Platz {rang} von "
            f"{len(eintraege)}")
    else:
        rang = None
        warnen("Waldfläche: Österreich fehlt in der Antwort")

    quelle_vermerken(
        name="Eurostat — for_area, Waldfläche (Quelle: FAO)",
        url="https://ec.europa.eu/eurostat/databrowser/view/for_area",
        lizenz="Eurostat-Nutzungsbedingungen",
        stand=str(eintraege[0]["bis"]),
        art="api",
    )

    return {
        "eintraege": eintraege,
        "oesterreich": oesterreich,
        "rang": rang,
        "anzahl": len(eintraege),
        "von": eintraege[0]["von"],
        "bis": eintraege[0]["bis"],
        "totholz_anteil": TOTHOLZ_ANTEIL,
        "totholz_periode": TOTHOLZ_PERIODE,
        "hinweis": (
            "Waldfläche ist eine Mengenangabe, kein Zustandsmaß — eine "
            "Fichtenmonokultur zählt so viel wie ein Auwald. Der eigentliche "
            f"Indikator im Wald ist das Totholz; sein Anteil am Holzvorrat "
            f"liegt in Österreich bei rund {TOTHOLZ_ANTEIL:.0f} % "
            f"({TOTHOLZ_PERIODE})."
        ),
    }
