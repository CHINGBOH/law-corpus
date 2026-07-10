BEGIN;

CREATE TABLE IF NOT EXISTS legal_domains (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  slug text NOT NULL UNIQUE,
  name text NOT NULL UNIQUE,
  description text,
  sort_order int NOT NULL DEFAULT 100,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS instrument_domains (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  instrument_id uuid NOT NULL REFERENCES legal_instruments(id) ON DELETE CASCADE,
  domain_id uuid NOT NULL REFERENCES legal_domains(id) ON DELETE CASCADE,
  is_primary boolean NOT NULL DEFAULT false,
  notes text,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (instrument_id, domain_id)
);

CREATE TABLE IF NOT EXISTS legal_relations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  subject_type text NOT NULL CHECK (subject_type IN (
    'legal_instrument',
    'legal_version',
    'legal_unit',
    'legal_domain',
    'document',
    'context_event'
  )),
  subject_id uuid NOT NULL,
  object_type text NOT NULL CHECK (object_type IN (
    'legal_instrument',
    'legal_version',
    'legal_unit',
    'legal_domain',
    'document',
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
  source_id uuid REFERENCES sources(id) ON DELETE SET NULL,
  confidence numeric(3,2) NOT NULL CHECK (confidence BETWEEN 0 AND 1),
  evidence_level text NOT NULL CHECK (evidence_level IN (
    'official',
    'academic',
    'professional',
    'secondary',
    'unverified'
  )),
  notes text,
  created_at timestamptz NOT NULL DEFAULT now(),
  CHECK (evidence_level <> 'unverified' OR confidence <= 0.50),
  UNIQUE (subject_type, subject_id, object_type, object_id, relation_type)
);

CREATE INDEX IF NOT EXISTS idx_instrument_domains_instrument ON instrument_domains (instrument_id);
CREATE INDEX IF NOT EXISTS idx_instrument_domains_domain ON instrument_domains (domain_id);
CREATE INDEX IF NOT EXISTS idx_legal_relations_subject ON legal_relations (subject_type, subject_id);
CREATE INDEX IF NOT EXISTS idx_legal_relations_object ON legal_relations (object_type, object_id);
CREATE INDEX IF NOT EXISTS idx_legal_relations_type ON legal_relations (relation_type, evidence_level, confidence);

INSERT INTO legal_domains (slug, name, description, sort_order) VALUES
  ('constitutional-foundation', '宪法基础', '社会主义市场经济、财产权和基本经济制度层面的上位基础。', 10),
  ('civil-law-foundation', '民法基础', '法人、民事主体、财产权、责任承担等一般法基础。', 20),
  ('commercial-organization', '商事组织法', '公司、合伙、个人独资等市场主体组织法。', 30),
  ('capital-market', '资本市场法', '股份发行、证券交易、信息披露和上市公司治理。', 40),
  ('insolvency-exit', '破产与退出', '债权人保护、破产清算、市场退出。', 50),
  ('registration-supervision', '登记与监管', '市场主体设立、变更、注销、公示与监管。', 60),
  ('state-owned-assets', '国资监管', '国家出资公司和国有资产监督管理。', 70),
  ('foreign-investment', '外商投资', '外商投资准入、组织形态和治理衔接。', 80)
ON CONFLICT (slug) DO UPDATE SET
  name = EXCLUDED.name,
  description = EXCLUDED.description,
  sort_order = EXCLUDED.sort_order;

INSERT INTO sources (
  slug, source_type, title, url, publisher, published_at,
  reliability_tier, notes
) VALUES
  (
    'src_constitution_2018_npc',
    'official',
    '中华人民共和国宪法（2018修正）',
    'https://www.gov.cn/xinwen/2018-03/22/content_5276318.htm',
    '中国政府网',
    '2018-03-22',
    1,
    '现行宪法修正案公开文本。'
  ),
  (
    'src_civil_code_2020_moj',
    'official',
    '中华人民共和国民法典',
    'https://www.moj.gov.cn/pub/sfbgw/zwgkztzl/2025nianzhuanti/2025mfdxcy/2025mfdxcy_mfdql/202505/t20250507_518708.html',
    '中华人民共和国司法部',
    '2025-05-07',
    1,
    '司法部转载现行民法典全文。'
  ),
  (
    'src_securities_law_2019_csrc',
    'official',
    '中华人民共和国证券法',
    'https://neris.csrc.gov.cn/falvfagui/rdqsHeader/mainbody?navbarId=1&secFutrsLawId=0fc431a2a10b47909beef058f6ac3335',
    '中国证券监督管理委员会',
    '2019-12-28',
    1,
    '现行证券法公开文本。'
  ),
  (
    'src_bankruptcy_law_2006_npc',
    'official',
    '中华人民共和国企业破产法',
    'https://www.gov.cn/flfg/2006-08/27/content_371296.htm',
    '中国政府网',
    '2006-08-27',
    1,
    '企业破产法公开文本。'
  ),
  (
    'src_registration_regulation_2021_gov',
    'official',
    '中华人民共和国市场主体登记管理条例',
    'https://www.gov.cn/zhengce/content/2021-07/27/content_5627763.htm',
    '中国政府网',
    '2021-07-27',
    1,
    '国务院令第746号。'
  ),
  (
    'src_state_assets_law_2008_npc',
    'official',
    '中华人民共和国企业国有资产法',
    'https://www.gov.cn/flfg/2008-10/30/content_1138549.htm',
    '中国政府网',
    '2008-10-30',
    1,
    '企业国有资产法公开文本。'
  ),
  (
    'src_foreign_investment_law_2019_npc',
    'official',
    '中华人民共和国外商投资法',
    'https://www.gov.cn/xinwen/2019-03/20/content_5375360.htm',
    '中国政府网',
    '2019-03-20',
    1,
    '外商投资法公开文本。'
  ),
  (
    'src_partnership_law_2006_npc',
    'official',
    '中华人民共和国合伙企业法',
    'https://www.gov.cn/flfg/2006-08/28/content_371299.htm',
    '中国政府网',
    '2006-08-28',
    1,
    '合伙企业法公开文本。'
  ),
  (
    'src_sole_proprietorship_law_1999_npc',
    'official',
    '中华人民共和国个人独资企业法',
    'https://www.gov.cn/banshi/2005-08/22/content_24956.htm',
    '中国政府网',
    '2005-08-22',
    2,
    '政府网法条转载文本，后续可补国家法律法规数据库来源。'
  )
ON CONFLICT (slug) DO UPDATE SET
  title = EXCLUDED.title,
  url = EXCLUDED.url,
  publisher = EXCLUDED.publisher,
  published_at = EXCLUDED.published_at,
  reliability_tier = EXCLUDED.reliability_tier,
  notes = EXCLUDED.notes;

INSERT INTO legal_instruments (
  slug, canonical_title, short_title, jurisdiction, instrument_type,
  subject_area, first_enacted_date, notes
) VALUES
  (
    'cn_constitution',
    '中华人民共和国宪法',
    '宪法',
    'CN_MAINLAND',
    'law',
    'constitutional-foundation',
    '1982-12-04',
    '当前先录入现行体系关系所需的现行版本与关键条文。'
  ),
  (
    'cn_civil_code',
    '中华人民共和国民法典',
    '民法典',
    'CN_MAINLAND',
    'law',
    'civil-law-foundation',
    '2020-05-28',
    '当前先录入总则编法人制度与责任承担相关关键条文。'
  ),
  (
    'cn_securities_law',
    '中华人民共和国证券法',
    '证券法',
    'CN_MAINLAND',
    'law',
    'capital-market',
    '1998-12-29',
    '当前先录入上市公司、证券发行与信息披露相关关键条文。'
  ),
  (
    'cn_enterprise_bankruptcy_law',
    '中华人民共和国企业破产法',
    '企业破产法',
    'CN_MAINLAND',
    'law',
    'insolvency-exit',
    '2006-08-27',
    '当前先录入债权人保护与破产程序关键条文。'
  ),
  (
    'cn_market_entity_registration_regulation',
    '中华人民共和国市场主体登记管理条例',
    '市场主体登记管理条例',
    'CN_MAINLAND',
    'administrative_regulation',
    'registration-supervision',
    '2021-07-27',
    '当前先录入登记、公示、注销相关关键条文。'
  ),
  (
    'cn_state_owned_assets_law',
    '中华人民共和国企业国有资产法',
    '企业国有资产法',
    'CN_MAINLAND',
    'law',
    'state-owned-assets',
    '2008-10-28',
    '当前先录入国家出资企业治理相关关键条文。'
  ),
  (
    'cn_foreign_investment_law',
    '中华人民共和国外商投资法',
    '外商投资法',
    'CN_MAINLAND',
    'law',
    'foreign-investment',
    '2019-03-15',
    '当前先录入组织形式和准入衔接关键条文。'
  ),
  (
    'cn_partnership_enterprise_law',
    '中华人民共和国合伙企业法',
    '合伙企业法',
    'CN_MAINLAND',
    'law',
    'commercial-organization',
    '1997-02-23',
    '作为并列商事组织法节点。'
  ),
  (
    'cn_sole_proprietorship_law',
    '中华人民共和国个人独资企业法',
    '个人独资企业法',
    'CN_MAINLAND',
    'law',
    'commercial-organization',
    '1999-08-30',
    '作为并列商事组织法节点。'
  )
ON CONFLICT (slug) DO UPDATE SET
  canonical_title = EXCLUDED.canonical_title,
  short_title = EXCLUDED.short_title,
  instrument_type = EXCLUDED.instrument_type,
  subject_area = EXCLUDED.subject_area,
  notes = EXCLUDED.notes;

INSERT INTO legal_versions (
  instrument_id, slug, version_label, version_sequence, action_type,
  adopted_date, promulgated_date, effective_date, status, chapter_count,
  article_count, official_source_id, notes
) VALUES
  (
    (SELECT id FROM legal_instruments WHERE slug = 'cn_constitution'),
    'cn_constitution_2018',
    '2018年宪法修正版',
    1,
    'amended',
    '2018-03-11',
    '2018-03-11',
    '2018-03-11',
    'current',
    NULL,
    NULL,
    (SELECT id FROM sources WHERE slug = 'src_constitution_2018_npc'),
    '现行有效版本。'
  ),
  (
    (SELECT id FROM legal_instruments WHERE slug = 'cn_civil_code'),
    'cn_civil_code_2020',
    '2020年民法典',
    1,
    'enacted',
    '2020-05-28',
    '2020-05-28',
    '2021-01-01',
    'current',
    NULL,
    NULL,
    (SELECT id FROM sources WHERE slug = 'src_civil_code_2020_moj'),
    '现行有效版本。'
  ),
  (
    (SELECT id FROM legal_instruments WHERE slug = 'cn_securities_law'),
    'cn_securities_law_2019',
    '2019年证券法修订版',
    1,
    'revised',
    '2019-12-28',
    '2019-12-28',
    '2020-03-01',
    'current',
    NULL,
    NULL,
    (SELECT id FROM sources WHERE slug = 'src_securities_law_2019_csrc'),
    '现行有效版本。'
  ),
  (
    (SELECT id FROM legal_instruments WHERE slug = 'cn_enterprise_bankruptcy_law'),
    'cn_enterprise_bankruptcy_law_2006',
    '2006年企业破产法',
    1,
    'enacted',
    '2006-08-27',
    '2006-08-27',
    '2007-06-01',
    'current',
    NULL,
    NULL,
    (SELECT id FROM sources WHERE slug = 'src_bankruptcy_law_2006_npc'),
    '现行有效版本。'
  ),
  (
    (SELECT id FROM legal_instruments WHERE slug = 'cn_market_entity_registration_regulation'),
    'cn_market_entity_registration_regulation_2021',
    '2021年市场主体登记管理条例',
    1,
    'enacted',
    '2021-07-27',
    '2021-07-27',
    '2022-03-01',
    'current',
    NULL,
    NULL,
    (SELECT id FROM sources WHERE slug = 'src_registration_regulation_2021_gov'),
    '现行有效版本。'
  ),
  (
    (SELECT id FROM legal_instruments WHERE slug = 'cn_state_owned_assets_law'),
    'cn_state_owned_assets_law_2008',
    '2008年企业国有资产法',
    1,
    'enacted',
    '2008-10-28',
    '2008-10-28',
    '2009-05-01',
    'current',
    NULL,
    NULL,
    (SELECT id FROM sources WHERE slug = 'src_state_assets_law_2008_npc'),
    '现行有效版本。'
  ),
  (
    (SELECT id FROM legal_instruments WHERE slug = 'cn_foreign_investment_law'),
    'cn_foreign_investment_law_2019',
    '2019年外商投资法',
    1,
    'enacted',
    '2019-03-15',
    '2019-03-15',
    '2020-01-01',
    'current',
    NULL,
    NULL,
    (SELECT id FROM sources WHERE slug = 'src_foreign_investment_law_2019_npc'),
    '现行有效版本。'
  ),
  (
    (SELECT id FROM legal_instruments WHERE slug = 'cn_partnership_enterprise_law'),
    'cn_partnership_enterprise_law_2006',
    '2006年合伙企业法修订版',
    1,
    'revised',
    '2006-08-27',
    '2006-08-27',
    '2007-06-01',
    'current',
    NULL,
    NULL,
    (SELECT id FROM sources WHERE slug = 'src_partnership_law_2006_npc'),
    '现行有效版本。'
  ),
  (
    (SELECT id FROM legal_instruments WHERE slug = 'cn_sole_proprietorship_law'),
    'cn_sole_proprietorship_law_1999',
    '1999年个人独资企业法',
    1,
    'enacted',
    '1999-08-30',
    '1999-08-30',
    '2000-01-01',
    'current',
    NULL,
    NULL,
    (SELECT id FROM sources WHERE slug = 'src_sole_proprietorship_law_1999_npc'),
    '现行有效版本。'
  )
ON CONFLICT (slug) DO UPDATE SET
  version_label = EXCLUDED.version_label,
  action_type = EXCLUDED.action_type,
  adopted_date = EXCLUDED.adopted_date,
  promulgated_date = EXCLUDED.promulgated_date,
  effective_date = EXCLUDED.effective_date,
  status = EXCLUDED.status,
  official_source_id = EXCLUDED.official_source_id,
  notes = EXCLUDED.notes;

INSERT INTO instrument_domains (instrument_id, domain_id, is_primary, notes)
SELECT li.id, ld.id, true, NULL
FROM legal_instruments li
JOIN legal_domains ld ON ld.slug = li.subject_area
ON CONFLICT (instrument_id, domain_id) DO UPDATE SET
  is_primary = EXCLUDED.is_primary;

INSERT INTO instrument_domains (instrument_id, domain_id, is_primary, notes)
SELECT li.id, ld.id, false, '公司法与民法典共同构成营利法人制度接口。'
FROM legal_instruments li
JOIN legal_domains ld ON ld.slug = 'commercial-organization'
WHERE li.slug = 'cn_civil_code'
ON CONFLICT (instrument_id, domain_id) DO NOTHING;

INSERT INTO legal_units (
  version_id, parent_id, unit_type, unit_number, unit_number_int,
  title, text, canonical_ref, path, order_index, text_hash
) VALUES
  (
    (SELECT id FROM legal_versions WHERE slug = 'cn_constitution_2018'),
    NULL, 'article', '第五条', 5, NULL,
    '国家维护社会主义法制的统一和尊严。一切法律、行政法规和地方性法规都不得同宪法相抵触。',
    'constitution:2018:article_5', 'article_5', 5, md5('constitution:2018:article_5')
  ),
  (
    (SELECT id FROM legal_versions WHERE slug = 'cn_constitution_2018'),
    NULL, 'article', '第六条', 6, NULL,
    '中华人民共和国的社会主义经济制度的基础是生产资料的社会主义公有制。国家在社会主义初级阶段，坚持公有制为主体、多种所有制经济共同发展。',
    'constitution:2018:article_6', 'article_6', 6, md5('constitution:2018:article_6')
  ),
  (
    (SELECT id FROM legal_versions WHERE slug = 'cn_constitution_2018'),
    NULL, 'article', '第十一条', 11, NULL,
    '在法律规定范围内的个体经济、私营经济等非公有制经济，是社会主义市场经济的重要组成部分。国家鼓励、支持和引导非公有制经济的发展。',
    'constitution:2018:article_11', 'article_11', 11, md5('constitution:2018:article_11')
  ),
  (
    (SELECT id FROM legal_versions WHERE slug = 'cn_civil_code_2020'),
    NULL, 'article', '第五十七条', 57, NULL,
    '法人是具有民事权利能力和民事行为能力，依法独立享有民事权利和承担民事义务的组织。',
    'civil_code:2020:article_57', 'article_57', 57, md5('civil_code:2020:article_57')
  ),
  (
    (SELECT id FROM legal_versions WHERE slug = 'cn_civil_code_2020'),
    NULL, 'article', '第五十八条', 58, NULL,
    '法人应当依法成立。法人应当有自己的名称、组织机构、住所、财产或者经费。',
    'civil_code:2020:article_58', 'article_58', 58, md5('civil_code:2020:article_58')
  ),
  (
    (SELECT id FROM legal_versions WHERE slug = 'cn_civil_code_2020'),
    NULL, 'article', '第七十六条', 76, NULL,
    '以取得利润并分配给股东等出资人为目的成立的法人，为营利法人。',
    'civil_code:2020:article_76', 'article_76', 76, md5('civil_code:2020:article_76')
  ),
  (
    (SELECT id FROM legal_versions WHERE slug = 'cn_civil_code_2020'),
    NULL, 'article', '第八十三条', 83, NULL,
    '营利法人的出资人不得滥用出资人权利损害法人或者其他出资人的利益。',
    'civil_code:2020:article_83', 'article_83', 83, md5('civil_code:2020:article_83')
  ),
  (
    (SELECT id FROM legal_versions WHERE slug = 'cn_securities_law_2019'),
    NULL, 'article', '第二条', 2, NULL,
    '在中华人民共和国境内，股票、公司债券、存托凭证和国务院依法认定的其他证券的发行和交易，适用本法。',
    'securities_law:2019:article_2', 'article_2', 2, md5('securities_law:2019:article_2')
  ),
  (
    (SELECT id FROM legal_versions WHERE slug = 'cn_securities_law_2019'),
    NULL, 'article', '第十二条', 12, NULL,
    '公司首次公开发行新股，应当符合健全且运行良好的组织机构、持续经营能力等条件。',
    'securities_law:2019:article_12', 'article_12', 12, md5('securities_law:2019:article_12')
  ),
  (
    (SELECT id FROM legal_versions WHERE slug = 'cn_securities_law_2019'),
    NULL, 'article', '第七十八条', 78, NULL,
    '发行人及法律、行政法规和国务院证券监督管理机构规定的信息披露义务人，应当及时依法履行信息披露义务。',
    'securities_law:2019:article_78', 'article_78', 78, md5('securities_law:2019:article_78')
  ),
  (
    (SELECT id FROM legal_versions WHERE slug = 'cn_enterprise_bankruptcy_law_2006'),
    NULL, 'article', '第二条', 2, NULL,
    '企业法人不能清偿到期债务，并且资产不足以清偿全部债务或者明显缺乏清偿能力的，依照本法规定清理债务。',
    'bankruptcy_law:2006:article_2', 'article_2', 2, md5('bankruptcy_law:2006:article_2')
  ),
  (
    (SELECT id FROM legal_versions WHERE slug = 'cn_enterprise_bankruptcy_law_2006'),
    NULL, 'article', '第七条', 7, NULL,
    '债务人有本法第二条规定的情形，可以向人民法院提出重整、和解或者破产清算申请。',
    'bankruptcy_law:2006:article_7', 'article_7', 7, md5('bankruptcy_law:2006:article_7')
  ),
  (
    (SELECT id FROM legal_versions WHERE slug = 'cn_market_entity_registration_regulation_2021'),
    NULL, 'article', '第八条', 8, NULL,
    '市场主体的一般登记事项包括名称、主体类型、经营范围、住所、注册资本或者出资额、法定代表人等。',
    'registration_regulation:2021:article_8', 'article_8', 8, md5('registration_regulation:2021:article_8')
  ),
  (
    (SELECT id FROM legal_versions WHERE slug = 'cn_market_entity_registration_regulation_2021'),
    NULL, 'article', '第三十四条', 34, NULL,
    '登记机关应当依法向社会公示市场主体登记管理信息。',
    'registration_regulation:2021:article_34', 'article_34', 34, md5('registration_regulation:2021:article_34')
  ),
  (
    (SELECT id FROM legal_versions WHERE slug = 'cn_market_entity_registration_regulation_2021'),
    NULL, 'article', '第三十一条', 31, NULL,
    '市场主体因解散、被宣告破产或者其他法定事由需要终止的，应当依法办理注销登记。',
    'registration_regulation:2021:article_31', 'article_31', 31, md5('registration_regulation:2021:article_31')
  ),
  (
    (SELECT id FROM legal_versions WHERE slug = 'cn_state_owned_assets_law_2008'),
    NULL, 'article', '第五条', 5, NULL,
    '国家出资企业包括国家出资的有限责任公司、股份有限公司和其他企业。',
    'state_assets_law:2008:article_5', 'article_5', 5, md5('state_assets_law:2008:article_5')
  ),
  (
    (SELECT id FROM legal_versions WHERE slug = 'cn_state_owned_assets_law_2008'),
    NULL, 'article', '第三十条', 30, NULL,
    '国家出资企业合并、分立、改制、上市等重大事项，应当依照法定权限和程序决定。',
    'state_assets_law:2008:article_30', 'article_30', 30, md5('state_assets_law:2008:article_30')
  ),
  (
    (SELECT id FROM legal_versions WHERE slug = 'cn_foreign_investment_law_2019'),
    NULL, 'article', '第三十一条', 31, NULL,
    '外商投资企业的组织形式、组织机构及其活动准则，适用公司法、合伙企业法等法律的规定。',
    'foreign_investment_law:2019:article_31', 'article_31', 31, md5('foreign_investment_law:2019:article_31')
  ),
  (
    (SELECT id FROM legal_versions WHERE slug = 'cn_partnership_enterprise_law_2006'),
    NULL, 'article', '第二条', 2, NULL,
    '本法所称合伙企业，是指自然人、法人和其他组织依照本法在中国境内设立的普通合伙企业和有限合伙企业。',
    'partnership_law:2006:article_2', 'article_2', 2, md5('partnership_law:2006:article_2')
  ),
  (
    (SELECT id FROM legal_versions WHERE slug = 'cn_sole_proprietorship_law_1999'),
    NULL, 'article', '第二条', 2, NULL,
    '本法所称个人独资企业，是指依照本法在中国境内设立，由一个自然人投资，财产为投资人个人所有，投资人以其个人财产对企业债务承担无限责任的经营实体。',
    'sole_proprietorship_law:1999:article_2', 'article_2', 2, md5('sole_proprietorship_law:1999:article_2')
  )
ON CONFLICT (canonical_ref) DO UPDATE SET
  text = EXCLUDED.text,
  title = EXCLUDED.title;

INSERT INTO legal_relations (
  subject_type, subject_id, object_type, object_id, relation_type,
  claim_text, source_id, confidence, evidence_level, notes
) VALUES
  (
    'legal_instrument',
    (SELECT id FROM legal_instruments WHERE slug = 'cn_company_law'),
    'legal_instrument',
    (SELECT id FROM legal_instruments WHERE slug = 'cn_constitution'),
    'based_on',
    '公司法的制度正当性和边界受宪法确立的社会主义市场经济和法制统一原则约束。',
    (SELECT id FROM sources WHERE slug = 'src_constitution_2018_npc'),
    0.95,
    'official',
    '上位法关系。'
  ),
  (
    'legal_instrument',
    (SELECT id FROM legal_instruments WHERE slug = 'cn_company_law'),
    'legal_instrument',
    (SELECT id FROM legal_instruments WHERE slug = 'cn_civil_code'),
    'specifies',
    '民法典提供法人和营利法人一般规则，公司法对公司这一营利法人类型作组织法层面的具体化。',
    (SELECT id FROM sources WHERE slug = 'src_civil_code_2020_moj'),
    0.95,
    'official',
    '一般法与特别法接口。'
  ),
  (
    'legal_instrument',
    (SELECT id FROM legal_instruments WHERE slug = 'cn_company_law'),
    'legal_instrument',
    (SELECT id FROM legal_instruments WHERE slug = 'cn_securities_law'),
    'supplements',
    '股份有限公司涉及证券发行、上市与信息披露时，由证券法作补充规范。',
    (SELECT id FROM sources WHERE slug = 'src_securities_law_2019_csrc'),
    0.90,
    'official',
    NULL
  ),
  (
    'legal_instrument',
    (SELECT id FROM legal_instruments WHERE slug = 'cn_company_law'),
    'legal_instrument',
    (SELECT id FROM legal_instruments WHERE slug = 'cn_enterprise_bankruptcy_law'),
    'constrained_by',
    '公司出现资不抵债或明显缺乏清偿能力时，退出与债权清理受企业破产法约束。',
    (SELECT id FROM sources WHERE slug = 'src_bankruptcy_law_2006_npc'),
    0.92,
    'official',
    NULL
  ),
  (
    'legal_instrument',
    (SELECT id FROM legal_instruments WHERE slug = 'cn_company_law'),
    'legal_instrument',
    (SELECT id FROM legal_instruments WHERE slug = 'cn_market_entity_registration_regulation'),
    'constrained_by',
    '公司设立、变更、注销和登记公示的程序规则，由市场主体登记管理条例承接和细化。',
    (SELECT id FROM sources WHERE slug = 'src_registration_regulation_2021_gov'),
    0.92,
    'official',
    NULL
  ),
  (
    'legal_instrument',
    (SELECT id FROM legal_instruments WHERE slug = 'cn_company_law'),
    'legal_instrument',
    (SELECT id FROM legal_instruments WHERE slug = 'cn_state_owned_assets_law'),
    'supplements',
    '国家出资公司治理中的出资人职责、重大事项决策和资产监管，由企业国有资产法补充。',
    (SELECT id FROM sources WHERE slug = 'src_state_assets_law_2008_npc'),
    0.88,
    'official',
    NULL
  ),
  (
    'legal_instrument',
    (SELECT id FROM legal_instruments WHERE slug = 'cn_company_law'),
    'legal_instrument',
    (SELECT id FROM legal_instruments WHERE slug = 'cn_foreign_investment_law'),
    'interacts_with',
    '外商投资企业采用公司等组织形式时，其组织规则回到公司法和合伙企业法。',
    (SELECT id FROM sources WHERE slug = 'src_foreign_investment_law_2019_npc'),
    0.94,
    'official',
    NULL
  ),
  (
    'legal_instrument',
    (SELECT id FROM legal_instruments WHERE slug = 'cn_company_law'),
    'legal_instrument',
    (SELECT id FROM legal_instruments WHERE slug = 'cn_partnership_enterprise_law'),
    'same_domain',
    '公司法与合伙企业法同属商事组织法的并列制度。',
    (SELECT id FROM sources WHERE slug = 'src_partnership_law_2006_npc'),
    0.80,
    'secondary',
    '法域并列关系。'
  ),
  (
    'legal_instrument',
    (SELECT id FROM legal_instruments WHERE slug = 'cn_company_law'),
    'legal_instrument',
    (SELECT id FROM legal_instruments WHERE slug = 'cn_sole_proprietorship_law'),
    'same_domain',
    '公司法与个人独资企业法同属市场主体组织法层面的并列制度。',
    (SELECT id FROM sources WHERE slug = 'src_sole_proprietorship_law_1999_npc'),
    0.75,
    'secondary',
    '法域并列关系。'
  ),
  (
    'legal_instrument',
    (SELECT id FROM legal_instruments WHERE slug = 'cn_company_law'),
    'context_event',
    (SELECT id FROM context_events WHERE slug = 'cn_registration_capital_reform_2013'),
    'policy_background',
    '2013年注册资本登记制度改革是公司法由实缴走向认缴的重要政策背景。',
    (SELECT id FROM sources WHERE slug = 'src_company_law_2013_amendment_szmee'),
    0.95,
    'official',
    NULL
  ),
  (
    'legal_instrument',
    (SELECT id FROM legal_instruments WHERE slug = 'cn_company_law'),
    'context_event',
    (SELECT id FROM context_events WHERE slug = 'cn_registered_capital_disorder_2023'),
    'policy_background',
    '2023年修订中的五年缴足、催缴失权与加速到期，与认缴制外溢问题治理直接相关。',
    (SELECT id FROM sources WHERE slug = 'src_company_law_2023_csrc_hubei_materials'),
    0.85,
    'professional',
    NULL
  ),
  (
    'legal_unit',
    (SELECT id FROM legal_units WHERE canonical_ref = 'company_law:2023:article_1'),
    'legal_unit',
    (SELECT id FROM legal_units WHERE canonical_ref = 'constitution:2018:article_5'),
    'based_on',
    '公司法的制定与适用不得与宪法相抵触。',
    (SELECT id FROM sources WHERE slug = 'src_constitution_2018_npc'),
    0.95,
    'official',
    NULL
  ),
  (
    'legal_unit',
    (SELECT id FROM legal_units WHERE canonical_ref = 'company_law:2023:article_3'),
    'legal_unit',
    (SELECT id FROM legal_units WHERE canonical_ref = 'civil_code:2020:article_57'),
    'specifies',
    '公司法人地位是民法典法人一般规则在公司法上的具体化。',
    (SELECT id FROM sources WHERE slug = 'src_civil_code_2020_moj'),
    0.95,
    'official',
    NULL
  ),
  (
    'legal_unit',
    (SELECT id FROM legal_units WHERE canonical_ref = 'company_law:2023:article_47'),
    'legal_unit',
    (SELECT id FROM legal_units WHERE canonical_ref = 'registration_regulation:2021:article_8'),
    'interacts_with',
    '注册资本制度与登记事项、公示事项直接衔接。',
    (SELECT id FROM sources WHERE slug = 'src_registration_regulation_2021_gov'),
    0.93,
    'official',
    NULL
  ),
  (
    'legal_unit',
    (SELECT id FROM legal_units WHERE canonical_ref = 'company_law:2023:article_47'),
    'legal_unit',
    (SELECT id FROM legal_units WHERE canonical_ref = 'bankruptcy_law:2006:article_2'),
    'constrained_by',
    '资本信用失灵最终会落到债务清理和破产退出机制。',
    (SELECT id FROM sources WHERE slug = 'src_bankruptcy_law_2006_npc'),
    0.80,
    'secondary',
    NULL
  ),
  (
    'legal_unit',
    (SELECT id FROM legal_units WHERE canonical_ref = 'company_law:2023:article_112'),
    'legal_unit',
    (SELECT id FROM legal_units WHERE canonical_ref = 'securities_law:2019:article_78'),
    'supplements',
    '涉及上市公司信息披露和资本市场治理时，证券法构成补充规范。',
    (SELECT id FROM sources WHERE slug = 'src_securities_law_2019_csrc'),
    0.78,
    'professional',
    '具体条号后续可继续精细校准。'
  )
ON CONFLICT (subject_type, subject_id, object_type, object_id, relation_type) DO UPDATE SET
  claim_text = EXCLUDED.claim_text,
  source_id = EXCLUDED.source_id,
  confidence = EXCLUDED.confidence,
  evidence_level = EXCLUDED.evidence_level,
  notes = EXCLUDED.notes;

CREATE OR REPLACE VIEW v_legal_instrument_catalog AS
SELECT
  li.id,
  li.slug,
  li.short_title,
  li.canonical_title,
  li.instrument_type,
  li.subject_area,
  li.first_enacted_date,
  lv.slug AS current_version_slug,
  lv.version_label AS current_version_label,
  lv.effective_date,
  lv.status,
  s.title AS source_title,
  s.url AS source_url,
  string_agg(ld.name, ' / ' ORDER BY ld.sort_order) AS domains
FROM legal_instruments li
LEFT JOIN legal_versions lv
  ON lv.instrument_id = li.id AND lv.status = 'current'
LEFT JOIN sources s ON s.id = lv.official_source_id
LEFT JOIN instrument_domains idm ON idm.instrument_id = li.id
LEFT JOIN legal_domains ld ON ld.id = idm.domain_id
GROUP BY
  li.id, li.slug, li.short_title, li.canonical_title, li.instrument_type,
  li.subject_area, li.first_enacted_date, lv.slug, lv.version_label,
  lv.effective_date, lv.status, s.title, s.url;

COMMIT;
