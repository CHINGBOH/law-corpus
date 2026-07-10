LEGAL_TERMS = [
    "资本信用",
    "注册资本",
    "认缴",
    "实缴",
    "出资",
    "五年",
    "缴足",
    "催缴",
    "失权",
    "加速到期",
    "股东",
    "董事",
    "监事",
    "高级管理人员",
    "股权转让",
    "股份回购",
    "公司登记",
    "清算",
    "注销",
    "人格否认",
    "债权人",
    "新加坡",
]

TERM_EXPANSIONS = {
    "资本信用": ["注册资本", "认缴", "实缴", "出资", "五年", "缴足", "债权人"],
    "人格与登记": ["公司登记", "营业执照", "公司成立", "人格", "债务承担"],
    "治理机关": ["股东会", "董事会", "监事会", "审计委员会", "经理"],
    "股东权利": ["股东", "股权转让", "知情权", "表决权", "利润分配"],
    "董监高责任": ["董事", "监事", "高级管理人员", "忠实", "勤勉"],
    "股份与融资": ["股份", "公司债券", "股份回购", "类别股", "无面额股"],
    "重组与退出": ["合并", "分立", "减资", "清算", "注销"],
}

PILLARS = [
    {
        "title": "人格与登记",
        "question": "公司何以成为独立法律主体？",
        "scope": "公司设立、登记、公示、营业执照、人格独立、横向人格否认。",
        "signal": "1993 建立公司主体框架，2023 新设公司登记章并强化登记公示效果。",
    },
    {
        "title": "资本信用",
        "question": "公司拿什么对外承担信用？",
        "scope": "注册资本、认缴/实缴、出资期限、催缴失权、加速到期、减资。",
        "signal": "2013 放开认缴，2023 用五年缴足和责任规则回收资本信用约束。",
    },
    {
        "title": "治理机关",
        "question": "公司内部权力如何分配和制衡？",
        "scope": "股东会、董事会、监事会、审计委员会、经理、国家出资公司治理。",
        "signal": "2005 强化现代治理，2023 允许审计委员会替代监事会并简化小公司机关。",
    },
    {
        "title": "股东权利",
        "question": "投资人如何进入、退出、监督和救济？",
        "scope": "股权转让、知情权、表决权、利润分配、异议股东回购、股东诉讼。",
        "signal": "2005 是股东权利扩张节点，2023 继续细化权利行使和责任边界。",
    },
    {
        "title": "董监高责任",
        "question": "经营权如何被约束？",
        "scope": "忠实义务、勤勉义务、关联交易、实际控制人、赔偿责任。",
        "signal": "2023 明显强化董监高、控股股东、实际控制人的责任链条。",
    },
    {
        "title": "股份与融资",
        "question": "公司如何组织资本流动？",
        "scope": "股份发行转让、公司债券、类别股、无面额股、授权资本、股份回购。",
        "signal": "2018 扩大股份回购，2023 引入更复杂的股份公司资本工具。",
    },
    {
        "title": "重组与退出",
        "question": "公司如何变化、死亡和承担收尾责任？",
        "scope": "合并、分立、增资、减资、解散、清算、简易注销、强制注销。",
        "signal": "2023 系统补强简易合并、简易减资、清算义务和注销机制。",
    },
]

