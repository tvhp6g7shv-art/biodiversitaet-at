/* ===========================================================================
   Sichtprüfung ohne Browser — jsdom + echarts, SVG-Renderer
   ---------------------------------------------------------------------------
   Prüft, was ein Blick auf die Seite prüfen würde, nur reproduzierbar:
   Laufen alle Module durch? Steht Text außerhalb der Zeichenfläche? Trägt
   jede Grafik ihren Untertitel? Hat jede Tabelle Zeilen?

   Warum nicht im Browser: `file://` funktioniert im Automatisierungstab
   nicht, ein Headless-Chromium steht nicht zur Verfügung. jsdom mit
   gestelltem Layout funktioniert — mit DREI Einschränkungen, die man
   kennen muss, weil jede davon eine halbe Stunde gekostet hat:

   1. jsdom rechnet KEIN Layout. `clientWidth` ist überall 0, `istSchmal()`
      wäre also immer wahr und die Desktop-Variante nie geprüft. Die
      Feldmaße werden deshalb unten von Hand gestellt.

   2. `getComputedStyle` löst `var()` in jsdom NICHT auf. Ohne Ersatz
      bekommt ECharts überall Leerstrings und zeichnet in seinen
      Vorgabefarben — die Prüfung träfe eine andere Grafik als die echte.
      Die Token werden deshalb aus dem <style>-Block gelesen.

   3. ECharts prüft BEIM IMPORT, ob `document` existiert, und schaltet
      sonst in einen Modus ohne DOM. Deshalb muss die jsdom-Umgebung
      stehen, BEVOR echarts importiert wird — daher der dynamische Import
      weiter unten. Und weil dieser Zustand global und einmalig ist, läuft
      je Bildschirmbreite ein EIGENER Prozess: der Aufruf ohne Argument
      startet sich selbst zweimal.

   WAS DIESE PRÜFUNG NICHT KANN, damit niemand ihr zu viel zutraut:
   Ohne das native `canvas`-Paket misst ECharts Textbreiten nur geschätzt
   (Zeichenzahl mal Faktor) statt echt. Die Lageprüfung unten findet
   deshalb grobe Ausreißer — einen Namen, der halb aus dem Feld ragt —
   aber nicht die letzten Pixel. Wer eine Abschneidung auf den Punkt
   klären muss, braucht weiterhin einen echten Browser.

   Aufruf:
       npm install jsdom echarts@5.5.1
       node docs/pruefung.mjs
   =========================================================================== */

import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";

const HIER = dirname(fileURLToPath(import.meta.url));

/* Zwei Breiten: Desktop und knapp unter der 560er-Schwelle. Genau dort
   schlägt das Layout um, und genau dort sind im Schwesterprojekt vier Mal
   Fehler entstanden. */
const BREITEN = [
  { name: "Desktop", breite: 1100 },
  { name: "Schmal",  breite: 420 },
];

/* --- Ohne Argument: sich selbst je Breite einmal starten --------------- */
const argument = process.argv.find((a) => a.startsWith("--breite="));
if (!argument) {
  let schiefgegangen = 0;
  for (const { name, breite } of BREITEN) {
    const lauf = spawnSync(process.execPath,
      [fileURLToPath(import.meta.url), `--breite=${breite}`, `--name=${name}`],
      { stdio: "inherit", env: process.env });
    if (lauf.status !== 0) schiefgegangen++;
  }
  console.log("=".repeat(70));
  console.log(schiefgegangen
    ? `PRÜFUNG FEHLGESCHLAGEN — ${schiefgegangen} von ${BREITEN.length} Breiten`
    : `PRÜFUNG BESTANDEN — ${BREITEN.length} Breiten, alle Abschnitte.`);
  console.log("=".repeat(70));
  process.exit(schiefgegangen ? 1 : 0);
}

const breite = parseInt(argument.split("=")[1], 10);
const name = (process.argv.find((a) => a.startsWith("--name=")) || "=?").split("=")[1];

/* Feldhöhen wie im CSS. jsdom liest sie nicht aus dem Stylesheet — wer
   sie dort ändert, muss hier mit. */
const HOEHEN = {
  "c-schutzgebiete": 340,
  "c-vogel": 420,
  "c-boden": 340,
  "c-rotelisten": 690,
  "c-erhaltung": 260,
  "c-biotoptypen": 300,
  "c-wald": 340,
  "c-biolandbau": 760,
};

const MODULE = ["kern.js", "charts/kpi.js", "charts/schutzgebiete.js",
                "charts/vogel.js", "charts/boden.js", "charts/rotelisten.js",
                "charts/erhaltung.js", "charts/biotoptypen.js",
                "charts/wald.js", "charts/biolandbau.js"];

const DATEN = ["meta", "kpi", "schutzgebiete", "vogel", "boden", "rotelisten",
               "erhaltung", "biotoptypen", "wald", "biolandbau"];

const ABSCHNITTE = ["schutzgebiete", "vogel", "boden", "rotelisten",
                    "erhaltung", "biotoptypen", "wald", "biolandbau"];

