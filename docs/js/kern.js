/* ===========================================================================
   Biodiversitäts-Dashboard Österreich — Kern
   ---------------------------------------------------------------------------
   Gemeinsame Helfer, Laden der Daten und Seitenaufbau. Wird von index.html
   als ERSTES Skript geladen; die Diagramme selbst stecken in je einer Datei
   unter js/charts/ und hängen sich an window.BIO an.

   Ladereihenfolge (defer hält sie ein): kern.js -> js/charts/*.js.
   start() läuft erst nach DOMContentLoaded, dann sind alle Bausteine da.

   Farben kommen ausschließlich aus CSS-Variablen (--viz-*). In Oxygen 6
   überschreibst du die Variablen im Stylesheet, die Diagramme ziehen nach.

   Herkunft: übernommen aus arbeitsmarkt-at/docs/js/kern.js. Die Helfer für
   schmale Fenster, das Hover-Abdunkeln und die Neuvermessung nach dem
   Schriftladen sind dort teuer erarbeitet worden und stehen hier
   unverändert — wer sie „aufräumt", tritt dieselben Fallen noch einmal.
   Ausgelassen: Kartenlayout (dieses Dashboard hat noch keine Karte) und
   der Einbettungscode.
   =========================================================================== */
(function (global) {
"use strict";

/* =====================================================================
   KONFIGURATION — hier die eigene Adresse eintragen
   ===================================================================== */
let DATEN_BASIS = "./data";   // In Oxygen: "https://DEIN-GITHUB-NAME.github.io/biodiversitaet-at/data"

/* --- Ausgabestand ----------------------------------------------------
   EINZIGE Quelle für die Fußzeilen-Signatur. index.html und die
   WordPress-Seite lesen beide diese Datei, also steht die Nummer nur
   hier — nicht im Markup.

   Was die Nummer zählt: sichtbare Ausgaben. Hochzählen, wenn sich für
   Besucher etwas ändert (neues Diagramm, neue Darstellung, neuer
   Abschnitt). NICHT hochzählen bei der Datenaktualisierung (die zeigt
   `stand_daten` aus meta.json) und nicht bei reinen Fehlerbehebungen —
   dafür ist die `?v=NN`-Cacheziffer in index.html zuständig, die eine
   andere Zählung führt. */
const VERSION = {
  nummer:     "10",                   // 08 Waldarten, 09 Natura 2000, 10 Fließgewässer (07 Baumarten)
  datum:      "2026-09-03",           // maschinenlesbar, für <time datetime>
  datum_text: "3. September 2026",    // sichtbar
  changelog:  "https://biodiversitaet-monitor.at/changelog/",
};

/* --- Hilfsmittel ------------------------------------------------------
   wurzel ist das Element, von dem ALLE Farb- und Größentoken gelesen
   werden. Es darf nie null werden: stil() läuft in jedem Diagrammmodul
   als Erstes, ein null hier legt also das ganze Dashboard lahm.
   Siehe setzeWurzel() weiter unten. */
let wurzel = document.getElementById("dashboard") || document.body;
const stil   = (name) => getComputedStyle(wurzel).getPropertyValue(name).trim();

/* --- Typografie ------------------------------------------------------
   ECharts erbt NICHTS aus dem CSS: Diagrammtext wird von der Bibliothek
   selbst gesetzt und dabei über eine Canvas-Messung ausgemessen. Darum
   werden Schriftgrößen hier aus den CSS-Variablen geholt und in die
   Option gegeben, statt sie per CSS zu setzen.

   Wichtig: Diagrammtext NIE über CSS-Selektoren stylen — auch nicht beim
   SVG-Renderer, wo der Text als <text> im DOM steht. ECharts misst die
   Breiten weiter über Canvas; ein CSS-Override verschiebt Achsenlabels
   und schneidet lange Gruppennamen falsch ab.

   Der zweite Parameter ist der Rückfallwert. Fehlt ein Token — etwa weil
   in Oxygen nur die Farben überschrieben wurden — bleibt die bisherige
   Größe stehen, statt dass ECharts NaN bekommt. */
const px = (name, standard) => parseFloat(stil(name)) || standard;
const schrift = () => ({
  familie: stil("--viz-font") || "system-ui, sans-serif",
  achse:   px("--viz-fs-achse", 11),      // Achsenbeschriftung, visualMap
  label:   px("--viz-fs-label", 11.5),    // Werte am Balken- oder Punktende
  serie:   px("--viz-fs-serie", 12),      // Kategorienamen, Legende
  tooltip: px("--viz-fs-tooltip", 12.5),
  eng:     px("--viz-fs-eng", 10.5),      // 27 Gruppennamen auf einer Achse
});
const zahl   = (n) => (n === null || n === undefined) ? "–" : n.toLocaleString("de-AT");
/* Prozent- und Kommawerte immer mit deutschem Dezimalkomma */
const pz     = (n, stellen = 1) => (n === null || n === undefined) ? "–"
  : n.toLocaleString("de-AT", { minimumFractionDigits: stellen, maximumFractionDigits: stellen });
const monat  = (s) => new Date(s).toLocaleDateString("de-AT", { month: "long", year: "numeric" });
const datum  = (s) => new Date(s).toLocaleDateString("de-AT");

async function hole(name) {
  /* cache: "no-cache" erzwingt eine Rückfrage beim Server. Ohne das zeigt
     der Browser nach der Aktualisierung wochenlang alte Zahlen — und
     einmal als fehlend gemerkte Dateien bleiben fehlend. Die Antwort ist
     bei unveränderten Daten ein 304, kostet also fast nichts. */
  const antwort = await fetch(`${DATEN_BASIS}/${name}.json`, { cache: "no-cache" });
  if (!antwort.ok) throw new Error(`${name}.json konnte nicht geladen werden (HTTP ${antwort.status})`);
  return antwort.json();
}

/* Gemeinsames ECharts-Grundgerüst: dünne Marken, zurückhaltendes Raster,
   Text in Textfarben statt in Serienfarben. */
function basis() {
  const s = schrift();
  return {
    textStyle: { fontFamily: s.familie, fontSize: s.serie, color: stil("--viz-text-2") },
    grid: { left: 8, right: 20, top: 18, bottom: 8, containLabel: true },
    tooltip: {
      backgroundColor: stil("--viz-surface"),
      borderColor: stil("--viz-border"),
      borderWidth: 1,
      padding: [9, 12],
      textStyle: { color: stil("--viz-text"), fontSize: s.tooltip },
      /* Ohne `confine` positioniert ECharts den Tooltip frei am Zeiger und
         laesst ihn ueber die Zeichenflaeche hinauslaufen — auf dem Handy
         landete er links ausserhalb des Bildes. `confine` haelt ihn im
         Container; die Breitengrenze verhindert, dass eine lange Zeile
         den Container selbst sprengt. */
      confine: true,
      /* Der Schatten war auf 10 % Schwarz gerechnet — auf dunklem Grund
         ist das nichts. Er trägt jetzt so viel, dass der Tooltip sich
         auch über der eigenen Grafik abhebt. --viz-surface bleibt
         deshalb deckend, siehe CSS-Abschnitt 45.1. */
      extraCssText: "box-shadow:0 8px 28px rgba(0,0,0,.45);border-radius:"
        + (stil("--viz-radius-s") || "8px") + ";"
        + "max-width:min(300px,80vw);white-space:normal;",
    },
  };
}
const achse = () => ({
  axisLine:  { lineStyle: { color: stil("--viz-axis"), width: 1 } },
  axisTick:  { show: false },
  axisLabel: { color: stil("--viz-muted"), fontSize: schrift().achse, hideOverlap: true },
  splitLine: { lineStyle: { color: stil("--viz-grid"), width: 1, type: "solid" } },
});

/* --- Schmale Fenster -------------------------------------------------
   ECharts kennt keine Media Queries. Die Option wird EINMAL gebaut,
   `resize()` skaliert sie danach nur noch — Gitterabstaende in Pixeln,
   Legenden und Endbeschriftungen bleiben, wie sie beim Bau waren. Genau
   daher kommen die zusammengeschobenen Achsenzahlen auf dem Handy.

   Diese Helfer liefern breitenabhaengige Werte, und `start()` baut die
   Diagramme neu, sobald die Schwelle ueberschritten wird.

   560 px: darunter reicht die Breite fuer die Desktop-Gitter der
   liegenden Balken nicht mehr (links allein 172 px fuer die
   Kategorienamen, rechts 72 px fuer die Werte — bei 350 px Fenster
   bleiben 106 px Zeichenflaeche). */
const SCHMAL = 560;

/* 768 px: die zweite, hoehere Schwelle — ab hier stehen die
   Kategorienamen der liegenden Balken NICHT mehr links neben dem
   Gitter, sondern ueber dem jeweiligen Balken. Grund: links kosten sie
   je nach Diagramm 118–168 px, und ein Name wie „von Vernichtung
   bedroht" bricht dort auf drei Zeilen um, waehrend dem Balken selbst
   ein Drittel der Karte bleibt. Ueber dem Balken steht die ganze
   Kartenbreite zur Verfuegung, und der Balken bekommt sie auch.

   Die Schwelle liegt bewusst ueber SCHMAL: zwischen 560 und 768 px
   bleiben Legende und Endbeschriftung wie am Desktop, nur die
   Kategorienamen wandern nach oben. */
const ENG = 768;
const feldBreite = (el) =>
  el?.clientWidth || document.documentElement.clientWidth;
const istSchmal = (el) => feldBreite(el) < SCHMAL;
const istEng = (el) => feldBreite(el) < ENG;

/* Zeilenhoehe der Kategorienamen und Mindestrand rechts.

   RAND_RECHTS: Am rechten Gitterrand stehen ZWEI Dinge, die ECharts beim
   Layout nicht mitrechnet — die Wertbeschriftung des laengsten Balkens
   (`position: "right"`, Abstand 8) und die HAELFTE der letzten
   Achsenzahl, die mittig ueber dem Gitterende sitzt. */
const ZEILE = 16;
const RAND_RECHTS = 60;

/* Eng gerechnet in PIXELN, nicht in Prozent der Kategoriezeile.

   Der erste Anlauf (Balken = halbe Zeile, Name in der anderen Haelfte)
   war falsch, und zwar auf eine Art, die eine Pruefung leicht uebersieht:
   der Name kollidiert nicht mit SEINEM Balken, sondern mit dem der Zeile
   DARUEBER. Bei 23 Tiergruppen auf 690 px sind das 30 px je Zeile —
   16 px Text plus 15 px Balken passen da nicht hinein, egal wie man den
   Text darin verschiebt.

   Deshalb steht die Zeilenhoehe eng FEST, und die Kartenhoehe richtet
   sich danach (siehe `balkenHoehe`), statt umgekehrt:
     40 px Zeile = 16 Text + 4 Luft + 14 Balken + 6 Luft nach unten.
   Wer ROW_ENG senkt, muss BAR_ENG mitsenken — sonst kleben die Namen
   wieder an den Balken der Zeile darueber. */
const ROW_ENG = 40;
const BAR_ENG = 14;

/* Zweite Stufe fuer Diagramme mit WENIGEN Zeilen.

   Die 14 px oben sind aus dem dichtesten Fall gerechnet (23 Tiergruppen
   auf 690 px). Bei zwei bis vier Zeilen ist das unnoetig duenn: dort ist
   Platz da, der Balken nutzt ihn nur nicht. Gemessen am 31.08.2026 auf
   1024 px — Zeichenflaeche 659 px, also eng — standen Fliessgewaesser,
   Natura 2000, Waldarten und Baumarten alle auf 14 px.

   Zeile und Balken muessen zusammen wachsen, sonst klebt der Name am
   Balken der Zeile darueber (dieselbe Falle wie bei ROW_ENG):
     60 px Zeile = 16 Text + 6 Luft + 28 Balken + 10 Luft nach unten.

   `anzahl` ist die Zahl der Kategoriezeilen. Fehlt sie, bleibt es bei
   der dichten Stufe — ein Modul, das sie nicht uebergibt, wird also
   nicht ueberraschend breiter. */
const ROW_ENG_WEIT = 60;
const BAR_ENG_WEIT = 28;
const WENIG_ZEILEN = 4;

const engStufe = (anzahl) => (anzahl > 0 && anzahl <= WENIG_ZEILEN)
  ? { zeile: ROW_ENG_WEIT, balken: BAR_ENG_WEIT }
  : { zeile: ROW_ENG,      balken: BAR_ENG };

const balkenBreite = (el, desktop, anzahl) =>
  istEng(el) ? engStufe(anzahl).balken : desktop;

/* Kartenhoehe eng aus der Zahl der Kategorien setzen.

   Warum ueberhaupt: die Hoehe der Zeichenflaeche steht im CSS und ist
   fuer das Desktop-Layout gerechnet, in dem der Name NEBEN dem Balken
   steht und keine eigene Zeile braucht. Ueber dem Balken braucht er
   eine — die Karte muss also eng hoeher werden, sonst schiebt ECharts
   die Zeilen einfach enger zusammen.

   `obenExtra` ist der Platz, den das Modul ueber dem Gitter zusaetzlich
   belegt (Legende): grid.top minus die 10 px des Standardgitters.

   Wird die Schwelle nach oben ueberschritten, wird die gesetzte Hoehe
   wieder ENTFERNT statt auf einen Desktopwert gesetzt — die richtige
   Zahl steht im CSS, nicht hier. */
function balkenHoehe(d, el, anzahl, obenExtra = 0) {
  if (!el) return;
  if (!istEng(el)) {
    if (el.dataset.hoeheGesetzt) {
      el.style.height = "";
      delete el.dataset.hoeheGesetzt;
      d?.resize?.();
    }
    return;
  }
  const soll = Math.round(anzahl * engStufe(anzahl).zeile + 44 + obenExtra);
  if (parseFloat(el.style.height) === soll) return;
  el.style.height = `${soll}px`;
  el.dataset.hoeheGesetzt = "1";
  d?.resize?.();   /* ECharts misst nur beim Aufbau und bei resize() */
}

/* Anteil der Breite, den die Kategorienamen hoechstens belegen duerfen.
   Darueber bleibt zu wenig Zeichenflaeche fuer die Balken. */
const ANTEIL_LINKS = 0.34;

/* Linker Gitterrand fuer liegende Balken. Desktop: der feste Pixelwert
   aus der Diagrammdatei, damit die Kategorienamen aller Diagramme in
   einer Flucht stehen — aber gedeckelt, sobald die Zeichenflaeche
   schmaler wird. */
const randLinks = (el, desktopLinks = 120) => istSchmal(el)
  ? Math.round(feldBreite(el) * 0.32)
  : Math.min(desktopLinks, Math.round(feldBreite(el) * ANTEIL_LINKS));

/* Gitter fuer liegende Balken.

   Eng (< 768): die Kategorienamen stehen IM Gitter ueber den Balken,
   also darf links kein Platz mehr fuer sie reserviert werden —
   `containLabel: false`, sonst rechnet ECharts die nun sehr breiten
   Etiketten in den linken Rand hinein und schiebt das Gitter aus der
   Karte. Die 14 px links sind kein Platz fuer Text, sondern die Haelfte
   der ersten Achsenzahl („0"), die mittig ueber dem Gitteranfang
   sitzt. */
const balkenGitter = (el, desktop) => istEng(el)
  ? { left: 14, right: RAND_RECHTS, top: 10, bottom: 34, containLabel: false }
  : { top: 10, bottom: 34, ...desktop,
      left: randLinks(el, desktop?.left),
      right: Math.max(RAND_RECHTS, desktop?.right ?? RAND_RECHTS) };

/* --- Hover an Balken: dunkler, nicht heller -------------------------------
   ECharts hellt einen Balken beim Hover per Default auf (lift +10 %). Bei
   hellen Grautoenen wie --viz-grid (#ececec) landet er damit fast auf Weiss
   und verschwindet vor dem Hintergrund. Umgekehrt ist richtig: der
   angefasste Balken tritt hervor. */
const HOVER_ANTEIL = 0.22;
function dunkler(farbe, anteil = HOVER_ANTEIL) {
  const h = String(farbe).trim();
  const kurz = /^#([0-9a-f])([0-9a-f])([0-9a-f])$/i.exec(h);
  const lang = /^#([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})$/i.exec(h);
  let rgb;
  if (lang)      rgb = [1, 2, 3].map((i) => parseInt(lang[i], 16));
  else if (kurz) rgb = [1, 2, 3].map((i) => parseInt(kurz[i] + kurz[i], 16));
  else {
    const m = /^rgba?\(([^)]+)\)/i.exec(h);
    if (!m) return farbe;                    /* unbekanntes Format: unveraendert */
    const t = m[1].split(",").map((s) => parseFloat(s));
    rgb = t.slice(0, 3).map((v) => (isFinite(v) ? v : 0));
    const a = t[3];
    const d = rgb.map((v) => Math.round(Math.max(0, v * (1 - anteil))));
    return a === undefined ? `rgb(${d.join(",")})` : `rgba(${d.join(",")},${a})`;
  }
  return "#" + rgb
    .map((v) => Math.round(Math.max(0, v * (1 - anteil))).toString(16).padStart(2, "0"))
    .join("");
}
/* Gegenstück zu dunkler(): dieselbe Formel, nur zum Weiß hin. */
function heller(farbe, anteil = HOVER_ANTEIL) {
  const h = String(farbe).trim();
  const kurz = /^#([0-9a-f])([0-9a-f])([0-9a-f])$/i.exec(h);
  const lang = /^#([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})$/i.exec(h);
  const auf = (v) => Math.round(v + (255 - v) * anteil);
  let rgb;
  if (lang)      rgb = [1, 2, 3].map((i) => parseInt(lang[i], 16));
  else if (kurz) rgb = [1, 2, 3].map((i) => parseInt(kurz[i] + kurz[i], 16));
  else {
    const m = /^rgba?\(([^)]+)\)/i.exec(h);
    if (!m) return farbe;
    const t = m[1].split(",").map((s) => parseFloat(s));
    rgb = t.slice(0, 3).map((v) => (isFinite(v) ? v : 0));
    const a = t[3];
    const d = rgb.map(auf);
    return a === undefined ? `rgb(${d.join(",")})` : `rgba(${d.join(",")},${a})`;
  }
  return "#" + rgb.map((v) => auf(v).toString(16).padStart(2, "0")).join("");
}

