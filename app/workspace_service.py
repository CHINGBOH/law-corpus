from __future__ import annotations

import re

from db_access import psql_json
from graph_service import get_neighbors, get_node, get_path
from query_defs import PILLARS, QUERIES
from review_service import accept_candidate, edit_candidate, get_candidate, list_candidates, reject_candidate

STATUS_OPTIONS = ["pending", "needs_edit", "accepted", "rejected", ""]


NODE_TYPE_LABELS = {
    "legal_instrument": "规范",
    "legal_version": "版本",
    "legal_unit": "条文",
    "context_event": "政策/历史事件",
}

RELATION_LABELS = {
    "based_on": "以上位法为基础",
    "specifies": "具体化",
    "supplements": "补充规范",
    "limits": "限制",
    "constrained_by": "受其约束",
    "same_domain": "同一法域",
    "related_to": "相关",
    "interacts_with": "制度联动",
    "policy_background": "政策背景",
    "interpreted_by": "解释来源",
    "contains": "结构隶属",
}

CANDIDATE_STATUS_LABELS = {
    "pending": "待审核",
    "needs_edit": "待改写",
    "accepted": "已转正",
    "rejected": "已驳回",
}

GRAPH_PRESETS = [
    {"label": "资本信用", "node_key": "legal_unit:company_law:2023:article_47"},
    {"label": "出资加速到期", "node_key": "legal_unit:company_law:2023:article_54"},
    {"label": "法人独立责任", "node_key": "legal_unit:civil_code:2020:article_60"},
    {"label": "法定代表人", "node_key": "legal_unit:civil_code:2020:article_61"},
    {"label": "登记公示", "node_key": "legal_unit:registration_regulation:2021:article_8"},
    {"label": "2013 改革", "node_key": "context_event:cn_registration_capital_reform_2013"},
]

GRAPH_RELATION_GROUPS = {
    "policy_background": {"label": "政策背景", "relation_types": {"policy_background"}},
    "upstream_supporting": {
        "label": "上位/配套规范",
        "relation_types": {"based_on", "specifies", "supplements", "constrained_by", "limits"},
    },
    "institutional_linkage": {
        "label": "制度联动",
        "relation_types": {"interacts_with", "related_to", "same_domain", "interpreted_by"},
    },
}

INSTRUMENT_SLUG_PREFIXES = {
    "civil_code:": "cn_civil_code",
    "constitution:": "cn_constitution",
    "securities_law:": "cn_securities_law",
    "bankruptcy_law:": "cn_enterprise_bankruptcy_law",
    "registration_regulation:": "cn_market_entity_registration_regulation",
    "state_assets_law:": "cn_state_owned_assets_law",
    "foreign_investment_law:": "cn_foreign_investment_law",
    "partnership_law:": "cn_partnership_enterprise_law",
    "sole_proprietorship_law:": "cn_sole_proprietorship_law",
}


def node_type_label(value: object) -> str:
    return NODE_TYPE_LABELS.get(str(value), str(value))


def relation_label(value: object) -> str:
    return RELATION_LABELS.get(str(value), str(value))


def candidate_status_label(value: object) -> str:
    return CANDIDATE_STATUS_LABELS.get(str(value), str(value))


def article_no_from_ref(canonical_ref: object) -> int:
    text = "" if canonical_ref is None else str(canonical_ref)
    match = re.search(r"article_(\d+)$", text)
    return int(match.group(1)) if match else 1


def version_slug_from_ref(canonical_ref: object) -> str:
    text = "" if canonical_ref is None else str(canonical_ref)
    match = re.match(r"company_law:(\d{4}):", text)
    if not match:
        return "cn_company_law_2023"
    return f"cn_company_law_{match.group(1)}"


def infer_instrument_slug_from_ref(canonical_ref: object) -> str:
    text = "" if canonical_ref is None else str(canonical_ref)
    for prefix, slug in INSTRUMENT_SLUG_PREFIXES.items():
        if text.startswith(prefix):
            return slug
    return ""


