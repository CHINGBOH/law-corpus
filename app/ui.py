from __future__ import annotations

import html

from db_access import parse_int, psql_json
from graph_service import get_neighbors, get_node, get_path
from query_defs import PILLARS, QUERIES
from review_service import get_candidate, list_candidates


def esc(value: object) -> str:
    if value is None:
        return ""
    return html.escape(str(value), quote=True)


def badge(value: object) -> str:
    return f'<span class="badge">{esc(value)}</span>'


def stat_box(label: str, value: object) -> str:
    return f'<article><strong>{esc(value)}</strong><span>{esc(label)}</span></article>'


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


def clip_text(value: object, limit: int = 120) -> str:
    text = "" if value is None else " ".join(str(value).split())
    return text if len(text) <= limit else text[:limit].rstrip() + "..."


def node_type_label(value: object) -> str:
    return NODE_TYPE_LABELS.get(str(value), str(value))


def relation_label(value: object) -> str:
    return RELATION_LABELS.get(str(value), str(value))


def graph_preset_links() -> str:
    presets = [
        ("资本信用", "legal_unit:company_law:2023:article_47"),
        ("出资加速到期", "legal_unit:company_law:2023:article_54"),
        ("法人独立责任", "legal_unit:civil_code:2020:article_60"),
        ("法定代表人", "legal_unit:civil_code:2020:article_61"),
        ("登记公示", "legal_unit:registration_regulation:2021:article_8"),
        ("2013 改革", "context_event:cn_registration_capital_reform_2013"),
    ]
    return "".join(
        f'<a href="/graph?node_key={esc(node_key)}">{esc(label)}</a>'
        for label, node_key in presets
    )


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


def candidate_status_label(value: object) -> str:
    mapping = {
        "pending": "待审核",
        "needs_edit": "待改写",
        "accepted": "已转正",
        "rejected": "已驳回",
    }
    return mapping.get(str(value), str(value))


def article_no_from_ref(canonical_ref: object) -> int:
    text = "" if canonical_ref is None else str(canonical_ref)
    match = __import__("re").search(r"article_(\d+)$", text)
    return int(match.group(1)) if match else 1


def version_slug_from_ref(canonical_ref: object) -> str:
    text = "" if canonical_ref is None else str(canonical_ref)
    match = __import__("re").match(r"company_law:(\d{4}):", text)
    if not match:
        return "cn_company_law_2023"
    return f"cn_company_law_{match.group(1)}"


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


def render_relation_target_link(relation: dict[str, object]) -> str:
    return f'<a href="{esc(relation_href(relation))}">{esc(relation.get("object_title"))}</a>'


def render_search_action_links(result: dict[str, object]) -> str:
    if result.get("instrument_slug") == "cn_company_law":
        version = result.get("version_slug") or version_slug_from_ref(result.get("canonical_ref"))
        article = result.get("unit_number_int") or result.get("order_index") or 1
        return (
            f'<a href="/law?version={esc(version)}&article={esc(article)}">打开原文</a>'
            f'<a href="/compare?left={esc(version)}&right=cn_company_law_2023&article={esc(article)}">与2023对比</a>'
        )
    article = result.get("unit_number_int") or result.get("order_index") or 1
    return (
        f'<a href="/instrument?slug={esc(result.get("instrument_slug"))}">查看规范</a>'
        f'<a href="/instrument-reader?slug={esc(result.get("instrument_slug"))}&unit={esc(article)}">读条文</a>'
    )


def render_instrument_unit_actions(unit: dict[str, object]) -> str:
    if unit.get("instrument_slug") == "cn_company_law":
        article = unit.get("unit_number_int") or unit.get("order_index") or 1
        return (
            f'<a href="/law?version={esc(unit.get("version_slug"))}&article={esc(article)}">打开原文</a>'
            f'<a href="/compare?left={esc(unit.get("version_slug"))}&right=cn_company_law_2023&article={esc(article)}">与2023对比</a>'
        )
    article = unit.get("unit_number_int") or unit.get("order_index") or 1
    return f'<a href="/instrument-reader?slug={esc(unit.get("instrument_slug"))}&unit={esc(article)}">读条文</a>'


