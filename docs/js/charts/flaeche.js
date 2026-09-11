/* ===========================================================================
   Biodiversitäts-Dashboard Österreich — Themenstrang: flaeche
   ---------------------------------------------------------------------------
   Wird nach js/kern.js geladen; die Helfer kommen aus window.BIO.
   =========================================================================== */
(function (BIO) {
"use strict";
const { stil, zahl, pz, basis, tabelle, setzeText, setzeHtml,
        diagramme, schrift } = BIO;

/* --- Flächeninanspruchnahme je Gemeinde: Zustandskarte -----------------

   WARUM NUR DER ZUSTAND UND KEINE VERÄNDERUNG:
   Das ist keine gestalterische Entscheidung, sondern die Auflage, unter der
   diese Karte überhaupt erlaubt ist. Das Umweltbundesamt (Gebhard Banko,
   04.09.2026) hat die Eigenberechnung aus den offenen GIS-Daten freigegeben,
   weil die amtliche Gemeindestatistik erst 2027 erscheint — mit der
   Bedingung, dass die Veränderungen 2022–2025 auf Gemeindeebene NICHT
   gezeigt werden. Der Grund liegt in der Ermittlung der
   Straßenveränderungen, die auf Gemeindeebene stark durchschlägt. Der
   Vorbehalt gehört in den Text, nicht in eine Fußnote; er steht in
   `hinweis` und kommt aus dem ETL mit.

   WARUM DIE KARTE ÜBER DIE GEMEINDEKENNZIFFER LÄUFT UND NICHT ÜBER DEN
   NAMEN: ECharts verknüpft Kartenflächen mit Daten über `properties.name`.
   In Österreich sind Gemeindenamen aber nicht eindeutig — in den 2.092
   Gemeinden des Gebietsstands 01.01.2025 kommen **Mühldorf, Warth und
   Krumbach je zweimal** vor. Über den Namen verknüpft, bekäme eine der
   beiden den Wert der anderen oder gar keinen, und zwar lautlos. Die
   Geometrie wird deshalb vor dem Registrieren umgeschlüsselt: `name` trägt
   die Kennziffer, der Anzeigename wandert nach `titel` und wird nur im
   Tooltip und in der Tabelle benutzt.

   WARUM FÜNF KLASSEN UND KEINE STUFENLOSE RAMPE:
   Die Verteilung ist stark rechtsschief — Bundeswert 6,8 %, Median 7,7 %,
   Spitze knapp 79 %. Stufenlos gefärbt lägen zwei Drittel der Gemeinden in
   einem kaum unterscheidbaren Farbband. Die Grenzen kommen aus den Daten
   (Quantile, auf halbe Prozentpunkte gerundet) und stehen in der Legende.

   WAS DER NENNER VERZERRT, UND WARUM ER TROTZDEM DIE GEMEINDEFLÄCHE IST:
   Im Bund stehen 6,8 % der Landesfläche gegen 17,4 % des
   Dauersiedlungsraums — Faktor 2,6. Je Gemeinde streut dieser Faktor mit
   dem Relief: Fels, Gletscher und Steilwald stehen im Nenner, eine
   Alpengemeinde wirkt dadurch makellos. Kaisers (0,15 %) und Rattenberg
   (78,7 % auf 11,3 Hektar) sind beide korrekt gerechnet und meinen
   Verschiedenes. Der Nenner ist deshalb in der Unterzeile benannt, und die
   Notiz sagt, was er nicht kann. → `feedback-nenner-vor-farbe`

   WARUM DIE TABELLE KLASSEN ZEIGT UND KEINE 2.092 ZEILEN:
   Eine Tabelle mit allen Gemeinden wäre unlesbar, eine mit den „zehn
   höchsten" wäre eine stille Auswahl. Die Klassentabelle ist vollständig —
   jede Gemeinde steckt in genau einer Zeile — und beantwortet die Frage,
   die die Karte aufwirft: wie viele Gemeinden liegen eigentlich oben. */

/* ECharts kennt nur Polygon und MultiPolygon. Eigene Fassung statt der aus
   `totholz.js`: Dieses Modul wird ausgeliefert, jenes liegt hinter der
   offenen BFW-Freigabe und ist auf der Seite gar nicht geladen — ein
   Rückgriff auf `BIO.flaechenNormalisieren` wäre in der Auslieferung
   `undefined`. */
function nurFlaechen(geometrie) {
  if (!geometrie) return null;
  if (geometrie.type === "Polygon" || geometrie.type === "MultiPolygon") return geometrie;
  if (geometrie.type === "GeometryCollection") {
    const teile = (geometrie.geometries ?? []).map(nurFlaechen).filter(Boolean);
    if (!teile.length) return null;
    const ringe = teile.flatMap((t) =>
      t.type === "Polygon" ? [t.coordinates] : t.coordinates);
    return { type: "MultiPolygon", coordinates: ringe };
  }
  return null;
}

/* Umschlüsseln auf die Kennziffer — siehe Kopfkommentar. Ohne diesen
   Schritt verlieren drei Gemeindepaare lautlos ihre Einfärbung. */
function aufKennziffer(geo) {
  if (!geo?.features) return geo;
  return {
    ...geo,
    features: geo.features
      .map((merkmal) => {
        const e = merkmal.properties || {};
        return {
          ...merkmal,
          geometry: nurFlaechen(merkmal.geometry),
          properties: { ...e, name: String(e.gkz || ""), titel: e.name || "" },
        };
      })
      .filter((m) => m.geometry && m.properties.name),
  };
}

/* Kartenrahmen in EPSG:31287 (MGI Austria Lambert), [[West, Süd], [Ost, Nord]]
   in Metern. Fest gesetzt und nicht aus der Geometrie gerechnet, damit ein
   einzelnes verzogenes Polygon den Zuschnitt nicht kippt. Lambert ist
   flächentreu und in Metern — anders als bei einer Gradkarte ist die
   Streckung deshalb 1. */
const RAHMEN_AT = [[105000, 275000], [695000, 580000]];
const ASPEKT = 1;

/* Der Zeichner wird nach Können gewählt, nicht nach Vorliebe. Im Browser
   ist Canvas bei 2.092 Flächen deutlich flüssiger als 2.092 SVG-Pfade; in
   der jsdom-Prüfung gibt es ohne das native canvas-Paket kein
   `getContext`, ECharts stirbt dort mit „Cannot set properties of null
   (setting 'dpr')" und die Grafik ließe sich gar nicht prüfen.
   → `reference-neuer-abschnitt-biodiversitaet` */
let ZEICHNER = null;
function zeichner() {
  /* Einmal fragen, Antwort merken. Ohne den Zwischenspeicher meldet jsdom
     die Probe bei jedem Aufbau erneut („Not implemented:
     HTMLCanvasElement's getContext()") und flutet das Prüfprotokoll — und
     das Protokoll ist der Ort, an dem man sehen soll, was herauskam. */
  if (ZEICHNER) return ZEICHNER;
  try {
    const probe = document.createElement("canvas");
    ZEICHNER = (probe.getContext && probe.getContext("2d")) ? "canvas" : "svg";
  } catch (fehler) {
    ZEICHNER = "svg";
  }
  return ZEICHNER;
}

function klassenNamen(grenzen) {
  const g = grenzen.map((x) => pz(x));
  return [
    `unter ${g[0]} %`,
    `${g[0]} bis ${g[1]} %`,
    `${g[1]} bis ${g[2]} %`,
    `${g[2]} bis ${g[3]} %`,
    `über ${g[3]} %`,
  ];
}

function klasseVon(anteil, grenzen) {
  for (let i = 0; i < grenzen.length; i += 1) if (anteil < grenzen[i]) return i;
  return grenzen.length;
}

function baueFlaeche(daten, geo) {
  const S = schrift();
  if (!daten?.gemeinden?.length) return;

  const abschnitt = document.getElementById("s-flaeche");
  if (abschnitt) abschnitt.style.display = "";

  const feld = document.getElementById("c-flaeche");
  if (!feld) return;

  const at = daten.oesterreich || {};
  const grenzen = daten.klassengrenzen || [4, 6.5, 9, 13.5];
  const namen = klassenNamen(grenzen);
  const mitWert = daten.gemeinden.filter((g) => g.anteil !== null);
  const sortiert = [...mitWert].sort((a, b) => b.anteil - a.anteil);
  const median = sortiert.length
    ? sortiert[Math.floor(sortiert.length / 2)].anteil : 0;

  setzeText("u-flaeche",
    `Anteil der Gemeindefläche, der verbaut, versiegelt oder als Verkehrsweg ` +
    `beansprucht ist · Stand ${daten.stand} · eigene Auswertung der ` +
    `ÖROK-Monitoringdaten`);

  /* Die Notiz nennt den Median GEGEN den Bundeswert. Das ist der Befund,
     den die Karte allein nicht hergibt: Der Bundeswert ist flächengewichtet
     und wird von wenigen sehr großen Alpengemeinden nach unten gezogen —
     die Hälfte aller Gemeinden liegt darüber. */
  setzeText("n-flaeche",
    `Österreichweit sind ${pz(at.anteil)} % der Fläche in Anspruch genommen. ` +
    `Die Hälfte der ${zahl(daten.gemeinden.length)} Gemeinden liegt aber über ` +
    `${pz(median)} % — der Bundeswert ist flächengewichtet, und die großen ` +
    `Gemeinden sind die alpinen. Der Nenner ist die gesamte Gemeindefläche, ` +
    `Fels und Gletscher eingerechnet: Wo wenig Boden besiedelbar ist, ` +
    `erscheint der Anteil niedrig, ohne dass dort mehr Platz wäre.`);

  setzeText("h-flaeche", daten.hinweis || "");

  if (!geo) {
    /* Höhe zurücknehmen, sonst steht ein leerer Kasten da — solange die
       Geometrie noch lädt oder wenn sie ausfällt. */
    feld.className = "";
    feld.style.height = "auto";
    feld.innerHTML = `<p class="viz-unterzeile" style="padding:4px 0 0">
      Die Karte wird geladen — die Verteilung steht in der Tabelle
      darunter.</p>`;
  } else {
    /* Zurücksetzen, falls vorher der Platzhalter stand: Das Feld wird
       zweimal gebaut — einmal ohne Geometrie, damit Text und Tabelle sofort
       stehen, und einmal mit, sobald die 1,5 MB da sind. */
    if (!feld.classList.contains("viz-chart")) {
      /* BEIDE Klassen zurückholen, nicht nur `viz-chart`: Der Platzhalter
         oben räumt `className` leer, und ein schlichtes
         `className = "viz-chart"` hätte `viz-chart-hoch` mitgenommen — die
         Karte wäre nach dem Nachladen in einem 340-px-Feld gelandet und auf
         zwei Drittel der Breite gedeckelt worden. Am Live-Stand gemessen:
         796 px Karte mit der hohen Klasse, 644 px ohne. */
      feld.className = "viz-chart viz-chart-hoch";
      feld.style.height = "";
      feld.innerHTML = "";
    }

    echarts.registerMap("at-gemeinden", aufKennziffer(geo));
    const d = echarts.getInstanceByDom(feld)
      || echarts.init(feld, null, { renderer: zeichner() });
    if (!diagramme.includes(d)) diagramme.push(d);

    const nachKennziffer = Object.fromEntries(
      daten.gemeinden.map((g) => [g.gkz, g]));
    const werte = daten.gemeinden.map((g) => ({
      name: g.gkz,
      value: g.anteil === null ? "-" : g.anteil,
    }));

    d.setOption({
      ...basis(),
      tooltip: {
        ...basis().tooltip, trigger: "item",
        formatter: (p) => {
          const g = nachKennziffer[p.name];
          if (!g) return `<span style="color:${stil("--viz-muted")}">keine Daten</span>`;
          return `<strong>${g.name}</strong><br>` +
            `${pz(g.anteil)} % der Gemeindefläche<br>` +
            `<span style="color:${stil("--viz-muted")}">` +
            `${zahl(Math.round(g.fi_ha))} von ${zahl(Math.round(g.flaeche_ha))} ha` +
            `</span>`;
        },
      },
      visualMap: {
        type: "piecewise",
        left: 12, bottom: 12, orient: "vertical",
        itemWidth: 14, itemHeight: 12, itemGap: 4,
        /* Absteigend, damit die dunkelste Stufe oben steht — die Legende
           liest sich dann in derselben Richtung wie die Karte. */
        inverse: true,
        pieces: [
          { lt: grenzen[0], label: namen[0] },
          { gte: grenzen[0], lt: grenzen[1], label: namen[1] },
          { gte: grenzen[1], lt: grenzen[2], label: namen[2] },
          { gte: grenzen[2], lt: grenzen[3], label: namen[3] },
          { gte: grenzen[3], label: namen[4] },
        ],
        textStyle: { color: stil("--viz-muted"), fontSize: S.achse },
        /* EIGENE Familie, nicht `--viz-seq-*`: Die Karte zeigt beanspruchte
           Fläche, und auf WordPress ist `--viz-seq-*` grün — das liest sich
           als Natur und sagt das Gegenteil. Befund des Users 11.09.2026.
           neutral-1 ist fast der Untergrund und bliebe auf einer Fläche
           unsichtbar; die fünf Stufen laufen deshalb von 2 nach 6.
           Dunkel heißt mehr — in beiden Farbmodi, weil die Rampe im
           Dunkelmodus mitgedreht wird. */
        inRange: { color: [
          stil("--viz-seq-neutral-2"), stil("--viz-seq-neutral-3"),
          stil("--viz-seq-neutral-4"), stil("--viz-seq-neutral-5"),
          stil("--viz-seq-neutral-6"),
        ] },
      },
      series: [{
        type: "map", map: "at-gemeinden", data: werte,
        roam: false,
        ...BIO.kartenLayout(feld, RAHMEN_AT, ASPEKT),
        itemStyle: {
          areaColor: stil("--viz-grid"),
          /* Haarlinie, keine Trennlinie: Ein 1-px-Rand verschluckt bei
             2.092 Flächen auf Österreichbreite die kleinen Gemeinden
             vollständig (Entscheid 09.09.). 0,5 px trägt das Bild — am
             Live-Stand gemessen und vom User am 11.09. abgenommen. Ohne
             Rand sind die Gemeinden innerhalb einer Klasse nicht zu
             unterscheiden, und genau das war der Befund. */
          borderWidth: 0.5,
          borderColor: stil("--viz-karte-rand"),
        },
        label: { show: false },
        emphasis: {
          label: { show: false },
          itemStyle: { borderColor: stil("--viz-text"), borderWidth: 1 },
        },
        select: { disabled: true },
      }],
    });

    /* `layoutSize` ist eine Pixelzahl und überlebt kein resize. */
    d.__neuLayouten = () => d.setOption({
      series: [BIO.kartenLayout(feld, RAHMEN_AT, ASPEKT)],
    });
  }

  /* Klassentabelle: vollständig, weil jede Gemeinde in genau einer Zeile
     steckt. Das Beispiel ist die größte Gemeinde der Klasse — nicht die
     extremste, sonst stünde in der obersten Zeile wieder Rattenberg mit
     seinen 11,3 Hektar und der Nenner wäre die Nachricht. */
  const faecher = namen.map((name, i) => ({ name, i, eintraege: [] }));
  mitWert.forEach((g) => faecher[klasseVon(g.anteil, grenzen)].eintraege.push(g));
  setzeHtml("t-flaeche", tabelle(
    [{ titel: "Anteil verbaut", wert: (z) => z.name },
     { titel: "Gemeinden", num: true, wert: (z) => zahl(z.eintraege.length) },
     { titel: "Anteil aller Gemeinden", num: true,
       wert: (z) => `${pz(100 * z.eintraege.length / mitWert.length)} %` },
     { titel: "größte Gemeinde darin",
       wert: (z) => {
         if (!z.eintraege.length) return "–";
         const g = z.eintraege.reduce((a, b) =>
           (b.flaeche_ha > a.flaeche_ha ? b : a));
         return `${g.name} (${pz(g.anteil)} %)`;
       } }],
    [...faecher].reverse()
  ));
}

BIO.baueFlaeche = baueFlaeche;
})(window.BIO);
