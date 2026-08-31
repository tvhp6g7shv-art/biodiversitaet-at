/* ===========================================================================
   Biodiversitäts-Dashboard Österreich — Themenstrang: natura2000
   ---------------------------------------------------------------------------
   Wird nach js/kern.js geladen; die Helfer kommen aus window.BIO.
   =========================================================================== */
(function (BIO) {
"use strict";
const { stil, zahl, pz, basis, achse, tabelle, setzeText, setzeHtml,
        diagramme, schrift, istSchmal, balkenGitter, kategorieLabel,
        balkenBreite, balkenHoehe, legende, legendeLinks, hoverDunkler } = BIO;

/* --- Waldlebensraumtypen: Fläche gegen Bewertung ----------------------
   Zwei gestapelte Balken, auf 100 % normiert. Beide zeigen denselben
   Wald aus derselben EU-Meldung — und kommen zu 92,8 % gegen 28,1 %.

   WARUM ÜBERHAUPT ZWEI BALKEN UND NICHT EINER: Weil beide Zahlen
   kursieren und beide belegbar sind. Ein Balken müsste sich für eine
   entscheiden; wer die andere kennt, hielte die Grafik für falsch.
   Nebeneinander wird aus dem Widerspruch der Inhalt.

   DIE MODELLENTSCHEIDUNG steckt im ETL, nicht hier: Für die untere
   Zeile werden „unzureichend" und „schlecht" zu „nicht gut"
   zusammengefasst. Das ist keine Vereinfachung, sondern die
   Zusammenfassung, die die FFH-Richtlinie selbst vornimmt — U1 und U2
   sind beide „unfavourable". Die Vierteilung bleibt in der Tabelle.

   ZUR FARBWAHL: `--viz-gut` / `--viz-kritisch` / `--viz-muted`. Die
   Hausregel hält `--viz-kritisch` für Statusfarben frei — und genau das
   ist es hier: die amtliche Einstufung der Quelle, nicht meine Wertung.
   Dieselbe Begründung wie in `erhaltung.js`. „Unbekannt" bekommt
   bewusst keinen Ton der Ampel, sondern einen neutralen Grauton: Es ist
   keine schlechtere Stufe als „nicht gut", sondern gar keine Stufe.

   ALLE DREI TOKEN sind in beiden Auslieferungen definiert — in
   index.html, in embed.html und in der idl.css. Bewusst kein
   `--viz-seq-rot-*`: das steht nur in der idl.css.

   BESCHRIFTUNG NUR IM ERSTEN SEGMENT: Die beiden Zahlen, um die es
   geht, stehen im Balken. Die übrigen Segmente bleiben stumm — das
   kleinste ist 0,2 % breit. */

const FARBEN = ["--viz-gut", "--viz-kritisch", "--viz-muted"];

function baueNatura2000(daten) {
  const S = schrift();
  if (!daten?.vergleich?.zeilen?.length) return;
  const abschnitt = document.getElementById("s-natura2000");
  if (abschnitt) abschnitt.style.display = "";

  const feld = document.getElementById("c-natura2000");
  if (!feld) return;
  const d = echarts.getInstanceByDom(feld) || echarts.init(feld, null, { renderer: "svg" });
  if (!diagramme.includes(d)) diagramme.push(d);

  const zeilen = daten.vergleich.zeilen;
  const faecher = daten.vergleich.faecher;

  setzeText("u-natura2000",
    `Dieselbe Meldung Österreichs an die EU, zwei Messweisen · ` +
    `Berichtsperiode ${daten.periode}`);
  setzeText("h-natura2000", daten.hinweis ?? "");

  balkenHoehe(d, feld, zeilen.length, 44);

  d.setOption({
    ...basis(),
    grid: { ...balkenGitter(feld, { left: 150, right: 60 }), top: 46 },
    legend: legende(feld, {
      top: 0, left: legendeLinks(feld, 150),
      itemWidth: 11, itemHeight: 11, itemGap: 14, data: faecher,
      textStyle: { color: stil("--viz-text-2"), fontSize: S.serie },
    }),
    tooltip: {
      ...basis().tooltip, trigger: "axis",
      axisPointer: { type: "shadow", shadowStyle: { color: stil("--viz-grid"), opacity: 0.35 } },
      formatter: (p) => {
        const z = zeilen[p[0].dataIndex];
        return `<strong>${z.name}</strong><br>` +
          `<span style="color:${stil("--viz-muted")}">${z.grundlage}</span><br>` +
          p.map((r) => `${r.marker} ${r.seriesName}&nbsp;&nbsp;` +
            `<strong>${pz(r.value, 1)} %</strong>`).join("<br>");
      },
    },
    xAxis: { ...achse(), type: "value", max: 100, axisLine: { show: false },
      axisLabel: { hideOverlap: true, color: stil("--viz-muted"),
                   fontSize: S.achse, formatter: (v) => v + " %" } },
    yAxis: { ...achse(), type: "category", inverse: true,
      data: zeilen.map((z) => z.name), splitLine: { show: false },
      axisLabel: { color: stil("--viz-text-2"), fontSize: S.serie, margin: 12,
                   ...kategorieLabel(feld, 150, zeilen.length) } },
    series: faecher.map((name, k) => ({
      name, type: "bar", stack: "zustand",
      barWidth: balkenBreite(feld, "48%", zeilen.length),
      data: zeilen.map((z) => z.werte[k]),
      itemStyle: {
        color: stil(FARBEN[k]),
        borderRadius: k === 0 ? [4, 0, 0, 4]
          : (k === faecher.length - 1 ? [0, 4, 4, 0] : 0),
        borderColor: stil("--viz-surface"), borderWidth: 2,
      },
      emphasis: hoverDunkler(stil(FARBEN[k])),
      /* Nur das erste Fach beschriftet — und auch nur, wenn es breit
         genug ist. Unter 20 % fällt das Label weg, statt aus dem
         Balken zu ragen. */
      label: k === 0 ? {
        show: true, position: "inside", color: stil("--viz-plane"),
        fontSize: S.label, fontWeight: "bold",
        formatter: (r) => (r.value >= 20 ? pz(r.value, 1) + " %" : ""),
      } : { show: false },
    })),
  }, { replaceMerge: ["series", "xAxis", "yAxis", "legend"] });

  /* Die Notiz trägt das, was der Balken nicht zeigen kann: WARUM die
     beiden Zeilen auseinandergehen. Ohne sie sieht der Abschnitt aus
     wie ein Datenfehler. Dazu die dritte Messweise und die Waldarten,
     die beide nicht in die Grafik passen, ohne sie zu überladen. */
  const w = daten.waldarten;
  setzeHtml("n-natura2000",
    `Der Abstand entsteht durch die Zusammenfassungsregel: Ein Waldtyp gilt ` +
    `als ungünstig, sobald <strong>einer von vier</strong> Teilwerten ` +
    `ungünstig ist — auch wenn seine Fläche zum größten Teil in gutem ` +
    `Zustand ist. Eine dritte Lesart kommt zu einem dritten Ergebnis: Nach ` +
    `dem Teilwert Fläche allein sind <strong>${pz(daten.area_guenstig_prozent, 0)} %</strong> ` +
    `günstig bewertet.` +
    (w ? ` Deutlich schlechter steht es um die Arten des Waldes: Von ihnen ` +
         `erreichen nur <strong>${pz(w.guenstig_prozent, 0)} %</strong> einen ` +
         `günstigen Zustand.` : ""));

  /* Die Tabelle zeigt die Vierteilung, die die Grafik zusammenfasst,
     und die beiden biogeografischen Regionen einzeln. */
  /* Felder BENANNT statt über Positionen zusammengesteckt: Die beiden
     Messweisen haben unterschiedlich viele Stufen — die Fläche kennt
     keine Zweiteilung in „unzureichend" und „schlecht". Ein
     Positionsarray würde die Flächenwerte um eine Spalte verschoben in
     die Tabelle schreiben, ohne dass es auffiele. */
  const f = daten.nach_flaeche.anteile;      // gut · nicht gut · unbekannt
  const b = daten.nach_bewertung.anteile;    // FV · U1 · U2 · XX
  const zusammen = (a) => round1(a[1] + a[2]);
  function round1(x) { return Math.round(x * 10) / 10; }

  const tabellenZeilen = [
    { name: "Nach Fläche gemessen", gut: f[0], nicht_gut: f[1],
      u1: null, u2: null, unbekannt: f[2],
      grundlage: zeilen[0].grundlage },
    { name: "Nach Gesamtbewertung", gut: b[0], nicht_gut: zusammen(b),
      u1: b[1], u2: b[2], unbekannt: b[3],
      grundlage: zeilen[1].grundlage },
    ...daten.regionen.map((r) => ({
      name: `davon ${r.name}`,
      gut: r.anteile[0], nicht_gut: zusammen(r.anteile),
      u1: r.anteile[1], u2: r.anteile[2], unbekannt: r.anteile[3],
      grundlage: `${zahl(r.bewertungen)} Bewertungen`,
    })),
  ];
  const prozent = (x) => (x == null ? "—" : pz(x, 1) + " %");
  setzeHtml("t-natura2000", tabelle(
    [{ titel: "Messweise", wert: (z) => z.name },
     { titel: "gut / günstig", num: true, wert: (z) => prozent(z.gut) },
     { titel: "nicht gut", num: true, wert: (z) => prozent(z.nicht_gut) },
     { titel: "davon unzureichend", num: true, wert: (z) => prozent(z.u1) },
     { titel: "davon schlecht", num: true, wert: (z) => prozent(z.u2) },
     { titel: "unbekannt", num: true, wert: (z) => prozent(z.unbekannt) },
     { titel: "Grundlage", wert: (z) => z.grundlage }],
    tabellenZeilen
  ));
}

BIO.baueNatura2000 = baueNatura2000;
})(window.BIO);
