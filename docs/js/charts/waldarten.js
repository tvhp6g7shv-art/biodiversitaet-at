/* ===========================================================================
   Biodiversitäts-Dashboard Österreich — Themenstrang: waldarten
   ---------------------------------------------------------------------------
   Wird nach js/kern.js geladen; die Helfer kommen aus window.BIO.
   =========================================================================== */
(function (BIO) {
"use strict";
const { stil, zahl, pz, basis, achse, tabelle, setzeText, setzeHtml,
        diagramme, schrift, istSchmal, balkenGitter, kategorieLabel,
        balkenBreite, balkenHoehe, legende, hoverDunkler } = BIO;

/* --- Gefährdete Waldpflanzen, drei Rote Listen ------------------------
   Drei gestapelte Balken, einer je Roter Liste, in ABSOLUTEN Zahlen.

   WARUM NICHT AUF 100 % NORMIERT, anders als bei `erhaltung`: Hier
   wächst die Summe (200 → 253 → 286), und dieses Wachstum ist die eine
   Hälfte der Aussage. Eine Normierung würde es wegrechnen. Der Nenner
   bleibt derweil konstant — alle drei Listen bewerten dieselben 1.341
   Taxa —, deshalb sind absolute Zahlen hier ehrlich vergleichbar. Das
   ist bei Roten Listen nicht selbstverständlich und steht in der
   Hinweiszeile.

   DIE ZWEITE HÄLFTE DER AUSSAGE steht in den Segmenten: „vom Aussterben
   bedroht" vervierfacht sich, während die unterste Stufe seit 1999
   zurückgeht. Es werden nicht nur mehr Arten gefährdet — die bereits
   gefährdeten rutschen weiter ab.

   ZUR FARBWAHL: `--viz-div-schlecht-1` bis `-4`, von hell nach kräftig.
   Alle vier Stufen sind Gefährdungsstufen, also eine geordnete Skala
   innerhalb EINER Bedeutung — dafür ist eine Rampe da und keine
   Kategorienfolge. Die Reihenfolge im Datensatz läuft von leicht nach
   schwer, die Rampe läuft mit; „regional ausgestorben" ist der
   kräftigste Ton.

   BEWUSST NICHT `--viz-seq-rot-*`: Diese Rampe steht nur in der idl.css
   der WordPress-Auslieferung, nicht in index.html und nicht in
   embed.html. Ein Token ohne Wert macht die ganze Deklaration ungültig —
   auf GitHub Pages und in den Bot-Bildern käme die Grafik dann in
   ECharts-Vorgabefarben. `--viz-div-schlecht-*` ist in beiden
   Auslieferungen definiert.

   KEINE BESCHRIFTUNG IN DEN SEGMENTEN: Das kleinste zählt 2 von 286.
   Werte im Tooltip und in der Tabelle. */

const FARBEN = ["--viz-div-schlecht-1", "--viz-div-schlecht-2",
                "--viz-div-schlecht-3", "--viz-div-schlecht-4"];

function baueWaldarten(daten) {
  const S = schrift();
  if (!daten?.gruppen?.length) return;
  const abschnitt = document.getElementById("s-waldarten");
  if (abschnitt) abschnitt.style.display = "";

  const feld = document.getElementById("c-waldarten");
  if (!feld) return;
  const d = echarts.getInstanceByDom(feld) || echarts.init(feld, null, { renderer: "svg" });
  if (!diagramme.includes(d)) diagramme.push(d);

  /* Gezeigt werden die Gefäßpflanzen. Moose und Farne sind die
     Gegenprobe und stehen in der Notiz — zwei Gruppen nebeneinander
     ergäben sechs Balken mit 24 Segmenten für eine Aussage, die ein
     Satz trägt. */
  const gruppe = daten.gruppen[0];
  const stufen = daten.stufen;
  const zeilen = gruppe.eintraege;

  setzeText("u-waldarten",
    `Waldgebundene Gefäßpflanzen nach Gefährdungsstufe · ` +
    `${zahl(gruppe.taxa_bewertet)} bewertete Arten je Liste`);
  setzeText("h-waldarten", daten.hinweis ?? "");

  balkenHoehe(d, feld, zeilen.length, 36);

  const maximum = Math.max(...zeilen.map((z) => z.gefaehrdet_gesamt));

  d.setOption({
    ...basis(),
    grid: { ...balkenGitter(feld, { left: 96, right: 60 }), top: 46 },
    legend: legende(feld, {
      top: 0, left: istSchmal(feld) ? 0 : 96,
      itemWidth: 11, itemHeight: 11, itemGap: 14, data: stufen,
      textStyle: { color: stil("--viz-text-2"), fontSize: S.serie },
    }),
    tooltip: {
      ...basis().tooltip, trigger: "axis",
      axisPointer: { type: "shadow", shadowStyle: { color: stil("--viz-grid"), opacity: 0.35 } },
      formatter: (p) => {
        const z = zeilen[p[0].dataIndex];
        return `<strong>Rote Liste ${z.jahr}</strong><br>` +
          `<span style="color:${stil("--viz-muted")}">` +
          `${zahl(z.gefaehrdet_gesamt)} von ${zahl(gruppe.taxa_bewertet)} ` +
          `Arten gefährdet · ${pz(z.anteil, 1)} %</span><br>` +
          p.map((r) => `${r.marker} ${r.seriesName}&nbsp;&nbsp;` +
            `<strong>${zahl(r.value)}</strong>`).join("<br>");
      },
    },
    xAxis: { ...achse(), type: "value", max: Math.ceil(maximum / 50) * 50,
      axisLine: { show: false },
      axisLabel: { hideOverlap: true, color: stil("--viz-muted"),
                   fontSize: S.achse, formatter: (v) => zahl(v) } },
    yAxis: { ...achse(), type: "category", inverse: true,
      data: zeilen.map((z) => `Rote Liste ${z.jahr}`), splitLine: { show: false },
      axisLabel: { color: stil("--viz-text-2"), fontSize: S.serie, margin: 12,
                   ...kategorieLabel(feld, 96, zeilen.length) } },
    series: stufen.map((name, k) => ({
      name, type: "bar", stack: "stufen",
      barWidth: balkenBreite(feld, "56%"),
      data: zeilen.map((z) => z.stufen[name]),
      itemStyle: {
        color: stil(FARBEN[k]),
        borderRadius: k === 0 ? [4, 0, 0, 4]
          : (k === stufen.length - 1 ? [0, 4, 4, 0] : 0),
        borderColor: stil("--viz-surface"), borderWidth: 2,
      },
      emphasis: hoverDunkler(stil(FARBEN[k])),
      label: { show: false },
    })),
  }, { replaceMerge: ["series", "xAxis", "yAxis", "legend"] });

  /* Die Notiz trägt zwei Befunde, die der Balken nicht zeigt: die
     Gegenprobe an einer zweiten Artengruppe, und dass die Bäume selbst
     zahlenmäßig stillstehen, während ihre Schwere zunimmt. */
  const s = daten.schwerste_stufe;
  const u = daten.unveraendert;
  const b = daten.baeume;
  if (s && u) {
    setzeHtml("n-waldarten",
      `Die Summe wächst, aber die Verschiebung nach oben wiegt schwerer: ` +
      `„${s.name}" steigt von <strong>${zahl(s.frueher)}</strong> auf ` +
      `<strong>${zahl(s.jetzt)}</strong> Arten, das ${pz(s.faktor, 1)}-Fache. ` +
      `Dass es kein allgemeiner Trend ist, zeigt die zweite bewertete ` +
      `Gruppe: ${u.name} liegen seit 1986 unverändert bei ` +
      `<strong>${zahl(u.frueher)}</strong> beziehungsweise ` +
      `<strong>${zahl(u.jetzt)}</strong> gefährdeten Arten.` +
      (b ? ` Auch bei den Waldbäumen selbst steht die Zahl still ` +
           `(${zahl(b.gefaehrdet_1986)} von ${zahl(b.taxa_bewertet)}, heute ` +
           `${zahl(b.gefaehrdet_2022)}) — erstmals steht aber eine Baumart ` +
           `unmittelbar vor dem Verschwinden.` : ""));
  }

  setzeHtml("t-waldarten", tabelle(
    [{ titel: "Liste", wert: (z) => `Rote Liste ${z.jahr}` },
     ...stufen.map((name) => ({
       titel: name, num: true, wert: (z) => zahl(z.stufen[name]),
     })),
     { titel: "Gefährdet gesamt", num: true,
       wert: (z) => zahl(z.gefaehrdet_gesamt) },
     { titel: "Anteil", num: true, wert: (z) => pz(z.anteil, 1) + " %" }],
    zeilen
  ));
}

BIO.baueWaldarten = baueWaldarten;
})(window.BIO);
