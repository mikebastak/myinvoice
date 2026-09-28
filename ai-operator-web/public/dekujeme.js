(function () {
  var t = new URLSearchParams(location.search).get('t') || '';
  var a = document.getElementById('dl'), bad = document.getElementById('bad');
  if (/^[a-f0-9]{64}$/.test(t)) {
    a.href = '/api/download?t=' + t;
    a.hidden = false;
  } else {
    bad.hidden = false;
  }
})();
