/* ===========================================================================
   Biodiversitäts-Dashboard Österreich — Themenstrang: rotelisten
   ---------------------------------------------------------------------------
   Wird nach js/kern.js geladen; die Helfer kommen aus window.BIO.
   =========================================================================== */
(function (BIO) {
"use strict";
const { stil, zahl, basis, achse, tabelle, setzeText, setzeHtml,
        diagramme, schrift, istSchmal, balkenGitter, kategorieLabel, balkenBreite, balkenHoehe,
        legende, hoverDunkler } = BIO;

/* --- 04 — Wie alt das Wissen über gefährdete Arten ist ----------------
   Liegende Balken, eine Zeile je Tiergruppe, sortiert nach Alter.

   DIE BAUFORM IST DIE AUSSAGE. Jeder Balken ist zweigeteilt:

     Segment 1  die Jahre INNERHALB des Zeitraums, den das Umweltbundesamt
                selbst für angemessen hält (sechs oder zwölf Jahre, je
                Gruppe verschieden)
     Segment 2  die Jahre DARÜBER HINAUS

   Zusammen ergeben sie das Alter der Liste. Damit zeigt eine einzige
   Zeichenfläche dreierlei: wie alt, wie alt sie sein dürfte, und wie weit
   sie darüber ist. Ein einfacher Altersbalken könnte das nicht — er
   behandelte Vögel (2017, Soll 6 Jahre) und Wasserkäfer (2005, Soll 12)
   gleich, obwohl die einen ihr Soll um drei Jahre reißen und die anderen
   um neun.

   Die Schwelle stammt nicht von mir. Sie steht in der Quelltabelle
   („Aktualisierungszeitraum"), Gruppe für Gruppe. Ein Dashboard, das hier
   eine runde eigene Zahl setzt, gibt eine fremde Fachentscheidung als
   eigene aus.

   ZUR FARBE: `--viz-kritisch` trägt das Überzugssegment. Nach den
   Konventionen ist diese Farbe Statusfarben vorbehalten — und genau das
   ist sie hier: „überfällig" ist die Statusspalte der Quelle, keine
   Kategorie, die ich erfunden habe.

   Die vier Gruppen OHNE jede Rote Liste stehen bewusst nicht im
   Diagramm. Ein Balken der Länge null läse sich als „gerade erst
   aktualisiert" — das genaue Gegenteil. Sie stehen als Satz darunter. */

function baueRoteListen(daten) {
  const S = schrift();
  if (!daten?.eintraege?.length) return;
  const abschnitt = document.getElementById("s-rotelisten");
  if (abschnitt) abschnitt.style.display = "";

  const feld = document.getElementById("c-rotelisten");
  if (!feld) return;
  const d = echarts.getInstanceByDom(feld) || echarts.init(feld, null, { renderer: "svg" });
  if (!diagramme.includes(d)) diagramme.push(d);

  /* Nur Gruppen mit Jahresangabe, älteste oben. */
  const zeilen = daten.eintraege
    .filter((e) => e.jahr !== null && e.jahr !== undefined)
    .sort((a, b) => b.alter - a.alter);

  const ohne = daten.ohne_liste_namen || [];

  setzeText("u-rotelisten",
    `Jahre seit der letzten Einstufung · ${zeilen.length} Tiergruppen · ` +
    `Stand der Übersicht Oktober 2025`);
  setzeText("h-rotelisten", daten.hinweis ?? "");

  /* Zwei Hauptfarben statt Rampenton plus Alarmfarbe (25.08.2026).
     Der Balken kennt genau zwei Zustände — innerhalb des Soll-Zeitraums
     und darüber hinaus. Das ist ein Gegensatzpaar, keine Abstufung, und
     gehört deshalb auf das Hauptpaar --viz-gut / --viz-kritisch.
     Vorher stand innen --viz-seq-3, ein Ton aus einer Rampe, die hier
     gar nicht benutzt wird. */
  const farbeInnen = stil("--viz-gut");
  const farbeUeber = stil("--viz-kritisch");

  /* Kopfraum rechts für die Gesamtbeschriftung am längsten Balken. */
  const maxAlter = Math.max(...zeilen.map((z) => z.alter));

  /* Eng braucht jede Kategorie eine eigene Zeile fuer ihren Namen.
     Die Kartenhoehe kommt deshalb aus der Zahl der Kategorien und
     nicht aus dem CSS — sonst schiebt ECharts die Zeilen enger
     zusammen, als der Name hoch ist, und die Namen kleben am
     Balken der Zeile darueber. Muss VOR setOption stehen. */
  balkenHoehe(d, feld, zeilen.length, 36);

  d.setOption({
    ...basis(),
    /* `top: 46` überschreibt die 10 aus balkenGitter — sonst klebt die
       Legende am obersten Balken. */
    grid: { ...balkenGitter(feld, { left: 150, right: 76 }), top: 46 },
    legend: legende(feld, {
      top: 0, left: istSchmal(feld) ? 0 : 150,
      itemWidth: 11, itemHeight: 11, itemGap: 14,
      data: ["im Soll-Zeitraum", "darüber hinaus"],
      textStyle: { color: stil("--viz-text-2"), fontSize: S.serie },
    }),
    tooltip: {
      ...basis().tooltip, trigger: "axis",
      axisPointer: { type: "shadow", shadowStyle: { color: stil("--viz-grid"), opacity: 0.35 } },
      formatter: (p) => {
        const z = zeilen[p[0].dataIndex];
        const ueber = z.ueberzug > 0
          ? `<br><span style="color:${stil("--viz-kritisch")}">` +
            `${zahl(z.ueberzug)} Jahre über dem Soll</span>`
          : `<br><span style="color:${stil("--viz-muted")}">im Soll-Zeitraum</span>`;
        return `<strong>${z.gruppe}</strong><br>` +
          `Letzte Einstufung ${z.jahr}, also vor ${zahl(z.alter)} Jahren<br>` +
          `<span style="color:${stil("--viz-muted")}">` +
          `Neuauflage vorgesehen alle ${zahl(z.soll_jahre)} Jahre · ` +
          `Status: ${z.status}</span>` + ueber;
      },
    },
    xAxis: { ...achse(), type: "value", min: 0,
             axisLine: { show: false },
             axisLabel: { hideOverlap: true, color: stil("--viz-muted"),
                          fontSize: S.achse, formatter: (v) => v + " J." } },
    yAxis: { ...achse(), type: "category", inverse: true,
             data: zeilen.map((z) => z.gruppe), splitLine: { show: false },
             axisLabel: { color: stil("--viz-text-2"), fontSize: S.serie,
                          margin: 12,
                          ...kategorieLabel(feld, 150, zeilen.length) } },
    series: [
      {
        name: "im Soll-Zeitraum", type: "bar", stack: "alter", barWidth: balkenBreite(feld, "64%"),
        data: zeilen.map((z) => Math.min(z.alter, z.soll_jahre)),
        itemStyle: { color: farbeInnen, borderRadius: [4, 0, 0, 4] },
        emphasis: hoverDunkler(farbeInnen),
        label: { show: false },
      },
      {
        name: "darüber hinaus", type: "bar", stack: "alter", barWidth: balkenBreite(feld, "64%"),
        data: zeilen.map((z) => Math.max(0, z.ueberzug)),
        itemStyle: {
          color: farbeUeber, borderRadius: [0, 4, 4, 0],
          /* 2-px-Fuge in Kartenfarbe: macht die Grenze zwischen den beiden
             Segmenten unabhängig von der Farbwahrnehmung sichtbar. */
          borderColor: stil("--viz-surface"), borderWidth: 2,
        },
        emphasis: hoverDunkler(farbeUeber),
        /* Die Gesamtzahl steht rechts außen — sie ist das, was man
           ablesen will („32 Jahre"), und passt in kein Segment. */
        label: {
          show: true, position: "right", distance: 8,
          color: stil("--viz-text-2"), fontSize: S.label,
          formatter: (p) => zahl(zeilen[p.dataIndex].alter) + " J.",
        },
      },
    ],
  }, { replaceMerge: ["series", "xAxis", "yAxis", "legend"] });

  /* Die Gruppen ohne jede Liste als Satz, nicht als Balken. */
  if (ohne.length) {
    setzeHtml("n-rotelisten",
      `Für ${ohne.length} weitere Gruppen gibt es <strong>überhaupt keine</strong> ` +
      `Rote Liste: ${ohne.join(", ")}. Sie fehlen im Diagramm, weil ein Balken ` +
      `der Länge null sich als „gerade aktualisiert" läse.`);
  }

  setzeHtml("t-rotelisten", tabelle(
    [{ titel: "Tiergruppe", wert: (z) => z.gruppe },
     { titel: "Letzte Einstufung", num: true, wert: (z) => z.jahr },
     { titel: "Alter", num: true, wert: (z) => zahl(z.alter) + " J." },
     { titel: "Soll-Zeitraum", num: true, wert: (z) => zahl(z.soll_jahre) + " J." },
     { titel: "Überzug", num: true,
       wert: (z) => z.ueberzug > 0 ? zahl(z.ueberzug) + " J." : "–" },
     { titel: "Status", wert: (z) => z.status }],
    zeilen
  ));
}

BIO.baueRoteListen = baueRoteListen;
})(window.BIO);
