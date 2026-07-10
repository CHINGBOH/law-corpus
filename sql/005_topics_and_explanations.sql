BEGIN;

CREATE TABLE IF NOT EXISTS doctrine_topics (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  slug text NOT NULL UNIQUE,
  title text NOT NULL UNIQUE,
  pillar_title text NOT NULL,
  question text,
  summary text,
  sort_order int NOT NULL DEFAULT 100,
  status text NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'draft', 'archived')),
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS topic_links (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  topic_id uuid NOT NULL REFERENCES doctrine_topics(id) ON DELETE CASCADE,
  target_type text NOT NULL CHECK (target_type IN (
    'legal_instrument',
    'legal_unit',
    'context_event'
  )),
  target_id uuid NOT NULL,
  role text NOT NULL CHECK (role IN (
    'core',
    'support',
    'background',
    'exception'
  )),
  notes text,
  sort_order int NOT NULL DEFAULT 100,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (topic_id, target_type, target_id, role)
);

CREATE TABLE IF NOT EXISTS plain_explanations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  topic_id uuid REFERENCES doctrine_topics(id) ON DELETE CASCADE,
  target_type text CHECK (target_type IN (
    'legal_instrument',
    'legal_unit',
    'context_event'
  )),
  target_id uuid,
  explanation_type text NOT NULL CHECK (explanation_type IN (
    'plain_language',
    'note',
    'outline',
    'risk',
    'comparison'
  )),
  title text NOT NULL,
  body text NOT NULL,
  source_id uuid REFERENCES sources(id) ON DELETE SET NULL,
  confidence numeric(3,2) NOT NULL DEFAULT 0.80 CHECK (confidence BETWEEN 0 AND 1),
  author text NOT NULL DEFAULT 'codex',
  created_at timestamptz NOT NULL DEFAULT now(),
  CHECK (topic_id IS NOT NULL OR target_id IS NOT NULL)
);

CREATE INDEX IF NOT EXISTS idx_topic_links_topic ON topic_links (topic_id, role, sort_order);
CREATE INDEX IF NOT EXISTS idx_topic_links_target ON topic_links (target_type, target_id);
CREATE INDEX IF NOT EXISTS idx_plain_explanations_topic ON plain_explanations (topic_id, explanation_type);

INSERT INTO legal_units (
  version_id, parent_id, unit_type, unit_number, unit_number_int,
  title, text, canonical_ref, path, order_index, text_hash
) VALUES
  (
    (SELECT id FROM legal_versions WHERE slug = 'cn_civil_code_2020'),
    NULL, 'article', '第六十条', 60, NULL,
    '法人以其全部财产独立承担民事责任。',
    'civil_code:2020:article_60', 'article_60', 60, md5('civil_code:2020:article_60')
  ),
  (
    (SELECT id FROM legal_versions WHERE slug = 'cn_civil_code_2020'),
    NULL, 'article', '第六十一条', 61, NULL,
    '依照法律或者法人章程的规定，代表法人从事民事活动的负责人，为法人的法定代表人。法定代表人以法人名义从事的民事活动，其法律后果由法人承受。法人章程或者法人权力机构对法定代表人代表权的限制，不得对抗善意相对人。',
    'civil_code:2020:article_61', 'article_61', 61, md5('civil_code:2020:article_61')
  ),
  (
    (SELECT id FROM legal_versions WHERE slug = 'cn_civil_code_2020'),
    NULL, 'article', '第八十四条', 84, NULL,
    '营利法人的控股出资人、实际控制人、董事、监事、高级管理人员不得利用其关联关系损害法人的利益；利用关联关系造成法人损失的，应当承担赔偿责任。',
    'civil_code:2020:article_84', 'article_84', 84, md5('civil_code:2020:article_84')
  )
ON CONFLICT (canonical_ref) DO UPDATE SET
  text = EXCLUDED.text;

