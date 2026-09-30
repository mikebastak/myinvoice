# AI Operátor pro e-shop – web

Landing page „15 promptů na produktové popisy a překlady“ + opt-in + stažení PDF + admin export.
Cloudflare Worker (statické assety + API) nad D1 `ai-operator-db`.

| Endpoint | Popis |
|---|---|
| `GET /api/health` | `{"ok":true}` pokud odpovídá D1 |
| `POST /api/subscribe` | form: `email`, `consent=on`, volitelně `name`, `utm_*` → `303 /dekujeme.html?t=<token>` |
| `GET /api/download?t=<token>` | PDF (`application/pdf`), zapíše řádek do `downloads` |
| `GET /api/admin/export.csv` | CSV kontaktů; `Authorization: Bearer <ADMIN_TOKEN>` nebo v prohlížeči Basic auth (jméno libovolné, heslo = token) |

Design: Plus Jakarta Sans + JetBrains Mono (OFL), self-hosted v `public/fonts` – žádné volání Google Fonts.

Bezpečnost: CSP bez inline skriptů/stylů, `no-referrer` (token z URL neuteče), honeypot, ochrana proti CSV injection,
porovnání admin tokenu v konstantním čase, PDF není veřejný asset (je zabalené ve Workeru).

## Nasazení

Automaticky přes GitHub Actions (`.github/workflows/ai-operator-deploy.yml`) při pushi do větve s tímto projektem
nebo ručně (Run workflow). Potřebné repo secrets: `CLOUDFLARE_API_TOKEN` (šablona *Edit Cloudflare Workers*
+ Account › D1 › Edit), volitelně `CLOUDFLARE_ACCOUNT_ID`.

Workflow: ověří D1 a schéma (migrace nespouští) → `wrangler deploy` → `ADMIN_TOKEN` ponechá (nový jen když chybí nebo při ručním spuštění s `rotate_admin_token`)
a nastaví ho jako secret (do logu jde jen zašifrovaný veřejným klíčem `deploy/admin-token.pub.pem`)
→ smoke test (`deploy/smoke-test.sh`) → smaže testovací kontakt.

Ručně (Mac):
```bash
npm install
npx wrangler login
npx wrangler deploy
TOKEN=$(openssl rand -hex 32)
printf '%s' "$TOKEN" | npx wrangler secret put ADMIN_TOKEN
security add-generic-password -a ai-operator -s ai-operator-admin -w "$TOKEN"
ADMIN_TOKEN="$TOKEN" deploy/smoke-test.sh https://ai-operator-web.<subdomain>.workers.dev
```

## Vývoj
```bash
npx wrangler d1 migrations apply ai-operator-db --local
echo 'ADMIN_TOKEN=dev' > .dev.vars && npx wrangler dev
npm run pdf   # přegeneruje private/15-promptu-ai-operator.pdf (python3 + reportlab)
```

Otevřené body: doplnit `[DOPLNIT]` v patičce, zásadách a obchodních podmínkách (rejstříkový soud/vložka, kontaktní e-mail);
napojit e-mailový nástroj (Ecomail/MailerLite) – zatím se kontakty jen ukládají do D1 a exportují do CSV.