def relation_href(relation: dict[str, object]) -> str:
    if relation.get("object_type") == "legal_instrument" and relation.get("object_slug"):
        return f"/instrument?slug={relation['object_slug']}"
    if relation.get("object_type") == "context_event":
        return "/api/contexts"
    if relation.get("object_type") == "legal_unit":
        object_slug = str(relation.get("object_slug") or "")
        if object_slug.startswith("company_law:"):
            slug = version_slug_from_ref(object_slug)
            article = article_no_from_ref(object_slug)
            return f"/law?version={slug}&article={article}"
        article = article_no_from_ref(object_slug)
        instrument_slug = infer_instrument_slug_from_ref(object_slug)
        if instrument_slug:
            return f"/instrument-reader?slug={instrument_slug}&unit={article}"
    return "/"


def topic_target_href(link: dict[str, object]) -> str:
    target_type = link.get("target_type")
    if target_type == "legal_instrument":
        return f"/instrument?slug={link.get('target_slug')}"
    if target_type == "context_event":
        return "/api/contexts"
    if target_type == "legal_unit":
        canonical_ref = str(link.get("canonical_ref") or "")
        if canonical_ref.startswith("company_law:"):
            return f"/law?version={version_slug_from_ref(canonical_ref)}&article={article_no_from_ref(canonical_ref)}"
        instrument_slug = infer_instrument_slug_from_ref(canonical_ref)
        if instrument_slug:
            return f"/instrument-reader?slug={instrument_slug}&unit={article_no_from_ref(canonical_ref)}"
    return "/"


def graph_hint(node: dict[str, object], meaningful_neighbors: list[dict[str, object]]) -> str:
    node_type = str(node.get("node_type") or "")
    ref = str(node.get("ref") or "")
    if node_type == "legal_unit" and ref.startswith("company_law:"):
        return "先看本条直接约束谁、受谁约束，再看它挂在哪个专题和政策背景上。"
    if node_type == "legal_unit":
        return "先把这条当一般法或配套法节点，再看它与公司法条文的补充或联动关系。"
    if node_type == "legal_version":
        return "版本节点适合看修法背景、结构承接和关键制度变化，不适合直接替代条文阅读。"
    if node_type == "context_event":
        return "事件节点不是法条本身，要重点看它影响了哪些版本、哪些条文、哪类制度。"
    if meaningful_neighbors:
        return "先看一跳制度关系，再决定是否沿路径继续穿透。"
    return "当前节点关系还少，优先补证据和候选关系。"


def _neighbor_summary(item: dict[str, object]) -> dict[str, object]:
    return {
        "direction": item.get("direction"),
        "relation_type": item.get("relation_type"),
        "relation_type_label": relation_label(item.get("relation_type")),
        "claim_text": item.get("claim_text"),
        "confidence": item.get("confidence"),
        "evidence_level": item.get("evidence_level"),
        "source_title": item.get("source_title"),
        "source_url": item.get("source_url"),
        "target": {
            "node_key": item.get("node_key"),
            "node_type": item.get("node_type"),
            "node_type_label": node_type_label(item.get("node_type")),
            "ref": item.get("ref"),
            "title": item.get("title"),
            "subtitle": item.get("subtitle"),
            "href": item.get("href"),
        },
    }


