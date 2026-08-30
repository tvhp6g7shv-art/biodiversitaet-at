/* ===========================================================================
   Biodiversitäts-Dashboard Österreich — Themenstrang: baumarten
   ---------------------------------------------------------------------------
   Wird nach js/kern.js geladen; die Helfer kommen aus window.BIO.
   =========================================================================== */
(function (BIO) {
"use strict";
const { stil, zahl, pz, basis, achse, tabelle, setzeText, setzeHtml,
        diagramme, schrift, istSchmal, balkenGitter, kategorieLabel,
        balkenBreite, balkenHoehe, legende, hoverDunkler } = BIO;

/* --- Nadel- und Laubholz im bewirtschafteten Wald ----------------------
   Vier gestapelte Balken, einer je Erhebungsperiode, auf 100 % normiert.
   Von oben nach unten gelesen ist das die Zeitachse: 1992/96 oben,
   2018/23 unten.

   WARUM GESTAPELT UND NICHT ALS LINIEN: Die drei Anteile sind Teile
   EINES Ganzen — der bewirtschafteten Waldfläche. Das ist keine
   Nebensache, sondern der Kern des Abschnitts: Genau dieses Ganze hat
   die Quelle zwischen den Perioden gewechselt (siehe Notiz). Ein
   gestapelter Balken zeigt das Ganze mit; drei Linien verlieren es.

   ZUR FARBWAHL: `--viz-series-1/2/3`. Das sind Kategorientöne ohne
   Wertung — Nadelholz ist nicht „schlechter" als Laubholz, und die
   Grafik darf das nicht suggerieren. Die Dreierstufung series-1/2/3 ist
   die einzige, die in allen vier ausgelieferten Paletten monoton fällt;
   series-4 ist in der Salbei-Palette heller als series-1.

   KEINE BESCHRIFTUNG IN DEN SEGMENTEN: Das kleinste ist 8,5 % breit.
   Auf schmalen Fenstern passt dort keine Zahl hinein, und eine Zahl,
   die nur manchmal erscheint, liest sich als Fehler. Werte im Tooltip
   und in der Tabelle. */

const FARBEN = ["--viz-series-1", "--viz-series-2", "--viz-series-3"];

function baueBaumarten(daten) {
  const S = schrift();
  if (!daten?.reihen?.length) return;
  const abschnitt = document.getElementById("s-baumarten");
  if (abschnitt) abschnitt.style.display = "";

  const feld = document.getElementById("c-baumarten");
  if (!feld) return;
  const d = echarts.getInstanceByDom(feld) || echarts.init(feld, null, { renderer: "svg" });
  if (!diagramme.includes(d)) diagramme.push(d);

  const perioden = daten.perioden;
  const reihen = daten.reihen;

  setzeText("u-baumarten",
    `Anteil an der bewirtschafteten Waldfläche · Österreichische Waldinventur ` +
    `${perioden[0]} bis ${perioden[perioden.length - 1]}`);
  setzeText("h-baumarten", daten.hinweis ?? "");

  balkenHoehe(d, feld, perioden.length, 36);

  /* Zeile für Zeile: je Periode die drei Anteile und die drei Flächen.
     Wird vom Tooltip und von der Tabelle gebraucht. */
  const zeilen = perioden.map((periode, i) => ({
    periode,
    anteile: reihen.map((r) => r.werte[i].anteil),
    flaechen: reihen.map((r) => r.werte[i].flaeche_tsd_ha),
    gesamt: reihen.reduce((s, r) => s + r.werte[i].flaeche_tsd_ha, 0),
  }));

  d.setOption({
    ...basis(),
    grid: { ...balkenGitter(feld, { left: 96, right: 60 }), top: 46 },
    legend: legende(feld, {
      top: 0, left: istSchmal(feld) ? 0 : 96,
      itemWidth: 11, itemHeight: 11, itemGap: 14,
      data: reihen.map((r) => r.name),
      textStyle: { color: stil("--viz-text-2"), fontSize: S.serie },
    }),
    tooltip: {
      ...basis().tooltip, trigger: "axis",
      axisPointer: { type: "shadow", shadowStyle: { color: stil("--viz-grid"), opacity: 0.35 } },
      formatter: (p) => {
        const z = zeilen[p[0].dataIndex];
        return `<strong>Erhebung ${z.periode}</strong><br>` +
          `<span style="color:${stil("--viz-muted")}">` +
          `${zahl(z.gesamt)} Tsd. Hektar bewirtschafteter Wald</span><br>` +
          p.map((r, i) => `${r.marker} ${r.seriesName}&nbsp;&nbsp;` +
            `<strong>${pz(r.value, 1)} %</strong> ` +
            `<span style="color:${stil("--viz-muted")}">` +
            `(${zahl(z.flaechen[i])} Tsd. ha)</span>`).join("<br>");
      },
    },
    xAxis: { ...achse(), type: "value", max: 100, axisLine: { show: false },
      axisLabel: { hideOverlap: true, color: stil("--viz-muted"),
                   fontSize: S.achse, formatter: (v) => v + " %" } },
    yAxis: { ...achse(), type: "category", inverse: true,
      data: perioden, splitLine: { show: false },
      axisLabel: { color: stil("--viz-text-2"), fontSize: S.serie, margin: 12,
                   ...kategorieLabel(feld, 96, perioden.length) } },
    series: reihen.map((r, k) => ({
      name: r.name, type: "bar", stack: "wald",
      barWidth: balkenBreite(feld, "56%"),
      data: zeilen.map((z) => z.anteile[k]),
      itemStyle: {
        color: stil(FARBEN[k]),
        borderRadius: k === 0 ? [4, 0, 0, 4]
          : (k === reihen.length - 1 ? [0, 4, 4, 0] : 0),
        borderColor: stil("--viz-surface"), borderWidth: 2,
      },
      emphasis: hoverDunkler(stil(FARBEN[k])),
      label: { show: false },
    })),
  }, { replaceMerge: ["series", "xAxis", "yAxis", "legend"] });

  /* Die Notiz trägt den Befund, den der Balken NICHT zeigen kann: dass
     die veröffentlichten Prozentwerte der ersten und der letzten Periode
     nicht gegen dasselbe Ganze gerechnet sind. Ohne sie liest sich die
     Grafik als Widerspruch zu jeder Zahl, die anderswo zu finden ist. */
  const n = daten.nennerwechsel;
  if (n) {
    setzeHtml("n-baumarten",
      `Die Waldinventur selbst weist für die letzte Erhebung ` +
      `<strong>${pz(n.veroeffentlicht_letzte, 1)} %</strong> Nadelholz aus, ` +
      `nicht ${pz(daten.nadel_jetzt, 1)} % — sie rechnet dort gegen die ` +
      `gesamte Waldfläche statt gegen den bewirtschafteten Wald. Wer beide ` +
      `veröffentlichten Werte nebeneinanderstellt, sieht einen Rückgang von ` +
      `<strong>${pz(n.scheinbarer_rueckgang, 1)}</strong> Prozentpunkten. ` +
      `Gegen ein gleichbleibendes Ganzes gerechnet sind es ` +
      `<strong>${pz(n.tatsaechlicher_rueckgang, 1)}</strong>.`);
  }

  setzeHtml("t-baumarten", tabelle(
    [{ titel: "Erhebung", wert: (z) => z.periode },
     ...reihen.map((r, i) => ({
       titel: r.name, num: true,
       wert: (z) => pz(z.anteile[i], 1) + " %",
     })),
     { titel: "Bewirtschafteter Wald", num: true,
       wert: (z) => zahl(z.gesamt) + " Tsd. ha" }],
    zeilen
  ));
}

BIO.baueBaumarten = baueBaumarten;
})(window.BIO);
