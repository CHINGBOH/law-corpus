BEGIN;

INSERT INTO documents (
  slug, doc_type, jurisdiction, title, title_normalized, issuing_body,
  publish_date, effective_date, status, summary
) VALUES
  (
    'doc_cn_company_law',
    'law',
    'CN_MAINLAND',
    '中华人民共和国公司法',
    '中华人民共和国公司法',
    '全国人民代表大会常务委员会',
    '1993-12-29',
    '1994-07-01',
    'effective',
    '大陆公司法主文档，版本覆盖 1993 制定、1999/2004/2013/2018 修正、2005/2023 全面修订。'
  ),
  (
    'doc_cn_company_law_2023_materials',
    'explanation',
    'CN_MAINLAND',
    '新公司法学习宣传材料汇编',
    '新公司法学习宣传材料汇编',
    '中国证监会湖北监管局',
    '2024-01-01',
    NULL,
    'historical',
    '用于理解 2023 年公司法修订背景、制度亮点和监管语境的材料。'
  ),
  (
    'doc_cn_company_registration_reform_2013',
    'policy',
    'CN_MAINLAND',
    '注册资本登记制度改革及商事制度改革背景',
    '注册资本登记制度改革及商事制度改革背景',
    '国务院及市场监管体系',
    '2013-10-01',
    NULL,
    'historical',
    '用于关联 2013 年公司法资本制度修正的政策背景。'
  ),
  (
    'doc_sg_company_law_comparative_material',
    'article',
    'SG',
    '新加坡公司法比较法影响材料',
    '新加坡公司法比较法影响材料',
    NULL,
    NULL,
    NULL,
    'unknown',
    '占位文档：只用于承载经来源证明的新加坡公司法比较法影响，不代表已确认官方立法来源。'
  )
ON CONFLICT (slug) DO UPDATE SET
  title = EXCLUDED.title,
  summary = EXCLUDED.summary,
  updated_at = now();

