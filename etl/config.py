"""
Zentrale Konfiguration der Datenpipeline.

Hier stehen alle Einstellungen an einem Ort. Wenn sich eine Quell-URL
ändert, muss nur diese Datei angepasst werden.

Zum Unterschied gegenüber arbeitsmarkt-at: Dort ist jede Quelle eine
CSV-Datei, die jeden Tag frisch geladen wird. Hier ist genau EINE Quelle
eine API — der Rest sind Publikationen, die alle ein bis drei Jahre
erscheinen. Deren Zahlen stehen abgeschrieben in den Modulen, mit Quelle
und Abrufdatum daneben. Die Konstanten unten sagen der Pipeline, wann
sie eine solche Reihe als überfällig melden soll.
"""

# ---------------------------------------------------------------------------
# Quelle 1 — Eurostat (echte API, wird bei jedem Lauf frisch geholt)
# ---------------------------------------------------------------------------

EUROSTAT_BASIS = (
    "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data"
)

# sdg_15_20 — Terrestrische Schutzgebietsfläche.
# Umfasst national ausgewiesene Schutzgebiete UND Natura-2000-Gebiete,
# Überschneidungen sind von der EEA herausgerechnet. Geprüft 24.08.2026:
# AT-Reihe 2011–2023 vollständig, keine Lücken.
SCHUTZGEBIETE_CODE = "sdg_15_20"
SCHUTZGEBIETE_PARAMS = {
    "format": "JSON",
    "lang": "DE",
    "geo": "AT",
    "areaprot": "TPA",   # Terrestrial protected area
    "unit": "PC",        # Prozent der Landesfläche
}
# Zweiter Abruf in km², damit die Karte nicht nur relativ erzählt.
SCHUTZGEBIETE_PARAMS_KM2 = dict(SCHUTZGEBIETE_PARAMS, unit="KM2")

# Ziel der EU-Biodiversitätsstrategie 2030 und der Biodiversitäts-Strategie
# Österreich 2030+: mindestens 30 % der Landfläche unter Schutz.
SCHUTZGEBIETE_ZIEL = 30.0
SCHUTZGEBIETE_ZIELJAHR = 2030

TIMEOUT_SEKUNDEN = 60

# ---------------------------------------------------------------------------
# Quelle 2 — Eurostat, europäischer Kontext
# ---------------------------------------------------------------------------
# Österreich ist keine Insel: Flora und Fauna teilt es mit den Nachbarn, und
# die FFH-Richtlinie bewertet das Land ausdrücklich in zwei grenzüber-
# schreitenden biogeografischen Regionen (alpin und kontinental). Die
# folgenden Reihen stellen die nationalen Zahlen in diesen Zusammenhang.

# sdg_15_60 — Index weit verbreiteter Vogelarten, EU-Aggregat.
# NUR das EU-Aggregat, keine Länderwerte (geprüft 24.08.2026). Die
# österreichische Reihe kommt weiterhin aus dem BirdLife-Bericht.
#
# ACHTUNG, zwei Fallen in einer Abfrage:
#  1. `unit` hat ZWEI Kategorien (I00 = 2000 = 100 und I90 = 1990 = 100).
#     Ohne Filter liegen beide Reihen hintereinander im selben Wertefeld,
#     und eine naive Zuordnung nach Zeitindex liest die falsche.
#  2. Die EU-Reihe hat die Basis 2000, die österreichische die Basis 1998.
#     Sie müssen vor dem Zeichnen auf dieselbe Basis gebracht werden —
#     siehe vogel.py.
VOGEL_EU_CODE = "sdg_15_60"
VOGEL_EU_PARAMS = {
    "format": "JSON", "lang": "DE",
    "comspec": "CO_FARM",   # gemeine Feldvogelarten, 39 Arten
    "unit": "I00",          # Index, 2000 = 100
    "statinfo": "SME",      # geglättete Schätzung
}

