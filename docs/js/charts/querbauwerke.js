/* ===========================================================================
   Biodiversitäts-Dashboard Österreich — Themenstrang: querbauwerke
   ---------------------------------------------------------------------------
   Wird nach js/kern.js geladen; die Helfer kommen aus window.BIO.
   =========================================================================== */
(function (BIO) {
"use strict";
const { stil, zahl, pz, basis, achse, tabelle, setzeText, setzeHtml,
        diagramme, schrift, balkenGitter, kategorieLabel,
        balkenBreite, balkenHoehe, legende, legendeLinks, hoverDunkler } = BIO;

/* --- Warum die Wasserkörper das Ziel verfehlen ------------------------
   Drei liegende Balken, gestapelt aus zwei Teilen. Der Abschnitt
   darüber (`fliessgewaesser`) zeigt, DASS 4.031 von 8.116 Wasserkörpern
   das Ziel verfehlen; dieser nennt die Gründe, die Österreich in
   derselben Meldung dafür angibt.

   WARUM DIE ACHSE BEI 4.031 ENDET UND NICHT BEIM GRÖSSTEN BALKEN: Die
   Länge eines Balkens soll unmittelbar als Anteil an den verfehlenden
   Wasserkörpern lesbar sein. Endete die Achse beim Maximum, füllte die
   Verbauung die Zeichenfläche und sähe nach 100 % aus statt nach 80.

   WARUM ZWEI TEILE JE BALKEN: Die Gruppen überlappen — ein Wasserkörper
   kann verbaut UND von Einträgen belastet sein, die Balken summieren
   sich deshalb auf mehr als 4.031. Ohne den dunklen Teil („einziger
   genannter Grund") wäre das ein stiller Lesefehler: Man addierte drei
   Balken und käme auf 5.542. Der dunkle Teil ist die überschneidungs-
   freie Zahl, und für die Verbauung ist er allein schon größer als der
   ganze zweite Balken.

   ZUR FARBWAHL: keine Ampel. Die drei Zeilen sind Ursachenkategorien,
   keine Bewertungsstufen — `--viz-kritisch` bleibt deshalb draußen
   (Konvention: nur für Status). Beide Töne kommen aus derselben
   sequenziellen Rampe, damit der Stapel als ein Balken mit zwei
   Abstufungen liest und nicht als zwei konkurrierende Kategorien.
   Beide sind in index.html, embed.html und der idl.css definiert,
   jeweils in allen drei Blöcken — am 01.09.2026 gezählt.

   WAS DIESER ABSCHNITT NICHT BEHAUPTET, und warum das hier steht: Die
   Meldung kennt keinen einzigen Wasserkörper in gutem Zustand mit einer
   signifikanten Belastung — „signifikant" heißt in der Richtlinie
   genau, dass die Belastung das Ziel gefährdet. Der Balken zeigt also
   eine Zuschreibung, keine gemessene Wirkung. Das steht in der
   Hinweiszeile und ist der Grund, warum der naheliegende Vergleich
   „belastet gegen unbelastet" gar nicht erst in den Daten liegt. */

const FARBEN = {
  nur:   "--viz-seq-rot-4",
  auch:  "--viz-seq-rot-2",
};

/* Unter dieser Breite trägt ein Segment kein Etikett mehr — es stünde
   sonst neben dem Balken statt darin. Anteil an der Achsenlänge, nicht
   am Balken. */
const ETIKETT_AB = 0.06;

function baueQuerbauwerke(daten) {
  const S = schrift();
  if (!daten?.balken?.length) return;
  const abschnitt = document.getElementById("s-querbauwerke");
  if (abschnitt) abschnitt.style.display = "";

  const feld = document.getElementById("c-querbauwerke");
  if (!feld) return;
  const d = echarts.getInstanceByDom(feld) || echarts.init(feld, null, { renderer: "svg" });
  if (!diagramme.includes(d)) diagramme.push(d);

  const zeilen = daten.balken;
  const nenner = daten.verfehlend;
  const SERIEN = [
    { schluessel: "nur_dieser_grund", name: "einziger genannter Grund",
      farbe: FARBEN.nur },
    { schluessel: "auch_andere", name: "zusammen mit anderen",
      farbe: FARBEN.auch },
  ];

  setzeText("u-querbauwerke",
    `Genannte Belastungen der ${zahl(nenner)} Wasserkörper, die den guten ` +
    `Zustand verfehlen · Meldezyklus ${daten.zyklus}`);
  setzeText("h-querbauwerke", daten.hinweis ?? "");

  balkenHoehe(d, feld, zeilen.length, 52);

  d.setOption({
    ...basis(),
    grid: { ...balkenGitter(feld, { left: 168, right: 60 }), top: 46 },
    legend: legende(feld, {
      top: 0, left: legendeLinks(feld, 168),
      itemWidth: 11, itemHeight: 11, itemGap: 14,
      data: SERIEN.map((s) => s.name),
      textStyle: { color: stil("--viz-text-2"), fontSize: S.serie },
    }),
    tooltip: {
      ...basis().tooltip, trigger: "axis",
      axisPointer: { type: "shadow", shadowStyle: { color: stil("--viz-grid"), opacity: 0.35 } },
      /* Die Kopfzeile nennt die Gesamtzahl und ihren Anteil — die beiden
         Segmente einzeln zu lesen und im Kopf zu addieren wäre genau die
         Rechnung, die der Abschnitt abnehmen soll. */
      formatter: (p) => {
        const z = zeilen[p[0].dataIndex];
        return `<strong>${z.gruppe}</strong><br>` +
          `<strong>${zahl(z.wasserkoerper)}</strong> Wasserkörper` +
          `&nbsp;&nbsp;<span style="color:${stil("--viz-muted")}">` +
          `${pz(z.anteil, 1)} % der verfehlenden</span><br>` +
          p.map((r) => `${r.marker} ${r.seriesName}&nbsp;&nbsp;` +
            `<strong>${zahl(r.value)}</strong>`).join("<br>");
      },
    },
    xAxis: { ...achse(), type: "value", max: nenner, axisLine: { show: false },
      axisLabel: { hideOverlap: true, color: stil("--viz-muted"),
                   fontSize: S.achse, formatter: (v) => zahl(v) } },
    yAxis: { ...achse(), type: "category", inverse: true,
      data: zeilen.map((z) => z.gruppe), splitLine: { show: false },
      axisLabel: { color: stil("--viz-text-2"), fontSize: S.serie, margin: 12,
                   ...kategorieLabel(feld, 168, zeilen.length) } },
    series: SERIEN.map((serie, k) => ({
      name: serie.name, type: "bar", stack: "grund",
      barWidth: balkenBreite(feld, "48%", zeilen.length),
      data: zeilen.map((z) => z[serie.schluessel]),
      itemStyle: {
        color: stil(serie.farbe),
        borderRadius: k === 0 ? [4, 0, 0, 4] : [0, 4, 4, 0],
        borderColor: stil("--viz-surface"), borderWidth: 2,
      },
      emphasis: hoverDunkler(stil(serie.farbe)),
      /* Nur der dunkle Teil wird beschriftet. Er ist die Zahl, die den
         Abschnitt trägt (1.690 allein durch Verbauung); der helle Teil
         ergibt sich als Rest und stünde nur im Weg. */
      label: k === 0 ? {
        show: true, position: "inside", color: stil("--viz-plane"),
        fontSize: S.label, fontWeight: "bold",
        formatter: (r) => (r.value / nenner >= ETIKETT_AB ? zahl(r.value) : ""),
      } : { show: false },
    })),
  }, { replaceMerge: ["series", "xAxis", "yAxis", "legend"] });

  /* Die Notiz trägt drei Dinge, die der Balken nicht zeigen kann: was
     die Verbauung konkret ist, dass die Zwecke sich NICHT aufteilen
     lassen, und wie viele Wasserkörper ganz ohne genannten Grund
     verfehlen. */
  const zwecke = daten.zwecke || [];
  const zweckSatz = zwecke.length
    ? zwecke.map((z) => `${z.zweck} ${zahl(z.wasserkoerper)}`).join(", ")
    : "";

  setzeHtml("n-querbauwerke",
    (daten.querbauwerke
      ? `Quer durch das Gewässer gebaut wird vor allem für zwei Zwecke: ` +
        `<strong>${zahl(daten.querbauwerke)}</strong> Wasserkörper stehen ` +
        `unter Dämmen, Wehren oder Schleusen — ${zweckSatz}. ` +
        `Diese Zahlen summieren sich auf ${zahl(daten.zwecke_nennungen)} und ` +
        `sind <em>keine</em> Aufteilung: Ein Wasserkörper trägt oft mehrere ` +
        `Zwecke. `
      : "") +
    (daten.ohne_belastung
      ? `Bei <strong>${zahl(daten.ohne_belastung)}</strong> Wasserkörpern ` +
        `nennt die Meldung gar keine Belastung, obwohl sie das Ziel ` +
        `verfehlen. `
      : "") +
    (daten.zyklen?.length > 1
      ? `Die Zahl der verbauten Wasserkörper sinkt über die drei ` +
        `Meldezyklen (${daten.zyklen.map((z) => zahl(z.wasserkoerper)).join(" → ")}), ` +
        `doch das ist kein Trend: 2010 hat Österreich fast nur einen ` +
        `Sammelcode gemeldet, die Aufschlüsselung nach Zweck gibt es erst ` +
        `ab ${daten.zyklen[1]?.jahr ?? 2016}.`
      : ""));

  /* Die Tabelle führt AUCH die Gruppen unter der Mindestzahl, die aus
     dem Bild fallen. Ohne sie summierte die Tabelle auf etwas anderes
     als der Text, und niemand könnte nachrechnen. */
  const alle = [
    ...zeilen.map((z) => ({
      gruppe: z.gruppe, wasserkoerper: z.wasserkoerper,
      nur: z.nur_dieser_grund, anteil: z.anteil, imBild: true,
    })),
    ...(daten.kleine_gruppen || []).map((z) => ({
      gruppe: z.gruppe, wasserkoerper: z.wasserkoerper,
      nur: z.nur_dieser_grund,
      anteil: Math.round(z.wasserkoerper / nenner * 1000) / 10,
      imBild: false,
    })),
  ];

  setzeHtml("t-querbauwerke", tabelle(
    [{ titel: "Genannte Belastung", wert: (z) => z.gruppe },
     { titel: "Wasserkörper", num: true, wert: (z) => zahl(z.wasserkoerper) },
     { titel: "Anteil der verfehlenden", num: true,
       wert: (z) => pz(z.anteil, 1) + " %" },
     { titel: "davon einziger Grund", num: true, wert: (z) => zahl(z.nur) },
     { titel: "im Bild", wert: (z) => (z.imBild ? "ja" : "zu klein") }],
    alle
  ));
}

BIO.baueQuerbauwerke = baueQuerbauwerke;
})(window.BIO);