def graph_view(node_key: str, to_node_key: str = "") -> dict[str, object]:
    selected = node_key or "legal_instrument:cn_company_law"
    node = get_node(selected)
    if not node:
        return {"ok": False, "error": "node not found", "node_key": selected}

    neighbors = get_neighbors(selected) or []
    structural_neighbors = [item for item in neighbors if item.get("relation_type") == "contains"]
    meaningful_neighbors = [item for item in neighbors if item.get("relation_type") != "contains"]

    grouped_relations: dict[str, dict[str, object]] = {}
    used_ids: set[int] = set()
    for key, group in GRAPH_RELATION_GROUPS.items():
        items = [item for item in meaningful_neighbors if item.get("relation_type") in group["relation_types"]]
        used_ids.update(id(item) for item in items)
        grouped_relations[key] = {
            "label": group["label"],
            "items": [_neighbor_summary(item) for item in items],
        }
    other_items = [item for item in meaningful_neighbors if id(item) not in used_ids]
    grouped_relations["other"] = {"label": "其他", "items": [_neighbor_summary(item) for item in other_items]}

    path_payload = None
    if to_node_key:
        path = get_path(selected, to_node_key) or {"nodes": [], "edges": []}
        path_payload = {
            "requested_to": to_node_key,
            "nodes": path.get("nodes") or [],
            "edges": path.get("edges") or [],
        }

    return {
        "ok": True,
        "node": {
            "node_key": node.get("node_key"),
            "node_type": node.get("node_type"),
            "node_type_label": node_type_label(node.get("node_type")),
            "ref": node.get("ref"),
            "title": node.get("title"),
            "subtitle": node.get("subtitle"),
            "href": node.get("href"),
            "hint": graph_hint(node, meaningful_neighbors),
            "can_extract_candidates": node.get("node_type") == "legal_unit",
        },
        "counts": {
            "meaningful_neighbors": len(meaningful_neighbors),
            "structural_neighbors": len(structural_neighbors),
        },
        "structural_neighbors": [
            {
                "node_key": item.get("node_key"),
                "title": item.get("title"),
                "subtitle": item.get("subtitle"),
                "href": item.get("href"),
            }
            for item in structural_neighbors[:6]
        ],
        "grouped_relations": grouped_relations,
        "neighbors": [_neighbor_summary(item) for item in meaningful_neighbors],
        "presets": GRAPH_PRESETS,
        "path": path_payload,
    }


def _candidate_summary(item: dict[str, object]) -> dict[str, object]:
    return {
        "id": item.get("id"),
        "relation_type": item.get("relation_type"),
        "relation_type_label": relation_label(item.get("relation_type")),
        "subject_title": item.get("subject_title"),
        "object_title": item.get("object_title"),
        "status": item.get("status"),
        "status_label": candidate_status_label(item.get("status")),
        "source_title": item.get("source_title"),
    }


def _candidate_detail(item: dict[str, object]) -> dict[str, object]:
    subject_node_key = item.get("subject_node_key") or ""
    object_node_key = item.get("object_node_key") or ""
    return {
        "id": item.get("id"),
        "status": item.get("status"),
        "status_label": candidate_status_label(item.get("status")),
        "proposer": item.get("proposer"),
        "subject_title": item.get("subject_title"),
        "object_title": item.get("object_title"),
        "claim_text": item.get("claim_text"),
        "relation_type": item.get("relation_type"),
        "relation_type_label": relation_label(item.get("relation_type")),
        "confidence": item.get("confidence"),
        "review_note": item.get("review_note"),
        "subject_node_key": subject_node_key,
        "object_node_key": object_node_key,
        "graph_hrefs": {
            "subject": f"/graph?node_key={subject_node_key}" if subject_node_key else "",
            "object": f"/graph?node_key={object_node_key}" if object_node_key else "",
            "path": (
                f"/graph?node_key={subject_node_key}&to_node_key={object_node_key}"
                if subject_node_key and object_node_key
                else ""
            ),
        },
        "evidence": {
            "source_title": item.get("source_title"),
            "source_url": item.get("source_url"),
            "excerpt_text": item.get("source_excerpt_text") or item.get("excerpt_text"),
        },
    }


def review_view(status: str, candidate_id: str = "") -> dict[str, object]:
    selected_status = status or "pending"
    candidates = list_candidates(selected_status) or []
    selected_id = candidate_id or (str(candidates[0]["id"]) if candidates else "")
    detail = get_candidate(selected_id) if selected_id else {}
    return {
        "status": selected_status,
        "status_options": STATUS_OPTIONS,
        "candidates": [_candidate_summary(item) for item in candidates],
        "selected_id": selected_id or None,
        "detail": _candidate_detail(detail) if detail else None,
    }


