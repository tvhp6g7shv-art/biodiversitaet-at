"""
Stickstoffüberschuss der Landwirtschaft — Eurostat aei_pr_gnb.

Was die Reihe misst: die Bruttonährstoffbilanz Stickstoff je Hektar
landwirtschaftlich genutzter Fläche, in Kilogramm. Zugeführt wird über
Mineral- und Wirtschaftsdünger, Saatgut, Deposition und biologische
Stickstoffbindung; abgeführt über Ernte, Futter und Ernterückstände. Was
übrig bleibt, ist der Überschuss — er geht als Nitrat ins Grundwasser und
als Ammoniak und Lachgas in die Luft. (Am 09.09.2026 an der Indikatorliste
des Datensatzes abgeglichen: Futter steht auf der ABFUHR-Seite, O_FOD.)

WARUM DIESER ABSCHNITT HIER STEHT: Er ist das Gegenstück zum Pestizidabsatz.
Das Dashboard zeigt fast nur Verschlechterungen; ein Bereich, der nur in eine
Richtung zeigt, verliert seine Glaubwürdigkeit. Der Stickstoffüberschuss
sinkt — nur nicht so glatt, wie es die Planung annahm.

DIE RECHNUNG, DIE HIER NICHT STEHT. Naheliegend wäre: 34,1 kg (2023) gegen
49,4 kg (1985), also −31 Prozent. Sie hängt an zwei Einzeljahren in einer
Reihe, die zwischen 22,9 (2004) und 51,1 kg (1992 und 2000) schwankt —
Witterung, Erntejahr, Düngerpreis. Ein anderes Startjahr ergibt eine andere
Zahl. Verglichen werden deshalb Fünfjahresmittel: 43,8 kg (1985–89) gegen
35,4 kg (2019–23), also −19,2 Prozent. Entscheid des Users am 09.09.2026;
der Einzeljahreswert wird trotzdem mitgerechnet und geloggt, damit der
Unterschied zwischen beiden Lesarten sichtbar bleibt.

UND DER RÜCKGANG IST NICHT DURCHGEHEND — er hat drei Abschnitte. Das
gleitende Fünfjahresmittel fällt bis zum Fenster 2004–2008 auf 29,6 kg,
steigt danach bis zum Fenster 2015–2019 auf 40,4 kg und steht heute bei
35,4 kg. „Seither steigt er wieder" wäre also genauso falsch wie „er sinkt
stetig"; das Modul sucht den Wiederanstieg deshalb in den Daten, statt ihn
zu behaupten. Ohne diesen Satz behauptet das Bild eine stetige Verbesserung,
die die Daten nicht hergeben.

DATENSTAND: Eurostat hat die Reihe am 08.09.2026, 23:00 aktualisiert. Sie hat
seither 39 lückenlose Stützstellen 1985–2023. Die Planungsakte vom 07.09.2026
nannte 37 Stützstellen mit einer Lücke bei 2020 und 2021, 51 kg für 1985 und
einen Höchstwert von 57 kg für 1992. Das war der vorige Jahrgang und ist
überholt — am 09.09.2026 an der API nachgemessen (39 Werte, Summe 1.502,4).

KEIN EU-VERGLEICH: Die EU-27-Reihe endet in diesem Datensatz 2014, alle ihre
Werte sind als „geschätzt" gekennzeichnet; 2015 bis 2023 stehen dort in
`positions-with-no-data`. Ein Vergleich „Österreich gegen EU" wäre nur über
eine eigene Länderaggregation zu haben und bleibt deshalb draußen.

KEINE ZIELMARKE: Für den Stickstoffüberschuss je Hektar gibt es keinen
verbindlichen österreichischen oder EU-Zielwert. Die Nitratrichtlinie regelt
Ausbringungsmengen und Grundwassergehalte, nicht die Bilanz. Eine Marke im
Bild wäre erfunden.
"""

from __future__ import annotations

import config
from gemeinsam import jsonstat_reihe, lade_json, log, quelle_vermerken, warnen


def _mittel(werte: list[float]) -> float:
    return sum(werte) / len(werte)


def _stdabw(werte: list[float]) -> float:
    """Stichproben-Standardabweichung; für n < 2 nicht definiert."""
    if len(werte) < 2:
        return 0.0
    m = _mittel(werte)
    return (sum((w - m) ** 2 for w in werte) / (len(werte) - 1)) ** 0.5


