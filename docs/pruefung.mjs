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

/* Drei Breiten, weil es ZWEI Schwellen gibt:
   - 768 (ENG): darunter stehen die Kategorienamen über dem Balken statt
     links daneben, und die Einordnung unter der Grafik ist eingeklappt.
   - 560 (SCHMAL): darunter zusätzlich Legende scrollbar und keine
     Endpunktbeschriftung.
   700 px prüft den Streifen dazwischen — dort gilt das eine, nicht das
   andere. Genau an solchen Schwellen sind im Schwesterprojekt vier Mal
   Fehler entstanden. */
const BREITEN = [
  { name: "Desktop", breite: 1100 },
  { name: "Tablet",  breite: 700 },
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
  "c-lebensraeume": 340,
  "c-biotoptypen": 300,
  "c-wald": 340,
  "c-biolandbau": 760,
  "c-falter": 340,
  "c-rueckkehrer": 300,
  "c-vogelarten": 644,
};

const MODULE = ["kern.js", "charts/kpi.js", "charts/schutzgebiete.js",
                "charts/vogel.js", "charts/boden.js", "charts/rotelisten.js",
                "charts/erhaltung.js", "charts/lebensraeume.js",
                "charts/biotoptypen.js",
                "charts/wald.js", "charts/totholz.js", "charts/fichte.js",
                "charts/baumarten.js", "charts/waldarten.js",
                "charts/natura2000.js",
                "charts/biolandbau.js",
                "charts/falter.js", "charts/rueckkehrer.js",
                "charts/vogelarten.js"];

const DATEN = ["meta", "kpi", "schutzgebiete", "vogel", "boden", "rotelisten",
               "erhaltung", "lebensraeume", "biotoptypen", "wald",
               "totholz", "totholz_geo",
               "fichte", "baumarten", "waldarten", "natura2000", "biolandbau",
               "falter", "rueckkehrer", "vogelarten"];

const ABSCHNITTE = ["schutzgebiete", "vogel", "boden", "rotelisten",
                    "erhaltung", "lebensraeume", "biotoptypen", "wald",
                    "totholz", "fichte",
                    "baumarten", "waldarten", "natura2000",
                    "biolandbau",
                    "falter", "rueckkehrer", "vogelarten"];

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
/* Eine per JavaScript gesetzte Hoehe MUSS gewinnen: `balkenHoehe()` in
   kern.js setzt `style.height` eng aus der Zahl der Kategorien, und
   ECharts liest danach `clientHeight`. Gibt die Pruefung stur den
   CSS-Wert zurueck, misst sie ein Layout, das es nicht gibt. */
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
/* `baumarten`, `waldarten` und `natura2000` stehen hier, weil ihr
   eigentlicher Befund AUSSERHALB der Grafik liegt: der Nennerwechsel der
   Waldinventur, die Gegenprobe an den Moosen, und die Regel, die aus
   93 % Fläche eine 28-%-Bewertung macht. Fehlt die Notiz, sieht jeder
   der drei Abschnitte aus wie ein Datenfehler. */
/* `lebensraeume` gehört aus demselben Grund dazu: Der Balken zeigt die
   Rangfolge, aber nicht, dass die zwei günstigen Grünlandwerte im
   Hochgebirge liegen, dass „unbekannt" bei den Gewässern eine
   Wissenslücke ist und keine gute Lage, und dass alle echten
   Verbesserungen im Wald liegen. Ohne Notiz fehlt der halbe Befund. */
