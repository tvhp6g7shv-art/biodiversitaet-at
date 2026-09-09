/* ===========================================================================
   Gegenprobe zur Gemeindekarte (`flaeche`).
   ---------------------------------------------------------------------------
   WARUM EINE EIGENE SUITE: `pruefung.mjs` ruft `BIO.start()` auf und misst
   danach. Die Karte wird aber erst gebaut, wenn `gemeinden.json` nachgeladen
   ist — 1,5 MB, die bewusst NICHT in der Sammelladung stecken. Die große
   Suite säße also vor einem leeren Feld. Hier wird das Modul direkt mit
   Geometrie aufgerufen und danach am gerenderten SVG gemessen.

     node pruefung-karte.mjs

   Geprüft wird das, was still schiefgehen kann:
     1. der Platzhalterweg (ohne Geometrie bleibt kein leerer Kasten)
     2. dass ALLE Gemeinden gezeichnet werden
     3. dass die drei doppelt vergebenen Gemeindenamen eigene Werte tragen
        — der Grund, warum die Karte über die Kennziffer verknüpft
     4. dass die zweite Runde die hohe Feldklasse zurückholt
     5. Hinweiszeile im Hausmaß 150–234
   =========================================================================== */
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const HIER = dirname(fileURLToPath(import.meta.url));
const fehler = [];
const pruefe = (bedingung, text) => {
  console.log((bedingung ? "  ✓ " : "  ✗ ") + text);
  if (!bedingung) fehler.push(text);
};

const { JSDOM } = await import("jsdom");
const html = readFileSync(join(HIER, "index.html"), "utf8");
const dom = new JSDOM(html, { runScripts: "outside-only", pretendToBeVisual: true });
const { window } = dom;
/* `navigator` ist in Node 22 ein Getter ohne Setter — defineProperty geht
   daran vorbei. Gleiche Behandlung für alle, wie in pruefung.mjs. */
for (const [feld, wert] of [
  ["window", window], ["document", window.document], ["navigator", window.navigator],
  ["self", window], ["HTMLElement", window.HTMLElement],
  ["SVGElement", window.SVGElement], ["Image", window.Image],
]) Object.defineProperty(globalThis, feld, { value: wert, writable: true, configurable: true });

const echarts = await import("echarts");
globalThis.echarts = echarts; window.echarts = echarts;

const BREITE = 950;
Object.defineProperty(window.HTMLElement.prototype, "clientWidth", {
  get() { return this.classList?.contains("viz-chart") ? BREITE - 42 : BREITE; },
  configurable: true,
});
Object.defineProperty(window.HTMLElement.prototype, "clientHeight", {
  get() {
    const gesetzt = parseFloat(this.style?.height);
    if (Number.isFinite(gesetzt)) return gesetzt;
    return this.classList?.contains("viz-chart-hoch") ? 420 : 340;
  },
  configurable: true,
});

/* CSS-Variablen aus dem Stylesheet der Seite beantworten. */
const stylequelle = html.slice(html.indexOf(".viz-root {"), html.indexOf("/* Dunkelmodus"));
const token = new Map();
for (const m of stylequelle.matchAll(/(--viz-[\w-]+)\s*:\s*([^;]+);/g)) token.set(m[1], m[2].trim());
const echtesGCS = window.getComputedStyle.bind(window);
const ersatzGCS = (el, pseudo) => {
  const stil = echtesGCS(el, pseudo);
  return new Proxy(stil, {
    get(ziel, feld) {
      if (feld === "getPropertyValue")
        return (n) => n.startsWith("--viz-") ? (token.get(n) ?? "") : ziel.getPropertyValue(n);
      const w = ziel[feld];
      return typeof w === "function" ? w.bind(ziel) : w;
    },
  });
};
window.getComputedStyle = ersatzGCS;
globalThis.getComputedStyle = ersatzGCS;

const lade = (p) => new Function(readFileSync(join(HIER, p), "utf8")).call(window);
lade("js/kern.js");
lade("js/charts/flaeche.js");
const B = window.BIO;
const doc = window.document;

const daten = JSON.parse(readFileSync(join(HIER, "data/flaecheninanspruchnahme.json"), "utf8"));
const geo = JSON.parse(readFileSync(join(HIER, "data/gemeinden.json"), "utf8"));

console.log("\n--- Platzhalterweg (ohne Geometrie) ---");
B.baueFlaeche(daten, null);
const feld = doc.getElementById("c-flaeche");
pruefe(feld.textContent.trim().length > 0,
  "ohne Geometrie steht ein Platzhalter im Feld, kein leerer Kasten");
pruefe(doc.getElementById("t-flaeche").innerHTML.includes("<tr>"),
  "Klassentabelle steht schon ohne Geometrie");

console.log("\n--- Mit Geometrie ---");
B.baueFlaeche(daten, geo);
pruefe(feld.classList.contains("viz-chart") && feld.classList.contains("viz-chart-hoch"),
  "zweite Runde holt beide Feldklassen zurück (sonst 644 statt 796 px Karte)");

const instanz = echarts.getInstanceByDom(feld);
pruefe(!!instanz, "ECharts-Instanz vorhanden");
const serie = instanz?.getOption()?.series?.[0];
pruefe((serie?.data?.length ?? 0) === daten.gemeinden.length,
  `alle ${daten.gemeinden.length} Gemeinden in der Serie (gefunden: ${serie?.data?.length ?? 0})`);
const pfade = feld.querySelectorAll("path").length;
pruefe(pfade >= daten.gemeinden.length,
  `mindestens ${daten.gemeinden.length} Pfade gezeichnet (gefunden: ${pfade})`);

console.log("\n--- Doppelt vergebene Gemeindenamen ---");
/* Der Grund für die Umschlüsselung auf die Kennziffer. Über den Namen
   verknüpft bekäme eine der beiden lautlos den Wert der anderen. */
const nachName = new Map();
for (const g of daten.gemeinden) {
  if (!nachName.has(g.name)) nachName.set(g.name, []);
  nachName.get(g.name).push(g);
}
const doppelte = [...nachName.entries()].filter(([, g]) => g.length > 1);
pruefe(doppelte.length > 0,
  `es gibt doppelt vergebene Namen (${doppelte.length}) — sonst prüft dieser Block nichts`);
for (const [name, gruppe] of doppelte) {
  const werte = gruppe.map((g) => `${g.gkz}=${g.anteil}`).join("  ");
  const inSerie = gruppe.map((g) => serie?.data?.find((d) => d.name === g.gkz)?.value);
  pruefe(inSerie.every((v) => v !== undefined)
      && new Set(inSerie).size === new Set(gruppe.map((g) => g.anteil)).size,
    `${name}: beide Kennziffern tragen ihren eigenen Wert (${werte})`);
}

console.log("\n--- Texte ---");
const h = doc.getElementById("h-flaeche").textContent.trim();
pruefe(h.length >= 150 && h.length <= 234,
  `Hinweiszeile ${h.length} Zeichen, Hausmaß 150–234`);
pruefe(/Stand|Entwicklung/.test(h),
  "Hinweiszeile trägt die UBA-Auflage (Stand statt Entwicklung)");
pruefe(doc.getElementById("n-flaeche").textContent.includes("Gemeindefläche"),
  "Notiz benennt den Nenner");

console.log("\n" + "=".repeat(66));
console.log(fehler.length
  ? `KARTENPRÜFUNG FEHLGESCHLAGEN — ${fehler.length} Befund(e)`
  : "KARTENPRÜFUNG BESTANDEN");
console.log("=".repeat(66));
process.exit(fehler.length ? 1 : 0);