def _review_bundle_after_mutation(status: str, candidate_id: str) -> dict[str, object]:
    selected_status = status or "pending"
    candidates = list_candidates(selected_status) or []
    ids = {str(item["id"]) for item in candidates}
    selected_id = candidate_id if candidate_id in ids else (str(candidates[0]["id"]) if candidates else "")
    detail = get_candidate(selected_id) if selected_id else {}
    return {
        "status": selected_status,
        "status_options": STATUS_OPTIONS,
        "candidates": [_candidate_summary(item) for item in candidates],
        "selected_id": selected_id or None,
        "detail": _candidate_detail(detail) if detail else None,
    }


def review_accept(candidate_id: str, status: str) -> dict[str, object]:
    accept_candidate(candidate_id)
    return _review_bundle_after_mutation(status, candidate_id)


def review_reject(candidate_id: str, review_note: str, status: str) -> dict[str, object]:
    reject_candidate(candidate_id, review_note)
    return _review_bundle_after_mutation(status, candidate_id)


def review_edit(
    candidate_id: str,
    relation_type: str,
    claim_text: str,
    confidence: str,
    review_note: str,
    status: str,
) -> dict[str, object]:
    edit_candidate(candidate_id, relation_type, claim_text, confidence, review_note)
    return _review_bundle_after_mutation(status, candidate_id)


def _paginate_nav(items: list[dict[str, object]], current_no: int, href_fn) -> list[dict[str, object]]:
    groups = []
    for start in range(1, len(items) + 1, 20):
        chunk = items[start - 1 : start + 19]
        if not chunk:
            continue
        first_no = int(chunk[0].get("unit_number_int") or 0)
        last_no = int(chunk[-1].get("unit_number_int") or 0)
        groups.append(
            {
                "start": first_no,
                "end": last_no,
                "open": first_no <= current_no <= last_no,
                "items": [
                    {
                        "unit_number": item.get("unit_number"),
                        "unit_number_int": item.get("unit_number_int"),
                        "href": href_fn(item),
                        "active": int(item.get("unit_number_int") or 0) == current_no,
                    }
                    for item in chunk
                ],
            }
        )
    return groups


def _reader_sidebar(canonical_ref: str, extra_actions: list[dict[str, str]]) -> dict[str, object]:
    relations = psql_json(QUERIES["article_relations"], {"canonical_ref": canonical_ref}) if canonical_ref else []
    topics = psql_json(QUERIES["unit_topics"], {"canonical_ref": canonical_ref}) if canonical_ref else []
    return {
        "actions": extra_actions
        + [{"label": "在图谱中打开", "href": f"/graph?node_key=legal_unit:{canonical_ref}"}],
        "relations": [
            {"label": f"{relation_label(r['relation_type'])} · {r.get('object_title')}", "href": relation_href(r)}
            for r in (relations or [])[:8]
        ],
        "topics": [
            {"label": f"{t['title']} · {t.get('pillar_title')}", "href": f"/topic?slug={t['slug']}"}
            for t in (topics or [])[:8]
        ],
    }


def reader_view(version: str, article: int | None) -> dict[str, object]:
    versions = psql_json(QUERIES["versions"]) or []
    selected = version or "cn_company_law_2023"
    articles = psql_json(QUERIES["articles"], {"version": selected}) or []
    current = None
    if article:
        current = psql_json(QUERIES["article"], {"version": selected, "article": str(article)})
    if not current and articles:
        current = articles[0]
    if not current:
        return {"ok": False, "error": "no articles found for version", "version": selected}

    current_no = int(current.get("unit_number_int") or 1)
    selected_version_label = next((v["version_label"] for v in versions if v["slug"] == selected), selected)
    ref = str(current.get("canonical_ref") or "")

    def href_fn(item: dict[str, object]) -> str:
        return f"/law?version={selected}&article={item.get('unit_number_int')}"

    sidebar = _reader_sidebar(
        ref,
        [
            {"label": "与 2023 同条号对比", "href": f"/compare?left={selected}&right=cn_company_law_2023&article={current_no}"},
            {"label": "与 2013 同条号对比", "href": f"/compare?left=cn_company_law_2013&right=cn_company_law_2023&article={current_no}"},
            {"label": "搜索本条号", "href": f"/search?q={current.get('unit_number')}"},
        ],
    )
    sidebar["meta"] = {"label": selected_version_label, "ref": ref}
    sidebar["tip"] = "同条号对比只说明位置差异，不等于制度继承。涉及制度演化时，应优先看法体系关系。"

    return {
        "ok": True,
        "mode": "law",
        "title": "原文阅读",
        "versions": [{"slug": v["slug"], "version_label": v["version_label"]} for v in versions],
        "selected_version": selected,
        "article": current,
        "nav_groups": _paginate_nav(articles, current_no, href_fn),
        "prev": {
            "enabled": current_no > 1,
            "href": f"/law?version={selected}&article={current_no - 1}",
            "label": "上一条",
        },
        "next": {
            "enabled": current_no < len(articles),
            "href": f"/law?version={selected}&article={current_no + 1}",
            "label": "下一条",
        },
        "compare_href": f"/compare?left={selected}&right=cn_company_law_2023&article={current_no}",
        "sidebar": sidebar,
    }