const fehler = [];
const hinweise = [];
const pruefe = (bedingung, text) => { if (!bedingung) fehler.push(text); };

/* --- Umgebung aufbauen, BEVOR echarts importiert wird ------------------ */
const { JSDOM } = await import("jsdom");
const html = readFileSync(join(HIER, "index.html"), "utf8");
const dom = new JSDOM(html, { runScripts: "outside-only", pretendToBeVisual: true });
const { window } = dom;

/* `navigator` ist in Node 22 ein Getter ohne Setter — einfache Zuweisung
   wirft. defineProperty geht an ihm vorbei. Dieselbe Behandlung für alle,
   damit der Grund an einer Stelle steht und nicht beim nächsten Node-Wechsel
   erneut gesucht werden muss. */
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

/* --- Layout stellen ---------------------------------------------------- */
Object.defineProperty(window.HTMLElement.prototype, "clientWidth", {
  get() { return this.classList?.contains("viz-chart") ? breite - 42 : breite; },
  configurable: true,
});
Object.defineProperty(window.HTMLElement.prototype, "clientHeight", {
  get() { return HOEHEN[this.id] ?? 340; },
  configurable: true,
});
Object.defineProperty(window.document.documentElement, "clientWidth", {
  get() { return breite; }, configurable: true,
});

/* --- CSS-Variablen beantworten ----------------------------------------- */
const stylequelle = html.slice(html.indexOf(".viz-root {"), html.indexOf("/* Dunkelmodus"));
const token = new Map();
for (const m of stylequelle.matchAll(/(--viz-[\w-]+)\s*:\s*([^;]+);/g)) {
  token.set(m[1], m[2].trim());
}
pruefe(token.size > 20, `[${name}] Nur ${token.size} Token gelesen — Stylesheet-Aufbau geändert?`);
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

/* --- Daten aus docs/data/ statt über fetch ------------------------------ */
const geladen = {};
for (const n of DATEN) {
  geladen[n] = JSON.parse(readFileSync(join(HIER, "data", `${n}.json`), "utf8"));
}
window.fetch = async (pfad) => {
  const schluessel = String(pfad).split("/").pop().replace(".json", "");
  if (!(schluessel in geladen)) return { ok: false, status: 404 };
  return { ok: true, status: 200, json: async () => geladen[schluessel] };
};

/* --- Realm-Falle, viertens ------------------------------------------
   ECharts prüft `replaceMerge` mit `val instanceof Array`. Das schlägt
   über Realm-Grenzen fehl: ein Array, das im jsdom-Fenster entsteht, ist
   NICHT `instanceof` des Node-Arrays. ECharts packt es dann in ein
   weiteres Array, und der Prüfschritt bekommt statt "series" ein Array
   zu sehen — Meldung „componentType.split is not a function".

   Im Browser gibt es dieses Problem nicht: dort liegen Seite und
   Bibliothek im selben Realm. Der Umweg unten ist deshalb reine
   Prüfmechanik und darf NICHT als Hinweis auf einen Fehler in den
   Diagrammdateien gelesen werden. `Array.from` erzeugt ein Array dieses
   Realms und stellt den Zustand her, den ein Browser ohnehin hätte. */
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

const konsolenfehler = [];
window.console = {
  ...console,
  error: (...a) => konsolenfehler.push(a.map(String).join(" ")),
  warn: (...a) => hinweise.push(`[${name}] ${a.map(String).join(" ")}`),
};

for (const datei of MODULE) {
  window.eval(readFileSync(join(HIER, "js", datei), "utf8"));
}

window.BIO.setzeWurzel(window.document.getElementById("dashboard"));
await window.BIO.start();

/* --- Erwartungen -------------------------------------------------------- */
const doc = window.document;
const t = (id) => doc.getElementById(id)?.textContent?.trim() ?? "";

pruefe(konsolenfehler.length === 0, `[${name}] Modulfehler: ${konsolenfehler.join(" | ")}`);

for (const kurz of ABSCHNITTE) {
  pruefe(doc.getElementById(`s-${kurz}`)?.style.display === "",
    `[${name}] Abschnitt s-${kurz} wurde nicht eingeblendet`);
  for (const praefix of ["u", "h"]) {
    pruefe(t(`${praefix}-${kurz}`).length > 0, `[${name}] ${praefix}-${kurz} ist leer`);
  }
}

/* Hinweiszeilen: 150–234 Zeichen laut Konvention. Kein harter Fehler —
   die Konvention ist eine Spanne, kein Gesetz. */
for (const kurz of ABSCHNITTE) {
  const laenge = t(`h-${kurz}`).length;
  if (laenge && (laenge < 150 || laenge > 234)) {
    hinweise.push(`[${name}] h-${kurz}: ${laenge} Zeichen (Konvention 150–234)`);
  }
}

/* Notizzeilen: nur dort Pflicht, wo ein Befund ausserhalb der Grafik steht. */
for (const kurz of ["vogel", "rotelisten", "erhaltung", "biotoptypen",
                    "wald", "biolandbau"]) {
  pruefe(t(`n-${kurz}`).length > 0, `[${name}] Notizzeile n-${kurz} ist leer`);
}

