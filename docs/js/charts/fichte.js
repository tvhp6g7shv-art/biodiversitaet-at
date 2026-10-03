/* ===========================================================================
   Biodiversitäts-Dashboard Österreich — Themenstrang: fichte
   ---------------------------------------------------------------------------
   Wird nach js/kern.js geladen; die Helfer kommen aus window.BIO.
   =========================================================================== */
(function (BIO) {
"use strict";
const { stil, zahl, pz, basis, achse, tabelle, setzeText, setzeHtml,
        diagramme, schrift, balkenGitter, kategorieLabel, balkenBreite,
        balkenHoehe, hoverDunkler } = BIO;

/* --- Fichte: Anteil am Ertragswald, liegende Balken -------------------

   WARUM DIE ANTEILE SELBST GERECHNET SIND:
   Die Waldinventur rechnet die Baumartenprozente in der Periode 2018/23
   gegen den GESAMTWALD, in 2016/21 gegen den ERTRAGSWALD. Für die Fichte
   ergibt das 39,8 gegenüber 49,9 Prozent, während die Fläche selbst nur von
   1.678 auf 1.598 Tausend Hektar zurückgeht. Wer die veröffentlichten Werte
   nebeneinanderstellt, zeigt einen Einbruch, den es nicht gibt. Das ETL
   rechnet deshalb aus Fläche und Ertragswald selbst; hier kommen nur noch
   fertige, vergleichbare Anteile an.

   WARUM ANTEIL UND NICHT FLÄCHE:
   Die Steiermark hat mit 475 Tausend Hektar dreissigmal so viel Fichte wie
   Vorarlberg mit 29. Absolute Flächen nebeneinander sagen über die
   Waldzusammensetzung nichts und machen die kleinen Länder unsichtbar.

   WARUM WIEN MITLÄUFT, OBWOHL DER BALKEN NULL IST:
   Null ist hier ein Befund, keine Lücke — auf Wiens 9.000 Hektar Wald
   wächst keine messbare Fichte. Ein weggelassenes Bundesland liest sich
   dagegen wie ein Datenfehler. Der Balken bekommt deshalb eine eigene
   Beschriftung statt zu verschwinden.

   WARUM DIE ANGABE „EIN DRITTEL" NICHT AUF DIE BALKEN GERECHNET WIRD:
   Dass die Fichte auf rund 1,3 Millionen Hektar standörtlich hingehört,
   stammt aus einer Auswertung von 2013 auf Basis der Inventur 2007/09 — die
   Fichtenfläche lag damals bei rund 2,17 Millionen Hektar, heute sind es
   1,598. Das damalige Verhältnis auf die heutige Fläche anzuwenden wäre eine
   Erfindung. Die Zahl steht deshalb als eigener Satz in der Notiz, mit ihrem
   eigenen Datenstand, und nicht als zweite Balkenreihe. */

function baueFichte(daten) {
  const S = schrift();
  if (!daten?.eintraege?.length) return;

  const abschnitt = document.getElementById("s-fichte");
  if (abschnitt) abschnitt.style.display = "";

  const feld = document.getElementById("c-fichte");
  if (!feld) return;
  const d = echarts.getInstanceByDom(feld) || echarts.init(feld, null, { renderer: "svg" });
  if (!diagramme.includes(d)) diagramme.push(d);

  const eintraege = daten.eintraege;
  /* A115 (03.10.2026, Entscheid User): Gruen aus der Rampe der
     Nachbarkarte Totholz statt Oliv (`--viz-series-1`). Auf dem dunklen
     Glas der Unterseiten wird `--viz-series-1` zur Schriftfarbe (weiss);
     `--viz-seq-5` bleibt dort und im Dashboard derselbe Gruenton. */
  const ton = stil("--viz-seq-5");
  const gedaempft = stil("--viz-series-3");

  setzeText("u-fichte",
    `Anteil der Fichte an der Ertragswaldfläche · ` +
    `Waldinventur ${daten.stand.replace("ÖWI ", "")}`);

  setzeText("n-fichte",
    `Auf ${pz(daten.bund_anteil)} Prozent des österreichischen Ertragswalds ` +
    `steht Fichte — ${pz(Math.abs(daten.bund_veraenderung))} Prozentpunkte ` +
    `weniger als ${daten.perioden[0]}. Standörtlich hingehört sie auf rund ` +
    `1,3 Millionen Hektar, also etwa ein Drittel der Waldfläche.`);

  setzeText("h-fichte", daten.hinweis);

  /* Eng braucht jede Kategorie eine eigene Zeile für ihren Namen. Die
     Kartenhöhe kommt deshalb aus der Zahl der Kategorien und nicht aus dem
     CSS. Muss VOR setOption stehen. */
  balkenHoehe(d, feld, eintraege.length, 2);

  /* Achse bis zum nächsten Zehner über dem grössten Wert. Fest gerundet,
     damit die Achse nicht bei jeder neuen Inventurperiode springt. */
  const max = Math.ceil(Math.max(...eintraege.map((e) => e.anteil)) / 10) * 10;

  d.setOption({
    ...basis(),
    /* A115 (01.10.2026): `balkenGitter` nimmt ein Objekt, kein Mass —
       die 130 wurden still verworfen, das Gitter stand auf 120 und
       „Niederösterreich" brach um. 150 px reichen fuer den laengsten
       Landesnamen; 44 px unten geben der Bezugsmarke Platz. */
    grid: balkenGitter(feld, { left: 150, bottom: 44 }),
    tooltip: {
      ...basis().tooltip, trigger: "item",
      formatter: (p) => {
        const e = eintraege[p.dataIndex];
        if (e.ohne_bestand) {
          return `<strong>${e.name}</strong><br>kein messbarer Fichtenbestand`;
        }
        return `<strong>${e.name}</strong><br>` +
          `${pz(e.anteil)} % des Ertragswalds<br>` +
          `<span style="color:${stil("--viz-muted")}">` +
          `${zahl(e.flaeche_tsd_ha)} Tsd. Hektar · ` +
          `${e.veraenderung > 0 ? "+" : ""}${pz(e.veraenderung)} Pkt seit ` +
          `${daten.perioden[0]}</span>`;
      },
    },
    xAxis: {
      ...achse(), type: "value", max,
      axisLabel: { ...achse().axisLabel, formatter: (v) => `${v} %` },
    },
    yAxis: {
      ...achse(), type: "category", inverse: true,
      data: eintraege.map((e) => e.name),
      axisLabel: kategorieLabel(feld, 150, eintraege.length),
    },
    series: [{
      type: "bar",
      barWidth: balkenBreite(feld, 18, eintraege.length),
      data: eintraege.map((e) => ({
        value: e.anteil,
        /* Länder ohne Bestand bekommen den gedämpften Ton. Sonst sieht der
           Nullbalken aus wie ein fehlender Wert in derselben Farbe wie die
           echten. */
        itemStyle: { color: e.ohne_bestand ? gedaempft : ton },
        emphasis: hoverDunkler(e.ohne_bestand ? gedaempft : ton),
      })),
      label: {
        show: true, position: "right",
        color: stil("--viz-text-2"), fontSize: S.serie,
        formatter: (p) => eintraege[p.dataIndex].ohne_bestand
          ? "keine Fichte" : `${pz(p.value)} %`,
      },
      /* Der Bundeswert als Bezugslinie. Ohne ihn muss man die Balken im Kopf
         mitteln, um zu sehen, welche Länder über dem Schnitt liegen. */
      markLine: {
        silent: true, symbol: "none",
        lineStyle: { color: stil("--viz-muted"), type: "dashed", width: 1 },
        label: {
          formatter: `Österreich ${pz(daten.bund_anteil)} %`,
          color: stil("--viz-muted"), fontSize: S.achse, position: "end",
          /* Unter die Achsenwerte, nicht darauf (A115: „Österreich 47,6 %"
             deckte 40 % / 50 % am Fuss). 22 px = Achsenzeile + Luft. */
          distance: 22,
        },
        data: [{ xAxis: daten.bund_anteil }],
      },
    }],
  });

  setzeHtml("t-fichte", tabelle(
    [{ titel: "Bundesland", wert: (z) => z.name },
     { titel: "Anteil", num: true,
       wert: (z) => z.ohne_bestand ? "–" : `${pz(z.anteil)} %` },
     { titel: daten.perioden[0], num: true,
       wert: (z) => z.anteil_frueher === null ? "–" : `${pz(z.anteil_frueher)} %` },
     { titel: "Fläche (Tsd. ha)", num: true, wert: (z) => zahl(z.flaeche_tsd_ha) }],
    eintraege
  ));
}

BIO.baueFichte = baueFichte;
})(window.BIO);
