"""
Grünland- und Waldfläche Österreichs — Eurostat lan_lcv_ovw (LUCAS).

WAS DIE REIHE MISST: LUCAS ist eine Flächenstichprobe. Feldbeobachter stehen
an gezogenen Punkten im Gelände und tragen ein, was dort wächst. Hochgerechnet
ergibt das eine Flächenschätzung — keine Vollerhebung, kein Kataster. Fünf
Stützstellen: 2009, 2012, 2015, 2018, 2022.

WARUM LUCAS UND NICHT DIE AGRARSTRUKTURERHEBUNG. `apro_cpsh1` (Dauergrünland)
wäre die naheliegende Quelle und ist unbrauchbar: Sie ist blockweise
fortgeschrieben — 2000 bis 2004 steht fünfmal derselbe Wert — und zwischen
2010 und 2011 liegt ein Definitionsbruch von rund 290.000 Hektar. Das steht
in der Liste der verworfenen Quellen; nicht neu recherchieren.

DER PREIS DER STICHPROBE, und warum er ins Bild gehört: Eurostat liefert zu
jedem Wert einen Variationskoeffizienten mit. Für das österreichische Grünland
liegt er bei 1,5 bis 3,7 Prozent. Der gemessene Rückgang ist größer als dieser
Fehler — aber nicht um ein Vielfaches. Deshalb rechnet dieses Modul die
Spanne aus und schreibt sie in die Hinweiszeile, statt eine Stichprobe wie
eine Zählung aussehen zu lassen.

DIE ZWEITE REIHE IST KEINE ZUGABE. Grünland und Wald laufen gegeneinander:
−1.562 km² hier, +2.278 km² dort. Ohne die zweite Linie liest sich der
Rückgang als allgemeiner Flächenverlust. Mit ihr ist zu sehen, dass Fläche
nicht verschwindet, sondern die Nutzung wechselt. Es ist ausdrücklich KEINE
Bilanz: Die beiden Kategorien tauschen nicht direkt untereinander, dazwischen
liegen Acker, Siedlung und Verkehrsfläche. Der Text sagt das.

WARUM DAS BILD VERÄNDERUNGEN ZEIGT UND NICHT QUADRATKILOMETER. In absoluten
Werten über eine Nullachse wäre ein Rückgang von 7,3 Prozent über dreizehn
Jahre eine fast waagrechte Linie — die Überschrift behauptete dann etwas, das
im Bild nicht als Länge vorkommt. Genau daran ist am 07.09.2026 die
Schutzstufen-Grafik zweimal gescheitert. Die absoluten Werte stehen in
Tooltip und Tabelle, wo sie nachzulesen und nicht zu vergleichen sind.
"""

from __future__ import annotations

import config
from gemeinsam import jsonstat_reihe, lade_json, log, quelle_vermerken, warnen


def _komma(wert: float | None) -> str:
    """Deutsche Schreibweise für die Hinweiszeile — sie geht als fertiger
    Text ins Frontend und läuft dort an keinem Zahlenformatierer mehr vorbei."""
    return "–" if wert is None else f"{wert:.1f}".replace(".", ",")


def _flaeche(code: str, name: str) -> dict[str, dict[str, float]]:
    """Die drei Einheiten einer Bodenbedeckung aus EINEM Download.

    Die Antwort hat zwei mehrfach besetzte Dimensionen — `unit` mit drei
    Kategorien und `time` mit fünf. Wer hier nach laufender Nummer zuordnet,
    liest die Variationskoeffizienten als Flächen. `jsonstat_reihe` filtert
    deshalb je Einheit und bricht ab, wenn mehr als eine Reihe übrig bleibt.
    """
    roh = lade_json(f"{config.EUROSTAT_BASIS}/{config.LANDNUTZUNG_CODE}",
                    dict(config.LANDNUTZUNG_PARAMS, landcover=code))
    return {
        einheit: jsonstat_reihe(roh, f"lan_lcv_ovw ({name}, {einheit})", unit=einheit)
        for einheit in ("KM2", "CVA", "PC")
    }


