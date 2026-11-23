// Filter zonder knop (#380): een keuze of het typen ververst alleen de lijst, niet de pagina.
// Zonder script blijft de knop in de HTML staan en werkt het formulier als gewone GET.
(function () {
  const MIN_TEKENS = 3;
  const PAUZE_MS = 300;
  const form = document.querySelector("form[data-lijstfilter]");
  const deel = document.querySelector("[data-lijstdeel]");
  const status = document.querySelector("[data-lijststatus]");
  if (!form || !deel || !status) return;

  const zoek = form.elements.zoek;
  let timer;
  let aanvraag;

  // De URL is die van het formulier; onder het minimum geldt de zoekterm niet.
  function adres() {
    const params = new URLSearchParams(new FormData(form));
    if (zoek && zoek.value.trim().length < MIN_TEKENS) params.set("zoek", "");
    return form.getAttribute("action") + "?" + params;
  }

  let laatste = adres();

  async function vernieuw() {
    clearTimeout(timer);
    const url = adres();
    if (url === laatste) return;
    laatste = url;
    if (aanvraag) aanvraag.abort();
    aanvraag = new AbortController();
    try {
      const r = await fetch(url, { credentials: "same-origin", signal: aanvraag.signal });
      const nieuw = new DOMParser().parseFromString(await r.text(), "text/html").querySelector("[data-lijstdeel]");
      // Een fout of een inlogscherm (verlopen sessie) heeft geen lijst: laad de pagina gewoon.
      if (!r.ok || !nieuw) {
        window.location.assign(url);
        return;
      }
      const melding = nieuw.querySelector(".bl-aantal, .ds-notice__body");
      // Eerst leeg: een gelijke tekst wordt anders niet opnieuw voorgelezen.
      status.textContent = "";
      status.textContent = melding ? melding.textContent.trim() : "";
      deel.replaceChildren(...nieuw.childNodes);
      history.replaceState(null, "", url);
    } catch (e) {
      if (e.name !== "AbortError") window.location.assign(url);
    }
  }

  form.querySelector('button[type="submit"]').hidden = true;
  const hint = form.querySelector("[data-zoekhint]");
  if (hint) {
    hint.hidden = false;
    zoek.setAttribute("aria-describedby", hint.id);
  }

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    vernieuw();
  });
  form.addEventListener("change", function (e) {
    if (e.target.tagName === "SELECT") vernieuw();
  });
  if (zoek) {
    zoek.addEventListener("input", function () {
      clearTimeout(timer);
      timer = setTimeout(vernieuw, PAUZE_MS);
    });
  }
})();
