(function () {
  var f = document.getElementById('optin'), m = document.getElementById('msg');
  if (!f || !m) return;
  function show(t) { m.textContent = t; m.hidden = false; }
  var errs = {
    email: 'Zadej platný e-mail.',
    souhlas: 'Pro stažení PDF potvrď souhlas se zasíláním e-mailů.'
  };
  var params = new URLSearchParams(location.search);
  ['utm_source', 'utm_medium', 'utm_campaign'].forEach(function (k) {
    if (f[k] && params.get(k)) f[k].value = params.get(k).slice(0, 100);
  });
  var q = params.get('chyba');
  if (q && errs[q]) show(errs[q]);
  f.addEventListener('submit', function (e) {
    var email = f.email.value.trim();
    if (f.website.value) { e.preventDefault(); return; }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(email)) { e.preventDefault(); show(errs.email); f.email.focus(); return; }
    if (!f.consent.checked) { e.preventDefault(); show(errs.souhlas); return; }
    var b = f.querySelector('button'); if (b) { b.disabled = true; b.textContent = 'Odesílám…'; }
  });
})();
