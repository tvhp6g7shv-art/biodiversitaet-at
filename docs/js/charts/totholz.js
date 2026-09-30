/* ===========================================================================
   Biodiversitäts-Dashboard Österreich — Themenstrang: totholz
   ---------------------------------------------------------------------------
   Wird nach js/kern.js geladen; die Helfer kommen aus window.BIO.
   =========================================================================== */
(function (BIO) {
"use strict";
const { stil, zahl, pz, basis, tabelle, setzeText, setzeHtml,
        diagramme, schrift } = BIO;

/* --- Totholz: Bundeslandkarte, sequenzielle Skala ---------------------

   WARUM EINE NEUTRALE FARBRAMPE UND KEINE GUT/SCHLECHT-SKALA:
   Das ist die wichtigste Entscheidung an dieser Grafik. Über acht
   Bundesländer ohne Wien korreliert das stehende Totholz mit dem
   Fichtenanteil zu r = +0,66 — je mehr Fichte, desto MEHR Totholz.
   Salzburg, Tirol und Vorarlberg stehen oben, weil dort Steilhänge die
   Nutzung erschweren und der Borkenkäfer stehende tote Fichten hinterlässt.
   Eine grün-eingefärbte „viel ist gut"-Skala würde daraus eine
   Naturnähe-Rangliste machen, die die Zahl nicht hergibt. `--viz-seq-*` ist
   einfarbig und sagt nur „mehr" und „weniger".

   WARUM BUNDESLAND UND NICHT BEZIRKSFORSTINSPEKTION:
   Die ÖWI gibt Totholz auch je BFI aus — dort liegen die Stichprobenfehler
   aber bei 20 bis 40 Prozent des Werts, und sieben Regionen sind als
   unsicher oder datenarm gekennzeichnet. Auf Bundeslandebene sind es 3,8 bis
   22 Prozent. Feiner wäre hier nicht genauer, sondern nur bunter.

   WARUM WIEN AUSGEGRAUT IST:
   28,9 ± 11,2 Vfm/ha auf 9.000 Hektar Wald — ein Stichprobenfehler von
   38,8 Prozent. Der Wert würde die Skala sprengen und die restlichen acht
   Länder in eine ununterscheidbare Farbe drücken. Er steht in der Tabelle
   und im Tooltip, aber er färbt nicht mit.

   WARUM DIE EINORDNUNG NICHT AUF DER KARTE STEHT:
   Die Karte zeigt STEHENDES Totholz, die Naturwald-Vergleichswerte gelten
   für GESAMTtotholz. Beides gegeneinanderzustellen wäre falsch. Die
   Einordnung steht deshalb als eigener Absatz darunter und nennt ihre
   Bezugsgrösse selbst. */

/* ECharts kennt nur Polygon und MultiPolygon. Sollte die Geometrie je aus
   einer Reparatur eine GeometryCollection mitbringen, sucht ECharts darin
   `coordinates`, findet nichts und wirft „Invalid geoJson format". */
function flaechenNormalisieren(geo) {
  if (!geo?.features) return geo;
  const raus = (g) => {
    if (!g) return null;
    if (g.type === "Polygon" || g.type === "MultiPolygon") return g;
    if (g.type === "GeometryCollection") {
      const teile = (g.geometries ?? []).map(raus).filter(Boolean);
      if (!teile.length) return null;
      const ringe = teile.flatMap((t) =>
        t.type === "Polygon" ? [t.coordinates] : t.coordinates);
      return { type: "MultiPolygon", coordinates: ringe };
    }
    return null;
  };
  return {
    ...geo,
    features: geo.features
      .map((f) => ({ ...f, geometry: raus(f.geometry) }))
      .filter((f) => f.geometry),
  };
}

/* Kartenrahmen [[West, Süd], [Ost, Nord]]. Fest gesetzt statt aus der
   Geometrie gerechnet, damit ein einzelnes kaputtes Polygon den Zuschnitt
   nicht verzieht. */
const RAHMEN_AT = [[9.5, 46.3], [17.2, 49.1]];
const ASPEKT = 0.673;

function baueTotholz(daten, geo) {
  const S = schrift();
  if (!daten?.eintraege?.length) return;

  const abschnitt = document.getElementById("s-totholz");
  if (abschnitt) abschnitt.style.display = "";

  const feld = document.getElementById("c-totholz");
  if (!feld) return;

  const belastbare = daten.eintraege.filter((e) => e.belastbar);
  const nachName = Object.fromEntries(daten.eintraege.map((e) => [e.name, e]));

  setzeText("u-totholz",
    `Stehendes Totholz im Ertragswald · Vorratsfestmeter je Hektar · ` +
    `Waldinventur ${daten.stand.replace("ÖWI ", "")}`);

  /* Die Notiz trägt den Befund, die Einordnung darunter die Vorbehalte.
     Beides getrennt, weil kern.js die Einordnung am Handy einklappt. */
  setzeText("n-totholz",
    `Im Durchschnitt stehen ${pz(daten.bund)} Vorratsfestmeter totes Holz je ` +
    `Hektar Ertragswald — gut doppelt so viel wie ${daten.seit} ` +
    `(${pz(daten.seit_wert)}). Zwischen ${daten.niedrigster.name} ` +
    `(${pz(daten.niedrigster.wert)}) und ${daten.hoechster.name} ` +
    `(${pz(daten.hoechster.wert)}) liegt Faktor ${pz(daten.spanne_faktor)}.`);

  /* Nur die Doppeldeutigkeit, nicht zusätzlich `hinweis` — zusammen waren
     die beiden 376 Zeichen und damit weit über der Konvention von 150–234.
     Der Messbereich steht ohnehin schon in der Unterzeile. */
  setzeText("h-totholz", daten.doppeldeutig);

  /* Skala nur über die belastbaren Werte. Nähme man Wien mit seinen 28,9
     dazu, lägen die acht anderen Länder alle im unteren Drittel der Rampe
     und wären farblich kaum noch zu unterscheiden. */
  const min = Math.floor(Math.min(...belastbare.map((e) => e.wert)));
  const max = Math.ceil(Math.max(...belastbare.map((e) => e.wert)));

  if (!geo) {
    /* Höhe zurücknehmen, sonst bleibt ein leerer Kasten stehen. */
    feld.className = "";
    feld.style.height = "auto";
    feld.innerHTML = `<p class="viz-unterzeile" style="padding:4px 0 0">
      Die Karte ist gerade nicht verfügbar — die Werte stehen in der Tabelle
      darunter.</p>`;
  } else {
    echarts.registerMap("at-bundeslaender", flaechenNormalisieren(geo));
    /* SVG statt Canvas. Die Schwesterkarte in arbeitsmarkt-at zeichnet 80
       Bezirke und ist mit Canvas schneller; hier sind es neun vereinfachte
       Flächen, da nimmt sich das nichts. Der Unterschied: Mit SVG lässt sich
       die Karte in der jsdom-Prüfung überhaupt aufbauen — Canvas braucht ein
       `getContext`, das jsdom ohne das native canvas-Paket nicht hat, und
       das Modul stirbt dort mit „Cannot set properties of null". Eine Grafik,
       die sich nicht prüfen lässt, ist die schnellere Zeichnung nicht wert. */
    const d = echarts.getInstanceByDom(feld) || echarts.init(feld, null, { renderer: "svg" });
    if (!diagramme.includes(d)) diagramme.push(d);

    /* Nicht belastbare Länder bekommen "-" statt einer Zahl. ECharts färbt
       sie dann mit `areaColor` aus itemStyle, nicht über die visualMap. */
    const werte = daten.eintraege.map((e) => ({
      name: e.name,
      value: e.belastbar ? e.wert : "-",
    }));

    d.setOption({
      ...basis(),
      tooltip: {
        ...basis().tooltip, trigger: "item",
        formatter: (p) => {
          const e = nachName[p.name];
          if (!e) return `${p.name}<br><span style="color:${stil("--viz-muted")}">keine Daten</span>`;
          return `<strong>${e.name}</strong><br>` +
            `${pz(e.wert)} Vfm/ha<br>` +
            `<span style="color:${stil("--viz-muted")}">± ${pz(e.fehler)} ` +
            `(${pz(e.fehler_relativ)} % Stichprobenfehler)</span>` +
            (e.belastbar ? "" :
              `<br><span style="color:${stil("--viz-muted")}">zu unsicher für die Karte</span>`);
        },
      },
      visualMap: {
        type: "continuous",
        min, max, left: 12, top: 12, orient: "vertical",
        itemWidth: 12, itemHeight: 140, calculable: true,
        /* Beschriftung sagt, was die Farbe bedeutet — bewusst „mehr/weniger"
           und nicht „gut/schlecht", siehe Kopfkommentar. */
        text: ["mehr Totholz", "weniger"],
        formatter: (v) => pz(v),
        textStyle: { color: stil("--viz-muted"), fontSize: S.achse },
        inRange: { color: [
          stil("--viz-seq-1"), stil("--viz-seq-2"), stil("--viz-seq-3"),
          stil("--viz-seq-4"), stil("--viz-seq-5"), stil("--viz-seq-6"),
        ] },
      },
      series: [{
        type: "map", map: "at-bundeslaender", data: werte,
        roam: false,
        ...BIO.kartenLayout(feld, RAHMEN_AT, ASPEKT),
        itemStyle: {
          areaColor: stil("--viz-grid"),
          borderColor: stil("--viz-surface"),
          borderWidth: 1,
        },
        label: { show: false },
        emphasis: {
          label: { show: false },
          itemStyle: { borderColor: stil("--viz-text"), borderWidth: 1.5 },
        },
        select: { disabled: true },
      }],
    });

    /* layoutSize ist eine Pixelzahl und überlebt kein resize — hier die
       Nachrechnung, die kern.js beim resize aufruft. */
    d.__neuLayouten = () => d.setOption({
      series: [BIO.kartenLayout(feld, RAHMEN_AT, ASPEKT)],
    });
  }

  /* Tabelle absteigend nach Wert. Der Stichprobenfehler steht als eigene
     Spalte daneben, nicht in einer Fussnote — bei Werten, die sich um
     Faktor 2 unterscheiden, entscheidet er mit, welche Reihung überhaupt
     belastbar ist. */
  setzeHtml("t-totholz", tabelle(
    [{ titel: "Bundesland", wert: (z) => z.name },
     { titel: "Vfm/ha", num: true, wert: (z) => pz(z.wert) },
     { titel: "Stichprobenfehler", num: true,
       wert: (z) => `± ${pz(z.fehler)} (${pz(z.fehler_relativ)} %)` },
     { titel: "belastbar", wert: (z) => z.belastbar ? "ja" : "nein" }],
    [...daten.eintraege].sort((a, b) => b.wert - a.wert)
  ));
}

BIO.flaechenNormalisieren = flaechenNormalisieren;
BIO.baueTotholz = baueTotholz;
})(window.BIO);
