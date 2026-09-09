/* ===========================================================================
   Biodiversitäts-Dashboard Österreich — Themenstrang: bioverlauf
   ---------------------------------------------------------------------------
   Wird nach js/kern.js geladen; die Helfer kommen aus window.BIO.
   =========================================================================== */
(function (BIO) {
"use strict";
const { stil, zahl, basis, achse, tabelle, setzeText, setzeHtml, diagramme,
        schrift, istSchmal, endEtikett } = BIO;

/* --- Bio-Anteil im Verlauf, und wo die Reihe aufhört -------------------
   LIEST DIESELBE DATEI wie `biolandbau` (docs/data/biolandbau.json). Der
   Abschnitt darüber zeigt den Ländervergleich eines Stichjahrs, dieser den
   Verlauf Österreichs — zwei Aussagen aus einem Abruf. Deshalb steht
   `bioverlauf` NICHT in der DATEN-Liste von kern.js: Es gibt keine eigene
   Datei, die fehlen könnte.

   WAS DIE GRAFIK ZEIGT: Der Anteil steigt von 13,8 auf 25,7 Prozent —
   und dann hört die Linie auf. Nicht weil nichts mehr passiert, sondern
   weil Österreich seit 2021 nicht mehr an Eurostat meldet. Der Datensatz
   selbst ist aktuell und reicht bis 2024; für Österreich sind vier Jahre
   leer. Am 09.09.2026 am Endpunkt geprüft, und in der Gegenrichtung: eine
   Abfrage auf 2023 liefert 32 Länder, Österreich steht unter
   `positions-with-no-data`.

   DIE LEERE FLÄCHE RECHTS IST DER BEFUND, nicht ein Layoutfehler. Die
   Achse läuft deshalb bis zum Ende des Datensatzes weiter, obwohl dort
   keine Werte stehen. Endete sie beim letzten Wert, sähe die Grafik
   vollständig aus und die Aussage wäre weg. Dieselbe Bauart wie
   `rotelisten`: Gegenstand ist, wie alt das Wissen ist.

   DIE NATIONALE ZAHL WIRD GENANNT, ABER NICHT GEZEICHNET. Das Ministerium
   führt für 2024 27,3 Prozent — aber gegen die INVEKOS-Fläche, nicht gegen
   den Eurostat-Nenner. Sie in dieselbe Linie zu setzen hiesse, einen
   Nennerwechsel als Zuwachs zu zeigen; 25,7 auf 27,3 wäre eine Bewegung,
   die niemand gemessen hat. Sie steht als waagrechte Marke im leeren Feld,
   ausdrücklich beschriftet, und in der Notiz mit ihrer Herkunft.

   KEINE ZIELMARKE IN DIESER GRAFIK. Die 35 Prozent der Biodiversitäts-
   strategie stehen bereits im Abschnitt darüber. Zweimal dieselbe Marke
   wäre zweimal dieselbe Grafik mit anderer Beschriftung. */

const FARBE = "--viz-series-1";

function baueBioverlauf(daten) {
  const S = schrift();
  if (!daten?.verlauf?.length) return;
  const abschnitt = document.getElementById("s-bioverlauf");
  if (abschnitt) abschnitt.style.display = "";

  const feld = document.getElementById("c-bioverlauf");
  if (!feld) return;
  const d = echarts.getInstanceByDom(feld) || echarts.init(feld, null, { renderer: "svg" });
  if (!diagramme.includes(d)) diagramme.push(d);

  const punkte = daten.verlauf;
  const letztes = punkte[punkte.length - 1];
  const bis = daten.datensatz_bis ?? letztes.jahr;

  /* Die Achse läuft bis zum Ende des Datensatzes, die Werte enden früher.
     Die Lücke wird als `null` aufgefüllt statt weggelassen — nur so bleibt
     die Kategorie auf der Achse stehen und die Fläche rechts sichtbar. */
  const jahre = [];
  const werte = [];
  for (let j = punkte[0].jahr; j <= bis; j += 1) {
    jahre.push(String(j));
    const treffer = punkte.find((p) => p.jahr === j);
    werte.push(treffer ? treffer.wert : null);
  }

  const national = daten.national || null;
  const luecke = daten.meldeluecke ?? (bis - letztes.jahr);

  setzeText("u-bioverlauf",
    `Anteil der biologisch bewirtschafteten Fläche an der landwirtschaftlich ` +
    `genutzten Fläche · Österreich · ${punkte[0].jahr} bis ${letztes.jahr}, ` +
    `Datensatz bis ${bis}`);
  setzeText("h-bioverlauf",
    `Eurostat sdg_02_40, umgestellte Flächen und Flächen in Umstellung ` +
    `zusammen. Für ${luecke} Jahre meldet Österreich keinen Wert; der ` +
    `Datensatz führt sie für andere Länder.`);

  const marken = [];
  if (national) {
    marken.push({
      yAxis: national.anteil,
      label: {
        show: !istSchmal(feld), position: "insideEndTop", distance: 4,
        color: stil("--viz-muted"), fontSize: S.achse,
        formatter: `national ${zahl(national.anteil)} % (${national.jahr}), anderer Nenner`,
      },
      lineStyle: { color: stil("--viz-muted"), type: "dashed", width: 1 },
    });
  }

  d.setOption({
    ...basis(),
    grid: { left: 8, right: istSchmal(feld) ? 16 : 70, top: 16, bottom: 8,
            containLabel: true },
    legend: { show: false },
    tooltip: {
      ...basis().tooltip, trigger: "axis",
      axisPointer: { type: "line", lineStyle: { color: stil("--viz-grid") } },
      formatter: (p) => {
        const jahr = p[0].axisValue;
        const wert = p[0].data;
        if (wert === null || wert === undefined) {
          return `<strong>${jahr}</strong><br>` +
            `<span style="color:${stil("--viz-muted")}">keine Meldung ` +
            `Österreichs an Eurostat</span>`;
        }
        return `<strong>${jahr}</strong><br><strong>${zahl(wert)} %</strong> ` +
          `der landwirtschaftlich genutzten Fläche`;
      },
    },
    xAxis: { ...achse(), type: "category", data: jahre, boundaryGap: false,
      splitLine: { show: false },
      axisLabel: { hideOverlap: true, color: stil("--viz-muted"), fontSize: S.achse } },
    yAxis: { ...achse(), type: "value", min: 0, axisLine: { show: false },
      axisLabel: { hideOverlap: true, color: stil("--viz-muted"),
                   fontSize: S.achse, formatter: (v) => zahl(v) + " %" } },
    series: [{
      name: "Bio-Anteil", type: "line", smooth: false, symbol: "none",
      data: werte, connectNulls: false,
      lineStyle: { color: stil(FARBE), width: 2.5 },
      itemStyle: { color: stil(FARBE) },
      areaStyle: { color: stil(FARBE), opacity: 0.10 },
      /* Das Etikett hängt am letzten Wert, nicht am Achsenende — sonst
         stünde es allein in der leeren Fläche und läse sich, als gälte es
         für das letzte Jahr der Achse. */
      markPoint: endEtikett(werte, feld, (r) => zahl(r.value) + " %", stil(FARBE)),
      markLine: marken.length
        ? { silent: true, symbol: "none", data: marken }
        : undefined,
      /* Die vier Jahre ohne Meldung als eigene Fläche. Sie trägt die
         Beschriftung, die erklärt, warum rechts nichts steht. */
      markArea: luecke > 0 ? {
        silent: true,
        data: [[
          { xAxis: String(letztes.jahr),
            itemStyle: { color: stil("--viz-grid"), opacity: 0.45 },
            label: istSchmal(feld) ? { show: false } : {
              show: true, position: "insideTop", distance: 6,
              color: stil("--viz-muted"), fontSize: S.achse,
              formatter: "keine Meldung",
            } },
          { xAxis: String(bis) },
        ]],
      } : undefined,
    }],
  }, { replaceMerge: ["series", "xAxis", "yAxis", "legend"] });

  setzeHtml("n-bioverlauf",
    `Zwischen ${punkte[0].jahr} und ${letztes.jahr} stieg der Anteil von ` +
    `<strong>${zahl(punkte[0].wert)} auf ${zahl(letztes.wert)} Prozent</strong>. ` +
    `Danach bricht die Reihe ab. <strong>Nicht der Datensatz endet, sondern ` +
    `die Meldung:</strong> Eurostat führt ihn bis ${bis}, für Österreich sind ` +
    `${luecke} Jahre leer. Der Bruch zwischen 2011 und 2012 — ` +
    `19,6 auf 18,6 Prozent — ist kein Rückgang der Fläche, sondern ein ` +
    `Wechsel der Erhebungsdefinition.` +
    (national
      ? ` <strong>Gezählt wird national weiter:</strong> ${national.quelle} ` +
        `nennt für ${national.jahr} ${zahl(national.anteil)} Prozent, ` +
        `${zahl(national.flaeche_ha)} Hektar und ${zahl(national.betriebe)} ` +
        `Biobetriebe. Diese Zahl steht als waagrechte Marke im Bild, aber ` +
        `nicht in der Linie: Sie misst gegen die INVEKOS-Fläche, die ` +
        `Eurostat-Reihe gegen die landwirtschaftlich genutzte Fläche der ` +
        `EU-Definition. Aus ${zahl(letztes.wert)} und ` +
        `${zahl(national.anteil)} Prozent lässt sich deshalb keine ` +
        `Veränderung ablesen.`
      : ""));

  setzeHtml("t-bioverlauf", tabelle(
    [{ titel: "Jahr", wert: (z) => z.jahr },
     { titel: "Anteil", num: true, wert: (z) => zahl(z.wert) + " %" }],
    punkte
  ));
}

BIO.baueBioverlauf = baueBioverlauf;
})(window.BIO);