QUERIES = {
    "topics": """
        SELECT jsonb_agg(to_jsonb(t) ORDER BY sort_order, title)
        FROM (
          SELECT dt.slug, dt.title, dt.pillar_title, dt.question, dt.summary,
                 dt.sort_order, dt.status,
                 count(DISTINCT tl.id) AS link_count,
                 count(DISTINCT pe.id) AS explanation_count
          FROM doctrine_topics dt
          LEFT JOIN topic_links tl ON tl.topic_id = dt.id
          LEFT JOIN plain_explanations pe ON pe.topic_id = dt.id
          GROUP BY dt.id, dt.slug, dt.title, dt.pillar_title, dt.question, dt.summary, dt.sort_order, dt.status
        ) t;
    """,
    "topic_detail": """
        SELECT to_jsonb(t)
        FROM (
          SELECT dt.id, dt.slug, dt.title, dt.pillar_title, dt.question, dt.summary,
                 dt.sort_order, dt.status,
                 count(DISTINCT tl.id) AS link_count,
                 count(DISTINCT pe.id) AS explanation_count
          FROM doctrine_topics dt
          LEFT JOIN topic_links tl ON tl.topic_id = dt.id
          LEFT JOIN plain_explanations pe ON pe.topic_id = dt.id
          WHERE dt.slug = %(topic)s
          GROUP BY dt.id, dt.slug, dt.title, dt.pillar_title, dt.question, dt.summary, dt.sort_order, dt.status
          LIMIT 1
        ) t;
    """,
    "topic_links": """
        SELECT jsonb_agg(to_jsonb(t) ORDER BY role_order, sort_order, target_title)
        FROM (
          SELECT
            CASE tl.role
              WHEN 'core' THEN 1
              WHEN 'support' THEN 2
              WHEN 'background' THEN 3
              ELSE 4
            END AS role_order,
            tl.role, tl.notes, tl.sort_order, tl.target_type,
            COALESCE(li.slug, ce.slug, lu.canonical_ref) AS target_slug,
            COALESCE(li.short_title, ce.title, lu.canonical_ref) AS target_title,
            li.instrument_type,
            lv.slug AS version_slug,
            lv.version_label,
            lu.unit_number,
            lu.unit_number_int,
            lu.canonical_ref,
            lu.text,
            ce.event_type,
            ce.start_date
          FROM topic_links tl
          JOIN doctrine_topics dt ON dt.id = tl.topic_id
          LEFT JOIN legal_instruments li ON tl.target_type = 'legal_instrument' AND tl.target_id = li.id
          LEFT JOIN legal_units lu ON tl.target_type = 'legal_unit' AND tl.target_id = lu.id
          LEFT JOIN legal_versions lv ON lu.version_id = lv.id
          LEFT JOIN context_events ce ON tl.target_type = 'context_event' AND tl.target_id = ce.id
          WHERE dt.slug = %(topic)s
        ) t;
    """,
    "topic_explanations": """
        SELECT jsonb_agg(to_jsonb(t) ORDER BY explanation_type, title)
        FROM (
          SELECT pe.explanation_type, pe.title, pe.body, pe.confidence, pe.author,
                 s.title AS source_title, s.url AS source_url
          FROM plain_explanations pe
          JOIN doctrine_topics dt ON dt.id = pe.topic_id
          LEFT JOIN sources s ON s.id = pe.source_id
          WHERE dt.slug = %(topic)s
        ) t;
    """,
    "instrument_topics": """
        SELECT jsonb_agg(to_jsonb(t) ORDER BY sort_order, title)
        FROM (
          SELECT DISTINCT dt.slug, dt.title, dt.pillar_title, dt.question, dt.summary, dt.sort_order
          FROM doctrine_topics dt
          JOIN topic_links tl ON tl.topic_id = dt.id
          JOIN legal_instruments li ON tl.target_type = 'legal_instrument' AND tl.target_id = li.id
          WHERE li.slug = %(instrument)s
        ) t;
    """,
    "unit_topics": """
        SELECT jsonb_agg(to_jsonb(t) ORDER BY sort_order, title)
        FROM (
          SELECT DISTINCT dt.slug, dt.title, dt.pillar_title, dt.question, dt.summary, dt.sort_order
          FROM doctrine_topics dt
          JOIN topic_links tl ON tl.topic_id = dt.id
          JOIN legal_units lu ON tl.target_type = 'legal_unit' AND tl.target_id = lu.id
          WHERE lu.canonical_ref = %(canonical_ref)s
        ) t;
    """,
    "domains": """
        SELECT jsonb_agg(to_jsonb(t) ORDER BY sort_order, name)
        FROM (
          SELECT ld.slug, ld.name, ld.description, ld.sort_order,
                 count(DISTINCT idm.instrument_id) AS instrument_count
          FROM legal_domains ld
          LEFT JOIN instrument_domains idm ON idm.domain_id = ld.id
          GROUP BY ld.id, ld.slug, ld.name, ld.description, ld.sort_order
        ) t;
    """,
    "instruments": """
        SELECT jsonb_agg(to_jsonb(t) ORDER BY subject_area, first_enacted_date NULLS LAST, short_title)
        FROM (
          SELECT slug, short_title, canonical_title, instrument_type, subject_area,
                 first_enacted_date, current_version_slug, current_version_label,
                 effective_date, status, domains, source_title, source_url
          FROM v_legal_instrument_catalog
        ) t;
    """,
    "instrument_detail": """
        SELECT to_jsonb(t)
        FROM (
          SELECT slug, short_title, canonical_title, instrument_type, subject_area,
                 first_enacted_date, current_version_slug, current_version_label,
                 effective_date, status, domains, source_title, source_url
          FROM v_legal_instrument_catalog
          WHERE slug = %(instrument)s
          LIMIT 1
        ) t;
    """,
    "instrument_versions": """
        SELECT jsonb_agg(to_jsonb(t) ORDER BY version_sequence)
        FROM (
          SELECT lv.slug, lv.version_label, lv.version_sequence, lv.action_type,
                 lv.adopted_date, lv.effective_date, lv.status
          FROM legal_versions lv
          JOIN legal_instruments li ON li.id = lv.instrument_id
          WHERE li.slug = %(instrument)s
        ) t;
    """,
    "instrument_units": """
        SELECT jsonb_agg(to_jsonb(t) ORDER BY version_sequence DESC, order_index)
        FROM (
          SELECT li.slug AS instrument_slug, li.short_title AS instrument_title,
                 lv.slug AS version_slug, lv.version_label, lv.version_sequence,
                 lu.unit_number, lu.unit_number_int, lu.canonical_ref, lu.text, lu.order_index
          FROM legal_units lu
          JOIN legal_versions lv ON lv.id = lu.version_id
          JOIN legal_instruments li ON li.id = lv.instrument_id
          WHERE li.slug = %(instrument)s
          LIMIT 60
        ) t;
    """,
    "instrument_unit_detail": """
        SELECT to_jsonb(t)
        FROM (
          SELECT li.slug AS instrument_slug, li.short_title AS instrument_title,
                 lv.slug AS version_slug, lv.version_label, lv.version_sequence,
                 lu.unit_number, lu.unit_number_int, lu.canonical_ref, lu.text, lu.order_index
          FROM legal_units lu
          JOIN legal_versions lv ON lv.id = lu.version_id
          JOIN legal_instruments li ON li.id = lv.instrument_id
          WHERE li.slug = %(instrument)s
            AND lu.unit_type = 'article'
            AND lu.unit_number_int = %(unit)s
          LIMIT 1
        ) t;
    """,
    "instrument_relations": """
        SELECT jsonb_agg(to_jsonb(t) ORDER BY confidence DESC, object_title)
        FROM (
          SELECT lr.relation_type, lr.claim_text, lr.confidence, lr.evidence_level, lr.notes,
                 lr.object_type, s.title AS source_title, s.url AS source_url,
                 COALESCE(oi.slug, od.slug, oc.slug, ou.canonical_ref) AS object_slug,
                 COALESCE(oi.short_title, od.name, oc.title, ou.canonical_ref) AS object_title
          FROM legal_relations lr
          LEFT JOIN sources s ON s.id = lr.source_id
          LEFT JOIN legal_instruments si ON lr.subject_type = 'legal_instrument' AND lr.subject_id = si.id
          LEFT JOIN legal_instruments oi ON lr.object_type = 'legal_instrument' AND lr.object_id = oi.id
          LEFT JOIN legal_domains od ON lr.object_type = 'legal_domain' AND lr.object_id = od.id
          LEFT JOIN context_events oc ON lr.object_type = 'context_event' AND lr.object_id = oc.id
          LEFT JOIN legal_units ou ON lr.object_type = 'legal_unit' AND lr.object_id = ou.id
          WHERE si.slug = %(instrument)s
        ) t;
    """,
    "domain_detail": """
        SELECT to_jsonb(t)
        FROM (
          SELECT ld.slug, ld.name, ld.description, ld.sort_order,
                 count(DISTINCT idm.instrument_id) AS instrument_count
          FROM legal_domains ld
          LEFT JOIN instrument_domains idm ON idm.domain_id = ld.id
          WHERE ld.slug = %(domain)s
          GROUP BY ld.id, ld.slug, ld.name, ld.description, ld.sort_order
          LIMIT 1
        ) t;
    """,
    "domain_instruments": """
        SELECT jsonb_agg(to_jsonb(t) ORDER BY is_primary DESC, first_enacted_date NULLS LAST, short_title)
        FROM (
          SELECT vic.slug, vic.short_title, vic.canonical_title, vic.instrument_type,
                 vic.current_version_slug, vic.current_version_label, vic.effective_date,
                 vic.domains, vic.first_enacted_date, idm.is_primary
          FROM instrument_domains idm
          JOIN legal_domains ld ON ld.id = idm.domain_id
          JOIN v_legal_instrument_catalog vic ON vic.id = idm.instrument_id
          WHERE ld.slug = %(domain)s
        ) t;
    """,
    "company_relations": """
        SELECT jsonb_agg(to_jsonb(t) ORDER BY confidence DESC, object_title)
        FROM (
          SELECT lr.relation_type, lr.claim_text, lr.confidence, lr.evidence_level, lr.object_type,
                 s.title AS source_title, s.url AS source_url,
                 COALESCE(oi.slug, oc.slug, ou.canonical_ref) AS object_slug,
                 COALESCE(oi.short_title, oc.title, ou.canonical_ref) AS object_title
          FROM legal_relations lr
          LEFT JOIN sources s ON s.id = lr.source_id
          LEFT JOIN legal_instruments si ON lr.subject_type = 'legal_instrument' AND lr.subject_id = si.id
          LEFT JOIN legal_instruments oi ON lr.object_type = 'legal_instrument' AND lr.object_id = oi.id
          LEFT JOIN context_events oc ON lr.object_type = 'context_event' AND lr.object_id = oc.id
          LEFT JOIN legal_units ou ON lr.object_type = 'legal_unit' AND lr.object_id = ou.id
          WHERE si.slug = 'cn_company_law'
        ) t;
    """,
    "article_relations": """
        SELECT jsonb_agg(to_jsonb(t) ORDER BY confidence DESC, object_title)
        FROM (
          SELECT lr.relation_type, lr.claim_text, lr.confidence, lr.evidence_level, lr.object_type,
                 s.title AS source_title, s.url AS source_url,
                 COALESCE(oi.short_title, ou.canonical_ref) AS object_title,
                 COALESCE(oi.slug, ou.canonical_ref) AS object_slug
          FROM legal_relations lr
          LEFT JOIN sources s ON s.id = lr.source_id
          LEFT JOIN legal_units su ON lr.subject_type = 'legal_unit' AND lr.subject_id = su.id
          LEFT JOIN legal_units ou ON lr.object_type = 'legal_unit' AND lr.object_id = ou.id
          LEFT JOIN legal_versions ov ON ou.version_id = ov.id
          LEFT JOIN legal_instruments oi ON ov.instrument_id = oi.id
          WHERE su.canonical_ref = %(canonical_ref)s
        ) t;
    """,
    "versions": """
        SELECT jsonb_agg(to_jsonb(t) ORDER BY version_sequence)
        FROM (
          SELECT slug, version_label, version_sequence, action_type,
                 adopted_date, effective_date, status, chapter_count,
                 article_count, official_source_title, official_source_url
          FROM v_company_law_versions
        ) t;
    """,
    "contexts": """
        SELECT jsonb_agg(to_jsonb(t) ORDER BY version_sequence, confidence DESC)
        FROM (
          SELECT lv.version_sequence, lv.version_label, ce.event_type, ce.title,
                 ce.start_date, cl.relation_type, cl.claim_text, cl.confidence,
                 cl.evidence_level, s.title AS source_title, s.url AS source_url
          FROM context_links cl
          JOIN legal_versions lv
            ON cl.subject_type = 'legal_version' AND cl.subject_id = lv.id
          JOIN context_events ce
            ON cl.object_type = 'context_event' AND cl.object_id = ce.id
          JOIN sources s ON s.id = cl.source_id
          ORDER BY lv.version_sequence, cl.confidence DESC
        ) t;
    """,
    "sources": """
        SELECT jsonb_agg(to_jsonb(t) ORDER BY reliability_tier, slug)
        FROM (
          SELECT slug, source_type, title, url, publisher, published_at,
                 reliability_tier, notes
          FROM sources
        ) t;
    """,
    "graph_node": """
        SELECT to_jsonb(t)
        FROM (
          SELECT node_key, node_type, ref, title, subtitle, href
          FROM v_graph_nodes
          WHERE node_key = %(node_key)s
          LIMIT 1
        ) t;
    """,
    "graph_neighbors": """
        SELECT jsonb_agg(to_jsonb(t) ORDER BY relation_type, title)
        FROM (
          SELECT
            CASE
              WHEN e.from_node_key = %(node_key)s THEN 'outbound'
              ELSE 'inbound'
            END AS direction,
            e.relation_type, e.claim_text, e.confidence, e.evidence_level,
            s.title AS source_title, s.url AS source_url,
            n.node_key, n.node_type, n.ref, n.title, n.subtitle, n.href
          FROM v_graph_edges e
          JOIN v_graph_nodes n
            ON n.node_key = CASE
              WHEN e.from_node_key = %(node_key)s THEN e.to_node_key
              ELSE e.from_node_key
            END
          LEFT JOIN sources s ON s.id = e.source_id
          WHERE e.from_node_key = %(node_key)s
             OR e.to_node_key = %(node_key)s
          LIMIT 60
        ) t;
    """,
    "graph_path": """
        WITH RECURSIVE walk AS (
          SELECT
            %(from_node_key)s::text AS current_key,
            ARRAY[%(from_node_key)s::text] AS visited,
            ARRAY[]::text[] AS path_edges,
            0 AS depth
          UNION ALL
          SELECT
            CASE
              WHEN e.from_node_key = walk.current_key THEN e.to_node_key
              ELSE e.from_node_key
            END AS current_key,
            walk.visited || CASE
              WHEN e.from_node_key = walk.current_key THEN e.to_node_key
              ELSE e.from_node_key
            END,
            walk.path_edges || e.edge_key,
            walk.depth + 1
          FROM walk
          JOIN (
            SELECT edge_key, from_node_key, to_node_key
            FROM v_graph_edges
          ) e
            ON e.from_node_key = walk.current_key OR e.to_node_key = walk.current_key
          WHERE walk.depth < 4
            AND NOT (
              CASE
                WHEN e.from_node_key = walk.current_key THEN e.to_node_key
                ELSE e.from_node_key
              END = ANY(walk.visited)
            )
        ),
        chosen AS (
          SELECT visited, path_edges, depth
          FROM walk
          WHERE current_key = %(to_node_key)s
          ORDER BY depth
          LIMIT 1
        )
        SELECT jsonb_build_object(
          'nodes',
          (
            SELECT jsonb_agg(to_jsonb(n) ORDER BY ord)
            FROM chosen c
            JOIN LATERAL unnest(c.visited) WITH ORDINALITY AS u(node_key, ord) ON true
            JOIN v_graph_nodes n ON n.node_key = u.node_key
          ),
          'edges',
          (
            SELECT jsonb_agg(to_jsonb(e) ORDER BY ord)
            FROM chosen c
            JOIN LATERAL unnest(c.path_edges) WITH ORDINALITY AS u(edge_key, ord) ON true
            JOIN v_graph_edges e ON e.edge_key = u.edge_key
          )
        )
        FROM chosen;
    """,
    "candidate_list": """
        SELECT jsonb_agg(to_jsonb(t) ORDER BY created_at DESC)
        FROM (
          SELECT
            rc.id,
            rc.subject_type, rc.object_type, rc.relation_type,
            rc.claim_text, rc.confidence, rc.proposer, rc.status,
            rc.review_note, rc.created_at, rc.reviewed_at,
            COALESCE(si.short_title, sv.version_label, su.canonical_ref, sce.title) AS subject_title,
            COALESCE(oi.short_title, ov.version_label, ou.canonical_ref, oce.title) AS object_title,
            s.title AS source_title
          FROM relation_candidates rc
          LEFT JOIN legal_instruments si ON rc.subject_type = 'legal_instrument' AND rc.subject_id = si.id
          LEFT JOIN legal_versions sv ON rc.subject_type = 'legal_version' AND rc.subject_id = sv.id
          LEFT JOIN legal_units su ON rc.subject_type = 'legal_unit' AND rc.subject_id = su.id
          LEFT JOIN context_events sce ON rc.subject_type = 'context_event' AND rc.subject_id = sce.id
          LEFT JOIN legal_instruments oi ON rc.object_type = 'legal_instrument' AND rc.object_id = oi.id
          LEFT JOIN legal_versions ov ON rc.object_type = 'legal_version' AND rc.object_id = ov.id
          LEFT JOIN legal_units ou ON rc.object_type = 'legal_unit' AND rc.object_id = ou.id
          LEFT JOIN context_events oce ON rc.object_type = 'context_event' AND rc.object_id = oce.id
          LEFT JOIN sources s ON s.id = rc.proposed_source_id
          WHERE (%(status)s = '' OR rc.status = %(status)s)
          LIMIT 120
        ) t;
    """,
    "candidate_detail": """
        SELECT to_jsonb(t)
        FROM (
          SELECT
            rc.id,
            rc.subject_type, rc.subject_id,
            rc.object_type, rc.object_id,
            rc.relation_type, rc.claim_text, rc.confidence,
            rc.proposer, rc.status, rc.review_note,
            rc.excerpt_text, rc.created_at, rc.reviewed_at,
            rc.accepted_relation_id,
            COALESCE(si.short_title, sv.version_label, su.canonical_ref, sce.title) AS subject_title,
            COALESCE(oi.short_title, ov.version_label, ou.canonical_ref, oce.title) AS object_title,
            CASE
              WHEN rc.subject_type = 'legal_instrument' THEN 'legal_instrument:' || si.slug
              WHEN rc.subject_type = 'legal_version' THEN 'legal_version:' || sv.slug
              WHEN rc.subject_type = 'legal_unit' THEN 'legal_unit:' || su.canonical_ref
              WHEN rc.subject_type = 'context_event' THEN 'context_event:' || sce.slug
            END AS subject_node_key,
            CASE
              WHEN rc.object_type = 'legal_instrument' THEN 'legal_instrument:' || oi.slug
              WHEN rc.object_type = 'legal_version' THEN 'legal_version:' || ov.slug
              WHEN rc.object_type = 'legal_unit' THEN 'legal_unit:' || ou.canonical_ref
              WHEN rc.object_type = 'context_event' THEN 'context_event:' || oce.slug
            END AS object_node_key,
            s.id AS source_id, s.slug AS source_slug, s.title AS source_title, s.url AS source_url,
            se.id AS source_excerpt_id, se.excerpt_text AS source_excerpt_text, se.locator
          FROM relation_candidates rc
          LEFT JOIN legal_instruments si ON rc.subject_type = 'legal_instrument' AND rc.subject_id = si.id
          LEFT JOIN legal_versions sv ON rc.subject_type = 'legal_version' AND rc.subject_id = sv.id
          LEFT JOIN legal_units su ON rc.subject_type = 'legal_unit' AND rc.subject_id = su.id
          LEFT JOIN context_events sce ON rc.subject_type = 'context_event' AND rc.subject_id = sce.id
          LEFT JOIN legal_instruments oi ON rc.object_type = 'legal_instrument' AND rc.object_id = oi.id
          LEFT JOIN legal_versions ov ON rc.object_type = 'legal_version' AND rc.object_id = ov.id
          LEFT JOIN legal_units ou ON rc.object_type = 'legal_unit' AND rc.object_id = ou.id
          LEFT JOIN context_events oce ON rc.object_type = 'context_event' AND rc.object_id = oce.id
          LEFT JOIN sources s ON s.id = rc.proposed_source_id
          LEFT JOIN source_excerpts se ON se.id = rc.source_excerpt_id
          WHERE rc.id::text = %(candidate_id)s
          LIMIT 1
        ) t;
    """,
    "source_excerpts": """
        SELECT jsonb_agg(to_jsonb(t) ORDER BY extracted_at DESC)
        FROM (
          SELECT se.id, se.excerpt_text, se.locator, se.quote_limit_ok, se.extracted_at
          FROM source_excerpts se
          JOIN sources s ON s.id = se.source_id
          WHERE s.slug = %(source_slug)s
        ) t;
    """,
    "stats": """
        SELECT jsonb_build_object(
          'instruments', (SELECT count(*) FROM legal_instruments),
          'domains', (SELECT count(*) FROM legal_domains),
          'topics', (SELECT count(*) FROM doctrine_topics),
          'versions', (SELECT count(*) FROM legal_versions),
          'sources', (SELECT count(*) FROM sources),
          'context_events', (SELECT count(*) FROM context_events),
          'context_links', (SELECT count(*) FROM context_links),
          'legal_relations', (SELECT count(*) FROM legal_relations),
          'relation_candidates', (SELECT count(*) FROM relation_candidates),
          'plain_explanations', (SELECT count(*) FROM plain_explanations),
          'legal_units', (SELECT count(*) FROM legal_units)
        );
    """,
    "search": """
        SELECT jsonb_agg(to_jsonb(t) ORDER BY rank DESC NULLS LAST, version_sequence, order_index)
        FROM (
          SELECT li.slug AS instrument_slug, li.short_title AS instrument_title,
                 lv.slug AS version_slug, lv.version_label, lv.version_sequence,
                 lu.canonical_ref, lu.unit_type, lu.unit_number, lu.unit_number_int,
                 lu.title, lu.text,
                 ts_rank(
                   to_tsvector('simple', coalesce(lu.title, '') || ' ' || coalesce(lu.text, '')),
                   plainto_tsquery('simple', %(query)s)
                 ) AS rank,
                 lu.order_index
          FROM legal_units lu
          JOIN legal_versions lv ON lv.id = lu.version_id
          JOIN legal_instruments li ON li.id = lv.instrument_id
          WHERE to_tsvector('simple', coalesce(lu.title, '') || ' ' || coalesce(lu.text, ''))
                @@ plainto_tsquery('simple', %(query)s)
          LIMIT 50
        ) t;
    """,
    "articles": """
        SELECT jsonb_agg(to_jsonb(t) ORDER BY order_index)
        FROM (
          SELECT lv.slug AS version_slug, lv.version_label, lu.unit_number,
                 lu.unit_number_int, lu.canonical_ref, lu.text, lu.order_index
          FROM legal_units lu
          JOIN legal_versions lv ON lv.id = lu.version_id
          WHERE lv.slug = %(version)s AND lu.unit_type = 'article'
          ORDER BY lu.order_index
        ) t;
    """,
    "article": """
        SELECT to_jsonb(t)
        FROM (
          SELECT lv.slug AS version_slug, lv.version_label, lu.unit_number,
                 lu.unit_number_int, lu.canonical_ref, lu.text, lu.order_index
          FROM legal_units lu
          JOIN legal_versions lv ON lv.id = lu.version_id
          WHERE lv.slug = %(version)s
            AND lu.unit_type = 'article'
            AND lu.unit_number_int = %(article)s
          LIMIT 1
        ) t;
    """,
    "compare": """
        SELECT jsonb_agg(to_jsonb(t) ORDER BY version_sequence)
        FROM (
          SELECT lv.slug AS version_slug, lv.version_label, lv.version_sequence,
                 lu.unit_number, lu.unit_number_int, lu.canonical_ref, lu.text
          FROM legal_units lu
          JOIN legal_versions lv ON lv.id = lu.version_id
          WHERE lv.slug IN (%(left_version)s, %(right_version)s)
            AND lu.unit_type = 'article'
            AND lu.unit_number_int = %(article)s
          ORDER BY lv.version_sequence
        ) t;
    """,
}