INSERT INTO sources (
  slug, document_id, source_type, title, url, publisher, published_at,
  storage_uri, reliability_tier, notes
) VALUES
  (
    'src_company_law_1993_wikisource_full',
    (SELECT id FROM documents WHERE slug = 'doc_cn_company_law'),
    'wiki',
    '中华人民共和国公司法（1993年制定版全文）',
    'https://zh.wikisource.org/wiki/中华人民共和国公司法_(1993年)',
    '维基文库',
    '1993-12-29',
    'object-store/company_law/1993/wikisource_company_law_1993.html',
    4,
    '二手全文备查；后续应替换为全国人大或公报来源。'
  ),
  (
    'src_company_law_2023_chinatax',
    (SELECT id FROM documents WHERE slug = 'doc_cn_company_law'),
    'government',
    '中华人民共和国公司法（国家税务总局政策法规库）',
    'https://fgk.chinatax.gov.cn/zcfgk/c100009/c5233383/content.html',
    '国家税务总局政策法规库',
    '2023-12-29',
    'object-store/company_law/2023/chinatax_company_law_2023.html',
    2,
    '现行全文和沿革注释入口。'
  ),
  (
    'src_company_law_2005_xinfang',
    (SELECT id FROM documents WHERE slug = 'doc_cn_company_law'),
    'government',
    '中华人民共和国公司法（2005 修订版全文入口）',
    'https://www.gjxfj.gov.cn/gjxfj/xxgk/fgwj/flfg/webinfo/2016/03/1460585589899465.htm',
    '国家信访局',
    '2016-03-01',
    'object-store/company_law/2005/gjxfj_company_law_2005.html',
    2,
    '政府网站转载 2005 修订版全文入口。'
  ),
  (
    'src_company_law_2013_amendment_szmee',
    (SELECT id FROM documents WHERE slug = 'doc_cn_company_law'),
    'government',
    '关于修改〈中华人民共和国海洋环境保护法〉等七部法律的决定',
    'https://meeb.sz.gov.cn/xxgk/zcfg/zcfg/gjflfg/content/post_2041712.html',
    '深圳市生态环境局',
    '2013-12-28',
    'object-store/company_law/2013/seven_laws_amendment_2013.html',
    2,
    '含 2013 年公司法资本制度修正。'
  ),
  (
    'src_company_law_2018_amendment_mofcom',
    (SELECT id FROM documents WHERE slug = 'doc_cn_company_law'),
    'government',
    '全国人民代表大会常务委员会关于修改〈中华人民共和国公司法〉的决定',
    'https://policy.mofcom.gov.cn/claw/clawContent.shtml?id=65419',
    '商务部全球法规网',
    '2018-10-26',
    'object-store/company_law/2018/company_law_amendment_2018.html',
    2,
    '2018 年股份回购条款修改决定。'
  ),
  (
    'src_company_law_2023_csrc_hubei_materials',
    (SELECT id FROM documents WHERE slug = 'doc_cn_company_law_2023_materials'),
    'government',
    '新《公司法》学习宣传材料汇编',
    'https://www.csrc.gov.cn/hubei/c106373/c7494831/7494831/files/%E6%96%B0%E3%80%8A%E5%85%AC%E5%8F%B8%E6%B3%95%E3%80%8B%E5%AD%A6%E4%B9%A0%E5%AE%A3%E4%BC%A0%E6%9D%90%E6%96%99%E6%B1%87%E7%BC%96.pdf',
    '中国证监会湖北监管局',
    '2024-01-01',
    'object-store/company_law/2023/csrc_hubei_company_law_materials.pdf',
    2,
    '用于 2023 修订背景和亮点。'
  ),
  (
    'src_company_law_1999_wikisource_full',
    (SELECT id FROM documents WHERE slug = 'doc_cn_company_law'),
    'wiki',
    '中华人民共和国公司法（1999年修正版全文）',
    'https://zh.wikisource.org/wiki/中华人民共和国公司法_(1999年)',
    '维基文库',
    '1999-12-25',
    'object-store/company_law/1999/wikisource_company_law_1999.html',
    4,
    '二手全文备查；正式入库时应替换为全国人大或公报来源。'
  ),
  (
    'src_company_law_2004_wikisource_full',
    (SELECT id FROM documents WHERE slug = 'doc_cn_company_law'),
    'wiki',
    '中华人民共和国公司法（2004年修正版全文）',
    'https://zh.wikisource.org/wiki/中华人民共和国公司法_(2004年)',
    '维基文库',
    '2004-08-28',
    'object-store/company_law/2004/wikisource_company_law_2004.html',
    4,
    '二手全文备查；正式入库时应替换为全国人大或公报来源。'
  ),
  (
    'src_company_law_2013_wikisource_full',
    (SELECT id FROM documents WHERE slug = 'doc_cn_company_law'),
    'wiki',
    '中华人民共和国公司法（2013年修正版全文）',
    'https://zh.wikisource.org/wiki/中华人民共和国公司法_(2013年)',
    '维基文库',
    '2013-12-28',
    'object-store/company_law/2013/wikisource_company_law_2013.html',
    4,
    '二手全文备查；后续应替换为全国人大或公报来源。'
  ),
  (
    'src_company_law_2018_sipf_full',
    (SELECT id FROM documents WHERE slug = 'doc_cn_company_law'),
    'professional',
    '中华人民共和国公司法（2018修正版全文）',
    'https://www.sipf.com.cn/flfg/2020/03/12855.shtml',
    '上海国际港务（集团）股份有限公司',
    '2020-03-01',
    'object-store/company_law/2018/sipf_company_law_2018.html',
    3,
    '专业/企业站转载 2018 修正版全文；后续应替换为全国人大或公报来源。'
  ),
  (
    'src_company_law_1999_wikisource',
    (SELECT id FROM documents WHERE slug = 'doc_cn_company_law'),
    'wiki',
    '关于修改《中华人民共和国公司法》的决定（1999年）',
    'https://zh.wikisource.org/wiki/全国人民代表大会常务委员会关于修改《中华人民共和国公司法》的决定_(1999年)',
    '维基文库',
    '1999-12-25',
    'object-store/company_law/1999/wikisource_amendment_1999.html',
    4,
    '二手备查；正式入库时应替换为全国人大或公报来源。'
  ),
  (
    'src_company_law_2004_wikisource',
    (SELECT id FROM documents WHERE slug = 'doc_cn_company_law'),
    'wiki',
    '关于修改《中华人民共和国公司法》的决定（2004年）',
    'https://zh.wikisource.org/wiki/全国人民代表大会常务委员会关于修改《中华人民共和国公司法》的决定_(2004年)',
    '维基文库',
    '2004-08-28',
    'object-store/company_law/2004/wikisource_amendment_2004.html',
    4,
    '二手备查；正式入库时应替换为全国人大或公报来源。'
  )
