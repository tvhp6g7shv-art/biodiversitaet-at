"""
Pestizidabsatz Österreich — Eurostat aei_fm_salpest09.

Was die Reihe misst: die in Verkehr gebrachte Menge Wirkstoff in Kilogramm,
nicht die ausgebrachte und nicht ihre Wirkung. Ein Kilogramm Schwefel und ein
Kilogramm eines synthetischen Wirkstoffs wiegen hier gleich viel.

DER ANSTIEG UND DER NAHELIEGENDE EINWAND. Der Absatz liegt 2024 rund die
Hälfte über 2011. Der erste Einwand dagegen lautet: Das seien vor allem
anorganische Fungizide — Schwefel und Kupfer, die schwer wiegen und auch im
Biolandbau zugelassen sind. Deshalb teilt dieses Modul den Absatz auf und
zeigt beide Teile im Bild, statt den Einwand in einer Fußnote abzuräumen.

**Die Planungsakte lag hier falsch, am 04.09.2026 korrigiert.** Sie hielt
fest, der Anteil der anorganischen Mittel *sinke* (24,8 % → 19,5 %) und der
Anstieg liege im synthetischen Rest. Das gilt nur, wenn man „anorganisch" als
Kupfer PLUS Schwefel liest. Nimmt man die Gruppe, die Eurostat selbst so
nennt — `F01`, anorganische Fungizide —, dreht sich der Befund:

    Gesamtabsatz   3.448 t (2011) → 5.232 t (2024)   +51,7 %
    davon F01        750 t        → 1.362 t          +81,5 %
    Rest           2.698 t        → 3.870 t          +43,5 %
    Anteil F01      21,8 %        → 26,0 %           steigt

Der Unterschied zwischen beiden Lesarten ist eine einzige Unterkategorie:
`F01_99`, sonstige anorganische Fungizide, **28 t (2012) → 341 t (2024)**,
also das Zwölffache. Kupfer und Schwefel allein verlieren tatsächlich Anteil;
die Gruppe als Ganzes gewinnt ihn.

KEINE ZIELMARKE. Das oft zitierte EU-Ziel „−50 % bis 2030" gehört zur
Farm-to-Fork-Strategie und misst **Einsatz und Risiko** über einen
gewichteten Indikator, nicht den Absatz in Kilogramm. Die Verordnung, die es
verbindlich gemacht hätte, ist 2023 im Parlament gescheitert und danach
zurückgezogen worden. Eine Marke bei −50 % neben dieser Kurve wäre deshalb
zweimal falsch: falscher Maßstab und kein geltendes Ziel.

LÜCKE 2015: Für die Aufteilung ist 2015 vertraulich. Der Gesamtwert ist da,
die beiden Teile fehlen. Das Bild lässt die Lücke stehen, statt sie zu
überbrücken.
"""

from __future__ import annotations

import config
from gemeinsam import jsonstat_reihe, lade_json, log, quelle_vermerken, warnen


def _reihe(code: str, name: str) -> dict[str, float]:
    url = f"{config.EUROSTAT_BASIS}/{config.PESTIZID_CODE}"
    params = dict(config.PESTIZID_PARAMS, pesticid=code)
    return jsonstat_reihe(lade_json(url, params), f"aei_fm_salpest09 ({name})")


