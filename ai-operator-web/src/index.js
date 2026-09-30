// AI Operátor pro e-shop – lead magnet (landing + opt-in + PDF download + admin export)
// Cloudflare Worker + static assets + D1.
import pdf from '../private/15-promptu-ai-operator.pdf';

// Přesné znění souhlasu u formuláře – ukládá se ke každému kontaktu jako důkaz (GDPR čl. 7 odst. 1).
const CONSENT_TEXT =
  'Souhlasím se zasíláním e-mailů s tipy a nabídkami produktů AI Operátor od OK ENERGO s.r.o. ' +
  'Odhlásit se lze jedním kliknutím v každém e-mailu. Podrobnosti v zásadách ochrany osobních údajů.';
const PDF_FILENAME = '15-promptu-AI-Operator.pdf';
const TOKEN_RE = /^[a-f0-9]{64}$/;
const EMAIL_RE = /^[^\s@<>"',;]+@[^\s@<>"',;]+\.[^\s@<>"',;]{2,}$/;

const CSP = [
  "default-src 'self'",
  "script-src 'self'",
  "style-src 'self'",
  "font-src 'self'",
  "img-src 'self' data:",
  "connect-src 'self'",
  "form-action 'self'",
  "frame-ancestors 'none'",
  "base-uri 'none'",
  "object-src 'none'",
].join('; ');

const SECURITY_HEADERS = {
  'content-security-policy': CSP,
  'x-content-type-options': 'nosniff',
  'referrer-policy': 'no-referrer',
  'x-frame-options': 'DENY',
  'permissions-policy': 'camera=(), microphone=(), geolocation=(), interest-cohort=()',
  'strict-transport-security': 'max-age=31536000; includeSubDomains',
};

function withSecurityHeaders(response) {
  const res = new Response(response.body, response);
  for (const [k, v] of Object.entries(SECURITY_HEADERS)) res.headers.set(k, v);
  return res;
}

function json(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store' },
  });
}

function redirect(location, status = 303) {
  return new Response(null, { status, headers: { location, 'cache-control': 'no-store' } });
}

function randomToken() {
  const bytes = crypto.getRandomValues(new Uint8Array(32));
  return [...bytes].map((b) => b.toString(16).padStart(2, '0')).join('');
}

async function sha256(text) {
  const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(text));
  return new Uint8Array(buf);
}

async function safeEqual(a, b) {
  // Compare digests so timing does not depend on input length or content.
  const [ha, hb] = await Promise.all([sha256(a), sha256(b)]);
  let diff = 0;
  for (let i = 0; i < ha.length; i++) diff |= ha[i] ^ hb[i];
  return diff === 0;
}

async function isAdmin(request, env) {
  if (!env.ADMIN_TOKEN) return false;
  const auth = request.headers.get('authorization') || '';
  let provided = '';
  if (auth.startsWith('Bearer ')) {
    provided = auth.slice(7).trim();
  } else if (auth.startsWith('Basic ')) {
    // Browser prompt: any username, password = ADMIN_TOKEN (handy on a phone).
    try {
      const decoded = atob(auth.slice(6).trim());
      provided = decoded.slice(decoded.indexOf(':') + 1);
    } catch {
      return false;
    }
  }
  return provided !== '' && safeEqual(provided, env.ADMIN_TOKEN);
}