def infer_instrument_slug_from_ref(canonical_ref: object) -> str:
    text = "" if canonical_ref is None else str(canonical_ref)
    prefix_map = {
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
    for prefix, slug in prefix_map.items():
        if text.startswith(prefix):
            return slug
    return ""


def render_page() -> str:
    stats = psql_json(QUERIES["stats"]) or {}
    domains = psql_json(QUERIES["domains"]) or []
    topics = psql_json(QUERIES["topics"]) or []
    instruments = psql_json(QUERIES["instruments"]) or []
    company_relations = psql_json(QUERIES["company_relations"]) or []
    versions = psql_json(QUERIES["versions"]) or []
    contexts = psql_json(QUERIES["contexts"]) or []
    sources = psql_json(QUERIES["sources"]) or []

    version_rows = "\n".join(
        f"""
        <tr>
          <td>{v['version_sequence']}</td>
          <td><strong>{esc(v['version_label'])}</strong><span>{esc(v['slug'])}</span></td>
          <td>{esc(v['action_type'])}</td>
          <td>{esc(v.get('adopted_date'))}</td>
          <td>{esc(v.get('effective_date'))}</td>
          <td>{badge(v['status'])}</td>
          <td>{esc(v.get('article_count'))}</td>
        </tr>
        """
        for v in versions
    )
    context_cards = "\n".join(
        f"""
        <article class="context-card">
          <div class="context-head">
            <span>{esc(c['version_label'])}</span>
            {badge(c['evidence_level'])}
          </div>
          <h3>{esc(c['title'])}</h3>
          <p>{esc(c.get('claim_text'))}</p>
          <footer>
            <span>{esc(c['relation_type'])}</span>
            <span>confidence {esc(c['confidence'])}</span>
          </footer>
        </article>
        """
        for c in contexts
    )
    source_rows = "\n".join(
        f"""
        <tr>
          <td>{esc(s['reliability_tier'])}</td>
          <td>{esc(s['source_type'])}</td>
          <td><a href="{esc(s.get('url'))}" target="_blank" rel="noreferrer">{esc(s['title'])}</a></td>
          <td>{esc(s.get('publisher'))}</td>
        </tr>
        """
        for s in sources
    )
    domain_cards = "\n".join(
        f"""
        <article class="domain-card">
          <div class="context-head">
            <span>{esc(d['name'])}</span>
            {badge(d['instrument_count'])}
          </div>
          <p>{esc(d['description'])}</p>
          <footer><a href="/domain?slug={esc(d['slug'])}">查看法域</a></footer>
        </article>
        """
        for d in domains
    )
    topic_cards = "\n".join(
        f"""
        <article class="domain-card">
          <div class="context-head">
            <span>{esc(t['title'])}</span>
            {badge(t['pillar_title'])}
          </div>
          <strong>{esc(t.get('question'))}</strong>
          <p>{esc(t.get('summary'))}</p>
          <footer><a href="/topic?slug={esc(t['slug'])}">查看专题</a></footer>
        </article>
        """
        for t in topics
    )
    instrument_rows = "\n".join(
        f"""
        <tr>
          <td><a href="/instrument?slug={esc(i['slug'])}"><strong>{esc(i['short_title'])}</strong></a><span>{esc(i['canonical_title'])}</span></td>
          <td>{esc(i['instrument_type'])}</td>
          <td>{esc(i.get('domains'))}</td>
          <td>{esc(i.get('current_version_label'))}</td>
          <td>{esc(i.get('effective_date'))}</td>
        </tr>
        """
        for i in instruments
    )
    relation_cards = "\n".join(
        f"""
        <article class="context-card">
          <div class="context-head">
            <span>{esc(r['relation_type'])}</span>
            {badge(r['evidence_level'])}
          </div>
          <h3>{render_relation_target_link(r)}</h3>
          <p>{esc(r.get('claim_text'))}</p>
          <footer>
            <span>confidence {esc(r['confidence'])}</span>
            <span>{esc(r.get('source_title'))}</span>
          </footer>
        </article>
        """
        for r in company_relations
    )
    pillar_cards = "\n".join(
        f"""
        <article class="pillar-card">
          <h3>{esc(p['title'])}</h3>
          <strong>{esc(p['question'])}</strong>
          <p>{esc(p['scope'])}</p>
          <footer>{esc(p['signal'])}</footer>
        </article>
        """
        for p in PILLARS
    )
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>法律规范体系仓库</title>
  <style>{CSS}</style>
</head>
<body>
  <header class="topbar">
    <div>
      <h1>法律规范体系仓库</h1>
      <p>先看法体系，再钻公司法版本、条文和制度演化</p>
    </div>
    <form class="search" action="/search" method="get">
      <input name="q" placeholder="搜索法律、条文、制度、政策背景">
      <button type="submit">查询</button>
    </form>
  </header>
  <main>
    <section class="quick-actions">
      <a href="/graph?node_key=legal_instrument:cn_company_law"><strong>关系穿透台</strong><span>从公司法节点展开图谱</span></a>
      <a href="/review"><strong>候选审核台</strong><span>模型提议关系，人来转正</span></a>
      <a href="/instrument?slug=cn_company_law"><strong>公司法</strong><span>版本、关键条文、对外关系</span></a>
      <a href="/domain?slug=commercial-organization"><strong>商事组织法</strong><span>公司、合伙、个人独资</span></a>
      <a href="/law?version=cn_company_law_2023&article=47"><strong>读原文</strong><span>2023 第47条</span></a>
      <a href="#ask"><strong>AI解释</strong><span>基于法体系、条文和政策上下文</span></a>
    </section>
    <section class="stats">
      {stat_box('规范', stats.get('instruments'))}
      {stat_box('法域', stats.get('domains'))}
      {stat_box('专题', stats.get('topics'))}
      {stat_box('版本', stats.get('versions'))}
      {stat_box('法律关系', stats.get('legal_relations'))}
      {stat_box('候选关系', stats.get('relation_candidates'))}
      {stat_box('解释', stats.get('plain_explanations'))}
    </section>
    <section>
      <div class="section-head">
        <h2>法域底座</h2>
        <a href="/api/domains">/api/domains</a>
      </div>
      <div class="pillar-grid">{domain_cards}</div>
    </section>
    <section>
      <div class="section-head">
        <h2>专题脉络</h2>
        <a href="/api/topics">/api/topics</a>
      </div>
      <div class="pillar-grid">{topic_cards}</div>
    </section>
    <section>
      <div class="section-head">
        <h2>规范目录</h2>
        <a href="/api/instruments">/api/instruments</a>
      </div>
      <div class="table-wrap">
        <table>
          <thead><tr><th>规范</th><th>类型</th><th>法域</th><th>当前版本</th><th>施行</th></tr></thead>
          <tbody>{instrument_rows}</tbody>
        </table>
      </div>
    </section>
    <section>
      <div class="section-head">
        <h2>公司法对外关系</h2>
        <a href="/api/relations?instrument=cn_company_law">/api/relations</a>
      </div>
      <div class="context-grid">{relation_cards}</div>
    </section>
    <section id="ask">
      <div class="section-head">
        <h2>问公司法</h2>
        <a href="/api/ask">POST /api/ask</a>
      </div>
      <div class="ask-panel">
        <textarea id="askQuestion" placeholder="例如：为什么 2023 公司法要把认缴出资改成五年缴足？这和 2013 改革有什么张力？"></textarea>
        <div class="ask-actions">
          <button type="button" onclick="askDeepSeek()">问 DeepSeek</button>
          <span id="askStatus"></span>
        </div>
        <div id="askAnswer" class="answer-card"></div>
      </div>
    </section>
    <section>
      <div class="section-head">
        <h2>公司法承力柱</h2>
        <a href="/api/versions">/api/versions</a>
      </div>
      <div class="pillar-grid">{pillar_cards}</div>
    </section>
    <section>
      <div class="section-head">
        <h2>公司法版本时间线</h2>
        <a href="/api/versions">/api/versions</a>
      </div>
      <div class="table-wrap">
        <table>
          <thead>
            <tr><th>#</th><th>版本</th><th>动作</th><th>通过</th><th>施行</th><th>状态</th><th>条数</th></tr>
          </thead>
          <tbody>{version_rows}</tbody>
        </table>
      </div>
    </section>
    <section>
      <div class="section-head">
        <h2>政策环境与比较法证据</h2>
        <a href="/api/contexts">/api/contexts</a>
      </div>
      <div class="context-grid">{context_cards}</div>
    </section>
    <section>
      <div class="section-head">
        <h2>来源</h2>
        <a href="/api/sources">/api/sources</a>
      </div>
      <div class="table-wrap">
        <table>
          <thead><tr><th>等级</th><th>类型</th><th>标题</th><th>发布方</th></tr></thead>
          <tbody>{source_rows}</tbody>
        </table>
      </div>
    </section>
  </main>
  <script>
    async function askDeepSeek() {{
      const question = document.getElementById('askQuestion').value.trim();
      const status = document.getElementById('askStatus');
      const answer = document.getElementById('askAnswer');
      if (!question) {{
        status.textContent = '请输入问题';
        return;
      }}
      status.textContent = '查询资料并调用 DeepSeek...';
      answer.innerHTML = '';
      try {{
        const res = await fetch('/api/ask', {{
          method: 'POST',
          headers: {{'Content-Type': 'application/json'}},
          body: JSON.stringify({{question}})
        }});
        const data = await res.json();
        status.textContent = data.ok ? `模型：${{data.model}}，上下文条文：${{data.context_units}}` : data.error;
        answer.innerHTML = data.answer_html || '';
        if (!data.answer_html && data.answer) {{
          answer.textContent = data.answer;
        }}
      }} catch (err) {{
        status.textContent = String(err);
      }}
    }}
  </script>
</body>
</html>"""


def render_search(query: str) -> str:
    results = psql_json(QUERIES["search"], {"query": query}) if query else []
    rows = "\n".join(
        f"""
        <article class="result">
          <div>{esc(r['instrument_title'])} · {esc(r['version_label'])} · {esc(r['canonical_ref'])}</div>
          <h2>{esc(r.get('unit_number'))} {esc(r.get('title'))}</h2>
          <p>{esc(r.get('text'))}</p>
          <footer class="result-actions">{render_search_action_links(r)}</footer>
        </article>
        """
        for r in (results or [])
    )
    return f"""<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>查询 · 法律规范体系仓库</title><style>{CSS}</style></head>
<body>
  <header class="topbar">
    <div><h1>查询</h1><p><a href="/">返回首页</a></p></div>
    <form class="search" action="/search" method="get">
      <input name="q" value="{esc(query)}" placeholder="搜索法律、条文">
      <button type="submit">查询</button>
    </form>
  </header>
  <main><section>{rows or '<p class="empty">当前还没有匹配结果。</p>'}</section></main>
</body></html>"""


def render_law_reader(version: str, article: int | None) -> str:
    versions = psql_json(QUERIES["versions"]) or []
    selected = version or "cn_company_law_2023"
    articles = psql_json(QUERIES["articles"], {"version": selected}) or []
    current = None
    if article:
        current = psql_json(QUERIES["article"], {"version": selected, "article": str(article)})
    if not current and articles:
        current = articles[0]

    version_options = "\n".join(
        f'<option value="{esc(v["slug"])}" {"selected" if v["slug"] == selected else ""}>{esc(v["version_label"])}</option>'
        for v in versions
    )
    article_options = "\n".join(
        f'<option value="{esc(a["unit_number_int"])}" {"selected" if current and a["unit_number_int"] == current["unit_number_int"] else ""}>{esc(a["unit_number"])} · {esc(a["canonical_ref"])}</option>'
        for a in articles
    )
    current_no = int(current["unit_number_int"]) if current and current.get("unit_number_int") else 1
    selected_version_label = next((v["version_label"] for v in versions if v["slug"] == selected), selected)
    article_list = render_article_nav(selected, articles, current_no)
    body = render_article_body(current)
    previous_link = nav_link(selected, current_no - 1, "上一条", current_no > 1)
    next_link = nav_link(selected, current_no + 1, "下一条", current_no < len(articles))
    context_panel = render_reader_context(selected, selected_version_label, current_no, current)
    return f"""<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>原文阅读 · 公司法制度演化仓库</title><style>{CSS}</style></head>
<body>
  <header class="topbar">
    <div><h1>原文阅读</h1><p><a href="/">返回首页</a> · <a href="/compare">版本对比</a></p></div>
    <form class="reader-controls" action="/law" method="get">
      <select name="version" onchange="this.form.submit()">{version_options}</select>
      <select name="article" onchange="this.form.submit()">{article_options}</select>
      <button type="submit">打开</button>
    </form>
  </header>
  <main class="reader-layout">
    <aside class="article-nav">
      <div class="nav-title">条文导航</div>
      {article_list}
    </aside>
    <section class="article-pane">
      <div class="reader-strip">
        {previous_link}
        <a href="/compare?left={esc(selected)}&right=cn_company_law_2023&article={esc(current_no)}">与2023对比</a>
        {next_link}
      </div>
      {body}
    </section>
    <aside class="reader-context">{context_panel}</aside>
  </main>
</body></html>"""


def render_article_nav(version: str, articles: list[dict[str, object]], current_no: int) -> str:
    groups = []
    for start in range(1, len(articles) + 1, 20):
        end = min(start + 19, len(articles))
        items = [
            a for a in articles
            if start <= int(a.get("unit_number_int") or 0) <= end
        ]
        links = "".join(
            f'<a class="article-link {"active" if int(a["unit_number_int"]) == current_no else ""}" href="/law?version={esc(version)}&article={esc(a["unit_number_int"])}">{esc(a["unit_number"])}</a>'
            for a in items
        )
        open_attr = " open" if start <= current_no <= end else ""
        groups.append(f"<details{open_attr}><summary>第{start}-{end}条</summary><div>{links}</div></details>")
    return "\n".join(groups)


def render_reader_context(
    version: str,
    version_label: object,
    article_no: int,
    current: dict[str, object] | None,
) -> str:
    ref = current.get("canonical_ref") if current else ""
    relations = psql_json(QUERIES["article_relations"], {"canonical_ref": str(ref)}) if ref else []
    topics = psql_json(QUERIES["unit_topics"], {"canonical_ref": str(ref)}) if ref else []
    relation_links = "".join(
        f'<a href="{esc(relation_href(r))}">{esc(r["relation_type"])} · {esc(r["object_title"])}</a>'
        for r in (relations or [])[:6]
    ) or "<p>当前条文尚未补录跨法关系。</p>"
    topic_links = "".join(
        f'<a href="/topic?slug={esc(t["slug"])}">{esc(t["title"])} · {esc(t["pillar_title"])}</a>'
        for t in (topics or [])[:6]
    ) or "<p>当前条文尚未挂接专题。</p>"
    return f"""
    <section>
      <h3>当前条文</h3>
      <p><strong>{esc(version_label)}</strong></p>
      <p><code>{esc(ref)}</code></p>
    </section>
    <section>
      <h3>常用动作</h3>
      <a href="/compare?left={esc(version)}&right=cn_company_law_2023&article={esc(article_no)}">与 2023 同条号对比</a>
      <a href="/compare?left=cn_company_law_2013&right=cn_company_law_2023&article={esc(article_no)}">与 2013 同条号对比</a>
      <a href="/search?q={esc(current.get('unit_number') if current else '')}">搜索本条号</a>
      <a href="/graph?node_key=legal_unit:{esc(ref)}">在图谱中打开</a>
    </section>
    <section>
      <h3>关联法条</h3>
      {relation_links}
    </section>
    <section>
      <h3>相关专题</h3>
      {topic_links}
    </section>
    <section>
      <h3>阅读提示</h3>
      <p>同条号对比只说明位置差异，不等于制度继承。涉及制度演化时，应优先看法体系关系。</p>
    </section>
    """


def nav_link(version: str, article: int, label: str, enabled: bool) -> str:
    if not enabled:
        return f'<span class="disabled-link">{esc(label)}</span>'
    return f'<a href="/law?version={esc(version)}&article={esc(article)}">{esc(label)}</a>'


def render_compare(left_version: str, right_version: str, article: int) -> str:
    versions = psql_json(QUERIES["versions"]) or []
    left = left_version or "cn_company_law_2018"
    right = right_version or "cn_company_law_2023"
    rows = psql_json(
        QUERIES["compare"],
        {"left_version": left, "right_version": right, "article": str(article or 47)},
    ) or []
    row_by_slug = {row["version_slug"]: row for row in rows}
    version_options_left = options_for_versions(versions, left)
    version_options_right = options_for_versions(versions, right)
    left_body = render_article_body(row_by_slug.get(left), compact=False)
    right_body = render_article_body(row_by_slug.get(right), compact=False)
    return f"""<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>版本对比 · 公司法制度演化仓库</title><style>{CSS}</style></head>
<body>
  <header class="topbar">
    <div><h1>版本对比</h1><p><a href="/">返回首页</a> · <a href="/law">原文阅读</a></p></div>
    <form class="reader-controls" action="/compare" method="get">
      <select name="left">{version_options_left}</select>
      <select name="right">{version_options_right}</select>
      <input name="article" value="{esc(article or 47)}" inputmode="numeric" aria-label="条号">
      <button type="submit">对比</button>
    </form>
  </header>
  <main>
    <section class="compare-grid">
      <article class="compare-pane">{left_body}</article>
      <article class="compare-pane">{right_body}</article>
    </section>
  </main>
</body></html>"""


def render_article_body(article: dict[str, object] | None, compact: bool = False) -> str:
    if not article:
        return '<p class="empty">没有找到该版本的对应条文。</p>'
    paragraphs = "".join(f"<p>{esc(part)}</p>" for part in str(article.get("text") or "").splitlines() if part.strip())
    return f"""
    <div class="article-meta">{esc(article.get('version_label'))} · <code>{esc(article.get('canonical_ref'))}</code></div>
    <h2>{esc(article.get('unit_number'))}</h2>
    <div class="article-text">{paragraphs}</div>
    """


def render_instrument(slug: str) -> str:
    instrument = psql_json(QUERIES["instrument_detail"], {"instrument": slug}) or {}
    versions = psql_json(QUERIES["instrument_versions"], {"instrument": slug}) or []
    units = psql_json(QUERIES["instrument_units"], {"instrument": slug}) or []
    relations = psql_json(QUERIES["instrument_relations"], {"instrument": slug}) or []
    topics = psql_json(QUERIES["instrument_topics"], {"instrument": slug}) or []
    if not instrument:
        return "<!doctype html><html lang='zh-CN'><body><p>未找到该规范。</p></body></html>"

    version_rows = "\n".join(
        f"<tr><td>{esc(v['version_sequence'])}</td><td>{esc(v['version_label'])}</td><td>{esc(v['action_type'])}</td><td>{esc(v.get('adopted_date'))}</td><td>{esc(v.get('effective_date'))}</td></tr>"
        for v in versions
    )
    unit_cards = "\n".join(
        f"""
        <article class="result">
          <div>{esc(u['version_label'])} · {esc(u['canonical_ref'])}</div>
          <h2>{esc(u['unit_number'])}</h2>
          <p>{esc(u['text'])}</p>
          <footer class="result-actions">{render_instrument_unit_actions(u)}</footer>
        </article>
        """
        for u in units[:18]
    ) or '<p class="empty">当前只录入了元数据，尚未补关键条文。</p>'
    relation_cards = "\n".join(
        f"""
        <article class="context-card">
          <div class="context-head">
            <span>{esc(r['relation_type'])}</span>
            {badge(r['evidence_level'])}
          </div>
          <h3>{render_relation_target_link(r)}</h3>
          <p>{esc(r.get('claim_text'))}</p>
          <footer><span>confidence {esc(r['confidence'])}</span><span>{esc(r.get('source_title'))}</span></footer>
        </article>
        """
        for r in relations
    ) or '<p class="empty">当前还没有关系数据。</p>'
    topic_cards = "\n".join(
        f"""
        <article class="domain-card">
          <div class="context-head">
            <span>{esc(t['title'])}</span>
            {badge(t['pillar_title'])}
          </div>
          <strong>{esc(t.get('question'))}</strong>
          <p>{esc(t.get('summary'))}</p>
          <footer><a href="/topic?slug={esc(t['slug'])}">查看专题</a></footer>
        </article>
        """
        for t in topics
    ) or '<p class="empty">当前规范还没有挂接专题。</p>'
    source_link = ""
    if instrument.get("source_url"):
        source_link = f'<a href="{esc(instrument["source_url"])}" target="_blank" rel="noreferrer">官方来源</a>'
    return f"""<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(instrument.get('short_title'))} · 法律规范体系仓库</title><style>{CSS}</style></head>