# sdg_02_40 — Anteil der ökologisch bewirtschafteten Fläche an der
# landwirtschaftlich genutzten Fläche. 2000–2024, rund 35 Meldeländer
# inklusive Schweiz und Norwegen.
BIOLANDBAU_CODE = "sdg_02_40"
BIOLANDBAU_PARAMS = {
    "format": "JSON", "lang": "DE",
    "unit": "PC_UAA",
    "crops": "UAAXK0000",   # LN ohne Haus- und Nutzgärten
    "agprdmet": "TOTAL",    # umgestellt plus in Umstellung
}
# Ziel der Biodiversitäts-Strategie Österreich 2030+ und des Green Deal.
BIOLANDBAU_ZIEL = 35.0

# for_area — Waldfläche nach FAO-Definition. Der EINZIGE geprüfte Datensatz,
# der auch die Nicht-EU-Nachbarn Schweiz und Liechtenstein mit echten Werten
# führt. Nur sechs Stützjahre, dafür 1990 bis 2025.
WALD_CODE = "for_area"
WALD_PARAMS = {
    "format": "JSON", "lang": "DE",
    "unit": "THS_HA",
    "indic_fo": "FOR",      # Waldfläche, nicht OWL („sonstiger Baumbestand")
}

# sdg_15_61 — Grünland-Schmetterlingsindex. Erhoben von Butterfly
# Conservation Europe und dem European Butterfly Monitoring Scheme, als
# Indikator geführt von der EEA (SEBI 028), verbreitet über Eurostat.
#
# ACHTUNG, drei Eigenheiten:
#  1. Es gibt NUR das EU-Aggregat (`geo = EU_V`), keine Länderwerte.
#     Österreich ist am Monitoring beteiligt, hat aber keine eigene
#     Reihe ab 1991 — siehe falter.py.
#  2. `statinfo` hat zwei Kategorien: NSME (ungeglättet) und SME
#     (geglättet). Wir nehmen SME; die ungeglättete Reihe schwankt
#     wetterbedingt zweistellig von Jahr zu Jahr.
#  3. `unit` hat ebenfalls zwei: I91 (1991 = 100) und I00 (2000 = 100).
#     Wir nehmen I91. Steht das Basisjahr nachher nicht bei 100, hat die
#     Abfrage die falsche erwischt — falter.py prüft das.
FALTER_CODE = "sdg_15_61"
FALTER_PARAMS = {
    "format": "JSON", "lang": "DE",
    "statinfo": "SME",      # geglättete Schätzung
    "unit": "I91",          # Index, 1991 = 100
}
# Wird zusätzlich beim Auswerten der Antwort angelegt, falls Eurostat die
# Filterparameter einmal ignoriert und doch alle Reihen ausliefert.
FALTER_FILTER = {"statinfo": "SME", "unit": "I91"}

# Österreich und seine acht Nachbarn. EU27 als Bezugsgröße dahinter.
# Liechtenstein grenzt nicht an Österreich? Doch — 34,9 km gemeinsame
# Grenze über den Rhein und das Rätikon.
NACHBARN = ["AT", "DE", "CZ", "SK", "HU", "SI", "IT", "CH", "LI"]
EU_AGGREGAT = "EU27_2020"

# Nicht jede Reihe führt jedes dieser Gebiete. Die Module melden, welche
# fehlen, statt sie stillschweigend als Lücke im Diagramm zu lassen.
HERVORHEBUNG = "AT"

# ---------------------------------------------------------------------------
# Gepflegte Reihen — Erscheinungsrhythmus in Jahren
# ---------------------------------------------------------------------------
# Überschreitet der Abstand zwischen dem Stand einer gepflegten Reihe und
# heute diesen Wert, meldet die Pipeline eine Warnung. Sie bricht NICHT ab:
# eine veraltete Zahl ist kein Fehler, sie ist ein Pflegehinweis.

