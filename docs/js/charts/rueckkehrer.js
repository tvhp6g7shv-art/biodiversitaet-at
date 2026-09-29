/* ===========================================================================
   Biodiversitäts-Dashboard Österreich — Themenstrang: rueckkehrer
   ---------------------------------------------------------------------------
   Wird nach js/kern.js geladen; die Helfer kommen aus window.BIO.
   =========================================================================== */
(function (BIO) {
"use strict";
const { stil, zahl, pz, basis, achse, tabelle, setzeText, setzeHtml,
        diagramme, schrift, istSchmal, istEng, balkenGitter, kategorieLabel,
        balkenHoehe, legende, legendeLinks, hoverDunkler } = BIO;

/* --- 10 — Biber und Fischotter, der Erholungspol ----------------------
   Wachsende Kreise, vier Berichtsperioden, zwei Arten (seit 29.09.2026;
   vorher schwebende Balken, siehe Block „BLASEN" unten).

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

  /* --- BLASEN statt schwebender Balken — Entscheid des Users 29.09.2026 --
     „Die gesamte Grafik funktioniert so nicht. Sie ist nicht lesbar."
     Bei 390 px lief das Etikett „13 833–16 654" aus der Karte (E1), die
     Achsenzahlen liefen ineinander (A109), und die Balken der ersten
     Perioden waren Punkte. Die Zunahme zeigen jetzt wachsende Kreise.

     AUFBAU: Spalten = Berichtsperioden, Zeilen = Arten. Je Periode und Art
     ZWEI Kreise um denselben Mittelpunkt: die gefüllte Scheibe ist die
     Untergrenze, der Ring die Obergrenze. Die Spanne bleibt damit sichtbar,
     ohne dass eine Mitte erfunden wird (siehe oben: keine einzelne Zahl).

     FLÄCHE, NICHT DURCHMESSER, ist proportional zum Wert: d = D · √(w / max).
     Ein Durchmesser proportional zum Wert ließe 16 654 Biber 40-mal so
     groß erscheinen wie 2 575 statt 6,5-mal. Beide Arten teilen eine Skala,
     damit Biber und Fischotter direkt vergleichbar bleiben.

     DIE LÜCKE BEIM FISCHOTTER bleibt eine Lücke: kein Kreis, ein Strich,
     und der Tooltip sagt warum (Rasterzellen statt Individuen). */
  const breite = feld.clientWidth || 600;
  const eng = istEng(feld);
  /* Eng stehen die Artnamen um 90° gedreht in einer schmalen Randspalte:
     die Legende allein trüge die Zuordnung nur über die Farbe. */
  const LINKS = eng ? 24 : 96;
  const RECHTS = 8;
  const spalte = Math.max(56, (breite - LINKS - RECHTS) / perioden.length);
  /* Größter Kreis: Spaltenbreite minus Luft, gedeckelt, damit die Grafik
     am Desktop nicht zur Plakatwand wird. */
  const D = Math.round(Math.min(spalte - 10, 120));
  const alle = arten.flatMap((a) => a.werte.map((w) => w.oben)).filter((v) => v != null);
  const maxWert = Math.max(...alle);
  const durchmesser = (v) => (v == null ? 0 : Math.max(6, D * Math.sqrt(v / maxWert)));

  /* Etikett unter dem Kreis: eng zweizeilig, sonst eine Zeile. Zeilenhöhe
     aus der Achsenschrift. */
  const ZEILE = Math.round(S.label * 1.35);
  const ETIKETT = (eng ? 2 : 1) * ZEILE + 8;
  const ZEILENHOEHE = D + ETIKETT + 18;
  const OBEN = 12;
  const UNTEN = 28;
  feld.style.height = `${OBEN + arten.length * ZEILENHOEHE + UNTEN}px`;
  d.resize();

  const etikett = (w) => {
    if (w.unten == null) return "keine Zählung";
    return eng ? `${zahl(w.unten)}–\n${zahl(w.oben)}` : `${zahl(w.unten)}–${zahl(w.oben)}`;
  };

  const reihen = [];
  arten.forEach((art, i) => {
    const wert = (k) => art.werte.find((w) => w.periode === perioden[k]) || {};
    const punkte = perioden.map((p, k) => ({ k, w: wert(k) }));
    /* Scheibe = Untergrenze. Steht VOR dem Ring, weil die Legende die
       Marke der ersten Reihe gleichen Namens zeigt — sonst ein leerer Kreis. */
    reihen.push({
      name: art.name, type: "scatter", z: 3, silent: true,
      data: punkte.map(({ k, w }) => ({
        value: [k, i], w,
        symbolSize: w.unten == null ? 0 : durchmesser(w.unten),
      })),
      itemStyle: { color: farben[i], opacity: 0.85 },
      emphasis: { disabled: true },
    });
    /* Ring = Obergrenze. Trägt das Etikett, weil er der äußere Kreis ist. */
    reihen.push({
      name: art.name, type: "scatter", z: 2,
      data: punkte.map(({ k, w }) => ({
        value: [k, i], w,
        symbolSize: w.oben == null ? 0 : durchmesser(w.oben),
      })),
      itemStyle: { color: "transparent", borderColor: farben[i], borderWidth: 2 },
      emphasis: { scale: false, itemStyle: { borderWidth: 3 } },
      label: {
        show: true, position: "bottom", distance: 6,
        color: stil("--viz-text-2"), fontSize: S.label, lineHeight: ZEILE,
        align: "center",
        formatter: (p) => etikett(p.data.w),
      },
      labelLayout: { hideOverlap: false },
    });
  });

  d.setOption({
    ...basis(),
    grid: { left: LINKS, right: RECHTS, top: OBEN, bottom: UNTEN, containLabel: false },
    /* KEINE LEGENDE: Die Zeilen tragen die Artnamen direkt. Eine Legende
       mit denselben Namen wäre doppelt — und legendenFreiraeumen() hielte
       die Zeilennamen „Biber“ und „Fischotter“ für Legendeneinträge und
       schöbe das Gitter um eine Zeile nach unten (am 29.09. gemessen:
       80 px Leerraum über der Grafik). */
    legend: { show: false },
    tooltip: {
      ...basis().tooltip, trigger: "item",
      formatter: (p) => {
        const w = p.data.w || {};
        const art = arten[p.data.value[1]];
        const kopf = `<strong>${art.name}</strong> · ${perioden[p.data.value[0]]}`;
        if (w.unten == null) {
          return `${kopf}<br><span style="color:${stil("--viz-muted")}">keine ` +
            `Individuenzahl gemeldet — Österreich meldete für diese Periode ` +
            `Rasterzellen</span>`;
        }
        return `${kopf}<br><strong>${zahl(w.unten)}–${zahl(w.oben)}</strong> Tiere` +
          `<br><span style="color:${stil("--viz-muted")}">Scheibe: Untergrenze · ` +
          `Ring: Obergrenze</span>`;
      },
    },
    xAxis: { ...achse(), type: "category", data: perioden, boundaryGap: true,
      position: "bottom", axisLine: { show: false }, axisTick: { show: false },
      splitLine: { show: false },
      axisLabel: { color: stil("--viz-muted"), fontSize: S.achse, interval: 0,
                   formatter: (v) => v } },
    yAxis: { ...achse(), type: "category", inverse: true,
      data: arten.map((a) => a.name), boundaryGap: true,
      axisLine: { show: false }, axisTick: { show: false },
      splitLine: { show: false },
      axisLabel: eng
        ? { color: stil("--viz-text-2"), fontSize: S.eng || S.serie, rotate: 90,
            margin: 8, align: "center" }
        : { color: stil("--viz-text-2"), fontSize: S.serie, margin: 12 } },
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