/* --- Hover: IMMER vom Grund weg, nie zum Grund hin ---------------------
   Der ursprüngliche hoverDunkler() ging fest nach Dunkel. Das war
   richtig, solange die Karte weiß war. Seit die Seite dunkel ist, wandert
   ein angefasster Balken damit auf den Grund zu und verschwindet — genau
   der Fehler, den die Funktion verhindern sollte, nur spiegelverkehrt.

   Ob der Grund dunkel ist, wird nicht geraten, sondern an der Textfarbe
   abgelesen: helle Schrift heißt dunkler Grund. Das gilt auch dann, wenn
   die Farbe über eine Systemeinstellung oder einen späteren CSS-Abschnitt
   kippt — es wird bei jedem Aufruf neu gelesen, nicht einmal beim Laden. */
function grundIstDunkel() {
  const m = /(\d+(?:\.\d+)?)[,\s]+(\d+(?:\.\d+)?)[,\s]+(\d+(?:\.\d+)?)/
    .exec(getComputedStyle(wurzel).color || "");
  if (!m) return false;
  const [r, g, b] = [1, 2, 3].map((i) => parseFloat(m[i]) / 255);
  const k = (c) => (c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4);
  return 0.2126 * k(r) + 0.7152 * k(g) + 0.0722 * k(b) > 0.5;
}
const hervor = (farbe) => (grundIstDunkel() ? heller(farbe) : dunkler(farbe));
/* Name bleibt, damit keines der neun Diagrammmodule angefasst werden muss. */
const hoverDunkler = (farbe) => ({ itemStyle: { color: hervor(farbe) } });

