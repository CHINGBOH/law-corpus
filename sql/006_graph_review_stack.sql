BEGIN;

CREATE TABLE IF NOT EXISTS relation_candidates (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  subject_type text NOT NULL CHECK (subject_type IN (
    'legal_instrument',
    'legal_version',
    'legal_unit',
    'context_event'
  )),
  subject_id uuid NOT NULL,
  object_type text NOT NULL CHECK (object_type IN (
    'legal_instrument',
    'legal_version',
    'legal_unit',
    'context_event'
  )),
  object_id uuid NOT NULL,
  relation_type text NOT NULL CHECK (relation_type IN (
    'based_on',
    'specifies',
    'supplements',
    'limits',
    'constrained_by',
    'same_domain',
    'related_to',
    'interacts_with',
    'policy_background',
    'interpreted_by'
  )),
  claim_text text,
  proposed_source_id uuid REFERENCES sources(id) ON DELETE SET NULL,
  source_excerpt_id uuid REFERENCES source_excerpts(id) ON DELETE SET NULL,
  excerpt_text text,
  confidence numeric(3,2) NOT NULL CHECK (confidence BETWEEN 0 AND 1),
  proposer text NOT NULL DEFAULT 'llm' CHECK (proposer IN ('llm', 'human')),
  status text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'accepted', 'rejected', 'needs_edit')),
  review_note text,
  accepted_relation_id uuid REFERENCES legal_relations(id) ON DELETE SET NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  reviewed_at timestamptz,
  CHECK (
    proposed_source_id IS NOT NULL
    OR source_excerpt_id IS NOT NULL
    OR excerpt_text IS NOT NULL
  )
);