PFLEGE_RHYTHMUS = {
    "vogel":        2,   # Farmland Bird Index, jährlicher Bericht mit Verzug
    "boden":        4,   # ÖROK-Monitoring, Zyklus seit 2025 dreijährig
    "rotelisten":   2,   # Übersicht der Erscheinungsjahre, lose gepflegt
    "erhaltung":    7,   # Artikel 17: Sechsjahreszyklus plus Berichtsverzug
    "lebensraeume": 7,   # dieselbe Meldung, nach Gruppen aufgeschlüsselt
    "biotoptypen": 15,   # Teilbände 2002–2008, Neuauflage nicht angekündigt
    "rueckkehrer":  7,   # Artikel 17: Sechsjahreszyklus plus Berichtsverzug
    "vogelarten":   2,   # Artentrends, jährlicher Bericht mit Verzug
    "totholz":      2,   # ÖWI-Zwischenauswertung, zuletzt 2018/23 im Jan. 2025
    "fichte":       2,   # dieselbe Quelle, derselbe Rhythmus
    "baumarten":    2,   # dieselbe Quelle, derselbe Rhythmus
    "waldarten":   25,   # Rote Liste Gefäßpflanzen: 1986, 1999, 2022
    "natura2000":   7,   # Artikel 17: Sechsjahreszyklus plus Berichtsverzug
}

# ---------------------------------------------------------------------------
# Quelle Waldinventur — Hinweis für die Pflege
# ---------------------------------------------------------------------------
#
# waldinventur.at hat KEINE dokumentierte Schnittstelle. Die Werte in
# totholz.py und fichte.py sind abgeschrieben. Zum Nachziehen:
#
#   Perioden:    https://www.waldinventur.at/data/erhebungen.txt
#   Werte:       https://www.waldinventur.at/data/{periode}/datajson/{id}.json
#
#   378_l_A  stehendes Totholz, Vfm/ha      Bund, Bundesland, BFI
#   22_01_A  Fichte, Waldfläche             Bund, Bundesland
#   22_08_A  Nadelholz gesamt, Waldfläche   Bund, Bundesland
#   22_34_A  Laubholz gesamt, Waldfläche    Bund, Bundesland
#   1_l      Ertragswald, Fläche            Bund, Bundesland, BFI
#
# Nur die Waldfläche-Baumarten sind so grob gegliedert: die Abfrage kennt
# dort 13 Positionen, die Tabellen des Berichts 30. Wer einzelne Laubarten
# braucht, kommt über `datajson` nicht heran.
#
# Regionscode Lbfi: 0 = Österreich, 1–9 = Bundesländer (1 Bgld, 2 Ktn, 3 NÖ,
# 4 OÖ, 5 Sbg, 6 Stmk, 7 Tirol, 8 Vbg, 9 Wien).
#
# ACHTUNG BEIM NACHZIEHEN: Das Feld `_Proz` ist zwischen den Perioden NICHT
# vergleichbar — 2018/23 rechnet gegen den Gesamtwald, 2016/21 gegen den
# Ertragswald. Anteile immer selbst aus Fläche und `1_l` rechnen.
WALDINVENTUR_PERIODE = "erg9_10"      # 2018/23, Zwischenauswertung

# ---------------------------------------------------------------------------
# Quelle Baulandreserven — OGD-FeatureServer des Umweltbundesamts
# ---------------------------------------------------------------------------
#
# Die zweite echte API dieser Pipeline neben Eurostat. Der Dienst speist auch
# den öffentlichen GIS-Viewer der ÖROK. Lizenz CC BY 4.0, gelistet auf
# data.gv.at als hochwertiger Datensatz nach HVD-Verordnung.
#
# Der Dienst kann serverseitig gruppieren und summieren
# (`supportsStatistics`), es muss also keine einzige Geometrie geladen werden:
# 538.541 Grundstücke werden zu 2.086 Gemeindezeilen, bevor irgendetwas über
# die Leitung geht.
#
# NICHT `Shape__Area` verwenden — Web Mercator, Flächen um Faktor ~2,2
# aufgebläht. Die FLAECHE_*-Felder sind echte Quadratmeter.