/* Kategorienamen links hart begrenzen. `anzahl` ist die Zahl der
   Kategorien: Passen zwei Textzeilen nicht in die Hoehe einer
   Kategoriezeile, wird gekuerzt statt umgebrochen. Ohne das kleben bei
   27 Tiergruppen die zweizeiligen Namen ineinander. */
function kategorieLabel(el, desktopLinks = 120, anzahl = 0, balkenPx = null) {
  /* Eng: der Name steht ueber seinem Balken statt links daneben.

     Wie das geht: `margin: 0` setzt den Ankerpunkt auf die Achslinie
     statt links davor, `align: "left"` laesst den Text von dort nach
     RECHTS ins Gitter laufen. `verticalAlign: "bottom"` legt die
     Unterkante des Textes auf die Mitte der Kategoriezeile; die
     Polsterung unten hebt ihn von dort um die halbe Balkenhoehe plus
     4 px an, also knapp ueber den Balken.

     Die halbe Balkenhoehe ist keine Schaetzung, sondern dieselbe Zahl,
     die `balkenBreite()` als `barWidth` an die Module gibt — seit der
     Staffelung vom 31.08.2026 also `engStufe(anzahl).balken`, nicht mehr
     die feste Konstante. Beide Seiten haengen an derselben Stufe; wer nur
     eine aendert, schiebt den Namen in den Balken.

     `balkenPx` ist der Ausweg fuer Module, die ihre Balkenhoehe eng SELBST
     setzen statt sie von `balkenBreite()` zu holen — bisher nur
     rueckkehrer.js mit zwei Gruppen je Kategorie. */
  if (istEng(el)) {
    return {
      align: "left",
      verticalAlign: "bottom",
      margin: 0,
      padding: [0, 0, (balkenPx ?? engStufe(anzahl).balken) / 2 + 4, 0],
      width: Math.max(120, feldBreite(el) - 14 - RAND_RECHTS),
      overflow: "truncate",
      lineHeight: ZEILE,
    };
  }
  const links = randLinks(el, desktopLinks);
  /* 44 px sind oberer (10) + unterer (34) Gitterrand. */
  const platz = anzahl > 0 ? ((el?.clientHeight || 300) - 44) / anzahl : 999;
  const zweiZeilen = platz >= 2 * ZEILE;
  /* Hier stand bis 26.08.2026 ein `return {}` fuer den Fall, dass der
     volle Desktop-Rand da ist und zwei Zeilen hineinpassen. Das war die
     Ursache eines still abgeschnittenen Namens: OHNE `width` bricht
     ECharts weder um noch kuerzt es mit „…" — es zeichnet den Text
     einfach ueber den linken Rand der Zeichenflaeche hinaus, wo er
     abgeschnitten wird. Ein zu langer Name sah damit nicht falsch aus,
     sondern nur seltsam formuliert.
     Jetzt gilt die Begrenzung IMMER. Wo der Name in den reservierten
     Rand passt — der Normalfall — aendert das nichts; wo er nicht
     passt, bricht er um, statt zu verschwinden. */
  return {
    width: Math.max(56, links - 16),   /* 12 px `margin` + Luft fuer „…" */
    overflow: zweiZeilen ? "break" : "truncate",
    lineHeight: ZEILE,
  };
}