function csvCell(value) {
  let s = value == null ? '' : String(value);
  if (/^[=+\-@\t\r]/.test(s)) s = "'" + s; // CSV/formula injection guard
  return /[",;\r\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
}

async function handleSubscribe(request, env) {
  const ct = request.headers.get('content-type') || '';
  if (!ct.includes('application/x-www-form-urlencoded') && !ct.includes('multipart/form-data')) {
    return json({ ok: false, error: 'unsupported_content_type' }, 415);
  }
  const form = await request.formData();
  const honeypot = (form.get('website') || '').toString();
  const email = (form.get('email') || '').toString().trim().toLowerCase();
  const name = (form.get('name') || '').toString().trim().slice(0, 80);
  const consent = (form.get('consent') || '').toString();

  // Bots filling the hidden field get a plausible redirect and nothing is stored.
  if (honeypot) return redirect('/dekujeme.html');
  if (!EMAIL_RE.test(email) || email.length > 254) return redirect('/?chyba=email#stahnout');
  if (consent !== 'on') return redirect('/?chyba=souhlas#stahnout');

  const utm = (k) => ((form.get(k) || '').toString().trim().slice(0, 100) || null);
  const now = new Date().toISOString();
  const existing = await env.DB.prepare('SELECT id, token FROM subscribers WHERE email = ?1').bind(email).first();
  let token;
  if (existing) {
    token = existing.token && TOKEN_RE.test(existing.token) ? existing.token : randomToken();
    await env.DB.prepare(
      `UPDATE subscribers SET name = COALESCE(NULLIF(?1, ''), name), consent_text = ?2, consent_at = ?3,
              unsubscribed_at = NULL, token = ?4 WHERE id = ?5`
    ).bind(name, CONSENT_TEXT, now, token, existing.id).run();
  } else {
    token = randomToken();
    await env.DB.prepare(
      `INSERT INTO subscribers (email, name, consent_text, consent_at, utm_source, utm_medium, utm_campaign, token, created_at)
       VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?4)`
    ).bind(email, name || null, CONSENT_TEXT, now, utm('utm_source'), utm('utm_medium'), utm('utm_campaign'), token).run();
  }
  return redirect('/dekujeme.html?t=' + token);
}

async function handleDownload(url, env) {
  const token = (url.searchParams.get('t') || '').toLowerCase();
  if (!TOKEN_RE.test(token)) return new Response('Neplatný odkaz ke stažení.', { status: 404 });
  const sub = await env.DB.prepare('SELECT id FROM subscribers WHERE token = ?1').bind(token).first();
  if (!sub) return new Response('Neplatný odkaz ke stažení.', { status: 404 });
  await env.DB.prepare('INSERT INTO downloads (file, subscriber_id, created_at) VALUES (?1, ?2, ?3)')
    .bind(PDF_FILENAME, sub.id, new Date().toISOString()).run();
  return new Response(pdf, {
    headers: {
      'content-type': 'application/pdf',
      'content-disposition': `attachment; filename="${PDF_FILENAME}"`,
      'cache-control': 'private, no-store',
    },
  });
}

async function handleExport(request, env) {
  if (!(await isAdmin(request, env))) {
    return new Response('Unauthorized', {
      status: 401,
      headers: { 'www-authenticate': 'Basic realm="ai-operator-admin", charset="UTF-8"', 'cache-control': 'no-store' },
    });
  }
  const { results } = await env.DB.prepare(
    `SELECT s.id, s.email, s.name, s.source, s.created_at, s.consent_at, s.utm_source, s.utm_medium, s.utm_campaign,
            s.unsubscribed_at,
            COUNT(d.id) AS downloads, MAX(d.created_at) AS last_download
       FROM subscribers s LEFT JOIN downloads d ON d.subscriber_id = s.id
      GROUP BY s.id ORDER BY s.created_at DESC`
  ).all();
  const cols = ['id', 'email', 'name', 'source', 'created_at', 'consent_at', 'utm_source', 'utm_medium', 'utm_campaign',
    'unsubscribed_at', 'downloads', 'last_download'];
  const lines = [cols.join(',')];
  for (const r of results) lines.push(cols.map((c) => csvCell(r[c])).join(','));
  const date = new Date().toISOString().slice(0, 10);
  return new Response('﻿' + lines.join('\r\n') + '\r\n', {
    headers: {
      'content-type': 'text/csv; charset=utf-8',
      'content-disposition': `attachment; filename="ai-operator-kontakty-${date}.csv"`,
      'cache-control': 'no-store',
    },
  });
}

async function route(request, env) {
  const url = new URL(request.url);
  const { pathname } = url;
  const method = request.method;

  if (pathname === '/api/health') {
    if (method !== 'GET' && method !== 'HEAD') return json({ ok: false }, 405);
    try {
      await env.DB.prepare('SELECT 1 FROM subscribers LIMIT 1').first();
      return json({ ok: true });
    } catch {
      return json({ ok: false }, 503);
    }
  }
  if (pathname === '/api/subscribe') {
    if (method !== 'POST') return json({ ok: false, error: 'method_not_allowed' }, 405);
    return handleSubscribe(request, env);
  }
  if (pathname === '/api/download') {
    if (method !== 'GET' && method !== 'HEAD') return json({ ok: false }, 405);
    return handleDownload(url, env);
  }
  if (pathname === '/api/admin/export.csv') {
    if (method !== 'GET') return json({ ok: false }, 405);
    return handleExport(request, env);
  }
  if (pathname.startsWith('/api/')) return json({ ok: false, error: 'not_found' }, 404);

  if (method !== 'GET' && method !== 'HEAD') return new Response('Method Not Allowed', { status: 405 });
  const assetUrl = new URL(url);
  if (pathname === '/' || pathname === '') assetUrl.pathname = '/index.html';
  const res = await env.ASSETS.fetch(new Request(assetUrl, request));
  if (res.status === 404) {
    const nf = await env.ASSETS.fetch(new Request(new URL('/404.html', url), request));
    return new Response(nf.body, { status: 404, headers: nf.headers });
  }
  return res;
}

export default {
  async fetch(request, env) {
    try {
      return withSecurityHeaders(await route(request, env));
    } catch (err) {
      console.error('unhandled', err && err.stack ? err.stack : err);
      return withSecurityHeaders(json({ ok: false, error: 'internal_error' }, 500));
    }
  },
};
