"""
Warum Österreichs Flüsse das Ziel verfehlen — die gemeldeten Belastungen.

WARUM DIESER ABSCHNITT: `fliessgewaesser` zeigt, DASS 4.031 der 8.116
Wasserkörper das Ziel der Wasserrahmenrichtlinie verfehlen. Dieser Abschnitt
zeigt, WAS Österreich in derselben Meldung als Grund dafür angibt — und die
Antwort ist einseitig:

    Hydromorphologie (Verbauung)   3.234 von 4.031   80,2 %
    diffuse Quellen                1.327             32,9 %
    Entnahme                         981             24,3 %
    Punktquellen                      18              0,4 %
    Altlasten                         14
    unbekannt                          9
    ohne genannte Belastung          155

Bei 1.690 Wasserkörpern — 41,9 % aller verfehlenden — ist die Verbauung der
EINZIGE genannte Grund. Das ist die Zahl, die den Abschnitt trägt: Nicht die
Verschmutzung hält Österreichs Flüsse vom guten Zustand ab, sondern die Art,
wie sie verbaut sind.

DER VORBEHALT, DER DIESEN ABSCHNITT ÜBERHAUPT ERST EHRLICH MACHT — und der
groß genug ist, dass er in der Hinweiszeile steht und nicht nur hier:

    Die Wasserrahmenrichtlinie definiert eine „signifikante Belastung" als
    eine, die das Erreichen der Ziele gefährdet. Gemeldet wird sie deshalb
    so gut wie nur für Wasserkörper, die das Ziel verfehlen.

Am 01.09.2026 selbst nachgemessen, nicht aus der Richtlinie abgeleitet: Von
3.879 Wasserkörpern mit einer gemeldeten Belastung erreichen ganze DREI das
Ziel — 0,08 %. Alle drei tragen Punktquellen; unter den 3.234 verbauten ist
kein einziger in gutem Zustand.

DIESE DREI HÄTTEN MICH FAST GEKOSTET. Die erste Fassung dieses Moduls
behauptete „kein einziger" und hätte das in die Hinweiszeile geschrieben.
Gefunden hat den Fehler nicht die Sorgfalt beim Formulieren, sondern der
Vergleich zweier Auszählungen, die dasselbe hätten ergeben müssen:
Punktquellen zählen über alle 8.116 Wasserkörper 21, über die 4.031
verfehlenden nur 18. Drei Stück Differenz, und die Aussage kippt von einer
Tatsache in eine Übertreibung. Die Gegenprobe im Modul prüft deshalb auf eine
Schwelle, nicht auf null — sie hätte auch die erste Fassung durchgehen
lassen, meldet aber, sobald die Ausnahmen den Promillebereich verlassen.

WAS DARAUS FOLGT, und was NICHT:

  ✓ Zulässig: „Von den Wasserkörpern, die das Ziel verfehlen, nennt
    Österreich bei 80 % die Verbauung als Grund." Das ist eine Aussage über
    die Ursachenzuschreibung — und die ist der Inhalt dieses Abschnitts.

  ✗ Unzulässig: „Verbaute Gewässer sind zu 0 % in gutem Zustand, unverbaute
    zu 81,6 %." Beide Zahlen sind gemessen und beide sind wertlos: Sie
    entstehen aus der Meldelogik, nicht aus der Ökologie. Wer sie als
    Wirkungsnachweis liest, hält eine Definition für einen Befund. Diese
    Auswertung wird deshalb ABSICHTLICH nicht in die Daten geschrieben.

  ✗ Ebenfalls unzulässig: die 4.031 als „Flüsse" zu bezeichnen. Ein
    Wasserkörper ist ein Planungsabschnitt, im Mittel 4,0 km lang — die
    8.116 sind nicht 8.116 Flüsse.

WAS DIESER ABSCHNITT NICHT ZEIGT — bewusst:

1. DIE DREI ZYKLEN. Die Gruppe P4 fällt 4.317 (2010) → 3.461 (2016) → 3.234
   (2022) und sähe nach stetiger Entlastung aus. Sie steht in der Tabelle,
   aber nicht im Bild. Grund ist ein Katalogwechsel, am 01.09.2026 an der
   Quelle belegt: 2010 hat Österreich die Belastung fast nur als Sammelcode
   gemeldet — 4.105 Wasserkörper unter „P4 - Hydromorphology" ohne jeden
   Untertyp, dazu 212 unter einem einzigen Zweckcode. Die feine Aufschlüsselung
   nach Zweck (Hochwasserschutz, Wasserkraft, …) gibt es erst ab 2016. Ein
   Rückgang zwischen einer groben und einer feinen Meldung misst zum Teil die
   Meldung.

   Die Planungsakte hielt dazu fest, „2010 liefert 212 Wasserkörper". Das
   stimmt für die Zweckcodes und ist als Warnung richtig, trifft aber nicht
   die Gruppenebene — dort sind es 4.317. Beides steht jetzt nebeneinander.

2. DIE ZWECKE DER QUERBAUWERKE als eigenes Bild. 2.669 Wasserkörper stehen
   unter „Dams, barriers and locks", und die Zwecke verteilen sich auf
   Hochwasserschutz 1.971, unbekannt/veraltet 991, Wasserkraft 949, sonstige
   699. DIESE ZAHLEN SUMMIEREN SICH AUF 4.610 UND SIND KEINE AUFTEILUNG DER
   2.669 — ein Wasserkörper trägt mehrere Zwecke. Als gestapelter Balken wäre
   das schlicht falsch; sie stehen deshalb in der Notiz, ausdrücklich als
   Mehrfachnennung.

3. EIN EUROPAVERGLEICH. Wäre der fünfte Ländervergleich des Dashboards und
   hinge zudem an der Meldedisziplin der einzelnen Länder, nicht am Zustand
   ihrer Gewässer.

P2-7 IST AUSGESCHLOSSEN, und ohne diesen Ausschluss ist die Auswertung wertlos:
Österreich hat „P2-7 - Diffuse - Atmospheric deposition" pauschal auf ALLE
8.116 Wasserkörper gesetzt, auch auf die 3.984 in gutem Zustand. Der Code
dominiert sonst jede Auszählung und ist der einzige, der auch auf
zielerreichenden Wasserkörpern steht.

Quelle: EEA Discodata, WISE_WFD, Tabelle
SWB_SurfaceWaterBody_swSignificantPressureType (https://discodata.eea.europa.eu/sql),
CC BY 4.0. Meldezyklus 2022.

Abgerufen am 01.09.2026.
"""

