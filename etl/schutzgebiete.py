"""
Terrestrische Schutzgebietsfläche Österreichs — Eurostat sdg_15_20.

Die einzige Reihe des Dashboards, die bei jedem Lauf frisch aus einer API
kommt. Sie umfasst national ausgewiesene Schutzgebiete UND Natura-2000-
Gebiete; Überschneidungen hat die EEA herausgerechnet.

Was die Zahl NICHT sagt: wie streng geschützt wird. Ein Landschaftsschutz-
gebiet zählt genauso wie eine Nationalpark-Kernzone. Der Hinweistext im
Dashboard muss das tragen, sonst liest sich „29,3 % geschützt" als
Entwarnung.
"""

from __future__ import annotations

import config
from gemeinsam import jsonstat_reihe, lade_json, log, quelle_vermerken, warnen


def baue_schutzgebiete() -> dict | None:
    log("\n[1/11] Schutzgebiete — Eurostat sdg_15_20")

    url = f"{config.EUROSTAT_BASIS}/{config.SCHUTZGEBIETE_CODE}"
    prozent = jsonstat_reihe(
        lade_json(url, config.SCHUTZGEBIETE_PARAMS), "sdg_15_20 (Prozent)"
    )
    if not prozent:
        warnen("Schutzgebiete: keine Prozentwerte — Abschnitt bleibt ausgeblendet")
        return None

    km2 = jsonstat_reihe(
        lade_json(url, config.SCHUTZGEBIETE_PARAMS_KM2), "sdg_15_20 (km²)"
    )

    jahre = sorted(prozent)
    letztes = jahre[-1]
    erstes = jahre[0]

    punkte = [
        {
            "jahr": int(jahr),
            "prozent": round(prozent[jahr], 1),
            "km2": round(km2[jahr]) if jahr in km2 else None,
        }
        for jahr in jahre
    ]

    # Wie lange steht die Kurve schon still? Das ist der eigentliche Befund:
    # nicht der Stand, sondern die Bewegungslosigkeit davor. Gerundet
    # vergleichen, weil die Quelle selbst auf eine Nachkommastelle rundet —
    # sonst erzeugt eine Differenz von 0,04 Punkten eine Scheinbewegung.
    aktuell = round(prozent[letztes], 1)
    stillstand_seit = letztes
    for jahr in reversed(jahre[:-1]):
        if round(prozent[jahr], 1) != aktuell:
            break
        stillstand_seit = jahr
    jahre_still = int(letztes) - int(stillstand_seit)

    # 11.09.2026 — Entscheid E6: Die Zielmarke bleibt im Bild, die daraus
    # abgeleitete *nationale* Lücke fällt weg. Das Ziel von 30 Prozent gilt
    # der EU als Ganzes; eine Fehlmenge für Österreich dagegen zu rechnen
    # unterstellt eine nationale Verpflichtung, die es nicht gibt. Mit
    # `luecke_km2` fällt auch der Dreisatz weg, der die Landesfläche aus
    # Fläche und Prozent zurückrechnete — eine aus gerundeten Werten
    # zurückgerechnete Größe ist keine Quelle.

    log(f"    {erstes}: {prozent[erstes]:.1f} %  →  {letztes}: {aktuell:.1f} %")
    if jahre_still:
        log(f"    Unverändert seit {stillstand_seit} ({jahre_still} Jahre)")
    log(f"    EU-weites Ziel {config.SCHUTZGEBIETE_ZIELJAHR}: {config.SCHUTZGEBIETE_ZIEL:.0f} %")

    quelle_vermerken(
        name="Eurostat — sdg_15_20, Surface of the terrestrial protected areas",
        url="https://ec.europa.eu/eurostat/databrowser/view/sdg_15_20",
        lizenz="Eurostat-Nutzungsbedingungen",
        stand=str(letztes),
        art="api",
    )

    return {
        "punkte": punkte,
        "aktuell": aktuell,
        "aktuell_km2": km2.get(letztes) and round(km2[letztes]),
        "stand": int(letztes),
        "beginn": int(erstes),
        "stillstand_seit": int(stillstand_seit),
        "jahre_still": jahre_still,
        "ziel": config.SCHUTZGEBIETE_ZIEL,
        "zieljahr": config.SCHUTZGEBIETE_ZIELJAHR,
        "hinweis": (
            "Nationale Schutzgebiete und Natura-2000-Gebiete zusammen, "
            "Überschneidungen herausgerechnet. Gemessen wird Fläche, nicht "
            "Schutzintensität. Das Ziel von 30 Prozent gilt der EU als Ganzes, "
            "nicht jedem Mitgliedstaat."
        ),
    }
