/* ===========================================================================
   Biodiversitäts-Dashboard Österreich — Themenstrang: lebensraeume
   ---------------------------------------------------------------------------
   Wird nach js/kern.js geladen; die Helfer kommen aus window.BIO.
   =========================================================================== */
(function (BIO) {
"use strict";
const { stil, zahl, pz, basis, achse, tabelle, setzeText, setzeHtml,
        diagramme, schrift, istSchmal, balkenGitter, kategorieLabel, balkenBreite, balkenHoehe,
        legende, hoverDunkler } = BIO;

/* --- Erhaltungszustand nach Lebensraumgruppen -------------------------
   Sechs gestapelte Balken, auf 100 % normiert — die Auflösung des
   Durchschnitts, den der Abschnitt `erhaltung` zeigt.

   FARBEN UND REIHENFOLGE SIND ABSICHTLICH DIESELBEN WIE IN erhaltung.js.
   Beide Abschnitte zeigen dieselbe Ampel derselben Quelle; verschiedene
   Töne für dieselbe Bedeutung wären hier ein Fehler und keine Abwechslung.
   Wer die Töne dort ändert, muss sie hier mitziehen. Begründung der
   Zuordnung steht ausführlich in erhaltung.js — kurz: „schlecht" darf
   `--viz-kritisch` tragen, weil es die amtliche Einstufung der Quelle ist
   und nicht meine Wertung, und „unbekannt" bekommt bewusst KEINEN Ton der
   Ampel, weil es keine schlechtere Stufe ist, sondern gar keine.

   DIE SORTIERUNG KOMMT AUS DEN DATEN, nicht von hier. `lebensraeume.py`
   sortiert nach dem Anteil „günstig" absteigend. Nicht im Frontend
   umsortieren: Die Reihenfolge trägt die Aussage des Abschnitts, und sie
   soll in JSON und Balken dieselbe sein.

   ZUR ACHSENBREITE: 140 px links, gerechnet gegen den längsten Kurznamen
   („Heide & Gebüsch", 15 Zeichen). Die ausführlichen Namen stehen in
   Tooltip und Tabelle. Ohne `width` im Label kürzt ECharts nicht, sondern
   zeichnet über den Rand hinaus — `kategorieLabel()` setzt es, deshalb
   muss der zweite Parameter zum `left` des Gitters passen.

   KEINE BESCHRIFTUNG IN DEN SEGMENTEN, wie im Schwesterabschnitt: Das
   kleinste Segment ist 6 % breit, dort passt keine Zahl hinein.

   FALLZAHLEN GEHÖREN IN DEN TOOLTIP. Anders als bei `erhaltung`, wo die
   kleinste Gruppe 114 Bewertungen hat, geht es hier um 6 bis 32. „50 %
   günstig" bei sechs Bewertungen heißt drei Stück, und das muss man
   sehen können, bevor man den Balken mit dem daneben vergleicht. Der
   Tooltip nennt deshalb neben dem Prozentwert die Anzahl. */

/* Reihenfolge: guenstig · unzureichend · schlecht · unbekannt */
const FARBEN = ["--viz-gut", "--viz-seq-rot-3", "--viz-kritisch", "--viz-muted"];

/* Muss zum `left` des Gitters passen — siehe Kopfkommentar. */
const RAND_LINKS = 140;

function baueLebensraeume(daten) {
  const S = schrift();
  if (!daten?.gruppen?.length) return;
  const abschnitt = document.getElementById("s-lebensraeume");
  if (abschnitt) abschnitt.style.display = "";

  const feld = document.getElementById("c-lebensraeume");
  if (!feld) return;
  const d = echarts.getInstanceByDom(feld) || echarts.init(feld, null, { renderer: "svg" });
  if (!diagramme.includes(d)) diagramme.push(d);

  const gruppen = daten.gruppen;
  const kategorien = daten.kategorien.map((k) => k.name);

  setzeText("u-lebensraeume",
    `Anteil der Bewertungen je Zustand · ${zahl(daten.bewertungen_gesamt)} ` +
    `Bewertungen aus ${zahl(daten.schutzgueter_gesamt)} Lebensraumtypen · ` +
    `Berichtsperiode ${daten.periode}`);
  setzeText("h-lebensraeume", daten.hinweis ?? "");

  /* Eng braucht jede Kategorie eine eigene Zeile fuer ihren Namen.
     Muss VOR setOption stehen — siehe erhaltung.js. */
  balkenHoehe(d, feld, gruppen.length, 36);

  d.setOption({
    ...basis(),
    grid: { ...balkenGitter(feld, { left: RAND_LINKS, right: 60 }), top: 46 },
    legend: legende(feld, {
      top: 0, left: istSchmal(feld) ? 0 : RAND_LINKS,
      itemWidth: 11, itemHeight: 11, itemGap: 14, data: kategorien,
      textStyle: { color: stil("--viz-text-2"), fontSize: S.serie },
    }),
    tooltip: {
      ...basis().tooltip, trigger: "axis",
      axisPointer: { type: "shadow", shadowStyle: { color: stil("--viz-grid"), opacity: 0.35 } },
      formatter: (p) => {
        const g = gruppen[p[0].dataIndex];
        return `<strong>${g.name_lang}</strong><br>` +
          `<span style="color:${stil("--viz-muted")}">${zahl(g.bewertungen)} ` +
          `Bewertungen aus ${zahl(g.schutzgueter)} Lebensraumtypen</span><br>` +
          p.map((r) => `${r.marker} ${r.seriesName}&nbsp;&nbsp;` +
            `<strong>${pz(r.value, 0)} %</strong>` +
            `<span style="color:${stil("--viz-muted")}">&nbsp;&nbsp;` +
            `${zahl(g.anzahl[r.seriesIndex])} von ${zahl(g.bewertungen)}` +
            `</span>`).join("<br>");
      },
    },
    xAxis: { ...achse(), type: "value", max: 100, axisLine: { show: false },
      axisLabel: { hideOverlap: true, color: stil("--viz-muted"),
                   fontSize: S.achse, formatter: (v) => v + " %" } },
    yAxis: { ...achse(), type: "category", inverse: true,
      data: gruppen.map((g) => g.name), splitLine: { show: false },
      axisLabel: { color: stil("--viz-text-2"), fontSize: S.serie, margin: 12,
                   ...kategorieLabel(feld, RAND_LINKS, gruppen.length) } },
    series: kategorien.map((name, k) => ({
      name, type: "bar", stack: "zustand", barWidth: balkenBreite(feld, "56%", gruppen.length),
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

  /* Die Notiz kommt aus den Daten, nicht aus dem Code. Sie trägt das,
     was der Balken nicht zeigen kann: dass die zwei günstigen
     Grünlandwerte im Hochgebirge liegen und kein einziger auf einer
     bewirtschafteten Wiese, dass „unbekannt" bei den Gewässern eine
     Wissenslücke ist und keine gute Lage, und dass alle vier echten
     Verbesserungen der Periode im Wald liegen. Ein Satz im JavaScript
     würde still altern; einer, den das ETL-Modul aus seinen eigenen
     Zahlen baut, kann das nicht. */
  if (daten.notiz) setzeHtml("n-lebensraeume", daten.notiz);

  setzeHtml("t-lebensraeume", tabelle(
    [{ titel: "Lebensraumgruppe", wert: (z) => z.name_lang },
     ...daten.kategorien.map((k, i) => ({
       titel: k.name, num: true,
       /* Anzahl vor Prozent: Bei sechs Bewertungen ist „50 %" die
          weniger ehrliche der beiden Zahlen. */
       wert: (z) => `${zahl(z.anzahl[i])} · ${pz(z.anteile[i], 0)} %`,
     })),
     { titel: "Bewertungen", num: true, wert: (z) => zahl(z.bewertungen) },
     { titel: "Lebensraumtypen", num: true, wert: (z) => zahl(z.schutzgueter) }],
    gruppen
  ));
}

BIO.baueLebensraeume = baueLebensraeume;
})(window.BIO);
