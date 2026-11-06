// Passkey registreren en inloggen (ADR-001). Gebruikt de JSON-helpers van WebAuthn Level 3.
(function () {
  const csrf = document.querySelector('meta[name="csrf-token"]').content;

  async function post(url, data) {
    const r = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRFToken": csrf },
      body: JSON.stringify(data || {}),
      credentials: "same-origin",
    });
    const body = await r.json().catch(() => ({}));
    // Een te oude inlog stuurt de server terug naar het inlogscherm (ADR-001).
    if (r.status === 401 && body.url) window.location.assign(body.url);
    if (!r.ok) throw new Error(body.fout || "Er ging iets mis. Probeer het opnieuw.");
    return body;
  }

  function toon(fout) {
    const el = document.getElementById("passkey-fout");
    el.textContent = fout;
    el.parentElement.hidden = false;
  }

  function koppel(id, vraag) {
    const knop = document.getElementById(id);
    if (!knop) return;
    if (!window.PublicKeyCredential || !PublicKeyCredential.parseCreationOptionsFromJSON) {
      knop.disabled = true;
      toon("Deze browser ondersteunt geen passkeys. Gebruik wachtwoord en code.");
      return;
    }
    knop.addEventListener("click", async () => {
      knop.disabled = true;
      try {
        const opties = await post(knop.dataset.opties);
        const credential = await vraag(opties);
        const antwoord = await post(knop.dataset.verifieer, credential.toJSON());
        window.location.assign(antwoord.url);
      } catch (e) {
        toon(e.name === "NotAllowedError" ? "Afgebroken of niet toegestaan." : e.message);
        knop.disabled = false;
      }
    });
  }

  koppel("passkey-registreren", (o) =>
    navigator.credentials.create({ publicKey: PublicKeyCredential.parseCreationOptionsFromJSON(o) }));
  koppel("passkey-inloggen", (o) =>
    navigator.credentials.get({ publicKey: PublicKeyCredential.parseRequestOptionsFromJSON(o) }));
})();
