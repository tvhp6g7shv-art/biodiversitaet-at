/* ===========================================================================
   Biodiversitäts-Dashboard Österreich — Themenstrang: stickstoff
   ---------------------------------------------------------------------------
   Wird nach js/kern.js geladen; die Helfer kommen aus window.BIO.
   =========================================================================== */
(function (BIO) {
"use strict";
const { stil, zahl, pz, basis, achse, tabelle, setzeText, setzeHtml,
        diagramme, schrift, istSchmal, legendeLinks, legendeHoehe } = BIO;

/* --- Stickstoffüberschuss je Hektar -----------------------------------
   Zwei Linien über dieselbe Reihe: die Jahreswerte dünn, das gleitende
   Fünfjahresmittel kräftig darüber. Dazu zwei schraffierte Fenster —
   1985–89 und 2019–23 —, deren Mittelwerte die Überschrift trägt.

   WARUM NICHT EINFACH 2023 GEGEN 1985: Das wären −31 Prozent, eine
   griffigere Zahl. Sie hängt aber an zwei Einzeljahren einer Reihe, die
   zwischen 22,9 und 51,1 kg schwankt — Witterung, Erntejahr, Düngerpreis.
   Ein anderes Startjahr ergibt eine andere Zahl. Der Abschnitt vergleicht
   deshalb Fünfjahresmittel (−19,2 Prozent) und sagt die Einzeljahresrechnung
   in der Notiz ausdrücklich dazu, statt sie zu verschweigen.
   Entscheid des Users vom 09.09.2026.

   WARUM DIE FENSTER IM BILD STEHEN: Eine Überschrift, die zwei Mittelwerte
   vergleicht, ist ohne Bild nicht nachprüfbar. Die beiden Flächen zeigen,
   WELCHE Jahre gemittelt wurden — schmal ohne Beschriftung, dort trägt die
   Fläche allein.

   DER SATZ, DEN DAS BILD NICHT VON SELBST SAGT: Der Rückgang hat drei
   Abschnitte. Das gleitende Mittel fällt bis 2008 auf 29,6 kg, steigt bis
   2019 auf 40,4 und steht heute bei 35,4. Wer nur Anfang und Ende ansieht,
   liest eine stetige Verbesserung, die es nicht gab. Die Notiz nennt alle
   drei Werte und holt sie aus den Daten, statt sie festzuschreiben.

   KEINE ZIELMARKE: Für den Überschuss je Hektar gibt es keinen verbindlichen
   Zielwert — die Nitratrichtlinie regelt Ausbringung und Grundwassergehalt,
   nicht die Bilanz. Eine Marke wäre erfunden. Dieselbe Linie wie bei
   `pestizide`, wo die −50-%-Marke aus demselben Grund fehlt.

   ZUR FARBWAHL: ein Serienton für die Jahreswerte, `--viz-text-2` für das
   Mittel. Keine Ampel — ein Bilanzwert ist keine Bewertungsstufe, und
   `--viz-kritisch` bleibt nach Konvention dem Status vorbehalten. */

const FARBE_JAHR = "--viz-series-1";

function baueStickstoff(daten) {
  const S = schrift();
  if (!daten?.punkte?.length) return;
  const abschnitt = document.getElementById("s-stickstoff");
  if (abschnitt) abschnitt.style.display = "";

  const feld = document.getElementById("c-stickstoff");
  if (!feld) return;
  const d = echarts.getInstanceByDom(feld) || echarts.init(feld, null, { renderer: "svg" });
  if (!diagramme.includes(d)) diagramme.push(d);

  const punkte = daten.punkte;
  const jahre = punkte.map((p) => String(p.jahr));
  const werte = punkte.map((p) => p.wert);
  const mittel = punkte.map((p) => p.mittel);

  const NAMEN = ["Jahreswert", `${daten.fenster}-Jahres-Mittel`];
  const LEG_LINKS = legendeLinks(feld, 14);
  const LEG_HOEHE = Math.max(40, legendeHoehe(feld, NAMEN, LEG_LINKS));

  setzeText("u-stickstoff",
    `Bruttostickstoffbilanz in Kilogramm je Hektar landwirtschaftlicher ` +
    `Fläche · Österreich · ${daten.beginn} bis ${daten.stand}`);
  setzeText("h-stickstoff", daten.hinweis ?? "");

  /* Die beiden Vergleichsfenster. Schmal ohne Beschriftung: „43,8 kg" über
     einer fünf Jahre breiten Fläche steht dort quer über der Linie. */
  const fenster = (von, bis, wert) => ([
    {
      xAxis: String(von),
      itemStyle: { color: stil("--viz-grid"), opacity: 0.5 },
      label: istSchmal(feld) ? { show: false } : {
        show: true, position: "insideTop", distance: 4,
        color: stil("--viz-muted"), fontSize: S.achse,
        formatter: `${zahl(wert)} kg`,
      },
    },
    { xAxis: String(bis) },
  ]);

  d.setOption({
    ...basis(),
    grid: { left: 8, right: istSchmal(feld) ? 16 : 60, top: LEG_HOEHE,
            bottom: 8, containLabel: true },
    legend: {
      top: 0, left: LEG_LINKS, width: feld.clientWidth - LEG_LINKS - 6,
      icon: "roundRect", itemWidth: 11, itemHeight: 11, itemGap: 14,
      data: NAMEN,
      textStyle: { color: stil("--viz-text-2"), fontSize: S.serie },
    },
    tooltip: {
      ...basis().tooltip, trigger: "axis",
      axisPointer: { type: "line", lineStyle: { color: stil("--viz-grid") } },
      formatter: (p) => {
        const z = punkte[p[0].dataIndex];
        return `<strong>${z.jahr}</strong><br>` +
          `<strong>${zahl(z.wert)}</strong> kg je Hektar` +
          (z.mittel === null || z.mittel === undefined ? "" :
            `<br><span style="color:${stil("--viz-muted")}">` +
            `${daten.fenster}-Jahres-Mittel ${zahl(z.mittel)} kg</span>`);
      },
    },
    xAxis: { ...achse(), type: "category", data: jahre, boundaryGap: false,
      splitLine: { show: false },
      axisLabel: { hideOverlap: true, color: stil("--viz-muted"), fontSize: S.achse } },
    /* Die Achse beginnt NICHT bei null. Der Überschuss schwankt zwischen 23
       und 51 kg; eine Nullachse drückte die gesamte Bewegung in das obere
       Drittel. Der Bereich ist keine Anteilsskala, bei der die Null etwas
       bedeutet — hier zählt der Abstand zwischen den Jahren. */
    yAxis: { ...achse(), type: "value", scale: true, axisLine: { show: false },
      axisLabel: { hideOverlap: true, color: stil("--viz-muted"),
                   fontSize: S.achse, formatter: (v) => zahl(v) } },
    series: [
      {
        name: NAMEN[0], type: "line", smooth: false, symbol: "none",
        data: werte,
        lineStyle: { color: stil(FARBE_JAHR), width: 1.5, opacity: 0.9 },
        itemStyle: { color: stil(FARBE_JAHR) },
        markArea: {
          silent: true,
          data: [
            fenster(daten.frueh_von, daten.frueh_bis, daten.mittel_frueh),
            fenster(daten.spaet_von, daten.spaet_bis, daten.mittel_spaet),
          ],
        },
      },
      {
        /* KEIN Endetikett. Es stand hier und zeigte „35,4 kg" — dieselbe
           Zahl, die das rechte Fenster schon in seiner Kopfzeile trägt, nur
           acht Pixel weiter und halb über der Feldkante. Am 09.09.2026 im
           gerenderten SVG nachgesehen: zwei Textknoten „35,4 kg". Die
           Fenster tragen die Zahlen, das Etikett entfällt. (`endLabel` von
           ECharts wäre ohnehin falsch platziert, siehe `kern.js`.) */
        name: NAMEN[1], type: "line", smooth: false, symbol: "none", z: 3,
        data: mittel, connectNulls: false,
        lineStyle: { color: stil("--viz-text-2"), width: 2.5 },
        itemStyle: { color: stil("--viz-text-2") },
      },
    ],
  }, { replaceMerge: ["series", "xAxis", "yAxis", "legend"] });

  /* Die Notiz trägt drei Dinge, die die Linien nicht zeigen: warum hier
     Mittel und keine Einzeljahre verglichen werden, dass der Rückgang
     nicht durchgehend war, und dass es keine Zielmarke gibt. */
  setzeHtml("n-stickstoff",
    `Verglichen werden Fünfjahresmittel, nicht Einzeljahre: ` +
    `<strong>${zahl(daten.mittel_frueh)} kg</strong> im Mittel der Jahre ` +
    `${daten.frueh_von}–${daten.frueh_bis} gegen ` +
    `<strong>${zahl(daten.mittel_spaet)} kg</strong> in ` +
    `${daten.spaet_von}–${daten.spaet_bis}. Die Reihe schwankt witterungs- ` +
    `und erntebedingt stark — zwischen ${zahl(daten.tiefstwert)} kg ` +
    `(${daten.tiefstjahre.join(", ")}) und ${zahl(daten.hoechstwert)} kg ` +
    `(${daten.hoechstjahre.join(" und ")}) —, deshalb trüge ein Vergleich ` +
    `zweier einzelner Jahre die Aussage nicht: ${daten.stand} gegen ` +
    `${daten.beginn} allein ergäbe einen Rückgang von ` +
    `${pz(Math.abs(daten.einzeljahr_rueckgang), 1)} Prozent. Der Unterschied ` +
    `der beiden Mittel liegt um den Faktor ${zahl(daten.faktor)} über seinem ` +
    `Standardfehler. <strong>Der Rückgang ist nicht durchgehend:</strong> Das ` +
    `gleitende Mittel fiel bis ${daten.gleitend_tief_bis} auf ` +
    `${zahl(daten.gleitend_tief)} kg, stieg bis ` +
    `${daten.gleitend_zwischenhoch_bis} wieder auf ` +
    `${zahl(daten.gleitend_zwischenhoch)} kg und steht heute bei ` +
    `${zahl(daten.gleitend_aktuell)} kg. Eine Zielmarke ist nicht ` +
    `eingezeichnet, weil es für den ` +
    `Überschuss je Hektar keine gibt: Die Nitratrichtlinie regelt Ausbringung ` +
    `und Grundwassergehalt, nicht die Bilanz.`);

  setzeHtml("t-stickstoff", tabelle(
    [{ titel: "Jahr", wert: (z) => z.jahr },
     { titel: "Überschuss", num: true, wert: (z) => zahl(z.wert) + " kg/ha" },
     { titel: `${daten.fenster}-Jahres-Mittel`, num: true,
       wert: (z) => z.mittel === null || z.mittel === undefined
         ? "–" : zahl(z.mittel) + " kg/ha" }],
    punkte
  ));
}

BIO.baueStickstoff = baueStickstoff;
})(window.BIO);