<body>
  <header class="topbar">
    <div><h1>{esc(instrument.get('short_title'))}</h1><p>{esc(instrument.get('canonical_title'))} · {esc(instrument.get('domains'))}</p></div>
    <div class="inline-actions"><a href="/">返回首页</a><a href="/graph?node_key=legal_instrument:{esc(slug)}">图谱打开</a>{source_link}</div>
  </header>
  <main>
    <section class="stats">
      {stat_box('当前版本', instrument.get('current_version_label'))}
      {stat_box('类型', instrument.get('instrument_type'))}
      {stat_box('施行', instrument.get('effective_date'))}
      {stat_box('初次制定', instrument.get('first_enacted_date'))}
      {stat_box('法域', instrument.get('domains'))}
    </section>
    <section>
      <div class="section-head"><h2>体系关系</h2><a href="/api/relations?instrument={esc(slug)}">/api/relations</a></div>
      <div class="context-grid">{relation_cards}</div>
    </section>
    <section>
      <div class="section-head"><h2>相关专题</h2><a href="/api/topic?slug=capital-credit">专题</a></div>
      <div class="pillar-grid">{topic_cards}</div>
    </section>
    <section>
      <div class="section-head"><h2>版本</h2><a href="/api/instrument?slug={esc(slug)}">/api/instrument</a></div>
      <div class="table-wrap"><table><thead><tr><th>#</th><th>版本</th><th>动作</th><th>通过</th><th>施行</th></tr></thead><tbody>{version_rows}</tbody></table></div>
    </section>
    <section>
      <div class="section-head"><h2>关键条文</h2><a href="/api/instrument-units?slug={esc(slug)}">/api/instrument-units</a></div>
      <div>{unit_cards}</div>
    </section>
  </main>
