"""
Prüfung des Moduls `flaecheninanspruchnahme` gegen eine Attrappe.

WARUM EINE ATTRAPPE UND KEIN ECHTER LAUF: Der Datensatz ist 1,27 GiB und
weder Sandkasten noch der Rechner des Users erreichen den Server. Geprüft
wird deshalb, was ohne die echten Daten prüfbar ist: das Zerlegen des
GPKG-Kopfes, die Aggregation je Gemeinde und Klasse, der Rückfall vom
Detail- auf den Aggregatcode, der Nenner aus `gemeinden.json`, die
Klassengrenzen und das Hausmaß der Hinweiszeile.

  python3 pruefung_flaecheninanspruchnahme.py

Grün heißt: die Rechenwege stimmen. Ob die Quelle liefert, sagt erst der
CI-Lauf.
"""
import json, sys
from pathlib import Path
import config, gemeinsam
import json, sqlite3, struct
from pathlib import Path
from shapely.geometry import box, MultiPolygon
import shapely

def gpkg_blob(geom, srs=31287):
    wkb = shapely.to_wkb(geom)
    kopf = b"GP" + bytes([0, 0x01]) + struct.pack("<i", srs)  # flags: little endian, keine Hülle
    return kopf + wkb

def baue(pfad: Path, zeilen):
    if pfad.exists(): pfad.unlink()
    v = sqlite3.connect(pfad)
    v.execute('''CREATE TABLE "FI_OGD_2025" ("OBJECTID" INTEGER primary key autoincrement not null,
      "Shape" MULTIPOLYGON, "OGD_FI" DOUBLE, "OGD_FI_agg" DOUBLE, "KG_NR" TEXT(5), "KG" TEXT(50),
      "GKZ" TEXT(5), "PG" TEXT(50), "BKZ" TEXT(3), "PB" TEXT(50), "BL_KZ" TEXT(1), "BL" TEXT(50))''')
    for gkz, detail, agg, geom in zeilen:
        v.execute('INSERT INTO "FI_OGD_2025" ("Shape","OGD_FI","OGD_FI_agg","GKZ") VALUES (?,?,?,?)',
                  (gpkg_blob(geom), detail, agg, gkz))
    v.commit(); v.close()

def quadrat(x, y, meter):
    return MultiPolygon([box(x, y, x + meter, y + meter)])

ORDNER = Path("docs/data"); ORDNER.mkdir(parents=True, exist_ok=True)
config.AUSGABE_ORDNER = "docs/data"

# Gemeinde A: 100 ha Fläche, davon 10 ha FI (2 ha Verkehr, 8 ha Siedlung) = 10,00 %
# Gemeinde B: 400 ha Fläche, davon 4 ha FI (nur Detailcode 2112 -> Aggregat 210) = 1,00 %
# Gemeinde C: FI vorhanden, aber kein Umriss -> muss als "ohne Nenner" gemeldet werden
zeilen = [
    ("10101", 103, 100, quadrat(0, 0, 100)),          # 1 ha
    ("10101", 103, 100, quadrat(200, 0, 100)),        # 1 ha
    ("10101", 213, 210, quadrat(0, 300, 200)),        # 4 ha
    ("10101", 2112, None, quadrat(0, 600, 200)),      # 4 ha, Aggregat fehlt -> 210
    ("10201", 2112, None, quadrat(0, 0, 200)),        # 4 ha
    ("99999", 511, 500, quadrat(0, 0, 100)),          # 1 ha, ohne Umriss
]
baue(Path("attrappe.gpkg"), zeilen)

grenzen = {"type": "FeatureCollection", "aufbau": 3, "features": [
    {"type": "Feature", "properties": {"name": "Eisenstadt", "gkz": "10101", "flaeche_m2": 1_000_000},
     "geometry": None},
    {"type": "Feature", "properties": {"name": "Rust", "gkz": "10201", "flaeche_m2": 4_000_000},
     "geometry": None},
]}
(ORDNER / "gemeinden.json").write_text(json.dumps(grenzen), encoding="utf-8")

