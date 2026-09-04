/* ===========================================================================
   Biodiversitäts-Dashboard Österreich — Themenstrang: falter
   ---------------------------------------------------------------------------
   Wird nach js/kern.js geladen; die Helfer kommen aus window.BIO.
   =========================================================================== */
(function (BIO) {
"use strict";
const { stil, pz, basis, achse, tabelle, setzeText, setzeHtml,
        diagramme, schrift, istSchmal } = BIO;

/* --- 09 — Wiesenfalter, der Verlustpol des Bereichs Tiergruppen -------
   Eine Linie, 1991–2024, Basis 1991 = 100.

   DIESER ABSCHNITT ZEIGT ALS EINZIGER KEINE ÖSTERREICHISCHE ZAHL.
   Eurostat führt für `sdg_15_61` genau ein Gebiet: das EU-Aggregat.
   Eine europäische Zahl als österreichische auszugeben wäre der stillste
   schwere Fehler dieses Abschnitts — deshalb steht „in Europa" im
   Untertitel, nicht nur in der Hinweiszeile darunter. Wer nur die
   Überschrift und die Achse liest, muss es trotzdem mitbekommen.

   ZUR ACHSE: Sie beginnt bei null, wie bei den Feldvögeln und aus
   demselben Grund. Die Aussage ist die GRÖSSE des Rückgangs, nicht der
   Abstand zu einer Zielmarke.

   ZUR GEGLÄTTETEN REIHE: Eurostat liefert beides. Die ungeglättete
   schwankt wetterbedingt zweistellig — 2002 steht bei 103,6, 2024 bei
   44,3 — und erzählt als Dashboard-Linie Wetter statt Bestand. Die
   Glättung steht deshalb im Untertitel, damit niemand die Linie für eine
   Jahreszählung hält.

   DIE HALBIERUNGSMARKE kommt aus den Daten, nicht aus dem Auge: Die
   Pipeline liefert `halbiert` — das erste Jahr mit einem Indexwert von
   50 oder darunter — oder `null`, solange die Reihe darüber liegt. Bei
   52,65 im Jahr 2024 ist sie derzeit `null` und die Marke bleibt aus.
   Das ist Absicht: eine Marke bei 50 ohne Schnittpunkt behauptet eine
   Schwelle, die noch nicht erreicht ist. */

function baueFalter(daten) {
  const S = schrift();
  if (!daten?.punkte?.length) return;
  const abschnitt = document.getElementById("s-falter");
  if (abschnitt) abschnitt.style.display = "";

  const feld = document.getElementById("c-falter");
  if (!feld) return;
  const d = echarts.getInstanceByDom(feld) || echarts.init(feld, null, { renderer: "svg" });
  if (!diagramme.includes(d)) diagramme.push(d);

  const punkte = daten.punkte;
  const halbiertIndex = daten.halbiert
    ? punkte.findIndex((p) => p.jahr === daten.halbiert) : -1;

  setzeText("u-falter",
    `${daten.arten_anzahl} Schmetterlingsarten auf festen Zählstrecken in ` +
    `Europa · ${daten.beginn} bis ${daten.stand}, ${daten.basis} = 100 · geglättet`);
  setzeText("h-falter", daten.hinweis ?? "");

  /* Die große Zahl kommt aus den Daten, nicht aus dem Markup. Stünde sie
     im HTML, wäre sie beim nächsten Eurostat-Lauf still falsch — genau
     der Fehler, der am 26.08.2026 zwei Abschnittsüberschriften erwischt
     hat. `verlust` ist der Abstand zur Basis in Indexpunkten; bei Basis
     100 liest man ihn als Prozent des Ausgangsbestands, so wie es die
     Kennzahlkacheln des Dashboards ohnehin tun. */
  setzeHtml("k-falter",
    `<span class="viz-plakat-zahl">−${pz(daten.verlust, 0)}` +
    `<span class="viz-plakat-einheit">%</span></span>` +
    `<p class="viz-plakat-satz">der Wiesenfalter in Europa sind seit ` +
    `${daten.basis} verschwunden — fast die Hälfte. Der Index steht ` +
    `${daten.stand} bei ${pz(daten.aktuell)} von 100.</p>`);

  d.setOption({
    ...basis(),
    grid: { left: 8, right: istSchmal(feld) ? 16 : 46, top: 26, bottom: 8,
            containLabel: true },
    tooltip: {
      ...basis().tooltip, trigger: "axis",
      axisPointer: { type: "line", lineStyle: { color: stil("--viz-grid"), width: 1 } },
      formatter: (p) => {
        const punkt = punkte[p[0].dataIndex];
        const diff = Math.round((punkt.index - 100) * 10) / 10;
        return `<strong>${punkt.jahr}</strong><br>` +
          `<strong>${pz(punkt.index)}</strong>` +
          ` <span style="color:${stil("--viz-muted")}">(${diff < 0 ? "−" : "+"}` +
          `${pz(Math.abs(diff))} gegenüber ${daten.basis})</span>`;
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
      type: "line", name: "Wiesenfalter in Europa", smooth: false,
      connectNulls: false,
      data: punkte.map((p) => p.index),
      lineStyle: { color: stil("--viz-series-1"), width: 2.5 },
      itemStyle: { color: stil("--viz-series-1") },
      /* Ohne Punkte: 34 Jahreswerte einer geglätteten Reihe ergeben eine
         Perlenkette, die die Kurvenform überdeckt. Der Tooltip trifft
         auch ohne sichtbares Symbol. */
      symbol: "circle", symbolSize: 0, showSymbol: false,
      /* `endEtikett` statt `endLabel`: Diese Linie zeichnet keine Symbole
         (`showSymbol: false`), ein Datenetikett hätte keinen Anker. Der
         `endLabel` stand hier bis 04.09.2026 links auf dem Indexsockel
         100 statt rechts auf dem Endwert. */
      markPoint: BIO.endEtikett(punkte.map((p) => p.index), feld,
        (r) => pz(r.value)),
      markLine: {
        silent: true, symbol: "none",
        lineStyle: { color: stil("--viz-muted"), width: 1, type: "dashed" },
        label: { position: "insideStartTop", color: stil("--viz-muted"),
                 fontSize: S.achse, formatter: `Stand ${daten.basis}` },
        data: [{ yAxis: 100 }],
      },
      markArea: halbiertIndex >= 0 ? {
        silent: true,
        itemStyle: { color: stil("--viz-grid"), opacity: 0.45 },
        label: {
          show: !istSchmal(feld), position: "insideTop",
          color: stil("--viz-muted"), fontSize: S.achse,
          formatter: `ab ${daten.halbiert} unter der Hälfte`,
        },
        data: [[{ xAxis: String(daten.halbiert) },
                { xAxis: String(daten.stand) }]],
      } : undefined,
    }],
  }, { replaceMerge: ["series", "xAxis", "yAxis", "legend"] });

  /* Zwei Nachsätze, beide nur wenn sie zutreffen.
     Der erste ist die wichtigste Einschränkung des Abschnitts und steht
     bewusst SICHTBAR unter der Grafik, nicht nur in der Hinweiszeile.
     Der zweite meldet, dass die Zahlen aus der abgeschriebenen Notreihe
     kommen — dann ist der Stand womöglich veraltet, und das darf nicht
     nur im Bauprotokoll stehen. */
  const saetze = [];
  saetze.push(
    `Österreich zählt seit 2020 mit (Viel-Falter, Universität Innsbruck, ` +
    `seit 2023 rund 480 Standorte). Für einen Verlauf ab ${daten.basis} ist ` +
    `diese Reihe zu kurz — <strong>die Linie zeigt Europa, nicht ` +
    `Österreich</strong>.`);
  if (daten.notreihe) {
    saetze.push(
      `<strong>Hinweis:</strong> Die Abfrage bei Eurostat ist beim letzten ` +
      `Lauf ausgefallen. Gezeigt wird ein abgeschriebener Stand bis ` +
      `${daten.stand}; er kann veraltet sein.`);
  }
  setzeHtml("n-falter", saetze.join(" "));

  setzeHtml("t-falter", tabelle(
    [{ titel: "Jahr", wert: (z) => z.jahr },
     { titel: "Index", num: true, wert: (z) => pz(z.index) },
     { titel: `gegenüber ${daten.basis}`, num: true,
       wert: (z) => pz(Math.round((z.index - 100) * 10) / 10) + " Punkte" }],
    punkte
  ));
}

BIO.baueFalter = baueFalter;
})(window.BIO);
