-- These queries are intended to be run after 001_schema.sql and
-- 002_seed_company_law.sql. They should return the expected counts/rows noted
-- in comments.

-- Expected: 7
SELECT count(*) AS company_law_version_count
FROM legal_versions lv
JOIN legal_instruments li ON li.id = lv.instrument_id
WHERE li.slug = 'cn_company_law';

-- Expected: one row, cn_company_law_2023
SELECT slug, version_label, status
FROM legal_versions
WHERE status = 'current';

-- Expected: no rows. Claims must have source/evidence.
SELECT id, claim_text
FROM context_links
WHERE claim_text IS NOT NULL
  AND (source_id IS NULL OR evidence_level IS NULL OR confidence IS NULL);

-- Expected: at least one unverified Singapore influence claim, confidence <= 0.50.
SELECT relation_type, claim_text, confidence, evidence_level
FROM v_context_claims
WHERE claim_text ILIKE '%新加坡%';

-- Expected: policy/history context linked to 2013 and 2023 versions.
SELECT
  lv.version_label,
  ce.event_type,
  ce.title,
  cl.relation_type,
  cl.confidence,
  cl.evidence_level
FROM context_links cl
JOIN legal_versions lv ON cl.subject_type = 'legal_version' AND cl.subject_id = lv.id
JOIN context_events ce ON cl.object_type = 'context_event' AND cl.object_id = ce.id
WHERE lv.slug IN ('cn_company_law_2013', 'cn_company_law_2023')
ORDER BY lv.version_sequence, ce.start_date NULLS LAST;

-- Expected article counts by version after running
-- scripts/import_company_law_articles.py:
-- 1993=230, 1999=230, 2004=230, 2005=219, 2013=218, 2018=218, 2023=266.
SELECT
  lv.slug,
  lv.article_count AS expected_articles,
  count(lu.id) FILTER (WHERE lu.unit_type = 'article') AS actual_articles
FROM legal_versions lv
LEFT JOIN legal_units lu ON lu.version_id = lv.id
GROUP BY lv.slug, lv.version_sequence, lv.article_count
ORDER BY lv.version_sequence;

-- Expected: 8 legal domains after 004_legal_system_base.sql.
SELECT count(*) AS legal_domain_count
FROM legal_domains;

-- Expected: at least 10 instruments including company law and related laws.
SELECT count(*) AS legal_instrument_count
FROM legal_instruments;

-- Expected: company law should relate to constitution, civil code, securities law,
-- enterprise bankruptcy law, market entity registration regulation, state-owned
-- assets law, foreign investment law, and key policy background events.
SELECT relation_type, object_type, claim_text, confidence, evidence_level
FROM legal_relations lr
JOIN legal_instruments li
  ON lr.subject_type = 'legal_instrument' AND lr.subject_id = li.id
WHERE li.slug = 'cn_company_law'
ORDER BY confidence DESC, relation_type;

-- Expected: at least 6 doctrine topics after 005_topics_and_explanations.sql.
SELECT count(*) AS doctrine_topic_count
FROM doctrine_topics;

-- Expected: capital-credit topic should have core company law units and at least
-- one background event.
SELECT tl.role, tl.target_type, count(*) AS row_count
FROM topic_links tl
JOIN doctrine_topics dt ON dt.id = tl.topic_id
WHERE dt.slug = 'capital-credit'
GROUP BY tl.role, tl.target_type
ORDER BY tl.role, tl.target_type;

-- Expected: plain explanations should exist for each seeded topic.
SELECT dt.slug, count(pe.id) AS explanation_count
FROM doctrine_topics dt
LEFT JOIN plain_explanations pe ON pe.topic_id = dt.id
GROUP BY dt.slug, dt.sort_order
ORDER BY dt.sort_order;

-- Expected: at least 3 seeded relation candidates after 006_graph_review_stack.sql.
SELECT status, count(*) AS candidate_count
FROM relation_candidates
GROUP BY status
ORDER BY status;

-- Expected: graph views should project nodes and edges.
SELECT
  (SELECT count(*) FROM v_graph_nodes) AS graph_node_count,
  (SELECT count(*) FROM v_graph_edges) AS graph_edge_count;

-- Expected: source excerpts should exist for at least company law 2023,
-- registration regulation 2021, and civil code 2020.
SELECT s.slug, count(se.id) AS excerpt_count
FROM sources s
LEFT JOIN source_excerpts se ON se.source_id = s.id
WHERE s.slug IN (
  'src_company_law_2023_chinatax',
  'src_registration_regulation_2021_gov',
  'src_civil_code_2020_moj'
)
GROUP BY s.slug
ORDER BY s.slug;
