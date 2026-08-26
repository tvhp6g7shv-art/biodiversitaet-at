/* ===========================================================================
   Biodiversitäts-Dashboard Österreich — Themenstrang: vogelarten
   ---------------------------------------------------------------------------
   Wird nach js/kern.js geladen; die Helfer kommen aus window.BIO.
   =========================================================================== */
(function (BIO) {
"use strict";
const { stil, zahl, pz, basis, achse, tabelle, setzeText, setzeHtml,
        diagramme, schrift, istSchmal, balkenGitter, kategorieLabel,
        balkenBreite, balkenHoehe, hoverDunkler } = BIO;

/* --- 11 — Feld- und Wiesenvögel Art für Art ---------------------------
   Liegende Balken, eine Art je Zeile, aufsteigend von der stärksten
   Abnahme zur stärksten Zunahme.

   WAS DIESER ABSCHNITT NEBEN `vogel` TUT: Dort steht der Index — eine
   Linie, das Mittel aus allen Arten. Sie sagt, wie GROSS der Rückgang
   ist. Sie sagt nicht, wie UNGLEICH er verteilt ist: Die Grauammer hat
   97 Prozent verloren, der Stieglitz seinen Bestand mehr als verdoppelt.
   Ein Mittelwert verdeckt genau das. Deshalb hier dieselben Vögel
   einzeln — es ist derselbe Datensatz, nicht ein zweiter.

   DREI FARBEN, KEINE RAMPE. Abnahme, keine gesicherte Richtung, Zunahme
   sind drei Zustände, kein Verlauf. Eine sequenzielle Skala würde eine
   Ordnung behaupten, die es nicht gibt — zwischen −97 und −16 Prozent
   liegt kein qualitativer Unterschied, beide sind gesicherte Abnahmen.
   Die Balkenlänge trägt die Größe, die Farbe den Befund.

   „GLEICH GEBLIEBEN" HEISST NICHT „GEMESSEN UNVERÄNDERT", sondern „die
   Zählung zeigt keine gesicherte Richtung". Der Unterschied ist kein
   Haarspalten: Der Feldsperling steht bei −3 Prozent und gilt als
   stabil, die Dorngrasmücke bei −31 Prozent als Abnahme — die Einstufung
   wägt den Verlauf gegen die statistische Unsicherheit ab. Das steht in
   der Hinweiszeile und im Tooltip.

   DIE DREI SPÄTSTARTER GEHÖREN NICHT IN DIESE BALKEN. Heidelerche,
   Steinschmätzer und Bergpieper werden erst ab 2008 gerechnet.
   Siebzehn Jahre neben siebenundzwanzig zu stellen wäre ein stiller
   Vergleich zweier verschiedener Dinge. Sie stehen im Nachsatz.

   DIE STICHPROBE STEHT IM TOOLTIP, weil sie extrem schwankt: Der
   Stieglitz wird auf 210 Zählstrecken erfasst, die Grauammer auf sechs.
   Beide Trends sind gesichert, aber der eine ruht auf deutlich mehr
   Boden als der andere. */

const WORT = {
  abnahme_stark: "starke Abnahme",
  abnahme: "Abnahme",
  stabil: "keine gesicherte Richtung",
  zunahme: "Zunahme",
};

function baueVogelarten(daten) {
  const S = schrift();
  if (!daten?.arten?.length) return;
  const abschnitt = document.getElementById("s-vogelarten");
  if (abschnitt) abschnitt.style.display = "";

  const feld = document.getElementById("c-vogelarten");
  if (!feld) return;
  const d = echarts.getInstanceByDom(feld) || echarts.init(feld, null, { renderer: "svg" });
  if (!diagramme.includes(d)) diagramme.push(d);

  const liste = daten.arten;
  const farbe = (a) => a.einstufung === "stabil" ? stil("--viz-muted")
    : (a.einstufung === "zunahme" ? stil("--viz-gut") : stil("--viz-kritisch"));

  const z = daten.zaehlung;
  setzeText("u-vogelarten",
    `Bestandsveränderung je Art · ${daten.beginn} bis ${daten.stand} · ` +
    `${z.rueckgang} weniger, ${z.stabil} gleich, ${z.zunahme} mehr`);
  setzeText("h-vogelarten", daten.hinweis ?? "");

  /* Die große Zahl ist der schlechteste Wert, der Satz daneben der beste.
     Beide kommen aus `schlechteste`/`beste` und wandern mit dem nächsten
     Bericht von selbst mit — im Markup stünden sie spätestens im August
     falsch da. Die Spannweite IST hier die Aussage: ein Mittelwert würde
     genau sie verdecken, deshalb gibt es diesen Abschnitt. */
  const s = daten.schlechteste, b = daten.beste;
  setzeHtml("k-vogelarten",
    `<span class="viz-plakat-zahl">−${pz(Math.abs(s.wert), 0)} %</span>` +
    `<span class="viz-plakat-zusatz">${s.name}, seit ${daten.beginn}</span>` +
    `<p class="viz-plakat-satz">Im selben Zeitraum hat der ${b.name} um ` +
    `${pz(b.wert, 0)} % zugelegt. Von ${daten.bewertet} Arten sind ` +
    `${z.rueckgang} zurückgegangen.</p>`);

  balkenHoehe(d, feld, liste.length, 14);

  d.setOption({
    ...basis(),
    grid: { ...balkenGitter(feld, { left: 130, right: 66 }), top: 24 },
    tooltip: {
      ...basis().tooltip, trigger: "axis",
      axisPointer: { type: "shadow", shadowStyle: { color: stil("--viz-grid"), opacity: 0.35 } },
      formatter: (p) => {
        const a = liste[p[0].dataIndex];
        return `<strong>${a.name}</strong><br>` +
          `<strong>${a.wert > 0 ? "+" : "−"}${pz(Math.abs(a.wert), 0)} %</strong> ` +
          `seit ${daten.beginn}` +
          `<br><span style="color:${stil("--viz-muted")}">${WORT[a.einstufung]}` +
          ` · ${pz(Math.abs(a.pro_jahr), 0)} % im Jahr` +
          ` · ${zahl(a.strecken)} Zählstrecken</span>`;
      },
    },
    /* Feste Achsengrenzen statt Automatik: Sie halten die Nulllinie an
       derselben Stelle, wenn sich einzelne Werte im nächsten Bericht
       verschieben. −100 ist die untere Schranke der Messgröße, +130
       lässt dem Stieglitz (+122) Platz für seine Beschriftung. */
    xAxis: { ...achse(), type: "value", min: -100, max: 130, interval: 50,
      axisLine: { show: false },
      axisLabel: { hideOverlap: true, color: stil("--viz-muted"),
                   fontSize: S.achse,
                   formatter: (v) => (v > 0 ? "+" : "") + v + " %" } },
    yAxis: { ...achse(), type: "category", inverse: true,
      data: liste.map((a) => a.name), splitLine: { show: false },
      axisLabel: { color: stil("--viz-text-2"),
                   fontSize: istSchmal(feld) ? S.eng : S.serie, margin: 12,
                   ...kategorieLabel(feld, 130, liste.length) } },
    series: [{
      type: "bar", name: "Bestandsveränderung",
      barWidth: balkenBreite(feld, "62%"),
      data: liste.map((a) => ({
        value: a.wert,
        itemStyle: {
          color: farbe(a),
          /* Die Ecke wird an dem Ende gerundet, an dem der Balken endet —
             links bei Abnahme, rechts bei Zunahme. */
          borderRadius: a.wert < 0 ? [4, 0, 0, 4] : [0, 4, 4, 0],
        },
        emphasis: hoverDunkler(farbe(a)),
        label: {
          position: a.wert < 0 ? "left" : "right", distance: 8,
          color: stil("--viz-text-2"), fontSize: S.label,
          formatter: () => (a.wert > 0 ? "+" : "−") + pz(Math.abs(a.wert), 0) + " %",
        },
      })),
      label: { show: true },
    }],
  }, { replaceMerge: ["series", "xAxis", "yAxis", "legend"] });

  /* Nachsatz: die Spätstarter und die Art, die nie ausgewertet wird.
     Beides gehört nicht in die Balken, aber es fehlt sonst. */
  const saetze = [];
  if (daten.spaete_arten?.length) {
    const s = daten.spaete_arten
      .map((a) => `${a.name} ${a.wert > 0 ? "+" : "−"}${pz(Math.abs(a.wert), 0)} %`)
      .join(", ");
    saetze.push(
      `Drei weitere Arten werden erst ab ${daten.beginn_spaet} gerechnet und ` +
      `stehen deshalb nicht in derselben Reihe: ${s}. Ihr kürzerer Zeitraum ` +
      `ist mit den ${daten.bewertet} Arten oben nicht vergleichbar.`);
  }
  if (daten.ohne_auswertung?.length) {
    saetze.push(
      `Der ${daten.ohne_auswertung.join(" und der ")} ist als Indikatorart ` +
      `definiert, erreicht aber nie eine ausreichende Stichprobe.`);
  }
  setzeHtml("n-vogelarten", saetze.join(" "));

  setzeHtml("t-vogelarten", tabelle(
    [{ titel: "Art", wert: (a) => a.name },
     { titel: `seit ${daten.beginn}`, num: true,
       wert: (a) => (a.wert > 0 ? "+" : "−") + pz(Math.abs(a.wert), 0) + " %" },
     { titel: "im Jahr", num: true,
       wert: (a) => (a.pro_jahr > 0 ? "+" : a.pro_jahr < 0 ? "−" : "±") +
                    pz(Math.abs(a.pro_jahr), 0) + " %" },
     { titel: "Einstufung", wert: (a) => WORT[a.einstufung] },
     { titel: "Zählstrecken", num: true, wert: (a) => zahl(a.strecken) }],
    liste.concat(daten.spaete_arten || [])
  ));
}

BIO.baueVogelarten = baueVogelarten;
})(window.BIO);
