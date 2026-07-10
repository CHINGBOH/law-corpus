# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A database-backed corpus for Chinese (mainland) legal and policy history, anchored on
Company Law but modeled as a general legal-system base (related laws, regulations, and
policy background as independent, cross-linked nodes). PostgreSQL is the only mutable
source of truth; XML/AKN and raw source files live outside the database and are
referenced by URI; DuckDB is a read-only analysis layer over exported Parquet/CSV, not
an application database.

## Commands

Bootstrap a fresh database (run in order):

```bash
createdb legal_corpus
psql -d legal_corpus -f sql/001_schema.sql
psql -d legal_corpus -f sql/002_seed_company_law.sql
psql -d legal_corpus -f sql/004_legal_system_base.sql
psql -d legal_corpus -f sql/005_topics_and_explanations.sql
psql -d legal_corpus -f sql/006_graph_review_stack.sql
psql -d legal_corpus -f sql/003_validation_queries.sql   # sanity checks, run last
```

Local dev connection defaults (see `.env.example`):

```bash
PGHOST=127.0.0.1 PGPORT=5432 PGDATABASE=legal_corpus PGUSER=legal_corpus PGPASSWORD=legal_corpus_dev
```

Run the app (single port serves HTML pages + JSON APIs, pure stdlib — no
`requirements.txt`, no build step):

```bash
python3 app/server.py
# http://127.0.0.1:8000
```

Enable the `/api/ask` DeepSeek Q&A endpoint:

```bash
export DEEPSEEK_API_KEY=...
export DEEPSEEK_MODEL=deepseek-v4-flash
python3 app/server.py
```

Import/refresh Company Law article text into `legal_units`:

```bash
python3 scripts/import_company_law_articles.py
```

There is no test suite or linter configured. Validate schema/data changes with
`sql/003_validation_queries.sql` and by exercising the relevant `/api/*` endpoint against
a running server.

## Architecture

```
XML / AKN files   Immutable structured legal text (xml-akn/)
PostgreSQL        Authoritative metadata, versions, units, sources, claims
DuckDB            Read-only analysis over exported Parquet/CSV (analysis/)
Object storage    Raw PDFs, HTML snapshots, OCR output (object-store/)
```

### `app/` — single-process HTTP app

`server.py` is a stdlib `http.server` app (`ThreadingHTTPServer`) that serves both HTML
reader pages and `/api/*` JSON endpoints from one port. It has **no Python DB driver** —
all queries go through `db_access.psql_json` / `psql_exec`, which shell out to `psql -A
-t -q -c "<sql>"` and parse stdout as JSON (queries are written to return
`jsonb`/`jsonb_agg` directly from Postgres).

Module responsibilities:
- `db_access.py` — psql subprocess wrapper, param substitution (`render_sql` replaces
  `%(name)s` placeholders with SQL-escaped literals — this is manual escaping, not
  driver-level parameterization; keep new query params going through `render_sql`/
  `sql_quote`, never string-format user input directly into SQL).
- `query_defs.py` — the `QUERIES` dict of named SQL strings used across the app, plus
  `LEGAL_TERMS`/`TERM_EXPANSIONS` (Chinese legal-term search vocabulary) and `PILLARS`
  (doctrine-topic definitions).
- `graph_service.py` — thin wrappers around the `v_graph_nodes`/`v_graph_edges` graph
  read model (node lookup, neighbors, path).
- `review_service.py` — human review workflow for `relation_candidates`
  (accept/reject/edit), where accept promotes a candidate into `legal_relations`.
- `agent_service.py` — LLM-assisted relation extraction: loads a legal unit as
  "subject", proposes candidate cross-references via DeepSeek (`llm_proposals`) with a
  rule-based fallback (`fallback_proposals`) when no API key is set, then inserts them
  into `relation_candidates` for review. `ALLOWED_RELATIONS` is the closed vocabulary of
  relation types.
- `llm_support.py` — DeepSeek client for `/api/ask` (builds context from instruments,
  version timeline, relations, topics, and full-text search hits, then requests a
  Markdown answer), plus a small hand-rolled Markdown→HTML renderer
  (`markdown_to_html`/`inline_md`) used to render answers without a Markdown dependency.
- `ui.py` — server-side HTML page rendering (reader pages, graph view, review UI,
  search).

Routing lives entirely in `server.py`'s `Handler.do_GET`/`do_POST`/`api_response`: adding
an endpoint means adding a branch there, a query in `query_defs.py` (or a service
function), and, for pages, a `render_*` function in `ui.py`.

### SQL migrations (`sql/`, applied in numeric order)

- `001_schema.sql` — core tables: `documents`, `sources`, `source_excerpts`,
  `legal_instruments`, versions, units.
- `002_seed_company_law.sql` — seed data for the seven Company Law versions.
- `004_legal_system_base.sql` — `legal_domains`, `instrument_domains`, `legal_relations`
  (cross-law/cross-article edges: `based_on`, `specifies`, `supplements`,
  `constrained_by`, `same_domain`, `interacts_with`, `policy_background`, etc.).
- `005_topics_and_explanations.sql` — `doctrine_topics`, `topic_links`,
  `plain_explanations` (plain-language doctrine layer, e.g. capital credit, corporate
  personality, registration/publicity, creditor protection, governance controls).
- `006_graph_review_stack.sql` — `relation_candidates` (pending graph edges awaiting
  review) and the `v_graph_nodes`/`v_graph_edges` views that project instruments,
  versions, articles, context events, and relations into a graph read model.
- `003_validation_queries.sql` — sanity/consistency checks, run last, not schema DDL.

### Evidence rule (applies to data, not just code)

Historical/comparative claims (e.g. "the Company Law drew on Singapore company law")
must be stored via `context_links`/`legal_relations` with `claim_text`, `source_id`,
`evidence_level`, and `confidence` — never as unconditional fact. This applies to
`relation_candidates` proposals from `agent_service.py` as much as to hand-entered SQL:
a candidate is only insertable when it resolves to a real `sources` row
(`insert_candidate` no-ops otherwise).
