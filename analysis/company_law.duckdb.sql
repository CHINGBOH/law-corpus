-- DuckDB analysis over exported PostgreSQL tables.
--
-- Example export names expected in legal-corpus/exports/:
--   legal_versions.parquet
--   legal_units.parquet
--   context_links.parquet
--   context_events.parquet

CREATE OR REPLACE VIEW legal_versions AS
SELECT *
FROM read_parquet('legal-corpus/exports/legal_versions.parquet');

CREATE OR REPLACE VIEW legal_units AS
SELECT *
FROM read_parquet('legal-corpus/exports/legal_units.parquet');

CREATE OR REPLACE VIEW context_links AS
SELECT *
FROM read_parquet('legal-corpus/exports/context_links.parquet');

CREATE OR REPLACE VIEW context_events AS
SELECT *
FROM read_parquet('legal-corpus/exports/context_events.parquet');

-- Version timeline.
SELECT
  version_sequence,
  version_label,
  action_type,
  adopted_date,
  effective_date,
  status,
  article_count
FROM legal_versions
ORDER BY version_sequence;

-- Article count by version once article extraction is populated.
SELECT
  lv.version_label,
  count(lu.id) FILTER (WHERE lu.unit_type = 'article') AS extracted_articles,
  lv.article_count AS expected_articles
FROM legal_versions lv
LEFT JOIN legal_units lu ON lu.version_id = lv.id
GROUP BY lv.version_label, lv.version_sequence, lv.article_count
ORDER BY lv.version_sequence;

-- Evidence-graded context claims.
SELECT
  relation_type,
  claim_text,
  confidence,
  evidence_level
FROM context_links
WHERE claim_text IS NOT NULL
ORDER BY confidence DESC;
