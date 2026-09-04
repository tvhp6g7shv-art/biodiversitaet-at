/* ===========================================================================
   Biodiversitäts-Dashboard Österreich — Themenstrang: schutzgebiete
   ---------------------------------------------------------------------------
   Wird nach js/kern.js geladen; die Helfer kommen aus window.BIO.
   =========================================================================== */
(function (BIO) {
"use strict";
const { stil, zahl, pz, basis, achse, tabelle, setzeText, setzeHtml,
        diagramme, schrift, istSchmal } = BIO;

/* --- 01 — Schutzgebiete: die Kurve steht still ------------------------
   Eine Linie, 2011–2023, plus eine waagrechte Marke beim Ziel von 30 %.
   DIE MARKE HEISST „EU-weites Ziel", und das ist keine Kosmetik: Die
   30 % der EU-Biodiversitätsstrategie gelten der EU ALS GANZES, nicht
   jedem Mitgliedstaat. Ohne das Wort las sich die Grafik als „Österreich
   verfehlt sein Ziel" — eine Aussage, die die Daten nicht hergeben.
   Angeglichen am 04.09.2026 an den Abschnitt `schutzherkunft` darunter,
   der denselben Vorbehalt in seiner Hinweiszeile trägt.

   ZUR ACHSE, weil die Frage kommen wird: Sie beginnt NICHT bei null.
   Das ist hier nicht Schönfärberei, sondern das Gegenteil — die Aussage
   ist der Abstand zum Ziel, nicht die absolute Größe. Bei einer Achse
   von 0 bis 30 läge die gesamte Reihe als flacher Strich ganz oben und
   der fehlende Rest wäre unsichtbar. Die Zielmarke bei 30 verankert die
   Skala stattdessen an der Größe, um die es geht.

   Untergrenze 26, Schrittweite 1: damit ist jede Achsenzahl ein
   Vielfaches der Schrittweite und die Zielmarke fällt exakt auf einen
   Teilstrich. Ohne feste Schrittweite lässt ECharts überzählige
   Beschriftungen weg und erzeugt Folgen wie 26, 28, 31.

   KEIN Flächenverlauf unter der Linie. Eine gefüllte Fläche von 26 bis
   zur Linie suggeriert eine Menge, die es nicht gibt — die Fläche unter
   einem abgeschnittenen Nullpunkt bedeutet nichts. */

const ACHSE_MIN = 26;
const ACHSE_MAX = 31;

function baueSchutzgebiete(daten) {
  const S = schrift();
  if (!daten?.punkte?.length) return;
  const abschnitt = document.getElementById("s-schutzgebiete");
  if (abschnitt) abschnitt.style.display = "";

  const feld = document.getElementById("c-schutzgebiete");
  if (!feld) return;
  const d = echarts.getInstanceByDom(feld) || echarts.init(feld, null, { renderer: "svg" });
  if (!diagramme.includes(d)) diagramme.push(d);

  const punkte = daten.punkte;
  const jahre = punkte.map((p) => String(p.jahr));

  setzeText("u-schutzgebiete",
    `Anteil der Landesfläche unter Schutz · ${daten.beginn} bis ${daten.stand}` +
    (daten.jahre_still ? ` · seit ${daten.stillstand_seit} unverändert` : ""));
  setzeText("h-schutzgebiete", daten.hinweis ?? "");

  d.setOption({
    ...basis(),
    grid: { left: 8, right: istSchmal(feld) ? 16 : 52, top: 26, bottom: 8,
            containLabel: true },
    tooltip: {
      ...basis().tooltip, trigger: "axis",
      axisPointer: { type: "line", lineStyle: { color: stil("--viz-grid"), width: 1 } },
      formatter: (p) => {
        const punkt = punkte[p[0].dataIndex];
        return `<strong>${punkt.jahr}</strong><br>` +
          `${pz(punkt.prozent)} % der Landesfläche` +
          (punkt.km2 ? `<br><span style="color:${stil("--viz-muted")}">` +
            `${zahl(punkt.km2)} km²</span>` : "");
      },
    },
    xAxis: { ...achse(), type: "category", data: jahre, boundaryGap: false,
             splitLine: { show: false } },
    yAxis: { ...achse(), type: "value",
             min: ACHSE_MIN, max: ACHSE_MAX, interval: 1,
             axisLine: { show: false },
             axisLabel: { hideOverlap: true, color: stil("--viz-muted"),
                          fontSize: S.achse, formatter: (v) => v + " %" } },
    series: [{
      type: "line", name: "Anteil unter Schutz", smooth: false,
      data: punkte.map((p) => p.prozent),
      lineStyle: { color: stil("--viz-series-1"), width: 2.5 },
      itemStyle: { color: stil("--viz-series-1") },
      symbol: "circle", symbolSize: 6,
      /* Endbeschriftung nur, wenn rechts Platz dafür freigehalten wurde.
         Über `endEtikett` statt über `endLabel` — siehe kern.js, der
         `endLabel` stand hier bis 04.09.2026 links am ersten Punkt und
         zeigte 27,5 % statt 29,3 %. */
      markPoint: BIO.endEtikett(punkte.map((p) => p.prozent), feld,
        (r) => pz(r.value) + " %"),
      markLine: {
        silent: true, symbol: "none",
        lineStyle: { color: stil("--viz-muted"), width: 1, type: "dashed" },
        label: {
          position: istSchmal(feld) ? "insideEndTop" : "insideStartTop",
          color: stil("--viz-muted"), fontSize: S.achse,
          formatter: `EU-weites Ziel ${daten.zieljahr}: ${pz(daten.ziel, 0)} %`,
        },
        data: [{ yAxis: daten.ziel }],
      },
    }],
  }, { replaceMerge: ["series", "xAxis", "yAxis"] });

  setzeHtml("t-schutzgebiete", tabelle(
    [{ titel: "Jahr", wert: (z) => z.jahr },
     { titel: "Anteil", num: true, wert: (z) => pz(z.prozent) + " %" },
     { titel: "Fläche", num: true, wert: (z) => z.km2 ? zahl(z.km2) + " km²" : "–" },
     { titel: "Abstand zum EU-Ziel", num: true,
       wert: (z) => pz(Math.round((30 - z.prozent) * 10) / 10) + " Punkte" }],
    punkte
  ));
}

BIO.baueSchutzgebiete = baueSchutzgebiete;
})(window.BIO);