BLR_ABFRAGE_URL = (
    "https://services7.arcgis.com/JhrnFQUbVgiJfOG5/arcgis/rest/services/"
    "Baulandreserven_2025_OGD/FeatureServer/0/query"
)

# Der Dienst meldet maxRecordCount 2000. Wer mehr anfordert, bekommt trotzdem
# 2000 — und merkt es nicht, wenn er nicht blättert.
BLR_SEITENGROESSE = 2000

# Bei 2.086 Gemeinden reichen zwei Seiten. Sechs sind Luft für Wachstum und
# zugleich die Reißleine, falls das Blättern in eine Schleife läuft.
BLR_MAX_SEITEN = 6

# Österreich hat rund 2.093 Gemeinden; 2.086 davon führen Baulandreserven
# (Stand 27.08.2026). Wien zählt als EINE Gemeinde, nicht als 23 Bezirke.
BLR_GEMEINDEN_MIN = 1_950
BLR_GEMEINDEN_MAX = 2_200

# Anteil der Grundstücke mit FLAECHE_SONSTIGE = -1 ("nicht ermittelt"), ab dem
# gewarnt wird. Am 27.08.2026 waren es 0,10 %.
BLR_SENTINEL_GRENZE = 2.0

# Flächeninanspruchnahme gesamt in Hektar, Stichjahr 2025 (568.120 ha =
# 5.681,2 km², siehe boden.py). Reserven sind laut ÖROK-Definition eine
# Teilmenge davon und können sie nicht übersteigen — die Gegenprobe dazu
# steht in baulandreserven.py.
BLR_FI_BESTAND_HA = 568_120

# ---------------------------------------------------------------------------
# Quelle Gemeindegrenzen — Statistik Austria WFS
# ---------------------------------------------------------------------------
#
# ACHTUNG bei der Adresse: Der Dienst leitet von statistik.gv.at auf
# statistik.at um. Wer die .gv.at-Adresse aus dem Browser heraus abruft,
# scheitert an der Same-Origin-Regel — in Python ist das gleichgültig,
# beim Prüfen im Browser nicht.
#
# Der Layername trägt den Gebietsstand: ..._GEM_20250101 ist der Stand
# 01.01.2025. Er muss zum Stichjahr der Daten passen, sonst fallen
# umnummerierte Gemeinden lautlos aus der Einfärbung.

GRENZEN_WFS_URL = "https://www.statistik.at/gs-open/GEODATA/ows"
GRENZEN_LAYER = "STATISTIK_AUSTRIA_GEM_20250101"

# 45 MB über eine Leitung, die man nicht kennt — großzügig bemessen.
GRENZEN_TIMEOUT_SEKUNDEN = 300

# Vereinfachungstoleranz in Metern (die Projektion rechnet in Metern).
# 150 m liegen bei einer Österreichkarte deutlich unter einem Bildpunkt.
GRENZEN_TOLERANZ_METER = 150

# Unterhalb dieser Zahl stimmt etwas nicht — vermutlich deckelt der Dienst.
GRENZEN_MIN_GEMEINDEN = 2_000

# Ab dieser Dateigröße wird gewarnt: die Karte lädt sonst spürbar langsam.
GRENZEN_MAX_KB = 900

