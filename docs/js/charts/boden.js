/* ===========================================================================
   Biodiversitäts-Dashboard Österreich — Themenstrang: boden
   ---------------------------------------------------------------------------
   Wird nach js/kern.js geladen; die Helfer kommen aus window.BIO.
   =========================================================================== */
(function (BIO) {
"use strict";
const { stil, zahl, pz, basis, achse, tabelle, setzeText, setzeHtml,
        diagramme, schrift, hoverDunkler } = BIO;

/* --- 03 — Bodenverbrauch ---------------------------------------------
   Vier stehende Balken, einer je Messperiode.

   WARUM BALKEN UND KEINE LINIE: Die Werte sind PERIODENMITTEL, keine
   Jahreswerte. „6,5 ha pro Tag" gilt für 2022–2025 als Ganzes, nicht für
   2025. Eine Linie würde zwischen den Punkten interpolieren und damit
   Jahreswerte behaupten, die niemand erhoben hat. Ein Balken belegt eine
   Spanne — genau das, was der Wert aussagt.

   Eine Farbe für alle vier Balken. Die Länge trägt die Größe, es gibt
   keine Kategorien zu unterscheiden. Kein Farbverlauf über die Zeit: der
   letzte Balken ist nicht „gut" und der erste nicht „schlecht", beide
   sind Messwerte. */

function baueBoden(daten) {
  const S = schrift();
  if (!daten?.tageswerte?.length) return;
  const abschnitt = document.getElementById("s-boden");
  if (abschnitt) abschnitt.style.display = "";

  const feld = document.getElementById("c-boden");
  if (!feld) return;
  const d = echarts.getInstanceByDom(feld) || echarts.init(feld, null, { renderer: "svg" });
  if (!diagramme.includes(d)) diagramme.push(d);

  const werte = daten.tageswerte;
  /* Rot, nicht neutral (25.08.2026). Neu beanspruchter Boden ist eine
     schlechte Größe, und Schlechtes steht in diesem Projekt im Rotraum.
     Dass die Balken FALLEN, sagt schon ihre Höhe — die Farbe bewertet
     die Größe, nicht ihren Verlauf.

     `--viz-seq-rot-4` und nicht `--viz-kritisch`: die Alarmfarbe ist
     für Status reserviert. Stufe 4 liegt in beiden Modi über 5 : 1
     gegen die Kartenfläche (Abschnitt 52 der idl.css). */
  const farbe = stil("--viz-seq-rot-4");

  setzeText("u-boden",
    `Neu beanspruchte Fläche je Tag, Mittel der Periode · ` +
    `${daten.erste_periode} bis ${daten.aktuell_periode}`);
  setzeText("h-boden", daten.hinweis ?? "");

  /* Kopfraum: Der höchste Balken darf sein Label nicht in die Titelzeile
     drücken. Eine halbe Schrittweite über dem Maximum reicht. */
  const hoechster = Math.max(...werte.map((w) => w.ha_pro_tag));
  const schritt = 5;
  const obergrenze = Math.ceil((hoechster + schritt / 2) / schritt) * schritt;

  d.setOption({
    ...basis(),
    grid: { left: 8, right: 16, top: 28, bottom: 8, containLabel: true },
    tooltip: {
      ...basis().tooltip, trigger: "axis",
      axisPointer: { type: "shadow", shadowStyle: { color: stil("--viz-grid"), opacity: 0.35 } },
      formatter: (p) => {
        const w = werte[p[0].dataIndex];
        const jahre = w.bis - w.von;
        const gesamt = Math.round(w.ha_pro_tag * 365.25 * jahre);
        return `<strong>${w.periode}</strong><br>` +
          `${pz(w.ha_pro_tag)} ha pro Tag<br>` +
          `<span style="color:${stil("--viz-muted")}">` +
          `rund ${zahl(gesamt)} ha in ${jahre} Jahren</span>`;
      },
    },
    xAxis: { ...achse(), type: "category", data: werte.map((w) => w.periode),
             splitLine: { show: false } },
    yAxis: { ...achse(), type: "value", min: 0, max: obergrenze, interval: schritt,
             axisLine: { show: false },
             axisLabel: { hideOverlap: true, color: stil("--viz-muted"),
                          fontSize: S.achse, formatter: (v) => v + " ha" } },
    series: [{
      type: "bar", name: "Hektar pro Tag", barWidth: "52%",
      data: werte.map((w) => w.ha_pro_tag),
      itemStyle: { color: farbe, borderRadius: [4, 4, 0, 0] },
      emphasis: hoverDunkler(farbe),
      label: { show: true, position: "top", distance: 6,
               color: stil("--viz-text-2"), fontSize: S.label,
               formatter: (p) => pz(p.value) },
    }],
  }, { replaceMerge: ["series", "xAxis", "yAxis"] });

  setzeHtml("t-boden", tabelle(
    [{ titel: "Periode", wert: (z) => z.periode },
     { titel: "Hektar pro Tag", num: true, wert: (z) => pz(z.ha_pro_tag) },
     { titel: "Jahre", num: true, wert: (z) => zahl(z.bis - z.von) },
     { titel: "in der Periode", num: true,
       wert: (z) => zahl(Math.round(z.ha_pro_tag * 365.25 * (z.bis - z.von))) + " ha" }],
    werte
  ));

  /* Die Aufteilung nach Kategorien steht als zweite Tabelle darunter.
     Sie gehört nicht ins Diagramm: der Bestand 2025 und die Tageswerte
     sind zwei verschiedene Größen (Lager gegen Zufluss), und wer sie in
     eine Zeichenfläche legt, lädt zum Verrechnen ein. */
  if (daten.kategorien?.length) {
    setzeHtml("t-boden-kategorien", tabelle(
      [{ titel: `Wofür der Boden ${daten.stand} beansprucht war`, wert: (z) => z.name },
       { titel: "Anteil", num: true, wert: (z) => pz(z.prozent) + " %" },
       { titel: "Fläche", num: true, wert: (z) => pz(z.km2, z.km2 < 100 ? 1 : 0) + " km²" }],
      daten.kategorien
    ));
  }
}

BIO.baueBoden = baueBoden;
})(window.BIO);
