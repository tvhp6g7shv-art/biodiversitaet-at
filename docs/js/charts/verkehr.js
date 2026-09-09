/* ===========================================================================
   Biodiversitäts-Dashboard Österreich — Themenstrang: verkehr
   ---------------------------------------------------------------------------
   Wird nach js/kern.js geladen; die Helfer kommen aus window.BIO.
   =========================================================================== */
(function (BIO) {
"use strict";
const { stil, zahl, pz, basis, achse, tabelle, setzeText, setzeHtml, diagramme,
        schrift, balkenGitter, kategorieLabel, balkenBreite, balkenHoehe,
        hoverDunkler } = BIO;

/* --- Verkehrsflächen nach Art ------------------------------------------

   WARUM DIESER ABSCHNITT NEBEN DER KARTE STEHT:
   Die Karte zeigt, WO Fläche beansprucht ist. Sie kann nicht zeigen, WOFÜR.
   Der ÖROK-Datensatz führt das je Polygon mit — und die Zerlegung des
   Verkehrs ist die Zahl, die am stärksten gegen die Anschauung läuft:

     Gemeinde- und sonstige Straßen   104.292 ha
     Landesstraßen (B und L)           42.875 ha
     Schiene                           12.700 ha
     Autobahnen und Schnellstraßen     10.990 ha
     Flughäfen                          1.964 ha

   Das Gemeindestraßennetz beansprucht das Neuneinhalbfache aller
   Autobahnen und Schnellstraßen. Über Bodenverbrauch wird an Autobahnen
   verhandelt; die Fläche liegt im Netz darunter, das niemand einweiht.

   WARUM EIN LIEGENDER BALKEN UND KEINE TORTE:
   Die Aussage ist ein Größenverhältnis — neuneinhalb zu eins. Das ist eine
   Länge, keine Fläche. Auf einer Torte müsste man zwei Winkel vergleichen,
   die nebeneinander liegen; im Balken steht das Verhältnis als Länge im
   Bild. → `feedback-nenner-vor-farbe`

   WARUM EINE FARBE FÜR ALLE FÜNF:
   Die fünf Arten sind Kategorien derselben Größe, keine Wertung — kein
   Balken ist gut oder schlecht. Eine Farbe je Kategorie würde eine
   Ordnung behaupten, die es nicht gibt; `--viz-kritisch` bleibt dem Status
   vorbehalten. → `reference-dashboard-konventionen`

   WARUM DIE NAMEN NICHT DIE DER QUELLE SIND:
   Die Code-Liste nennt „Landesstraße B+L" und „Gemeinde- und sonstige
   Straßen". Die Kürzel B und L stehen für die ehemaligen Bundesstraßen und
   die Landesstraßen; ausgeschrieben liest es sich ohne Vorwissen. Die
   Originalbezeichnung steht in der Tabelle daneben, damit die Zuordnung
   zur Quelle nachvollziehbar bleibt. */

/* Reihenfolge steht fest und wird NICHT aus den Daten sortiert: Sie ist die
   Aussage. Absteigend gelesen ist der erste Balken der überraschende. */
const ARTEN = [
  { code: "103", name: "Gemeinde- und sonstige Straßen", quelle: "Gemeinde- und sonstige Straßen" },
  { code: "102", name: "Landesstraßen (B und L)",        quelle: "Landesstraße B+L" },
  { code: "104", name: "Schiene",                        quelle: "Schiene" },
  { code: "101", name: "Autobahnen und Schnellstraßen",  quelle: "Autobahn und Schnellstraße" },
  { code: "105", name: "Flughäfen",                      quelle: "Flughafen" },
];

function baueVerkehr(daten) {
  const S = schrift();
  const detail = daten?.oesterreich?.detail_ha;
  if (!detail) return;

  const zeilen = ARTEN
    .map((a) => ({ ...a, ha: Number(detail[a.code]) }))
    .filter((z) => isFinite(z.ha) && z.ha > 0);
  if (zeilen.length < 2) return;

  const abschnitt = document.getElementById("s-verkehr");
  if (abschnitt) abschnitt.style.display = "";

  const feld = document.getElementById("c-verkehr");
  if (!feld) return;
  const d = echarts.getInstanceByDom(feld) || echarts.init(feld, null, { renderer: "svg" });
  if (!diagramme.includes(d)) diagramme.push(d);

  const verkehrGesamt = zeilen.reduce((s, z) => s + z.ha, 0);
  /* Nenner ist die gesamte Flächeninanspruchnahme, nicht nur der Verkehr —
     sonst stünde in der Notiz ein Anteil an sich selbst. */
  const fiGesamt = Object.values(detail)
    .map(Number).filter(isFinite).reduce((s, v) => s + v, 0);
  const strassen = zeilen.find((z) => z.code === "103");
  const autobahn = zeilen.find((z) => z.code === "101");
  const faktor = (strassen && autobahn && autobahn.ha > 0)
    ? strassen.ha / autobahn.ha : null;

  setzeText("u-verkehr",
    `Für Verkehr in Anspruch genommene Fläche nach Art · Hektar · ` +
    `Stand ${daten.stand} · Einteilung nach der ÖROK-Code-Liste`);

  setzeText("n-verkehr",
    `Verkehr beansprucht ${zahl(Math.round(verkehrGesamt))} Hektar und damit ` +
    `${pz(100 * verkehrGesamt / fiGesamt)} % der gesamten ` +
    `Flächeninanspruchnahme Österreichs.` +
    (faktor
      ? ` Das Gemeindestraßennetz allein steht für ${pz(faktor)}-mal so viel ` +
        `Fläche wie alle Autobahnen und Schnellstraßen zusammen.`
      : ""));

  /* Hinweiszeile im Hausmaß 150–234 → `reference-dashboard-konventionen`. */
  setzeText("h-verkehr",
    `Über Bodenverbrauch wird an Autobahnen gestritten. Die Fläche liegt im ` +
    `Netz darunter: Gemeindestraßen und Wege sind die größte einzelne ` +
    `Verkehrsfläche des Landes — und die, über die niemand streitet.`);

  balkenHoehe(d, feld, zeilen.length);

  const farbe = stil("--viz-akzent");

  d.setOption({
    ...basis(),
    grid: balkenGitter(feld, { left: 190, right: 84 }),
    tooltip: {
      ...basis().tooltip, trigger: "axis",
      axisPointer: { type: "shadow", shadowStyle: { color: stil("--viz-grid"), opacity: 0.35 } },
      formatter: (p) => {
        const z = zeilen[p[0].dataIndex];
        return `<strong>${z.name}</strong><br>` +
          `${zahl(Math.round(z.ha))} ha<br>` +
          `<span style="color:${stil("--viz-muted")}">` +
          `${pz(100 * z.ha / verkehrGesamt)} % der Verkehrsfläche · ` +
          `in der Quelle „${z.quelle}"</span>`;
      },
    },
    xAxis: { ...achse(), type: "value", axisLine: { show: false },
      axisLabel: { hideOverlap: true, color: stil("--viz-muted"),
                   fontSize: S.achse, formatter: (v) => zahl(v) } },
    yAxis: { ...achse(), type: "category", inverse: true,
      data: zeilen.map((z) => z.name), splitLine: { show: false },
      axisLabel: { color: stil("--viz-text-2"), fontSize: S.serie, margin: 12,
                   ...kategorieLabel(feld, 190, zeilen.length) } },
    series: [{
      type: "bar",
      barWidth: balkenBreite(feld, "62%", zeilen.length),
      data: zeilen.map((z) => z.ha),
      itemStyle: { color: farbe, borderRadius: [0, 4, 4, 0] },
      emphasis: hoverDunkler(farbe),
      /* Die Zahl steht am Balkenende, nicht darin: Der kürzeste Balken ist
         mit 1.964 ha rund ein Fünfzigstel des längsten — innen läge sein
         Etikett außerhalb des eigenen Balkens. */
      label: {
        show: true, position: "right", color: stil("--viz-text-2"),
        fontSize: S.label, fontWeight: "bold",
        formatter: (r) => zahl(Math.round(r.value)),
      },
    }],
  });

  setzeHtml("t-verkehr", tabelle(
    [{ titel: "Art", wert: (z) => z.name },
     { titel: "Hektar", num: true, wert: (z) => zahl(Math.round(z.ha)) },
     { titel: "Anteil am Verkehr", num: true,
       wert: (z) => `${pz(100 * z.ha / verkehrGesamt)} %` },
     { titel: "Anteil an der Inanspruchnahme", num: true,
       wert: (z) => `${pz(100 * z.ha / fiGesamt)} %` },
     { titel: "Bezeichnung in der Quelle", wert: (z) => z.quelle }],
    zeilen
  ));
}

BIO.baueVerkehr = baueVerkehr;
})(window.BIO);