</body></html>"""


def render_domain(slug: str) -> str:
    domain = psql_json(QUERIES["domain_detail"], {"domain": slug}) or {}
    instruments = psql_json(QUERIES["domain_instruments"], {"domain": slug}) or []
    if not domain:
        return "<!doctype html><html lang='zh-CN'><body><p>未找到该法域。</p></body></html>"
    rows = "\n".join(
        f"""
        <tr>
          <td><a href="/instrument?slug={esc(i['slug'])}"><strong>{esc(i['short_title'])}</strong></a><span>{esc(i['canonical_title'])}</span></td>
          <td>{badge('主节点' if i.get('is_primary') else '关联节点')}</td>
          <td>{esc(i['instrument_type'])}</td>
          <td>{esc(i.get('current_version_label'))}</td>
        </tr>
        """
        for i in instruments
    )
    return f"""<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(domain.get('name'))} · 法律规范体系仓库</title><style>{CSS}</style></head>
<body>
  <header class="topbar">
    <div><h1>{esc(domain.get('name'))}</h1><p>{esc(domain.get('description'))}</p></div>
    <div class="inline-actions"><a href="/">返回首页</a></div>
  </header>
  <main>
    <section class="stats">
      {stat_box('规范数', domain.get('instrument_count'))}
      {stat_box('法域', domain.get('name'))}
      {stat_box('排序', domain.get('sort_order'))}
      {stat_box('主线', '先看体系，再钻条文')}
      {stat_box('入口', slug)}
    </section>
    <section>
      <div class="section-head"><h2>规范</h2><a href="/api/domain?slug={esc(slug)}">/api/domain</a></div>
      <div class="table-wrap"><table><thead><tr><th>规范</th><th>定位</th><th>类型</th><th>当前版本</th></tr></thead><tbody>{rows}</tbody></table></div>
    </section>
  </main>
</body></html>"""


def render_topic(slug: str) -> str:
    topic = psql_json(QUERIES["topic_detail"], {"topic": slug}) or {}
    links = psql_json(QUERIES["topic_links"], {"topic": slug}) or []
    explanations = psql_json(QUERIES["topic_explanations"], {"topic": slug}) or []
    if not topic:
        return "<!doctype html><html lang='zh-CN'><body><p>未找到该专题。</p></body></html>"

    core_cards = "\n".join(
        render_topic_link_card(link)
        for link in links
        if link.get("role") == "core"
    ) or '<p class="empty">当前没有核心节点。</p>'
    support_cards = "\n".join(
        render_topic_link_card(link)
        for link in links
        if link.get("role") in {"support", "exception"}
    ) or '<p class="empty">当前没有补充节点。</p>'
    background_cards = "\n".join(
        render_topic_link_card(link)
        for link in links
        if link.get("role") == "background"
    ) or '<p class="empty">当前没有背景事件。</p>'
    explanation_cards = "\n".join(
        f"""
        <article class="context-card">
          <div class="context-head">
            <span>{esc(item['title'])}</span>
            {badge(item['explanation_type'])}
          </div>
          <p>{esc(item['body'])}</p>
          <footer>
            <span>confidence {esc(item['confidence'])}</span>
            <span>{esc(item.get('source_title'))}</span>
          </footer>
        </article>
        """
        for item in explanations
    ) or '<p class="empty">当前还没有解释说明。</p>'
    return f"""<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(topic.get('title'))} · 法律规范体系仓库</title><style>{CSS}</style></head>