ON CONFLICT (slug) DO UPDATE SET
  title = EXCLUDED.title,
  url = EXCLUDED.url,
  notes = EXCLUDED.notes;

INSERT INTO legal_instruments (
  slug, canonical_title, short_title, jurisdiction, instrument_type,
  subject_area, first_enacted_date, notes
) VALUES (
  'cn_company_law',
  '中华人民共和国公司法',
  '公司法',
  'CN_MAINLAND',
  'law',
  'commercial/company',
  '1993-12-29',
  '大陆公司法制度演化仓库的第一批入库对象。'
)
ON CONFLICT (slug) DO UPDATE SET notes = EXCLUDED.notes;

INSERT INTO legal_versions (
  instrument_id, slug, version_label, version_sequence, action_type,
  adopted_date, promulgated_date, effective_date, status, chapter_count,
  article_count, official_source_id, xml_uri, raw_text_uri, notes
) VALUES
  (
    (SELECT id FROM legal_instruments WHERE slug = 'cn_company_law'),
    'cn_company_law_1993',
    '1993 年制定版',
    1,
    'enacted',
    '1993-12-29',
    '1993-12-29',
    '1994-07-01',
    'historical',
    11,
    230,
    (SELECT id FROM sources WHERE slug = 'src_company_law_1993_wikisource_full'),
    'xml-akn/company_law/1993.xml',
    'object-store/company_law/1993/raw.txt',
    '待补官方全文来源。'
  ),
  (
    (SELECT id FROM legal_instruments WHERE slug = 'cn_company_law'),
    'cn_company_law_1999',
    '1999 年第一次修正版',
    2,
    'amended',
    '1999-12-25',
    '1999-12-25',
    '1999-12-25',
    'historical',
    11,
    230,
    (SELECT id FROM sources WHERE slug = 'src_company_law_1999_wikisource_full'),
    'xml-akn/company_law/1999.xml',
    'object-store/company_law/1999/raw.txt',
    '局部修正：国有独资公司监事会、高新技术股份公司特别规则。'
  ),
  (
    (SELECT id FROM legal_instruments WHERE slug = 'cn_company_law'),
    'cn_company_law_2004',
    '2004 年第二次修正版',
    3,
    'amended',
    '2004-08-28',
    '2004-08-28',
    '2004-08-28',
    'historical',
    11,
    230,
    (SELECT id FROM sources WHERE slug = 'src_company_law_2004_wikisource_full'),
    'xml-akn/company_law/2004.xml',
    'object-store/company_law/2004/raw.txt',
    '局部修正：删除股票溢价发行行政审批条款。'
  ),
  (
    (SELECT id FROM legal_instruments WHERE slug = 'cn_company_law'),
    'cn_company_law_2005',
    '2005 年第一次修订版',
    4,
    'revised',
    '2005-10-27',
    '2005-10-27',
    '2006-01-01',
    'historical',
    13,
    219,
    (SELECT id FROM sources WHERE slug = 'src_company_law_2005_xinfang'),
    'xml-akn/company_law/2005.xml',
    'object-store/company_law/2005/raw.txt',
    '第一次全面修订。'
  ),
  (
    (SELECT id FROM legal_instruments WHERE slug = 'cn_company_law'),
    'cn_company_law_2013',
    '2013 年第三次修正版',
    5,
    'amended',
    '2013-12-28',
    '2013-12-28',
    '2014-03-01',
    'historical',
    13,
    218,
    (SELECT id FROM sources WHERE slug = 'src_company_law_2013_wikisource_full'),
    'xml-akn/company_law/2013.xml',
    'object-store/company_law/2013/raw.txt',
    '注册资本登记制度改革：实缴登记制转向认缴登记制。'
  ),
  (
    (SELECT id FROM legal_instruments WHERE slug = 'cn_company_law'),
    'cn_company_law_2018',
    '2018 年第四次修正版',
    6,
    'amended',
    '2018-10-26',
    '2018-10-26',
    '2018-10-26',
    'historical',
    13,
    218,
    (SELECT id FROM sources WHERE slug = 'src_company_law_2018_sipf_full'),
    'xml-akn/company_law/2018.xml',
    'object-store/company_law/2018/raw.txt',
    '股份回购规则扩容。'
  ),
  (
    (SELECT id FROM legal_instruments WHERE slug = 'cn_company_law'),
    'cn_company_law_2023',
    '2023 年第二次修订版',
    7,
    'revised',
    '2023-12-29',
    '2023-12-29',
    '2024-07-01',
    'current',
    15,
    266,
    (SELECT id FROM sources WHERE slug = 'src_company_law_2023_chinatax'),
    'xml-akn/company_law/2023.xml',
    'object-store/company_law/2023/raw.txt',
    '第二次全面修订；现行版本。'
  )
