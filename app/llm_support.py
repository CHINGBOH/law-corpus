from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request

from db_access import clip, psql_json, sql_quote
from query_defs import LEGAL_TERMS, QUERIES, TERM_EXPANSIONS


DEEPSEEK_API_URL = os.environ.get(
    "DEEPSEEK_API_URL", "https://api.deepseek.com/chat/completions"
)
DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-v4-flash")
TOPIC_KEYWORDS = {
    "资本信用": "capital-credit",
    "注册资本": "capital-credit",
    "认缴": "capital-credit",
    "缴足": "capital-credit",
    "法人独立": "corporate-personality",
    "人格否认": "corporate-personality",
    "法定代表人": "corporate-personality",
    "登记": "registration-publicity",
    "公示": "registration-publicity",
    "注销": "registration-publicity",
    "债权人": "creditor-protection",
    "减资": "creditor-protection",
    "合并": "creditor-protection",
    "董事": "governance-controls",
    "监事": "governance-controls",
    "高级管理人员": "governance-controls",
    "忠实": "governance-controls",
    "勤勉": "governance-controls",
    "证券": "capital-market-shares",
    "股份": "capital-market-shares",
    "公司债券": "capital-market-shares",
    "信息披露": "capital-market-shares",
}


def search_relevant_units(question: str) -> list[dict[str, object]]:
    terms = [term for term in LEGAL_TERMS if term in question]
    expanded = []
    for term in terms:
        expanded.extend(TERM_EXPANSIONS.get(term, []))
    terms.extend(expanded)
    terms = list(dict.fromkeys(terms))
    if not terms:
        terms = [question.strip()]
    predicates = " OR ".join(
        f"(coalesce(lu.title, '') || ' ' || coalesce(lu.text, '')) ILIKE {sql_quote('%' + term + '%')}"
        for term in terms[:8]
    )
    sql = f"""
        SELECT jsonb_agg(to_jsonb(t) ORDER BY version_sequence DESC, order_index)
        FROM (
          SELECT li.short_title AS instrument_title, lv.version_label, lv.version_sequence,
                 lu.canonical_ref, lu.unit_type, lu.unit_number, lu.title, lu.text, lu.order_index
          FROM legal_units lu
          JOIN legal_versions lv ON lv.id = lu.version_id
          JOIN legal_instruments li ON li.id = lv.instrument_id
          WHERE {predicates}
          ORDER BY lv.version_sequence DESC, lu.order_index
          LIMIT 18
        ) t;
    """
    return psql_json(sql) or []


def search_relevant_topics(question: str) -> list[dict[str, object]]:
    slugs = []
    for term, slug in TOPIC_KEYWORDS.items():
        if term in question and slug not in slugs:
            slugs.append(slug)
    if not slugs:
        return []
    quoted = ", ".join(sql_quote(slug) for slug in slugs[:3])
    sql = f"""
        SELECT jsonb_agg(to_jsonb(t) ORDER BY sort_order)
        FROM (
          SELECT dt.slug, dt.title, dt.pillar_title, dt.question, dt.summary, dt.sort_order
          FROM doctrine_topics dt
          WHERE dt.slug IN ({quoted})
        ) t;
    """
    return psql_json(sql) or []


def ask_deepseek(question: str) -> dict[str, object]:
    log_event("ask.start", question=clip(question, 80), model=DEEPSEEK_MODEL)
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        log_event("ask.no_api_key")
        return {
            "ok": False,
            "error": "DEEPSEEK_API_KEY is not set",
            "answer": "未设置 DEEPSEEK_API_KEY。先在启动服务前导出环境变量，再使用问答。",
        }

    instruments = psql_json(QUERIES["instruments"]) or []
    versions = psql_json(QUERIES["versions"]) or []
    contexts = psql_json(QUERIES["contexts"]) or []
    relations = psql_json(QUERIES["company_relations"]) or []
    topics = search_relevant_topics(question)
    results = search_relevant_units(question)
    log_event(
        "ask.context",
        instruments=len(instruments),
        versions=len(versions),
        contexts=len(contexts),
        relations=len(relations),
        topics=len(topics),
        legal_units=len(results or []),
    )
    context = build_llm_context(instruments, versions, contexts, relations, topics, results or [])
    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "你是一个中国大陆公司法制度演化研究助手。回答必须基于给定资料，"
                    "区分法律条文、政策背景、比较法待证命题和你的推理。"
                    "涉及未验证的新加坡影响时必须标注为待证，不得写成确定事实。"
                    "用中文回答，尽量给出条文引用 canonical_ref 或来源名称。"
                    "输出为简洁 Markdown：先给 2-3 句结论，再用二级标题和列表展开；"
                    "不要使用表格，避免长段落。"
                ),
            },
            {
                "role": "user",
                "content": f"问题：{question}\n\n资料：\n{context}",
            },
        ],
        "temperature": 0.2,
        "max_tokens": 1200,
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
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        log_event("ask.deepseek_http_error", status=exc.code)
        return {"ok": False, "error": f"DeepSeek HTTP {exc.code}: {body}", "answer": ""}
    except Exception as exc:
        log_event("ask.deepseek_error", error=clip(str(exc), 160))
        return {"ok": False, "error": str(exc), "answer": ""}

    answer = data.get("choices", [{}])[0].get("message", {}).get("content", "")
    log_event(
        "ask.deepseek_ok",
        response_id=data.get("id"),
        answer_chars=len(answer),
        context_units=len(results or []),
    )
    return {
        "ok": True,
        "model": DEEPSEEK_MODEL,
        "answer": answer,
        "answer_html": markdown_to_html(answer),
        "context_units": len(results or []),
        "raw_id": data.get("id"),
    }