INSERT INTO doctrine_topics (
  slug, title, pillar_title, question, summary, sort_order, status
) VALUES
  (
    'capital-credit',
    '资本信用',
    '资本信用',
    '公司对外信用究竟靠什么支撑？',
    '围绕认缴、实缴、催缴失权、加速到期、减资与债权人保护组织公司法和相关法律材料。',
    10,
    'active'
  ),
  (
    'corporate-personality',
    '法人独立与人格否认',
    '人格与登记',
    '公司为何能独立承担责任，何时又会被刺破人格外壳？',
    '围绕法人财产独立、股东有限责任、法定代表人和人格否认构造专题。',
    20,
    'active'
  ),
  (
    'registration-publicity',
    '公司登记与公示',
    '人格与登记',
    '公司设立、登记、公示和注销如何形成法律效果？',
    '围绕公司登记章、登记事项、公示和注销程序建立专题。',
    30,
    'active'
  ),
  (
    'creditor-protection',
    '债权人保护',
    '重组与退出',
    '公司运转、减资、合并和资不抵债时，债权人如何被保护？',
    '围绕资本维持、加速到期、减资通知、合并通知和破产进入条件建立专题。',
    40,
    'active'
  ),
  (
    'governance-controls',
    '公司治理与董监高责任',
    '董监高责任',
    '公司内部权力如何分配，经营者又如何被约束？',
    '围绕股东会、董事会、忠实勤勉、关联交易和派生诉讼建立专题。',
    50,
    'active'
  ),
  (
    'capital-market-shares',
    '股份公司与资本市场',
    '股份与融资',
    '股份公司进入资本市场后，公司法与证券法如何衔接？',
    '围绕股份公司治理、公司债券、证券发行和信息披露建立专题。',
    60,
    'active'
  )
ON CONFLICT (slug) DO UPDATE SET
  title = EXCLUDED.title,
  pillar_title = EXCLUDED.pillar_title,
  question = EXCLUDED.question,
  summary = EXCLUDED.summary,
  sort_order = EXCLUDED.sort_order,
  status = EXCLUDED.status;

