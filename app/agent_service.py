from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from db_access import psql_exec, psql_json
from llm_support import DEEPSEEK_API_URL, DEEPSEEK_MODEL, clip, log_event, search_relevant_units


ALLOWED_RELATIONS = {
    "based_on",
    "specifies",
    "supplements",
    "limits",
    "constrained_by",
    "same_domain",
    "related_to",
    "interacts_with",
    "policy_background",
    "interpreted_by",
}


def load_subject(ref: str) -> dict[str, object]:
    sql = """
        SELECT to_jsonb(t)
        FROM (
          SELECT
            'legal_unit'::text AS subject_type,
            lu.id AS subject_id,
            lu.canonical_ref AS ref,
            lu.unit_number AS title,
            lu.text AS body,
            li.slug AS instrument_slug,
            li.short_title AS instrument_title,
            lv.slug AS version_slug,
            lv.version_label,
            s.id AS source_id,
            s.slug AS source_slug,
            s.title AS source_title
          FROM legal_units lu
          JOIN legal_versions lv ON lv.id = lu.version_id
          JOIN legal_instruments li ON li.id = lv.instrument_id
          LEFT JOIN sources s ON s.id = lv.official_source_id
          WHERE lu.canonical_ref = %(ref)s
          LIMIT 1
        ) t;
    """
    return psql_json(sql, {"ref": ref}) or {}


def load_context_events() -> list[dict[str, object]]:
    sql = """
        SELECT jsonb_agg(to_jsonb(t) ORDER BY start_date NULLS LAST, slug)
        FROM (
          SELECT slug, title, event_type, start_date, description
          FROM context_events
          LIMIT 12
        ) t;
    """
    return psql_json(sql) or []


def lookup_target(target_type: str, target_ref: str) -> dict[str, object]:
    if target_type == "legal_unit":
        sql = """
            SELECT jsonb_build_object(
              'target_id', lu.id,
              'target_title', lu.canonical_ref
            )
            FROM legal_units lu
            WHERE lu.canonical_ref = %(target_ref)s
            LIMIT 1;
        """
        return psql_json(sql, {"target_ref": target_ref}) or {}
    if target_type == "context_event":
        sql = """
            SELECT jsonb_build_object(
              'target_id', ce.id,
              'target_title', ce.title
            )
            FROM context_events ce
            WHERE ce.slug = %(target_ref)s
            LIMIT 1;
        """
        return psql_json(sql, {"target_ref": target_ref}) or {}
    if target_type == "legal_instrument":
        sql = """
            SELECT jsonb_build_object(
              'target_id', li.id,
              'target_title', li.short_title
            )
            FROM legal_instruments li
            WHERE li.slug = %(target_ref)s
            LIMIT 1;
        """
        return psql_json(sql, {"target_ref": target_ref}) or {}
    return {}


def insert_candidate(
    subject: dict[str, object],
    target_type: str,
    target_ref: str,
    relation_type: str,
    claim_text: str,
    confidence: float,
    source_slug: str,
    excerpt_text: str,
    proposer: str = "llm",
) -> dict[str, object]:
    target = lookup_target(target_type, target_ref)
    if not target or relation_type not in ALLOWED_RELATIONS:
        return {}
    sql = """
        WITH src AS (
          SELECT id, slug FROM sources WHERE slug = %(source_slug)s LIMIT 1
        ),
        inserted AS (
          INSERT INTO relation_candidates (
            subject_type, subject_id, object_type, object_id, relation_type,
            claim_text, proposed_source_id, excerpt_text, confidence, proposer, status
          )
          SELECT
            %(subject_type)s,
            %(subject_id)s::uuid,
            %(target_type)s,
            %(target_id)s::uuid,
            %(relation_type)s,
            %(claim_text)s,
            (SELECT id FROM src),
            %(excerpt_text)s,
            %(confidence)s::numeric(3,2),
            %(proposer)s,
            'pending'
          WHERE EXISTS (SELECT 1 FROM src)
          RETURNING id::text
        )
        SELECT jsonb_build_object('candidate_id', id) FROM inserted;
    """
    return psql_json(
        sql,
        {
            "subject_type": subject["subject_type"],
            "subject_id": subject["subject_id"],
            "target_type": target_type,
            "target_id": target["target_id"],
            "relation_type": relation_type,
            "claim_text": claim_text,
            "source_slug": source_slug,
            "excerpt_text": excerpt_text,
            "confidence": f"{confidence:.2f}",
            "proposer": proposer,
        },
    ) or {}