/* Legende schmal: scrollbar in EINER Zeile statt ueber drei Zeilen ins
   Diagramm zu laufen. */
const legende = (el, werte) => istSchmal(el)
  ? { ...werte, type: "scroll", itemGap: 10 }
  : werte;

/* Linke Kante der Legende — dieselbe wie die des Gitters.

   Die Module hatten den Desktop-Wert ihres Gitters fest eingetragen
   (96, 130, 150, 168 …) und nur schmal auf 0 geschaltet. Dazwischen,
   also zwischen 560 und 768 px, stimmte es nicht mehr: eng faellt
   `grid.left` auf 14 (die Kategorienamen stehen dann UEBER dem Balken),
   die Legende blieb aber auf ihrem Desktop-Wert stehen und schwebte
   weit rechts neben den Balken. Befund des Users am 31.08.2026 bei
   1024 px Fensterbreite, Zeichenflaeche 659 px.

   Deshalb rechnet die Kante jetzt aus derselben Quelle wie das Gitter:
   eng die 14 px aus `balkenGitter`, sonst `randLinks` — also inklusive
   der Deckelung, die bei mittleren Breiten greift. Wer `balkenGitter`
   aendert, muss hier mit. */
const legendeLinks = (el, desktopLinks) =>
  istEng(el) ? 14 : randLinks(el, desktopLinks);

/* Endpunktbeschriftung rechts kostet Breite, die schmal nicht da ist. */
const endLabelZeigen = (el) => !istSchmal(el);

/* Ruft `neuBauen` auf, sobald die Seite die Schwelle wechselt — nicht bei
   jedem Pixel. Entprellt, weil ein Fensterzug Dutzende Ereignisse wirft.
   Verglichen wird eine grobe Stufe von 160 px; das loest beim Umschlagen
   des Layouts aus, aber nicht bei jedem Zug am Fenster. */
const STUFE = 160;
const breitenStufe = (el) =>
  istSchmal(el) ? -2
    : istEng(el) ? -1        /* eigene Stufe: 768 faellt sonst mitten in
                                die 160er-Stufe 640–800 und der Wechsel
                                der Kategorienamen loeste nie aus */
    : Math.floor(feldBreite(el) / STUFE);

function beiBreitenwechsel(neuBauen) {
  let warStufe = breitenStufe(document.getElementById("c-schutzgebiete"));
  let timer = null;
  global.addEventListener("resize", () => {
    clearTimeout(timer);
    timer = setTimeout(() => {
      const jetzt = breitenStufe(document.getElementById("c-schutzgebiete"));
      if (jetzt === warStufe) return;
      warStufe = jetzt;
      neuBauen();
    }, 200);
  });
}

/* --- Neuvermessung nach dem Laden der Schrift ------------------------
   ECharts misst und zeichnet EINMAL beim Aufbau und rendert danach nie
   von selbst neu. Ist Figtree zu diesem Zeitpunkt noch nicht geladen,
   bleibt der gesamte Diagrammtext dauerhaft in der Ersatzschrift stehen —
   während die Seite ringsum bereits richtig aussieht.

   resize() stößt eine vollständige Neuvermessung an. Der Aufruf ist
   folgenlos, wenn die Schrift schon da war. */
function neuVermessen() {
  diagramme.forEach((d) => {
    if (!d || d.isDisposed?.()) return;
    d.resize();
    if (typeof d.__neuLayouten === "function") d.__neuLayouten();
  });
}

/* Setzt Text/HTML nur, wenn das Element existiert — eine Gastgeberseite
   enthält womöglich nur einen Ausschnitt der Markierungen. */
function setzeText(id, text) {
  const el = document.getElementById(id);
  if (el) el.textContent = text ?? "";
}
function setzeHtml(id, html) {
  const el = document.getElementById(id);
  if (el) el.innerHTML = html ?? "";
}