INSERT INTO topic_links (topic_id, target_type, target_id, role, notes, sort_order) VALUES
  ((SELECT id FROM doctrine_topics WHERE slug = 'capital-credit'), 'legal_instrument', (SELECT id FROM legal_instruments WHERE slug = 'cn_company_law'), 'core', NULL, 10),
  ((SELECT id FROM doctrine_topics WHERE slug = 'capital-credit'), 'legal_instrument', (SELECT id FROM legal_instruments WHERE slug = 'cn_civil_code'), 'support', NULL, 20),
  ((SELECT id FROM doctrine_topics WHERE slug = 'capital-credit'), 'legal_instrument', (SELECT id FROM legal_instruments WHERE slug = 'cn_enterprise_bankruptcy_law'), 'support', NULL, 30),
  ((SELECT id FROM doctrine_topics WHERE slug = 'capital-credit'), 'legal_instrument', (SELECT id FROM legal_instruments WHERE slug = 'cn_market_entity_registration_regulation'), 'support', NULL, 40),
  ((SELECT id FROM doctrine_topics WHERE slug = 'capital-credit'), 'legal_unit', (SELECT id FROM legal_units WHERE canonical_ref = 'company_law:2023:article_47'), 'core', NULL, 50),
  ((SELECT id FROM doctrine_topics WHERE slug = 'capital-credit'), 'legal_unit', (SELECT id FROM legal_units WHERE canonical_ref = 'company_law:2023:article_49'), 'core', NULL, 60),
  ((SELECT id FROM doctrine_topics WHERE slug = 'capital-credit'), 'legal_unit', (SELECT id FROM legal_units WHERE canonical_ref = 'company_law:2023:article_51'), 'core', NULL, 70),
  ((SELECT id FROM doctrine_topics WHERE slug = 'capital-credit'), 'legal_unit', (SELECT id FROM legal_units WHERE canonical_ref = 'company_law:2023:article_52'), 'core', NULL, 80),
  ((SELECT id FROM doctrine_topics WHERE slug = 'capital-credit'), 'legal_unit', (SELECT id FROM legal_units WHERE canonical_ref = 'company_law:2023:article_54'), 'core', NULL, 90),
  ((SELECT id FROM doctrine_topics WHERE slug = 'capital-credit'), 'legal_unit', (SELECT id FROM legal_units WHERE canonical_ref = 'company_law:2023:article_224'), 'support', NULL, 100),
  ((SELECT id FROM doctrine_topics WHERE slug = 'capital-credit'), 'legal_unit', (SELECT id FROM legal_units WHERE canonical_ref = 'civil_code:2020:article_60'), 'support', NULL, 110),
  ((SELECT id FROM doctrine_topics WHERE slug = 'capital-credit'), 'legal_unit', (SELECT id FROM legal_units WHERE canonical_ref = 'bankruptcy_law:2006:article_2'), 'support', NULL, 120),
  ((SELECT id FROM doctrine_topics WHERE slug = 'capital-credit'), 'context_event', (SELECT id FROM context_events WHERE slug = 'cn_registration_capital_reform_2013'), 'background', NULL, 130),
  ((SELECT id FROM doctrine_topics WHERE slug = 'capital-credit'), 'context_event', (SELECT id FROM context_events WHERE slug = 'cn_registered_capital_disorder_2023'), 'background', NULL, 140),

  ((SELECT id FROM doctrine_topics WHERE slug = 'corporate-personality'), 'legal_instrument', (SELECT id FROM legal_instruments WHERE slug = 'cn_company_law'), 'core', NULL, 10),
  ((SELECT id FROM doctrine_topics WHERE slug = 'corporate-personality'), 'legal_instrument', (SELECT id FROM legal_instruments WHERE slug = 'cn_civil_code'), 'support', NULL, 20),
  ((SELECT id FROM doctrine_topics WHERE slug = 'corporate-personality'), 'legal_unit', (SELECT id FROM legal_units WHERE canonical_ref = 'company_law:2023:article_3'), 'core', NULL, 30),
  ((SELECT id FROM doctrine_topics WHERE slug = 'corporate-personality'), 'legal_unit', (SELECT id FROM legal_units WHERE canonical_ref = 'company_law:2023:article_11'), 'support', NULL, 40),
  ((SELECT id FROM doctrine_topics WHERE slug = 'corporate-personality'), 'legal_unit', (SELECT id FROM legal_units WHERE canonical_ref = 'company_law:2023:article_13'), 'support', NULL, 50),
  ((SELECT id FROM doctrine_topics WHERE slug = 'corporate-personality'), 'legal_unit', (SELECT id FROM legal_units WHERE canonical_ref = 'company_law:2023:article_21'), 'support', NULL, 60),
  ((SELECT id FROM doctrine_topics WHERE slug = 'corporate-personality'), 'legal_unit', (SELECT id FROM legal_units WHERE canonical_ref = 'company_law:2023:article_23'), 'core', NULL, 70),
  ((SELECT id FROM doctrine_topics WHERE slug = 'corporate-personality'), 'legal_unit', (SELECT id FROM legal_units WHERE canonical_ref = 'civil_code:2020:article_57'), 'support', NULL, 80),
  ((SELECT id FROM doctrine_topics WHERE slug = 'corporate-personality'), 'legal_unit', (SELECT id FROM legal_units WHERE canonical_ref = 'civil_code:2020:article_58'), 'support', NULL, 90),
  ((SELECT id FROM doctrine_topics WHERE slug = 'corporate-personality'), 'legal_unit', (SELECT id FROM legal_units WHERE canonical_ref = 'civil_code:2020:article_60'), 'support', NULL, 100),
  ((SELECT id FROM doctrine_topics WHERE slug = 'corporate-personality'), 'legal_unit', (SELECT id FROM legal_units WHERE canonical_ref = 'civil_code:2020:article_61'), 'support', NULL, 110),

  ((SELECT id FROM doctrine_topics WHERE slug = 'registration-publicity'), 'legal_instrument', (SELECT id FROM legal_instruments WHERE slug = 'cn_company_law'), 'core', NULL, 10),
  ((SELECT id FROM doctrine_topics WHERE slug = 'registration-publicity'), 'legal_instrument', (SELECT id FROM legal_instruments WHERE slug = 'cn_market_entity_registration_regulation'), 'support', NULL, 20),
  ((SELECT id FROM doctrine_topics WHERE slug = 'registration-publicity'), 'legal_unit', (SELECT id FROM legal_units WHERE canonical_ref = 'company_law:2023:article_29'), 'core', NULL, 30),
  ((SELECT id FROM doctrine_topics WHERE slug = 'registration-publicity'), 'legal_unit', (SELECT id FROM legal_units WHERE canonical_ref = 'company_law:2023:article_30'), 'core', NULL, 40),
  ((SELECT id FROM doctrine_topics WHERE slug = 'registration-publicity'), 'legal_unit', (SELECT id FROM legal_units WHERE canonical_ref = 'company_law:2023:article_32'), 'core', NULL, 50),
  ((SELECT id FROM doctrine_topics WHERE slug = 'registration-publicity'), 'legal_unit', (SELECT id FROM legal_units WHERE canonical_ref = 'company_law:2023:article_33'), 'core', NULL, 60),
  ((SELECT id FROM doctrine_topics WHERE slug = 'registration-publicity'), 'legal_unit', (SELECT id FROM legal_units WHERE canonical_ref = 'registration_regulation:2021:article_8'), 'support', NULL, 70),
  ((SELECT id FROM doctrine_topics WHERE slug = 'registration-publicity'), 'legal_unit', (SELECT id FROM legal_units WHERE canonical_ref = 'registration_regulation:2021:article_31'), 'support', NULL, 80),

  ((SELECT id FROM doctrine_topics WHERE slug = 'creditor-protection'), 'legal_instrument', (SELECT id FROM legal_instruments WHERE slug = 'cn_company_law'), 'core', NULL, 10),
  ((SELECT id FROM doctrine_topics WHERE slug = 'creditor-protection'), 'legal_instrument', (SELECT id FROM legal_instruments WHERE slug = 'cn_enterprise_bankruptcy_law'), 'support', NULL, 20),
  ((SELECT id FROM doctrine_topics WHERE slug = 'creditor-protection'), 'legal_unit', (SELECT id FROM legal_units WHERE canonical_ref = 'company_law:2023:article_23'), 'support', NULL, 30),
  ((SELECT id FROM doctrine_topics WHERE slug = 'creditor-protection'), 'legal_unit', (SELECT id FROM legal_units WHERE canonical_ref = 'company_law:2023:article_54'), 'core', NULL, 40),
  ((SELECT id FROM doctrine_topics WHERE slug = 'creditor-protection'), 'legal_unit', (SELECT id FROM legal_units WHERE canonical_ref = 'company_law:2023:article_220'), 'core', NULL, 50),
  ((SELECT id FROM doctrine_topics WHERE slug = 'creditor-protection'), 'legal_unit', (SELECT id FROM legal_units WHERE canonical_ref = 'company_law:2023:article_224'), 'core', NULL, 60),
  ((SELECT id FROM doctrine_topics WHERE slug = 'creditor-protection'), 'legal_unit', (SELECT id FROM legal_units WHERE canonical_ref = 'bankruptcy_law:2006:article_2'), 'support', NULL, 70),
  ((SELECT id FROM doctrine_topics WHERE slug = 'creditor-protection'), 'legal_unit', (SELECT id FROM legal_units WHERE canonical_ref = 'bankruptcy_law:2006:article_7'), 'support', NULL, 80),

  ((SELECT id FROM doctrine_topics WHERE slug = 'governance-controls'), 'legal_instrument', (SELECT id FROM legal_instruments WHERE slug = 'cn_company_law'), 'core', NULL, 10),
  ((SELECT id FROM doctrine_topics WHERE slug = 'governance-controls'), 'legal_instrument', (SELECT id FROM legal_instruments WHERE slug = 'cn_civil_code'), 'support', NULL, 20),
  ((SELECT id FROM doctrine_topics WHERE slug = 'governance-controls'), 'legal_unit', (SELECT id FROM legal_units WHERE canonical_ref = 'company_law:2023:article_67'), 'core', NULL, 30),
  ((SELECT id FROM doctrine_topics WHERE slug = 'governance-controls'), 'legal_unit', (SELECT id FROM legal_units WHERE canonical_ref = 'company_law:2023:article_181'), 'core', NULL, 40),
  ((SELECT id FROM doctrine_topics WHERE slug = 'governance-controls'), 'legal_unit', (SELECT id FROM legal_units WHERE canonical_ref = 'company_law:2023:article_183'), 'core', NULL, 50),
  ((SELECT id FROM doctrine_topics WHERE slug = 'governance-controls'), 'legal_unit', (SELECT id FROM legal_units WHERE canonical_ref = 'company_law:2023:article_188'), 'core', NULL, 60),
  ((SELECT id FROM doctrine_topics WHERE slug = 'governance-controls'), 'legal_unit', (SELECT id FROM legal_units WHERE canonical_ref = 'company_law:2023:article_189'), 'support', NULL, 70),
  ((SELECT id FROM doctrine_topics WHERE slug = 'governance-controls'), 'legal_unit', (SELECT id FROM legal_units WHERE canonical_ref = 'company_law:2023:article_192'), 'support', NULL, 80),
  ((SELECT id FROM doctrine_topics WHERE slug = 'governance-controls'), 'legal_unit', (SELECT id FROM legal_units WHERE canonical_ref = 'civil_code:2020:article_84'), 'support', NULL, 90),

  ((SELECT id FROM doctrine_topics WHERE slug = 'capital-market-shares'), 'legal_instrument', (SELECT id FROM legal_instruments WHERE slug = 'cn_company_law'), 'core', NULL, 10),
  ((SELECT id FROM doctrine_topics WHERE slug = 'capital-market-shares'), 'legal_instrument', (SELECT id FROM legal_instruments WHERE slug = 'cn_securities_law'), 'support', NULL, 20),
  ((SELECT id FROM doctrine_topics WHERE slug = 'capital-market-shares'), 'legal_instrument', (SELECT id FROM legal_instruments WHERE slug = 'cn_foreign_investment_law'), 'support', NULL, 30),
  ((SELECT id FROM doctrine_topics WHERE slug = 'capital-market-shares'), 'legal_unit', (SELECT id FROM legal_units WHERE canonical_ref = 'company_law:2023:article_112'), 'support', NULL, 40),
  ((SELECT id FROM doctrine_topics WHERE slug = 'capital-market-shares'), 'legal_unit', (SELECT id FROM legal_units WHERE canonical_ref = 'company_law:2023:article_194'), 'core', NULL, 50),
  ((SELECT id FROM doctrine_topics WHERE slug = 'capital-market-shares'), 'legal_unit', (SELECT id FROM legal_units WHERE canonical_ref = 'securities_law:2019:article_2'), 'support', NULL, 60),
  ((SELECT id FROM doctrine_topics WHERE slug = 'capital-market-shares'), 'legal_unit', (SELECT id FROM legal_units WHERE canonical_ref = 'securities_law:2019:article_12'), 'support', NULL, 70),
  ((SELECT id FROM doctrine_topics WHERE slug = 'capital-market-shares'), 'legal_unit', (SELECT id FROM legal_units WHERE canonical_ref = 'securities_law:2019:article_78'), 'support', NULL, 80),
  ((SELECT id FROM doctrine_topics WHERE slug = 'capital-market-shares'), 'legal_unit', (SELECT id FROM legal_units WHERE canonical_ref = 'foreign_investment_law:2019:article_31'), 'support', NULL, 90)