<body>
  <header class="topbar">
    <div><h1>{esc(topic.get('title'))}</h1><p>{esc(topic.get('pillar_title'))} · {esc(topic.get('question'))}</p></div>
    <div class="inline-actions"><a href="/">返回首页</a><a href="/instrument?slug=cn_company_law">返回公司法</a></div>
  </header>
  <main>
    <section class="stats">
      {stat_box('专题', topic.get('title'))}
      {stat_box('承力柱', topic.get('pillar_title'))}
      {stat_box('关联节点', topic.get('link_count'))}
      {stat_box('解释数', topic.get('explanation_count'))}
      {stat_box('状态', topic.get('status'))}
    </section>
    <section>
      <div class="section-head"><h2>专题摘要</h2><a href="/api/topic?slug={esc(slug)}">/api/topic</a></div>
      <article class="context-card"><p>{esc(topic.get('summary'))}</p></article>
    </section>
    <section>
      <div class="section-head"><h2>核心法条与规范</h2><a href="/api/topic?slug={esc(slug)}">核心节点</a></div>
      <div>{core_cards}</div>
    </section>
    <section>
      <div class="section-head"><h2>补充节点</h2><a href="/api/topic?slug={esc(slug)}">补充节点</a></div>
      <div>{support_cards}</div>
    </section>
    <section>
      <div class="section-head"><h2>政策与历史背景</h2><a href="/api/topic?slug={esc(slug)}">背景</a></div>
      <div>{background_cards}</div>
    </section>
    <section>
      <div class="section-head"><h2>大白话与提纲</h2><a href="/api/topic?slug={esc(slug)}">解释</a></div>
      <div>{explanation_cards}</div>
    </section>
  </main>
</body></html>"""


def render_topic_link_card(link: dict[str, object]) -> str:
    title = render_topic_target(link)
    description = esc(link.get("text") if link.get("target_type") == "legal_unit" else link.get("notes") or "")
    if link.get("target_type") == "context_event":
        description = esc(link.get("target_title"))
    meta = []
    if link.get("role"):
        meta.append(str(link["role"]))
    if link.get("version_label"):
        meta.append(str(link["version_label"]))
    if link.get("event_type"):
        meta.append(str(link["event_type"]))
    meta_text = " · ".join(meta)
    return f"""
    <article class="result">
      <div>{esc(meta_text)}</div>
      <h2>{title}</h2>
      <p>{description}</p>
    </article>
    """


def render_topic_target(link: dict[str, object]) -> str:
    href = topic_target_href(link)
    return f'<a href="{esc(href)}">{esc(link.get("target_title"))}</a>'


def topic_target_href(link: dict[str, object]) -> str:
    if link.get("target_type") == "legal_instrument":
        return f"/instrument?slug={link.get('target_slug')}"
    if link.get("target_type") == "legal_unit":
        target_slug = str(link.get("target_slug") or "")
        if target_slug.startswith("company_law:"):
            version = version_slug_from_ref(target_slug)
            article = article_no_from_ref(target_slug)
            return f"/law?version={version}&article={article}"
        instrument_slug = infer_instrument_slug_from_ref(target_slug)
        article = article_no_from_ref(target_slug)
        return f"/instrument-reader?slug={instrument_slug}&unit={article}"
    return "/api/contexts"


def render_instrument_reader(slug: str, unit: int | None) -> str:
    instrument = psql_json(QUERIES["instrument_detail"], {"instrument": slug}) or {}
    units = psql_json(QUERIES["instrument_units"], {"instrument": slug}) or []
    current = None
    if unit:
        current = psql_json(QUERIES["instrument_unit_detail"], {"instrument": slug, "unit": str(unit)})
    if not current and units:
        current = units[0]
    if not instrument:
        return "<!doctype html><html lang='zh-CN'><body><p>未找到该规范。</p></body></html>"

    current_no = int(current["unit_number_int"]) if current and current.get("unit_number_int") else 1
    unit_options = "\n".join(
        f'<option value="{esc(u["unit_number_int"])}" {"selected" if current and u["unit_number_int"] == current["unit_number_int"] else ""}>{esc(u["unit_number"])} · {esc(u["canonical_ref"])}</option>'
        for u in units
    )
    body = render_article_body(current)
    previous_link = nav_link_generic(slug, current_no - 1, "上一条", any(int(u.get("unit_number_int") or 0) == current_no - 1 for u in units))
    next_link = nav_link_generic(slug, current_no + 1, "下一条", any(int(u.get("unit_number_int") or 0) == current_no + 1 for u in units))
    relation_panel = ""
    if current and current.get("canonical_ref"):
        relations = psql_json(QUERIES["article_relations"], {"canonical_ref": str(current["canonical_ref"])}) or []
        relation_panel = "".join(
            f'<a href="{esc(relation_href(r))}">{esc(r["relation_type"])} · {esc(r["object_title"])}</a>'
            for r in relations[:8]
        ) or "<p>当前条文还没有补录跨法关系。</p>"
    topic_panel = ""
    if current and current.get("canonical_ref"):
        topics = psql_json(QUERIES["unit_topics"], {"canonical_ref": str(current["canonical_ref"])}) or []
        topic_panel = "".join(
            f'<a href="/topic?slug={esc(t["slug"])}">{esc(t["title"])} · {esc(t["pillar_title"])}</a>'
            for t in topics[:8]
        ) or "<p>当前条文还没有挂接专题。</p>"
    return f"""<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(instrument.get('short_title'))}条文阅读 · 法律规范体系仓库</title><style>{CSS}</style></head>
<body>
  <header class="topbar">
    <div><h1>{esc(instrument.get('short_title'))}条文阅读</h1><p><a href="/">返回首页</a> · <a href="/instrument?slug={esc(slug)}">返回规范页</a></p></div>
    <form class="reader-controls" action="/instrument-reader" method="get">
      <input type="hidden" name="slug" value="{esc(slug)}">
      <select name="unit" onchange="this.form.submit()">{unit_options}</select>
      <button type="submit">打开</button>
    </form>
  </header>
  <main class="reader-layout">
    <aside class="article-nav">
      <div class="nav-title">条文导航</div>
      {render_generic_article_nav(slug, units, current_no)}
    </aside>
    <section class="article-pane">
      <div class="reader-strip">
        {previous_link}
        <a href="/instrument?slug={esc(slug)}">返回规范概览</a>
        {next_link}
      </div>
      {body}
    </section>
    <aside class="reader-context">
      <section>
        <h3>当前规范</h3>
        <p><strong>{esc(instrument.get('short_title'))}</strong></p>
        <p><code>{esc(current.get('canonical_ref') if current else '')}</code></p>
        <a href="/graph?node_key=legal_unit:{esc(current.get('canonical_ref') if current else '')}">在图谱中打开</a>
      </section>
      <section>
        <h3>关联法条</h3>
        {relation_panel}
      </section>
      <section>
        <h3>相关专题</h3>
        {topic_panel}
      </section>
    </aside>
  </main>