/* --- Einordnung unter der Grafik einklappen --------------------------
   Unter jeder Grafik stehen bis zu zwei Absaetze: die Notiz (`#n-...`,
   der Befund in Worten) und die Einordnung (`#h-...`, Vorbehalte zur
   Messgroesse). Zusammen sind das 150–450 Zeichen — am Handy mehr
   Hoehe als das Diagramm darueber.

   Sie werden deshalb ZUR LAUFZEIT in ein <details> gehaengt, statt im
   Markup zu stehen. Zwei Gruende:
   - Es gibt zwei Auslieferungen (GitHub Pages und WordPress/Oxygen).
     Eine Aenderung hier wirkt in beiden; im Markup waeren es
     8 Abschnitte × 2 Auslieferungen.
   - Der Text bleibt Text im Dokument. Die Diagrammmodule fuellen ihn
     weiterhin ueber `setzeText(id, ...)`; die Kennungen wandern mit.

   28.08.2026 — ZWEI STUFEN STATT EINER. Befund des Users am
   Vogel-Abschnitt: neben der Grafik steht dreimal dieselbe Angabe
   („1998 = 100" in Unterzeile, Notiz und Einordnung). Der Aufklapper
   griff bisher nur unter 768 px; auf dem Desktop stand alles offen.

   Seither gilt:
   - AB 768 px liegt nur die Einordnung (`#h-...`) im Aufklapper. Die
     Notiz bleibt sichtbar — sie traegt den Befund, also das, wofuer
     der Abschnitt ueberhaupt da ist.
   - UNTER 768 px wandert die Notiz zusaetzlich hinein. Dort war der
     Anlass ein anderer (mehr Text als Grafik), und der gilt weiter.

   DER BEHAELTER IST PFLICHT, NICHT KOSMETIK. Auf der Website ist jede
   Sektion ein vierspaltiges Raster, in dem Kopf und Grafik ihren Platz
   ausdruecklich zugewiesen bekommen und die Einordnung ihn per
   Auto-Platzierung findet. Das funktioniert nur, solange die Karte
   GENAU DREI sichtbare Kinder hat (Abschnitt 59 der idl.css, dort am
   Live-Stand gemessen). Eine Notiz, die neben dem <details> als
   viertes Kind stuende, riss die Karte auf. `div.viz-einordnung` haelt
   beide zusammen und bleibt damit das eine dritte Kind. */
const ENG_MQ = "(max-width: 767.98px)";

function einordnungEinklappen() {
  const karten = document.querySelectorAll(".viz-karte");
  karten.forEach((karte) => {
    if (karte.querySelector(":scope > .viz-einordnung")) return;
    const notiz = karte.querySelector(':scope > p[id^="n-"]');
    const hinweis = karte.querySelector(':scope > p[id^="h-"]');
    if (!notiz && !hinweis) return;

    const behaelter = document.createElement("div");
    behaelter.className = "viz-einordnung";
    (notiz ?? hinweis).before(behaelter);
    if (notiz) behaelter.appendChild(notiz);

    if (!hinweis) return;
    const auf = document.createElement("details");
    auf.className = "viz-mehr";
    const zeile = document.createElement("summary");
    zeile.textContent = "Einordnung";
    auf.appendChild(zeile);
    auf.appendChild(hinweis);
    behaelter.appendChild(auf);
  });

  /* matchMedia ist die genaue Auskunft; die Breitenabfrage ist der
     Rueckfall fuer Umgebungen ohne sie (die jsdom-Pruefung ist eine).
     Ohne den Rueckfall reisst diese Funktion dort ab — und mit ihr der
     ganze Aufklapper. */
  const medien = global.matchMedia ? global.matchMedia(ENG_MQ) : null;
  const engJetzt = () => medien ? medien.matches
    : document.documentElement.clientWidth < ENG;

  /* Die Notiz wandert mit der Breite in den Aufklapper und wieder
     heraus. Verschoben wird der Absatz selbst, nicht eine Kopie: die
     Diagrammmodule halten keine Referenz darauf, sie schreiben ueber
     `getElementById`. Die Kennung wandert mit, also findet
     `setzeText("n-...")` ihn an beiden Orten. */
  const stellen = () => document.querySelectorAll(".viz-einordnung").forEach((b) => {
    const auf = b.querySelector(":scope > .viz-mehr");
    const notiz = b.querySelector('p[id^="n-"]');
    if (auf && notiz) {
      if (engJetzt()) {
        /* In den Aufklapper, aber HINTER die Zusammenfassungszeile. */
        if (notiz.parentElement !== auf) auf.appendChild(notiz);
        if (notiz.previousElementSibling?.tagName !== "SUMMARY") {
          auf.querySelector(":scope > summary")?.after(notiz);
        }
      } else if (notiz.parentElement !== b) {
        b.prepend(notiz);
      }
    }
    /* Zugeklappt auf allen Breiten — es sei denn, jemand hat dieses
       <details> in dieser Sitzung selbst aufgeklappt. */
    if (auf) auf.open = auf.dataset.selbst === "1";
  });

  document.addEventListener("toggle", (e) => {
    const d = e.target;
    if (d.classList?.contains("viz-mehr")) {
      d.dataset.selbst = d.open ? "1" : "0";
    }
  }, true);
  if (medien?.addEventListener) medien.addEventListener("change", stellen);
  else global.addEventListener("resize", stellen);
  stellen();
}

/* --- Tabellenansicht: jedes Diagramm hat eine ------------------------- */
document.addEventListener("click", (e) => {
  const knopf = e.target.closest(".viz-tabelle-schalter");
  if (!knopf) return;
  const feld = document.getElementById(knopf.dataset.ziel);
  const zeigen = feld.classList.contains("viz-verborgen");
  feld.classList.toggle("viz-verborgen", !zeigen);
  knopf.textContent = zeigen ? "Diagramm" : "Tabelle";
});

function tabelle(spalten, zeilen) {
  const kopf = spalten.map((s) => `<th class="${s.num ? "num" : ""}">${s.titel}</th>`).join("");
  const koerper = zeilen.map((z) =>
    "<tr>" + spalten.map((s) => `<td class="${s.num ? "num" : ""}">${s.wert(z)}</td>`).join("") + "</tr>"
  ).join("");
  return `<table class="viz-tabelle"><thead><tr>${kopf}</tr></thead><tbody>${koerper}</tbody></table>`;
}

/* --- Schutzhülle -----------------------------------------------------
   Fällt ein Diagramm aus, darf das nicht die restliche Seite leeren. */
const FEHLER = [];
const FEHLENDE = [];
function sicher(name, aufruf) {
  try {
    aufruf();
  } catch (fehler) {
    FEHLER.push(name);
    console.error(`[Dashboard] ${name} fehlgeschlagen:`, fehler);
  }
}

/* --- Signaturzeile ---------------------------------------------------
   Herkunft, Urheber und Ausgabestand in einer Zeile. Steht in allen
   Auslieferungen identisch, deshalb hier gebaut und nicht mehrfach ins
   Markup geschrieben.

   `rel="noopener"` bei target="_blank" ist Pflicht, sonst bekommt die
   Zielseite über window.opener Zugriff auf diese hier. */
