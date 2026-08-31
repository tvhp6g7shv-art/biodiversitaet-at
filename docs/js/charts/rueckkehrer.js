/* ===========================================================================
   Biodiversitäts-Dashboard Österreich — Themenstrang: rueckkehrer
   ---------------------------------------------------------------------------
   Wird nach js/kern.js geladen; die Helfer kommen aus window.BIO.
   =========================================================================== */
(function (BIO) {
"use strict";
const { stil, zahl, pz, basis, achse, tabelle, setzeText, setzeHtml,
        diagramme, schrift, istSchmal, istEng, balkenGitter, kategorieLabel,
        balkenHoehe, legende, hoverDunkler } = BIO;

/* --- 10 — Biber und Fischotter, der Erholungspol ----------------------
   Liegende Balken, vier Berichtsperioden, zwei Arten.

   WARUM SPANNEN UND KEIN MITTELWERT: Beide Arten werden über Reviere und
   Nachweise erhoben und auf Individuen hochgerechnet. Eine einzelne Zahl
   wäre eine Genauigkeit, die die Erhebung nicht hergibt. Der Balken läuft
   deshalb von der gemeldeten Unter- zur Obergrenze und beginnt nicht am
   Nullpunkt.

   WIE EIN SCHWEBENDER BALKEN IN ECHARTS ENTSTEHT: Es gibt keinen
   Balkentyp, der von a nach b läuft. Jede Art bekommt deshalb ZWEI
   Reihen im selben Stapel — einen unsichtbaren Sockel bis zur
   Untergrenze und darüber die sichtbare Spanne. Zwei verschiedene
   `stack`-Namen sorgen dafür, dass die Arten NEBENEINANDER stehen statt
   übereinander. Die Sockel tragen `silent` und stehen nicht in der
   Legende; wer sie dort einträgt, bietet dem Leser ein Element an, das
   nichts bedeutet.

   DAS JAHR 1869 STEHT NICHT AUF DER ACHSE. Der Biber war damals in
   Österreich ausgerottet, die Aussetzung lief 1976–1982. Auf einer
   Kategorieachse wäre der Abstand 1869 → 2001 genauso breit wie sechs
   Jahre — eine Zeitlüge. Die Null trägt deshalb der Nachsatz unter der
   Grafik.

   DIE LÜCKE BEIM FISCHOTTER IST KEINE LÜCKE IN DER NATUR. Österreich
   meldete für 2013–2018 keine Individuen, sondern besetzte Rasterzellen.
   Diese Zahlen sind mit den Individuenzahlen davor und danach nicht
   vergleichbar. Sie werden deshalb NICHT umgerechnet — der Balken fehlt,
   und der Tooltip sagt, warum. Wer die Rasterzellen einsetzt, erzeugt
   einen Einbruch, den es nie gab. */

function baueRueckkehrer(daten) {
  const S = schrift();
  if (!daten?.arten?.length) return;
  const abschnitt = document.getElementById("s-rueckkehrer");
  if (abschnitt) abschnitt.style.display = "";

  const feld = document.getElementById("c-rueckkehrer");
  if (!feld) return;
  const d = echarts.getInstanceByDom(feld) || echarts.init(feld, null, { renderer: "svg" });
  if (!diagramme.includes(d)) diagramme.push(d);

  const perioden = daten.perioden;
  const arten = daten.arten;
  const farben = [stil("--viz-series-1"), stil("--viz-series-2")];
  const letzte = perioden.length - 1;

  setzeText("u-rueckkehrer",
    `Gemeldete Bestandsspanne je Berichtsperiode · ` +
    `${perioden[0]} bis ${daten.periode}`);
  setzeText("h-rueckkehrer", daten.hinweis ?? "");

  /* KORREKTUR 26.08.2026, Befund des Users: Hier stand die Null von 1869
     als große Zahl. Unter der Überschrift „sind zurückgekommen" liest
     sich eine riesige 0 als Widerspruch — sie ist der Wert von 1869 und
     nicht der heutige, und der Abschnitt handelt von zwei Arten, nicht
     von einer. Das Argument dafür war eines über Genauigkeit (die Null
     ist exakt, der heutige Bestand eine Spanne) und keines darüber, ob
     man es beim Lesen versteht.

     Jetzt trägt der Faktor die Zahl: Er misst dasselbe wie die Grafik —
     Wachstum über die Berichtsperioden — und ist auf der UNTERGRENZE
     gerechnet, also die vorsichtigste Lesart. 1869 bleibt als Pointe im
     Satz, wo es keinen Wert behauptet, den die Grafik nicht zeigt. */
  const biberPlakat = arten.find((a) => a.name === "Biber") || arten[0];
  const otter = arten.find((a) => a.name === "Fischotter");
  setzeHtml("k-rueckkehrer",
    `<span class="viz-plakat-zahl">${pz(biberPlakat.faktor)}` +
    `<span class="viz-plakat-einheit">×</span></span>` +
    `<p class="viz-plakat-satz">mehr Biber als in der Berichtsperiode ` +
    `${biberPlakat.erste_periode}. ${daten.biber_ausgerottet} war die Art ` +
    `in Österreich ausgerottet; heute leben hier wieder ` +
    `${zahl(biberPlakat.letzte_unten)} bis ${zahl(biberPlakat.letzte_oben)} ` +
    `Biber` +
    (otter ? ` und ${zahl(otter.letzte_unten)} bis ` +
             `${zahl(otter.letzte_oben)} Fischotter` : "") + `.</p>`);

  balkenHoehe(d, feld, perioden.length * arten.length, 30);

  /* BALKENBREITE — KORREKTUR 26.08.2026, Befund des Users am Bildschirmfoto.
     Hier stand `balkenBreite(feld, "62%")` wie in den übrigen Modulen. Dort
     ist es richtig, weil dort EINE Balkengruppe je Kategorie steht: 62 % der
     Bandbreite, 38 % Luft. Dieses Modul hat als einziges ZWEI Gruppen je
     Kategorie (`s0` und `s1` sind getrennte Stapel, damit die Arten
     nebeneinander stehen). Zwei Gruppen zu je 62 % ergeben 124 % — die
     Gruppe ist breiter als ihr Band, ECharts zentriert sie trotzdem, und
     jeder Balken rutscht aus seiner Zeile.

     Gemessen am gerenderten SVG bei 1.058 px Feldbreite: Band 58 px, Balken
     36 px, Bandmitten bei y = 63/121/179/237. Der Fischotter-Balken der
     Periode 2001–2006 lag bei y = 64,8–100,8 und damit auf der Beschriftung
     „2007–2012". Die Grafik ordnete jede Zahl der falschen Periode zu.

     Die Obergrenze für zwei Gruppen liegt bei 50 % minus Zwischenraum.
     40 % ergibt 23,2 px je Balken, dazu der ECharts-Standardabstand von
     30 % der Balkenbreite (7 px) — zusammen 53,4 px in einem 58-px-Band.

     ENG (unter 768 px): dort ist die Breite ein fester Pixelwert, weil der
     Kategoriename ÜBER dem Balken steht. `kategorieLabel` setzt dessen
     Unterkante auf `BAR_ENG / 2 + 4` = 11 px über die Bandmitte. Der feste
     Wert BAR_ENG = 14 aus `balkenBreite()` gilt für EINE Gruppe; zwei
     Gruppen zu 14 px belegen ±16 px und schöben den oberen Balken 5 px in
     den Namen. Deshalb 8 px: gemessen bei 700 px Fensterbreite belegt die
     Gruppe y = 66,35–83,15 um die Bandmitte 74,75, die Namensunterkante
     liegt bei 63,75 — 2,6 px Luft. Wer diesen Wert erhöht, schiebt den
     Namen in den oberen Balken. */
  const spannenBreite = istEng(feld) ? 8 : "40%";

  /* Je Art ein unsichtbarer Sockel und die sichtbare Spanne, in einem
     eigenen Stapel. `wert()` liest aus der Periodenliste der Art. */
  const reihen = [];
  arten.forEach((art, i) => {
    const wert = (k) => art.werte.find((w) => w.periode === perioden[k]) || {};
    reihen.push({
      name: `${art.name} (Sockel)`, type: "bar", stack: `s${i}`,
      silent: true, legendHoverLink: false,
      barWidth: spannenBreite,
      itemStyle: { color: "transparent" },
      emphasis: { disabled: true },
      data: perioden.map((p, k) => wert(k).unten ?? null),
    });
    reihen.push({
      name: art.name, type: "bar", stack: `s${i}`,
      barWidth: spannenBreite,
      itemStyle: { color: farben[i], borderRadius: 4 },
      emphasis: hoverDunkler(farben[i]),
      data: perioden.map((p, k) => {
        const w = wert(k);
        return w.spanne === null || w.spanne === undefined ? null : w.spanne;
      }),
      /* Beschriftet wird nur die jüngste Periode. Alle vier zu
         beschriften ergibt acht Zahlenpaare auf engem Raum; die
         übrigen Werte stehen in Tooltip und Tabelle. */
      label: {
        show: true, position: "right", distance: 8,
        color: stil("--viz-text-2"), fontSize: S.label,
        formatter: (p) => {
          if (p.dataIndex !== letzte) return "";
          const w = wert(letzte);
          if (w.unten === null || w.unten === undefined) return "";
          return `${zahl(w.unten)}–${zahl(w.oben)}`;
        },
      },
    });
  });

  d.setOption({
    ...basis(),
    grid: { ...balkenGitter(feld, { left: 96, right: 112 }), top: 34 },
    legend: legende(feld, {
      top: 0, left: istSchmal(feld) ? 0 : 96,
      itemWidth: 11, itemHeight: 11, itemGap: 16,
      data: arten.map((a) => a.name),
      textStyle: { color: stil("--viz-text-2"), fontSize: S.serie },
    }),
    tooltip: {
      ...basis().tooltip, trigger: "axis",
      axisPointer: { type: "shadow", shadowStyle: { color: stil("--viz-grid"), opacity: 0.35 } },
      formatter: (p) => {
        const k = p[0].dataIndex;
        const zeilen = [`<strong>${perioden[k]}</strong>`];
        arten.forEach((art, i) => {
          const w = art.werte.find((x) => x.periode === perioden[k]) || {};
          if (w.unten === null || w.unten === undefined) {
            zeilen.push(
              `<span style="color:${farben[i]}">■</span> ${art.name} ` +
              `<span style="color:${stil("--viz-muted")}">keine Individuenzahl ` +
              `gemeldet — Österreich meldete für diese Periode Rasterzellen</span>`);
          } else {
            zeilen.push(
              `<span style="color:${farben[i]}">■</span> ${art.name} ` +
              `<strong>${zahl(w.unten)}–${zahl(w.oben)}</strong>`);
          }
        });
        return zeilen.join("<br>");
      },
    },
    xAxis: { ...achse(), type: "value", min: 0, axisLine: { show: false },
      axisLabel: { hideOverlap: true, color: stil("--viz-muted"),
                   fontSize: S.achse, formatter: (v) => zahl(v) } },
    yAxis: { ...achse(), type: "category", inverse: true,
      data: perioden, splitLine: { show: false },
      axisLabel: { color: stil("--viz-text-2"),
                   fontSize: istSchmal(feld) ? S.eng : S.serie, margin: 12,
                   /* Viertes Argument: dieses Modul setzt seine Balkenhoehe eng selbst
       (`spannenBreite` = 8 px), holt sie also nicht von `balkenBreite()`.
       Die 14 halten den gemessenen Abstand von 2,6 px zwischen Name und
       Balken — siehe den Block ueber `spannenBreite`. Ohne das Argument
       zoege die Staffelung nach Zeilenzahl den Namen 7 px hoeher. */
    ...kategorieLabel(feld, 96, perioden.length, 14) } },
    series: reihen,
  }, { replaceMerge: ["series", "xAxis", "yAxis", "legend"] });

  /* Der Nachsatz trägt die beiden Zahlen, die im Balken nicht stehen
     können: die Null von 1869 und den Befund, dass die Erholung im
     Alpenraum als echt gemeldet ist und nicht als besseres Wissen. */
  const biber = arten.find((a) => a.name === "Biber") || arten[0];
  const saetze = [
    `<strong>${daten.biber_ausgerottet}</strong> war der Biber in Österreich ` +
    `ausgerottet. Zwischen ${daten.biber_aussetzung} wurden an drei Stellen ` +
    `wieder Tiere ausgesetzt — heute sind es ${zahl(biber.letzte_unten)} bis ` +
    `${zahl(biber.letzte_oben)}.`,
  ];
  if (daten.echte_erholung) {
    const e = daten.echte_erholung;
    saetze.push(
      `Im ${e.region} meldet Österreich für beide Arten eine <strong>echte ` +
      `Erholung</strong>, nicht bloß besseres Wissen: Der Erhaltungszustand ` +
      `wechselte dort von „${e.von}“ auf „${e.auf}“.`);
  }
  setzeHtml("n-rueckkehrer", saetze.join(" "));

  /* Eine Zeile je Periode, eine Spalte je Art. */
  setzeHtml("t-rueckkehrer", tabelle(
    [{ titel: "Berichtsperiode", wert: (z) => z.periode },
     ...arten.map((art) => ({
       titel: art.name, num: true,
       wert: (z) => {
         const w = art.werte.find((x) => x.periode === z.periode) || {};
         return w.unten === null || w.unten === undefined
           ? "–" : `${zahl(w.unten)}–${zahl(w.oben)}`;
       },
     }))],
    perioden.map((p) => ({ periode: p }))
  ));
}

BIO.baueRueckkehrer = baueRueckkehrer;
})(window.BIO);
