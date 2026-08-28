/* ===========================================================================
   Einbettseite prüfen — jsdom + echarts, SVG-Renderer
   ---------------------------------------------------------------------------
   Prüft für alle acht Grafiknamen, dass embed.html?chart=<name> genau die
   Bedingungen herstellt, auf die social/rendern.py im echten Browser
   wartet. Tritt eine davon nicht ein, wartet der Bot dort 30 Sekunden und
   fällt durch — hier fällt es in einer Sekunde auf.

   Geprüft wird je Grafik:
     1. In #c-<name> entsteht eine Zeichenfläche (ECharts-Instanz mit Pfaden).
     2. #untertitel ist gefüllt und enthält nicht mehr „werden geladen".
     3. #signatur ist nicht leer.
     4. Kein JavaScript-Fehler beim Aufbau.
   Zusätzlich: #hinweisfeld gefüllt, und bei chart=boden existiert das Ziel
   t-boden-kategorien, das boden.js beschreibt.

   Umgebungsaufbau übernommen aus docs/pruefung.mjs — dort steht auch,
   warum jedes Stück nötig ist. Kurzfassung der vier Fallen:
     · jsdom rechnet kein Layout, clientWidth/clientHeight werden gestellt.
     · getComputedStyle löst var() nicht auf, die Token kommen aus dem
       <style>-Block der Einbettseite selbst.
     · echarts prüft beim Import auf `document` — daher dynamischer Import
       NACH dem Aufbau der Umgebung.
     · `instanceof Array` schlägt über Realm-Grenzen fehl, daher die
       Brücke um setOption.
   Weil dieser Zustand global und einmalig ist, läuft je Grafik ein
   EIGENER Prozess: der Aufruf ohne Argument startet sich achtmal selbst.

   Anders als index.html führt embed.html seine Logik in einem inline
   <script> aus, das jsdom mit runScripts:"outside-only" nicht startet.
   Der Block wird deshalb unten herausgeschnitten und über window.eval
   ausgeführt; danach wird los() von Hand aufgerufen, weil DOMContentLoaded
   zu diesem Zeitpunkt längst gefallen ist.

   Aufruf:
       node docs/pruefung-embed.mjs
   =========================================================================== */

import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";

const HIER = dirname(fileURLToPath(import.meta.url));

const GRAFIKEN = ["schutzgebiete", "vogel", "boden", "rotelisten",
                  "erhaltung", "lebensraeume", "biotoptypen", "wald",
                  "totholz", "fichte",
                  "baumarten", "waldarten", "natura2000",
                  "biolandbau",
                  "falter", "rueckkehrer", "vogelarten"];

/* Eine Breite reicht: die Einbettung sitzt im iframe der Gastgeberseite,
   und rendern.py setzt dort ein festes Fenster. 1100 px entspricht dem
   Desktopfall, den der Bot aufnimmt. */
const BREITE = 1100;

/* --- Ohne Argument: sich selbst je Grafik einmal starten ---------------- */
const argument = process.argv.find((a) => a.startsWith("--chart="));
if (!argument) {
  const schief = [];
  for (const g of GRAFIKEN) {
    const lauf = spawnSync(process.execPath,
      [fileURLToPath(import.meta.url), `--chart=${g}`],
      { stdio: "inherit", env: process.env });
    if (lauf.status !== 0) schief.push(g);
  }
  console.log("=".repeat(70));
  console.log(schief.length
    ? `EINBETTPRÜFUNG FEHLGESCHLAGEN — ${schief.join(", ")}`
    : `EINBETTPRÜFUNG BESTANDEN — ${GRAFIKEN.length} Grafiken.`);
  console.log("=".repeat(70));
  process.exit(schief.length ? 1 : 0);
}

const chart = argument.split("=")[1];

const fehler = [];
const hinweise = [];
const pruefe = (bedingung, text) => { if (!bedingung) fehler.push(text); };

/* --- Umgebung aufbauen, BEVOR echarts importiert wird ------------------- */
const { JSDOM, VirtualConsole } = await import("jsdom");
const html = readFileSync(join(HIER, "embed.html"), "utf8");

/* ECharts misst Textbreiten über einen Canvas-Kontext. Den gibt es ohne
   das native canvas-Paket nicht, und jsdom meldet das je Messung einmal —
   dutzende Zeilen, die keinen Befund tragen. Sie werden hier verschluckt,
   alles andere aus der Seite bleibt sichtbar. Folge: Textbreiten sind
   geschätzt, nicht gemessen (siehe Kopf von pruefung.mjs). */
const stilleKonsole = new VirtualConsole();
stilleKonsole.on("jsdomError", (e) => {
  if (!/Not implemented/.test(String(e?.message))) console.error(e);
});
for (const art of ["log", "info", "warn", "error"]) {
  stilleKonsole.on(art, (...a) => console[art](...a));
}

const dom = new JSDOM(html, {
  runScripts: "outside-only",
  pretendToBeVisual: true,
  virtualConsole: stilleKonsole,
  url: `https://example.invalid/embed.html?chart=${encodeURIComponent(chart)}`,
});
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

