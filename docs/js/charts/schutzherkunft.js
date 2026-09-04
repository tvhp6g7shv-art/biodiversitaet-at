/* ===========================================================================
   Biodiversitäts-Dashboard Österreich — Themenstrang: schutzherkunft
   ---------------------------------------------------------------------------
   Wird nach js/kern.js geladen; die Helfer kommen aus window.BIO.
   =========================================================================== */
(function (BIO) {
"use strict";
const { stil, zahl, pz, basis, achse, tabelle, setzeText, setzeHtml,
        diagramme, schrift, balkenGitter, kategorieLabel,
        balkenBreite, balkenHoehe, legende, legendeLinks, hoverDunkler } = BIO;

/* --- Woher der Schutz kommt -------------------------------------------
   Zwei liegende Balken, jeder gestapelt aus zwei Teilen. Der Abschnitt
   darüber (`schutzgebiete`) zeigt EINE Zahl im Zeitverlauf: 29,3 % der
   Landesfläche stehen unter Schutz. Dieser zerlegt sie und stellt ihr
   den EU-Schnitt gegenüber.

   MUSS DIREKT HINTER `schutzgebiete` STEHEN. Getrennt gelesen ist keiner
   von beiden falsch, aber der erste allein lässt offen, wer diesen
   Schutz eigentlich beschlossen hat — und das ist der ganze Befund.

   WARUM NUR ZWEI BALKEN UND NICHT 27: Fünf der neun Abschnitte dieser
   Planungsrunde sind Balken-Ländervergleiche. Zwei davon nebeneinander
   lesen sich als dieselbe Grafik mit anderer Beschriftung. Die Rangfolge
   steht deshalb im Text, nicht im Bild — das Bild trägt die Aufteilung,
   und die ist mit zwei Balken schärfer als mit 27.

   WARUM KEINE ZIELMARKE BEI 30 %: Die 30 % der EU-Biodiversitäts-
   strategie sind ein Ziel für die EU ALS GANZES. Eine senkrechte Linie
   neben dem österreichischen Balken behauptete ein Ziel je Mitgliedstaat,
   das es so nicht gibt. Die Zahl steht in der Hinweiszeile und in der
   Notiz, wo sie eingeordnet werden kann. Der Abschnitt `schutzgebiete`
   zeichnet sie — dort als Bezugspunkt einer Zeitreihe, nicht als
   Bewertung eines Ländervergleichs.

   WARUM DIE ACHSE BEI 35 ENDET: Ein Ende bei 30 machte die Marke, die
   hier bewusst fehlt, zur Achsengrenze und damit doch zum Maßstab. Ein
   Ende bei 100 (Anteil an der Landesfläche) drückte beide Stapel auf ein
   Viertel der Breite, und die Aufteilung wäre nicht mehr lesbar. 35 ist
   die nächste Fünferstufe über dem größeren der beiden Werte.

   ZUR FARBWAHL: keine sequenzielle Rampe, sondern zwei Serientöne. Die
   beiden Teile sind nicht zwei Stufen einer Skala, sondern zwei Wege zur
   Ausweisung — eine Richtlinie und eine Landesentscheidung. Verfügbar
   sind auf Pages ohnehin nur `--viz-seq-rot-*` und die Serientöne; Rot
   wäre hier eine Wertung, die die Daten nicht hergeben. `series-1` und
   `series-2` sind die beiden, die in jeder Palette sicher unterscheidbar
   sind. */

const FARBEN = {
  natura:   "--viz-series-1",
  national: "--viz-series-2",
};

/* Obergrenze der Achse in Prozentpunkten — siehe Kopfkommentar. */
const ACHSE_MAX = 35;

/* Unter diesem Anteil an der Achsenlänge trägt ein Segment kein Etikett
   mehr. Bei den vier Segmenten dieses Abschnitts (7,8 bis 18,6 Punkte auf
   einer Achse bis 35) greift die Schwelle nicht — sie steht für den Fall,
   dass ein künftiger Jahrgang einen Teil zusammenschrumpfen lässt. */
const ETIKETT_AB = 0.08;

function baueSchutzherkunft(daten) {
  const S = schrift();
  if (!daten?.balken?.length) return;
  const abschnitt = document.getElementById("s-schutzherkunft");
  if (abschnitt) abschnitt.style.display = "";

  const feld = document.getElementById("c-schutzherkunft");
  if (!feld) return;
  const d = echarts.getInstanceByDom(feld) || echarts.init(feld, null, { renderer: "svg" });
  if (!diagramme.includes(d)) diagramme.push(d);

  const zeilen = daten.balken;
  const at = zeilen[0];
  const eu = zeilen[1];

  const SERIEN = [
    { schluessel: "natura",   name: "Natura 2000",          farbe: FARBEN.natura },
    { schluessel: "national", name: "national ausgewiesen", farbe: FARBEN.national },
  ];

  setzeText("u-schutzherkunft",
    `Anteil an der Landesfläche, aufgeteilt nach der Art der Ausweisung · ` +
    `Stand Ende ${daten.stichjahr}`);
  setzeText("h-schutzherkunft", daten.hinweis ?? "");

  balkenHoehe(d, feld, zeilen.length, 46);

  d.setOption({
    ...basis(),
    grid: { ...balkenGitter(feld, { left: 120, right: 74 }), top: 46 },
    legend: legende(feld, {
      top: 0, left: legendeLinks(feld, 120),
      itemWidth: 11, itemHeight: 11, itemGap: 14,
      data: SERIEN.map((s) => s.name),
      textStyle: { color: stil("--viz-text-2"), fontSize: S.serie },
    }),
    tooltip: {
      ...basis().tooltip, trigger: "axis",
      axisPointer: { type: "shadow", shadowStyle: { color: stil("--viz-grid"), opacity: 0.35 } },
      /* Die Kopfzeile nennt die Summe. Die beiden Teile einzeln zu lesen
         und im Kopf zu addieren wäre genau die Rechnung, die der
         Abschnitt abnehmen soll. */
      formatter: (p) => {
        const z = zeilen[p[0].dataIndex];
        return `<strong>${z.gebiet}</strong><br>` +
          `<strong>${pz(z.gesamt, 1)} %</strong> der Landesfläche geschützt` +
          `&nbsp;&nbsp;<span style="color:${stil("--viz-muted")}">` +
          `${pz(z.anteil_national, 1)} % davon national</span><br>` +
          p.filter((r) => r.seriesName !== "Summe")
           .map((r) => `${r.marker} ${r.seriesName}&nbsp;&nbsp;` +
             `<strong>${pz(r.value, 1)}</strong> Punkte`).join("<br>");
      },
    },
    xAxis: { ...achse(), type: "value", max: ACHSE_MAX, axisLine: { show: false },
      axisLabel: { hideOverlap: true, color: stil("--viz-muted"),
                   fontSize: S.achse, formatter: (v) => zahl(v) + " %" } },
    yAxis: { ...achse(), type: "category", inverse: true,
      data: zeilen.map((z) => z.gebiet), splitLine: { show: false },
      axisLabel: { color: stil("--viz-text-2"), fontSize: S.serie, margin: 12,
                   ...kategorieLabel(feld, 120, zeilen.length) } },
    series: [
      ...SERIEN.map((serie, k) => ({
        name: serie.name, type: "bar", stack: "herkunft",
        barWidth: balkenBreite(feld, "48%", zeilen.length),
        data: zeilen.map((z) => z[serie.schluessel]),
        itemStyle: {
          color: stil(serie.farbe),
          borderRadius: k === 0 ? [4, 0, 0, 4] : [0, 4, 4, 0],
          borderColor: stil("--viz-surface"), borderWidth: 2,
        },
        emphasis: hoverDunkler(stil(serie.farbe)),
        /* Beide Teile tragen ihre Zahl. Anders als bei den Querbauwerken
           ist hier keiner der beiden ein Rest, der sich von selbst ergibt
           — die Aufteilung IST der Befund. */
        label: {
          show: true, position: "inside", color: stil("--viz-plane"),
          fontSize: S.label, fontWeight: "bold",
          formatter: (r) => (r.value / ACHSE_MAX >= ETIKETT_AB ? pz(r.value, 1) : ""),
        },
      })),
      /* Ein unsichtbarer dritter Stapelteil trägt die Summe an das rechte
         Balkenende. Ohne ihn stünde die Zahl, um die es geht — 29,3 gegen
         26,4 — nur im Tooltip und in der Notiz. `silent` hält ihn aus dem
         Hover heraus, und er steht nicht in `legend.data`. */
      {
        name: "Summe", type: "bar", stack: "herkunft", silent: true,
        barWidth: balkenBreite(feld, "48%", zeilen.length),
        data: zeilen.map(() => 0),
        itemStyle: { color: "transparent" },
        label: {
          show: true, position: "right", color: stil("--viz-text-2"),
          fontSize: S.label, fontWeight: "bold",
          formatter: (r) => pz(zeilen[r.dataIndex].gesamt, 1) + " %",
        },
      },
    ],
  }, { replaceMerge: ["series", "xAxis", "yAxis", "legend"] });

  /* Die Notiz trägt, was das Bild bewusst nicht zeigt: die Rangfolge und
     die 30-Prozent-Marke — beides mit der Einordnung, ohne die sie in die
     Irre führen. */
  setzeHtml("n-schutzherkunft",
    `Von den <strong>${pz(at.gesamt, 1)} Prozent</strong> geschützter Landesfläche ` +
    `gehen ${pz(at.natura, 1)} Punkte auf Natura 2000 zurück und ` +
    `${pz(at.national, 1)} Punkte auf Ausweisungen der Länder — ` +
    `<strong>${pz(at.anteil_national, 1)} Prozent</strong> des Schutzes stehen also ` +
    `nicht wegen einer EU-Richtlinie unter Schutz. Im EU-Schnitt sind es ` +
    `${pz(eu.anteil_national, 1)} Prozent. ` +
    (daten.rang
      ? `Mit seinem Gesamtanteil liegt Österreich auf Platz ${zahl(daten.rang)} ` +
        `von ${zahl(daten.mitgliedstaaten)}; ${zahl(daten.ueber_ziel)} Mitgliedstaaten ` +
        `kommen über ${zahl(daten.eu_ziel)} Prozent. Diese Marke gilt der EU als ` +
        `Ganzes — die EU selbst steht bei ${pz(eu.gesamt, 1)} Prozent.`
      : ""));

  setzeHtml("t-schutzherkunft", tabelle(
    [{ titel: "Gebiet", wert: (z) => z.gebiet },
     { titel: "Natura 2000", num: true, wert: (z) => pz(z.natura, 1) + " Punkte" },
     { titel: "national ausgewiesen", num: true,
       wert: (z) => pz(z.national, 1) + " Punkte" },
     { titel: "geschützt gesamt", num: true, wert: (z) => pz(z.gesamt, 1) + " %" },
     { titel: "davon national", num: true,
       wert: (z) => pz(z.anteil_national, 1) + " %" }],
    zeilen
  ));
}

BIO.baueSchutzherkunft = baueSchutzherkunft;
})(window.BIO);