for (const kurz of ["vogel", "rotelisten", "erhaltung", "lebensraeume",
                    "biotoptypen", "wald", "biolandbau",
                    "baumarten", "waldarten", "natura2000"]) {
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
/* --- Überschrift gegen die Daten lesen --------------------------------
   „Zwei von 24 Grünland-Bewertungen sind gut, im Wald neun von 32" nennt
   vier Zahlen, die im HTML fest stehen. Beim nächsten Berichtszyklus
   ändern sie sich, und eine feste Überschrift altert dann STILL — die
   Grafik zeigt neue Werte, die Zeile darüber die alten. Genau dieser
   Fehler ist im Schwesterprojekt schon vorgekommen.

   Geprüft wird gegen die JSON, nicht gegen Konstanten: Ein Sollwert aus
   derselben Quelle wie die Daten könnte den Fehler nicht finden. */
{
  const d = JSON.parse(readFileSync(join(HIER, "data", "lebensraeume.json"), "utf8"));
  const gr = d.gruppen.find((g) => g.gruppe_quelle === "Grasslands");
  const wa = d.gruppen.find((g) => g.gruppe_quelle === "Forests");
  const h2 = doc.querySelector("#s-lebensraeume h2")?.textContent ?? "";
  const WORT = ["null", "eine", "zwei", "drei", "vier", "fünf", "sechs",
                "sieben", "acht", "neun", "zehn", "elf", "zwölf"];
  /* Jede Zahl darf als Ziffer ODER als Wort dastehen — die Überschrift
     schreibt kleine Zahlen aus, große nicht. */
  const steht = (n) => {
    const wort = WORT[n];
    return new RegExp(`\\b${n}\\b`).test(h2)
        || (wort && new RegExp(wort, "i").test(h2));
  };
  for (const [n, was] of [
    [gr.anzahl[0], "günstige Grünland-Bewertungen"],
    [gr.bewertungen, "Grünland-Bewertungen gesamt"],
    [wa.anzahl[0], "günstige Wald-Bewertungen"],
    [wa.bewertungen, "Wald-Bewertungen gesamt"],
  ]) {
    pruefe(steht(n),
      `[${name}] Überschrift s-lebensraeume nennt ${was} nicht mehr ` +
      `(${n} laut Daten): „${h2}"`);
  }
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

/* --- Kategorienamen über dem Balken (< 768 px) ------------------------
   Gemessen, nicht geglaubt: in den fünf liegenden Balkendiagrammen wird
   aus dem SVG gelesen, wo der Kategoriename steht. Erwartet wird eng:
   - der Name beginnt INNERHALB der Zeichenfläche, nicht links davor
     (x >= 0 — links neben dem Gitter wären es negative Werte),
   - er steht ÜBER seinem Balken, nicht darin: die Textmitte liegt über
     der Oberkante des zugehörigen Balkenrechtecks.
   Weit gilt das Gegenteil: der Name steht links vom Gitter. */
const BALKENFELDER = ["c-rotelisten", "c-erhaltung", "c-biotoptypen",
                      "c-wald", "c-biolandbau"];
for (const feldId of BALKENFELDER) {
  const instanz = echarts.getInstanceByDom(doc.getElementById(feldId));
  if (!instanz) continue;
  const svg = instanz.renderToSVGString();
  const opt = instanz.getOption();
  const kategorien = (opt.yAxis?.[0]?.data || []).map(String);
  if (!kategorien.length) { hinweise.push(`[${name}] ${feldId}: keine Kategorien gelesen`); continue; }

  /* Textknoten einsammeln. ECharts setzt die Lage im SVG NICHT über
     x/y-Attribute allein, sondern über `transform="translate(x y)"` plus
     ein y-Attribut als Versatz. Wer nur x/y liest, findet nichts —
     genau das ist beim ersten Anlauf passiert. */
  const texte = [...svg.matchAll(/<text([^>]*)>([^<]*)</g)].map((m) => {
    const attr = m[1];
    const tr = /transform="translate\((-?[\d.]+)[ ,]+(-?[\d.]+)\)"/.exec(attr);
    const yAttr = /\sy="(-?[\d.]+)"/.exec(attr);
    const xAttr = /\sx="(-?[\d.]+)"/.exec(attr);
    return {
      x: (tr ? +tr[1] : 0) + (xAttr ? +xAttr[1] : 0),
      y: (tr ? +tr[2] : 0) + (yAttr ? +yAttr[1] : 0),
      versatz: yAttr ? +yAttr[1] : 0,
      anker: (/text-anchor="(\w+)"/.exec(attr) || [, "start"])[1],
      wort: m[2].trim(),
    };
  });
  const treffer = kategorien
    .map((k) => texte.find((t) => t.wort === k || (k.length > 8 && t.wort.startsWith(k.slice(0, 8)))))
    .filter(Boolean);
  if (treffer.length < 2) { hinweise.push(`[${name}] ${feldId}: nur ${treffer.length} Kategorienamen im SVG gefunden`); continue; }

  const linkeste = Math.min(...treffer.map((t) => t.x));
  if (breite < 768) {
    pruefe(linkeste >= 0,
      `[${name}] ${feldId}: Kategoriename beginnt bei x=${linkeste} — steht noch links vom Gitter statt über dem Balken`);
    /* Zwei Abstände, und der ZWEITE ist der, an dem der erste Anlauf am
       25.08. gescheitert ist: der Name kollidiert nicht mit seinem
       eigenen Balken, sondern mit dem der Zeile DARÜBER. Eine Prüfung,
       die nur den eigenen misst, meldet „in Ordnung", während die Seite
       unlesbar ist. Beide werden hier gemessen.

       Gerechnet wird aus den tatsächlichen y-Werten der Namen: ihr
       Abstand IST die Zeilenhöhe, die muss nicht geschätzt werden.
       Die Textmitte liegt bei y, die Ober-/Unterkante ±6 (Schriftgröße
       12). Der Balken ist BAR_ENG = 14 hoch und sitzt mittig auf der
       Zeile, reicht also 7 px über deren Mitte. */
    const HALBER_BALKEN = 7;      /* BAR_ENG / 2 in kern.js */
    const HALBER_TEXT = 6;
    const sortiert = [...treffer].sort((a, b) => a.y - b.y);
    const mitte = (tf) => tf.y - tf.versatz;   /* Mitte der Kategoriezeile */

    const eigene = sortiert.map((tf) => (mitte(tf) - HALBER_BALKEN) - (tf.y + HALBER_TEXT));
    pruefe(Math.min(...eigene) > 0,
      `[${name}] ${feldId}: Name sitzt IM eigenen Balken (${Math.min(...eigene).toFixed(1)} px)`);

    const darueber = sortiert.slice(1).map((tf, i) =>
      (tf.y - HALBER_TEXT) - (mitte(sortiert[i]) + HALBER_BALKEN));
    if (darueber.length) {
      const engste = Math.min(...darueber);
      pruefe(engste > 0,
        `[${name}] ${feldId}: Name überschneidet den Balken der Zeile DARÜBER um ${(-engste).toFixed(1)} px — Zeile ${(mitte(sortiert[1]) - mitte(sortiert[0])).toFixed(1)} px`);
    }
  } else {
    /* Weit hängen die Namen mit ihrem RECHTEN Rand am Gitter
       (text-anchor="end") und laufen nach links aus dem Gitter heraus.
       Der x-Wert ist dann der Ankerpunkt, nicht der Textanfang — er
       liegt naturgemäß bei 106–156 px. Geprüft wird deshalb die
       Ausrichtung, nicht die Zahl. */
    const falsch = treffer.filter((tf) => tf.anker !== "end");
    pruefe(falsch.length === 0,
      `[${name}] ${feldId}: ${falsch.length} Kategorienamen linksbündig — weit gehören sie rechtsbündig ans Gitter`);
    pruefe(treffer.every((tf) => Math.abs(tf.versatz) < 8),
      `[${name}] ${feldId}: Kategoriename um ${treffer[0].versatz} px nach oben versetzt — weit gehört er auf die Balkenmitte`);
  }
}

/* --- Einordnung: eingeklappt oder nicht -------------------------------- */
const aufklapper = doc.querySelectorAll(".viz-mehr");
pruefe(aufklapper.length === ABSCHNITTE.length,
  `[${name}] ${aufklapper.length} Aufklapper statt ${ABSCHNITTE.length} — wurde ein Absatz nicht eingesammelt?`);
for (const d of aufklapper) {
  pruefe(d.querySelector("summary")?.textContent === "Einordnung",
    `[${name}] Aufklapper ohne Zusammenfassungszeile`);
  pruefe(d.querySelectorAll(":scope > p").length > 0,
    `[${name}] Aufklapper ohne Inhalt`);
  /* Ohne matchMedia entscheidet in jsdom die Dokumentbreite. */
  pruefe(d.open === (breite >= 768),
    `[${name}] Aufklapper ist ${d.open ? "offen" : "zu"} — bei ${breite} px erwartet: ${breite >= 768 ? "offen" : "zu"}`);
}
/* Der Text muss im Dokument bleiben, auch wenn er zu ist — sonst ist die
   Einordnung für Suchmaschinen weg. */
for (const kurz of ABSCHNITTE) {
  pruefe(t(`h-${kurz}`).length > 0,
    `[${name}] h-${kurz} ist nach dem Einklappen leer`);
}

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