def baue_pestizide() -> dict | None:
    log("\n[21/21] Pestizidabsatz — Eurostat aei_fm_salpest09")

    gesamt = _reihe(config.PESTIZID_GESAMT, "Insgesamt")
    if not gesamt:
        warnen("Pestizide: keine Gesamtreihe — Abschnitt bleibt ausgeblendet")
        return None

    anorg = _reihe(config.PESTIZID_ANORGANISCH, "anorganische Fungizide")

    jahre = sorted(gesamt)
    erstes, letztes = jahre[0], jahre[-1]

    # --- Gegenprobe 1: keine Lücke in der Gesamtreihe ----------------------
    # Der Abschnitt behauptet einen Verlauf. Fehlt darin ein Jahr, ist die
    # Linie eine Interpolation, die niemand angekündigt hat.
    luecken = [str(j) for j in range(int(erstes), int(letztes) + 1) if str(j) not in gesamt]
    if luecken:
        warnen(
            f"Pestizide: Gesamtreihe hat Lücken bei {', '.join(luecken)} — "
            f"der Verlauf wäre keine durchgehende Messung"
        )
        return None

    # --- Gegenprobe 2: der Teil ist nie größer als das Ganze ---------------
    zu_gross = [j for j in anorg if j in gesamt and anorg[j] > gesamt[j]]
    if zu_gross:
        warnen(
            f"Pestizide: anorganische Fungizide übersteigen den Gesamtabsatz "
            f"({', '.join(sorted(zu_gross))}) — die Codes passen nicht zueinander"
        )
        return None

    # --- Gegenprobe 3: die drei Unterkategorien ergeben die Gruppe ---------
    # Kupfer + Schwefel + Sonstige müssen F01 auf das Kilogramm treffen. Das
    # prüft, dass `F01` wirklich die Obergruppe ist und nicht eine vierte,
    # gleichnamige Kategorie — und es ist die Rechnung, auf der die
    # Korrektur an der Planungsakte beruht.
    teile = {
        name: _reihe(code, name)
        for name, code in config.PESTIZID_TEILE.items()
    }
    abweichung = []
    for j in sorted(anorg):
        if all(j in t for t in teile.values()):
            summe = sum(t[j] for t in teile.values())
            if abs(summe - anorg[j]) > 1:
                abweichung.append(f"{j}: {summe:.0f} statt {anorg[j]:.0f}")
    if abweichung:
        warnen(
            "Pestizide: Unterkategorien summieren nicht auf F01 — "
            + "; ".join(abweichung[:3])
        )
        return None

    punkte = [
        {
            "jahr": int(j),
            "gesamt": round(gesamt[j] / 1000),
            "anorganisch": round(anorg[j] / 1000) if j in anorg else None,
            "rest": round((gesamt[j] - anorg[j]) / 1000) if j in anorg else None,
            "anteil": round(anorg[j] / gesamt[j] * 100, 1) if j in anorg else None,
        }
        for j in jahre
    ]

    ohne_teilung = [p["jahr"] for p in punkte if p["anorganisch"] is None]

    def wachstum(a: float, b: float) -> float:
        return round((b / a - 1) * 100, 1)

    hoch_jahr = max(gesamt, key=lambda j: gesamt[j])
    seit_hoch = wachstum(gesamt[hoch_jahr], gesamt[letztes])

    basis_jahre = [j for j in config.PESTIZID_BASISPERIODE if j in gesamt]
    basis = sum(gesamt[j] for j in basis_jahre) / len(basis_jahre) if basis_jahre else None

    hat_teilung = anorg and erstes in anorg and letztes in anorg
    w_gesamt = wachstum(gesamt[erstes], gesamt[letztes])
    w_anorg = wachstum(anorg[erstes], anorg[letztes]) if hat_teilung else None
    w_rest = (wachstum(gesamt[erstes] - anorg[erstes], gesamt[letztes] - anorg[letztes])
              if hat_teilung else None)

    # --- Gegenprobe 4: trägt der Satz, den die Notiz schreiben wird? -------
    # Die Notiz sagt, welcher Teil schneller wächst. Diese Aussage wird hier
    # aus den Zahlen abgeleitet und nicht im Frontend behauptet — sonst
    # überlebt sie den nächsten Jahrgang, in dem sie vielleicht falsch ist.
    schneller = None
    if hat_teilung:
        schneller = "anorganisch" if w_anorg > w_rest else "rest"

    log(f"    {erstes}: {gesamt[erstes]/1000:,.0f} t  →  {letztes}: "
        f"{gesamt[letztes]/1000:,.0f} t  ({w_gesamt:+.1f} %)")
    if hat_teilung:
        log(f"    davon anorganische Fungizide {w_anorg:+.1f} %, Rest {w_rest:+.1f} % "
            f"— schneller wächst: {schneller}")
    log(f"    Höhepunkt {hoch_jahr} ({gesamt[hoch_jahr]/1000:,.0f} t), seither {seit_hoch:+.1f} %")
    if ohne_teilung:
        log(f"    ohne Aufteilung (vertraulich): {ohne_teilung}")

    quelle_vermerken(
        name="Eurostat — aei_fm_salpest09, Absatz von Pflanzenschutzmitteln",
        url="https://ec.europa.eu/eurostat/databrowser/view/aei_fm_salpest09",
        lizenz="Eurostat-Nutzungsbedingungen",
        stand=str(letztes),
        art="api",
    )

    return {
        "punkte": punkte,
        "beginn": int(erstes),
        "stand": int(letztes),
        "gesamt_aktuell": round(gesamt[letztes] / 1000),
        "gesamt_beginn": round(gesamt[erstes] / 1000),
        "wachstum": w_gesamt,
        "wachstum_anorganisch": w_anorg,
        "wachstum_rest": w_rest,
        "schneller": schneller,
        "anteil_beginn": round(anorg[erstes] / gesamt[erstes] * 100, 1) if hat_teilung else None,
        "anteil_aktuell": round(anorg[letztes] / gesamt[letztes] * 100, 1) if hat_teilung else None,
        "hoehepunkt_jahr": int(hoch_jahr),
        "hoehepunkt": round(gesamt[hoch_jahr] / 1000),
        "seit_hoehepunkt": seit_hoch,
        "basisperiode": [int(j) for j in basis_jahre],
        "basis_mittel": round(basis / 1000) if basis else None,
        "gegen_basis": wachstum(basis, gesamt[letztes]) if basis else None,
        "ohne_teilung": ohne_teilung,
        "kachel_wert": w_gesamt,
        "hinweis": (
            "Gemessen wird die in Verkehr gebrachte Menge Wirkstoff, nicht die "
            "ausgebrachte und nicht ihre Wirkung: Ein Kilogramm Schwefel wiegt hier "
            "so viel wie ein Kilogramm eines synthetischen Mittels."
        ),
    }
