/* ===========================================================================
   Biodiversitäts-Dashboard Österreich — Themenstrang: gruenland
   ---------------------------------------------------------------------------
   Wird nach js/kern.js geladen; die Helfer kommen aus window.BIO.
   =========================================================================== */
(function (BIO) {
"use strict";
const { stil, zahl, pz, basis, achse, tabelle, setzeText, setzeHtml,
        diagramme, schrift, istSchmal } = BIO;

/* --- Grünland gegen Wald, als Veränderung ------------------------------
   Zwei Linien über fünf Stützstellen, gemessen gegen das erste Jahr.

   WARUM VERÄNDERUNG UND NICHT QUADRATKILOMETER. Die Überschrift sagt, dass
   Grünland verschwindet. In absoluten Werten über einer Nullachse wäre das
   eine Linie, die von 21.494 auf 19.932 fällt — bei diesem Maßstab optisch
   waagrecht. Die Aussage stünde dann in der Überschrift und nicht im Bild,
   und das Auge glaubt dem Bild. Genau daran ist am 07.09.2026 die
   Schutzstufen-Grafik zweimal gescheitert, bevor der Nennerwechsel sie
   gerettet hat. Hier trägt die Achse die Aussage: −7,3 ist als Länge unter
   der Null abzulesen, +6,7 darüber.

   WAS DIE ZWEITE LINIE LEISTET. Ohne den Wald liest sich der Rückgang als
   Flächenverlust überhaupt. Mit ihm ist zu sehen: Die Fläche verschwindet
   nicht, ihre Nutzung wechselt. Der Text sagt ausdrücklich, dass das KEINE
   Bilanz ist — zwischen Wiese und Wald liegen Acker, Siedlung und Verkehr,
   die beiden Kategorien tauschen nicht direkt untereinander.

   ZUR FARBWAHL: zwei Serientöne, keine Ampel. Wiese und Wald sind
   Nutzungsarten, keine Bewertungsstufen — `--viz-kritisch` bleibt draußen
   (Konvention: nur für Status). Genommen sind `series-1` und `series-3`,
   dasselbe Paar wie in `wald.js` (dort „dunkel" und „hell"). Die Serientöne
   sind eine Helligkeitsrampe EINER Farbfamilie, keine verschiedenen Farben:
   Auf der Lichtung-Palette am 08.09.2026 gemessen — series-1 #444a3b,
   series-3 #848b7a. Die beiden Linien unterscheiden sich also in der
   Helligkeit, nicht im Ton; deshalb tragen sie zusätzlich ihr Etikett am
   Ende. `series-5`/`-6` kommen nicht in Frage, sie stehen auf WordPress gar
   nicht zur Verfügung — ein `var()` ohne Wert macht die ganze Deklaration
   ungültig, und der Ausfall wäre still.

   KEIN `endLabel`, sondern `BIO.endEtikett`: ECharts setzt `endLabel` in
   dieser Auslieferung an den ERSTEN Punkt und zeigt dessen Wert. Hier wäre
   das besonders tückisch — der erste Wert ist bei beiden Reihen die Null. */

const FARBEN = {
  gruenland: "--viz-series-1",
  wald:      "--viz-series-3",
};

function baueGruenland(daten) {
  const S = schrift();
  if (!daten?.punkte?.length) return;
  const abschnitt = document.getElementById("s-gruenland");
  if (abschnitt) abschnitt.style.display = "";

  const feld = document.getElementById("c-gruenland");
  if (!feld) return;
  const d = echarts.getInstanceByDom(feld) || echarts.init(feld, null, { renderer: "svg" });
  if (!diagramme.includes(d)) diagramme.push(d);

  const punkte = daten.punkte;
  const jahre = punkte.map((p) => String(p.jahr));
  const reiheGruen = punkte.map((p) => p.gruenland_ver);
  const reiheWald = punkte.map((p) => p.wald_ver);

  /* Vorzeichen gehört an jede Zahl dieser Achse: Ohne es liest sich „7,3"
     als Bestand und nicht als Verlust.

     Das Minus wird selbst gesetzt und nicht `pz()` überlassen: Dessen
     `toLocaleString("de-AT")` liefert den ASCII-Bindestrich, das Haus
     schreibt aber das typografische Minus U+2212 — so machen es `falter`,
     `kpi` und `vogel`. Am 08.09.2026 am gerenderten SVG nachgesehen, dort
     stand vorher „-9 %". */
  const mitVorzeichen = (v, stellen = 1) =>
    (v > 0 ? "+" : v < 0 ? "−" : "") + pz(Math.abs(v), stellen);

  setzeText("u-gruenland",
    `Veränderung der Fläche gegenüber ${daten.beginn}, in Prozent · Österreich · ` +
    `${daten.beginn} bis ${daten.stand}`);
  setzeText("h-gruenland", daten.hinweis ?? "");

  d.setOption({
    ...basis(),
    /* Rechts Platz für die beiden Endetiketten. Im schmalen Feld blendet
       `endLabelZeigen()` sie ohnehin aus, dann ist der Rand verschenkt. */
    grid: { left: 8, right: istSchmal(feld) ? 16 : 64, top: 40, bottom: 8,
            containLabel: true },
    legend: {
      top: 0, left: "center", icon: "roundRect",
      itemWidth: 11, itemHeight: 11, itemGap: 14,
      data: ["Wiesen und Weiden", "Wald"],
      textStyle: { color: stil("--viz-text-2"), fontSize: S.serie },
    },
    tooltip: {
      ...basis().tooltip, trigger: "axis",
      axisPointer: { type: "line", lineStyle: { color: stil("--viz-grid") } },
      /* Der Tooltip trägt, was die Achse absichtlich nicht zeigt: die
         absoluten Flächen und den Anteil am Land. Wer wissen will, wie groß
         das alles ist, findet es hier — im Bild stünde es dem Vergleich im Weg. */
      formatter: (p) => {
        const z = punkte[p[0].dataIndex];
        return `<strong>${z.jahr}</strong><br>` +
          `Wiesen und Weiden&nbsp;&nbsp;<strong>${zahl(z.gruenland_km2)}</strong> km²` +
          `&nbsp;&nbsp;<span style="color:${stil("--viz-muted")}">` +
          `${pz(z.gruenland_pc, 1)} % des Landes · ${mitVorzeichen(z.gruenland_ver)} %</span><br>` +
          `Wald&nbsp;&nbsp;<strong>${zahl(z.wald_km2)}</strong> km²` +
          `&nbsp;&nbsp;<span style="color:${stil("--viz-muted")}">` +
          `${pz(z.wald_pc, 1)} % des Landes · ${mitVorzeichen(z.wald_ver)} %</span>`;
      },
    },
    xAxis: { ...achse(), type: "category", data: jahre, splitLine: { show: false },
      axisLabel: { hideOverlap: true, color: stil("--viz-muted"), fontSize: S.achse } },
    yAxis: { ...achse(), type: "value", axisLine: { show: false },
      axisLabel: { hideOverlap: true, color: stil("--viz-muted"),
                   fontSize: S.achse, formatter: (v) => mitVorzeichen(v, 0) + " %" } },
    series: [
      {
        name: "Wiesen und Weiden", type: "line", smooth: false, z: 3,
        data: reiheGruen,
        /* Die Nulllinie hängt an dieser Reihe, nicht an einer eigenen Serie:
           Als Serie brauchte sie einen Namen in der Legende und stünde dort
           als dritte Kategorie. `markLine` bleibt aus der Legende heraus. */
        markLine: {
          silent: true, symbol: "none", animation: false,
          data: [{ yAxis: 0 }],
          lineStyle: { color: stil("--viz-grid"), width: 1, type: "solid" },
          label: { show: true, position: "insideStartTop", formatter: String(daten.beginn),
                   color: stil("--viz-muted"), fontSize: S.achse },
        },
        markPoint: BIO.endEtikett(reiheGruen, feld,
          (r) => mitVorzeichen(r.value) + " %", stil(FARBEN.gruenland)),
        lineStyle: { color: stil(FARBEN.gruenland), width: 2.5 },
        itemStyle: { color: stil(FARBEN.gruenland) },
        symbol: "circle", symbolSize: 6,
      },
      {
        name: "Wald", type: "line", smooth: false, z: 2,
        data: reiheWald,
        markPoint: BIO.endEtikett(reiheWald, feld,
          (r) => mitVorzeichen(r.value) + " %", stil(FARBEN.wald)),
        lineStyle: { color: stil(FARBEN.wald), width: 2.5 },
        itemStyle: { color: stil(FARBEN.wald) },
        symbol: "circle", symbolSize: 6,
      },
    ],
  }, { replaceMerge: ["series", "xAxis", "yAxis", "legend"] });

  /* Die Notiz trägt drei Dinge, die die Linien nicht zeigen: wie groß der
     Verlust in Fläche ist, dass die beiden Kurven keine Bilanz bilden, und
     wie sich die Anteile am Land verschoben haben. */
  setzeHtml("n-gruenland",
    `In Fläche gerechnet sind das <strong>${zahl(daten.verlust_km2)} Quadratkilometer</strong> ` +
    `weniger Wiesen und Weiden und <strong>${zahl(daten.zuwachs_km2)} Quadratkilometer</strong> ` +
    `mehr Wald. Ihr Anteil am Land verschiebt sich von ${pz(daten.gruenland_anteil_beginn, 1)} ` +
    `auf ${pz(daten.gruenland_anteil_aktuell, 1)} Prozent, der des Waldes auf ` +
    `${pz(daten.wald_anteil_aktuell, 1)} Prozent. ` +
    `<strong>Eine Bilanz ist das nicht:</strong> Die beiden Kategorien tauschen nicht ` +
    `direkt untereinander — zwischen ihnen liegen Acker, Siedlung und Verkehrsfläche. ` +
    `Ablesbar ist, dass Grünland zurückgeht, während Wald zunimmt, nicht, dass das eine ` +
    `zum anderen wird.`);

  setzeHtml("t-gruenland", tabelle(
    [{ titel: "Jahr", wert: (z) => z.jahr },
     { titel: "Wiesen und Weiden", num: true, wert: (z) => zahl(z.gruenland_km2) + " km²" },
     { titel: "Anteil", num: true, wert: (z) => pz(z.gruenland_pc, 1) + " %" },
     { titel: "gegenüber " + daten.beginn, num: true,
       wert: (z) => mitVorzeichen(z.gruenland_ver) + " %" },
     { titel: "Wald", num: true, wert: (z) => zahl(z.wald_km2) + " km²" },
     { titel: "Anteil", num: true, wert: (z) => pz(z.wald_pc, 1) + " %" },
     { titel: "gegenüber " + daten.beginn, num: true,
       wert: (z) => mitVorzeichen(z.wald_ver) + " %" }],
    punkte
  ));
}

BIO.baueGruenland = baueGruenland;
})(window.BIO);