/* --- Layout stellen ----------------------------------------------------- */
/* .viz-root hat 18 px Innenabstand je Seite, das Diagrammfeld ist also
   36 px schmaler als das Dokument. */
const FELDBREITE = BREITE - 36;
Object.defineProperty(window.HTMLElement.prototype, "clientWidth", {
  get() { return this.classList?.contains("viz-chart") ? FELDBREITE : BREITE; },
  configurable: true,
});
/* Eine per JavaScript gesetzte Höhe muss gewinnen: balkenHoehe() in
   kern.js schreibt style.height, und ECharts liest danach clientHeight.
   Sonst gelten die Feldhöhen aus dem <style>-Block der Einbettseite. */
Object.defineProperty(window.HTMLElement.prototype, "clientHeight", {
  get() {
    const gesetzt = parseFloat(this.style?.height);
    if (Number.isFinite(gesetzt)) return gesetzt;
    return this.classList?.contains("viz-chart-hoch") ? 420 : 340;
  },
  configurable: true,
});
Object.defineProperty(window.document.documentElement, "clientWidth", {
  get() { return BREITE; }, configurable: true,
});

/* matchMedia fehlt in jsdom. Gestellt wird die Desktopantwort, passend
   zu BREITE — kern.js fragt damit die Schwelle bei 768 px ab. */
window.matchMedia = (abfrage) => ({
  media: abfrage, matches: false,
  addEventListener() {}, removeEventListener() {},
  addListener() {}, removeListener() {},
});
globalThis.matchMedia = window.matchMedia;

/* ResizeObserver fehlt in jsdom; embed.html beobachtet damit die
   Dokumenthöhe. Ohne Ersatz bräche los() genau dort ab — im Browser
   nicht, deshalb ist der Ersatz Prüfmechanik und kein Befund. */
window.ResizeObserver = class { observe() {} unobserve() {} disconnect() {} };
globalThis.ResizeObserver = window.ResizeObserver;

/* --- CSS-Variablen beantworten ------------------------------------------ */
const stilquelle = html.slice(html.indexOf(".viz-root {"), html.indexOf("/* Dunkelmodus"));
const token = new Map();
for (const m of stilquelle.matchAll(/(--viz-[\w-]+)\s*:\s*([^;]+);/g)) {
  token.set(m[1], m[2].trim());
}
pruefe(token.size > 20,
  `[${chart}] Nur ${token.size} Token aus embed.html gelesen — Stylesheet-Aufbau geändert?`);
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

/* --- Daten aus docs/data/ statt über das Netz --------------------------- */
window.fetch = async (pfad) => {
  const schluessel = String(pfad).split("?")[0].split("/").pop().replace(".json", "");
  try {
    const inhalt = JSON.parse(
      readFileSync(join(HIER, "data", `${schluessel}.json`), "utf8"));
    return { ok: true, status: 200, json: async () => inhalt };
  } catch {
    return { ok: false, status: 404, json: async () => ({}) };
  }
};
globalThis.fetch = window.fetch;

/* --- Realm-Brücke um setOption (siehe Kopfkommentar) -------------------- */
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

/* --- Alles, was die Seite auf die Konsole schreibt, einsammeln ---------- */
const konsolenfehler = [];
window.console = {
  ...console,
  error: (...a) => konsolenfehler.push(a.map(String).join(" ")),
  warn: (...a) => hinweise.push(`[${chart}] ${a.map(String).join(" ")}`),
};

/* Entspricht pageerror in einem echten Browser: alles, was durch die
   Ereignisschleife nach oben durchschlägt, statt still zu verschwinden. */
const seitenfehler = [];
window.addEventListener("error", (e) => seitenfehler.push(String(e.message ?? e)));
process.on("unhandledRejection",
  (grund) => seitenfehler.push(`unhandledRejection: ${grund?.stack ?? grund}`));

/* --- Die Skripte laden, die embed.html per <script src> einbindet ------- */
const quellen = [...html.matchAll(/<script src="(js\/[^"?]+)/g)].map((m) => m[1]);
/* Je Grafik ein Modul, dazu kern.js. Die Zahl stand bis 26.08.2026 fest
   im Text und meldete beim Ergaenzen einer Grafik einen Fehler, den es
   nicht gab — jetzt folgt sie der Liste. */
const sollModule = GRAFIKEN.length + 1;
pruefe(quellen.length === sollModule,
  `[${chart}] ${quellen.length} Moduldateien in embed.html verlinkt statt ${sollModule}`);
for (const datei of quellen) {
  window.eval(readFileSync(join(HIER, datei), "utf8"));
}

/* --- Den inline <script>-Block ausführen -------------------------------- */
/* Herausgeschnitten wird der letzte <script>-Block ohne src-Attribut —
   das ist die Ablaufsteuerung der Einbettseite. */
const inline = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map((m) => m[1]);
if (inline.length !== 1) {
  fehler.push(`[${chart}] ${inline.length} inline <script>-Blöcke statt 1 gefunden`);
} else {
  window.eval(inline[0]);
  pruefe(typeof window.los === "function",
    `[${chart}] Funktion los() ist nach dem Auswerten nicht erreichbar`);
  if (typeof window.los === "function") {
    try {
      await window.los();
    } catch (e) {
      seitenfehler.push(`los(): ${e?.stack ?? e}`);
    }
  }
}

