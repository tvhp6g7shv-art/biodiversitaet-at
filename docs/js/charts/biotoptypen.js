/* ===========================================================================
   Biodiversitäts-Dashboard Österreich — Themenstrang: biotoptypen
   ---------------------------------------------------------------------------
   Wird nach js/kern.js geladen; die Helfer kommen aus window.BIO.
   =========================================================================== */
(function (BIO) {
"use strict";
const { stil, zahl, pz, basis, achse, tabelle, setzeText, setzeHtml,
        diagramme, schrift, hoverDunkler } = BIO;

/* --- 06 — Rote Liste der Biotoptypen ---------------------------------
   Liegende Balken, eine Zeile je Gefährdungsstufe, in der Reihenfolge der
   IUCN-Skala von „völlig vernichtet" bis „nicht gefährdet".

   WARUM NICHT EIN GESTAPELTER BALKEN wie beim Erhaltungszustand: Dort
   waren es zwei vergleichbare Gruppen, deren Zusammensetzung man
   gegeneinander lesen sollte. Hier gibt es nur EINE Verteilung. Ein
   einzelner gestapelter Balken zwingt das Auge, Segmentlängen ohne
   gemeinsame Grundlinie zu vergleichen — fünf getrennte Balken auf einer
   Achse sind schlicht ablesbar.

   ZUR REIHENFOLGE: Nicht nach Größe sortiert, sondern nach Schweregrad.
   Die Skala ist geordnet, und eine Sortierung nach Häufigkeit würde
   „stark gefährdet" und „gefährdet" (beide 123) willkürlich trennen.

   ZUR FARBE: Eine sequenzielle Rampe von dunkel nach hell, nicht die
   Ampel. Die Stufen sind Grade derselben Sache, keine Zustandsurteile mit
   Handlungsbezug — und fünf Ampelfarben wären ohnehin Konfetti.
   „Ohne Angabe" bekommt den Rasterton: keine Stufe, sondern eine Lücke. */

const FARBEN = {
  RE: "--viz-seq-6", CR: "--viz-seq-5", EN: "--viz-seq-4",
  VU: "--viz-seq-3", LC: "--viz-seq-2", "—": "--viz-grid",
};

function baueBiotoptypen(daten) {
  const S = schrift();
  if (!daten?.stufen?.length) return;
  const abschnitt = document.getElementById("s-biotoptypen");
  if (abschnitt) abschnitt.style.display = "";

  const feld = document.getElementById("c-biotoptypen");
  if (!feld) return;
  const d = echarts.getInstanceByDom(feld) || echarts.init(feld, null, { renderer: "svg" });
  if (!diagramme.includes(d)) diagramme.push(d);

  const stufen = daten.stufen;

  setzeText("u-biotoptypen",
    `${zahl(daten.bewertet)} bewertete Biotoptypen nach Gefährdungsstufe · ` +
    `Teilbände ${daten.erster_band} bis ${daten.stand}`);
  setzeText("h-biotoptypen", daten.hinweis ?? "");

  d.setOption({
    ...basis(),
    grid: { ...BIO.balkenGitter(feld, { left: 168, right: 72 }), top: 12 },
    tooltip: {
      ...basis().tooltip, trigger: "axis",
      axisPointer: { type: "shadow", shadowStyle: { color: stil("--viz-grid"), opacity: 0.35 } },
      formatter: (p) => {
        const s = stufen[p[0].dataIndex];
        return `<strong>${s.name}</strong>` +
          (s.kuerzel !== "—" ? ` <span style="color:${stil("--viz-muted")}">` +
            `(${s.kuerzel})</span>` : "") + `<br>` +
          `${zahl(s.anzahl)} Biotoptypen · <strong>${pz(s.anteil)} %</strong> ` +
          `<span style="color:${stil("--viz-muted")}">der ${zahl(daten.bewertet)} ` +
          `bewerteten</span>`;
      },
    },
    xAxis: { ...achse(), type: "value", min: 0, axisLine: { show: false },
      axisLabel: { hideOverlap: true, color: stil("--viz-muted"),
                   fontSize: S.achse } },
    yAxis: { ...achse(), type: "category", inverse: true,
      data: stufen.map((s) => s.name), splitLine: { show: false },
      axisLabel: { color: stil("--viz-text-2"), fontSize: S.serie, margin: 12,
                   ...BIO.kategorieLabel(feld, 168, stufen.length) } },
    series: [{
      type: "bar", name: "Biotoptypen", barWidth: "58%",
      data: stufen.map((s) => ({
        value: s.anzahl,
        itemStyle: { color: stil(FARBEN[s.kuerzel] || "--viz-series-4"),
                     borderRadius: [0, 4, 4, 0] },
        emphasis: hoverDunkler(stil(FARBEN[s.kuerzel] || "--viz-series-4")),
      })),
      label: { show: true, position: "right", distance: 8,
               color: stil("--viz-text-2"), fontSize: S.label,
               formatter: (p) => zahl(p.value) },
    }],
  }, { replaceMerge: ["series", "xAxis", "yAxis"] });

  setzeHtml("n-biotoptypen",
    `Zusammen sind <strong>${zahl(daten.gefaehrdet)} von ${zahl(daten.bewertet)}</strong> ` +
    `Biotoptypen (${pz(daten.anteil_gefaehrdet)} %) in einer Gefährdungsstufe. ` +
    `${zahl(daten.vernichtet)} gelten als völlig vernichtet. ` +
    `Die übrigen ${zahl(daten.nicht_bewertet)} der insgesamt ${zahl(daten.gesamt)} ` +
    `Biotoptypen galten als nicht besonders schutzwürdig und wurden gar nicht ` +
    `erst eingestuft.`);

  setzeHtml("t-biotoptypen", tabelle(
    [{ titel: "Stufe", wert: (z) => z.name },
     { titel: "Kürzel", wert: (z) => z.kuerzel },
     { titel: "Biotoptypen", num: true, wert: (z) => zahl(z.anzahl) },
     { titel: "Anteil", num: true, wert: (z) => pz(z.anteil) + " %" }],
    stufen
  ));
}

BIO.baueBiotoptypen = baueBiotoptypen;
})(window.BIO);