ON CONFLICT (slug) DO UPDATE SET
  version_label = EXCLUDED.version_label,
  chapter_count = EXCLUDED.chapter_count,
  article_count = EXCLUDED.article_count,
  official_source_id = EXCLUDED.official_source_id,
  xml_uri = EXCLUDED.xml_uri,
  raw_text_uri = EXCLUDED.raw_text_uri,
  notes = EXCLUDED.notes;

INSERT INTO version_events (
  instrument_id, legal_version_id, event_type, event_date, title,
  description, source_id
)
SELECT
  li.id,
  lv.id,
  CASE lv.action_type
    WHEN 'enacted' THEN 'enactment'
    WHEN 'amended' THEN 'amendment'
    ELSE 'revision'
  END,
  lv.adopted_date,
  lv.version_label,
  lv.notes,
  lv.official_source_id
FROM legal_versions lv
JOIN legal_instruments li ON li.id = lv.instrument_id
WHERE li.slug = 'cn_company_law'
ON CONFLICT DO NOTHING;

INSERT INTO context_events (
  slug, event_type, title, start_date, end_date, jurisdiction, description, source_id
) VALUES
  (
    'cn_socialist_market_economy_1992',
    'historical_origin',
    '建立社会主义市场经济体制改革目标',
    '1992-10-12',
    NULL,
    'CN_MAINLAND',
    '公司法制定的制度源头之一：从计划经济体制下的企业管理转向社会主义市场经济中的公司制度。',
    NULL
  ),
  (
    'cn_modern_enterprise_system_reform_1990s',
    'reform',
    '国有企业现代企业制度改革',
    '1993-01-01',
    NULL,
    'CN_MAINLAND',
    '1993 制定公司法的重要历史背景：建立产权清晰、权责明确、政企分开、管理科学的现代企业制度。',
    NULL
  ),
  (
    'cn_registration_capital_reform_2013',
    'reform',
    '注册资本登记制度改革',
    '2013-10-01',
    NULL,
    'CN_MAINLAND',
    '2013 公司法修正的核心政策环境：注册资本由实缴登记制转向认缴登记制，降低市场准入门槛。',
    (SELECT id FROM sources WHERE slug = 'src_company_law_2013_amendment_szmee')
  ),
  (
    'cn_share_repurchase_capital_market_2018',
    'policy',
    '资本市场股份回购制度调整',
    '2018-10-26',
    NULL,
    'CN_MAINLAND',
    '2018 公司法修正的直接制度环境：拓展股份回购用途，支持股权激励、可转债转换和维护公司价值。',
    (SELECT id FROM sources WHERE slug = 'src_company_law_2018_amendment_mofcom')
  ),
  (
    'cn_registered_capital_disorder_2023',
    'policy',
    '认缴制外溢问题和注册资本信用约束回收',
    '2023-12-29',
    NULL,
    'CN_MAINLAND',
    '2023 公司法修订的重要问题背景：对长期、过高、虚化认缴形成制度约束。',
    (SELECT id FROM sources WHERE slug = 'src_company_law_2023_csrc_hubei_materials')
  ),
  (
    'sg_company_law_influence_claim',
    'comparative_law',
    '新加坡公司法比较法影响待证命题',
    NULL,
    NULL,
    'SG',
    '用于存放“大陆公司法学习或借鉴新加坡公司法”的来源证据。当前作为待证命题，不作为官方确定事实。',
    NULL
  )
ON CONFLICT (slug) DO UPDATE SET
  description = EXCLUDED.description,
  source_id = EXCLUDED.source_id;

