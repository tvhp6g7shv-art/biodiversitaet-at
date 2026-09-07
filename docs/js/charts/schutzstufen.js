/* ===========================================================================
   Biodiversitäts-Dashboard Österreich — Themenstrang: schutzstufen
   ---------------------------------------------------------------------------
   Wird nach js/kern.js geladen; die Helfer kommen aus window.BIO.
   =========================================================================== */
(function (BIO) {
"use strict";
const { stil, zahl, pz, basis, achse, tabelle, setzeText, setzeHtml,
        diagramme, schrift, balkenGitter, kategorieLabel,
        balkenBreite, balkenHoehe, hoverDunkler } = BIO;

/* --- Wie streng der Schutz ist ----------------------------------------
   Vier liegende Balken, kumulativ, von oben nach unten kürzer werdend.
   Der dritte Abschnitt über dieselbe Zahl: `schutzgebiete` zeigt sie im
   Zeitverlauf, `schutzherkunft` zerlegt sie danach, WER ausgewiesen hat,
   dieser danach, WIE STRENG geschützt wird.

   MUSS HINTER `schutzherkunft` STEHEN. Erst wenn klar ist, woher der
   Schutz kommt, ist die Frage nach seiner Tiefe die nächste.

   DIE BALKEN LAUFEN VON UNTEN NACH OBEN ZU. Oben steht alles Geschützte,
   unten nur das streng Geschützte — die Kaskade fällt, und der unterste
   Balken ist der Befund. Gedreht wird das im ETL, nicht hier: ein
   `reverse()` an dieser Stelle stünde ohne erkennbaren Grund im Code.

   WARUM HIER KEINE SERIENTÖNE WIE BEI `schutzherkunft`: Dort sind die
   beiden Teile zwei Wege zur Ausweisung — nebeneinander, nicht
   übereinander. Hier sind die vier Werte Stufen einer geordneten Skala.
   Serientöne behaupteten vier gleichrangige Kategorien.

   Warum es trotzdem KEINE Rampe mehr ist, sondern eine Betonung: siehe
   den Block über `KONTEXT`/`BEFUND` weiter unten. Kurz — die Rampe
   arbeitete gegen die Balkenlänge und ließ die Grafik wirken, als sei
   alles in Ordnung.

   NICHT `--viz-seq-rot-*`: Rot wäre eine Wertung, die die Daten nicht
   hergeben. Ein gering geschütztes Gebiet ist kein Schaden, es ist ein
   Landschaftsschutzgebiet. Das galt für die Rampe und gilt für die
   Betonung unverändert.

   DIE FARBEN SEHEN IN DEN BEIDEN AUSLIEFERUNGEN VERSCHIEDEN AUS und das
   ist gewollt: Auf WordPress ist `--viz-seq-*` grün (Palette „Lichtung",
   #d7ebc8 → #477707), auf Pages grau (#f2f2f2 → #262626). Pages ist
   monochrom, die Einbettungen sind bunt. Beide führen alle sechs Stufen —
   am 07.09.2026 an beiden Auslieferungen gemessen.

   NICHT ZU VERWECHSELN mit `--viz-series-5/6`, die auf WordPress fehlen.
   Das ist eine andere Tokenfamilie; `--viz-seq-*` ist in beiden
   Auslieferungen vollständig.

   WARUM DIE ACHSE BEI 35 ENDET: dieselbe Grenze wie im Abschnitt darüber,
   damit die Balken beider Abschnitte auf denselben Maßstab fallen. Wer
   von `schutzherkunft` herunterscrollt, vergleicht sonst Längen, die
   nichts miteinander zu tun haben. 35 ist die nächste Fünferstufe über
   dem größten Wert (29,6).

   KEINE ZIELMARKE BEI 10 %: Die 10 Prozent streng geschützter Fläche der
   EU-Biodiversitätsstrategie gelten der EU ALS GANZES, nicht je
   Mitgliedstaat — dieselbe Lage wie bei den 30 % in `schutzherkunft`.
   Eine senkrechte Linie neben dem untersten Balken behauptete ein Ziel,
   das es so nicht gibt. Die Zahl steht in der Hinweiszeile und in der
   Notiz, wo sie eingeordnet werden kann.

   EIN EUROPAVERGLEICH FEHLT NICHT, ES GIBT IHN NICHT. Das JRC-Dashboard
   der EU-Biodiversitätsstrategie führt zu Target 2 „Indicator under
   development". Wer ihn vermisst, sucht nach einer Zahl, die niemand
   erhebt. */

/* BIS 07.09.2026 STAND HIER EINE VIERSTUFIGE RAMPE (seq-3 bis seq-6) —
   eine Stufe je Balken, dunkler = strenger. Der User hat sie verworfen:
   „Diese Grafik ist grün, wirkt wie gut."

   Er hat recht, und die Ursache ist nicht der Farbton allein:

   DIE RAMPE ARBEITETE GEGEN DIE BALKENLÄNGE. Eine sequenzielle Rampe
   liest sich als „dunkler = mehr". Hier ist der dunkelste Balken der
   KÜRZESTE. Zwei Signale, die sich widersprechen — und das Auge glaubt
   der Länge. Übrig blieb der Eindruck von vier langen grünen Balken.

   VIER ABSTUFUNGEN BEHAUPTEN AUSSERDEM VIER GLEICHRANGIGE WERTE. Der
   Abschnitt hat aber genau einen Befund: die 2,9 %. Die drei anderen
   Balken sind Kontext, der zeigt, wovon die 2,9 ein Teil sind.

   DESHALB JETZT BETONUNG STATT RAMPE: drei Balken tragen denselben
   gedämpften Ton, der unterste — der Befund — den dunkelsten. Keine
   Wertung, kein Rot; nur die Auskunft, welcher Balken die Überschrift
   trägt.

   WARUM seq-3 UND seq-6 und nicht andere Token: In allen VIER
   Auslieferungen muss der Befundbalken sich vom Kontext absetzen, und
   zwar immer in Richtung MEHR Kontrast zum Grund. Vorgerechnet
   (WCAG-Kontrast, nicht geschätzt — `getComputedStyle` löst `var()` in
   jsdom nicht auf):

     Auslieferung   Grund     seq-3 : Grund   seq-6 : Grund   Sprung
     WP hell        #f9fbf5      1,99            5,15          2,59
     WP dunkel      #151a11      1,94            9,64          4,97
     Pages hell     #ffffff      2,10           15,13          7,22
     Pages dunkel   #1c1f21      2,47           12,68          5,14

   `--viz-muted` wäre der naheliegende Kontextton und fällt aus: auf
   WordPress hell steht er bei #6b7162 gegen #477707 — Sprung 1,06, also
   praktisch dieselbe Helligkeit. Wer Farben schlecht unterscheidet, sähe
   vier gleiche Balken. seq-2 fällt umgekehrt aus: Sprung gut, aber nur
   1,28–1,65 gegen den Grund — die Kontextbalken verschwänden.

   Index 0 ist der oberste, breiteste Balken; der Befund steht unten. */
const KONTEXT = "--viz-seq-3";
const BEFUND  = "--viz-seq-6";

/* Obergrenze der Achse in Prozentpunkten — siehe Kopfkommentar. */
const ACHSE_MAX = 35;

function baueSchutzstufen(daten) {
  const S = schrift();
  if (!daten?.balken?.length) return;
  const abschnitt = document.getElementById("s-schutzstufen");
  if (abschnitt) abschnitt.style.display = "";

  const feld = document.getElementById("c-schutzstufen");
  if (!feld) return;
  const d = echarts.getInstanceByDom(feld) || echarts.init(feld, null, { renderer: "svg" });
  if (!diagramme.includes(d)) diagramme.push(d);

  const zeilen = daten.balken;
  const streng = zeilen[zeilen.length - 1];

  setzeText("u-schutzstufen",
    `Anteil an der Landesfläche, kumuliert nach abnehmendem Schutzgrad · ` +
    `Stand ${daten.stand}`);
  setzeText("h-schutzstufen", daten.hinweis ?? "");

  balkenHoehe(d, feld, zeilen.length, 40);

  d.setOption({
    ...basis(),
    /* Der linke Rand trägt die längste Stufenbeschriftung. 210 px sind an
       der MONO-Auslieferung gemessen, nicht geschätzt — ohne genug Platz
       schneidet ECharts hart ab.

       Der Wert hat die Umbenennung vom 07.09.2026 überstanden: 210 lässt
       `kategorieLabel` 194 px Text, MONO 12 px, zwei Zeilen. Die längste
       Zeile nach Umbruch ist jetzt „Artenschutzgebiete" (18 Zeichen) —
       kürzer als die frühere längste („… plus gering geschützt (V–VI)").
       Wer die Namen wieder ändert, misst diesen Wert neu.

       Kein `top`-Wert wie bei `schutzherkunft`: Dieser Abschnitt hat
       keine Legende. Die Farben benennen keine Kategorien, sie heben
       einen Balken hervor; die Namen stehen in der Achse. */
    grid: { ...balkenGitter(feld, { left: 210, right: 74 }), top: 8 },
    tooltip: {
      ...basis().tooltip, trigger: "axis",
      axisPointer: { type: "shadow", shadowStyle: { color: stil("--viz-grid"), opacity: 0.35 } },
      /* Der Tooltip nennt beides: den Anteil an Österreich und die
         Fläche. Die km² sind die Zahl der Quelle — die Prozente sind
         gerechnet, und wer nachrechnen will, braucht den Zähler. */
      formatter: (p) => {
        const z = zeilen[p[0].dataIndex];
        return `<strong>${z.stufe}</strong><br>` +
          `<strong>${pz(z.anteil, 1)} %</strong> der Landesfläche` +
          `&nbsp;&nbsp;<span style="color:${stil("--viz-muted")}">` +
          `${zahl(z.km2)} km²</span>`;
      },
    },
    xAxis: { ...achse(), type: "value", max: ACHSE_MAX, axisLine: { show: false },
      axisLabel: { hideOverlap: true, color: stil("--viz-muted"),
                   fontSize: S.achse, formatter: (v) => zahl(v) + " %" } },
    yAxis: { ...achse(), type: "category", inverse: true,
      data: zeilen.map((z) => z.stufe), splitLine: { show: false },
      axisLabel: { color: stil("--viz-text-2"), fontSize: S.serie, margin: 12,
                   ...kategorieLabel(feld, 210, zeilen.length) } },
    series: [{
      name: "Anteil", type: "bar",
      barWidth: balkenBreite(feld, "62%", zeilen.length),
      /* Der letzte Balken ist der Befund, nicht der erste: die Kaskade
         läuft von oben (alles Geschützte) nach unten (nur das streng
         Geschützte). Gedreht wird im ETL — siehe Kopfkommentar. */
      data: zeilen.map((z, k) => ({
        value: z.anteil,
        itemStyle: { color: stil(k === zeilen.length - 1 ? BEFUND : KONTEXT) },
      })),
      itemStyle: { borderRadius: [0, 4, 4, 0] },
      emphasis: { itemStyle: { opacity: 0.85 } },
      /* Die Zahl steht rechts neben dem Balken, nicht in ihm: Kontext-
         und Befundton unterscheiden sich deutlich in der Helligkeit (das
         ist ihr Zweck), eine feste Schriftfarbe wäre auf einem der beiden
         zwangsläufig zu schwach. Außen liegt sie immer auf dem Grund der
         Karte und ist damit in beiden Farbmodi lesbar. */
      label: {
        show: true, position: "right", color: stil("--viz-text-2"),
        fontSize: S.label, fontWeight: "bold",
        formatter: (r) => pz(r.value, 1) + " %",
      },
    }],
  }, { replaceMerge: ["series", "xAxis", "yAxis", "legend"] });

  /* Die Notiz trägt die beiden Zahlen, die das Bild nicht zeigen kann:
     den Anteil des strengen Schutzes AM SCHUTZ SELBST — nicht an der
     Landesfläche — und was auf die EU-Marke fehlt, samt der Einordnung,
     ohne die sie in die Irre führt. */
  setzeHtml("n-schutzstufen",
    `Von den <strong>${pz(daten.gesamt_anteil, 1)} Prozent</strong> geschützter ` +
    `Landesfläche sind <strong>${pz(daten.streng_anteil, 1)} Prozent</strong> ` +
    `streng geschützt — Nationalparks und Wildnisgebiete. Das sind ` +
    `<strong>${pz(daten.anteil_streng_am_schutz, 1)} Prozent</strong> des Schutzes ` +
    `selbst, also nicht einmal jeder zehnte geschützte Quadratkilometer. ` +
    `Auf ${zahl(daten.eu_ziel_streng)} Prozent streng geschützter Fläche fehlen ` +
    `${zahl(daten.luecke_km2)} km²; das Land müsste seinen strengen Schutz ` +
    `auf das ${pz(daten.faktor, 2)}-Fache ausweiten. Diese Marke gilt der EU als ` +
    `Ganzes, nicht je Mitgliedstaat — einen Vergleich der Mitgliedstaaten gibt ` +
    `es zu ihr nicht, der Indikator ist bei der Kommission als „in Entwicklung“ ` +
    `geführt.`);

  setzeHtml("t-schutzstufen", tabelle(
    [{ titel: "Schutzstufe", wert: (z) => z.stufe },
     { titel: "Fläche", num: true, wert: (z) => zahl(z.km2) + " km²" },
     { titel: "Anteil an Österreich", num: true, wert: (z) => pz(z.anteil, 1) + " %" }],
    zeilen
  ));
}

BIO.baueSchutzstufen = baueSchutzstufen;
})(window.BIO);