ON CONFLICT (topic_id, target_type, target_id, role) DO UPDATE SET
  notes = EXCLUDED.notes,
  sort_order = EXCLUDED.sort_order;

INSERT INTO plain_explanations (
  topic_id, target_type, target_id, explanation_type, title, body, source_id, confidence, author
) VALUES
  (
    (SELECT id FROM doctrine_topics WHERE slug = 'capital-credit'),
    NULL, NULL, 'plain_language', '资本信用的大白话',
    '这组规则解决的是：公司嘴上写了很多注册资本，但如果长期不缴、随意减资、债权人又追不到钱，公司信用就会被掏空。2013年改革把设立门槛降下来了，2023年修法则把信用约束重新收回来。',
    (SELECT id FROM sources WHERE slug = 'src_company_law_2023_csrc_hubei_materials'),
    0.82,
    'codex'
  ),
  (
    (SELECT id FROM doctrine_topics WHERE slug = 'corporate-personality'),
    NULL, NULL, 'plain_language', '法人独立与人格否认的大白话',
    '正常情况下，公司自己背债，股东只在出资范围内负责；但如果股东把公司当作自己的口袋、故意逃债，法律就会把公司外壳刺破，让股东直接对债权人负责。',
    (SELECT id FROM sources WHERE slug = 'src_civil_code_2020_moj'),
    0.88,
    'codex'
  ),
  (
    (SELECT id FROM doctrine_topics WHERE slug = 'registration-publicity'),
    NULL, NULL, 'outline', '登记公示专题提纲',
    '核心问题包括：设立登记的成立效果、登记事项与公示系统的外部对抗力、营业执照与电子营业执照、注销与终止的衔接。',
    (SELECT id FROM sources WHERE slug = 'src_registration_regulation_2021_gov'),
    0.72,
    'codex'
  ),
  (
    (SELECT id FROM doctrine_topics WHERE slug = 'creditor-protection'),
    NULL, NULL, 'risk', '债权人保护的制度风险',
    '风险集中在三处：认缴资本虚化、减资或合并通知不足、以及公司已经不能清偿到期债务却继续拖延退出。公司法、破产法和登记规则必须联合看。',
    (SELECT id FROM sources WHERE slug = 'src_bankruptcy_law_2006_npc'),
    0.80,
    'codex'
  ),
  (
    (SELECT id FROM doctrine_topics WHERE slug = 'governance-controls'),
    NULL, NULL, 'plain_language', '公司治理与董监高责任的大白话',
    '治理结构管的是谁决策、谁执行、谁监督；责任规则管的是这些人如果利用职权、关联交易或者怠于履职导致公司受损，最后由谁赔。',
    (SELECT id FROM sources WHERE slug = 'src_civil_code_2020_moj'),
    0.84,
    'codex'
  ),
  (
    (SELECT id FROM doctrine_topics WHERE slug = 'capital-market-shares'),
    NULL, NULL, 'comparison', '股份公司与资本市场的接口',
    '公司法主要负责股份公司内部组织和资本工具，证券法继续往外延伸到公开发行、上市交易和信息披露。进入资本市场后，两部法要联动读，不能只看公司法条文。',
    (SELECT id FROM sources WHERE slug = 'src_securities_law_2019_csrc'),
    0.84,
    'codex'
  )
ON CONFLICT DO NOTHING;

COMMIT;