def fallback_proposals(subject: dict[str, object]) -> list[dict[str, object]]:
    ref = str(subject.get("ref") or "")
    body = str(subject.get("body") or "")
    proposals: list[dict[str, object]] = []
    if "认缴" in body or "注册资本" in body:
        proposals.append(
            {
                "target_type": "context_event",
                "target_ref": "cn_registration_capital_reform_2013",
                "relation_type": "policy_background",
                "claim_text": "注册资本登记制度改革是该条资本规则的重要制度背景。",
                "confidence": 0.78,
                "source_slug": "src_company_law_2023_csrc_hubei_materials",
                "excerpt_text": "2013年注册资本登记制度改革是公司法由实缴走向认缴的重要政策背景。",
            }
        )
        proposals.append(
            {
                "target_type": "legal_unit",
                "target_ref": "registration_regulation:2021:article_8",
                "relation_type": "interacts_with",
                "claim_text": "该条的注册资本规则需要通过登记事项对外公示，和登记管理条例形成联动。",
                "confidence": 0.74,
                "source_slug": "src_registration_regulation_2021_gov",
                "excerpt_text": "市场主体的一般登记事项包括名称、主体类型、经营范围、住所、注册资本或者出资额、法定代表人等。",
            }
        )
    if "法定代表人" in body:
        proposals.append(
            {
                "target_type": "legal_unit",
                "target_ref": "civil_code:2020:article_61",
                "relation_type": "supplements",
                "claim_text": "法定代表人规则在民法典的一般法人规则中得到补充。",
                "confidence": 0.71,
                "source_slug": "src_civil_code_2020_moj",
                "excerpt_text": "依照法律或者法人章程的规定，代表法人从事民事活动的负责人，为法人的法定代表人。",
            }
        )
    if "债务" in body or "债权人" in body:
        proposals.append(
            {
                "target_type": "legal_unit",
                "target_ref": "civil_code:2020:article_60",
                "relation_type": "supplements",
                "claim_text": "债务承担仍受民法典法人责任的一般规则约束。",
                "confidence": 0.69,
                "source_slug": "src_civil_code_2020_moj",
                "excerpt_text": "法人以其全部财产独立承担民事责任。",
            }
        )
    if not proposals:
        matches = search_relevant_units(body) or []
        for match in matches[:2]:
            target_ref = str(match.get("canonical_ref") or "")
            if target_ref and target_ref != ref and not target_ref.startswith("company_law:"):
                proposals.append(
                    {
                        "target_type": "legal_unit",
                        "target_ref": target_ref,
                        "relation_type": "related_to",
                        "claim_text": "该条与命中的相关规范存在待审核的制度联系。",
                        "confidence": 0.55,
                        "source_slug": str(subject.get("source_slug") or ""),
                        "excerpt_text": clip(match.get("text"), 100),
                    }
                )
    return proposals[:4]


def llm_proposals(subject: dict[str, object]) -> list[dict[str, object]]:
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        return []
    contexts = load_context_events()
    related_units = search_relevant_units(str(subject.get("body") or "")) or []
    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "你是法律关系抽取助手。只输出 JSON 数组。每个元素包含 "
                    "target_type,target_ref,relation_type,claim_text,confidence,source_slug,excerpt_text。"
                    "只允许 target_type 为 legal_unit、legal_instrument、context_event。"
                    "relation_type 必须是 based_on,specifies,supplements,limits,constrained_by,"
                    "same_domain,related_to,interacts_with,policy_background,interpreted_by 之一。"
                ),
            },
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "subject": subject,
                        "context_events": contexts[:8],
                        "related_units": related_units[:8],
                    },
                    ensure_ascii=False,
                ),
            },
        ],
        "temperature": 0.1,
        "max_tokens": 800,
        "response_format": {"type": "json_object"},
    }
    req = urllib.request.Request(
        DEEPSEEK_API_URL,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            data = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        log_event("extract.deepseek_error", error=clip(str(exc), 120))
        return []
    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        return []
    proposals = parsed.get("items") if isinstance(parsed, dict) else parsed
    return proposals if isinstance(proposals, list) else []


def extract_relation_candidates(canonical_ref: str) -> dict[str, object]:
    subject = load_subject(canonical_ref)
    if not subject:
        return {"ok": False, "error": "subject not found", "created": []}
    proposals = llm_proposals(subject) or fallback_proposals(subject)
    created = []
    for item in proposals:
        result = insert_candidate(
            subject,
            str(item.get("target_type") or ""),
            str(item.get("target_ref") or ""),
            str(item.get("relation_type") or ""),
            str(item.get("claim_text") or ""),
            float(item.get("confidence") or 0.5),
            str(item.get("source_slug") or subject.get("source_slug") or ""),
            str(item.get("excerpt_text") or ""),
        )
        if result:
            created.append(result)
    return {"ok": True, "subject": subject, "created": created, "proposals": len(proposals)}