from __future__ import annotations

import config
from fliessgewaesser import _abfrage
from gemeinsam import log, quelle_vermerken, warnen

# Die sechs Belastungsgruppen, wie das Feld `swSignificantPressureTypeGroup`
# sie liefert, mit dem Namen, unter dem sie im Balken steht. Reihenfolge ist
# die des Bildes und wird zur Laufzeit nach Größe sortiert — hier steht sie
# nur der Lesbarkeit halber absteigend.
#
# Die Kurznamen sind bewusst keine Fachbegriffe: „Hydromorphologie" ist der
# Begriff der Richtlinie und sagt niemandem etwas, der ihn nicht schon kennt.
GRUPPEN = [
    {"code": "P4", "name": "Verbauung des Gewässers"},
    {"code": "P2", "name": "Einträge aus der Fläche"},
    {"code": "P3", "name": "Wasserentnahme"},
    {"code": "P1", "name": "Einleitungen"},
    {"code": "P9", "name": "Altlasten"},
    {"code": "P8", "name": "unbekannte Ursache"},
]

# Die Zweckcodes innerhalb der Querbauwerke. NUR für die Notiz — sie
# überlappen und dürfen nie gestapelt werden, siehe Kopf.
ZWECKE = {
    "P4-2-2": "Hochwasserschutz",
    "P4-2-9": "unbekannt oder veraltet",
    "P4-2-1": "Wasserkraft",
    "P4-2-8": "sonstige",
}