def build_llm_context(
    instruments: list[dict[str, object]],
    versions: list[dict[str, object]],
    contexts: list[dict[str, object]],
    relations: list[dict[str, object]],
    topics: list[dict[str, object]],
    results: list[dict[str, object]],
) -> str:
    instrument_lines = [
        f"- {i['short_title']} / {i['instrument_type']} / 法域={i.get('domains')} / 当前版本={i.get('current_version_label')}"
        for i in instruments[:12]
    ]
    version_lines = [
        f"- {v['version_label']} ({v['action_type']}): adopted={v.get('adopted_date')}, "
        f"effective={v.get('effective_date')}, articles={v.get('article_count')}, status={v.get('status')}"
        for v in versions
    ]
    context_lines = [
        f"- {c['version_label']} / {c['title']} / {c['relation_type']} / "
        f"evidence={c['evidence_level']} / confidence={c['confidence']}: {c.get('claim_text')}"
        for c in contexts
    ]
    relation_lines = [
        f"- {r['relation_type']} / {r.get('object_title')} / evidence={r['evidence_level']} / confidence={r['confidence']}: {r.get('claim_text')}"
        for r in relations[:12]
    ]
    topic_lines = [
        f"- {t['title']} / 承力柱={t['pillar_title']} / 问题={t.get('question')}: {t.get('summary')}"
        for t in topics[:6]
    ]
    result_lines = [
        f"- {r.get('instrument_title')} / {r['version_label']} / {r['canonical_ref']} {r.get('unit_number')}: {clip(r.get('text'), 420)}"
        for r in results[:12]
    ]
    return "\n".join(
        [
            "【法体系底座】",
            *instrument_lines,
            "",
            "【公司法版本时间线】",
            *version_lines,
            "",
            "【公司法对外关系】",
            *relation_lines,
            "",
            "【命中的专题】",
            *(topic_lines or ["- 当前没有直接命中专题，按法体系与条文命中回答。"]),
            "",
            "【政策/历史/比较法证据】",
            *context_lines,
            "",
            "【检索命中的条文】",
            *(result_lines or ["- 无直接全文命中；请按法体系关系与版本演化作框架性回答，并说明资料缺口。"]),
        ]
    )


def log_event(event: str, **fields: object) -> None:
    details = " ".join(f"{key}={json.dumps(value, ensure_ascii=False)}" for key, value in fields.items())
    print(f"[legal-corpus] {event} {details}".rstrip(), flush=True)


def markdown_to_html(markdown: str) -> str:
    blocks = []
    list_items = []

    def flush_list() -> None:
        nonlocal list_items
        if list_items:
            blocks.append("<ul>" + "".join(f"<li>{item}</li>" for item in list_items) + "</ul>")
            list_items = []

    for raw_line in markdown.splitlines():
        line = raw_line.strip()
        if not line:
            flush_list()
            continue
        if line.startswith("### "):
            flush_list()
            blocks.append(f"<h4>{inline_md(line[4:])}</h4>")
        elif line.startswith("## "):
            flush_list()
            blocks.append(f"<h3>{inline_md(line[3:])}</h3>")
        elif line.startswith("# "):
            flush_list()
            blocks.append(f"<h2>{inline_md(line[2:])}</h2>")
        elif line.startswith(("- ", "* ")):
            list_items.append(inline_md(line[2:]))
        elif re.match(r"^\d+\.\s+(.*)$", line):
            list_items.append(inline_md(re.match(r"^\d+\.\s+(.*)$", line).group(1)))
        elif line.startswith("> "):
            flush_list()
            blocks.append(f"<blockquote>{inline_md(line[2:])}</blockquote>")
        else:
            flush_list()
            blocks.append(f"<p>{inline_md(line)}</p>")
    flush_list()
    return "\n".join(blocks)


def inline_md(text: str) -> str:
    from ui import esc

    value = esc(text)
    value = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", value)
    value = re.sub(r"`([^`]+)`", r"<code>\1</code>", value)
    value = re.sub(r"([a-z_]+:\d{4}:article_\d+)", r"<code class=\"ref\">\1</code>", value)
    return value
