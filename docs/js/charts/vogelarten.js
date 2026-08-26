/* ===========================================================================
   Biodiversitäts-Dashboard Österreich — Themenstrang: vogelarten
   ---------------------------------------------------------------------------
   Wird nach js/kern.js geladen; die Helfer kommen aus window.BIO.
   =========================================================================== */
(function (BIO) {
"use strict";
const { stil, zahl, pz, basis, achse, tabelle, setzeText, setzeHtml,
        diagramme, schrift, istSchmal, istEng, balkenGitter, kategorieLabel,
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

  /* KORREKTUR 26.08.2026, Befund des Users: Hier stand die −97 % der
     Grauammer als große Zahl. Das ist der schlechteste Einzelwert und
     nicht die Aussage des Abschnitts — wer schnell liest, hält ihn für
     den Rückgang der Feld- und Wiesenvögel insgesamt. Der liegt bei
     −47 % und steht zwei Abschnitte weiter oben: zwei Zahlen, die sich
     für dieselbe Vogelgruppe widersprechen.

     Jetzt trägt „14 von 20" die Zahl. Sie ist eindeutig, verwechselt
     sich mit keiner anderen Größe auf der Seite und ist genau das, was
     die zwanzig Balken zeigen. Die Spannweite — die eigentliche
     Ungleichheit — steht im Satz daneben. Alle Werte kommen aus den
     Daten und wandern mit dem nächsten Bericht von selbst mit. */
  const s = daten.schlechteste, b = daten.beste;
  setzeHtml("k-vogelarten",
    `<span class="viz-plakat-zahl">${z.rueckgang}` +
    `<span class="viz-plakat-einheit">&nbsp;von&nbsp;${daten.bewertet}</span>` +
    `</span>` +
    `<p class="viz-plakat-satz">Feld- und Wiesenvogelarten sind seit ` +
    `${daten.beginn} gesichert zurückgegangen. Die Spannweite reicht von ` +
    `der ${s.name} mit −${pz(Math.abs(s.wert), 0)} % bis zum ${b.name} ` +
    `mit +${pz(b.wert, 0)} %.</p>`);

  balkenHoehe(d, feld, liste.length, 14);

  /* FEHLER VOM 26.08.2026, vom User an der Live-Seite gesehen: Bei der
     Grauammer stand „−97 %" quer über dem Artnamen.

     Die Ursache ist keine Kollision zweier Beschriftungen, sondern eine
     Asymmetrie der Ränder. `position: "left"` setzt die Zahl AUSSERHALB
     des Balkens nach links. Bei −97 endet der Balken fast an der
     Achsenuntergrenze (−100), also am linken Rand der Zeichenfläche —
     und links davon liegt die Spalte mit den Artnamen. Rechts tritt das
     nicht auf: dort sind 66 px Rand frei, in die „+122 %" bequem passt.

     Die Regel unten rechnet den verbleibenden Platz aus, statt eine
     Balkenlänge zu raten: Passt die Zahl links vom Balkenende nicht mehr
     in die Zeichenfläche, wandert sie INS Balkeninnere. Am Handy, wo die
     Namen über den Balken stehen und links nur 14 px bleiben, greift
     dieselbe Rechnung von selbst.

     Die Textfarbe im Balken wird nicht gesetzt, sondern gerechnet:
     Schwarz oder Weiß, je nachdem, was gegen die Füllung mehr Kontrast
     bringt. Nachgerechnet für alle drei ausgelieferten Paletten liegt
     der schlechteste Fall bei 4,54 : 1 (Pages hell, „stabil"), alle
     übrigen zwischen 5,56 und 10,80. */
  const ACHSE_MIN = -100, ACHSE_MAX = 130;
  const randLinks = istEng(feld) ? 14 : 130;
  const plotBreite = Math.max(120, (feld.clientWidth || 900) - randLinks - 66);
  const proEinheit = plotBreite / (ACHSE_MAX - ACHSE_MIN);
  const platzLinks = (w) => (w - ACHSE_MIN) * proEinheit;
  const nachInnen = (w) => w < 0 && platzLinks(w) < 52;

  const helligkeit = (farbe) => {
    const m = String(farbe).match(/^#?([0-9a-f]{6})$/i)
      || String(farbe).match(/rgba?\((\d+)[,\s]+(\d+)[,\s]+(\d+)/i);
    if (!m) return null;
    const teile = m[1] && m[1].length === 6
      ? [0, 2, 4].map((i) => parseInt(m[1].slice(i, i + 2), 16))
      : [Number(m[1]), Number(m[2]), Number(m[3])];
    const lin = teile.map((v) => {
      const c = v / 255;
      return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
    });
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2];
  };
  const aufFarbe = (fuellung) => {
    const l = helligkeit(fuellung);
    if (l === null) return stil("--viz-text-2");
    /* Kontrast gegen Schwarz und gegen Weiß, das Bessere gewinnt. */
    const gegenSchwarz = (l + 0.05) / (0.05 + 0.0);
    const gegenWeiss = (1.05) / (l + 0.05);
    return gegenSchwarz >= gegenWeiss ? "#0a0a0a" : "#ffffff";
  };

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
        label: (() => {
          const innen = nachInnen(a.wert);
          return {
            position: innen ? "insideLeft" : (a.wert < 0 ? "left" : "right"),
            distance: 8,
            offset: innen ? [6, 0] : [0, 0],
            color: innen ? aufFarbe(farbe(a)) : stil("--viz-text-2"),
            fontSize: S.label,
            formatter: () => (a.wert > 0 ? "+" : "−") + pz(Math.abs(a.wert), 0) + " %",
          };
        })(),
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