def baue_stickstoff() -> dict | None:
    log("\n[23/23] Stickstoffüberschuss — Eurostat aei_pr_gnb")

    reihe = jsonstat_reihe(
        lade_json(f"{config.EUROSTAT_BASIS}/{config.STICKSTOFF_CODE}",
                  config.STICKSTOFF_PARAMS),
        "aei_pr_gnb (Bruttostickstoffbilanz je Hektar)",
    )
    if not reihe:
        warnen("Stickstoff: keine Reihe — Abschnitt bleibt ausgeblendet")
        return None

    jahre = sorted(reihe)
    erstes, letztes = jahre[0], jahre[-1]
    fenster = config.STICKSTOFF_FENSTER

    # --- Gegenprobe 1: keine Lücke ----------------------------------------
    # Der Abschnitt zeichnet ein gleitendes Mittel. Fehlt ein Jahr, mittelt
    # das Fenster über einen Sprung hinweg, ohne dass man es dem Bild ansieht.
    luecken = [str(j) for j in range(int(erstes), int(letztes) + 1)
               if str(j) not in reihe]
    if luecken:
        warnen(
            f"Stickstoff: Lücken bei {', '.join(luecken)} — ein gleitendes "
            f"Mittel darüber wäre eine Interpolation, die niemand angekündigt hat"
        )
        return None

    # --- Gegenprobe 2: zwei volle Fenster ---------------------------------
    if len(jahre) < 2 * fenster:
        warnen(
            f"Stickstoff: nur {len(jahre)} Jahre, für zwei {fenster}-Jahres-Fenster "
            f"braucht es {2 * fenster} — der Vergleich trägt nicht"
        )
        return None

    frueh_jahre = jahre[:fenster]
    spaet_jahre = jahre[-fenster:]
    frueh = [reihe[j] for j in frueh_jahre]
    spaet = [reihe[j] for j in spaet_jahre]
    m_frueh, m_spaet = _mittel(frueh), _mittel(spaet)

    # --- Gegenprobe 3: trägt der Unterschied gegen die Schwankung? --------
    # Die Reihe schwankt stark von Jahr zu Jahr. Der Unterschied zweier
    # Fünfjahresmittel muss deutlich größer sein als der Standardfehler
    # dieser Mittel, sonst ist er Witterung und keine Entwicklung — und
    # dann darf er nicht in der Überschrift stehen.
    standardfehler = (_stdabw(frueh) ** 2 / fenster
                      + _stdabw(spaet) ** 2 / fenster) ** 0.5
    differenz = m_frueh - m_spaet
    faktor = abs(differenz) / standardfehler if standardfehler else 0.0
    log(f"    {frueh_jahre[0]}–{frueh_jahre[-1]}: {m_frueh:.1f} kg  →  "
        f"{spaet_jahre[0]}–{spaet_jahre[-1]}: {m_spaet:.1f} kg  "
        f"({differenz:+.1f} kg, Standardfehler {standardfehler:.1f}, "
        f"Faktor {faktor:.1f})")
    if faktor < config.STICKSTOFF_MIN_FAKTOR:
        warnen(
            f"Stickstoff: Der Unterschied von {abs(differenz):.1f} kg liegt nur um "
            f"den Faktor {faktor:.1f} über dem Standardfehler von "
            f"{standardfehler:.1f} kg — das trägt keine Überschrift"
        )
        return None

    # --- Gleitendes Mittel ------------------------------------------------
    gleitend: dict[str, float] = {}
    for i in range(fenster - 1, len(jahre)):
        werte = [reihe[j] for j in jahre[i - fenster + 1:i + 1]]
        gleitend[jahre[i]] = round(_mittel(werte), 1)

    tief_jahr = min(gleitend, key=lambda j: gleitend[j])
    hoch_jahr = max(gleitend, key=lambda j: gleitend[j])

    # Der Verlauf hat DREI Abschnitte, nicht zwei: Abfall bis zum Tief,
    # Wiederanstieg, erneuter Rückgang. Der Wiederanstieg wird eigens
    # gesucht — ein Satz „seither steigt er wieder" wäre am 09.09.2026
    # falsch gewesen, weil das Mittel seit 2019 wieder fällt.
    nach_tief = {j: w for j, w in gleitend.items() if j > tief_jahr}
    zwischenhoch_jahr = max(nach_tief, key=lambda j: nach_tief[j]) if nach_tief else None

    # Der Einzeljahresvergleich wird mitgerechnet, nicht weggelassen: Er ist
    # die Zahl, die man erwartet, und die Notiz erklärt, warum eine andere
    # im Titel steht.
    einzel = round((reihe[letztes] / reihe[erstes] - 1) * 100, 1)
    rueckgang = round((m_spaet / m_frueh - 1) * 100, 1)

    hoechst = max(reihe.values())
    tiefst = min(reihe.values())
    hoechst_jahre = [int(j) for j in jahre if reihe[j] == hoechst]
    tiefst_jahre = [int(j) for j in jahre if reihe[j] == tiefst]

    log(f"    Einzeljahre {erstes} → {letztes}: {reihe[erstes]:.1f} → "
        f"{reihe[letztes]:.1f} kg ({einzel:+.1f} %) — nicht der Titelwert")
    log(f"    gleitendes Mittel: Tief {gleitend[tief_jahr]:.1f} kg "
        f"(Fenster bis {tief_jahr}), Zwischenhoch "
        f"{gleitend[zwischenhoch_jahr]:.1f} kg (bis {zwischenhoch_jahr}), "
        f"heute {gleitend[letztes]:.1f} kg" if zwischenhoch_jahr else
        f"    gleitendes Mittel: Tief {gleitend[tief_jahr]:.1f} kg "
        f"(Fenster bis {tief_jahr}), heute {gleitend[letztes]:.1f} kg")
    log(f"    Spanne der Einzeljahre: {tiefst:.1f} ({tiefst_jahre}) bis "
        f"{hoechst:.1f} ({hoechst_jahre})")

    punkte = [
        {
            "jahr": int(j),
            "wert": reihe[j],
            "mittel": gleitend.get(j),
        }
        for j in jahre
    ]

    quelle_vermerken(
        name="Eurostat — aei_pr_gnb, Bruttonährstoffbilanz je Hektar",
        url="https://ec.europa.eu/eurostat/databrowser/view/aei_pr_gnb",
        lizenz="Eurostat-Nutzungsbedingungen",
        stand=str(letztes),
        art="api",
    )

    return {
        "punkte": punkte,
        "beginn": int(erstes),
        "stand": int(letztes),
        "aktuell": reihe[letztes],
        "fenster": fenster,
        "frueh_von": int(frueh_jahre[0]),
        "frueh_bis": int(frueh_jahre[-1]),
        "spaet_von": int(spaet_jahre[0]),
        "spaet_bis": int(spaet_jahre[-1]),
        "mittel_frueh": round(m_frueh, 1),
        "mittel_spaet": round(m_spaet, 1),
        "differenz": round(differenz, 1),
        "rueckgang": rueckgang,
        "standardfehler": round(standardfehler, 1),
        "faktor": round(faktor, 1),
        "einzeljahr_rueckgang": einzel,
        "hoechstwert": hoechst,
        "hoechstjahre": hoechst_jahre,
        "tiefstwert": tiefst,
        "tiefstjahre": tiefst_jahre,
        "gleitend_tief": gleitend[tief_jahr],
        "gleitend_tief_bis": int(tief_jahr),
        "gleitend_hoch": gleitend[hoch_jahr],
        "gleitend_hoch_bis": int(hoch_jahr),
        "gleitend_zwischenhoch": gleitend[zwischenhoch_jahr] if zwischenhoch_jahr else None,
        "gleitend_zwischenhoch_bis": int(zwischenhoch_jahr) if zwischenhoch_jahr else None,
        "gleitend_aktuell": gleitend[letztes],
        "kachel_wert": rueckgang,
        "hinweis": (
            "Die Bruttobilanz rechnet je Hektar Zufuhr minus Abfuhr: Dünger, "
            "Deposition und Stickstoffbindung gegen Ernte, Futter und "
            "Rückstände. Sie beziffert den Überschuss, der im System bleibt — "
            "nicht, wohin er von dort geht."
        ),
    }
