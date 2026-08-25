/* ===========================================================================
   Biodiversitäts-Dashboard Österreich — Themenstrang: biolandbau
   ---------------------------------------------------------------------------
   Wird nach js/kern.js geladen; die Helfer kommen aus window.BIO.
   =========================================================================== */
(function (BIO) {
"use strict";
const { stil, zahl, pz, basis, achse, tabelle, setzeText, setzeHtml,
        diagramme, schrift, istSchmal, balkenGitter, kategorieLabel,
        hoverDunkler } = BIO;

/* --- 08 — Biologische Landwirtschaft im europäischen Vergleich -------
   Liegende Balken, ein Land je Zeile, absteigend nach Anteil.

   WARUM RANGLISTE UND NICHT ZIELMARKE: Die Bio-Fläche hat wie die
   Schutzgebiete ein Ziel aus der Biodiversitäts-Strategie 2030+ (35 %).
   Beide als Linie mit Zielmarke zu zeigen wäre zweimal dieselbe Grafik —
   der Leser sieht dann die Wiederholung und nicht den Inhalt. Hier trägt
   der Ländervergleich die Aussage, und der sagt etwas anderes als „Ziel
   noch nicht erreicht": Österreich liegt an der Spitze.

   Die Zielmarke steht trotzdem drin, als senkrechte Linie. Sie ordnet den
   Spitzenplatz ein — Erster zu sein und das Ziel zu verfehlen ist kein
   Widerspruch, sondern der eigentliche Befund.

   ÖSTERREICH HERVORGEHOBEN, Nachbarn im Mittelton, alle übrigen blass.
   Drei Stufen statt zwei, weil die Frage „wie stehen wir zu den Nachbarn"
   sonst im Feld der 30 Länder untergeht.

   ZUM VERGLEICHSJAHR: Alle Länder im selben Jahr, und zwar dem jüngsten,
   für das Österreich meldet. Ein Ranking auf „das jeweils neueste Jahr je
   Land" stellte Österreichs 2020er-Wert gegen 2024er-Werte anderer. */

function baueBiolandbau(daten) {
  const S = schrift();
  if (!daten?.rangliste?.length) return;
  const abschnitt = document.getElementById("s-biolandbau");
  if (abschnitt) abschnitt.style.display = "";

  const feld = document.getElementById("c-biolandbau");
  if (!feld) return;
  const d = echarts.getInstanceByDom(feld) || echarts.init(feld, null, { renderer: "svg" });
  if (!diagramme.includes(d)) diagramme.push(d);

  const liste = daten.rangliste;
  const dunkel = stil("--viz-series-1");
  const mittel = stil("--viz-series-4");
  const blass  = stil("--viz-series-3");
  const farbe = (e) => e.hervorgehoben ? dunkel : (e.nachbar ? mittel : blass);

  setzeText("u-biolandbau",
    `Anteil an der landwirtschaftlich genutzten Fläche · ${daten.vergleichsjahr} · ` +
    `${daten.anzahl} Meldeländer`);
  setzeText("h-biolandbau", daten.hinweis ?? "");

  d.setOption({
    ...basis(),
    grid: { ...balkenGitter(feld, { left: 118, right: 68 }), top: 24 },
    tooltip: {
      ...basis().tooltip, trigger: "axis",
      axisPointer: { type: "shadow", shadowStyle: { color: stil("--viz-grid"), opacity: 0.35 } },
      formatter: (p) => {
        const e = liste[p[0].dataIndex];
        const platz = p[0].dataIndex + 1;
        return `<strong>${e.name}</strong><br>` +
          `<strong>${pz(e.wert)} %</strong> Bio-Fläche` +
          `<br><span style="color:${stil("--viz-muted")}">Platz ${platz} von ` +
          `${daten.anzahl}${e.nachbar && !e.hervorgehoben ? " · Nachbarland" : ""}</span>`;
      },
    },
    xAxis: { ...achse(), type: "value", min: 0, axisLine: { show: false },
      axisLabel: { hideOverlap: true, color: stil("--viz-muted"),
                   fontSize: S.achse, formatter: (v) => v + " %" } },
    yAxis: { ...achse(), type: "category", inverse: true,
      data: liste.map((e) => e.name), splitLine: { show: false },
      axisLabel: { fontSize: istSchmal(feld) ? S.eng : S.serie, margin: 12,
                   color: stil("--viz-text-2"),
                   ...kategorieLabel(feld, 118, liste.length) } },
    series: [{
      type: "bar", name: "Bio-Anteil", barWidth: "62%",
      data: liste.map((e) => ({
        value: e.wert,
        itemStyle: { color: farbe(e), borderRadius: [0, 4, 4, 0] },
        emphasis: hoverDunkler(farbe(e)),
      })),
      label: { show: true, position: "right", distance: 8,
               color: stil("--viz-text-2"), fontSize: S.label,
               formatter: (p) => pz(p.value) + " %" },
      markLine: {
        silent: true, symbol: "none",
        lineStyle: { color: stil("--viz-muted"), width: 1, type: "dashed" },
        label: { position: "insideEndTop", color: stil("--viz-muted"),
                 fontSize: S.achse,
                 formatter: `Ziel 2030: ${pz(daten.ziel, 0)} %` },
        data: [{ xAxis: daten.ziel }],
      },
    }],
  }, { replaceMerge: ["series", "xAxis", "yAxis"] });

  const at = daten.oesterreich;
  setzeHtml("n-biolandbau",
    `Österreich liegt mit <strong>${pz(at.wert)} %</strong> auf Platz ` +
    `<strong>${daten.rang} von ${daten.anzahl}</strong>` +
    (daten.eu_wert ? `, der EU-Schnitt liegt bei ${pz(daten.eu_wert)} %` : "") +
    `. Auf das Ziel von ${pz(daten.ziel, 0)} % für 2030 fehlen trotzdem ` +
    `${pz(daten.luecke)} Punkte — Spitzenreiter zu sein und das Ziel zu ` +
    `verfehlen schließt einander nicht aus.` +
    (daten.meldeluecke >= 2
      ? ` Der Datensatz reicht bis ${daten.datensatz_bis}; Österreich meldet ` +
        `zuletzt für ${daten.vergleichsjahr}, deshalb ist das das Vergleichsjahr.`
      : ""));

  setzeHtml("t-biolandbau", tabelle(
    [{ titel: "Land", wert: (z) => z.name },
     { titel: "Bio-Anteil", num: true, wert: (z) => pz(z.wert) + " %" },
     { titel: "auf 35 % fehlen", num: true,
       wert: (z) => z.wert >= daten.ziel ? "erreicht"
         : pz(Math.round((daten.ziel - z.wert) * 10) / 10) + " Punkte" }],
    liste
  ));
}

BIO.baueBiolandbau = baueBiolandbau;
})(window.BIO);