def baue_gruenland() -> dict | None:
    log("\n[22/22] Grünland- und Waldfläche — Eurostat lan_lcv_ovw (LUCAS)")

    gruen = _flaeche(config.LANDNUTZUNG_GRUENLAND, "Grünland")
    wald = _flaeche(config.LANDNUTZUNG_WALD, "Wald")

    if not gruen["KM2"] or not wald["KM2"]:
        warnen("Grünland: keine Flächenreihe — Abschnitt bleibt ausgeblendet")
        return None

    # --- Gegenprobe 1: beide Reihen stehen auf denselben Stützjahren -------
    # LUCAS erhebt beide Kategorien im selben Durchgang. Fehlt einer Reihe
    # ein Jahr, liefe die eine Linie über einen Punkt, den die andere nicht
    # hat — die Schere im Bild wäre dann ein Artefakt der Lücke.
    jahre = sorted(set(gruen["KM2"]) & set(wald["KM2"]))
    fehlend = sorted((set(gruen["KM2"]) | set(wald["KM2"])) - set(jahre))
    if fehlend:
        warnen(
            f"Grünland: {', '.join(fehlend)} steht nur in einer der beiden Reihen — "
            f"die Jahre werden übergangen"
        )
    if len(jahre) < config.LANDNUTZUNG_MIN_PUNKTE:
        warnen(
            f"Grünland: nur {len(jahre)} gemeinsame Stützjahre, mindestens "
            f"{config.LANDNUTZUNG_MIN_PUNKTE} erwartet — kein Verlauf"
        )
        return None

    erstes, letztes = jahre[0], jahre[-1]

    # --- Gegenprobe 2: Fläche und Anteil gehören zusammen -----------------
    # Aus km² und Prozent lässt sich die Landesfläche zurückrechnen. Sie muss
    # für beide Kategorien und über alle Jahre dieselbe sein. Weicht sie ab,
    # beziehen sich die beiden Einheiten auf verschiedene Nenner — dann wäre
    # jede Aussage über Anteile falsch, ohne dass man es dem Bild ansieht.
    hochgerechnet = []
    for reihe in (gruen, wald):
        for j in jahre:
            if j in reihe["PC"] and reihe["PC"][j]:
                hochgerechnet.append(reihe["KM2"][j] / reihe["PC"][j] * 100)
    if hochgerechnet:
        spanne = (max(hochgerechnet) - min(hochgerechnet)) / min(hochgerechnet) * 100
        if spanne > config.LANDNUTZUNG_NENNER_TOLERANZ:
            warnen(
                f"Grünland: aus km² und Prozent ergeben sich Landesflächen zwischen "
                f"{min(hochgerechnet):,.0f} und {max(hochgerechnet):,.0f} km² "
                f"({spanne:.1f} % Streuung) — die beiden Einheiten teilen keinen Nenner"
            )
            return None
        log(f"    Landesfläche aus km²/Prozent: {sum(hochgerechnet)/len(hochgerechnet):,.0f} km² "
            f"(Streuung {spanne:.2f} %)")

    def wachstum(a: float, b: float) -> float:
        return round((b / a - 1) * 100, 1)

    ver_gruen = wachstum(gruen["KM2"][erstes], gruen["KM2"][letztes])
    ver_wald = wachstum(wald["KM2"][erstes], wald["KM2"][letztes])

    # --- Gegenprobe 3: trägt der Rückgang gegen die Stichprobe? -----------
    # Der Variationskoeffizient gilt je Einzelschätzung. Für die DIFFERENZ
    # zweier unabhängiger Schätzungen addieren sich die relativen Fehler
    # quadratisch. Ist die gemessene Veränderung nicht deutlich größer als
    # dieser kombinierte Fehler, ist sie keine Aussage, sondern Rauschen —
    # und dann darf sie nicht in der Überschrift stehen.
    def belastbar(reihe: dict[str, dict[str, float]], ver: float, was: str) -> bool:
        cv_a, cv_b = reihe["CVA"].get(erstes), reihe["CVA"].get(letztes)
        if cv_a is None or cv_b is None:
            warnen(f"{was}: kein Variationskoeffizient für {erstes} oder {letztes} — "
                   f"die Belastbarkeit ist nicht prüfbar")
            return True
        kombiniert = (cv_a ** 2 + cv_b ** 2) ** 0.5
        faktor = abs(ver) / kombiniert if kombiniert else 0
        log(f"    {was}: {ver:+.1f} % gegen kombinierten Stichprobenfehler "
            f"{kombiniert:.1f} % — Faktor {faktor:.1f}")
        if faktor < config.LANDNUTZUNG_MIN_FAKTOR:
            warnen(
                f"{was}: Die Veränderung von {ver:+.1f} % liegt nur um den Faktor "
                f"{faktor:.1f} über dem Stichprobenfehler von {kombiniert:.1f} % — "
                f"das trägt keine Überschrift"
            )
            return False
        return True

    if not belastbar(gruen, ver_gruen, "Grünland"):
        return None
    belastbar(wald, ver_wald, "Wald")

    punkte = [
        {
            "jahr": int(j),
            "gruenland_km2": round(gruen["KM2"][j]),
            "gruenland_pc": gruen["PC"].get(j),
            "gruenland_cv": gruen["CVA"].get(j),
            "gruenland_ver": wachstum(gruen["KM2"][erstes], gruen["KM2"][j]),
            "wald_km2": round(wald["KM2"][j]),
            "wald_pc": wald["PC"].get(j),
            "wald_cv": wald["CVA"].get(j),
            "wald_ver": wachstum(wald["KM2"][erstes], wald["KM2"][j]),
        }
        for j in jahre
    ]

    cvs = [p["gruenland_cv"] for p in punkte if p["gruenland_cv"] is not None]
    cv_min, cv_max = (min(cvs), max(cvs)) if cvs else (None, None)

    verlust_km2 = round(gruen["KM2"][erstes] - gruen["KM2"][letztes])
    zuwachs_km2 = round(wald["KM2"][letztes] - wald["KM2"][erstes])

    log(f"    Grünland {erstes}: {gruen['KM2'][erstes]:,.0f} km²  →  {letztes}: "
        f"{gruen['KM2'][letztes]:,.0f} km²  ({ver_gruen:+.1f} %)")
    log(f"    Wald     {erstes}: {wald['KM2'][erstes]:,.0f} km²  →  {letztes}: "
        f"{wald['KM2'][letztes]:,.0f} km²  ({ver_wald:+.1f} %)")
    log(f"    Anteil Grünland {gruen['PC'][erstes]} % → {gruen['PC'][letztes]} %")

    quelle_vermerken(
        name="Eurostat — lan_lcv_ovw, Bodenbedeckung nach LUCAS-Flächenstichprobe",
        url="https://ec.europa.eu/eurostat/databrowser/view/lan_lcv_ovw",
        lizenz="Eurostat-Nutzungsbedingungen",
        stand=str(letztes),
        art="api",
    )

    return {
        "punkte": punkte,
        "beginn": int(erstes),
        "stand": int(letztes),
        "gruenland_beginn": round(gruen["KM2"][erstes]),
        "gruenland_aktuell": round(gruen["KM2"][letztes]),
        "gruenland_veraenderung": ver_gruen,
        "gruenland_anteil_beginn": gruen["PC"].get(erstes),
        "gruenland_anteil_aktuell": gruen["PC"].get(letztes),
        "verlust_km2": verlust_km2,
        "wald_beginn": round(wald["KM2"][erstes]),
        "wald_aktuell": round(wald["KM2"][letztes]),
        "wald_veraenderung": ver_wald,
        "wald_anteil_aktuell": wald["PC"].get(letztes),
        "zuwachs_km2": zuwachs_km2,
        "cv_min": cv_min,
        "cv_max": cv_max,
        "kachel_wert": ver_gruen,
        # Die Hinweiszeile wird gegen 150–234 Zeichen geprüft. Die beiden
        # Fehlerwerte kommen aus den Daten, deshalb steht die Länge nicht
        # fest — sie schwankt um zwei Zeichen, wenn eine Nachkommastelle
        # wegfällt. Das bleibt innerhalb der Spanne.
        "hinweis": (
            f"LUCAS ist eine Stichprobe, keine Vollerhebung: Beobachter tragen an "
            f"gezogenen Punkten im Gelände ein, was dort wächst. Der Stichprobenfehler "
            f"liegt je Jahr zwischen {_komma(cv_min)} und {_komma(cv_max)} Prozent — "
            f"kleiner als der Rückgang."
        ),
    }
