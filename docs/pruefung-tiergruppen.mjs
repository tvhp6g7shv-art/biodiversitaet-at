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

const HOEHEN = { "c-falter": 340, "c-rueckkehrer": 300, "c-vogelarten": 520 };

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
  let farbfehler = 0, seitefehler = 0;
  liste.forEach((a, i) => {
    const soll = a.einstufung === "stabil" ? muted
      : (a.einstufung === "zunahme" ? gut : kritisch);
    if (reihe.data[i].itemStyle.color !== soll) farbfehler++;
    const sollSeite = a.wert < 0 ? "left" : "right";
    if (reihe.data[i].label.position !== sollSeite) seitefehler++;
  });
  pruefe(farbfehler === 0, `vogelarten: Farbe je Einstufung (${farbfehler} Abweichungen)`);
  pruefe(seitefehler === 0,
    `vogelarten: Beschriftung außen am Balken (${seitefehler} Abweichungen)`);
  pruefe(o.xAxis[0].min === -100 && o.xAxis[0].max === 130,
    `vogelarten: Achse −100 bis +130 (ist ${o.xAxis[0].min} bis ${o.xAxis[0].max})`);

  const spanne = [liste[0].wert, liste[liste.length - 1].wert];
  pruefe(spanne[0] >= o.xAxis[0].min && spanne[1] <= o.xAxis[0].max,
    `vogelarten: Extremwerte ${spanne[0]} und ${spanne[1]} liegen in der Achse`);
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
      zusatz: el?.querySelector(".viz-plakat-zusatz")?.textContent?.trim() ?? "",
      satz: el?.querySelector(".viz-plakat-satz")?.textContent?.trim() ?? "",
    };
  };
  const zahlAus = (t) => Number(t.replace(/[^\d,.-]/g, "").replace(/\./g, "").replace(",", "."));

  const f = lies("falter");
  pruefe(Math.abs(zahlAus(f.zahl) - daten.falter.verlust) < 1,
    `Plakat falter: „${f.zahl}" gegen verlust ${daten.falter.verlust}`);
  pruefe(f.zusatz.includes(String(daten.falter.basis)),
    `Plakat falter: Zusatz nennt das Basisjahr (${f.zusatz})`);

  const r = lies("rueckkehrer");
  pruefe(r.zahl === "0", `Plakat rueckkehrer: grosse Zahl ist die Null (ist „${r.zahl}")`);
  pruefe(r.zusatz.includes(String(daten.rueckkehrer.biber_ausgerottet)),
    `Plakat rueckkehrer: Zusatz nennt ${daten.rueckkehrer.biber_ausgerottet} (${r.zusatz})`);
  const biber = daten.rueckkehrer.arten.find((a) => a.name === "Biber");
  pruefe(r.satz.includes(String(biber.letzte_unten).replace(/\B(?=(\d{3})+(?!\d))/g, "\u00a0")) ||
         r.satz.replace(/\u00a0/g, "").includes(String(biber.letzte_unten)),
    `Plakat rueckkehrer: Satz nennt die Untergrenze ${biber.letzte_unten}`);

  const v = lies("vogelarten");
  const s = daten.vogelarten.schlechteste, b = daten.vogelarten.beste;
  pruefe(Math.abs(zahlAus(v.zahl) - Math.abs(s.wert)) < 1,
    `Plakat vogelarten: „${v.zahl}" gegen schlechteste ${s.wert}`);
  pruefe(v.zusatz.includes(s.name), `Plakat vogelarten: Zusatz nennt ${s.name}`);
  pruefe(v.satz.includes(b.name) && v.satz.includes(String(b.wert)),
    `Plakat vogelarten: Satz nennt ${b.name} mit ${b.wert}`);

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
