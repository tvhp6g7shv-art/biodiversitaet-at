/* ===========================================================================
   Biodiversitäts-Dashboard Österreich — Themenstrang: kpi
   ---------------------------------------------------------------------------
   Wird nach js/kern.js geladen; die Helfer kommen aus window.BIO.
   =========================================================================== */
(function (BIO) {
"use strict";
const { pz, zahl, setzeHtml } = BIO;

/* --- Kennzahlenzeile -------------------------------------------------
   Vier Kacheln, vier Abschnitte. Bewusst KEINE Gesamtnote: es gibt keinen
   sinnvollen Index, der Schutzgebietsfläche, Vogelbestand, Bodenverbrauch
   und Datenlage zu einer Zahl verrechnet. Wer eine baut, erfindet
   Gewichte, die niemand belegen kann.

   Jede Kachel trägt ihr eigenes Bezugsjahr. Das ist hier kein Detail,
   sondern nötig: die vier Zahlen stammen aus 2023, 2023, 2025 und 2025 —
   eine gemeinsame Datumszeile über der Reihe wäre schlicht falsch. */

/* `kennung` ist NEU und traegt keine Wertung, sondern nur den Namen der
   Kachel — dieselbe Kennung wie die zugehoerige Sektion (`s-vogel` usw.).
   Ob eine Zahl gut oder schlecht ist, entscheidet das CSS
   (Abschnitt 49 der idl.css), nicht diese Datei.

   WARUM DIE TRENNUNG: die Wertung ist eine redaktionelle Aussage und
   aendert sich, wenn sich die Lage aendert. Als CSS-Regel ist das ein
   Einzeiler; hier waere es ein Push und eine neue Cache-Ziffer.

   WARUM NICHT `:nth-child()` STATT DESSEN: jede Kachel haengt an einem
   `if (kpi.X !== undefined)`. Fehlt ein Wert, ruecken alle folgenden
   Kacheln eine Stelle vor — und die Farben saessen still auf den
   falschen Zahlen. Ein Name kann das nicht. */
/* ALLE ACHT TITEL SIND NOMINALPHRASEN, KEINE SATZENDEN (25.08.2026)

   `idl.css` 45.5 zieht `.viz-kpi-titel` mit `order: -1` ÜBER den Wert,
   obwohl diese Funktion Wert → Titel → Fussnote baut. Ein Titel, der als
   Fortsetzung der Zahl geschrieben ist („3 von 27 Roten Listen sind auf
   aktuellem Stand"), steht damit VOR seinem Subjekt und liest sich
   rueckwaerts. Wer hier einen Titel aendert: er muss allein stehen
   koennen, ohne die Zahl davor. */
/* TITEL UND FUSSNOTE BLEIBEN EINZEILIG (03.09.2026)

   Bei vier Spalten ist der Textbereich einer Kachel 261 px breit
   (Container 1336 px, gemessen an der WordPress-Auslieferung). Titel und
   Fussnote muessen darunter bleiben, sonst bricht eine Kachel um und ihre
   Zahl sitzt tiefer als die der Nachbarn — die Reihe fluchtet nicht mehr.

   Gemessene Breiten des aktuellen Satzes (Titel / Fussnote, in px):
     schutzgebiete 216 / 210   vogel       231 / 149
     boden         193 / 107   rotelisten  160 / 208
     erhaltung     239 / 211   biotoptypen 188 / 198
     wald          163 / 147   biolandbau  212 / 185

   Wer hier Text aendert, misst nach — nicht nach Zeichenzahl schaetzen:
   die Titel stehen in Versalien mit `letter-spacing`, ein Zeichen kostet
   je nach Buchstabe zwischen 5 und 9 px. Messung: Testspan mit
   `white-space: nowrap` und dem `font`/`letter-spacing`/`text-transform`
   der echten `.viz-kpi-titel` gegen deren `getBoundingClientRect().width`.

   Unterhalb von 1025 px Breite stellt `idl.css` auf zwei Spalten um; dort
   ist die Kachel breiter und die Regel unkritisch. Zwischen 1025 px und
   rund 1700 px sind die vier Spalten schmaler als 261 px und die Titel
   brechen wieder — das ist hingenommen, nicht uebersehen. */
function kachel(wert, einheit, titel, fussnote, kennung) {
  return (
    `<div class="viz-kpi" data-kpi="${kennung}">` +
      `<div class="viz-kpi-wert">${wert}<span class="viz-kpi-einheit">${einheit}</span></div>` +
      `<div class="viz-kpi-titel">${titel}</div>` +
      `<div class="viz-kpi-fuss">${fussnote}</div>` +
    `</div>`
  );
}

function baueKpis(kpi) {
  if (!kpi) return;
  const teile = [];

  if (kpi.schutzgebiete_prozent !== undefined) {
    teile.push(kachel(
      pz(kpi.schutzgebiete_prozent), " %",
      /* 03.09.2026 — „Anteil der“ gestrichen: die Einheit hinter der Zahl
         ist „%“, damit ist der Anteil schon gesagt. */
      "Landesfläche unter Schutz",
      `${kpi.schutzgebiete_jahr} · Ziel 30 %, ${pz(kpi.schutzgebiete_luecke)} Punkte fehlen`,
      "schutzgebiete"
    ));
  }

  /* 25.08.2026 — Index raus, Verlust rein. „56,8" war ohne die Basiszeile
     nicht lesbar, und die Basiszeile stand klein darunter. Die Kachel sagt
     jetzt dasselbe wie die Überschrift der Sektion („gut vier von zehn sind
     seit 1998 verschwunden") und ist baugleich zur Wald-Kachel: Größe seit
     einem Jahr, als Veränderung.

     `vogel_verlust` kommt aus build.py. Der Rückfall rechnet ihn aus dem
     Index, damit eine ältere kpi.json aus dem Cache die Kachel nicht
     leert — sie zeigt dann dieselbe Zahl. */
  if (kpi.vogel_index !== undefined) {
    const verlust = kpi.vogel_verlust !== undefined
      ? kpi.vogel_verlust : 100 - kpi.vogel_index;
    const beginn = kpi.vogel_beginn ?? 1998;
    teile.push(kachel(
      "−" + pz(verlust, 0), " %",
      /* 03.09.2026 — „Vogelbestand“ und „seit 1998“ raus: das Minus vor
         der Zahl sagt, dass es ein Rueckgang ist, und die Fussnote
         darunter traegt den Zeitraum ohnehin („1998 bis 2025“). Beide
         Habitate bleiben stehen — „Feldvoegel“ allein waere ein
         Fachbegriff. */
      "Vögel auf Feldern und Wiesen",
      (kpi.vogel_arten ? `${zahl(kpi.vogel_arten)} Arten · ` : "") +
        `${beginn} bis ${kpi.vogel_jahr}`,
      "vogel"
    ));
  }

  if (kpi.boden_ha_pro_tag !== undefined) {
    teile.push(kachel(
      pz(kpi.boden_ha_pro_tag), " ha",
      /* 25.08.2026 — „Boden werden pro Tag neu beansprucht" war der
         Schluss eines Satzes, der mit der Zahl begann. Über der Zahl
         stehend war es kein Satz mehr, sondern ein Fehler im Numerus.
         Jetzt derselbe Begriff wie in der Überschrift der Sektion. */
      "Bodenverbrauch pro Tag",
      `Mittel ${kpi.boden_periode}`,
      "boden"
    ));
  }

  /* 25.08.2026 — Der Titel war das Ende eines Satzes, dessen Anfang die
     Zahl war („3 von 27 Roten Listen sind auf aktuellem Stand"). CSS 45.5
     zieht den Titel aber mit `order: -1` ÜBER die Zahl, und damit las sich
     die Kachel rückwärts. Jetzt eine Nominalphrase, die für sich steht.

     Die Fußnote sagt neu, WORAN „aktuell" gemessen ist. Ohne sie war die
     Zahl nicht einzuordnen: 3 von 27 klingt nach einem Versäumnis, sagt
     aber nicht, wie weit die übrigen zurückliegen. */
  if (kpi.rotelisten_aktuell !== undefined) {
    /* 03.09.2026 — Die Fussnote trug bisher Altersspanne, Fehlbestand UND
       Stichmonat und lief damit ueber zwei Zeilen. Von den dreien traegt
       der Nenner am meisten: „27“ steht in der Zahl, aber ohne die
       Fussnote weiss niemand, dass 27 Tiergruppen gemeint sind und nicht
       27 Listen. Zweitwichtigstes ist der Fehlbestand — vier Gruppen
       haben ueberhaupt keine Liste, das ist etwas anderes als eine alte.
       Die Altersspanne der uebrigen steht im Abschnitt darunter. */
    const spanne = kpi.rotelisten_ohne
      ? `${zahl(kpi.rotelisten_ohne)} ganz ohne Liste`
      : "Oktober 2025";
    teile.push(kachel(
      `${zahl(kpi.rotelisten_aktuell)}<span class="viz-kpi-von"> von ${zahl(kpi.rotelisten_gesamt)}</span>`, "",
      /* Titel 25.08.2026: „Tiergruppen mit aktuellem Wissensstand" war
         nicht verständlich. „Wissensstand" ist kein Wort, das jemand
         außerhalb des Fachs benutzt, und es sagt nicht, WORAN der Stand
         hängt. Gemessen wird, ob die Rote Liste einer Tiergruppe noch
         innerhalb ihres vorgesehenen Neuauflage-Zeitraums liegt — also
         ob es eine aktuelle Rote Liste gibt. Genau das steht jetzt da. */
      /* 03.09.2026 — „Tiergruppen mit aktueller Roter Liste“ brauchte
         zwei Zeilen (295 px bei 261 px Platz). „Tiergruppen“ wandert in
         die Fussnote, wo es den Nenner erklaert; der Titel behaelt das,
         was gemessen wird. */
      "Aktuelle Rote Listen",
      `${zahl(kpi.rotelisten_gesamt)} Tiergruppen · ${spanne}`,
      "rotelisten"
    ));
  }

  if (kpi.erhaltung_guenstig !== undefined) {
    teile.push(kachel(
      pz(kpi.erhaltung_guenstig, 0), " %",
      /* 03.09.2026 — „-typen“ gestrichen (276 px bei 261 px Platz). Die
         Fussnote nennt Artikel 17 FFH, dort sind Typen gemeint. */
      "Lebensräume in gutem Zustand",
      `Artikel 17 FFH · Periode ${kpi.erhaltung_periode}`,
      "erhaltung"
    ));
  }

  if (kpi.biotoptypen_anteil !== undefined) {
    teile.push(kachel(
      pz(kpi.biotoptypen_anteil), " %",
      "Gefährdete Biotoptypen",
      `${zahl(kpi.biotoptypen_bewertet)} bewertete Typen · Rote Liste`,
      "biotoptypen"
    ));
  }

  if (kpi.wald_veraenderung !== undefined) {
    teile.push(kachel(
      (kpi.wald_veraenderung > 0 ? "+" : "") + pz(kpi.wald_veraenderung), " %",
      "Waldfläche seit 1990",
      `${kpi.wald_von} bis ${kpi.wald_bis} · Eurostat`,
      "wald"
    ));
  }

  if (kpi.bio_anteil !== undefined) {
    teile.push(kachel(
      pz(kpi.bio_anteil), " %",
      /* 03.09.2026 — „in Bio-Bewirtschaftung“ war 288 px bei 261 px
         Platz. Gleiche Aussage, kuerzer. */
      "Bio-Anteil der Agrarfläche",
      `${kpi.bio_jahr} · Platz ${kpi.bio_rang} von ${kpi.bio_anzahl} in Europa`,
      "biolandbau"
    ));
  }

  setzeHtml("kpis", teile.join(""));
}

BIO.baueKpis = baueKpis;
})(window.BIO);