CREATE INDEX IF NOT EXISTS idx_relation_candidates_status
  ON relation_candidates (status, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_relation_candidates_subject
  ON relation_candidates (subject_type, subject_id);

CREATE INDEX IF NOT EXISTS idx_relation_candidates_object
  ON relation_candidates (object_type, object_id);

CREATE OR REPLACE VIEW v_graph_nodes AS
SELECT
  'legal_instrument:' || li.slug AS node_key,
  'legal_instrument'::text AS node_type,
  li.id AS entity_id,
  li.slug AS ref,
  li.short_title AS title,
  li.canonical_title AS subtitle,
  '/instrument?slug=' || li.slug AS href
FROM legal_instruments li
UNION ALL
SELECT
  'legal_version:' || lv.slug AS node_key,
  'legal_version'::text AS node_type,
  lv.id AS entity_id,
  lv.slug AS ref,
  lv.version_label AS title,
  li.short_title || ' · ' || lv.action_type AS subtitle,
  CASE
    WHEN li.slug = 'cn_company_law' THEN '/law?version=' || lv.slug || '&article=1'
    ELSE '/instrument?slug=' || li.slug
  END AS href
FROM legal_versions lv
JOIN legal_instruments li ON li.id = lv.instrument_id
UNION ALL
SELECT
  'legal_unit:' || lu.canonical_ref AS node_key,
  'legal_unit'::text AS node_type,
  lu.id AS entity_id,
  lu.canonical_ref AS ref,
  coalesce(lu.unit_number, lu.canonical_ref) AS title,
  coalesce(left(lu.text, 120), '') AS subtitle,
  CASE
    WHEN li.slug = 'cn_company_law' THEN '/law?version=' || lv.slug || '&article=' || coalesce(lu.unit_number_int::text, '1')
    ELSE '/instrument-reader?slug=' || li.slug || '&unit=' || coalesce(lu.unit_number_int::text, '1')
  END AS href
FROM legal_units lu
JOIN legal_versions lv ON lv.id = lu.version_id
JOIN legal_instruments li ON li.id = lv.instrument_id
WHERE lu.unit_type = 'article'
UNION ALL
SELECT
  'context_event:' || ce.slug AS node_key,
  'context_event'::text AS node_type,
  ce.id AS entity_id,
  ce.slug AS ref,
  ce.title AS title,
  coalesce(ce.event_type, '') || coalesce(' · ' || ce.start_date::text, '') AS subtitle,
  '/api/contexts' AS href
FROM context_events ce;

CREATE OR REPLACE VIEW v_graph_edges AS
SELECT
  'contains:' || li.slug || ':' || lv.slug AS edge_key,
  'legal_instrument:' || li.slug AS from_node_key,
  'legal_version:' || lv.slug AS to_node_key,
  'contains'::text AS relation_type,
  NULL::text AS claim_text,
  1.00::numeric(3,2) AS confidence,
  'structural'::text AS evidence_level,
  NULL::uuid AS source_id
FROM legal_versions lv
JOIN legal_instruments li ON li.id = lv.instrument_id
UNION ALL
SELECT
  'contains:' || lv.slug || ':' || lu.canonical_ref AS edge_key,
  'legal_version:' || lv.slug AS from_node_key,
  'legal_unit:' || lu.canonical_ref AS to_node_key,
  'contains'::text AS relation_type,
  NULL::text AS claim_text,
  1.00::numeric(3,2) AS confidence,
  'structural'::text AS evidence_level,
  NULL::uuid AS source_id
FROM legal_units lu
JOIN legal_versions lv ON lv.id = lu.version_id
WHERE lu.unit_type = 'article'
UNION ALL
SELECT
  'context:' || lv.slug || ':' || ce.slug || ':' || cl.relation_type AS edge_key,
  'legal_version:' || lv.slug AS from_node_key,
  'context_event:' || ce.slug AS to_node_key,
  cl.relation_type,
  cl.claim_text,
  cl.confidence,
  cl.evidence_level,
  cl.source_id
FROM context_links cl
JOIN legal_versions lv
  ON cl.subject_type = 'legal_version' AND cl.subject_id = lv.id
JOIN context_events ce
  ON cl.object_type = 'context_event' AND cl.object_id = ce.id
UNION ALL
SELECT
  'relation:' || lr.id::text AS edge_key,
  CASE
    WHEN lr.subject_type = 'legal_instrument' THEN 'legal_instrument:' || si.slug
    WHEN lr.subject_type = 'legal_version' THEN 'legal_version:' || sv.slug
    WHEN lr.subject_type = 'legal_unit' THEN 'legal_unit:' || su.canonical_ref
    WHEN lr.subject_type = 'context_event' THEN 'context_event:' || sce.slug
  END AS from_node_key,
  CASE
    WHEN lr.object_type = 'legal_instrument' THEN 'legal_instrument:' || oi.slug
    WHEN lr.object_type = 'legal_version' THEN 'legal_version:' || ov.slug
    WHEN lr.object_type = 'legal_unit' THEN 'legal_unit:' || ou.canonical_ref
    WHEN lr.object_type = 'context_event' THEN 'context_event:' || oce.slug
  END AS to_node_key,
  lr.relation_type,
  lr.claim_text,
  lr.confidence,
  lr.evidence_level,
  lr.source_id
FROM legal_relations lr
LEFT JOIN legal_instruments si
  ON lr.subject_type = 'legal_instrument' AND lr.subject_id = si.id
LEFT JOIN legal_versions sv
  ON lr.subject_type = 'legal_version' AND lr.subject_id = sv.id
LEFT JOIN legal_units su
  ON lr.subject_type = 'legal_unit' AND lr.subject_id = su.id
LEFT JOIN context_events sce
  ON lr.subject_type = 'context_event' AND lr.subject_id = sce.id
LEFT JOIN legal_instruments oi
  ON lr.object_type = 'legal_instrument' AND lr.object_id = oi.id
LEFT JOIN legal_versions ov
  ON lr.object_type = 'legal_version' AND lr.object_id = ov.id
LEFT JOIN legal_units ou
  ON lr.object_type = 'legal_unit' AND lr.object_id = ou.id
LEFT JOIN context_events oce
  ON lr.object_type = 'context_event' AND lr.object_id = oce.id;

INSERT INTO source_excerpts (source_id, excerpt_text, locator, quote_limit_ok)
SELECT s.id, v.excerpt_text, v.locator, true
FROM (
  VALUES
    (
      'src_company_law_2023_chinatax',
      '有限责任公司的注册资本为在公司登记机关登记的全体股东认缴的出资额。全体股东认缴的出资额由股东按照公司章程的规定自公司成立之日起五年内缴足。',
      'company_law:2023:article_47'
    ),
    (
      'src_registration_regulation_2021_gov',
      '市场主体的一般登记事项包括名称、主体类型、经营范围、住所、注册资本或者出资额、法定代表人等。',
      'registration_regulation:2021:article_8'
    ),
    (
      'src_civil_code_2020_moj',
      '法人以其全部财产独立承担民事责任。',
      'civil_code:2020:article_60'
    )
) AS v(source_slug, excerpt_text, locator)
JOIN sources s ON s.slug = v.source_slug
WHERE NOT EXISTS (
  SELECT 1 FROM source_excerpts se
  WHERE se.source_id = s.id
    AND se.locator = v.locator
    AND se.excerpt_text = v.excerpt_text
);

INSERT INTO relation_candidates (
  subject_type, subject_id, object_type, object_id, relation_type,
  claim_text, proposed_source_id, source_excerpt_id, excerpt_text,
  confidence, proposer, status
)
SELECT *
FROM (
  SELECT
    'legal_unit'::text,
    (SELECT id FROM legal_units WHERE canonical_ref = 'company_law:2023:article_47'),
    'context_event'::text,
    (SELECT id FROM context_events WHERE slug = 'cn_registration_capital_reform_2013'),
    'policy_background'::text,
    '2013年注册资本登记制度改革是2023年五年缴足规则回收资本信用约束的重要前置背景。',
    (SELECT id FROM sources WHERE slug = 'src_company_law_2023_csrc_hubei_materials'),
    NULL::uuid,
    '2013年注册资本登记制度改革是公司法由实缴走向认缴的重要政策背景。',
    0.88::numeric(3,2),
    'llm'::text,
    'pending'::text
  UNION ALL
  SELECT
    'legal_unit'::text,
    (SELECT id FROM legal_units WHERE canonical_ref = 'company_law:2023:article_47'),
    'legal_unit'::text,
    (SELECT id FROM legal_units WHERE canonical_ref = 'registration_regulation:2021:article_8'),
    'interacts_with'::text,
    '公司法第47条的注册资本与缴足规则，需要通过登记管理规则在登记事项上对外公示。',
    (SELECT id FROM sources WHERE slug = 'src_registration_regulation_2021_gov'),
    (SELECT se.id FROM source_excerpts se
      JOIN sources s ON s.id = se.source_id
      WHERE s.slug = 'src_registration_regulation_2021_gov'
        AND se.locator = 'registration_regulation:2021:article_8'
      LIMIT 1),
    NULL::text,
    0.82::numeric(3,2),
    'llm'::text,
    'pending'::text
  UNION ALL
  SELECT
    'legal_unit'::text,
    (SELECT id FROM legal_units WHERE canonical_ref = 'company_law:2023:article_54'),
    'legal_unit'::text,
    (SELECT id FROM legal_units WHERE canonical_ref = 'civil_code:2020:article_60'),
    'supplements'::text,
    '公司法第54条的出资加速到期责任，落在民法典关于法人以全部财产独立承担民事责任的一般法框架内。',
    (SELECT id FROM sources WHERE slug = 'src_civil_code_2020_moj'),
    (SELECT se.id FROM source_excerpts se
      JOIN sources s ON s.id = se.source_id
      WHERE s.slug = 'src_civil_code_2020_moj'
        AND se.locator = 'civil_code:2020:article_60'
      LIMIT 1),
    NULL::text,
    0.73::numeric(3,2),
    'llm'::text,
    'pending'::text
) seeded (
  subject_type, subject_id, object_type, object_id, relation_type,
  claim_text, proposed_source_id, source_excerpt_id, excerpt_text,
  confidence, proposer, status
)
WHERE seeded.subject_id IS NOT NULL
  AND seeded.object_id IS NOT NULL
  AND NOT EXISTS (
    SELECT 1
    FROM relation_candidates rc
    WHERE rc.subject_type = seeded.subject_type
      AND rc.subject_id = seeded.subject_id
      AND rc.object_type = seeded.object_type
      AND rc.object_id = seeded.object_id
      AND rc.relation_type = seeded.relation_type
      AND rc.status = 'pending'
  );

COMMIT;