def instrument_reader_view(slug: str, unit: int | None) -> dict[str, object]:
    instrument = psql_json(QUERIES["instrument_detail"], {"instrument": slug}) or {}
    if not instrument:
        return {"ok": False, "error": "instrument not found", "slug": slug}
    units = psql_json(QUERIES["instrument_units"], {"instrument": slug}) or []
    current = None
    if unit:
        current = psql_json(QUERIES["instrument_unit_detail"], {"instrument": slug, "unit": str(unit)})
    if not current and units:
        current = units[0]
    if not current:
        return {"ok": False, "error": "no units found for instrument", "slug": slug}

    current_no = int(current.get("unit_number_int") or 1)
    ref = str(current.get("canonical_ref") or "")
    has_prev = any(int(u.get("unit_number_int") or 0) == current_no - 1 for u in units)
    has_next = any(int(u.get("unit_number_int") or 0) == current_no + 1 for u in units)

    def href_fn(item: dict[str, object]) -> str:
        return f"/instrument-reader?slug={slug}&unit={item.get('unit_number_int')}"

    sidebar = _reader_sidebar(ref, [])
    sidebar["meta"] = {"label": instrument.get("short_title"), "ref": ref}

    return {
        "ok": True,
        "mode": "instrument",
        "title": f"{instrument.get('short_title')}条文阅读",
        "instrument_slug": slug,
        "instrument_title": instrument.get("short_title"),
        "units": units,
        "selected_version": None,
        "article": current,
        "nav_groups": _paginate_nav(units, current_no, href_fn),
        "prev": {"enabled": has_prev, "href": f"/instrument-reader?slug={slug}&unit={current_no - 1}", "label": "上一条"},
        "next": {"enabled": has_next, "href": f"/instrument-reader?slug={slug}&unit={current_no + 1}", "label": "下一条"},
        "compare_href": None,
        "sidebar": sidebar,
    }


def compare_view(left_version: str, right_version: str, article: int) -> dict[str, object]:
    versions = psql_json(QUERIES["versions"]) or []
    left = left_version or "cn_company_law_2018"
    right = right_version or "cn_company_law_2023"
    article_no = article or 47
    rows = psql_json(
        QUERIES["compare"],
        {"left_version": left, "right_version": right, "article": str(article_no)},
    ) or []
    row_by_slug = {row["version_slug"]: row for row in rows}
    return {
        "ok": True,
        "versions": [{"slug": v["slug"], "version_label": v["version_label"]} for v in versions],
        "left": {"slug": left, "article": row_by_slug.get(left)},
        "right": {"slug": right, "article": row_by_slug.get(right)},
        "article_no": article_no,
    }


def _search_actions(result: dict[str, object]) -> list[dict[str, str]]:
    article = result.get("unit_number_int") or result.get("order_index") or 1
    if result.get("instrument_slug") == "cn_company_law":
        version = result.get("version_slug") or version_slug_from_ref(result.get("canonical_ref"))
        return [
            {"label": "打开原文", "href": f"/law?version={version}&article={article}"},
            {"label": "与2023对比", "href": f"/compare?left={version}&right=cn_company_law_2023&article={article}"},
        ]
    return [
        {"label": "查看规范", "href": f"/instrument?slug={result.get('instrument_slug')}"},
        {"label": "读条文", "href": f"/instrument-reader?slug={result.get('instrument_slug')}&unit={article}"},
    ]