</body></html>"""


def render_generic_article_nav(slug: str, units: list[dict[str, object]], current_no: int) -> str:
    groups = []
    for start in range(1, len(units) + 1, 20):
        chunk = units[start - 1:start + 19]
        if not chunk:
            continue
        first_no = int(chunk[0].get("unit_number_int") or 0)
        last_no = int(chunk[-1].get("unit_number_int") or 0)
        links = "".join(
            f'<a class="article-link {"active" if int(u["unit_number_int"]) == current_no else ""}" href="/instrument-reader?slug={esc(slug)}&unit={esc(u["unit_number_int"])}">{esc(u["unit_number"])}</a>'
            for u in chunk
        )
        open_attr = " open" if first_no <= current_no <= last_no else ""
        groups.append(f"<details{open_attr}><summary>第{first_no}-{last_no}条</summary><div>{links}</div></details>")
    return "\n".join(groups)


def nav_link_generic(slug: str, unit: int, label: str, enabled: bool) -> str:
    if not enabled:
        return f'<span class="disabled-link">{esc(label)}</span>'
    return f'<a href="/instrument-reader?slug={esc(slug)}&unit={esc(unit)}">{esc(label)}</a>'


def options_for_versions(versions: list[dict[str, object]], selected: str) -> str:
    return "\n".join(
        f'<option value="{esc(v["slug"])}" {"selected" if v["slug"] == selected else ""}>{esc(v["version_label"])}</option>'
        for v in versions
    )


def render_graph(node_key: str, to_node_key: str = "") -> str:
    selected = node_key or "legal_instrument:cn_company_law"
    node = get_node(selected)
    neighbors = get_neighbors(selected)
    path = get_path(selected, to_node_key) if to_node_key else {"nodes": [], "edges": []}
    if not node:
        return "<!doctype html><html lang='zh-CN'><body><p>未找到该图谱节点。</p></body></html>"

    structural_neighbors = [item for item in neighbors if item.get("relation_type") == "contains"]
    meaningful_neighbors = [item for item in neighbors if item.get("relation_type") != "contains"]
    grouped = {
        "政策背景": [item for item in meaningful_neighbors if item.get("relation_type") == "policy_background"],
        "上位/配套规范": [
            item for item in meaningful_neighbors
            if item.get("relation_type") in {"based_on", "specifies", "supplements", "constrained_by", "limits"}
        ],
        "制度联动": [
            item for item in meaningful_neighbors
            if item.get("relation_type") in {"interacts_with", "related_to", "same_domain", "interpreted_by"}
        ],
    }
    used_ids = {id(item) for items in grouped.values() for item in items}
    grouped["其他"] = [item for item in meaningful_neighbors if id(item) not in used_ids]

    neighbor_cards = "\n".join(
        f"""
        <article class="context-card">
          <div class="context-head">
            <span>{esc(relation_label(item['relation_type']))}</span>
            {badge('出去' if item['direction'] == 'outbound' else '进来')}
          </div>
          <h3><a href="/graph?node_key={esc(item['node_key'])}">{esc(item['title'])}</a></h3>
          <p>{esc(clip_text(item.get('subtitle'), 110))}</p>
          <footer>
            <span>{esc(item.get('evidence_level'))}</span>
            <span>{esc(item.get('source_title'))}</span>
          </footer>
        </article>
        """
        for item in meaningful_neighbors
    ) or '<p class="empty">当前节点还没有已整理的一跳制度关系。</p>'
    grouped_cards = "\n".join(
        f"""
        <article class="ask-panel">
          <div class="section-head"><h2>{esc(title)}</h2><span>{esc(len(items))} 个</span></div>
          <div class="mini-links">
            {"".join(f'<a href="/graph?node_key={esc(item["node_key"])}">{esc(item["title"])}</a>' for item in items[:8]) or '<span class="empty">当前没有。</span>'}
          </div>
        </article>
        """
        for title, items in grouped.items()
        if items
    )
    structure_cards = "\n".join(
        f'<a href="/graph?node_key={esc(item["node_key"])}">{esc(item["title"])} · {esc(clip_text(item.get("subtitle"), 48))}</a>'
        for item in structural_neighbors[:6]
    ) or '<p class="empty">当前没有结构隶属信息。</p>'
    path_body = ""
    if to_node_key:
        path_nodes = path.get("nodes") or []
        path_edges = path.get("edges") or []
        if path_nodes:
            path_lines = []
            for idx, item in enumerate(path_nodes):
                path_lines.append(f'<span class="path-node">{esc(item["title"])}</span>')
                if idx < len(path_edges):
                    edge = path_edges[idx]
                    path_lines.append(f'<span class="path-edge">{esc(edge["relation_type"])}</span>')
            path_body = "".join(path_lines)
        else:
            path_body = '<p class="empty">当前没有找到 4 跳以内的穿透路径。</p>'
    extract_action = ""
    if node.get("node_type") == "legal_unit":
        extract_action = f"""
        <button type="button" onclick="extractCandidates('{esc(node['ref'])}')">抽取候选关系</button>
        <span id="extractStatus"></span>
        """
    node_title = clip_text(node.get("title"), 40)
    node_subtitle = clip_text(node.get("subtitle"), 180)
    return f"""<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>关系穿透台 · 法律规范体系仓库</title><style>{CSS}</style></head>
<body>
  <header class="topbar">
    <div><h1>关系穿透台</h1><p>{esc(node_title)} · {esc(node_subtitle)}</p></div>
    <form class="search" action="/graph" method="get">
      <input name="node_key" value="{esc(selected)}" placeholder="legal_unit:company_law:2023:article_47">
      <button type="submit">打开节点</button>
    </form>
  </header>
  <main>
    <section class="stats">
      {stat_box('节点类型', node_type_label(node.get('node_type')))}
      {stat_box('引用', node.get('ref'))}
      {stat_box('制度关系', len(meaningful_neighbors))}
      {stat_box('结构关系', len(structural_neighbors))}
      {stat_box('路径目标', to_node_key or '-')}
    </section>
    <section class="graph-layout">
      <aside class="graph-side">
        <article class="graph-center">
          <div class="context-head">
            <span>{esc(node_type_label(node.get('node_type')))}</span>
            {badge('当前节点')}
          </div>
          <h2>{esc(node_title)}</h2>
          <p>{esc(node_subtitle)}</p>
          <div class="hint-box">{esc(graph_hint(node, meaningful_neighbors))}</div>
          <footer class="result-actions">
            <a href="{esc(node.get('href'))}">打开原文</a>
            <a href="/review">去审核台</a>
          </footer>
        </article>
        <article class="ask-panel">
          <div class="section-head"><h2>常用入口</h2><span>研究预设</span></div>
          <div class="mini-links">{graph_preset_links()}</div>
        </article>
        <article class="ask-panel">
          <div class="section-head"><h2>结构定位</h2><span>不计入制度关系</span></div>
          <div class="mini-links">{structure_cards}</div>
        </article>
        <article class="ask-panel">
          <div class="section-head"><h2>候选提议</h2><a href="/api/review/candidates">/api/review/candidates</a></div>
          <p>先在条文节点触发候选关系抽取，再到审核台转正。</p>
          <div class="ask-actions">{extract_action}</div>
        </article>
        <article class="ask-panel">
          <div class="section-head"><h2>路径查询</h2><a href="/api/graph/path">/api/graph/path</a></div>
          <form class="reader-controls" action="/graph" method="get">
            <input type="hidden" name="node_key" value="{esc(selected)}">
            <input name="to_node_key" value="{esc(to_node_key)}" placeholder="context_event:cn_registration_capital_reform_2013">
            <button type="submit">查路径</button>
          </form>
          <div class="path-box">{path_body or '<p class="empty">输入目标节点，查看穿透路径。</p>'}</div>
        </article>
      </aside>
      <section>
        <div class="stack-grid">{grouped_cards}</div>
        <div class="section-head"><h2>一跳关系</h2><a href="/api/graph/neighbors?node_key={esc(selected)}">/api/graph/neighbors</a></div>
        <div class="context-grid">{neighbor_cards}</div>
      </section>
    </section>
  </main>
  <script>
    async function extractCandidates(ref) {{
      const status = document.getElementById('extractStatus');
      status.textContent = '正在抽取...';
      try {{
        const res = await fetch('/api/agent/extract-relations', {{
          method: 'POST',
          headers: {{'Content-Type': 'application/json'}},
          body: JSON.stringify({{canonical_ref: ref}})
        }});
        const data = await res.json();
        status.textContent = data.ok ? `已写入候选 ${'{'}data.created.length{'}'} 条` : (data.error || '抽取失败');
      }} catch (err) {{
        status.textContent = String(err);
      }}
    }}
  </script>