pruefe(doc.querySelectorAll(".viz-kpi").length === 8,
  `[${name}] ${doc.querySelectorAll(".viz-kpi").length} Kennzahlkacheln statt 8`);

pruefe(t("fuss").includes("Datenquellen"), `[${name}] Fuß ohne Quellenzeile`);
pruefe(doc.querySelector(".viz-signatur") !== null, `[${name}] Signaturzeile fehlt`);
pruefe(!t("fuss").includes("Gerade nicht verfügbar"),
  `[${name}] Fuß meldet Ausfälle: ${t("fuss").slice(-200)}`);

for (const kurz of ABSCHNITTE) {
  pruefe(doc.querySelectorAll(`#t-${kurz} tbody tr`).length > 0,
    `[${name}] Tabelle t-${kurz} ist leer`);
}
const rlZeilen = doc.querySelectorAll("#t-rotelisten tbody tr").length;
pruefe(rlZeilen === 23, `[${name}] Rote-Listen-Tabelle: ${rlZeilen} Zeilen statt 23`);
pruefe(t("n-rotelisten").includes("keine"),
  `[${name}] Notiz zu den Gruppen ohne Rote Liste fehlt`);

/* Die EU-Linie im Vogelabschnitt: zwei Serien statt einer, und die
   Legende muss beide benennen. Ohne sie wüsste niemand, welche Linie
   welche ist. */
const vogelFeld = doc.getElementById("c-vogel");
const vogelInstanz = echarts.getInstanceByDom(vogelFeld);
if (vogelInstanz) {
  const opt = vogelInstanz.getOption();
  pruefe(opt.series.length === 2,
    `[${name}] Vogelabschnitt hat ${opt.series.length} Serien statt 2 (EU-Linie fehlt?)`);
  const namen = opt.series.map((s) => s.name);
  pruefe(namen.includes("Österreich") && namen.includes("EU-27"),
    `[${name}] Serienbenennung im Vogelabschnitt: ${namen.join(", ")}`);
  /* connectNulls muss AUS sein — sonst zieht ECharts die AT-Linie durch
     Jahre, für die es keine Erhebung gibt. */
  pruefe(opt.series.every((s) => s.connectNulls !== true),
    `[${name}] Vogelabschnitt: connectNulls ist an, die Lücken werden überbrückt`);
}

/* Österreich muss in beiden Ländervergleichen vorkommen und hervorgehoben
   sein — sonst ist es eine Europagrafik ohne Österreichbezug. */
for (const [kurz, spalte] of [["wald", 0], ["biolandbau", 0]]) {
  const zellen = [...doc.querySelectorAll(`#t-${kurz} tbody tr td:nth-child(1)`)]
    .map((z) => z.textContent);
  pruefe(zellen.includes("Österreich"),
    `[${name}] ${kurz}: Österreich fehlt in der Tabelle`);
}

/* --- Aus dem SVG lesen, nicht schätzen ---------------------------------
   Die eigentliche Sichtprüfung: Wo steht der Text tatsächlich? */
for (const feldId of Object.keys(HOEHEN)) {
  const feld = doc.getElementById(feldId);
  if (!feld) { fehler.push(`[${name}] Feld ${feldId} fehlt im Markup`); continue; }
  const instanz = echarts.getInstanceByDom(feld);
  if (!instanz) { fehler.push(`[${name}] ${feldId} hat keine ECharts-Instanz`); continue; }
  const svg = instanz.renderToSVGString();

  const feldbreite = breite - 42;
  let raus = [];
  for (const m of svg.matchAll(/<text[^>]*\sx="(-?[\d.]+)"[^>]*>([^<]*)/g)) {
    const x = parseFloat(m[1]);
    if (x < -2 || x > feldbreite + 2) raus.push(`"${m[2]}" bei x=${x}`);
  }
  pruefe(raus.length === 0,
    `[${name}] ${feldId}: Text ausserhalb der Zeichenflaeche (0–${feldbreite}): ${raus.slice(0, 4).join(", ")}`);

  const pfade = (svg.match(/<path/g) || []).length;
  pruefe(pfade > 3, `[${name}] ${feldId}: nur ${pfade} Pfade — Grafik vermutlich leer`);
}

/* Platz je Zeile in der Rote-Listen-Grafik: 44 px Gitterrand, 46 px Legende. */
const zeilenhoehe = (HOEHEN["c-rotelisten"] - 44 - 46) / rlZeilen;
pruefe(zeilenhoehe >= 16,
  `[${name}] Rote Listen: nur ${zeilenhoehe.toFixed(1)} px je Zeile — Namen kleben`);

/* --- Ergebnis ----------------------------------------------------------- */
console.log("-".repeat(70));
console.log(`${name} (${breite} px)`);
if (hinweise.length) {
  for (const h of hinweise) console.log(`  · ${h}`);
}
if (fehler.length) {
  for (const f of fehler) console.log(`  ✗ ${f}`);
  process.exit(1);
}
console.log("  ✓ alles in Ordnung");
