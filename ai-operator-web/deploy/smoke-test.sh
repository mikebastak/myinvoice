#!/usr/bin/env bash
# Smoke test produkce/lokálu. Použití: ADMIN_TOKEN=... deploy/smoke-test.sh https://ai-operator-web.<subdomain>.workers.dev
# Výsledky jde do stdout a (v GitHub Actions) do $GITHUB_STEP_SUMMARY. Exit 1 = aspoň jeden test selhal.
set -uo pipefail
BASE="${1:?base URL}"
BASE="${BASE%/}"
EMAIL="${TEST_EMAIL:-test+deploy@okenergo.cz}"
TMP="$(mktemp -d)"
FAIL=0
SUMMARY="${GITHUB_STEP_SUMMARY:-/dev/null}"

report() { # $1=PASS|FAIL $2=test $3=detail
  printf '%s  %s — %s\n' "$1" "$2" "$3"
  printf '| %s | %s | %s |\n' "$([ "$1" = PASS ] && echo ✅ || echo ❌)" "$2" "$3" >> "$SUMMARY"
  [ "$1" = PASS ] || FAIL=1
}
printf '| | Test | Detail |\n|---|---|---|\n' >> "$SUMMARY"

# 1) health
body=$(curl -sS --max-time 20 "$BASE/api/health" || true)
[ "$body" = '{"ok":true}' ] && report PASS "GET /api/health" "$body" || report FAIL "GET /api/health" "body: ${body:0:200}"

# 2) homepage + CSP
code=$(curl -sS --max-time 20 -o /dev/null -D "$TMP/h" -w '%{http_code}' "$BASE/" || true)
csp=$(grep -i '^content-security-policy:' "$TMP/h" | head -1 | tr -d '\r')
if [ "$code" = 200 ] && [ -n "$csp" ]; then report PASS "GET /" "200 + content-security-policy"; else report FAIL "GET /" "status $code, CSP: ${csp:-chybí}"; fi

# 3) subscribe
code=$(curl -sS --max-time 20 -o /dev/null -D "$TMP/s" -w '%{http_code}' \
  --data-urlencode "email=$EMAIL" --data-urlencode "consent=on" "$BASE/api/subscribe" || true)
loc=$(grep -i '^location:' "$TMP/s" | head -1 | sed 's/^[Ll]ocation: *//' | tr -d '\r')
T=$(printf '%s' "$loc" | sed -n 's#^/dekujeme\.html?t=\([a-f0-9]\{64\}\)$#\1#p')
if [ "$code" = 303 ] && [ -n "$T" ]; then report PASS "POST /api/subscribe" "303 → /dekujeme.html?t=…"; else report FAIL "POST /api/subscribe" "status $code, location: ${loc:-chybí}"; fi

# 4) PDF download
if [ -n "$T" ]; then
  res=$(curl -sS --max-time 30 -o "$TMP/f.pdf" -w '%{http_code} %{content_type}' "$BASE/api/download?t=$T" || true)
  magic=$(head -c 5 "$TMP/f.pdf" 2>/dev/null)
  if [[ "$res" == "200 application/pdf"* ]] && [ "$magic" = "%PDF-" ]; then
    report PASS "GET /api/download (PDF)" "200 application/pdf, $(wc -c < "$TMP/f.pdf") B"
  else report FAIL "GET /api/download (PDF)" "$res"; fi
else
  report FAIL "GET /api/download (PDF)" "přeskočeno – chybí token ze subscribe"
fi

# 5) admin export
if [ -n "${ADMIN_TOKEN:-}" ]; then
  code=$(curl -sS --max-time 20 -o "$TMP/e.csv" -D "$TMP/eh" -w '%{http_code}' -H "Authorization: Bearer $ADMIN_TOKEN" "$BASE/api/admin/export.csv" || true)
  ct=$(grep -i '^content-type:' "$TMP/eh" | head -1 | tr -d '\r')
  if [ "$code" = 200 ] && grep -qi 'text/csv' <<<"$ct" && grep -qF "$EMAIL" "$TMP/e.csv"; then
    report PASS "GET /api/admin/export.csv" "200 text/csv, obsahuje $EMAIL ($(($(wc -l < "$TMP/e.csv")-1)) kontaktů)"
  else report FAIL "GET /api/admin/export.csv" "status $code, $ct"; fi
  noauth=$(curl -sS --max-time 20 -o /dev/null -w '%{http_code}' "$BASE/api/admin/export.csv" || true)
  [ "$noauth" = 401 ] && report PASS "export bez tokenu" "401" || report FAIL "export bez tokenu" "status $noauth (čekáno 401)"
else
  # Token se při běžném deployi nerotuje, CI ho proto nezná. Ověříme aspoň, že export bez tokenu nepustí.
  noauth=$(curl -sS --max-time 20 -o /dev/null -w '%{http_code}' "$BASE/api/admin/export.csv" || true)
  [ "$noauth" = 401 ] && report PASS "export bez tokenu" "401 (export s tokenem přeskočen – token se nerotoval)" || report FAIL "export bez tokenu" "status $noauth (čekáno 401)"
fi

rm -rf "$TMP"
exit $FAIL