function signaturHtml() {
  return (
    `<a href="https://biodiversitaet-monitor.at/" target="_blank" rel="noopener">biodiversitaet-monitor.at</a>` +
    `<span class="viz-signatur-teiler" aria-hidden="true">|</span>` +
    `Ein Projekt von Philip Reitsperger` +
    `<span class="viz-signatur-teiler" aria-hidden="true">|</span>` +
    `<a href="${VERSION.changelog}" target="_blank" rel="noopener" ` +
    `title="Was sich in dieser Ausgabe geändert hat">V ${VERSION.nummer}</a>` +
    `<span class="viz-signatur-teiler" aria-hidden="true">|</span>` +
    `<time datetime="${VERSION.datum}">${VERSION.datum_text}</time>`
  );
}

/* --- Quellenangabe (CC BY 4.0 verlangt Namensnennung) ----------------
   Anders als beim Schwesterprojekt trägt jede Quelle hier zusätzlich
   ihren Stand und ihre Art. Das ist keine Zier: Wer „Datenquellen: ÖROK"
   liest, hält die Zahl sonst für so frisch wie die Seite. Sie ist es
   nicht — sie ist von 2025 und die nächste kommt 2028. */
function baueFuss(meta) {
  const feld = document.getElementById("fuss");
  if (!feld) return;
  const quellen = (meta.quellen || []).map((q) => {
    const marke = q.art === "api"
      ? `<span class="viz-quelle-art" title="Wird bei jedem Lauf frisch abgerufen">laufend</span>`
      : `<span class="viz-quelle-art" title="Aus einer Publikation übernommen">Stand ${q.stand}</span>`;
    return `<a href="${q.url}" target="_blank" rel="noopener">${q.name}</a> (${q.lizenz}) ${marke}`;
  }).join(" · ");
  feld.innerHTML =
    "Datenquellen: " + quellen +
    `<br>${meta.hinweis_definitionen || ""}` +
    (meta.hinweis_beschaffung ? `<br>${meta.hinweis_beschaffung}` : "") +
    `<span class="viz-signatur">${signaturHtml()}</span>`;
}

/* =====================================================================
   AUFBAU — ruft die Diagrammbausteine aus js/charts/ über BIO auf
   ===================================================================== */
const diagramme = [];

