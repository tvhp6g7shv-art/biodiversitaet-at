/* ===========================================================================
   Gegenprobe für die drei Tiergruppen-Grafiken — Geometrie statt Augenmaß.

   docs/pruefung.mjs prüft alle Abschnitte gleich: Kartenhöhen, Aufklapper,
   Kollision von Kategorienamen und Balken. Was sie NICHT wissen kann, ist,
   ob die neue Bauform in `rueckkehrer` überhaupt tut, was sie soll —
   schwebende Balken gibt es in ECharts nicht, sie entstehen aus einem
   unsichtbaren Sockel plus sichtbarer Spanne in EINEM Stapel. Geht dabei
   etwas schief, sieht die Karte trotzdem gefüllt aus: die Balken beginnen
   dann nur alle bei null, und aus einer Spanne wird eine Menge.

   Deshalb hier drei gezielte Messungen am gerenderten SVG:

     1  falter      — 34 Punkte, Basislinie bei 100, kein Symbol
     2  rueckkehrer — Sockel unsichtbar, Balken beginnen bei der
                      Untergrenze, die Lücke beim Fischotter bleibt leer
     3  vogelarten  — 20 Balken, Farbe je Einstufung, Beschriftung links
                      bei Abnahme und rechts bei Zunahme

   Aufruf:  node docs/pruefung-tiergruppen.mjs [breite]
   =========================================================================== */

import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const HIER = dirname(fileURLToPath(import.meta.url));
const breite = Number(process.argv[2] || 1100);

const HOEHEN = { "c-falter": 340, "c-rueckkehrer": 300, "c-vogelarten": 644 };

const fehler = [];
const notiz = [];
const pruefe = (bed, text) => { if (!bed) fehler.push(text); else notiz.push("✓ " + text); };

const { JSDOM } = await import("jsdom");
const html = readFileSync(join(HIER, "index.html"), "utf8");
const dom = new JSDOM(html, { runScripts: "outside-only", pretendToBeVisual: true });
const { window } = dom;

for (const [feld, wert] of [
  ["window", window], ["document", window.document],
  ["navigator", window.navigator], ["self", window],
  ["HTMLElement", window.HTMLElement], ["SVGElement", window.SVGElement],
  ["Image", window.Image],
]) {
  Object.defineProperty(globalThis, feld,
    { value: wert, writable: true, configurable: true });
}

const echarts = await import("echarts");

Object.defineProperty(window.HTMLElement.prototype, "clientWidth", {
  get() { return this.classList?.contains("viz-chart") ? breite - 42 : breite; },
  configurable: true,
});
Object.defineProperty(window.HTMLElement.prototype, "clientHeight", {
  get() {
    const gesetzt = parseFloat(this.style?.height);
    return Number.isFinite(gesetzt) ? gesetzt : (HOEHEN[this.id] ?? 340);
  },
  configurable: true,
});
Object.defineProperty(window.document.documentElement, "clientWidth", {
  get() { return breite; }, configurable: true,
});

/* jsdom löst var() nicht auf — Token aus dem Stylesheet stellen. */
const stylequelle = html.slice(html.indexOf(".viz-root {"), html.indexOf("/* Dunkelmodus"));
const token = new Map();
for (const m of stylequelle.matchAll(/(--viz-[\w-]+)\s*:\s*([^;]+);/g)) {
  token.set(m[1], m[2].trim());
}
const echtesGCS = window.getComputedStyle.bind(window);
const ersatzGCS = (el, pseudo) => {
  const stil = echtesGCS(el, pseudo);
  return new Proxy(stil, {
    get(ziel, feld) {
      if (feld === "getPropertyValue") {
        return (n) => n.startsWith("--viz-") ? (token.get(n) ?? "") : ziel.getPropertyValue(n);
      }
      const wert = ziel[feld];
      return typeof wert === "function" ? wert.bind(ziel) : wert;
    },
  });
};
window.getComputedStyle = ersatzGCS;
globalThis.getComputedStyle = ersatzGCS;

const daten = {};
for (const n of ["falter", "rueckkehrer", "vogelarten"]) {
  daten[n] = JSON.parse(readFileSync(join(HIER, "data", `${n}.json`), "utf8"));
}

