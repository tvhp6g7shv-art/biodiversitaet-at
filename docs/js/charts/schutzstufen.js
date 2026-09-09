/* ===========================================================================
   Biodiversitäts-Dashboard Österreich — Themenstrang: schutzstufen
   ---------------------------------------------------------------------------
   Wird nach js/kern.js geladen; die Helfer kommen aus window.BIO.
   =========================================================================== */
(function (BIO) {
"use strict";
const { stil, zahl, pz, basis, achse, tabelle, setzeText, setzeHtml,
        diagramme, schrift, balkenGitter, legendeLinks, legendeHoehe,
        istSchmal, balkenHoehe, hoverDunkler } = BIO;

/* --- Wie streng der Schutz ist ----------------------------------------
   EIN liegender Balken — das geschützte Gebiet —, aufgeteilt in vier
   Segmente nach Strenge des Schutzes. Bis zum 07.09.2026 abends waren es
   vier kumulative Balken gegen die Landesfläche; warum das ersetzt wurde,
   steht beim Block `SEGMENTTOENE`.
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
/* --- Der Umbau vom 07.09.2026, abends -------------------------------------

   BETONUNG STATT RAMPE HAT NICHT GEREICHT. Der User, nach der Korrektur:
   „Ich sehe weiterhin das hier." Zu Recht — der Fehler saß nicht in den
   Farbtönen, sondern im NENNER.

   Die Kaskade zeigte vier Anteile an der LANDESFLÄCHE: 29,6 / 29,0 / 17,6
   / 2,9. Die Überschrift behauptet dagegen ein VERHÄLTNIS ZWISCHEN ZWEIEN
   davon — 2,9 zu 29,6, also die 9,9 %. Dieses Verhältnis stand nirgends im
   Bild; es musste im Kopf gerechnet werden. Drei lange Balken sagten
   „viel geschützt", die Überschrift sagte „kaum streng". Das Auge glaubt
   dem Bild. In jeder Farbe.

   JETZT: EIN gestapelter Balken, der das geschützte Gebiet IST. Die vier
   Segmente sind seine Teile, das erste ist sichtbar ein Zehntel — die
   Überschrift wird ablesbar statt behauptet. Der Bezug zur Landesfläche
   steht in der Hinweiszeile; der Nachbarabschnitt `schutzgebiete`
   beantwortet „wie viel ist geschützt" ohnehin. Zwei Fragen, zwei Bilder,
   jeweils der passende Nenner.

   WAS DABEI VERLOREN GEHT, offen benannt: Die Kaskade zeigte, dass jede
   Stufe die strengere enthält. Die Segmente stehen nebeneinander statt
   ineinander. Der Tausch ist trotzdem richtig — die Teilmengen-Idee hat
   ohnehin niemand aus dem Bild gelesen, das war der Kern des zweiten
   Einwands über die „… plus"-Namen.

   DIE TÖNE, in allen vier Auslieferungen vorgerechnet. Nur die BEIDEN
   RANDSEGMENTE grenzen an den Kartengrund und brauchen Grundkontrast; die
   inneren grenzen an Nachbarn, wo zusätzlich der 2-px-Spalt in Kartenfarbe
   trägt (`SPALT`).

     Auslieferung   links:Grund  rechts:Grund   1|2    2|3    3|4
     WP hell            5,15         4,84      1,90   1,78   3,17
     WP dunkel          9,64         6,96      2,63   2,86   5,43
     Pages hell        15,13         4,54      4,50   2,38   3,22
     Pages dunkel      12,68         6,26      2,92   2,64   3,80

   `--viz-muted` FÜR DAS LETZTE SEGMENT ist kein Verlegenheitsgriff,
   sondern die Aussage: „ohne festgelegte Stufe" IST keine Schutzstufe,
   sie fällt aus der Rampe. Ein Neutralton sagt das. Praktisch trägt er
   zugleich den Rand — seq-1 stünde dort bei 1,06–1,22 gegen den Grund und
   das 2,1-%-Segment sähe aus, als endete der Balken zu früh. */
const SEGMENTTOENE = [
  "--viz-seq-6",   /* streng — Nationalparks, Wildnis */
  "--viz-seq-4",   /* Naturdenkmäler, Artenschutzgebiete */
  "--viz-seq-2",   /* geschützte Landschaften */
  "--viz-muted",   /* ohne festgelegte Stufe — keine Stufe, kein Rampenton */
];

/* Spalt zwischen den Segmenten, in Kartenfarbe. Kein Strich um die Marke —
   die Trennung entsteht durch die Lücke, wie bei gestapelten Balken üblich.
   2 px, damit auch das schmalste Segment (2,1 % ≈ 12 px) noch Fläche
   behält. */
const SPALT = 2;

/* Obergrenze der Achse in Prozentpunkten. Steht seit dem Umbau auf 100:
   Der Balken IST das geschützte Gebiet, die Achse sein Anteil daran. Die
   frühere 35 kam vom gemeinsamen Maßstab mit `schutzherkunft` — der gilt
   nicht mehr, weil die beiden Abschnitte seither verschiedene Nenner
   haben. Genau darin lag der Fehler. */
const ACHSE_MAX = 100;

function baueSchutzstufen(daten) {
  const S = schrift();
  if (!daten?.balken?.length) return;
  const abschnitt = document.getElementById("s-schutzstufen");
  if (abschnitt) abschnitt.style.display = "";

  const feld = document.getElementById("c-schutzstufen");
  if (!feld) return;
  const d = echarts.getInstanceByDom(feld) || echarts.init(feld, null, { renderer: "svg" });
  if (!diagramme.includes(d)) diagramme.push(d);

  /* `segmente` zeichnet das Bild, `balken` trägt die Tabelle darunter. Der
     Rückfall auf `balken` hält den Abschnitt am Leben, falls eine ältere
     `schutzstufen.json` ausgeliefert wird als das Modul erwartet — dann
     fehlen die Segmente, aber die Tabelle steht. */
  const zeilen = daten.balken;
  const segmente = daten.segmente;
  if (!segmente?.length) {
    console.warn("[Dashboard] schutzstufen: keine `segmente` in den Daten — " +
      "ältere JSON? Das Diagramm bleibt leer, die Tabelle wird gebaut.");
  }

  setzeText("u-schutzstufen",
    `Die geschützte Fläche Österreichs, aufgeteilt nach Strenge des ` +
    `Schutzes · Stand ${daten.stand}`);
  setzeText("h-schutzstufen", daten.hinweis ?? "");

  /* Wie viel Höhe die Legende über dem Balken braucht.

     HIER STAND `istSchmal(feld) ? 3 : 1` UND WAR EINE ZEILE ZU WENIG. Der
     User hat es am 09.09.2026 auf dem Telefon gesehen: Der Balken lief in
     die vierte Legendenzeile hinein und strich „+ ohne festgelegte Stufe"
     durch. Nachgemessen am gerenderten SVG (Feld 344 px): die vier
     Einträge stehen auf VIER Zeilen im Abstand von 26 px — nicht drei zu
     je 16. Beide Zahlen der alten Rechnung waren falsch, und weil sie
     Annahmen waren, fiel es nur im Bild auf.

     Jetzt rechnet `legendeHoehe` aus Feldbreite und Namenslänge; die
     Namen stehen in den Daten und können mit dem UBA-Stand wachsen. */
  const NAMEN = segmente?.map((z) => z.stufe) ?? [];
  const LEG_LINKS = legendeLinks(feld, 4);
  const LEG_HOEHE = legendeHoehe(feld, NAMEN, LEG_LINKS);

  /* Balkenstärke. 120 px füllen die Desktop-Fläche; schmal sind sie zu
     viel, seit die Legende vier Zeilen belegt — 64 px lassen der Zahl
     über dem ersten Segment Luft, ohne dass die Karte wächst. */
  const BALKEN = istSchmal(feld) ? 64 : 120;

  /* Mindestbreite eines Segments, damit sein Etikett hineinpasst — in
     PIXELN, nicht in Prozent. Die alte Schwelle (`>= 14`) war ein Anteil
     und traf damit dieselbe Falle wie `fliessgewaesser`: Bei 300 px Feld
     sind 14 % noch 37 px, „14,0 %" braucht 42 und stünde über der Kante. */
  const GITTER = balkenGitter(feld, { left: 16, right: 22 });
  const PLOT = Math.max(80, feld.clientWidth - GITTER.left - GITTER.right);
  const ETIKETT_SCHWELLE = Math.max(14, (46 / PLOT) * 100);

  /* EINE Kategoriezeile statt vier — der Balken ist das Ganze. Die Höhe
     kommt deshalb nicht mehr aus `balkenHoehe(…, zeilen.length, 40)`;
     ein einzelner Balken braucht eine feste, ruhige Fläche, plus den Platz
     für die mehrzeilige Legende. */
  balkenHoehe(d, feld, 1, BALKEN - 8 + LEG_HOEHE);

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
    /* Kein linker Rand mehr für Stufennamen — es gibt nur eine
       Kategoriezeile, und die braucht keine Beschriftung: Der Balken IST
       das geschützte Gebiet, das sagt die Unterzeile. Die Stufennamen
       tragen jetzt die Legende und die Direktetiketten.
       `top: 34` hält die Legende frei. */
    /* Ränder tragen die halbe Breite des äussersten Achsenlabels, nicht die
       Kategorienamen — die stehen seit dem Umbau in der Legende.

       `left: 4` STAND HIER UND WAR ZU KNAPP: Am ausgelieferten Stand
       gemessen (07.09.2026, WordPress, SVG 1178 px) ragte „0 %" um 5,9 px
       über die linke Kante und wurde zu „%" abgeschnitten. ECharts setzt
       Achsenlabels mittig über den Tick; bei 0 liegt die halbe Labelbreite
       also im Nichts. „0 %" ist rund 20 px breit, „100 %" rund 33 —
       daher 16 links und 22 rechts, je die halbe Breite plus etwas Luft.
       Die Prüfsuite hat das NICHT gemeldet: Sie misst Text gegen die
       Zeichenfläche, und der Überstand blieb knapp darunter. */
    grid: { ...GITTER, top: LEG_HOEHE, bottom: 34 },
    /* HIER BEWUSST NICHT `legende()`. Der Helfer schaltet schmal auf
       `type: "scroll"` — eine Zeile zum Blättern statt drei Zeilen ins
       Diagramm hinein. Für die meisten Abschnitte ist das richtig; für
       diesen ist es falsch, denn die Legende ist die EINZIGE Erklärung der
       vier Segmente. Bei 420 px zeigte sie „1/4": ein Name sichtbar, drei
       hinter einem Pfeil. Am gerenderten SVG gemessen, nicht vermutet.
       Also plain und mehrzeilig, und das Feld bekommt die Zeilen dazu. */
    legend: {
      left: LEG_LINKS, top: 0,
      itemWidth: 10, itemHeight: 10, itemGap: 14,
      textStyle: { color: stil("--viz-text-2"), fontSize: S.serie },
      data: segmente?.map((z) => z.stufe) ?? [],
    },
    tooltip: {
      ...basis().tooltip, trigger: "item",
      /* Der Tooltip nennt beide Nenner nebeneinander — das ist genau die
         Verwechslung, an der die erste Fassung gescheitert ist. Die km²
         sind die Zahl der Quelle; die Prozente sind gerechnet, und wer
         nachrechnen will, braucht den Zähler. */
      formatter: (p) => {
        const z = segmente[p.seriesIndex];
        const vomLand = (z.km2 / daten.flaeche_km2) * 100;
        return `<strong>${z.stufe}</strong><br>` +
          `<strong>${pz(z.anteil, 1)} %</strong> des geschützten Gebiets` +
          `<br><span style="color:${stil("--viz-muted")}">` +
          `${zahl(z.km2)} km² · ${pz(vomLand, 1)} % des Landes</span>`;
      },
    },
    xAxis: { ...achse(), type: "value", max: ACHSE_MAX, axisLine: { show: false },
      axisLabel: { hideOverlap: true, color: stil("--viz-muted"),
                   fontSize: S.achse, formatter: (v) => zahl(v) + " %" } },
    /* Eine namenlose Kategorie. `show: false` an der Achsenbeschriftung,
       nicht ein leerer String — sonst reserviert ECharts trotzdem Platz. */
    yAxis: { ...achse(), type: "category", data: [""], splitLine: { show: false },
      axisLabel: { show: false }, axisTick: { show: false } },
    /* Vier Serien mit demselben `stack` ergeben EINEN Balken. Nicht eine
       Serie mit vier Werten — die stünde als vier Balken untereinander,
       und genau die Bauform wird hier ersetzt. */
    series: (segmente ?? []).map((z, k) => ({
      name: z.stufe,
      type: "bar",
      stack: "schutz",
      /* 120 px, nicht der übliche Prozentwert aus `balkenBreite()`: Der
         rechnet gegen die Zahl der Kategorien, und die ist hier 1. Der
         Wert füllt die Feldhöhe, die im CSS auf 340 px steht — ein
         52-px-Band sähe darin verloren aus.
         DIE HÖHE SELBST GEHÖRT KLEINER. Sie stammt aus der Zeit der vier
         Balken; ein einzelner braucht keine 340 px. Ändern lässt sie sich
         nur im CSS beider Auslieferungen (und `min-height` schlägt jeden
         JS-Wert), deshalb steht sie auf der Liste für den CSS-Durchgang
         am 12.09. und nicht hier. */
      barWidth: BALKEN,
      data: [z.anteil],
      itemStyle: {
        color: stil(SEGMENTTOENE[k]),
        /* Der Spalt: ein Rahmen in Kartenfarbe, nur links und rechts.
           Oben und unten 0, sonst wirkt der Balken dünner als 52 px. */
        borderColor: stil("--viz-surface"),
        borderWidth: 0,
        borderRadius: k === 0 ? [4, 0, 0, 4]
                    : k === segmente.length - 1 ? [0, 4, 4, 0] : 0,
      },
      emphasis: { itemStyle: { opacity: 0.85 } },
      /* Etikett IM Segment, wo es hineinpasst. Die Schwelle ist nicht
         geraten: 14 % der Achse sind bei der schmalsten geprüften Breite
         (420 px minus Ränder) rund 55 px — genug für „49,4 %" in
         MONO 11,5. Darunter bleibt das Segment leer und wird allein über
         die Legende erklärt; ein Etikett daneben würde bei 2,1 % in den
         Nachbarn ragen.
         Die Schriftfarbe ist NICHT fest: Auf seq-6 (dunkel) muss sie hell
         stehen, auf seq-2 (hell) dunkel. `--viz-invers-text` gegen
         `--viz-text` — vorgerechnet, nicht geschätzt. */
      label: {
        show: z.anteil >= ETIKETT_SCHWELLE,
        position: "inside",
        color: stil(k === 0 ? "--viz-invers-text" : "--viz-text"),
        fontSize: S.label, fontWeight: "bold",
        formatter: () => pz(z.anteil, 1) + " %",
      },
    })),
  }, { replaceMerge: ["series", "xAxis", "yAxis", "legend"] });

  /* Das erste Segment trägt den Befund und ist mit 9,9 % zu schmal für ein
     Etikett darin. Es bekommt seine Zahl über den Balken gesetzt — als
     `markPoint` der ersten Serie, damit sie mit dem Segment wandert, falls
     das UBA fortschreibt. */
  if (segmente?.length) {
    d.setOption({ series: [{
      markPoint: {
        silent: true, symbol: "rect", symbolSize: [0, 0],
        label: {
          /* ABSTAND AUS DER BALKENSTÄRKE, nicht fest. `distance` misst von
             der MITTE des Balkens, nicht von seiner Kante: mit den alten
             12 px landete die Zahl IM ersten Segment — dunkles Grau auf
             `--viz-seq-6`, praktisch unlesbar, auf dem Telefon wie am
             Desktop. Halbe Stärke plus 12 px setzt sie darüber. */
          show: true, position: "top", distance: BALKEN / 2 + 12,
          color: stil("--viz-text"), fontSize: S.label, fontWeight: "bold",
          formatter: () => pz(segmente[0].anteil, 1) + " %",
        },
        data: [{ coord: [segmente[0].anteil / 2, 0] }],
      },
    }] });
  }

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

  /* Die Tabelle führt seit dem Umbau BEIDE Nenner. Das Bild zeigt nur noch
     den einen; wer den anderen sucht — etwa um gegen den Abschnitt
     `schutzgebiete` zu prüfen —, findet ihn hier. Grundlage sind die
     kumulierten `balken`, weil die Kaskade in einer Tabelle lesbar bleibt,
     wo sie im Bild nicht funktioniert hat. */
  setzeHtml("t-schutzstufen", tabelle(
    [{ titel: "Schutzstufe (kumuliert)", wert: (z) => z.stufe },
     { titel: "Fläche", num: true, wert: (z) => zahl(z.km2) + " km²" },
     { titel: "Anteil an Österreich", num: true, wert: (z) => pz(z.anteil, 1) + " %" }],
    zeilen
  ));
}

BIO.baueSchutzstufen = baueSchutzstufen;
})(window.BIO);