</body></html>"""


def render_review(status: str, candidate_id: str = "") -> str:
    selected_status = status or "pending"
    candidates = list_candidates(selected_status)
    current_id = candidate_id or (str(candidates[0]["id"]) if candidates else "")
    current = get_candidate(current_id) if current_id else {}
    list_items = "\n".join(
        f"""
        <a class="candidate-item {'active' if str(item['id']) == current_id else ''}" href="/review?status={esc(selected_status)}&candidate_id={esc(item['id'])}">
          <strong>{esc(relation_label(item['relation_type']))}</strong>
          <span>{esc(item['subject_title'])} -> {esc(item['object_title'])}</span>
          <span>{esc(candidate_status_label(item['status']))} · {esc(item['source_title'])}</span>
        </a>
        """
        for item in candidates
    ) or '<p class="empty">当前状态下没有候选关系。</p>'
    current_claim = esc(current.get("claim_text")) if current else ""
    current_note = esc(current.get("review_note")) if current else ""
    return f"""<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>候选审核台 · 法律规范体系仓库</title><style>{CSS}</style></head>
<body>
  <header class="topbar">
    <div><h1>候选审核台</h1><p>模型先提议，你再接受、驳回或改写。</p></div>
    <form class="reader-controls" action="/review" method="get">
      <select name="status">
        <option value="pending" {"selected" if selected_status == "pending" else ""}>pending</option>
        <option value="needs_edit" {"selected" if selected_status == "needs_edit" else ""}>needs_edit</option>
        <option value="accepted" {"selected" if selected_status == "accepted" else ""}>accepted</option>
        <option value="rejected" {"selected" if selected_status == "rejected" else ""}>rejected</option>
        <option value="" {"selected" if selected_status == "" else ""}>all</option>
      </select>
      <button type="submit">切换</button>
    </form>
  </header>
  <main class="review-layout">
    <aside class="article-nav">
      <div class="nav-title">候选队列</div>
      <div class="candidate-list">{list_items}</div>
    </aside>
    <section class="article-pane">
      <div class="section-head"><h2>候选详情</h2><a href="/api/review/candidates?status={esc(selected_status)}">/api/review/candidates</a></div>
      {render_candidate_detail(current)}
      <article class="ask-panel">
        <div class="section-head"><h2>编辑与审核</h2><a href="/api/review/candidate">candidate</a></div>
        <input id="candidateId" type="hidden" value="{esc(current.get('id') if current else '')}">
        <label>关系类型</label>
        <input id="candidateRelationType" value="{esc(current.get('relation_type') if current else '')}">
        <label>主张</label>
        <textarea id="candidateClaim">{current_claim}</textarea>
        <label>置信度</label>
        <input id="candidateConfidence" value="{esc(current.get('confidence') if current else '')}">
        <label>审核备注</label>
        <textarea id="candidateNote">{current_note}</textarea>
        <div class="ask-actions">
          <button type="button" onclick="acceptCandidate()">接受</button>
          <button type="button" onclick="saveCandidateEdit()">改写</button>
          <button type="button" onclick="rejectCandidate()">驳回</button>
          <span id="reviewStatus"></span>
        </div>
      </article>
    </section>
    <aside class="reader-context">
      <section>
        <h3>证据来源</h3>
        <p><strong>{esc(current.get('source_title') if current else '')}</strong></p>
        <p>{esc(current.get('source_excerpt_text') or current.get('excerpt_text') if current else '')}</p>
        <a href="{esc(current.get('source_url') if current else '')}" target="_blank" rel="noreferrer">打开来源</a>
      </section>
      <section>
        <h3>图谱跳转</h3>
        <a href="/graph?node_key={esc(current.get('subject_node_key') if current else '')}">打开主体节点</a>
        <a href="/graph?node_key={esc(current.get('object_node_key') if current else '')}">打开客体节点</a>
      </section>
    </aside>
  </main>
  <script>
    async function postCandidate(path, payload) {{
      const res = await fetch(path, {{
        method: 'POST',
        headers: {{'Content-Type': 'application/json'}},
        body: JSON.stringify(payload)
      }});
      return await res.json();
    }}
    async function acceptCandidate() {{
      const id = document.getElementById('candidateId').value;
      const status = document.getElementById('reviewStatus');
      const data = await postCandidate('/api/review/candidate/accept', {{candidate_id: id}});
      status.textContent = data.status || data.error || '完成';
    }}
    async function rejectCandidate() {{
      const id = document.getElementById('candidateId').value;
      const note = document.getElementById('candidateNote').value;
      const status = document.getElementById('reviewStatus');
      const data = await postCandidate('/api/review/candidate/reject', {{candidate_id: id, review_note: note}});
      status.textContent = data.status || data.error || '完成';
    }}
    async function saveCandidateEdit() {{
      const id = document.getElementById('candidateId').value;
      const relationType = document.getElementById('candidateRelationType').value;
      const claimText = document.getElementById('candidateClaim').value;
      const confidence = document.getElementById('candidateConfidence').value;
      const note = document.getElementById('candidateNote').value;
      const status = document.getElementById('reviewStatus');
      const data = await postCandidate('/api/review/candidate/edit', {{
        candidate_id: id,
        relation_type: relationType,
        claim_text: claimText,
        confidence: confidence,
        review_note: note
      }});
      status.textContent = data.status || data.error || '完成';
    }}
  </script>