def _tabelle() -> str:
    return "[WISE_WFD].[latest].[SWB_SurfaceWaterBody_swSignificantPressureType]"


def _bedingung() -> str:
    return (f"countryCode = 'AT' "
            f"AND surfaceWaterBodyCategory = '{config.FG_KATEGORIE}' "
            f"AND cYear = {config.FG_ZYKLUS}")


def _nur_verfehlende() -> str:
    """
    Alle Auszählungen des Bildes laufen über die Wasserkörper, die das Ziel
    verfehlen — das ist der Nenner des Abschnitts.

    OHNE DIESEN FILTER STIMMT EINE ZAHL NICHT, und zwar leise: Punktquellen
    zählen über alle 8.116 Wasserkörper 21, über die 4.031 verfehlenden 18.
    Die Tabelle rechnete sonst 21 gegen einen Nenner von 4.031 und mischte
    damit zwei Grundgesamtheiten in einer Prozentspalte. Bei P2, P3 und P4
    ist der Filter wirkungslos — genau deshalb fällt sein Fehlen nicht auf.
    """
    return (f"euSurfaceWaterBodyCode IN ("
            f"SELECT euSurfaceWaterBodyCode "
            f"FROM [WISE_WFD].[latest].[SWB_SurfaceWaterBody] "
            f"WHERE {_bedingung()} "
            f"AND swEcologicalStatusOrPotentialValue IN ('3', '4', '5'))")


def _eine_zahl(zeilen: list[dict] | None, feld: str = "n") -> int | None:
    """Discodata liefert auch für COUNT(*) eine Zeilenliste."""
    if not zeilen:
        return None
    return int(zeilen[0][feld])


