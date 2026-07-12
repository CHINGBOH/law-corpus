# Legal Corpus

This project is the database base for a legal and policy-history corpus. The
first anchored corpus is mainland China's Company Law, but the storage model is
built as a broader legal-system base so related laws, regulations, and policy
background can be recorded as independent nodes.

## Architecture

```text
XML / AKN files        Immutable structured legal text
PostgreSQL            Authoritative metadata, versions, units, sources, claims
DuckDB                Read-only analysis over exported Parquet/CSV
Object storage        Raw PDFs, HTML snapshots, OCR output, source archives
```

PostgreSQL is the only mutable source of truth. XML and raw files are stored
outside PostgreSQL and referenced by URI. DuckDB reads exported data for
analysis; it is not an application database.

## Layout

```text
legal-corpus/
├── sql/
│   ├── 001_schema.sql
│   ├── 002_seed_company_law.sql
│   ├── 003_validation_queries.sql
│   ├── 004_legal_system_base.sql
│   ├── 005_topics_and_explanations.sql
│   ├── 006_graph_review_stack.sql
│   └── 007_chinese_fts.sql
├── app/
│   ├── server.py
│   ├── db_access.py
│   ├── graph_service.py
│   ├── review_service.py
│   ├── agent_service.py
│   ├── query_defs.py
│   ├── llm_support.py
│   ├── workspace_service.py
│   └── static/            # built frontend output (generated, not committed)
├── frontend/               # Vue 3 + Vite research workstation (SPA)
│   └── src/
├── analysis/
│   └── company_law.duckdb.sql
├── xml-akn/
│   └── company_law/
├── exports/
└── object-store/
```

## Bootstrap

```bash
createdb legal_corpus
psql -d legal_corpus -f legal-corpus/sql/001_schema.sql
psql -d legal_corpus -f legal-corpus/sql/002_seed_company_law.sql
psql -d legal_corpus -f legal-corpus/sql/004_legal_system_base.sql
psql -d legal_corpus -f legal-corpus/sql/005_topics_and_explanations.sql
psql -d legal_corpus -f legal-corpus/sql/006_graph_review_stack.sql
psql -d legal_corpus -f legal-corpus/sql/007_chinese_fts.sql
psql -d legal_corpus -f legal-corpus/sql/003_validation_queries.sql
```

Local development database created in this workspace:

```bash
PGHOST=127.0.0.1
PGPORT=5432
PGDATABASE=legal_corpus
PGUSER=legal_corpus
PGPASSWORD=legal_corpus_dev
```

## App: Python API + Vue Research Workstation

The backend (`app/server.py`) is a stdlib `http.server` app that serves JSON
`/api/*` endpoints and, in production, the built frontend as static files
(SPA fallback to `index.html` so client-side routes survive a hard refresh).
It uses `psql` to query PostgreSQL, so no Python database driver is required.
The frontend (`frontend/`) is a Vue 3 + Vite single-page app — the research
workstation UI (graph explorer, review queue, article readers, compare view,
topic/domain/instrument browsers).

**Development** (two ports — backend serves the API, Vite serves the UI and
proxies `/api/*` to the backend):

```bash
python3 legal-corpus/app/server.py        # terminal A, http://127.0.0.1:8000
cd legal-corpus/frontend && npm install && npm run dev  # terminal B, http://127.0.0.1:5173
```

Open `http://127.0.0.1:5173` during development.

**Production** (single port — build the frontend into `app/static/`, then run
only the Python server):

```bash
cd legal-corpus/frontend && npm run build   # outputs to ../app/static
python3 legal-corpus/app/server.py
```

Open:

```text
http://127.0.0.1:8000
```

Aggregated view endpoints used by the frontend (`/api/workspace/*`, each
returns everything one SPA route needs in a single call — labels, hrefs, and
groupings pre-resolved server-side):

```text
GET  /api/workspace/home
GET  /api/workspace/search?q=注册资本
GET  /api/workspace/graph?node_key=legal_unit:company_law:2023:article_47&to_node_key=
GET  /api/workspace/reader?version=cn_company_law_2023&article=47
GET  /api/workspace/instrument-reader?slug=cn_civil_code&unit=61
GET  /api/workspace/compare?left=cn_company_law_2018&right=cn_company_law_2023&article=47
GET  /api/workspace/instrument?slug=cn_company_law
GET  /api/workspace/domain?slug=commercial-organization
GET  /api/workspace/topic?slug=capital-credit
GET  /api/workspace/review?status=pending&candidate_id=
POST /api/workspace/review/candidate/accept   {candidate_id, status}
POST /api/workspace/review/candidate/reject   {candidate_id, review_note, status}
POST /api/workspace/review/candidate/edit     {candidate_id, relation_type, claim_text, confidence, review_note, status}
```

