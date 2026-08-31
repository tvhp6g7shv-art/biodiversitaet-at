/* ===========================================================================
   Biodiversitäts-Dashboard Österreich — Themenstrang: wald
   ---------------------------------------------------------------------------
   Wird nach js/kern.js geladen; die Helfer kommen aus window.BIO.
   =========================================================================== */
(function (BIO) {
"use strict";
const { stil, zahl, pz, basis, achse, tabelle, setzeText, setzeHtml,
        diagramme, schrift, balkenGitter, kategorieLabel, balkenBreite, balkenHoehe, hoverDunkler } = BIO;

/* --- 07 — Waldfläche: Österreich und seine Nachbarn ------------------
   Liegende Balken, Veränderung der Waldfläche seit 1990 in Prozent.

   WARUM VERÄNDERUNG UND NICHT FLÄCHE: Deutschland hat dreimal so viel
   Wald wie Österreich und Liechtenstein ein Tausendstel davon. Absolute
   Flächen nebeneinander sagen über die Entwicklung nichts und machen die
   kleinen Länder unsichtbar. Prozent macht sie vergleichbar.

   WARUM DIESER DATENSATZ: `for_area` ist der einzige geprüfte
   Biodiversitätsdatensatz, der auch die Nicht-EU-Nachbarn Schweiz und
   Liechtenstein mit echten Werten führt. Bei den Schutzgebieten sind beide
   zwar als Dimension gelistet, aber ohne Daten — wer das übersieht, baut
   eine Nachbarschaftsgrafik mit zwei stillen Lücken.

   ÖSTERREICH IST HERVORGEHOBEN, der Rest ist Kontext. Ein Ranking, in dem
   alle Balken gleich aussehen, zwingt zum Suchen.

   ZUR NULLLINIE: Sie ist hier bedeutungstragend — links davon schrumpft
   der Wald, rechts wächst er. Deshalb steht sie als eigene Achslinie und
   nicht nur als Rasterlinie. */

function baueWald(daten) {
  const S = schrift();
  if (!daten?.eintraege?.length) return;
  const abschnitt = document.getElementById("s-wald");
  if (abschnitt) abschnitt.style.display = "";

  const feld = document.getElementById("c-wald");
  if (!feld) return;
  const d = echarts.getInstanceByDom(feld) || echarts.init(feld, null, { renderer: "svg" });
  if (!diagramme.includes(d)) diagramme.push(d);

  const eintraege = daten.eintraege;
  const hell = stil("--viz-series-3");
  const dunkel = stil("--viz-series-1");

  setzeText("u-wald",
    `Veränderung der Waldfläche ${daten.von} bis ${daten.bis} · ` +
    `Österreich und seine acht Nachbarn`);
  setzeText("h-wald", daten.hinweis ?? "");

  /* Eng braucht jede Kategorie eine eigene Zeile fuer ihren Namen.
     Die Kartenhoehe kommt deshalb aus der Zahl der Kategorien und
     nicht aus dem CSS — sonst schiebt ECharts die Zeilen enger
     zusammen, als der Name hoch ist, und die Namen kleben am
     Balken der Zeile darueber. Muss VOR setOption stehen. */
  balkenHoehe(d, feld, eintraege.length, 2);

  d.setOption({
    ...basis(),
    grid: { ...balkenGitter(feld, { left: 128, right: 72 }), top: 12 },
    tooltip: {
      ...basis().tooltip, trigger: "axis",
      axisPointer: { type: "shadow", shadowStyle: { color: stil("--viz-grid"), opacity: 0.35 } },
      formatter: (p) => {
        const e = eintraege[p[0].dataIndex];
        if (e.nur_ein_jahr) {
          return `<strong>${e.name}</strong><br>` +
            `<span style="color:${stil("--viz-muted")}">Nur ein Stützjahr ` +
            `(${e.bis}) gemeldet — keine Veränderung berechenbar</span>`;
        }
        return `<strong>${e.name}</strong><br>` +
          `<strong>${e.veraenderung > 0 ? "+" : ""}${pz(e.veraenderung)} %</strong> ` +
          `seit ${e.von}<br>` +
          `<span style="color:${stil("--viz-muted")}">` +
          `${zahl(Math.round(e.flaeche_von))} → ${zahl(Math.round(e.flaeche_bis))} ` +
          `Tausend Hektar</span>`;
      },
    },
    xAxis: { ...achse(), type: "value",
      axisLine: { show: false },
      axisLabel: { hideOverlap: true, color: stil("--viz-muted"),
                   fontSize: S.achse,
                   formatter: (v) => (v > 0 ? "+" : "") + v + " %" } },
    yAxis: { ...achse(), type: "category", inverse: true,
      data: eintraege.map((e) => e.name), splitLine: { show: false },
      axisLabel: { fontSize: S.serie, margin: 12,
                   color: stil("--viz-text-2"),
                   ...kategorieLabel(feld, 128, eintraege.length) } },
    series: [{
      type: "bar", name: "Veränderung", barWidth: balkenBreite(feld, "58%", eintraege.length),
      data: eintraege.map((e) => ({
        value: e.veraenderung,
        itemStyle: {
          color: e.hervorgehoben ? dunkel : hell,
          borderRadius: e.veraenderung >= 0 ? [0, 4, 4, 0] : [4, 0, 0, 4],
        },
        emphasis: hoverDunkler(e.hervorgehoben ? dunkel : hell),
      })),
      label: { show: true, position: "right", distance: 8,
               color: stil("--viz-text-2"), fontSize: S.label,
               formatter: (p) => (p.value > 0 ? "+" : "") + pz(p.value) + " %" },
      /* Nulllinie sichtbar machen: Sie trennt Wachstum von Rückgang. */
      markLine: {
        silent: true, symbol: "none",
        lineStyle: { color: stil("--viz-axis"), width: 1 },
        label: { show: false },
        data: [{ xAxis: 0 }],
      },
    }],
  }, { replaceMerge: ["series", "xAxis", "yAxis"] });

  const at = daten.oesterreich;
  if (at) {
    /* 28.08.2026 — der Schlusssatz („Dass die Fläche wächst, sagt nichts
       darüber, was auf ihr wächst") ist entfallen. Die Einordnung
       darunter sagt dasselbe, nur konkret: „eine Fichtenmonokultur zählt
       so viel wie ein Auwald". Von zwei Fassungen desselben Gedankens
       bleibt die mit dem Bild. */
    setzeHtml("n-wald",
      `Österreichs Waldfläche wuchs zwischen ${at.von} und ${at.bis} um ` +
      `<strong>${pz(at.veraenderung)} %</strong> auf ${zahl(Math.round(at.flaeche_bis))} ` +
      `Tausend Hektar — Platz ${daten.rang} von ${daten.anzahl} im ` +
      `Nachbarschaftsvergleich.`);
  }

  setzeHtml("t-wald", tabelle(
    [{ titel: "Land", wert: (z) => z.name },
     { titel: `${daten.von} (Tsd. ha)`, num: true,
       wert: (z) => z.nur_ein_jahr ? "–" : zahl(Math.round(z.flaeche_von)) },
     { titel: `${daten.bis} (Tsd. ha)`, num: true,
       wert: (z) => zahl(Math.round(z.flaeche_bis)) },
     { titel: "Veränderung", num: true,
       wert: (z) => z.nur_ein_jahr ? "–"
         : (z.veraenderung > 0 ? "+" : "") + pz(z.veraenderung) + " %" }],
    eintraege
  ));
}

BIO.baueWald = baueWald;
})(window.BIO);
