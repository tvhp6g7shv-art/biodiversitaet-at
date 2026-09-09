/* ===========================================================================
   Biodiversitäts-Dashboard Österreich — Themenstrang: bauland
   ---------------------------------------------------------------------------
   Wird nach js/kern.js geladen; die Helfer kommen aus window.BIO.
   =========================================================================== */
(function (BIO) {
"use strict";
const { stil, zahl, basis, achse, tabelle, setzeText, setzeHtml, diagramme,
        schrift, istSchmal, balkenGitter, kategorieLabel, balkenBreite,
        legende, legendeLinks, hoverDunkler } = BIO;

/* --- Baulandbilanz: bebaut gegen neu gewidmet --------------------------
   Zwei liegende Balken je Bundesland, NEBENEINANDER, nicht gestapelt.

   WARUM NICHT DER ANTEIL, den die Quelle fertig liefert: „19,6 % des
   gewidmeten Baulands sind unbebaut" ist die naheliegende Zahl, und sie ist
   zwischen 2022 und 2025 in JEDEM Bundesland gesunken. Wer nur den Anteil
   zeigt, zeigt eine Verbesserung. Der Anteil sinkt aber auch deshalb, weil
   sein Nenner mitwächst — es wird laufend neu gewidmet. Die Bewegung selbst
   ist die Aussage, nicht ihr Quotient → `feedback-nenner-vor-farbe`.

   DIE ZERLEGUNG GEHT EXAKT AUF (Österreich, 2022 → 2025, Hektar):
     bebaute Grundstücke        +4.819,4
     nicht bebaubare              −41,2
     Baulandreserve            −2.304,1
     gewidmetes Bauland        +2.474,1     Probe: 4.819,4 − 41,2 − 2.304,1

   Auf jeden verbauten Hektar kam gut ein halber Hektar neuer Widmung. Genau
   das stehen die beiden Balken nebeneinander.

   DIE BESCHRIFTUNG IST BEWUSST VORSICHTIG. „Zuwachs an bebauter Fläche",
   nicht „verbaute Reserve": Ein Grundstück kann auch aus neu gewidmetem Land
   heraus bebaut werden. Die Zerlegung belegt die Bilanz, nicht den Weg des
   einzelnen Hektars. Dieselbe Zurückhaltung wie bei `gruenland`, wo die
   zweite Linie ausdrücklich keine Bilanz ist.

   ZWEI GRUPPEN, ALSO 40 % BALKENBREITE, nicht die 62 % des Hauses:
   `barWidth` gilt je Gruppe, nicht je Kategorie — zwei mal 62 % sind 124 %
   der Bandbreite, und ECharts schiebt die Balken dann stumm in die
   Nachbarzeile → `reference-balkenbreite-zwei-gruppen`.

   ZUR FARBWAHL: `--viz-series-1` für das Bebaute, `--viz-series-3` für die
   neue Widmung. Keine Ampel — was hier steht, ist eine Flächenbilanz und
   keine Bewertungsstufe; `--viz-kritisch` bleibt nach Konvention dem Status
   vorbehalten. Das Paar dunkel/hell ist dasselbe, das sich in `stickstoff`
   am 09.09.2026 als unterscheidbar erwiesen hat — `--viz-series-1` gegen
   `--viz-text-2` wäre es nicht.

   KEINE ZIELMARKE. Das 2,5-Hektar-Ziel der Bodenstrategie misst die
   Netto-Neuinanspruchnahme pro Tag über ALLE Nutzungen, nicht die Widmung
   von Bauland. Es hier einzuzeichnen hieße, zwei Größen gleichzusetzen, die
   verschiedene Nenner haben. Dieselbe Linie wie bei `pestizide` und
   `stickstoff`. */

const SERIEN = [
  { name: "bebaut dazugekommen", schluessel: "bebaut_zuwachs",  farbe: "--viz-series-1" },
  { name: "neu gewidmet (netto)", schluessel: "bauland_zuwachs", farbe: "--viz-series-3" },
];

function baueBauland(daten) {
  const S = schrift();
  if (!daten?.laender?.length) return;
  const abschnitt = document.getElementById("s-bauland");
  if (abschnitt) abschnitt.style.display = "";

  const feld = document.getElementById("c-bauland");
  if (!feld) return;
  const d = echarts.getInstanceByDom(feld) || echarts.init(feld, null, { renderer: "svg" });
  if (!diagramme.includes(d)) diagramme.push(d);

  const zeilen = daten.laender;
  const NAMEN = SERIEN.map((s) => s.name);
  const LEG_LINKS = legendeLinks(feld, 120);

  setzeText("u-bauland",
    `Veränderung von bebauter Fläche und gewidmetem Bauland in Hektar · ` +
    `Bundesländer · ${daten.frueh} bis ${daten.spaet}`);
  setzeText("h-bauland", daten.hinweis ?? "");

  d.setOption({
    ...basis(),
    grid: { ...balkenGitter(feld, { left: 120, right: 74 }), top: 46 },
    legend: legende(feld, {
      top: 0, left: LEG_LINKS,
      itemWidth: 11, itemHeight: 11, itemGap: 14,
      data: NAMEN,
      textStyle: { color: stil("--viz-text-2"), fontSize: S.serie },
    }),
    tooltip: {
      ...basis().tooltip, trigger: "axis",
      axisPointer: { type: "shadow", shadowStyle: { color: stil("--viz-grid"), opacity: 0.35 } },
      /* Die Kopfzeile trägt das Verhältnis. Es aus zwei Balkenlängen im
         Kopf zu bilden wäre genau die Rechnung, die der Abschnitt abnimmt. */
      formatter: (p) => {
        const z = zeilen[p[0].dataIndex];
        const quote = z.bebaut_zuwachs > 0
          ? Math.round(z.bauland_zuwachs / z.bebaut_zuwachs * 100) : null;
        return `<strong>${z.name}</strong><br>` +
          p.map((r) => `${r.marker} ${r.seriesName}&nbsp;&nbsp;` +
            `<strong>${zahl(r.value)}</strong> ha`).join("<br>") +
          (quote === null ? "" :
            `<br><span style="color:${stil("--viz-muted")}">auf 100 ha bebaut ` +
            `kamen ${zahl(quote)} ha neue Widmung</span>`) +
          `<br><span style="color:${stil("--viz-muted")}">Reserve heute ` +
          `${zahl(z.anteil)} % des gewidmeten Baulands (${daten.frueh}: ` +
          `${zahl(z.anteil_frueher)} %)</span>`;
      },
    },
    xAxis: { ...achse(), type: "value", axisLine: { show: false },
      axisLabel: { hideOverlap: true, color: stil("--viz-muted"),
                   fontSize: S.achse, formatter: (v) => zahl(v) } },
    yAxis: { ...achse(), type: "category", inverse: true,
      data: zeilen.map((z) => z.name), splitLine: { show: false },
      axisLabel: { color: stil("--viz-text-2"), fontSize: S.serie, margin: 12,
                   ...kategorieLabel(feld, 120, zeilen.length) } },
    series: SERIEN.map((serie) => ({
      name: serie.name, type: "bar",
      barWidth: balkenBreite(feld, "40%", zeilen.length),
      data: zeilen.map((z) => z[serie.schluessel]),
      itemStyle: { color: stil(serie.farbe), borderRadius: [0, 4, 4, 0] },
      emphasis: hoverDunkler(stil(serie.farbe)),
      /* Beide Balken tragen ihre Zahl aussen. Innen ginge nicht: Wien und
         Vorarlberg liegen bei gut 100 ha, ihre Balken sind zu kurz für eine
         Zahl. Im schmalen Feld entfallen die Etiketten ganz — dort steht
         die Zahl im Tooltip und in der Tabelle. */
      label: {
        show: !istSchmal(feld), position: "right",
        color: stil("--viz-text-2"), fontSize: S.label,
        formatter: (r) => zahl(r.value),
      },
    })),
  }, { replaceMerge: ["series", "xAxis", "yAxis", "legend"] });

  /* Die Notiz trägt vier Dinge, die die Balken nicht zeigen: die
     Gesamtbilanz, warum der sinkende Anteil kein Erfolg ist, was „bebaut"
     hier NICHT heisst, und die vier Gemeinden ohne Vergleichsjahr. */
  const quote = daten.ersatzquote;
  setzeHtml("n-bauland",
    `Österreichweit kamen zwischen ${daten.frueh} und ${daten.spaet} ` +
    `<strong>${zahl(daten.bebaut_zuwachs)} Hektar</strong> bebaute Fläche ` +
    `dazu. Die Baulandreserve schrumpfte dabei nur um ` +
    `<strong>${zahl(daten.reserve_rueckgang)} Hektar</strong> — weil ` +
    `gleichzeitig <strong>${zahl(daten.bauland_zuwachs)} Hektar</strong> neu ` +
    `gewidmet wurden. Auf 100 Hektar bebaute Fläche kamen also ` +
    `${zahl(quote)} Hektar neues Bauland. <strong>Der Anteil unbebauten ` +
    `Baulands ist trotzdem gesunken</strong>, von ` +
    `${zahl(daten.anteil_frueher)} auf ${zahl(daten.anteil)} Prozent, und ` +
    `zwar in jedem Bundesland: Er misst die Reserve an einem Nenner, der ` +
    `selbst wächst. ${daten.hoechster_anteil} führt ihn heute mit dem ` +
    `höchsten, ${daten.niedrigster_anteil} mit dem niedrigsten Wert. ` +
    `<strong>„Bebaut dazugekommen" heisst nicht „aus der Reserve ` +
    `verbaut":</strong> Gebaut werden kann auch auf neu gewidmetem Land. ` +
    `Die Zerlegung belegt die Bilanz, nicht den Weg des einzelnen Hektars. ` +
    `In vier Gemeinden (Eberstein, Glödnitz, Keutschach am See, ` +
    `Sachsenburg) liegt ein digitaler Flächenwidmungsplan erst ab ` +
    `${daten.spaet} vor; für sie werden dessen Daten auch für ` +
    `${daten.frueh} herangezogen, ihre Veränderung ist daher null.`);

  setzeHtml("t-bauland", tabelle(
    [{ titel: "Bundesland", wert: (z) => z.name },
     { titel: "bebaut dazu", num: true, wert: (z) => zahl(z.bebaut_zuwachs) + " ha" },
     { titel: "neu gewidmet", num: true, wert: (z) => zahl(z.bauland_zuwachs) + " ha" },
     { titel: "Reserve heute", num: true, wert: (z) => zahl(z.reserve) + " ha" },
     { titel: "Anteil", num: true, wert: (z) => zahl(z.anteil) + " %" }],
    zeilen
  ));
}

BIO.baueBauland = baueBauland;
})(window.BIO);
