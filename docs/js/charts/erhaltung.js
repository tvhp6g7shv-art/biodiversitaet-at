/* ===========================================================================
   Biodiversitäts-Dashboard Österreich — Themenstrang: erhaltung
   ---------------------------------------------------------------------------
   Wird nach js/kern.js geladen; die Helfer kommen aus window.BIO.
   =========================================================================== */
(function (BIO) {
"use strict";
const { stil, zahl, pz, basis, achse, tabelle, setzeText, setzeHtml,
        diagramme, schrift, istSchmal, balkenGitter, kategorieLabel, balkenBreite, balkenHoehe,
        legende, hoverDunkler } = BIO;

/* --- 05 — Erhaltungszustand nach Artikel 17 ---------------------------
   Zwei gestapelte Balken, auf 100 % normiert: Lebensraumtypen und Arten.

   ZUR FARBWAHL, weil sie gegen die Hausregel zu verstoßen scheint:
   `--viz-kritisch` ist laut Konventionen Statusfarben vorbehalten und
   „nur für Veränderungen, immer mit Pfeil und Text". Hier trägt sie die
   Kategorie „schlechter Erhaltungszustand" — und das IST ein Status, und
   zwar die amtliche Einstufung der Quelle, nicht meine Wertung. Die
   FFH-Richtlinie selbst arbeitet mit einer Ampel (günstig / unzureichend /
   schlecht). Eine Grafik, die das in Graustufen übersetzt, verschweigt die
   Bewertung, die im Datensatz steht.

   „unbekannt" bekommt bewusst KEINEN Ton der Ampel, sondern einen
   neutralen Grauton: Es ist keine schlechtere Stufe als „schlecht",
   sondern gar keine Stufe.

   KORREKTUR 25.08.2026 — zwei Toene getauscht:

   „unzureichend" stand auf --viz-series-4 (#e3ead9, fast weiss). Das ist
   ein Kategorienton ohne Wertung, und zwischen dem Gruen und dem Rot las
   er sich wie eine EIGENE Bedeutung statt wie die mittlere Stufe einer
   Ampel. Jetzt --viz-seq-rot-3: der zurueckhaltendste der benutzten
   Rottoene. Damit liegen „unzureichend" und „schlecht" erkennbar in
   derselben Familie, mit „schlecht" als dem auffaelligeren.

   „unbekannt" stand auf --viz-grid — Limette bei 10 % Deckung, praktisch
   unsichtbar. Derselbe Fehler wie bei „ohne Angabe" in biotoptypen.js.
   Jetzt --viz-muted (#97a888): neutral, gehoert keiner der beiden
   Bedeutungsfarben an, und man sieht es. Eine Luecke soll unauffaellig
   sein, nicht unsichtbar.

   KEINE BESCHRIFTUNG IN DEN SEGMENTEN. Das kleinste ist 3 % breit — dort
   passt keine Zahl hinein, und eine Zahl, die nur manchmal erscheint,
   liest sich als Fehler. Die Werte stehen im Tooltip und in der Tabelle. */

/* Reihenfolge: guenstig · unzureichend · schlecht · unbekannt */
const FARBEN = ["--viz-gut", "--viz-seq-rot-3", "--viz-kritisch", "--viz-muted"];

function baueErhaltung(daten) {
  const S = schrift();
  if (!daten?.gruppen?.length) return;
  const abschnitt = document.getElementById("s-erhaltung");
  if (abschnitt) abschnitt.style.display = "";

  const feld = document.getElementById("c-erhaltung");
  if (!feld) return;
  const d = echarts.getInstanceByDom(feld) || echarts.init(feld, null, { renderer: "svg" });
  if (!diagramme.includes(d)) diagramme.push(d);

  const gruppen = daten.gruppen;
  const kategorien = daten.kategorien.map((k) => k.name);

  setzeText("u-erhaltung",
    `Anteil der Bewertungen je Zustand · Berichtsperiode ${daten.periode}`);
  setzeText("h-erhaltung", daten.hinweis ?? "");

  /* Eng braucht jede Kategorie eine eigene Zeile fuer ihren Namen.
     Die Kartenhoehe kommt deshalb aus der Zahl der Kategorien und
     nicht aus dem CSS — sonst schiebt ECharts die Zeilen enger
     zusammen, als der Name hoch ist, und die Namen kleben am
     Balken der Zeile darueber. Muss VOR setOption stehen. */
  balkenHoehe(d, feld, gruppen.length, 36);

  d.setOption({
    ...basis(),
    grid: { ...balkenGitter(feld, { left: 130, right: 60 }), top: 46 },
    legend: legende(feld, {
      top: 0, left: istSchmal(feld) ? 0 : 130,
      itemWidth: 11, itemHeight: 11, itemGap: 14, data: kategorien,
      textStyle: { color: stil("--viz-text-2"), fontSize: S.serie },
    }),
    tooltip: {
      ...basis().tooltip, trigger: "axis",
      axisPointer: { type: "shadow", shadowStyle: { color: stil("--viz-grid"), opacity: 0.35 } },
      formatter: (p) => {
        const g = gruppen[p[0].dataIndex];
        return `<strong>${g.name}</strong><br>` +
          `<span style="color:${stil("--viz-muted")}">${zahl(g.bewertungen)} ` +
          `Bewertungen aus ${zahl(g.schutzgueter)} Schutzgütern</span><br>` +
          p.map((r) => `${r.marker} ${r.seriesName}&nbsp;&nbsp;` +
            `<strong>${pz(r.value, 0)} %</strong>`).join("<br>");
      },
    },
    xAxis: { ...achse(), type: "value", max: 100, axisLine: { show: false },
      axisLabel: { hideOverlap: true, color: stil("--viz-muted"),
                   fontSize: S.achse, formatter: (v) => v + " %" } },
    yAxis: { ...achse(), type: "category", inverse: true,
      data: gruppen.map((g) => g.name), splitLine: { show: false },
      axisLabel: { color: stil("--viz-text-2"), fontSize: S.serie, margin: 12,
                   ...kategorieLabel(feld, 130, gruppen.length) } },
    series: kategorien.map((name, k) => ({
      name, type: "bar", stack: "zustand", barWidth: balkenBreite(feld, "56%"),
      data: gruppen.map((g) => g.anteile[k]),
      itemStyle: {
        color: stil(FARBEN[k]),
        borderRadius: k === 0 ? [4, 0, 0, 4]
          : (k === kategorien.length - 1 ? [0, 4, 4, 0] : 0),
        /* 2-px-Fuge in Kartenfarbe: macht die Segmentgrenzen unabhängig
           von der Farbwahrnehmung sichtbar. */
        borderColor: stil("--viz-surface"), borderWidth: 2,
      },
      emphasis: hoverDunkler(stil(FARBEN[k])),
      label: { show: false },
    })),
  }, { replaceMerge: ["series", "xAxis", "yAxis", "legend"] });

  /* Der Hinweis auf die fehlende Folgeperiode gehört sichtbar unter die
     Grafik: Ohne ihn liest sich eine Momentaufnahme wie ein aktueller
     Stand — die Zahlen sind aus der Periode 2013–2018. */
  if (daten.naechste_vorhanden === false) {
    setzeHtml("n-erhaltung",
      `Dies ist die letzte abgeschlossene Berichtsperiode. Die Meldung für ` +
      `<strong>${daten.naechste_periode}</strong> war bis ${daten.naechste_faellig} ` +
      `fällig und ist noch nicht veröffentlicht — bis dahin bleibt es bei ` +
      `dieser einen Momentaufnahme statt eines Vergleichs.`);
  }

  setzeHtml("t-erhaltung", tabelle(
    [{ titel: "Gruppe", wert: (z) => z.name },
     ...daten.kategorien.map((k, i) => ({
       titel: k.name, num: true, wert: (z) => pz(z.anteile[i], 0) + " %",
     })),
     { titel: "Bewertungen", num: true, wert: (z) => zahl(z.bewertungen) },
     { titel: "Schutzgüter", num: true, wert: (z) => zahl(z.schutzgueter) }],
    gruppen
  ));
}

BIO.baueErhaltung = baueErhaltung;
})(window.BIO);