def search_view(query: str) -> dict[str, object]:
    results = psql_json(QUERIES["search"], {"query": query}) if query else []
    return {
        "query": query,
        "results": [{**r, "actions": _search_actions(r)} for r in (results or [])],
    }


def home_view() -> dict[str, object]:
    stats = psql_json(QUERIES["stats"]) or {}
    domains = psql_json(QUERIES["domains"]) or []
    topics = psql_json(QUERIES["topics"]) or []
    instruments = psql_json(QUERIES["instruments"]) or []
    company_relations = psql_json(QUERIES["company_relations"]) or []
    versions = psql_json(QUERIES["versions"]) or []
    contexts = psql_json(QUERIES["contexts"]) or []
    sources = psql_json(QUERIES["sources"]) or []
    return {
        "stats": stats,
        "domains": domains,
        "topics": topics,
        "instruments": instruments,
        "company_relations": [
            {**r, "relation_type_label": relation_label(r.get("relation_type")), "href": relation_href(r)}
            for r in company_relations
        ],
        "versions": versions,
        "contexts": contexts,
        "sources": sources,
        "pillars": PILLARS,
    }


def instrument_view(slug: str) -> dict[str, object]:
    instrument = psql_json(QUERIES["instrument_detail"], {"instrument": slug}) or {}
    if not instrument:
        return {"ok": False, "error": "instrument not found", "slug": slug}
    versions = psql_json(QUERIES["instrument_versions"], {"instrument": slug}) or []
    units = psql_json(QUERIES["instrument_units"], {"instrument": slug}) or []
    relations = psql_json(QUERIES["instrument_relations"], {"instrument": slug}) or []
    topics = psql_json(QUERIES["instrument_topics"], {"instrument": slug}) or []
    return {
        "ok": True,
        "instrument": instrument,
        "versions": versions,
        "relations": [
            {**r, "relation_type_label": relation_label(r.get("relation_type")), "href": relation_href(r)}
            for r in relations
        ],
        "topics": topics,
        "units": [
            {**u, "actions": _search_actions({**u, "instrument_slug": slug})} for u in units[:18]
        ],
    }


def domain_view(slug: str) -> dict[str, object]:
    domain = psql_json(QUERIES["domain_detail"], {"domain": slug}) or {}
    if not domain:
        return {"ok": False, "error": "domain not found", "slug": slug}
    instruments = psql_json(QUERIES["domain_instruments"], {"domain": slug}) or []
    return {"ok": True, "domain": domain, "instruments": instruments}


def _topic_link_card(link: dict[str, object]) -> dict[str, object]:
    if link.get("target_type") == "context_event":
        description = link.get("target_title")
    elif link.get("target_type") == "legal_unit":
        description = link.get("text")
    else:
        description = link.get("notes") or ""
    meta = [str(value) for value in (link.get("role"), link.get("version_label"), link.get("event_type")) if value]
    return {
        "title": link.get("target_title"),
        "href": topic_target_href(link),
        "description": description,
        "meta": " · ".join(meta),
    }


def topic_view(slug: str) -> dict[str, object]:
    topic = psql_json(QUERIES["topic_detail"], {"topic": slug}) or {}
    if not topic:
        return {"ok": False, "error": "topic not found", "slug": slug}
    links = psql_json(QUERIES["topic_links"], {"topic": slug}) or []
    explanations = psql_json(QUERIES["topic_explanations"], {"topic": slug}) or []
    return {
        "ok": True,
        "topic": topic,
        "core": [_topic_link_card(link) for link in links if link.get("role") == "core"],
        "support": [_topic_link_card(link) for link in links if link.get("role") in {"support", "exception"}],
        "background": [_topic_link_card(link) for link in links if link.get("role") == "background"],
        "explanations": explanations,
    }