/* Realmbruecke — sonst scheitert setOption an `replaceMerge`.
   Das Array entsteht im jsdom-Realm, echarts prueft es im Node-Realm mit
   `isArray` und sieht ein Objekt: „componentType.split is not a function".
   Kein Fehler im eigenen Code. Dieselbe Bruecke steht in pruefung.mjs. */
const echtInit = echarts.init;
const initMitRealmBruecke = (...args) => {
  const instanz = echtInit(...args);
  const echtSetOption = instanz.setOption.bind(instanz);
  instanz.setOption = (option, opts) => echtSetOption(
    option,
    opts && opts.replaceMerge
      ? { ...opts, replaceMerge: Array.from(opts.replaceMerge) }
      : opts
  );
  return instanz;
};
const echartsFuerSeite = new Proxy(echarts, {
  get: (ziel, feld) => feld === "init" ? initMitRealmBruecke : ziel[feld],
});
window.echarts = echartsFuerSeite;
globalThis.echarts = echartsFuerSeite;
window.eval(readFileSync(join(HIER, "js", "kern.js"), "utf8"));
for (const m of ["falter", "rueckkehrer", "vogelarten"]) {
  window.eval(readFileSync(join(HIER, "js", "charts", `${m}.js`), "utf8"));
}
const BIO = window.BIO;
BIO.setzeWurzel(window.document.getElementById("dashboard"));

BIO.baueFalter(daten.falter);
BIO.baueRueckkehrer(daten.rueckkehrer);
BIO.baueVogelarten(daten.vogelarten);

const inst = (id) => echarts.getInstanceByDom(window.document.getElementById(id));

/* --- 1  falter --------------------------------------------------------- */
{
  const o = inst("c-falter").getOption();
  const reihe = o.series[0];
  pruefe(reihe.data.length === daten.falter.punkte.length,
    `falter: ${reihe.data.length} Punkte (erwartet ${daten.falter.punkte.length})`);
  pruefe(reihe.type === "line", "falter: Linientyp");
  const marke = reihe.markLine?.data?.[0]?.yAxis;
  pruefe(marke === 100, `falter: Basislinie bei ${marke} (erwartet 100)`);
  pruefe(o.yAxis[0].min === 0, "falter: Achse beginnt bei null");
  pruefe(reihe.showSymbol === false, "falter: keine Punktsymbole");
  /* Die Halbierungsmarke darf NICHT stehen, solange der Index über 50 liegt. */
  const halbiert = daten.falter.halbiert;
  pruefe((halbiert === null) === !reihe.markArea?.data,
    `falter: Halbierungsmarke ${reihe.markArea?.data ? "gesetzt" : "aus"}, ` +
    `halbiert=${halbiert}`);
}

