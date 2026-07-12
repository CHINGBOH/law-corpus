-- Chinese full-text search: replace the 'simple' text-search config (which
-- does not tokenize Chinese at all -- to_tsvector('simple', '法人是...')
-- produces one giant token per clause) with zhparser, a real SCWS-based
-- Chinese word-segmentation parser for Postgres. Fixes /api/search and
-- QUERIES["search"]'s ranking, both previously unable to match Chinese
-- substrings.

BEGIN;

CREATE EXTENSION IF NOT EXISTS zhparser;

CREATE TEXT SEARCH CONFIGURATION chinesecfg (PARSER = zhparser);
ALTER TEXT SEARCH CONFIGURATION chinesecfg
  ADD MAPPING FOR n,v,a,i,e,l,j,m,q,r WITH simple;

-- Rebuild the two FTS indexes from 001_schema.sql against the new config.
-- A functional GIN index is baked to the config used at CREATE time, so the
-- config swap can't be applied to the existing index in place.
DROP INDEX IF EXISTS idx_documents_title_fts;
CREATE INDEX idx_documents_title_fts ON documents
  USING gin (to_tsvector('chinesecfg', coalesce(title,'') || ' ' || coalesce(summary,'')));

DROP INDEX IF EXISTS idx_legal_units_text_fts;
CREATE INDEX idx_legal_units_text_fts ON legal_units
  USING gin (to_tsvector('chinesecfg', coalesce(title,'') || ' ' || coalesce(text,'')));

COMMIT;
