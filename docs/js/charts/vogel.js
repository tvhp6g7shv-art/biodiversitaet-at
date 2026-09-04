/* ===========================================================================
   Biodiversitäts-Dashboard Österreich — Themenstrang: vogel
   ---------------------------------------------------------------------------
   Wird nach js/kern.js geladen; die Helfer kommen aus window.BIO.
   =========================================================================== */
(function (BIO) {
"use strict";
const { stil, pz, basis, achse, tabelle, setzeText, setzeHtml,
        diagramme, schrift, istSchmal } = BIO;

/* --- 02 — Feld- und Wiesenvögel --------------------------------------
   Eine Linie, 1998–2023, Basis 1998 = 100.

   ZUR ACHSE: Hier beginnt sie bei null — anders als bei den
   Schutzgebieten und aus demselben Grund. Die Aussage ist diesmal die
   GRÖSSE des Rückgangs („fast die Hälfte weg"), nicht der Abstand zu
   einer Zielmarke. Ein abgeschnittener Nullpunkt würde den Absturz
   dramatisieren, statt ihn zu zeigen.

   Der Knickpunkt kommt aus den Daten, nicht aus dem Auge: die Pipeline
   sucht das erste Jahr, ab dem der Index seinen Tiefbereich nicht mehr
   verlässt, und liefert es als `knick`. Die Marke steht dort, weil der
   Bericht zwei Phasen beschreibt — starker Rückgang, dann flach auf
   niedrigem Niveau — und ein Betrachter sonst raten müsste, wo die eine
   in die andere übergeht.

   Die Grundlinie bei 100 ist die Basis, nicht ein Ziel. Sie ist deshalb
   beschriftet mit dem Jahr, nicht mit einem Sollwert. */

function baueVogel(daten) {
  const S = schrift();
  if (!daten?.punkte?.length) return;
  const abschnitt = document.getElementById("s-vogel");
  if (abschnitt) abschnitt.style.display = "";

  const feld = document.getElementById("c-vogel");
  if (!feld) return;
  const d = echarts.getInstanceByDom(feld) || echarts.init(feld, null, { renderer: "svg" });
  if (!diagramme.includes(d)) diagramme.push(d);

  const punkte = daten.punkte;

  const mitEu = !!daten.eu_vorhanden;

  /* 25.08.2026 — „Bestandsindex" und „Offenland" raus. Beides sind
     Begriffe aus dem Bericht, nicht aus der Alltagssprache; was der Index
     misst und was er nicht misst, steht ohnehin in der Hinweiszeile
     darunter. Die Basis bleibt hier, weil die Achse sie zeigt. */
  setzeText("u-vogel",
    `${daten.arten_anzahl} Vogelarten auf Feldern und Wiesen · ` +
    `${daten.beginn} bis ${daten.stand}, ${daten.beginn} = 100` +
    (mitEu ? ` · EU-Vergleich bis ${daten.eu_stand}` : ""));
  setzeText("h-vogel", daten.hinweis ?? "");

  const knickIndex = punkte.findIndex((p) => p.jahr === daten.knick);

  d.setOption({
    ...basis(),
    /* Mit Legende oben braucht das Gitter mehr Kopfraum, sonst klebt die
       Legende an der obersten Rasterlinie. */
    grid: { left: 8, right: istSchmal(feld) ? 16 : 46,
            top: mitEu ? 44 : 26, bottom: 8, containLabel: true },
    legend: mitEu ? BIO.legende(feld, {
      top: 0, left: 0, itemWidth: 22, itemHeight: 2, itemGap: 16,
      data: ["Österreich", "EU-27"],
      textStyle: { color: stil("--viz-text-2"), fontSize: S.serie },
    }) : undefined,
    tooltip: {
      ...basis().tooltip, trigger: "axis",
      axisPointer: { type: "line", lineStyle: { color: stil("--viz-grid"), width: 1 } },
      formatter: (p) => {
        const punkt = punkte[p[0].dataIndex];
        const zeilen = [`<strong>${punkt.jahr}</strong>`];
        if (punkt.index !== null && punkt.index !== undefined) {
          const diff = Math.round((punkt.index - 100) * 10) / 10;
          zeilen.push(`Österreich <strong>${pz(punkt.index)}</strong>` +
            ` <span style="color:${stil("--viz-muted")}">(${diff < 0 ? "−" : "+"}` +
            `${pz(Math.abs(diff))} gegenüber ${daten.beginn})</span>`);
        }
        if (punkt.eu !== null && punkt.eu !== undefined) {
          zeilen.push(`EU-27 <strong>${pz(punkt.eu)}</strong>`);
        }
        return zeilen.join("<br>");
      },
    },
    xAxis: { ...achse(), type: "category", boundaryGap: false,
             data: punkte.map((p) => String(p.jahr)),
             splitLine: { show: false } },
    yAxis: { ...achse(), type: "value", min: 0, max: 110, interval: 20,
             axisLine: { show: false },
             axisLabel: { hideOverlap: true, color: stil("--viz-muted"),
                          fontSize: S.achse } },
    series: [{
      type: "line", name: "Österreich", smooth: false,
      /* `connectNulls: false` ist hier entscheidend: Die österreichische
         Reihe beginnt 1998 und endet 2023, die EU-Reihe läuft von 1990 bis
         2024. Würde ECharts die Lücken überbrücken, zöge es die AT-Linie
         waagrecht in Jahre hinein, für die es keine Erhebung gibt. */
      connectNulls: false,
      data: punkte.map((p) => p.index),
      lineStyle: { color: stil("--viz-series-1"), width: 2.5 },
      itemStyle: { color: stil("--viz-series-1") },
      symbol: "circle", symbolSize: 5,
      /* `endEtikett` statt `endLabel` — siehe kern.js. Wichtig hier: Die
         AT-Reihe endet VOR der EU-Reihe, die letzten Einträge sind `null`.
         `endEtikett` sucht deshalb den letzten Wert, der keiner ist. */
      markPoint: BIO.endEtikett(punkte.map((p) => p.index), feld,
        (r) => pz(r.value)),
      markLine: {
        silent: true, symbol: "none",
        lineStyle: { color: stil("--viz-muted"), width: 1, type: "dashed" },
        label: { position: "insideStartTop", color: stil("--viz-muted"),
                 fontSize: S.achse, formatter: `Stand ${daten.beginn}` },
        data: [{ yAxis: 100 }],
      },
      /* Senkrechte Marke am Knickpunkt. `markArea` statt einer zweiten
         markLine: die Fläche sagt „ab hier flach", eine Linie sagt nur
         „hier ist etwas". Sehr blass, damit sie die Linie nicht schlägt. */
      markArea: knickIndex >= 0 ? {
        silent: true,
        itemStyle: { color: stil("--viz-grid"), opacity: 0.45 },
        label: {
          show: !istSchmal(feld), position: "insideTop",
          color: stil("--viz-muted"), fontSize: S.achse,
          formatter: `ab ${daten.knick} auf niedrigem Niveau`,
        },
        data: [[{ xAxis: String(daten.knick) },
                { xAxis: String(daten.stand) }]],
      } : undefined,
    },
    /* EU-Linie als Kontext, nicht als Hauptaussage: dünner, gestrichelt,
       ohne Punkte. Sie soll die österreichische Kurve einordnen, nicht mit
       ihr um Aufmerksamkeit ringen. */
    ...(mitEu ? [{
      type: "line", name: "EU-27", smooth: false, connectNulls: false,
      data: punkte.map((p) => p.eu),
      lineStyle: { color: stil("--viz-series-2"), width: 1.5, type: "dashed" },
      itemStyle: { color: stil("--viz-series-2") },
      symbol: "none",
      /* Diese Linie zeichnet keine Symbole (`symbol: "none"`), ein
         Datenetikett hätte keinen Anker — deshalb `markPoint`. */
      markPoint: BIO.endEtikett(punkte.map((p) => p.eu), feld,
        (r) => pz(r.value), stil("--viz-muted")),
    }] : []),
    ],
  }, { replaceMerge: ["series", "xAxis", "yAxis", "legend"] });

  /* Der Vergleichssatz gehört unter die Grafik, nicht in den Untertitel:
     Er ist ein Befund, keine Beschreibung der Achsen. */
  if (daten.eu_vergleich) {
    const v = daten.eu_vergleich;
    setzeHtml("n-vogel",
      `${v.jahr} steht Österreich bei <strong>${pz(v.at)}</strong>, die EU-27 bei ` +
      `<strong>${pz(v.eu)}</strong> — beide auf ${daten.beginn} = 100 gerechnet. ` +
      `Der Rückgang fällt hier also um ${pz(Math.abs(v.differenz))} Punkte ` +
      `${v.differenz < 0 ? "stärker" : "schwächer"} aus als im europäischen Mittel.`);
  }

  setzeHtml("t-vogel", tabelle(
    [{ titel: "Jahr", wert: (z) => z.jahr },
     { titel: "Österreich", num: true,
       wert: (z) => z.index === null || z.index === undefined ? "–" : pz(z.index) },
     ...(mitEu ? [{ titel: "EU-27", num: true,
       wert: (z) => z.eu === null || z.eu === undefined ? "–" : pz(z.eu) }] : []),
     { titel: `AT gegenüber ${daten.beginn}`, num: true,
       wert: (z) => z.index === null || z.index === undefined ? "–"
         : pz(Math.round((z.index - 100) * 10) / 10) + " Punkte" }],
    punkte
  ));
}

BIO.baueVogel = baueVogel;
})(window.BIO);
