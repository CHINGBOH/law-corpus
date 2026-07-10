#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from db_access import parse_int, psql_json
from agent_service import extract_relation_candidates
from graph_service import get_neighbors, get_node, get_path
from llm_support import ask_deepseek
from query_defs import QUERIES
from review_service import accept_candidate, edit_candidate, get_candidate, list_candidates, reject_candidate
from ui import (
    render_compare,
    render_domain,
    render_graph,
    render_instrument,
    render_instrument_reader,
    render_law_reader,
    render_page,
    render_review,
    render_search,
    render_topic,
)


HOST = os.environ.get("LEGAL_CORPUS_HOST", "127.0.0.1")
PORT = int(os.environ.get("LEGAL_CORPUS_PORT", "8000"))


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        try:
            if parsed.path == "/":
                self.send_html(render_page())
            elif parsed.path == "/instrument":
                query = parse_qs(parsed.query)
                slug = query.get("slug", ["cn_company_law"])[0]
                self.send_html(render_instrument(slug))
            elif parsed.path == "/domain":
                query = parse_qs(parsed.query)
                slug = query.get("slug", ["commercial-organization"])[0]
                self.send_html(render_domain(slug))
            elif parsed.path == "/topic":
                query = parse_qs(parsed.query)
                slug = query.get("slug", ["capital-credit"])[0]
                self.send_html(render_topic(slug))
            elif parsed.path == "/instrument-reader":
                query = parse_qs(parsed.query)
                slug = query.get("slug", ["cn_civil_code"])[0]
                unit = parse_int(query.get("unit", ["1"])[0], 1)
                self.send_html(render_instrument_reader(slug, unit))
            elif parsed.path == "/law":
                query = parse_qs(parsed.query)
                version = query.get("version", ["cn_company_law_2023"])[0]
                article = parse_int(query.get("article", ["1"])[0], 1)
                self.send_html(render_law_reader(version, article))
            elif parsed.path == "/compare":
                query = parse_qs(parsed.query)
                left = query.get("left", ["cn_company_law_2018"])[0]
                right = query.get("right", ["cn_company_law_2023"])[0]
                article = parse_int(query.get("article", ["47"])[0], 47)
                self.send_html(render_compare(left, right, article))
            elif parsed.path == "/search":
                query = parse_qs(parsed.query).get("q", [""])[0].strip()
                self.send_html(render_search(query))
            elif parsed.path == "/graph":
                query = parse_qs(parsed.query)
                node_key = query.get("node_key", ["legal_instrument:cn_company_law"])[0]
                to_node_key = query.get("to_node_key", [""])[0]
                self.send_html(render_graph(node_key, to_node_key))
            elif parsed.path == "/review":
                query = parse_qs(parsed.query)
                status = query.get("status", ["pending"])[0]
                candidate_id = query.get("candidate_id", [""])[0]
                self.send_html(render_review(status, candidate_id))
            elif parsed.path.startswith("/api/"):
                self.send_json(self.api_response(parsed.path, parsed.query))
            else:
                self.send_error(404, "Not found")
        except Exception as exc:
            self.send_error(500, str(exc))

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        try:
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length).decode("utf-8") if length else "{}"
            payload = json.loads(body or "{}")
            if parsed.path == "/api/ask":
                question = str(payload.get("question", "")).strip()
                if not question:
                    self.send_json({"ok": False, "error": "question is required", "answer": ""})
                    return
                self.send_json(ask_deepseek(question))
                return
            if parsed.path == "/api/review/candidate/accept":
                self.send_json(accept_candidate(str(payload.get("candidate_id", "")).strip()))
                return
            if parsed.path == "/api/review/candidate/reject":
                self.send_json(
                    reject_candidate(
                        str(payload.get("candidate_id", "")).strip(),
                        str(payload.get("review_note", "")).strip(),
                    )
                )
                return
            if parsed.path == "/api/review/candidate/edit":
                self.send_json(
                    edit_candidate(
                        str(payload.get("candidate_id", "")).strip(),
                        str(payload.get("relation_type", "")).strip(),
                        str(payload.get("claim_text", "")).strip(),
                        str(payload.get("confidence", "")).strip() or "0.50",
                        str(payload.get("review_note", "")).strip(),
                    )
                )
                return
            if parsed.path == "/api/agent/extract-relations":
                self.send_json(extract_relation_candidates(str(payload.get("canonical_ref", "")).strip()))
                return
            self.send_error(404, "Not found")
        except Exception as exc:
            self.send_error(500, str(exc))

    def api_response(self, path: str, query_string: str) -> object:
        if path == "/api/domains":
            return psql_json(QUERIES["domains"]) or []
        if path == "/api/topics":
            return psql_json(QUERIES["topics"]) or []
        if path == "/api/topic":
            query = parse_qs(query_string)
            slug = query.get("slug", ["capital-credit"])[0]
            return {
                "topic": psql_json(QUERIES["topic_detail"], {"topic": slug}) or {},
                "links": psql_json(QUERIES["topic_links"], {"topic": slug}) or [],
                "explanations": psql_json(QUERIES["topic_explanations"], {"topic": slug}) or [],
            }
        if path == "/api/instruments":
            return psql_json(QUERIES["instruments"]) or []
        if path == "/api/graph/node":
            query = parse_qs(query_string)
            node_key = query.get("node_key", ["legal_instrument:cn_company_law"])[0]
            return get_node(node_key)
        if path == "/api/graph/neighbors":
            query = parse_qs(query_string)
            node_key = query.get("node_key", ["legal_instrument:cn_company_law"])[0]
            return get_neighbors(node_key)
        if path == "/api/graph/path":
            query = parse_qs(query_string)
            from_node_key = query.get("from_node_key", ["legal_instrument:cn_company_law"])[0]
            to_node_key = query.get("to_node_key", [""])[0]
            return get_path(from_node_key, to_node_key) if to_node_key else {"nodes": [], "edges": []}
        if path == "/api/instrument":
            query = parse_qs(query_string)
            slug = query.get("slug", ["cn_company_law"])[0]
            return psql_json(QUERIES["instrument_detail"], {"instrument": slug}) or {}
        if path == "/api/instrument-units":
            query = parse_qs(query_string)
            slug = query.get("slug", ["cn_company_law"])[0]
            return psql_json(QUERIES["instrument_units"], {"instrument": slug}) or []
        if path == "/api/domain":
            query = parse_qs(query_string)
            slug = query.get("slug", ["commercial-organization"])[0]
            return {
                "domain": psql_json(QUERIES["domain_detail"], {"domain": slug}) or {},
                "instruments": psql_json(QUERIES["domain_instruments"], {"domain": slug}) or [],
            }
        if path == "/api/relations":
            query = parse_qs(query_string)
            slug = query.get("instrument", ["cn_company_law"])[0]
            return psql_json(QUERIES["instrument_relations"], {"instrument": slug}) or []
        if path == "/api/versions":
            return psql_json(QUERIES["versions"]) or []
        if path == "/api/contexts":
            return psql_json(QUERIES["contexts"]) or []
        if path == "/api/sources":
            return psql_json(QUERIES["sources"]) or []
        if path == "/api/evidence/excerpts":
            query = parse_qs(query_string)
            source_slug = query.get("source_slug", [""])[0]
            return psql_json(QUERIES["source_excerpts"], {"source_slug": source_slug}) or []
        if path == "/api/review/candidates":
            query = parse_qs(query_string)
            status = query.get("status", ["pending"])[0]
            return list_candidates(status)
        if path == "/api/review/candidate":
            query = parse_qs(query_string)
            candidate_id = query.get("candidate_id", [""])[0]
            return get_candidate(candidate_id)
        if path == "/api/stats":
            return psql_json(QUERIES["stats"]) or {}
        if path == "/api/articles":
            query = parse_qs(query_string)
            version = query.get("version", ["cn_company_law_2023"])[0]
            return psql_json(QUERIES["articles"], {"version": version}) or []
        if path == "/api/article":
            query = parse_qs(query_string)
            version = query.get("version", ["cn_company_law_2023"])[0]
            article = parse_int(query.get("article", ["1"])[0], 1)
            return psql_json(QUERIES["article"], {"version": version, "article": str(article)}) or {}
        if path == "/api/compare":
            query = parse_qs(query_string)
            left = query.get("left", ["cn_company_law_2018"])[0]
            right = query.get("right", ["cn_company_law_2023"])[0]
            article = parse_int(query.get("article", ["47"])[0], 47)
            return psql_json(
                QUERIES["compare"],
                {"left_version": left, "right_version": right, "article": str(article)},
            ) or []
        if path == "/api/search":
            query = parse_qs(query_string).get("q", [""])[0].strip()
            return psql_json(QUERIES["search"], {"query": query}) if query else []
        raise ValueError("Unknown API path")

    def send_html(self, body: str) -> None:
        data = body.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def send_json(self, body: object) -> None:
        data = json.dumps(body, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, fmt: str, *args: object) -> None:
        print("%s - %s" % (self.address_string(), fmt % args))


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Legal corpus app: http://{HOST}:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