# ---------------------------------------------------------------------------
# Quelle Fließgewässer — EEA Discodata (SQL auf die WISE-WFD-Datenbank)
# ---------------------------------------------------------------------------
#
# Die dritte echte API dieser Pipeline neben Eurostat und dem ArcGIS-Dienst
# des Umweltbundesamts. Discodata legt die Meldungen der Mitgliedstaaten nach
# Wasserrahmenrichtlinie als abfragbare Tabellen offen; CC BY 4.0 (EEA Legal
# Notice). Eine Abfrage je Auswertung, Antwort ist JSON unter `results`.
#
# VIER FALLEN, alle am 30./31.08.2026 erlebt und nicht aus der Doku:
#
#   1. Die ERSTE Spalte braucht zwingend einen Alias (`AS v`), sonst
#      Fehlercode 10004. Die übrigen dürfen ohne.
#   2. `GROUP BY` zusammen mit `ORDER BY` wird abgewiesen. Ohne ORDER BY
#      abfragen und im Modul sortieren.
#   3. `INFORMATION_SCHEMA` ist gesperrt ("Your query is not allowed
#      execution"). Der Spaltenkatalog steht unter `…/md`, 24 MB JSON.
#   4. Aus dem Browser geht die Abfrage nur von der Discodata-Herkunft aus
#      (CORS), und ein Abruf über ein URL-Werkzeug kippt ab einer gewissen
#      Länge mit HTTP 403 "URL exceeds maximum length". In Python über
#      `requests` ist beides gleichgültig — deshalb läuft dieses Modul
#      ausschließlich in der CI und nicht im Sandkasten, der ohnehin kein
#      Netz hat.
#
# WARUM `cLength` UND NICHT DIE ANZAHL ALLEIN: siehe fliessgewaesser.py.

FG_ABFRAGE_URL = "https://discodata.eea.europa.eu/sql"

# Eigener, großzügiger Zeitablauf statt der allgemeinen TIMEOUT_SEKUNDEN (60).
# Discodata antwortet messbar langsam: am 31.08.2026 lief ein Abruf über ein
# URL-Werkzeug selbst bei kurzer Abfrage in einen 180-Sekunden-Zeitablauf.
# Vier Abfragen à 180 s sind im schlimmsten Fall zwölf Minuten — deshalb
# bricht ein Fehlschlag hier auch NICHT die Pipeline ab, siehe die
# Begründung an `_abfrage()` in fliessgewaesser.py.
FG_TIMEOUT_SEKUNDEN = 180

# Der Bewertungszyklus, den der Abschnitt zeigt. 2010, 2016 und 2022 liegen
# in derselben Tabelle; verglichen wird aber NICHT über die Zyklen — die
# Wasserkörper-Abgrenzung und die Bewertungsmethodik haben zwischen ihnen
# gewechselt. Die beiden älteren Zyklen holt das Modul trotzdem, als
# Zeitkontext für Tabelle und Notiz.
FG_ZYKLUS = 2022
FG_ZYKLEN = [2010, 2016, 2022]

# `RW` = river water body. Seen (`LW`), Übergangs- und Küstengewässer sind
# ausgeschlossen — Österreich meldet ohnehin keine Küste.
FG_KATEGORIE = "RW"

# Gegenprobe gegen den Nationalen Gewässerbewirtschaftungsplan 2021: Der NGP
# berichtet über Fließgewässer mit einem Einzugsgebiet über 10 km², teilt sie
# in 8.116 Oberflächenwasserkörper und beziffert das Netz mit 32.101 km
# (NGP 2021, Abschnitt 1.2.1.1). Discodata liefert exakt dieselben 8.116
# Wasserkörper und 32.135 km. Das ist KEIN zweiter, engerer Nenner — es ist
# dieselbe Meldung, einmal national und einmal an die EU berichtet.
FG_ERWARTET_WASSERKOERPER = 8_116
FG_ERWARTET_LAENGE_KM = 32_101      # NGP-Wert
FG_TOLERANZ_LAENGE_KM = 100         # Rundung und Meldestand

# Zweite Gegenprobe, unabhängig von der ersten: Der NGP nennt 12,3 % erheblich
# veränderte und 1,8 % künstliche Fließgewässer, jeweils längenbezogen.
FG_ERWARTET_HMWB_PROZENT = 12.3
FG_ERWARTET_AWB_PROZENT = 1.8
FG_TOLERANZ_PUNKTE = 0.5

# ---------------------------------------------------------------------------
# Ausgabe
# ---------------------------------------------------------------------------

AUSGABE_ORDNER = "docs/data"

# Wird in meta.json mitgeschrieben und vom Frontend für den Einbettungscode
# benutzt. Beim Umzug auf die eigene Domain hier ändern.
EINBETTUNG = {
    "basis": "https://biodiversitaet-monitor.at",
    "pfad": "/einbetten/",
}