async function start() {
  /* Jede Datei einzeln laden. Fällt eine aus, fehlt nur ihr Abschnitt —
     nicht die halbe Seite. Zwingend sind allein meta und kpi. */
  /* `totholz_geo` ist die Kartengeometrie und damit die mit Abstand grösste
     Datei (rund 310 KB gegen 2 KB für die Werte). Sie steht bewusst als
     eigener Eintrag: Fällt sie aus, zeigt der Abschnitt weiterhin seine
     Tabelle, statt ganz zu verschwinden. */
  const DATEIEN = ["meta", "kpi", "schutzgebiete", "vogel", "boden",
                   "rotelisten", "erhaltung", "lebensraeume",
                   "biotoptypen", "fliessgewaesser", "querbauwerke", "wald",
                   "baumarten", "waldarten", "natura2000",
                   "biolandbau", "falter", "rueckkehrer", "vogelarten"];
  /* STAND 30.08.2026 — drei der fünf Wald-Abschnitte hängen wieder drin.
   Am 29.08. waren alle fünf ausgeklinkt, weil ihre Modul- und Datendateien
   nicht im Repo lagen: ausgeliefert hätten sie 404 erzeugt und die rote
   Störmeldung im Fuß ausgelöst, derselbe Fehler wie am 21.08. mit
   `selbstaendige`. Das war richtig und bleibt die Regel — **erst
   committen, dann einhängen**.

   Die Sperre galt aber nie für alle fünf. Sie gilt für Daten, die aus
   `waldinventur.at/data/` gezogen werden, also für `totholz` und
   `fichte`. `baumarten` bezieht seine Bundeswerte aus Tab. 2 des
   Waldbiodiversitätsberichts, dessen Impressum den auszugsweisen Abdruck
   mit Quellenangabe ausdrücklich gestattet; `waldarten` und `natura2000`
   stammen aus Tab. 7 desselben Berichts bzw. aus dem Eionet-Werkzeug.

   NOCH AUSGEKLINKT, bis die BFW-Freigabe da ist: "totholz", "totholz_geo",
   "fichte". Wieder einzuhängen sind dann vier Stellen — hier, index.html
   (Sektionsblock UND Skript-Tag), embed.html über den Generator, und die
   beiden Prüfskripte.

   ZUR NOTIZ VOM 29.08., die hier stand: Sie versprach, die
   <section>-Blöcke stünden unverändert im Markup. Das stimmte nicht —
   sie waren mitentfernt worden. Wer sich darauf verlässt, sucht an vier
   Stellen und braucht fünf. */
  const geladen = {};
  await Promise.all(DATEIEN.map(async (name) => {
    geladen[name] = await hole(name).catch(() => null);
    if (!geladen[name]) FEHLENDE.push(name);
  }));

  const meta = geladen.meta, kpi = geladen.kpi;

  if (!meta || !kpi) {
    setzeText("lead", "Die Grunddaten konnten nicht geladen werden. Bitte die Seite neu laden.");
    return;
  }

  /* Die Vorspannzeile ZÄHLT, statt eine feste Zahl zu nennen.
     Bis zum 28.08.2026 stand hier „Elf Messgrößen". Die Zahl stimmte, als
     sie geschrieben wurde, und war beim nächsten Abschnitt still falsch —
     derselbe Fehler wie bei der fest verdrahteten Notiz in erhaltung.js.
     Gezählt werden die Abschnitte, die ihre Daten bekommen haben und
     deshalb sichtbar sind; ein Abschnitt ohne Datei bleibt ausgeblendet
     und darf nicht mitgezählt werden.

     Die europäischen Abschnitte stehen als Liste da und nicht als Zahl,
     damit beim Hinzufügen sofort sichtbar ist, wo nachzutragen wäre. */
  const EUROPAEISCH = ["vogel", "wald", "biolandbau", "falter"];
  const WORTE = ["null", "eine", "zwei", "drei", "vier", "fünf", "sechs",
                 "sieben", "acht", "neun", "zehn", "elf", "zwölf",
                 "dreizehn", "vierzehn", "fünfzehn", "sechzehn", "siebzehn",
                 "achtzehn", "neunzehn", "zwanzig"];
  const wortzahl = (n, grossAmSatzanfang) => {
    const w = WORTE[n] ?? String(n);
    return grossAmSatzanfang ? w[0].toUpperCase() + w.slice(1) : w;
  };
  function vorspannSetzen() {
    const sichtbar = [...document.querySelectorAll("section.viz-karte")]
      .filter((s) => s.style.display !== "none");
    const eu = sichtbar.filter((s) => EUROPAEISCH.includes(s.id.replace(/^s-/, "")));
    setzeText("lead",
      `${wortzahl(sichtbar.length, true)} Messgrößen zum Zustand der ` +
      `biologischen Vielfalt in Österreich, ${wortzahl(eu.length, false)} ` +
      `davon im europäischen Vergleich` +
      (meta?.generiert_am ? ` · zuletzt aktualisiert am ${datum(meta.generiert_am)}` : ""));
  }

  /* Alle Diagramme in EINER Funktion, damit sie beim Wechsel der
     Breitenschwelle vollstaendig neu gebaut werden koennen. Was nur
     einmal passieren darf — Quellenzeile, Ausfallmeldung — steht
     bewusst ausserhalb. */
  function baueAlles() {
    sicher("Kennzahlen",     () => BIO.baueKpis(kpi));
    sicher("Schutzgebiete",  () => BIO.baueSchutzgebiete(geladen.schutzgebiete));
    sicher("Vögel",          () => BIO.baueVogel(geladen.vogel));
    sicher("Bodenverbrauch", () => BIO.baueBoden(geladen.boden));
    sicher("Rote Listen",    () => BIO.baueRoteListen(geladen.rotelisten));
    sicher("Erhaltungszustand", () => BIO.baueErhaltung(geladen.erhaltung));
    /* Loest den Durchschnitt des Abschnitts darueber auf: 22,8 % guenstig
       ist ein Mittelwert ueber Gruppen zwischen 0 und 75 %. Muss direkt
       dahinter stehen — getrennt gelesen ist keiner von beiden falsch,
       aber der erste allein laesst die Spanne verschwinden. */
    sicher("Lebensraumgruppen", () => BIO.baueLebensraeume(geladen.lebensraeume));
    sicher("Biotoptypen",    () => BIO.baueBiotoptypen(geladen.biotoptypen));
    sicher("Fließgewässer",  () => BIO.baueFliessgewaesser(geladen.fliessgewaesser));
    /* Muss direkt hinter Fließgewässer stehen: Der Abschnitt darüber nennt
       die Zahl der Wasserkörper, die das Ziel verfehlen, dieser die Gründe.
       Getrennt gelesen wirkt der zweite wie eine beliebige Belastungsstatistik
       — sein Nenner steht im ersten. */
    /* WIEDER EINGEHÄNGT 04.09.2026 mit V 11. Am 03.09. war diese Zeile mit
       V 10 versehentlich mitgegangen, während Modul und Datendatei nicht im
       Repo lagen (beide 404 auf Pages) — das gab die rote Störmeldung im Fuß
       beider Auslieferungen und wurde mit `de9783c` zurückgenommen. Diesmal
       gehen alle elf Einbaustellen in EINEM Commit raus, Modul und Daten
       eingeschlossen. Die Regel bleibt: erst committen, dann einhängen. */
    sicher("Belastungen",    () => BIO.baueQuerbauwerke(geladen.querbauwerke));
    sicher("Waldfläche",     () => BIO.baueWald(geladen.wald));
    /* Bereich Wald — die Reihenfolge ist die Aussage: erst wie viel Wald es
       gibt, dann was in ihm steht. Die Waldfläche wächst; Totholz und
       Fichtenanteil sagen, dass daraus noch keine Vielfalt folgt.

       NOCH AUSGEKLINKT (Stand 30.08.2026): Totholz und Fichte ziehen ihre
       Werte aus `waldinventur.at/data/` und warten auf die BFW-Freigabe.
       Sobald sie da ist: hier einhängen, dazu Sektionsblock und Skript-Tag
       in index.html, den Generator für embed.html und die beiden
       Prüfskripte.

    sicher("Totholz",        () => BIO.baueTotholz(geladen.totholz, geladen.totholz_geo));
    sicher("Fichte",         () => BIO.baueFichte(geladen.fichte));
    */
    sicher("Baumarten",      () => BIO.baueBaumarten(geladen.baumarten));
    /* Erst der Wald selbst, dann was in ihm lebt und wie er bewertet wird.
       `waldarten` zeigt den Verlust, `natura2000` die Kehrseite: dass
       dieselbe Meldung je nach Messweise zwei Antworten gibt. */
    sicher("Waldarten",      () => BIO.baueWaldarten(geladen.waldarten));
    sicher("Natura 2000",    () => BIO.baueNatura2000(geladen.natura2000));
    sicher("Biolandbau",     () => BIO.baueBiolandbau(geladen.biolandbau));
    /* Bereich Tiergruppen — als Gegensatz gebaut: Verlust, Erholung,
       Stillstand. Die Reihenfolge ist die Aussage und darf nicht nach
       Bequemlichkeit umgestellt werden. */
    sicher("Wiesenfalter",   () => BIO.baueFalter(geladen.falter));
    sicher("Rückkehrer",     () => BIO.baueRueckkehrer(geladen.rueckkehrer));
    sicher("Vogelarten",     () => BIO.baueVogelarten(geladen.vogelarten));
  }
  baueAlles();
  /* NACH baueAlles(): erst dort blenden die Module ihre Abschnitte ein.
     Vorher gezählt wäre das Ergebnis immer null. */
  sicher("Vorspannzeile", vorspannSetzen);
  beiBreitenwechsel(baueAlles);
  sicher("Einordnung einklappen", einordnungEinklappen);

  sicher("Quellenangabe", () => baueFuss(meta));

  /* Ausfälle benennen statt still schlucken */
  const ausgefallen = [...new Set([...FEHLER, ...FEHLENDE])];
  if (ausgefallen.length) {
    const feld = document.getElementById("fuss");
    /* Vor die Signatur, nicht dahinter: die Signaturzeile schließt den
       Fuß ab und darf nicht von einer Fehlermeldung untertitelt werden. */
    const signatur = feld?.querySelector(".viz-signatur");
    const meldung =
      `<br><span style="color:${stil("--viz-kritisch")}">Gerade nicht ` +
      `verfügbar: ${ausgefallen.join(", ")}. Die übrigen Angaben sind ` +
      `davon unberührt.</span>`;
    if (signatur) signatur.insertAdjacentHTML("beforebegin", meldung);
    else if (feld) feld.insertAdjacentHTML("beforeend", meldung);
  }

  /* Erst NACH dem Aufbau anhängen: Ist die Schrift schon da, löst das
     Versprechen sofort aus und der Aufruf kostet nur ein resize. Ist sie
     noch unterwegs, kommt die Neuvermessung, sobald sie eintrifft. */
  if (document.fonts?.ready) document.fonts.ready.then(neuVermessen);

  window.addEventListener("resize", () => diagramme.forEach((d) => {
    d.resize();
    if (typeof d.__neuLayouten === "function") d.__neuLayouten();
  }));

  springeZuAbschnitt();
}