import flaecheninanspruchnahme as fi
fi.ZIEL = ORDNER / "flaecheninanspruchnahme.json"
fi.GRENZEN = ORDNER / "gemeinden.json"

je_gemeinde, je_detail = fi._aggregieren(Path("attrappe.gpkg"))
fehler = []
def pruefe(name, ist, soll, tol=1e-6):
    ok = abs(ist - soll) <= tol
    print(("  OK  " if ok else "  FEHL") + f" {name}: {ist} (soll {soll})")
    if not ok: fehler.append(name)

print("\n[1] Aggregation je Gemeinde und Klasse")
pruefe("10101 Verkehr (100) m²", je_gemeinde["10101"][100], 20_000)
pruefe("10101 Siedlung (210) m²", je_gemeinde["10101"][210], 80_000)
pruefe("10201 Siedlung (210) m²", je_gemeinde["10201"][210], 40_000)
pruefe("Detail 2112 gesamt m²", je_detail[2112], 80_000)
pruefe("Detail 103 gesamt m²", je_detail[103], 20_000)

print("\n[2] Rückfall Detail -> Aggregat")
pruefe("2112 -> 210", fi._klasse_aus_detail(2112), 210)
pruefe("101 -> 100", fi._klasse_aus_detail(101), 100)
pruefe("420 -> 400", fi._klasse_aus_detail(420), 400)
pruefe("520 -> 500", fi._klasse_aus_detail(520), 500)

print("\n[3] GPKG-Kopf")
from shapely.geometry import box
blob = gpkg_blob(box(0,0,1,1))
pruefe("WKB-Länge nach Kopfabzug", len(fi._wkb(blob)), len(blob) - 8)
print(("  OK  " if fi._wkb(b"XX") is None else "  FEHL") + " Fremdblob wird abgewiesen")
if fi._wkb(b"XX") is not None: fehler.append("Fremdblob")

print("\n[4] Nenner und Anteil")
nenner = fi._gemeindeflaechen()
pruefe("Nenner Eisenstadt m²", nenner["10101"][1], 1_000_000)
anteil_a = 100 * sum(je_gemeinde["10101"].values()) / nenner["10101"][1]
pruefe("Anteil Eisenstadt %", round(anteil_a, 2), 10.0)
anteil_b = 100 * sum(je_gemeinde["10201"].values()) / nenner["10201"][1]
pruefe("Anteil Rust %", round(anteil_b, 2), 1.0)

print("\n[5] Klassengrenzen streng steigend")
g = fi._klassen([0.5, 1.0, 2.0, 4.0, 8.0, 16.0, 30.0])
print("  Grenzen:", g)
if not all(b > a for a, b in zip(g, g[1:])): fehler.append("Klassengrenzen")
print(("  OK  " if all(b > a for a, b in zip(g, g[1:])) else "  FEHL") + " streng steigend")
g2 = fi._klassen([1.0, 1.0, 1.0, 1.0, 1.0])
print("  Entartet (alle gleich):", g2)
if not all(b > a for a, b in zip(g2, g2[1:])): fehler.append("Klassengrenzen entartet")

print("\n[6] Hinweiszeile im Hausmaß 150-234")
z = fi._hinweis(6.8, {"name": "Wien", "anteil": 33.4})
print(f"  {len(z)} Zeichen")
print("  " + z)
if not 150 <= len(z) <= 234: fehler.append("Hinweiszeile")

