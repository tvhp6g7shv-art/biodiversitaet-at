/* ===========================================================================
   Biodiversitäts-Dashboard Österreich — Themenstrang: pestizide
   ---------------------------------------------------------------------------
   Wird nach js/kern.js geladen; die Helfer kommen aus window.BIO.
   =========================================================================== */
(function (BIO) {
"use strict";
const { stil, zahl, pz, basis, achse, tabelle, setzeText, setzeHtml,
        diagramme, schrift, hoverDunkler, istSchmal } = BIO;

/* --- Pestizidabsatz und seine Aufteilung ------------------------------
   Gestapelte Balken je Jahr, darüber die Gesamtlinie. Die Balken tragen
   die Aufteilung, die Linie den Verlauf — und sie schließt die Lücke
   2015, für die Eurostat nur den Gesamtwert veröffentlicht.

   WARUM DIE AUFTEILUNG ÜBERHAUPT IM BILD STEHT: Gegen die Aussage
   „der Absatz steigt" kommt sofort der Einwand, das seien vor allem
   anorganische Fungizide — Schwefel und Kupfer, die schwer wiegen und
   auch im Biolandbau zugelassen sind. Der Einwand gehört nicht in eine
   Fußnote, sondern ins Bild: Dort ist zu sehen, dass beide Teile wachsen.

   UND DASS ER ANDERS AUSGEHT ALS ERWARTET, ist der eigentliche Befund.
   Die anorganischen Fungizide wachsen SCHNELLER als der Rest (+81,5 %
   gegen +43,5 %), ihr Anteil steigt von 21,8 auf 26,0 %. Die Planungsakte
   hielt das Gegenteil fest — sie hatte „anorganisch" als Kupfer plus
   Schwefel gerechnet und dabei die dritte Unterkategorie übersehen, die
   sich verzwölffacht hat. Der Text sagt das ausdrücklich, statt die
   frühere Fassung stillschweigend zu ersetzen.

   KEINE ZIELMARKE BEI −50 %: Das Ziel der Farm-to-Fork-Strategie misst
   Einsatz und Risiko über einen gewichteten Indikator, nicht den Absatz
   in Kilogramm, und die Verordnung, die es verbindlich gemacht hätte, ist
   2023 gescheitert. Eine Marke wäre falscher Maßstab und kein geltendes
   Ziel zugleich. Dieselbe Linie wie bei `schutzgebiete`, wo die
   30-%-Marke seit 04.09.2026 „EU-weites Ziel" heißt.

   ZUR FARBWAHL: zwei Serientöne, keine Ampel. Anorganisch und übrig sind
   Stoffgruppen, keine Bewertungsstufen — `--viz-kritisch` bleibt draußen
   (Konvention: nur für Status). Die Linie nimmt `--viz-text-2`, damit sie
   sich von beiden Balkenteilen absetzt und nicht als dritte Kategorie
   gelesen wird. */

const FARBEN = {
  anorganisch: "--viz-series-2",
  rest:        "--viz-series-1",
};

function bauePestizide(daten) {
  const S = schrift();
  if (!daten?.punkte?.length) return;
  const abschnitt = document.getElementById("s-pestizide");
  if (abschnitt) abschnitt.style.display = "";

  const feld = document.getElementById("c-pestizide");
  if (!feld) return;
  const d = echarts.getInstanceByDom(feld) || echarts.init(feld, null, { renderer: "svg" });
  if (!diagramme.includes(d)) diagramme.push(d);

  const punkte = daten.punkte;
  const jahre = punkte.map((p) => String(p.jahr));

  setzeText("u-pestizide",
    `In Verkehr gebrachte Wirkstoffmenge in Tonnen · Österreich · ` +
    `${daten.beginn} bis ${daten.stand}`);
  setzeText("h-pestizide", daten.hinweis ?? "");

  d.setOption({
    ...basis(),
    grid: { left: 8, right: istSchmal(feld) ? 16 : 52, top: 40, bottom: 8,
            containLabel: true },
    legend: {
      top: 0, left: "center", icon: "roundRect",
      itemWidth: 11, itemHeight: 11, itemGap: 14,
      data: ["übrige Mittel", "anorganische Fungizide", "Absatz insgesamt"],
      textStyle: { color: stil("--viz-text-2"), fontSize: S.serie },
    },
    tooltip: {
      ...basis().tooltip, trigger: "axis",
      axisPointer: { type: "shadow", shadowStyle: { color: stil("--viz-grid"), opacity: 0.35 } },
      /* Die Kopfzeile nennt den Gesamtwert. Bei 2015 sagt der Tooltip
         ausdrücklich, dass die Aufteilung fehlt — sonst liest sich die
         Lücke als Null. */
      formatter: (p) => {
        const z = punkte[p[0].dataIndex];
        const kopf = `<strong>${z.jahr}</strong><br><strong>${zahl(z.gesamt)}</strong> Tonnen`;
        if (z.anorganisch === null) {
          return kopf + `<br><span style="color:${stil("--viz-muted")}">` +
            `Aufteilung für dieses Jahr vertraulich</span>`;
        }
        return kopf +
          `&nbsp;&nbsp;<span style="color:${stil("--viz-muted")}">` +
          `${pz(z.anteil, 1)} % anorganische Fungizide</span><br>` +
          `anorganische Fungizide&nbsp;&nbsp;<strong>${zahl(z.anorganisch)}</strong> t<br>` +
          `übrige Mittel&nbsp;&nbsp;<strong>${zahl(z.rest)}</strong> t`;
      },
    },
    xAxis: { ...achse(), type: "category", data: jahre, splitLine: { show: false },
      axisLabel: { hideOverlap: true, color: stil("--viz-muted"), fontSize: S.achse } },
    yAxis: { ...achse(), type: "value", axisLine: { show: false },
      axisLabel: { hideOverlap: true, color: stil("--viz-muted"),
                   fontSize: S.achse, formatter: (v) => zahl(v) } },
    series: [
      {
        name: "anorganische Fungizide", type: "bar", stack: "absatz",
        data: punkte.map((p) => p.anorganisch),
        itemStyle: { color: stil(FARBEN.anorganisch) },
        emphasis: hoverDunkler(stil(FARBEN.anorganisch)),
      },
      {
        name: "übrige Mittel", type: "bar", stack: "absatz",
        data: punkte.map((p) => p.rest),
        itemStyle: { color: stil(FARBEN.rest), borderRadius: [4, 4, 0, 0] },
        emphasis: hoverDunkler(stil(FARBEN.rest)),
      },
      /* Die Linie läuft über ALLE Jahre, auch über 2015, wo die Balken
         fehlen. Ohne sie wäre dort ein Loch und der Gesamtwert dieses
         Jahres — 3.778 t — gar nicht abzulesen. */
      {
        name: "Absatz insgesamt", type: "line", smooth: false, z: 3,
        /* KEIN `endLabel`. Am 04.09.2026 am ausgelieferten Stand gemessen:
           ECharts setzt ihn hier an den ERSTEN Punkt und zeigt dessen Wert —
           auf Pages bei `schutzgebiete` (27,5 statt 29,3), `vogel` und
           `falter` genauso. Vermutlich hängt er am Aufklapp-Clip der
           Einblendung, der nicht läuft, wenn der Abschnitt beim Bau noch
           `display:none` trägt.

           Stattdessen trägt der letzte Datenpunkt sein Etikett selbst. Das
           ist an das Datum gebunden und nicht an eine Animation — es kann
           gar nicht an der falschen Stelle landen. */
        data: punkte.map((p) => p.gesamt),
        markPoint: BIO.endEtikett(punkte.map((p) => p.gesamt), feld,
          (r) => zahl(r.value) + " t"),
        lineStyle: { color: stil("--viz-text-2"), width: 2 },
        itemStyle: { color: stil("--viz-text-2") },
        symbol: "circle", symbolSize: 5,
      },
    ],
  }, { replaceMerge: ["series", "xAxis", "yAxis", "legend"] });

  /* Die Notiz trägt vier Dinge, die die Balken nicht zeigen: dass die
     Kurve über dem Berg ist, wie der naheliegende Einwand ausgeht, warum
     ein Jahr keine Aufteilung hat, und warum hier keine Zielmarke steht. */
  const richtung = daten.schneller === "anorganisch"
    ? `Der Einwand geht anders aus als erwartet: Die anorganischen Fungizide — ` +
      `Schwefel, Kupfer und Verwandtes, auch im Biolandbau zugelassen — wachsen ` +
      `mit <strong>${pz(daten.wachstum_anorganisch, 1)} Prozent</strong> ` +
      `<em>schneller</em> als die übrigen Mittel (${pz(daten.wachstum_rest, 1)} Prozent). ` +
      `Ihr Anteil am Absatz steigt von ${pz(daten.anteil_beginn, 1)} auf ` +
      `${pz(daten.anteil_aktuell, 1)} Prozent.`
    : `Die anorganischen Fungizide wachsen mit ${pz(daten.wachstum_anorganisch, 1)} ` +
      `Prozent langsamer als die übrigen Mittel (${pz(daten.wachstum_rest, 1)} Prozent); ` +
      `der Anstieg liegt also im übrigen Teil.`;

  setzeHtml("n-pestizide",
    `Der Absatz ist nicht durchgehend gestiegen: Sein Höchststand liegt ` +
    `${daten.hoehepunkt_jahr} bei <strong>${zahl(daten.hoehepunkt)} Tonnen</strong>, ` +
    `seither sind es ${pz(Math.abs(daten.seit_hoehepunkt), 1)} Prozent weniger. ` +
    richtung + " " +
    (daten.ohne_teilung?.length
      ? `Für ${daten.ohne_teilung.join(", ")} veröffentlicht Eurostat nur den ` +
        `Gesamtwert, die Aufteilung ist dort vertraulich — deshalb fehlen die ` +
        `Balken und läuft nur die Linie durch. `
      : "") +
    `Das oft zitierte EU-Ziel „minus 50 Prozent" ist hier bewusst nicht ` +
    `eingezeichnet: Es misst Einsatz und Risiko über einen gewichteten ` +
    `Indikator, nicht die abgesetzte Menge.`);

  setzeHtml("t-pestizide", tabelle(
    [{ titel: "Jahr", wert: (z) => z.jahr },
     { titel: "Absatz gesamt", num: true, wert: (z) => zahl(z.gesamt) + " t" },
     { titel: "anorganische Fungizide", num: true,
       wert: (z) => z.anorganisch === null ? "vertraulich" : zahl(z.anorganisch) + " t" },
     { titel: "übrige Mittel", num: true,
       wert: (z) => z.rest === null ? "vertraulich" : zahl(z.rest) + " t" },
     { titel: "Anteil anorganisch", num: true,
       wert: (z) => z.anteil === null ? "–" : pz(z.anteil, 1) + " %" }],
    punkte
  ));
}

BIO.bauePestizide = bauePestizide;
})(window.BIO);
