# biodiversitaet-monitor.at

Schutzgebiete, Feld- und Wiesenvögel, Bodenverbrauch und der Zustand der
Roten Listen — der Zustand der biologischen Vielfalt in Österreich, aus
offenen Daten aufbereitet.

**Live: [biodiversitaet-monitor.at](https://biodiversitaet-monitor.at)**

Dieses Repository enthält die Datenpipeline und die Diagramme. Die erzeugten
JSON-Dateien liegen in `docs/data/` und werden über GitHub Pages ausgeliefert.

## Warum manche Zahlen im Code stehen

Anders als beim Schwesterprojekt [arbeitsmarkt-monitor.at](https://arbeitsmarkt-monitor.at)
lässt sich hier **nicht alles automatisch abrufen**. Österreich erhebt zur
Biodiversität reichlich, veröffentlicht aber überwiegend PDF-Fachberichte ohne
Datenanhang. Die Pipeline unterscheidet deshalb zwei Sorten von Abschnitten:

| Sorte | Beschaffung | Module |
|---|---|---|
| **Automatisch** | Bei jedem Lauf frisch von einer API | `schutzgebiete.py` (Eurostat) |
| **Gepflegt** | Aus einer Publikation abgeschrieben, mit Quelle und Abrufdatum im Modul | `vogel.py`, `boden.py`, `rotelisten.py` |

Gepflegte Reihen tragen im JSON das Feld `"pflege"` mit Quelle, Stand und dem
Hinweis, wann die nächste Ausgabe erwartet wird. Die Pipeline meldet im Log,
wenn eine gepflegte Reihe älter ist als ihr erwarteter Erscheinungsrhythmus —
so verfällt keine Zahl unbemerkt.

## Datenquellen

| Quelle | Kennzahl | Lizenz |
|---|---|---|
| [Eurostat — sdg_15_20](https://ec.europa.eu/eurostat/databrowser/view/sdg_15_20) | Terrestrische Schutzgebietsfläche | Eurostat-Nutzungsbedingungen |
| [BirdLife Österreich / BMLUK — Farmland Bird Index](https://www.bmluk.gv.at/) | Bestandsindex 23 Feld- und Wiesenvogelarten | Quellenangabe, siehe Bericht |
| [ÖROK — Monitoring Flächeninanspruchnahme](https://www.oerok.gv.at/monitoring-flaecheninanspruchnahme) | Bodenverbrauch, Versiegelung | Open Government Data |
| [Umweltbundesamt — Rote Listen](https://www.umweltbundesamt.at/umweltthemen/naturschutz/rotelisten) | Erscheinungsjahre der Roten Listen | siehe Publikation |

Die Schutzgebietszahl umfasst national ausgewiesene Schutzgebiete **und**
Natura-2000-Gebiete; Überschneidungen sind herausgerechnet. Sie sagt nichts
über die Schutzintensität — ein Landschaftsschutzgebiet zählt gleich wie ein
Nationalpark-Kernzonengebiet.

## Lizenz

Grafiken und aufbereitete Daten: CC BY 4.0, Namensnennung
`biodiversitaet-monitor.at`. Für die Rohdaten gelten die Lizenzen der
jeweiligen Quelle (siehe Tabelle).
