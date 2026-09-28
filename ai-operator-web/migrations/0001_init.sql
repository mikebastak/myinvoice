-- AI Operátor – schéma odpovídá produkční D1 ai-operator-db (stav 2026-09-28).
-- V produkci je už nasazené; v CI se migrace NESPOUŠTÍ. Slouží pro lokální vývoj (wrangler d1 migrations apply --local).
CREATE TABLE IF NOT EXISTS subscribers (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  email TEXT NOT NULL UNIQUE,
  name TEXT,
  source TEXT NOT NULL DEFAULT 'lead-magnet-15-promptu',
  consent_text TEXT NOT NULL,
  consent_at TEXT NOT NULL,
  ip_hash TEXT,
  user_agent TEXT,
  utm_source TEXT,
  utm_medium TEXT,
  utm_campaign TEXT,
  exported_at TEXT,
  unsubscribed_at TEXT,
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  token TEXT
);
CREATE INDEX IF NOT EXISTS idx_subscribers_created ON subscribers(created_at);
CREATE UNIQUE INDEX IF NOT EXISTS idx_subscribers_token ON subscribers(token);

CREATE TABLE IF NOT EXISTS downloads (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  file TEXT NOT NULL,
  subscriber_id INTEGER,
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);
CREATE INDEX IF NOT EXISTS idx_downloads_subscriber ON downloads(subscriber_id);
