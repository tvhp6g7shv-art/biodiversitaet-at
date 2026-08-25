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

function kachel(wert, einheit, titel, fussnote) {
  return (
    `<div class="viz-kpi">` +
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
      "der Landesfläche steht unter Schutz",
      `${kpi.schutzgebiete_jahr} · ${pz(kpi.schutzgebiete_luecke)} Punkte fehlen auf das Ziel von 30 %`
    ));
  }

  if (kpi.vogel_index !== undefined) {
    teile.push(kachel(
      pz(kpi.vogel_index), "",
      "Bestandsindex der Feld- und Wiesenvögel",
      `${kpi.vogel_jahr} · 1998 = 100`
    ));
  }

  if (kpi.boden_ha_pro_tag !== undefined) {
    teile.push(kachel(
      pz(kpi.boden_ha_pro_tag), " ha",
      "Boden werden pro Tag neu beansprucht",
      `Mittel ${kpi.boden_periode}`
    ));
  }

  if (kpi.rotelisten_aktuell !== undefined) {
    teile.push(kachel(
      `${zahl(kpi.rotelisten_aktuell)}<span class="viz-kpi-von"> von ${zahl(kpi.rotelisten_gesamt)}</span>`, "",
      "Roten Listen sind auf aktuellem Stand",
      `Tiergruppen · Stand Oktober 2025`
    ));
  }

  if (kpi.erhaltung_guenstig !== undefined) {
    teile.push(kachel(
      pz(kpi.erhaltung_guenstig, 0), " %",
      "der Lebensraumtypen sind in gutem Zustand",
      `Artikel 17 FFH · Periode ${kpi.erhaltung_periode}`
    ));
  }

  if (kpi.biotoptypen_anteil !== undefined) {
    teile.push(kachel(
      pz(kpi.biotoptypen_anteil), " %",
      "der Biotoptypen sind gefährdet",
      `${zahl(kpi.biotoptypen_bewertet)} bewertete Typen · Rote Liste`
    ));
  }

  if (kpi.wald_veraenderung !== undefined) {
    teile.push(kachel(
      (kpi.wald_veraenderung > 0 ? "+" : "") + pz(kpi.wald_veraenderung), " %",
      "Waldfläche seit 1990",
      `${kpi.wald_von} bis ${kpi.wald_bis} · Eurostat`
    ));
  }

  if (kpi.bio_anteil !== undefined) {
    teile.push(kachel(
      pz(kpi.bio_anteil), " %",
      "der Agrarfläche werden biologisch bewirtschaftet",
      `${kpi.bio_jahr} · Platz ${kpi.bio_rang} von ${kpi.bio_anzahl} in Europa`
    ));
  }

  setzeHtml("kpis", teile.join(""));
}

BIO.baueKpis = baueKpis;
})(window.BIO);