/* document.fonts.ready gibt es in jsdom nicht; die Neuvermessung nach
   dem Schriftladen fällt hier aus. Der Aufbau selbst ist davon
   unabhängig — geprüft wird der Zustand direkt nach los(). */

/* --- Erwartungen -------------------------------------------------------- */
const doc = window.document;
const t = (id) => doc.getElementById(id)?.textContent?.trim() ?? "";

pruefe(seitenfehler.length === 0,
  `[${chart}] JavaScript-Fehler beim Aufbau: ${seitenfehler.join(" | ")}`);
pruefe(konsolenfehler.length === 0,
  `[${chart}] Konsolenfehler: ${konsolenfehler.join(" | ")}`);

/* 1. Zeichenfläche in #c-<name> */
const feld = doc.getElementById(`c-${chart}`);
if (!feld) {
  fehler.push(`[${chart}] Feld c-${chart} wurde nicht angelegt`);
} else {
  const instanz = echarts.getInstanceByDom(feld);
  if (!instanz) {
    fehler.push(`[${chart}] c-${chart} hat keine ECharts-Instanz — rendern.py würde 30 s warten`);
  } else {
    const svg = instanz.renderToSVGString();
    const pfade = (svg.match(/<path/g) || []).length;
    pruefe(pfade > 3, `[${chart}] c-${chart}: nur ${pfade} Pfade — Grafik vermutlich leer`);
    /* Text, der aus dem Feld ragt, ist auf der Einbettseite genauso ein
       Fehler wie im Dashboard — dort ist nur das Feld schmaler. */
    const raus = [];
    for (const m of svg.matchAll(/<text[^>]*\sx="(-?[\d.]+)"[^>]*>([^<]*)/g)) {
      const x = parseFloat(m[1]);
      if (x < -2 || x > FELDBREITE + 2) raus.push(`"${m[2]}" bei x=${x}`);
    }
    pruefe(raus.length === 0,
      `[${chart}] c-${chart}: Text ausserhalb der Zeichenflaeche (0–${FELDBREITE}): ${raus.slice(0, 4).join(", ")}`);
  }
}

/* 2. Untertitel — gefüllt und nicht mehr der Ladetext */
const untertitel = t("untertitel");
pruefe(untertitel.length > 0, `[${chart}] #untertitel ist leer`);
pruefe(!untertitel.includes("werden geladen"),
  `[${chart}] #untertitel steht noch auf „${untertitel}" — rendern.py wartet darauf vergeblich`);
pruefe(!untertitel.includes("konnten nicht geladen werden"),
  `[${chart}] #untertitel meldet einen Datenausfall: „${untertitel}"`);
pruefe(!untertitel.includes("Unbekannte Grafik"),
  `[${chart}] embed.html kennt diesen Namen nicht: „${untertitel}"`);

/* 3. Signatur */
pruefe(t("signatur").length > 0,
  `[${chart}] #signatur ist leer — Namensnennung fehlt und rendern.py wartet darauf`);

/* Zusätzlich: Hinweiszeile und Quellenangabe */
pruefe(t("hinweisfeld").length > 0, `[${chart}] #hinweisfeld ist leer`);
pruefe(t("quelle").includes("Datenquellen"), `[${chart}] Quellenzeile ohne Datenquellen`);
pruefe(t("stand").startsWith("Stand:"), `[${chart}] Standzeile fehlt`);
pruefe(t("titel").length > 0 && t("titel") !== "Biodiversität Österreich",
  `[${chart}] #titel wurde nicht auf den Grafiktitel gesetzt`);

/* Zusätzlich: boden.js schreibt seine Kategorientabelle in ein eigenes
   Ziel. Fehlt das Element, bricht der Aufbau ab — deshalb hier eigens. */
if (chart === "boden") {
  pruefe(doc.getElementById("t-boden-kategorien") !== null,
    `[${chart}] Element t-boden-kategorien fehlt — boden.js schreibt dorthin`);
  pruefe((doc.getElementById("t-boden-kategorien")?.innerHTML ?? "").length > 0,
    `[${chart}] t-boden-kategorien blieb leer`);
}

/* Die Hinweiszeile stammt aus dem Datensatz und wird ins h-Feld gelegt;
   ist dieses leer, hat das Modul das Feld nicht gefunden. */
pruefe(t(`h-${chart}`).length > 0, `[${chart}] verstecktes Feld h-${chart} blieb leer`);
pruefe(t(`u-${chart}`).length > 0, `[${chart}] verstecktes Feld u-${chart} blieb leer`);

/* --- Ergebnis ----------------------------------------------------------- */
console.log("-".repeat(70));
console.log(`embed.html?chart=${chart}`);
for (const h of hinweise) console.log(`  · ${h}`);
if (fehler.length) {
  for (const f of fehler) console.log(`  ✗ ${f}`);
  process.exit(1);
}
console.log(`  ✓ Zeichenfläche, Untertitel („${untertitel.slice(0, 60)}"), Signatur, Hinweis`);