def baue_querbauwerke() -> dict | None:
    log("\n[19/19] Querbauwerke — warum die Wasserkörper das Ziel verfehlen")

    # --- 1. Der Nenner: wie viele verfehlen das Ziel? ----------------------
    # Kommt aus DERSELBEN Tabelle wie `fliessgewaesser`, damit die beiden
    # Abschnitte nicht mit verschiedenen Beständen rechnen können.
    verfehlend_zeilen = _abfrage(f"""
        SELECT COUNT(*) AS n, SUM(cLength) AS km
        FROM [WISE_WFD].[latest].[SWB_SurfaceWaterBody]
        WHERE {_bedingung()}
          AND swEcologicalStatusOrPotentialValue IN ('3', '4', '5')
    """)
    verfehlend = _eine_zahl(verfehlend_zeilen)
    if not verfehlend:
        warnen("Querbauwerke: Nenner nicht ermittelbar — Abschnitt wird "
               "übersprungen. Die zuletzt gebaute querbauwerke.json bleibt "
               "in Kraft.")
        return None
    verfehlend_km = round(float(verfehlend_zeilen[0]["km"] or 0), 1)

    # --- 2. Belastungsgruppen, P2-7 ausgeschlossen ------------------------
    gruppen_zeilen = _abfrage(f"""
        SELECT swSignificantPressureTypeGroup AS g,
               COUNT(DISTINCT euSurfaceWaterBodyCode) AS n
        FROM {_tabelle()}
        WHERE {_bedingung()}
          AND swSignificantPressureType NOT LIKE '{config.QB_PAUSCHALCODE}%'
          AND {_nur_verfehlende()}
        GROUP BY swSignificantPressureTypeGroup
    """)
    if not gruppen_zeilen:
        warnen("Querbauwerke: keine Belastungszeilen — Abschnitt wird "
               "übersprungen.")
        return None

    # Der Gruppenschlüssel steht als „P4 - Hydromorphology" in den Daten;
    # verglichen wird nur der Code vor dem Trennstrich.
    gezaehlt = {}
    for zeile in gruppen_zeilen:
        code = str(zeile["g"]).split(" ")[0].split("-")[0]
        gezaehlt[code] = gezaehlt.get(code, 0) + int(zeile["n"])

    unbekannte = sorted(set(gezaehlt) - {g["code"] for g in GRUPPEN})
    if unbekannte:
        warnen(
            f"Querbauwerke: unerwartete Belastungsgruppen {unbekannte} — die "
            f"Gruppenliste im Modul ist nicht mehr vollständig. Sie fallen "
            f"aus dem Bild, nicht aus der Summe."
        )

    # --- 3. Je Gruppe: wie oft ist sie der EINZIGE genannte Grund? --------
    # Eine Abfrage je Gruppe. Teurer als eine einzige, aber die Alternative
    # wäre ein Selbst-Join über eine Tabelle, die kein ORDER BY neben einem
    # GROUP BY verträgt (Falle 2 in config.py).
    allein = {}
    for gruppe in GRUPPEN:
        code = gruppe["code"]
        zeilen = _abfrage(f"""
            SELECT COUNT(DISTINCT euSurfaceWaterBodyCode) AS n
            FROM {_tabelle()}
            WHERE {_bedingung()}
              AND swSignificantPressureType NOT LIKE '{config.QB_PAUSCHALCODE}%'
              AND {_nur_verfehlende()}
              AND swSignificantPressureTypeGroup LIKE '{code} %'
              AND euSurfaceWaterBodyCode NOT IN (
                    SELECT euSurfaceWaterBodyCode FROM {_tabelle()}
                    WHERE {_bedingung()}
                      AND swSignificantPressureType
                          NOT LIKE '{config.QB_PAUSCHALCODE}%'
                      AND swSignificantPressureTypeGroup NOT LIKE '{code} %')
        """)
        wert = _eine_zahl(zeilen)
        if wert is None:
            warnen(f"Querbauwerke: Alleinstellung der Gruppe {code} nicht "
                   f"ermittelbar — Abschnitt wird übersprungen, statt ihn "
                   f"mit einer Lücke im Balken auszuliefern.")
            return None
        allein[code] = wert

    # --- 4. Wie viele verfehlen OHNE genannte Belastung? ------------------
    # Der Filter auf die verfehlenden ist NICHT redundant, auch wenn er auf
    # den ersten Blick so aussieht: Es gibt Wasserkörper mit Belastung, die
    # das Ziel erreichen — siehe Gegenprobe 1. Ohne den Filter fiele
    # `ohne_belastung` um genau deren Zahl zu niedrig aus.
    mit_belastung_verfehlend = _eine_zahl(_abfrage(f"""
        SELECT COUNT(DISTINCT euSurfaceWaterBodyCode) AS n
        FROM {_tabelle()}
        WHERE {_bedingung()}
          AND swSignificantPressureType NOT LIKE '{config.QB_PAUSCHALCODE}%'
          AND euSurfaceWaterBodyCode IN (
                SELECT euSurfaceWaterBodyCode
                FROM [WISE_WFD].[latest].[SWB_SurfaceWaterBody]
                WHERE {_bedingung()}
                  AND swEcologicalStatusOrPotentialValue IN ('3', '4', '5'))
    """))
    ohne_belastung = (verfehlend - mit_belastung_verfehlend
                      if mit_belastung_verfehlend is not None else None)

    # --- GEGENPROBE 1: wie sauber trennt die Meldelogik wirklich? ---------
    # Der ganze Abschnitt steht und fällt damit, dass eine „signifikante
    # Belastung" nur dort gemeldet wird, wo sie das Ziel gefährdet. Am
    # 01.09.2026 gemessen: Von 3.879 Wasserkörpern mit einer Belastung
    # erreichen GENAU DREI das Ziel — alle drei tragen Punktquellen
    # (Siedlungsabwasser, Industrieanlagen, Deponien).
    #
    # ERSTE FASSUNG DIESES MODULS BEHAUPTETE „kein einziger". Das war falsch
    # und wäre in Hinweiszeile und Notiz gelandet. Gefunden hat es nicht die
    # Sorgfalt beim Schreiben, sondern der Vergleich zweier Auszählungen:
    # Punktquellen zählen über alle Wasserkörper 21, über die verfehlenden
    # 18. Die Differenz war die ganze Meldung.
    #
    # Die Gegenprobe prüft deshalb nicht auf null, sondern auf eine Schwelle:
    # Solange die Ausnahmen im Promillebereich bleiben, trägt der Vorbehalt.
    # Werden es mehr, ist die Formulierung „so gut wie ausschließlich" nicht
    # mehr zu halten.
    mit_belastung_gesamt = _eine_zahl(_abfrage(f"""
        SELECT COUNT(DISTINCT euSurfaceWaterBodyCode) AS n
        FROM {_tabelle()}
        WHERE {_bedingung()}
          AND swSignificantPressureType NOT LIKE '{config.QB_PAUSCHALCODE}%'
    """))
    belastet_und_gut = (mit_belastung_gesamt - mit_belastung_verfehlend
                        if None not in (mit_belastung_gesamt,
                                        mit_belastung_verfehlend) else None)
    if belastet_und_gut is not None and mit_belastung_gesamt:
        anteil_ausnahmen = belastet_und_gut / mit_belastung_gesamt * 100
        if anteil_ausnahmen > config.QB_AUSNAHME_SCHWELLE_PROZENT:
            warnen(
                f"Querbauwerke: {belastet_und_gut} von "
                f"{mit_belastung_gesamt} belasteten Wasserkörpern erreichen "
                f"das Ziel ({anteil_ausnahmen:.2f} %). Über der Schwelle von "
                f"{config.QB_AUSNAHME_SCHWELLE_PROZENT} % trägt der Satz in "
                f"der Hinweiszeile nicht mehr — HINWEISZEILE UND NOTIZ "
                f"PRÜFEN."
            )
        else:
            log(f"    Meldelogik bestätigt: nur {belastet_und_gut} von "
                f"{mit_belastung_gesamt} belasteten Wasserkörpern erreichen "
                f"das Ziel ({anteil_ausnahmen:.2f} %)")

    # --- GEGENPROBE 2: gegen den Bestand des Fließgewässer-Abschnitts -----
    # Beide Abschnitte müssen denselben Bestand kennen, sonst rechnen sie
    # gegeneinander. Der Sollwert ist der des NGP 2021, nicht der aus
    # derselben Abfrage — sonst prüft die Probe nur die Abschrift.
    gesamt = _eine_zahl(_abfrage(f"""
        SELECT COUNT(*) AS n
        FROM [WISE_WFD].[latest].[SWB_SurfaceWaterBody]
        WHERE {_bedingung()}
    """))
    if gesamt != config.FG_ERWARTET_WASSERKOERPER:
        warnen(
            f"Querbauwerke: {gesamt} Wasserkörper im Bestand, der NGP 2021 "
            f"nennt {config.FG_ERWARTET_WASSERKOERPER}. Der Nenner dieses "
            f"Abschnitts und der von `fliessgewaesser` stimmen nicht mehr "
            f"überein."
        )
    else:
        log(f"    Bestand deckt sich mit dem NGP 2021 ({gesamt})")

    # --- GEGENPROBE 3: kein „einzig" größer als das Ganze -----------------
    for code, wert in allein.items():
        if wert > gezaehlt.get(code, 0):
            warnen(
                f"Querbauwerke: Gruppe {code} ist {wert} mal alleiniger "
                f"Grund, kommt aber nur {gezaehlt.get(code, 0)} mal vor. "
                f"Die beiden Abfragen schneiden verschieden zu."
            )
            return None

    # --- 5. Die Zwecke der Querbauwerke, nur für die Notiz ----------------
    zweck_zeilen = _abfrage(f"""
        SELECT swSignificantPressureType AS p,
               COUNT(DISTINCT euSurfaceWaterBodyCode) AS n
        FROM {_tabelle()}
        WHERE {_bedingung()}
          AND swSignificantPressureType LIKE '{config.QB_QUERBAUWERK_CODE}%'
        GROUP BY swSignificantPressureType
    """) or []
    if not zweck_zeilen:
        warnen("Querbauwerke: Zweckabfrage ausgefallen — die Notiz kommt "
               "ohne sie aus, das Bild ist unberührt.")

    zwecke = []
    for zeile in zweck_zeilen:
        code = str(zeile["p"]).split(" ")[0]
        if code in ZWECKE:
            zwecke.append({"zweck": ZWECKE[code],
                           "wasserkoerper": int(zeile["n"])})
    zwecke.sort(key=lambda z: z["wasserkoerper"], reverse=True)

    querbauwerke_gesamt = _eine_zahl(_abfrage(f"""
        SELECT COUNT(DISTINCT euSurfaceWaterBodyCode) AS n
        FROM {_tabelle()}
        WHERE {_bedingung()}
          AND swSignificantPressureType LIKE '{config.QB_QUERBAUWERK_CODE}%'
    """))

    # --- GEGENPROBE 4: die Zwecke dürfen sich NICHT aufteilen lassen ------
    # Klingt verkehrt herum, ist es aber nicht: Wäre die Summe der Zwecke
    # gleich der Zahl der Wasserkörper, gäbe es keine Mehrfachnennung — und
    # dann wäre der ausdrückliche Hinweis darauf in der Notiz falsch.
    summe_zwecke = sum(z["wasserkoerper"] for z in zwecke)
    if querbauwerke_gesamt and summe_zwecke <= querbauwerke_gesamt:
        warnen(
            f"Querbauwerke: die Zwecke summieren sich auf {summe_zwecke} bei "
            f"{querbauwerke_gesamt} Wasserkörpern — es gibt also keine "
            f"Mehrfachnennung mehr. Der entsprechende Satz in der Notiz ist "
            f"dann irreführend und gehört gestrichen."
        )
    elif querbauwerke_gesamt:
        log(f"    Zwecke überlappen wie erwartet ({summe_zwecke} Nennungen "
            f"auf {querbauwerke_gesamt} Wasserkörpern)")

    # --- 6. Zeitkontext, ausdrücklich nicht als Reihe im Bild -------------
    zyklus_zeilen = _abfrage(f"""
        SELECT cYear AS y, swSignificantPressureTypeGroup AS g,
               COUNT(DISTINCT euSurfaceWaterBodyCode) AS n
        FROM {_tabelle()}
        WHERE countryCode = 'AT'
          AND surfaceWaterBodyCategory = '{config.FG_KATEGORIE}'
          AND swSignificantPressureTypeGroup LIKE 'P4%'
        GROUP BY cYear, swSignificantPressureTypeGroup
    """) or []
    je_jahr: dict[int, int] = {}
    for zeile in zyklus_zeilen:
        je_jahr[int(zeile["y"])] = je_jahr.get(int(zeile["y"]), 0) + int(zeile["n"])
    zyklen = [{"jahr": j, "wasserkoerper": je_jahr[j]}
              for j in config.FG_ZYKLEN if j in je_jahr]

    # --- 7. Das Bild -----------------------------------------------------
    balken = []
    for gruppe in GRUPPEN:
        code = gruppe["code"]
        gesamt_gruppe = gezaehlt.get(code, 0)
        if gesamt_gruppe < config.QB_MINDESTZAHL:
            continue
        nur = allein.get(code, 0)
        balken.append({
            "gruppe": gruppe["name"],
            "code": code,
            "wasserkoerper": gesamt_gruppe,
            "nur_dieser_grund": nur,
            "auch_andere": gesamt_gruppe - nur,
            "anteil": round(gesamt_gruppe / verfehlend * 100, 1),
            "anteil_nur": round(nur / verfehlend * 100, 1),
        })
    balken.sort(key=lambda b: b["wasserkoerper"], reverse=True)

    if not balken:
        warnen("Querbauwerke: keine Gruppe über der Mindestzahl — nichts zu "
               "zeichnen.")
        return None

    fuehrend = balken[0]

    # Die Gruppen unter der Mindestzahl fallen aus dem Bild, aber nicht aus
    # der Tabelle — sonst summiert die Tabelle auf etwas anderes als der
    # Text und niemand kann nachrechnen.
    kleine = [
        {"gruppe": g["name"], "code": g["code"],
         "wasserkoerper": gezaehlt.get(g["code"], 0),
         "nur_dieser_grund": allein.get(g["code"], 0)}
        for g in GRUPPEN
        if 0 < gezaehlt.get(g["code"], 0) < config.QB_MINDESTZAHL
    ]

    daten = {
        "stand": f"Meldezyklus {config.FG_ZYKLUS}",
        "zyklus": config.FG_ZYKLUS,
        "abgerufen": "2026-09-01",
        "verfehlend": verfehlend,
        "verfehlend_km": verfehlend_km,
        "bestand": gesamt,
        "ohne_belastung": ohne_belastung,
        "belastet_gesamt": mit_belastung_gesamt,
        "belastet_und_zielerreichend": belastet_und_gut,
        "balken": balken,
        "kleine_gruppen": kleine,
        "fuehrend": {
            "gruppe": fuehrend["gruppe"],
            "wasserkoerper": fuehrend["wasserkoerper"],
            "anteil": fuehrend["anteil"],
            "nur_dieser_grund": fuehrend["nur_dieser_grund"],
            "anteil_nur": fuehrend["anteil_nur"],
        },
        "querbauwerke": querbauwerke_gesamt,
        "querbauwerke_anteil_bestand": (
            round(querbauwerke_gesamt / gesamt * 100, 1)
            if querbauwerke_gesamt and gesamt else None),
        "zwecke": zwecke,
        "zwecke_nennungen": summe_zwecke,
        "zyklen": zyklen,
        "kachel_wert": fuehrend["anteil"],
        # Einordnung unter der Grafik, Konvention 150–234 Zeichen.
        # Sie trägt den Vorbehalt aus dem Kopf — ohne ihn liest sich der
        # Abschnitt als Wirkungsnachweis, und das ist er nicht.
        # „So gut wie ausschließlich" statt „ausschließlich": drei von 3.879
        # belasteten Wasserkörpern erreichen das Ziel doch, siehe
        # Gegenprobe 1.
        "hinweis": (
            "Eine Belastung wird so gut wie nur dort gemeldet, wo sie das "
            "Ziel gefährdet. Der Balken zeigt deshalb, welche Ursache "
            "Österreich dem Verfehlen zuschreibt — nicht, wie stark eine "
            "Verbauung für sich wirkt."
        ),
    }

    quelle_vermerken(
        "Belastungen der Fließgewässer",
        "https://discodata.eea.europa.eu/sql",
        "EEA Discodata, WISE_WFD "
        "(SWB_SurfaceWaterBody_swSignificantPressureType), CC BY 4.0",
        f"Meldezyklus {config.FG_ZYKLUS}",
        "api",
    )

    log(f"  {fuehrend['gruppe']}: {fuehrend['wasserkoerper']} von "
        f"{verfehlend} ({fuehrend['anteil']} %), davon "
        f"{fuehrend['nur_dieser_grund']} als einziger Grund")

    return daten