INSERT INTO context_links (
  subject_type, subject_id, object_type, object_id, relation_type,
  claim_text, confidence, evidence_level, source_id, notes
) VALUES
  (
    'legal_version',
    (SELECT id FROM legal_versions WHERE slug = 'cn_company_law_1993'),
    'context_event',
    (SELECT id FROM context_events WHERE slug = 'cn_socialist_market_economy_1992'),
    'background_of',
    '1993 年公司法制定与建立社会主义市场经济体制的历史转向相关。',
    0.80,
    'secondary',
    (SELECT id FROM sources WHERE slug = 'src_company_law_2023_csrc_hubei_materials'),
    '需继续补全国人大立法说明或官方历史材料。'
  ),
  (
    'legal_version',
    (SELECT id FROM legal_versions WHERE slug = 'cn_company_law_1993'),
    'context_event',
    (SELECT id FROM context_events WHERE slug = 'cn_modern_enterprise_system_reform_1990s'),
    'background_of',
    '1993 年公司法制定服务于国有企业现代企业制度改革和公司制改造。',
    0.80,
    'secondary',
    (SELECT id FROM sources WHERE slug = 'src_company_law_2023_csrc_hubei_materials'),
    '需继续补 1993 年立法背景一手材料。'
  ),
  (
    'legal_version',
    (SELECT id FROM legal_versions WHERE slug = 'cn_company_law_2013'),
    'context_event',
    (SELECT id FROM context_events WHERE slug = 'cn_registration_capital_reform_2013'),
    'responds_to',
    '2013 年公司法修正回应注册资本登记制度改革，降低设立门槛。',
    0.95,
    'official',
    (SELECT id FROM sources WHERE slug = 'src_company_law_2013_amendment_szmee'),
    NULL
  ),
  (
    'legal_version',
    (SELECT id FROM legal_versions WHERE slug = 'cn_company_law_2018'),
    'context_event',
    (SELECT id FROM context_events WHERE slug = 'cn_share_repurchase_capital_market_2018'),
    'responds_to',
    '2018 年公司法修正集中调整股份回购规则，服务资本市场工具需求。',
    0.95,
    'official',
    (SELECT id FROM sources WHERE slug = 'src_company_law_2018_amendment_mofcom'),
    NULL
  ),
  (
    'legal_version',
    (SELECT id FROM legal_versions WHERE slug = 'cn_company_law_2023'),
    'context_event',
    (SELECT id FROM context_events WHERE slug = 'cn_registered_capital_disorder_2023'),
    'responds_to',
    '2023 年公司法修订通过五年缴足、催缴失权和加速到期等机制，回收认缴制外溢问题。',
    0.85,
    'professional',
    (SELECT id FROM sources WHERE slug = 'src_company_law_2023_csrc_hubei_materials'),
    NULL
  ),
  (
    'legal_version',
    (SELECT id FROM legal_versions WHERE slug = 'cn_company_law_2023'),
    'context_event',
    (SELECT id FROM context_events WHERE slug = 'sg_company_law_influence_claim'),
    'influenced_by',
    '大陆公司法，尤其 2023 年修订中的部分公司治理制度，可能借鉴以新加坡为代表的普通法系公司法经验。',
    0.40,
    'unverified',
    (SELECT id FROM sources WHERE slug = 'src_company_law_2023_csrc_hubei_materials'),
    '当前只有待证方向；需补学术论文、全国人大立法材料或权威比较法材料后再提高置信度。'
  )
ON CONFLICT DO NOTHING;

INSERT INTO tags (name, tag_type) VALUES
  ('公司法', 'topic'),
  ('商事制度改革', 'policy_goal'),
  ('注册资本', 'legal_concept'),
  ('公司治理', 'legal_concept'),
  ('比较法', 'doctrine'),
  ('新加坡公司法', 'topic')
ON CONFLICT (name) DO NOTHING;

INSERT INTO taggings (tag_id, target_type, target_id)
SELECT t.id, 'legal_version', lv.id
FROM tags t
CROSS JOIN legal_versions lv
JOIN legal_instruments li ON li.id = lv.instrument_id
WHERE t.name = '公司法' AND li.slug = 'cn_company_law'
ON CONFLICT DO NOTHING;

COMMIT;