</body></html>"""


def render_candidate_detail(candidate: dict[str, object]) -> str:
    if not candidate:
        return '<p class="empty">当前没有可审核候选。</p>'
    return f"""
    <article class="result">
      <div>{esc(candidate_status_label(candidate.get('status')))} · {esc(candidate.get('proposer'))}</div>
      <h2>{esc(candidate.get('subject_title'))} -> {esc(candidate.get('object_title'))}</h2>
      <p>{esc(candidate.get('claim_text'))}</p>
      <p><strong>关系语义：</strong>{esc(relation_label(candidate.get('relation_type')))}</p>
      <footer class="result-actions">
        <a href="/graph?node_key={esc(candidate.get('subject_node_key'))}">主体图谱</a>
        <a href="/graph?node_key={esc(candidate.get('subject_node_key'))}&to_node_key={esc(candidate.get('object_node_key'))}">穿透路径</a>
      </footer>
    </article>
    """


CSS = """
:root {
  color-scheme: light;
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  color: #1d2430;
  background: #f5f7fa;
}
* { box-sizing: border-box; }
body { margin: 0; }
a { color: #225ea8; text-decoration: none; }
a:hover { text-decoration: underline; }
.topbar {
  display: flex;
  align-items: end;
  justify-content: space-between;
  gap: 24px;
  padding: 28px 32px;
  background: #ffffff;
  border-bottom: 1px solid #d9e0e8;
}
h1 { margin: 0; font-size: 26px; letter-spacing: 0; }
h2 { margin: 0; font-size: 18px; letter-spacing: 0; }
h3 { margin: 8px 0; font-size: 16px; letter-spacing: 0; }
p { line-height: 1.6; }
.topbar p { margin: 8px 0 0; color: #627084; }
.inline-actions { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }
.search { display: flex; gap: 8px; min-width: 360px; }
.search input {
  width: 100%;
  height: 38px;
  border: 1px solid #c7d0dc;
  border-radius: 6px;
  padding: 0 12px;
  font-size: 14px;
}
.search button,
.ask-actions button,
.reader-controls button {
  height: 38px;
  border: 0;
  border-radius: 6px;
  padding: 0 16px;
  background: #1f6feb;
  color: white;
  font-weight: 600;
}
.ask-panel input,
.ask-panel textarea {
  width: 100%;
  border: 1px solid #c7d0dc;
  border-radius: 6px;
  padding: 10px 12px;
  font: inherit;
}
.ask-panel label {
  display: block;
  margin: 10px 0 6px;
  color: #44546a;
  font-size: 13px;
  font-weight: 700;
}
main { max-width: 1180px; margin: 0 auto; padding: 28px 24px 64px; }
section { margin-top: 24px; }
.quick-actions, .stats, .pillar-grid, .context-grid, .compare-grid, .graph-layout, .review-layout, .stack-grid {
  display: grid;
  gap: 12px;
}
.quick-actions { grid-template-columns: repeat(3, minmax(0, 1fr)); margin-top: 0; }
.stats { grid-template-columns: repeat(5, minmax(0, 1fr)); margin-top: 0; }
.pillar-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }
.context-grid, .compare-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
.graph-layout { grid-template-columns: 340px minmax(0, 1fr); align-items: start; }
.review-layout { grid-template-columns: 280px minmax(0, 1fr) 260px; align-items: start; }
.stack-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); margin-bottom: 12px; }
.quick-actions a, .context-card, .pillar-card, .domain-card, .result, .ask-panel, .article-pane, .compare-pane, .stats article {
  background: white;
  border: 1px solid #d9e0e8;
  border-radius: 8px;
  padding: 16px;
}
.quick-actions a { min-height: 72px; }
.quick-actions strong, .pillar-card strong { display: block; color: #172033; }
.quick-actions span, .stats span, .pillar-card footer, .reader-context p { color: #637287; font-size: 13px; }
.reader-controls {
  display: flex;
  gap: 8px;
  align-items: center;
  min-width: 520px;
}
.reader-controls select, .reader-controls input {
  height: 38px;
  border: 1px solid #c7d0dc;
  border-radius: 6px;
  padding: 0 10px;
  background: #ffffff;
  font: inherit;
}
.reader-controls input { width: 72px; }
.reader-layout {
  display: grid;
  grid-template-columns: 240px minmax(0, 1fr) 260px;
  gap: 18px;
  max-width: 1440px;
}
.article-nav, .reader-context section {
  border: 1px solid #d9e0e8;
  border-radius: 8px;
  background: #ffffff;
}
.article-nav {
  position: sticky;
  top: 12px;
  align-self: start;
  max-height: calc(100vh - 32px);
  overflow: auto;
  padding: 10px;
}
.nav-title { padding: 4px 6px 10px; color: #24364d; font-weight: 750; }
.article-nav details { border-top: 1px solid #edf1f5; padding: 6px 0; }
.article-nav details:first-of-type { border-top: 0; }
.article-nav summary { cursor: pointer; padding: 6px; color: #526173; font-size: 13px; font-weight: 700; }
.article-nav details div { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 4px; }
.article-link { display: block; padding: 6px 8px; border-radius: 5px; color: #44546a; font-size: 13px; }
.article-link.active, .article-link:hover { background: #e8f0fe; color: #174ea6; text-decoration: none; }
.reader-strip, .context-head, .context-card footer, .section-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
}
.reader-strip { margin-bottom: 18px; padding-bottom: 12px; border-bottom: 1px solid #edf1f5; }
.reader-strip a, .disabled-link, .result-actions a, .reader-context a {
  display: inline-flex;
  align-items: center;
  min-height: 32px;
  padding: 6px 10px;
  border-radius: 5px;
}
.reader-strip a, .result-actions a { background: #edf5ff; color: #174ea6; font-weight: 650; }
.reader-context { position: sticky; top: 12px; align-self: start; }
.reader-context section { margin: 0 0 12px; padding: 14px; }
.reader-context a { display: block; margin: 8px 0; background: #f6f8fb; font-weight: 650; }
.graph-side { position: sticky; top: 12px; align-self: start; display: grid; gap: 12px; }
.graph-center { background: white; border: 1px solid #d9e0e8; border-radius: 8px; padding: 16px; }
.mini-links {
  display: grid;
  gap: 8px;
}
.mini-links a {
  display: block;
  padding: 8px 10px;
  border-radius: 6px;
  background: #f6f8fb;
  color: #1d3557;
}
.hint-box {
  margin-top: 12px;
  padding: 10px 12px;
  border-radius: 6px;
  background: #eef5ff;
  color: #24435f;
  font-size: 13px;
}
.candidate-list { display: grid; gap: 8px; }
.candidate-item {
  display: block;
  padding: 10px;
  border-radius: 6px;
  background: #f6f8fb;
  border: 1px solid #e2e8f0;
}
.candidate-item span { display: block; margin-top: 4px; color: #637287; font-size: 12px; }
.candidate-item.active { background: #e8f0fe; border-color: #9ec3ff; color: #174ea6; text-decoration: none; }
.path-box {
  margin-top: 12px;
  padding: 12px;
  border-radius: 6px;
  background: #f7fafc;
  min-height: 72px;
}
.path-node, .path-edge {
  display: inline-flex;
  align-items: center;
  min-height: 28px;
  padding: 4px 8px;
  margin: 0 6px 6px 0;
  border-radius: 6px;
}
.path-node { background: #e8f0fe; color: #174ea6; }
.path-edge { background: #eef2f7; color: #556476; font-size: 12px; }
.reader-context code, .article-meta code, .answer-card code {
  padding: 2px 5px;
  border-radius: 4px;
  background: #eef2f7;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}
.article-meta { color: #637287; font-size: 13px; margin-bottom: 10px; }
.article-text p { margin: 10px 0; line-height: 1.85; font-size: 17px; }
.table-wrap { overflow: auto; background: white; border: 1px solid #d9e0e8; border-radius: 8px; }
table { width: 100%; border-collapse: collapse; font-size: 14px; }
th, td { padding: 12px 14px; text-align: left; border-bottom: 1px solid #edf1f5; vertical-align: top; }
th { background: #f9fafc; color: #526173; font-weight: 700; }
td span { display: block; margin-top: 4px; color: #68778a; font-size: 12px; }
.badge {
  display: inline-block;
  padding: 3px 8px;
  border-radius: 999px;
  background: #e8f0fe;
  color: #244f9e;
  font-size: 12px;
  font-weight: 700;
}
.ask-panel textarea {
  width: 100%;
  min-height: 112px;
  resize: vertical;
  border: 1px solid #c7d0dc;
  border-radius: 6px;
  padding: 12px;
  font: inherit;
}
.ask-actions { display: flex; align-items: center; gap: 12px; margin-top: 10px; }
#askStatus, .empty { color: #637287; font-size: 13px; }
#askAnswer.answer-card {
  margin: 14px 0 0;
  padding: 14px;
  border-radius: 8px;
  background: #f7fafc;
  color: #152033;
  line-height: 1.6;
  overflow: auto;
}
.answer-card:empty { display: none; }
.answer-card ul { margin: 8px 0 10px 18px; padding: 0; }
.answer-card blockquote { margin: 10px 0; padding: 8px 12px; border-left: 3px solid #6aa3ff; background: #eef5ff; }
@media (max-width: 820px) {
  .topbar { display: block; padding: 20px; }
  .search, .reader-controls { min-width: 0; margin-top: 16px; }
  .reader-controls { display: grid; grid-template-columns: 1fr; }
  .reader-controls input { width: 100%; }
  main { padding: 20px 14px 48px; }
  .stats { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .quick-actions, .pillar-grid, .context-grid, .compare-grid, .reader-layout, .graph-layout, .review-layout, .stack-grid { grid-template-columns: 1fr; }
  .article-nav { position: static; max-height: 220px; }
  .reader-context { position: static; }
  .graph-side { position: static; }
}
"""
