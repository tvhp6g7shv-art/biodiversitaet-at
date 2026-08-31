/* ===========================================================================
   Biodiversitäts-Dashboard Österreich — Themenstrang: fliessgewaesser
   ---------------------------------------------------------------------------
   Wird nach js/kern.js geladen; die Helfer kommen aus window.BIO.
   =========================================================================== */
(function (BIO) {
"use strict";
const { stil, zahl, pz, basis, achse, tabelle, setzeText, setzeHtml,
        diagramme, schrift, istSchmal, balkenGitter, kategorieLabel,
        balkenBreite, balkenHoehe, legende, hoverDunkler } = BIO;

/* --- Fließgewässer: Wasserkörper gegen Flusskilometer -----------------
   Zwei gestapelte Balken, auf 100 % normiert. Beide zeigen denselben
   Bestand aus derselben Meldung, im selben Jahr — und kommen auf
   49,1 % gegen 42,5 % „gut oder besser".

   WARUM ZWEI BALKEN: Der Abstand ist der Inhalt. Er entsteht nicht aus
   zwei Methoden, sondern aus einer Eigenschaft des Bestands: Die
   Wasserkörper in schlechtem Zustand sind die längeren (2,97 km im
   Mittel bei „sehr gut", 6,10 km bei „schlecht"). Wer zählt, gewichtet
   jeden Oberlaufabschnitt so schwer wie eine verbaute Flussstrecke.
   Wer misst, nicht.

   IM UNTERSCHIED ZU natura2000.js — dort gehen zwei Messweisen wegen
   einer Bewertungsregel auseinander, hier wegen der Größenverteilung
   des Gezählten. Gleiche Bauform, anderer Mechanismus; die Notiz muss
   das tragen, sonst liest es sich als dieselbe Geschichte.

   ZUR FARBWAHL: Die fünf Zustandsklassen der Wasserrahmenrichtlinie
   sind eine amtliche Einstufung, keine eigene Wertung — deshalb die
   Ampel. Die Schwelle liegt zwischen Klasse 2 und 3: „gut" erreicht
   das Ziel, „mäßig" verfehlt es. Genau dort wechselt die Rampe von
   Grün auf Rot, und der grüne Block IST damit die Zahl, um die es
   geht. „Unbekannt" bekommt einen neutralen Grauton — es ist keine
   schlechtere Stufe, sondern gar keine.

   ALLE SECHS TOKEN sind in beiden Auslieferungen definiert: in
   index.html, in embed.html und in der idl.css. `--viz-div-*` steht
   seit dem Waldarten-Abschnitt in allen dreien, geprüft am 31.08.2026.

   BESCHRIFTET WERDEN DIE ZWEI GRÜNEN FÄCHER — zusammen ergeben sie die
   Schlagzeile. Die roten bleiben stumm; das kleinste ist 0,7 % breit
   und das Etikett stünde neben dem Balken statt darin. */

const FARBEN = [
  "--viz-div-gut-4",        // sehr gut
  "--viz-div-gut-2",        // gut
  "--viz-div-schlecht-1",   // mäßig
  "--viz-div-schlecht-3",   // unbefriedigend
  "--viz-kritisch",         // schlecht
  "--viz-muted",            // unbekannt
];

/* Die ersten beiden Klassen erreichen das Ziel der Richtlinie. Die Zahl
   steckt nicht in einem Fach, sondern in ihrer Summe — deshalb hier und
   nicht im Etikett einer einzelnen Serie. */
const ZIEL_FAECHER = 2;

function baueFliessgewaesser(daten) {
  const S = schrift();
  if (!daten?.vergleich?.zeilen?.length) return;
  const abschnitt = document.getElementById("s-fliessgewaesser");
  if (abschnitt) abschnitt.style.display = "";

  const feld = document.getElementById("c-fliessgewaesser");
  if (!feld) return;
  const d = echarts.getInstanceByDom(feld) || echarts.init(feld, null, { renderer: "svg" });
  if (!diagramme.includes(d)) diagramme.push(d);

  const zeilen = daten.vergleich.zeilen;
  const faecher = daten.vergleich.faecher;
  const ziel = (z) => z.werte.slice(0, ZIEL_FAECHER)
                       .reduce((a, b) => a + b, 0);

  setzeText("u-fliessgewaesser",
    `Anteil der Zustandsklassen, einmal nach Wasserkörpern und einmal nach ` +
    `Gewässerlänge · Meldezyklus ${daten.zyklus}`);
  setzeText("h-fliessgewaesser", daten.hinweis ?? "");

  balkenHoehe(d, feld, zeilen.length, 44);

  d.setOption({
    ...basis(),
    grid: { ...balkenGitter(feld, { left: 168, right: 60 }), top: 46 },
    legend: legende(feld, {
      top: 0, left: istSchmal(feld) ? 0 : 168,
      itemWidth: 11, itemHeight: 11, itemGap: 14, data: faecher,
      textStyle: { color: stil("--viz-text-2"), fontSize: S.serie },
    }),
    tooltip: {
      ...basis().tooltip, trigger: "axis",
      axisPointer: { type: "shadow", shadowStyle: { color: stil("--viz-grid"), opacity: 0.35 } },
      /* Die Kopfzeile nennt die Summe der beiden grünen Fächer. Ohne sie
         müsste man im Tooltip zwei Zahlen im Kopf addieren, um die
         Aussage des Abschnitts zu bekommen. */
      formatter: (p) => {
        const z = zeilen[p[0].dataIndex];
        return `<strong>${z.name}</strong><br>` +
          `<span style="color:${stil("--viz-muted")}">${z.grundlage}</span><br>` +
          `gut oder besser&nbsp;&nbsp;<strong>${pz(ziel(z), 1)} %</strong><br>` +
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
                   ...kategorieLabel(feld, 168, zeilen.length) } },
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
      /* Nur die zwei Zielklassen beschriftet, und auch die nur, wenn das
         Fach breit genug ist. Unter 12 % fällt das Etikett weg, statt
         aus dem Balken zu ragen. Die Schwelle liegt niedriger als die
         20 % in natura2000.js, weil hier sechs Fächer nebeneinander
         liegen statt drei — „sehr gut" misst 18,9 %. */
      label: k < ZIEL_FAECHER ? {
        show: true, position: "inside", color: stil("--viz-plane"),
        fontSize: S.label, fontWeight: "bold",
        formatter: (r) => (r.value >= 12 ? pz(r.value, 1) + " %" : ""),
      } : { show: false },
    })),
  }, { replaceMerge: ["series", "xAxis", "yAxis", "legend"] });

  /* Die Notiz trägt, was der Balken nicht zeigen kann: WARUM die beiden
     Zeilen auseinandergehen. Ohne sie sieht der Abschnitt aus wie ein
     Rundungsfehler. Dazu die Einordnung in Europa, die als eigene
     Grafik der fünfte Ländervergleich des Dashboards wäre. */
  const bewertet = (daten.mittlere_laenge || [])
    .filter((m) => m.klasse !== "unbekannt");
  const kurz = bewertet[0];
  const lang = bewertet[bewertet.length - 1];
  const hmwb = (daten.wasserkoerperarten || [])
    .find((a) => a.art === "erheblich verändert");

  setzeHtml("n-fliessgewaesser",
    (kurz && lang
      ? `Der Abstand von <strong>${pz(daten.abstand_punkte, 1)} Punkten</strong> ` +
        `entsteht durch die Größenverteilung: Ein Wasserkörper der Klasse ` +
        `„${lang.klasse}" ist im Mittel <strong>${pz(lang.km, 2)} km</strong> ` +
        `lang, einer der Klasse „${kurz.klasse}" nur ` +
        `<strong>${pz(kurz.km, 2)} km</strong>. Die belasteten Strecken sind ` +
        `die langen — nach Kilometern gerechnet wiegen sie entsprechend ` +
        `schwerer als beim bloßen Abzählen. `
      : "") +
    (daten.rang
      ? `Im europäischen Vergleich liegt Österreich mit ` +
        `<strong>${pz(daten.nach_anzahl.gut_prozent, 1)} %</strong> auf Rang ` +
        `${zahl(daten.rang)} von ${zahl(daten.laender_gesamt)} Meldeländern. `
      : "") +
    (hmwb
      ? `Auf <strong>${pz(hmwb.anteil_netz, 1)} %</strong> des Netzes gilt ein ` +
        `weicherer Maßstab: Erheblich veränderte Gewässer werden am guten ` +
        `Potenzial gemessen, nicht am guten Zustand — und erreichen es zu ` +
        `${pz(hmwb.gut_prozent, 1)} %.`
      : ""));

  /* Die Tabelle zeigt die Klassen einzeln, in beiden Maßstäben, plus die
     mittlere Wasserkörperlänge — die Spalte, aus der die Aussage des
     Abschnitts stammt. Felder BENANNT statt über Positionen
     zusammengesteckt, wie in natura2000.js begründet. */
  const laengeJeKlasse = new Map(
    (daten.mittlere_laenge || []).map((m) => [m.klasse, m.km]));

  const klassenZeilen = faecher.map((name, k) => ({
    klasse: name,
    wk: daten.nach_anzahl.zahlen[k],
    wk_anteil: daten.nach_anzahl.anteile[k],
    km: daten.nach_laenge.km[k],
    km_anteil: daten.nach_laenge.anteile[k],
    mittel: laengeJeKlasse.get(name) ?? null,
  }));

  const prozent = (x) => (x == null ? "—" : pz(x, 1) + " %");
  const km = (x) => (x == null ? "—" : pz(x, 1) + " km");

  setzeHtml("t-fliessgewaesser", tabelle(
    [{ titel: "Zustandsklasse", wert: (z) => z.klasse },
     { titel: "Wasserkörper", num: true, wert: (z) => zahl(z.wk) },
     { titel: "Anteil", num: true, wert: (z) => prozent(z.wk_anteil) },
     { titel: "Länge", num: true, wert: (z) => km(z.km) },
     { titel: "Anteil der Länge", num: true, wert: (z) => prozent(z.km_anteil) },
     { titel: "im Mittel je Wasserkörper", num: true,
       wert: (z) => (z.mittel == null ? "—" : pz(z.mittel, 2) + " km") }],
    klassenZeilen
  ));
}

BIO.baueFliessgewaesser = baueFliessgewaesser;
})(window.BIO);
