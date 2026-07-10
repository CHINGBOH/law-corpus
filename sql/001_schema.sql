BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE documents (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  slug text NOT NULL UNIQUE,
  doc_type text NOT NULL CHECK (doc_type IN (
    'law',
    'administrative_regulation',
    'department_rule',
    'policy',
    'plan',
    'explanation',
    'draft',
    'speech',
    'article',
    'case',
    'academic',
    'media',
    'archive'
  )),
  jurisdiction text NOT NULL,
  title text NOT NULL,
  title_normalized text NOT NULL,
  issuing_body text,
  publish_date date,
  effective_date date,
  expiry_date date,
  status text NOT NULL DEFAULT 'unknown' CHECK (status IN (
    'effective',
    'expired',
    'draft',
    'historical',
    'unknown'
  )),
  language text NOT NULL DEFAULT 'zh-CN',
  summary text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE sources (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  slug text NOT NULL UNIQUE,
  document_id uuid REFERENCES documents(id) ON DELETE SET NULL,
  source_type text NOT NULL CHECK (source_type IN (
    'official',
    'gazette',
    'government',
    'court',
    'academic',
    'professional',
    'law_firm',
    'media',
    'wiki',
    'archive'
  )),
  title text NOT NULL,
  url text,
  publisher text,
  accessed_at timestamptz NOT NULL DEFAULT now(),
  published_at date,
  storage_uri text,
  sha256 text,
  reliability_tier int NOT NULL CHECK (reliability_tier BETWEEN 1 AND 4),
  notes text,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE source_excerpts (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  source_id uuid NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
  excerpt_text text NOT NULL,
  locator text,
  quote_limit_ok boolean NOT NULL DEFAULT false,
  extracted_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE legal_instruments (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  slug text NOT NULL UNIQUE,
  canonical_title text NOT NULL,
  short_title text NOT NULL,
  jurisdiction text NOT NULL,
  instrument_type text NOT NULL CHECK (instrument_type IN (
    'law',
    'administrative_regulation',
    'department_rule',
    'judicial_interpretation',
    'policy'
  )),
  subject_area text NOT NULL,
  first_enacted_date date,
  notes text,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE legal_versions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  instrument_id uuid NOT NULL REFERENCES legal_instruments(id) ON DELETE CASCADE,
  slug text NOT NULL UNIQUE,
  version_label text NOT NULL,
  version_sequence int NOT NULL,
  action_type text NOT NULL CHECK (action_type IN ('enacted', 'amended', 'revised')),
  adopted_date date,
  promulgated_date date,
  effective_date date NOT NULL,
  status text NOT NULL CHECK (status IN ('historical', 'current')),
  chapter_count int,
  article_count int,
  official_source_id uuid REFERENCES sources(id) ON DELETE SET NULL,
  xml_uri text,
  raw_text_uri text,
  notes text,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (instrument_id, version_sequence),
  UNIQUE (instrument_id, version_label)
);

CREATE TABLE legal_units (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  version_id uuid NOT NULL REFERENCES legal_versions(id) ON DELETE CASCADE,
  parent_id uuid REFERENCES legal_units(id) ON DELETE CASCADE,
  unit_type text NOT NULL CHECK (unit_type IN (
    'part',
    'chapter',
    'section',
    'article',
    'paragraph',
    'item',
    'subitem'
  )),
  unit_number text,
  unit_number_int int,
  title text,
  text text,
  canonical_ref text NOT NULL UNIQUE,
  path text NOT NULL,
  order_index int NOT NULL,
  text_hash text,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (version_id, path),
  UNIQUE (version_id, order_index)
);

CREATE TABLE version_events (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  instrument_id uuid NOT NULL REFERENCES legal_instruments(id) ON DELETE CASCADE,
  legal_version_id uuid REFERENCES legal_versions(id) ON DELETE SET NULL,
  event_type text NOT NULL CHECK (event_type IN (
    'enactment',
    'amendment',
    'revision',
    'draft_review',
    'promulgation',
    'effective'
  )),
  event_date date NOT NULL,
  title text NOT NULL,
  description text,
  source_id uuid REFERENCES sources(id) ON DELETE SET NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (instrument_id, event_type, event_date, title)
);

CREATE TABLE unit_mappings (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  from_unit_id uuid REFERENCES legal_units(id) ON DELETE CASCADE,
  to_unit_id uuid REFERENCES legal_units(id) ON DELETE CASCADE,
  mapping_type text NOT NULL CHECK (mapping_type IN (
    'unchanged',
    'modified',
    'split',
    'merged',
    'deleted',
    'added',
    'renumbered'
  )),
  confidence numeric(3,2) NOT NULL CHECK (confidence BETWEEN 0 AND 1),
  evidence_source_id uuid REFERENCES sources(id) ON DELETE SET NULL,
  notes text,
  created_at timestamptz NOT NULL DEFAULT now(),
  CHECK (from_unit_id IS NOT NULL OR to_unit_id IS NOT NULL)
);

CREATE TABLE context_events (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  slug text NOT NULL UNIQUE,
  event_type text NOT NULL CHECK (event_type IN (
    'policy',
    'economic',
    'political',
    'legislative',
    'reform',
    'comparative_law',
    'historical_origin'
  )),
  title text NOT NULL,
  start_date date,
  end_date date,
  jurisdiction text NOT NULL,
  description text,
  source_id uuid REFERENCES sources(id) ON DELETE SET NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE context_links (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  subject_type text NOT NULL CHECK (subject_type IN (
    'legal_version',
    'legal_unit',
    'document',
    'context_event'
  )),
  subject_id uuid NOT NULL,
  object_type text NOT NULL CHECK (object_type IN (
    'document',
    'context_event',
    'source',
    'legal_version',
    'legal_unit'
  )),
  object_id uuid NOT NULL,
  relation_type text NOT NULL CHECK (relation_type IN (
    'background_of',
    'caused_by',
    'influenced_by',
    'explained_by',
    'implements',
    'responds_to',
    'compared_with'
  )),
  claim_text text,
  confidence numeric(3,2) NOT NULL CHECK (confidence BETWEEN 0 AND 1),
  evidence_level text NOT NULL CHECK (evidence_level IN (
    'official',
    'academic',
    'professional',
    'secondary',
    'unverified'
  )),
  source_id uuid REFERENCES sources(id) ON DELETE RESTRICT,
  notes text,
  created_at timestamptz NOT NULL DEFAULT now(),
  CHECK (claim_text IS NULL OR source_id IS NOT NULL),
  CHECK (evidence_level <> 'unverified' OR confidence <= 0.50),
  UNIQUE (subject_type, subject_id, object_type, object_id, relation_type, claim_text)
);

CREATE TABLE annotations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  target_type text NOT NULL CHECK (target_type IN (
    'legal_version',
    'legal_unit',
    'context_event',
    'source',
    'document'
  )),
  target_id uuid NOT NULL,
  annotation_type text NOT NULL CHECK (annotation_type IN (
    'note',
    'question',
    'interpretation',
    'todo',
    'correction'
  )),
  body text NOT NULL,
  author text NOT NULL DEFAULT 'l',
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE citations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  from_type text NOT NULL CHECK (from_type IN (
    'legal_unit',
    'legal_version',
    'document',
    'context_event'
  )),
  from_id uuid NOT NULL,
  to_type text NOT NULL CHECK (to_type IN (
    'legal_unit',
    'legal_version',
    'document',
    'source',
    'context_event'
  )),
  to_id uuid NOT NULL,
  citation_type text NOT NULL CHECK (citation_type IN (
    'cites',
    'interprets',
    'applies',
    'amends',
    'explains',
    'references'
  )),
  source_id uuid REFERENCES sources(id) ON DELETE SET NULL,
  notes text,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE tags (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL UNIQUE,
  tag_type text NOT NULL CHECK (tag_type IN (
    'topic',
    'institution',
    'doctrine',
    'policy_goal',
    'legal_concept'
  ))
);

CREATE TABLE taggings (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tag_id uuid NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
  target_type text NOT NULL CHECK (target_type IN (
    'legal_version',
    'legal_unit',
    'context_event',
    'source',
    'document'
  )),
  target_id uuid NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tag_id, target_type, target_id)
);

CREATE INDEX idx_documents_type_date ON documents (doc_type, publish_date);
CREATE INDEX idx_sources_document_id ON sources (document_id);
CREATE INDEX idx_sources_reliability ON sources (reliability_tier, source_type);
CREATE INDEX idx_legal_versions_instrument ON legal_versions (instrument_id, version_sequence);
CREATE INDEX idx_legal_units_version_type ON legal_units (version_id, unit_type, order_index);
CREATE INDEX idx_legal_units_ref ON legal_units (canonical_ref);
CREATE INDEX idx_context_events_type_date ON context_events (event_type, start_date);
CREATE INDEX idx_context_links_subject ON context_links (subject_type, subject_id);
CREATE INDEX idx_context_links_object ON context_links (object_type, object_id);
CREATE INDEX idx_context_links_relation ON context_links (relation_type, evidence_level, confidence);

CREATE INDEX idx_documents_title_fts
  ON documents USING gin (to_tsvector('simple', coalesce(title, '') || ' ' || coalesce(summary, '')));

CREATE INDEX idx_legal_units_text_fts
  ON legal_units USING gin (to_tsvector('simple', coalesce(title, '') || ' ' || coalesce(text, '')));

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS trigger AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_documents_updated_at
BEFORE UPDATE ON documents
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE VIEW v_company_law_versions AS
SELECT
  li.short_title,
  lv.slug,
  lv.version_label,
  lv.version_sequence,
  lv.action_type,
  lv.adopted_date,
  lv.effective_date,
  lv.status,
  lv.chapter_count,
  lv.article_count,
  s.title AS official_source_title,
  s.url AS official_source_url
FROM legal_versions lv
JOIN legal_instruments li ON li.id = lv.instrument_id
LEFT JOIN sources s ON s.id = lv.official_source_id
WHERE li.slug = 'cn_company_law'
ORDER BY lv.version_sequence;

CREATE VIEW v_context_claims AS
SELECT
  cl.subject_type,
  cl.subject_id,
  cl.relation_type,
  cl.claim_text,
  cl.confidence,
  cl.evidence_level,
  s.title AS source_title,
  s.url AS source_url
FROM context_links cl
JOIN sources s ON s.id = cl.source_id
WHERE cl.claim_text IS NOT NULL;

COMMIT;
