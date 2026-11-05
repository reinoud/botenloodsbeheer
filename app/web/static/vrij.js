// Het filter op /vrij werkt direct bij een keuze; zonder script staat de knop in <noscript>.
document.getElementById("bootsoort").addEventListener("change", (e) => e.target.form.submit());
