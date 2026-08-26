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
    "biotoptypen": 15,   # Teilbände 2002–2008, Neuauflage nicht angekündigt
    "rueckkehrer":  7,   # Artikel 17: Sechsjahreszyklus plus Berichtsverzug
    "vogelarten":   2,   # Artentrends, jährlicher Bericht mit Verzug
}

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