/* --- Tieflink auf einen Abschnitt: /#s-rotelisten ---------------------
   Abschnitte, die sich selbst einblenden, tragen beim Seitenaufbau
   `style="display:none"`. Auf ein verstecktes Element springt der Browser
   nicht — und wenn das Modul es Sekunden später einblendet, hat er den
   Fragmentbezeichner längst abgehakt. Ohne diese Funktion landet jeder
   geteilte Link oben auf der Seite.

   Deshalb wird kurz gewartet, statt einmal zu prüfen. Zehn Versuche à
   300 ms decken den üblichen Fall ab; danach wird aufgegeben, ohne die
   Seite zu bewegen — ein Sprung ins Leere wäre schlimmer als kein Sprung.

   `history.replaceState` bleibt aus: Die Adresse soll teilbar bleiben. */
function springeZuAbschnitt() {
  const kennung = (location.hash || "").slice(1);
  if (!/^s-[\w-]+$/.test(kennung)) return;
  if (window.scrollY > 0) return;

  /* Der Sprung wird selbst gerechnet und mit `behavior: "instant"` gesetzt.
     `behavior: "auto"` heisst laut Spezifikation NICHT "sofort", sondern
     "nimm das berechnete `scroll-behavior`" — und das Theme setzt
     `html { scroll-behavior: smooth }`. Die weiche Animation laeuft auf
     dieser Seite nicht los: gemessen am 26.08.2026 blieb `scrollY` mit
     "auto" auf 0, waehrend derselbe Aufruf mit "instant" traf. Das
     Navigationsskript der Menueleiste rechnet aus demselben Grund seit
     jeher selbst — nur der Tieflink tat es nicht.

     `scroll-margin-top` der Karte haelt den Abstand zum klebrigen Kopf.
     `scrollIntoView` haette ihn von selbst beruecksichtigt, `scrollTo`
     nicht — also hier abziehen. */
  const setzen = (ziel) => {
    const marge = parseFloat(getComputedStyle(ziel).scrollMarginTop) || 0;
    const y = Math.max(
      0, window.scrollY + ziel.getBoundingClientRect().top - marge);
    try { window.scrollTo({ top: y, left: 0, behavior: "instant" }); }
    catch (e) { window.scrollTo(0, y); }   /* Browser ohne "instant" */
  };

  /* Nach dem Sprung waechst die Seite noch: ECharts vermisst neu, sobald
     die Schrift eintrifft, Tabellen und Hinweiszeilen kommen dazu. Also
     dreimal nachfassen — aber nur, solange der Leser die Seite nicht
     selbst bewegt hat. Sonst reisst die Korrektur ihn zurueck. */
  let eigenerScroll = false;
  const merken = () => { eigenerScroll = true; };
  ["wheel", "touchstart", "keydown"].forEach((art) =>
    window.addEventListener(art, merken, { once: true, passive: true }));

  let nach = 0;
  const nachfassen = () => {
    if (eigenerScroll || ++nach > 3) return;
    const ziel = document.getElementById(kennung);
    if (!ziel || ziel.getClientRects().length === 0) return;
    const marge = parseFloat(getComputedStyle(ziel).scrollMarginTop) || 0;
    if (Math.abs(ziel.getBoundingClientRect().top - marge) > 2) setzen(ziel);
    setTimeout(nachfassen, 400);
  };

  let versuche = 0;
  const versuchen = () => {
    const ziel = document.getElementById(kennung);
    const sichtbar = ziel && ziel.getClientRects().length > 0;
    if (sichtbar) {
      setzen(ziel);
      setTimeout(nachfassen, 400);
      return;
    }
    if (++versuche < 10) setTimeout(versuchen, 300);
  };
  versuchen();
}

/* --- Karten: Zuschnitt in Pixeln ------------------------------------
   ECharts kennt für Geokarten kein „passe dich dem Container an". Weder ein
   prozentuales `layoutSize` noch `left/right/top/bottom` erzeugen einen
   verzerrungsfreien Zuschnitt — `layoutSize` will eine Pixelzahl.

   Die Rechnung: Aus dem Kartenrahmen in Grad und dem `aspectScale` ergibt
   sich das Seitenverhältnis der Karte. Je nachdem, ob sie breiter oder
   höher als der Container ist, begrenzt die Breite oder die Höhe. Die 98 %
   am Ende sind Luft für den Rand, damit Vorarlberg nicht an der Kante klebt.

   WICHTIG: Das Ergebnis ist eine Pixelzahl und überlebt kein resize. Module,
   die diesen Helfer nutzen, müssen sich ein `__neuLayouten` an die
   Diagramminstanz hängen — `neuVermessen()` ruft es beim Umbau auf. */
function kartenLayout(feld, rahmen, aspectScale) {
  const breite = feld.clientWidth || 1;
  const hoehe = feld.clientHeight || 1;
  const gradBreit = rahmen[1][0] - rahmen[0][0];
  const gradHoch = rahmen[1][1] - rahmen[0][1];
  const verhaeltnis = (gradBreit * aspectScale) / gradHoch;
  const groesse = verhaeltnis >= 1
    ? Math.min(breite, hoehe * verhaeltnis)     // breiter als hoch: Breite begrenzt
    : Math.min(hoehe, breite / verhaeltnis);    // höher als breit: Höhe begrenzt
  return {
    aspectScale,
    boundingCoords: rahmen,
    layoutCenter: ["50%", "50%"],
    layoutSize: Math.floor(groesse * 0.98),
  };
}

/* --- Namensraum: die Chart-Dateien hängen sich hier an ---------------- */
const BIO = {
  hole, basis, achse, tabelle, stil, zahl, pz, monat, datum,
  setzeText, setzeHtml, sicher, diagramme, baueFuss,
  schrift, px, neuVermessen, kartenLayout,
  VERSION, signaturHtml,
  /* Breitenabhaengiges Layout — siehe „Schmale Fenster" oben */
  istSchmal, istEng, balkenGitter, kategorieLabel, balkenBreite, balkenHoehe,
  legende, legendeLinks, endLabelZeigen,
  /* Hover an Balken: dunkler statt heller */
  dunkler, hoverDunkler,
  setzeBasis: (pfad) => { DATEN_BASIS = pfad; },
  /* Fail-soft: ein null-Argument darf den Rückfall (#dashboard bzw. body)
     NICHT überschreiben. Ohne Wrapper fehlen nur die Token: die Diagramme
     kommen dann in den ECharts-Vorgabefarben, statt gar nicht zu
     erscheinen. */
  setzeWurzel: (element) => {
    if (!element) {
      console.warn("[Dashboard] setzeWurzel: kein Element übergeben — " +
        "fehlt der .viz-root-Wrapper? Es bleibt bei " +
        (wurzel === document.body ? "document.body" : "#dashboard") +
        ", die --viz-*-Token greifen dort vermutlich nicht.");
      return;
    }
    wurzel = element;
  },
  start,
};
global.BIO = BIO;
})(window);