print("\n[7] Spitzenreiter braucht eine Mindestflaeche")
# Rattenberg-Fall: hoechster Anteil, aber winzige Gemeinde. Der Satz soll
# eine Regel erklaeren, nicht eine Ausnahme.
kandidaten = [
    {"name": "Rattenberg", "anteil": 78.7, "flaeche_ha": 11.3},
    {"name": "Brunn am Gebirge", "anteil": 78.2, "flaeche_ha": 725.8},
    {"name": "Irgendwo", "anteil": 12.0, "flaeche_ha": 900.0},
]
gewaehlt = fi._spitzenreiter(kandidaten)
pruefe("gewaehlter Name ist nicht Rattenberg", 1 if gewaehlt["name"] == "Brunn am Gebirge" else 0, 1)
# Wenn KEINE Gemeinde die Schwelle nimmt, lieber ungefiltert als gar nichts
nur_klein = [{"name": "Rattenberg", "anteil": 78.7, "flaeche_ha": 11.3}]
pruefe("Rueckfall ohne taugliche Gemeinde", 1 if fi._spitzenreiter(nur_klein)["name"] == "Rattenberg" else 0, 1)
pruefe("leere Liste ergibt None", 1 if fi._spitzenreiter([]) is None else 0, 1)

print("\n[8] Zwischenspeicher friert die Texte NICHT ein")
# Der teure Teil (gemeinden, oesterreich) kommt aus der Datei, die
# abgeleiteten Groessen werden neu gerechnet.
kern = {
    "stand": config.FI_STAND_JAHR,
    "aufbau": config.FI_AUFBAU,
    "gemeinden": [
        {"gkz": "10101", "name": "Eisenstadt", "fi_ha": 100.0,
         "flaeche_ha": 1000.0, "anteil": 10.0, "klassen": {"100": 20.0}},
        {"gkz": "10201", "name": "Rust", "fi_ha": 4.0,
         "flaeche_ha": 400.0, "anteil": 1.0, "klassen": {"210": 4.0}},
        {"gkz": "10301", "name": "Winzig", "fi_ha": 40.0,
         "flaeche_ha": 50.0, "anteil": 80.0, "klassen": {"210": 40.0}},
    ],
    "oesterreich": {"fi_km2": 1.44, "anteil": 6.8, "bericht_km2": 5681.2,
                    "abweichung_prozent": 0.0, "detail_ha": {}},
}
quellen_vorher = len(gemeinsam.QUELLEN)
erg = fi._ableiten(kern)
pruefe("Klassengrenzen ergaenzt", 1 if erg.get("klassengrenzen") else 0, 1)
pruefe("Hinweiszeile ergaenzt", 1 if erg.get("hinweis") else 0, 1)
pruefe("Auflage ergaenzt", 1 if "Zustandskarte" in erg.get("auflage", "") else 0, 1)
pruefe("Klassennamen aus config", len(erg.get("klassennamen", {})), len(config.FI_KLASSEN))
pruefe("Kern unveraendert durchgereicht", len(erg["gemeinden"]), 3)
# Der Zwischenspeicher-Weg muss die Quelle ebenfalls melden, sonst faellt
# der Abschnitt still aus dem Quellenblock (passiert am 31.08.2026).
pruefe("Quelle vermerkt", len(gemeinsam.QUELLEN) - quellen_vorher, 1)
# Und der Spitzenreiter im Text ist NICHT die 50-ha-Gemeinde
print("  " + erg["hinweis"])
if "Winzig" in erg["hinweis"]: fehler.append("Spitzenreiter ungefiltert")
print(("  OK  " if "Winzig" not in erg["hinweis"] else "  FEHL") + " kleine Gemeinde nicht im Satz")
# `gemeinsam.AUSGABE` steht beim Import fest (WURZEL / config.AUSGABE_ORDNER);
# ein spaeteres Umbiegen von config.AUSGABE_ORDNER wirkt nicht mehr. Deshalb
# hier gegen den Pfad pruefen, den das Modul tatsaechlich benutzt.
pruefe("Datei geschrieben", 1 if (gemeinsam.AUSGABE / "flaecheninanspruchnahme.json").exists() else 0, 1)

print("\n" + ("ALLE PRUEFUNGEN GRUEN" if not fehler else f"FEHLER: {fehler}"))
sys.exit(1 if fehler else 0)
