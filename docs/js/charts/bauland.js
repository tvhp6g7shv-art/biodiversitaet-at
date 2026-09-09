/* ===========================================================================
   Biodiversitäts-Dashboard Österreich — Themenstrang: bauland
   ---------------------------------------------------------------------------
   Wird nach js/kern.js geladen; die Helfer kommen aus window.BIO.
   =========================================================================== */
(function (BIO) {
"use strict";
const { stil, zahl, basis, achse, tabelle, setzeText, setzeHtml, diagramme,
        schrift, istSchmal, istEng, balkenGitter, kategorieLabel, balkenBreite,
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

   ZWEI GRUPPEN, ALSO 36 % BALKENBREITE, nicht die 62 % des Hauses:
   `barWidth` gilt je Gruppe, nicht je Kategorie — zwei mal 62 % sind 124 %
   der Bandbreite, und ECharts schiebt die Balken dann stumm in die
   Nachbarzeile → `reference-balkenbreite-zwei-gruppen`.

   ALLE ZAHLEN HIER SIND AM GERENDERTEN SVG GEMESSEN, nicht aus `barWidth`
   und `barGap` hochgerechnet — der erste Versuch am 09.09.2026 tat genau
   das und lag daneben: Aus dem Vorgabewert `barGap: "30%"` folgt NICHT ein
   Zwischenraum von 30 % der Balkenbreite. ECharts verteilt den Rest der
   Kategoriezeile selbst, sobald `barWidth` fest steht. Gemessen (Feld
   950 px breit, neun Laender, zwei Serien):

     Feld 340 px, 40 %:  Zeile 28,9 px · Balken 11,6 · Paar 1,1 · Land 4,6
     Feld 520 px, 36 %:  Zeile 48,9 px · Balken 17,6 · Paar 1,7 · Land 12,0

   Der Befund des Users galt der ersten Zeile: 11,6 px Balken gegen rund
   600 px Balkenlaenge sind ein Faden. `barGap: "10%"` haelt die beiden
   Balken eines Landes zusammen, waehrend die Zeile waechst — sonst zoege
   die groessere Zeilenhoehe das Paar mit auseinander.
   Beide Zahlen haengen an der FELDHOEHE aus dem CSS (`#c-bauland`). Wer sie
   aendert, misst neu, statt zu rechnen.
   Eng bleibt unangetastet: dort steht die Balkenhoehe in Pixeln aus
   `engStufe()`, und der Kategoriename sitzt UEBER dem Balken — sein
   Ankerpunkt haengt an derselben Zahl.

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
  const LEG_LINKS = legendeLinks(feld, 136);

  setzeText("u-bauland",
    `Veränderung von bebauter Fläche und gewidmetem Bauland in Hektar · ` +
    `Bundesländer · ${daten.frueh} bis ${daten.spaet}`);
  setzeText("h-bauland", daten.hinweis ?? "");

  d.setOption({
    ...basis(),
    /* ACHSENRAND GEGEN DEN LÄNGSTEN NAMEN GERECHNET, nicht geschätzt. Am
       09.09.2026 im ausgelieferten Stand gemessen: „Niederösterreich" ist in
       der MONO-Auslieferung (12 px) 116 px breit, dazu 12 px `margin` des
       Achsenetiketts. Bei 120 brach der Name in zwei Zeilen um („Niederösterrei
       ch") — derselbe Fehler wie am selben Tag bei `rotelisten` und
       `biolandbau`. 136 lässt 8 px Luft. → reference-achsenrand-mono */
    grid: { ...balkenGitter(feld, { left: 136, right: 74 }), top: 46 },
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
                   ...kategorieLabel(feld, 136, zeilen.length) } },
    series: SERIEN.map((serie) => ({
      name: serie.name, type: "bar",
      barWidth: balkenBreite(feld, "36%", zeilen.length),
      barGap: istEng(feld) ? "30%" : "10%",
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

  /* Die Notiz trägt drei Dinge, die die Balken nicht zeigen: die Gesamtbilanz,
     warum der sinkende Anteil kein Erfolg ist, und was „bebaut" hier NICHT
     heisst. Die vier Gemeinden ohne Vergleichsjahr standen hier auch — sie
     stehen in der Methodik und sind am 09.09.2026 aus der Notiz genommen
     worden: Sie war mit 903 Zeichen die längste des ganzen Dashboards, bei
     einem Hausschnitt von rund 330. */
  setzeHtml("n-bauland",
    `Österreichweit kamen zwischen ${daten.frueh} und ${daten.spaet} ` +
    `<strong>${zahl(daten.bebaut_zuwachs)} Hektar</strong> bebaute Fläche ` +
    `dazu. Die Baulandreserve schrumpfte dabei nur um ` +
    `<strong>${zahl(daten.reserve_rueckgang)} Hektar</strong> — weil ` +
    `gleichzeitig <strong>${zahl(daten.bauland_zuwachs)} Hektar</strong> neu ` +
    `gewidmet wurden. <strong>Der Anteil unbebauten Baulands ist trotzdem ` +
    `gesunken</strong>, von ${zahl(daten.anteil_frueher)} auf ` +
    `${zahl(daten.anteil)} Prozent: Er misst die Reserve an einem Nenner, der ` +
    `selbst wächst. „Bebaut dazugekommen" heisst nicht „aus der Reserve ` +
    `verbaut" — gebaut werden kann auch auf neu gewidmetem Land.`);

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