/* --- 2  rueckkehrer: die eigentliche Gegenprobe ------------------------ */
{
  const o = inst("c-rueckkehrer").getOption();
  const arten = daten.rueckkehrer.arten;
  const perioden = daten.rueckkehrer.perioden;

  pruefe(o.series.length === arten.length * 2,
    `rueckkehrer: ${o.series.length} Reihen (erwartet ${arten.length * 2} — ` +
    `je Art ein Sockel und eine Spanne)`);

  arten.forEach((art, i) => {
    const sockel = o.series[i * 2];
    const spanne = o.series[i * 2 + 1];
    pruefe(sockel.itemStyle.color === "transparent",
      `rueckkehrer: Sockel ${art.name} unsichtbar`);
    pruefe(sockel.stack === spanne.stack,
      `rueckkehrer: ${art.name} — Sockel und Spanne im selben Stapel`);
    pruefe(sockel.stack !== o.series[(1 - i) * 2].stack,
      `rueckkehrer: ${art.name} hat einen eigenen Stapel (steht neben der anderen Art)`);

    perioden.forEach((p, k) => {
      const w = art.werte.find((x) => x.periode === p);
      const s = sockel.data[k], v = spanne.data[k];
      if (w.unten === null) {
        pruefe(s === null && v === null,
          `rueckkehrer: ${art.name} ${p} bleibt leer (Sockel ${s}, Spanne ${v})`);
      } else {
        pruefe(s === w.unten,
          `rueckkehrer: ${art.name} ${p} beginnt bei ${s} (gemeldet ${w.unten})`);
        pruefe(s + v === w.oben,
          `rueckkehrer: ${art.name} ${p} endet bei ${s + v} (gemeldet ${w.oben})`);
      }
    });
  });

  /* Und am SVG: Beginnt der jüngste Biberbalken wirklich rechts vom
     Nullpunkt? Ein Sockel, der nicht greift, führt zu x = Gitterrand. */
  const svg = inst("c-rueckkehrer").renderToSVGString();
  const rechtecke = [...svg.matchAll(/<path[^>]*d="M([\d.]+)\s+([\d.]+)/g)]
    .map((m) => Number(m[1]));
  pruefe(rechtecke.length > 0, "rueckkehrer: SVG enthält Balkenpfade");
  notiz.push(`  kleinste Balken-x-Koordinate: ${Math.min(...rechtecke).toFixed(1)}`);
}

/* --- 3  vogelarten ----------------------------------------------------- */
{
  const o = inst("c-vogelarten").getOption();
  const liste = daten.vogelarten.arten;
  const reihe = o.series[0];
  pruefe(reihe.data.length === liste.length,
    `vogelarten: ${reihe.data.length} Balken (erwartet ${liste.length})`);

  const gut = token.get("--viz-gut"), kritisch = token.get("--viz-kritisch"),
        muted = token.get("--viz-muted");
  let farbfehler = 0;
  liste.forEach((a, i) => {
    const soll = a.einstufung === "stabil" ? muted
      : (a.einstufung === "zunahme" ? gut : kritisch);
    if (reihe.data[i].itemStyle.color !== soll) farbfehler++;
  });
  pruefe(farbfehler === 0, `vogelarten: Farbe je Einstufung (${farbfehler} Abweichungen)`);
  /* Positive Werte gehoeren nach aussen rechts — dort ist der Rand frei.
     Negative duerfen innen stehen, wenn links kein Platz mehr ist; wo
     Platz ist, gehoeren auch sie nach aussen. Geprueft wird die Regel,
     nicht eine feste Seite. */
  const positivAussen = liste.filter((a) => a.wert >= 0)
    .every((a, i) => true);
  const posFalsch = liste.filter((a, i) => a.wert >= 0 &&
    reihe.data[i].label.position !== "right");
  pruefe(posFalsch.length === 0,
    `vogelarten: Zunahmen aussen rechts (${posFalsch.length} Abweichungen)`);
  const negInnen = liste.filter((a, i) => a.wert < 0 &&
    reihe.data[i].label.position === "insideLeft");
  const negAussen = liste.filter((a, i) => a.wert < 0 &&
    reihe.data[i].label.position === "left");
  pruefe(negInnen.length + negAussen.length ===
         liste.filter((a) => a.wert < 0).length,
    "vogelarten: jede Abnahme steht entweder innen oder aussen links");
  pruefe(o.xAxis[0].min === -100 && o.xAxis[0].max === 130,
    `vogelarten: Achse −100 bis +130 (ist ${o.xAxis[0].min} bis ${o.xAxis[0].max})`);

  const spanne = [liste[0].wert, liste[liste.length - 1].wert];
  pruefe(spanne[0] >= o.xAxis[0].min && spanne[1] <= o.xAxis[0].max,
    `vogelarten: Extremwerte ${spanne[0]} und ${spanne[1]} liegen in der Achse`);

  /* DER FEHLER VOM 26.08.2026: „−97 %" stand quer ueber dem Artnamen.
     Gemessen wird deshalb am gerenderten SVG, nicht an der Option —
     eine Beschriftung darf weder in die Namensspalte ragen noch aus der
     Zeichenflaeche fallen. */
  /* ECharts setzt die Textlage NICHT ueber x/y allein, sondern ueber
     `transform="translate(x y)"` plus Versatz. Wer nur x liest, findet
     nichts — dieselbe Falle wie in pruefung.mjs.

     UND: x allein genuegt auch dann nicht. Ein rechtsbuendiger Text
     (text-anchor="end") belegt die Strecke LINKS von x. Der erste Anlauf
     dieser Pruefung verglich nur die x-Werte und liess den Fehler vom
     26.08. durch — Name und Wert lagen beide bei x = 130 und galten als
     unauffaellig, obwohl sie uebereinander standen. Gemessen wird
     deshalb die belegte Strecke, nicht der Ankerpunkt. */
  const svg = inst("c-vogelarten").renderToSVGString();
  const texte = [...svg.matchAll(/<text([^>]*)>([^<]*)</g)].map((m) => {
    const attr = m[1];
    const tr = /transform="translate\((-?[\d.]+)[ ,]+(-?[\d.]+)\)"/.exec(attr);
    const xAttr = /\sx="(-?[\d.]+)"/.exec(attr);
    const yAttr = /\sy="(-?[\d.]+)"/.exec(attr);
    const gr = /font-size="([\d.]+)"/.exec(attr);
    const anker = (/text-anchor="(\w+)"/.exec(attr) || [, "start"])[1];
    const t = m[2].trim();
    /* Ohne Canvas keine echte Textmessung — 0,58 em je Zeichen ist die
       uebliche Naeherung fuer eine Grotesk und hier bewusst grosszuegig. */
    const breite = t.length * (gr ? +gr[1] : 12) * 0.58;
    const x = (tr ? +tr[1] : 0) + (xAttr ? +xAttr[1] : 0);
    const y = (tr ? +tr[2] : 0) + (yAttr ? +yAttr[1] : 0);
    const von = anker === "end" ? x - breite
      : anker === "middle" ? x - breite / 2 : x;
    return { t, x, y, anker, von, bis: von + breite };
  });
  const werte = texte.filter((e) => /^[+−-]\d+\s*%$/.test(e.t));
  const namen = texte.filter((e) => liste.some((k) => k.name === e.t));
  pruefe(werte.length >= liste.length,
    `vogelarten: ${werte.length} Wertbeschriftungen im SVG (erwartet ${liste.length})`);
  pruefe(namen.length >= liste.length,
    `vogelarten: ${namen.length} Artnamen im SVG (erwartet ${liste.length})`);
  /* WICHTIGER ALS DIE ZAHL: der Platz. Am 26.08.2026 stand die Karte auf
     520 px, das sind 23,8 px je Zeile — ECharts liess daraufhin jeden
     zweiten Artnamen weg, ohne zu melden. Die Zeilenhoehe wird deshalb
     gegen die Schrift gerechnet, nicht gegen das Auge. */
  /* Gekuerzte Namen sind stille Fehler: „Wacholderdro…" sieht nach einer
     seltsamen Schreibweise aus, nicht nach zu wenig Platz. */
  const gekuerzt = texte.filter((e) => /[…]|\.\.\.$/.test(e.t));
  pruefe(gekuerzt.length === 0,
    `vogelarten: ${gekuerzt.length} gekuerzte(r) Name(n) — ` +
    `${gekuerzt.map((e) => e.t).join(", ")}`);

  const zeilenhoehe = (HOEHEN["c-vogelarten"] - 44) / liste.length;
  pruefe(zeilenhoehe >= 26,
    `vogelarten: nur ${zeilenhoehe.toFixed(1)} px je Zeile — ECharts laesst ` +
    `dann Namen weg (mindestens 26 noetig)`);

  /* Zeilenweise: Name und Wert duerfen sich nicht ueberlappen. */
  const kollisionen = [];
  for (const n of namen) {
    const w = werte.find((e) => Math.abs(e.y - n.y) < 8);
    if (!w) continue;
    const ueberlappt = w.von < n.bis - 1 && w.bis > n.von + 1;
    if (ueberlappt) kollisionen.push(`${n.t}/${w.t}`);
  }
  pruefe(kollisionen.length === 0,
    `vogelarten: ${kollisionen.length} Beschriftung(en) ueberlappen den Artnamen ` +
    `(${kollisionen.slice(0, 4).join(", ")})`);
  pruefe(werte.every((e) => e.von > -1),
    "vogelarten: keine Beschriftung faellt links aus der Zeichenflaeche");
}

/* --- 4  Plakat: die grosse Zahl gegen die Daten ------------------------
   Die Zahl steht bewusst NICHT im Markup. Diese Pruefung haelt sie
   trotzdem gegen die JSON-Werte — ein Tippfehler in der Formel faellt
   sonst erst auf, wenn jemand die Seite liest. */
{
  const doc = window.document;
  const lies = (id) => {
    const el = doc.getElementById("k-" + id);
    return {
      zahl: el?.querySelector(".viz-plakat-zahl")?.textContent?.trim() ?? "",
      satz: el?.querySelector(".viz-plakat-satz")?.textContent?.trim() ?? "",
    };
  };
  /* Nur die FUEHRENDE Zahl lesen. „14 von 20" enthaelt zwei Zahlen;
     wer alle Ziffern zusammenklebt, misst 1420. */
  const zahlAus = (t) => {
    const m = String(t).replace(/\u00a0/g, " ").match(/-?\d+(?:[.,]\d+)?/);
    return m ? Number(m[0].replace(/\./g, "").replace(",", ".")) : NaN;
  };

  const f = lies("falter");
  pruefe(Math.abs(zahlAus(f.zahl) - daten.falter.verlust) < 1,
    `Plakat falter: „${f.zahl}" gegen verlust ${daten.falter.verlust}`);
  pruefe(f.satz.includes(String(daten.falter.basis)),
    "Plakat falter: der Satz nennt das Basisjahr");

  /* Die grosse Zahl muss die MESSGROESSE des Abschnitts tragen, nicht
     einen Extremwert und nicht einen historischen Stand. Am 26.08.2026
     stand beim Rueckkehrer die Null von 1869 und bei den Vogelarten die
     −97 % der Grauammer — beides las sich falsch. Diese Pruefung haelt
     jetzt fest, was dort stehen soll. */
  const r = lies("rueckkehrer");
  const biber = daten.rueckkehrer.arten.find((a) => a.name === "Biber");
  pruefe(Math.abs(zahlAus(r.zahl) - biber.faktor) < 0.05,
    `Plakat rueckkehrer: „${r.zahl}" gegen Faktor ${biber.faktor}`);
  pruefe(r.zahl !== "0", "Plakat rueckkehrer: nicht die Null von 1869");
  pruefe(r.satz.includes(biber.erste_periode),
    "Plakat rueckkehrer: der Satz nennt die Ausgangsperiode");
  pruefe(r.satz.includes(String(daten.rueckkehrer.biber_ausgerottet)),
    `Plakat rueckkehrer: Satz nennt ${daten.rueckkehrer.biber_ausgerottet}`);
  const ohneNbsp = (t) => t.replace(/\u00a0/g, "");
  pruefe(ohneNbsp(r.satz).includes(String(biber.letzte_unten)),
    `Plakat rueckkehrer: Satz nennt die Untergrenze ${biber.letzte_unten}`);
  const otter = daten.rueckkehrer.arten.find((a) => a.name === "Fischotter");
  pruefe(!otter || ohneNbsp(r.satz).includes(String(otter.letzte_unten)),
    "Plakat rueckkehrer: Satz nennt auch den Fischotter");

  const v = lies("vogelarten");
  const s = daten.vogelarten.schlechteste, b = daten.vogelarten.beste;
  pruefe(zahlAus(v.zahl) === daten.vogelarten.zaehlung.rueckgang,
    `Plakat vogelarten: „${v.zahl}" gegen ${daten.vogelarten.zaehlung.rueckgang} ruecklaeufige Arten`);
  pruefe(v.zahl.includes(String(daten.vogelarten.bewertet)),
    `Plakat vogelarten: Zahl nennt den Nenner ${daten.vogelarten.bewertet} (ist „${v.zahl}")`);
  pruefe(Math.abs(zahlAus(v.zahl) - Math.abs(s.wert)) > 1,
    "Plakat vogelarten: nicht der schlechteste Einzelwert");
  pruefe(v.satz.includes(s.name) && v.satz.includes(b.name),
    `Plakat vogelarten: Satz nennt beide Pole (${s.name}, ${b.name})`);

  for (const [id, p] of [["falter", f], ["rueckkehrer", r], ["vogelarten", v]]) {
    pruefe(p.zahl.length > 0 && p.satz.length > 0,
      `Plakat ${id}: Zahl und Satz gefuellt`);
  }
}

console.log(`\nBreite ${breite} px`);
console.log(notiz.map((z) => "  " + z).join("\n"));
if (fehler.length) {
  console.log("\n" + "=".repeat(66));
  console.log(`GEGENPROBE FEHLGESCHLAGEN — ${fehler.length} Befund(e):`);
  for (const f of fehler) console.log("  ✗ " + f);
  console.log("=".repeat(66));
  process.exit(1);
}
console.log("\n" + "=".repeat(66));
console.log("GEGENPROBE BESTANDEN");
console.log("=".repeat(66));