The three review POST endpoints return the entire refreshed queue bundle
(list + selected detail), not just the mutated row, so the frontend never
needs a separate re-fetch after accept/reject/edit.

Lower-level raw endpoints, kept for scripting/debugging independent of any
page's presentation layer:

```text
/api/stats
/api/versions
/api/contexts
/api/sources
/api/search?q=注册资本
/api/evidence/excerpts?source_slug=src_registration_regulation_2021_gov
/api/graph/node?node_key=legal_unit:company_law:2023:article_47
/api/graph/neighbors?node_key=legal_unit:company_law:2023:article_47
/api/graph/path?from_node_key=legal_unit:company_law:2023:article_47&to_node_key=context_event:cn_registration_capital_reform_2013
/api/agent/extract-relations   (POST {canonical_ref})
/api/ask                        (POST {question}, DeepSeek Q&A, see below)
```

DeepSeek question answering is enabled when `DEEPSEEK_API_KEY` is set:

```bash
export DEEPSEEK_API_KEY=...
export DEEPSEEK_MODEL=deepseek-v4-flash
python3 legal-corpus/app/server.py
```

The ask endpoint builds context from the legal-system catalog, company-law
version timeline, cross-law relations, policy/history evidence, and matching
legal units. The response is requested as concise Markdown and rendered as a
styled answer card in the page.

Frontend routes (client-side, Vue Router history mode — same path/query
scheme as the endpoints above):

```text
/                                    home
/search?q=
/instrument?slug=cn_company_law
/domain?slug=commercial-organization
/topic?slug=capital-credit
/graph?node_key=legal_unit:company_law:2023:article_47
/review?status=pending
/law?version=cn_company_law_2023&article=47
/instrument-reader?slug=cn_civil_code&unit=61
/compare?left=cn_company_law_2018&right=cn_company_law_2023&article=47
```

## Legal-System Base

- `legal_domains`: constitutional foundation, civil-law foundation, commercial
  organization, capital market, insolvency/exit, registration/supervision,
  state-owned assets, foreign investment.
- `instrument_domains`: maps legal instruments into one or more domains.
- `legal_relations`: stores cross-law and cross-article relations such as
  `based_on`, `specifies`, `supplements`, `constrained_by`, `same_domain`,
  `interacts_with`, and `policy_background`.
- `doctrine_topics`: stores doctrine/topic nodes such as capital credit,
  corporate personality, registration/publicity, creditor protection, and
  governance controls.
- `topic_links`: binds topics to instruments, units, and context events with
  roles such as `core`, `support`, and `background`.
- `plain_explanations`: stores plain-language explanations, outlines, risks,
  and comparisons tied to topics or legal nodes.
- `relation_candidates`: stores model- or human-proposed graph edges pending
  review. A candidate must carry source evidence before it can be accepted into
  `legal_relations`.
- `v_graph_nodes` / `v_graph_edges`: project instruments, versions, articles,
  context events, structural containment edges, formal legal relations, and
  version-context links into a graph-oriented read model.
- The first wave of related instruments currently includes Constitution, Civil
  Code, Securities Law, Enterprise Bankruptcy Law, Market Entity Registration
  Regulation, State-owned Assets Law, Foreign Investment Law, Partnership
  Enterprise Law, and Sole Proprietorship Law.

## Company Law v1 Scope

- Seven formal mainland Company Law versions: 1993, 1999, 2004, 2005, 2013,
  2018, 2023.
- Source records for official or government/professional materials already
  identified during research.
- Policy and historical context events for company-law formation and major
  amendments.
- Evidence-graded claims for historical origin and comparative-law influence.

The first implementation stores article-level legal units. Paragraph/item-level
units can be added later through the same `legal_units` table.

## Import Article Text

Fetch available full-text pages, write raw/XML files, and populate
`legal_units` at article level:

```bash
python3 legal-corpus/scripts/import_company_law_articles.py
```

Current article extraction counts:

| Version | Articles | Source quality |
| --- | ---: | --- |
| 1993 | 230 | Wiki full text, to be replaced with official/gazette source |
| 1999 | 230 | Wiki full text, to be replaced with official/gazette source |
| 2004 | 230 | Wiki full text, to be replaced with official/gazette source |
| 2005 | 219 | Government site full text |
| 2013 | 218 | Wiki full text, to be replaced with official/gazette source |
| 2018 | 218 | Professional site full text, to be replaced with official/gazette source |
| 2023 | 266 | Government policy database full text |

## Evidence Rule

Claims such as "the Company Law learned from Singapore company law" must be
stored in `context_links` with:

- `claim_text`
- `source_id`
- `evidence_level`
- `confidence`

They must not be represented as unconditional facts unless backed by a source
record and an explicit confidence level.
