#!/usr/bin/env python3
from __future__ import annotations

import json
import mimetypes
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from db_access import parse_int, psql_json
from agent_service import extract_relation_candidates
from graph_service import get_neighbors, get_node, get_path
from llm_support import ask_deepseek
from query_defs import QUERIES
from workspace_service import (
    compare_view,
    domain_view,
    graph_view,
    home_view,
    instrument_reader_view,
    instrument_view,
    reader_view,
    review_accept,
    review_edit,
    review_reject,
    review_view,
    search_view,
    topic_view,
)


HOST = os.environ.get("LEGAL_CORPUS_HOST", "127.0.0.1")
PORT = int(os.environ.get("LEGAL_CORPUS_PORT", "8000"))
STATIC_DIR = (Path(__file__).parent / "static").resolve()


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        try:
            if parsed.path.startswith("/api/"):
                self.send_json(self.api_response(parsed.path, parsed.query))
            elif not self.serve_static(parsed.path):
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
            if parsed.path == "/api/agent/extract-relations":
                self.send_json(extract_relation_candidates(str(payload.get("canonical_ref", "")).strip()))
                return
            if parsed.path == "/api/workspace/review/candidate/accept":
                self.send_json(
                    review_accept(
                        str(payload.get("candidate_id", "")).strip(),
                        str(payload.get("status", "")).strip(),
                    )
                )
                return
            if parsed.path == "/api/workspace/review/candidate/reject":
                self.send_json(
                    review_reject(
                        str(payload.get("candidate_id", "")).strip(),
                        str(payload.get("review_note", "")).strip(),
                        str(payload.get("status", "")).strip(),
                    )
                )
                return
            if parsed.path == "/api/workspace/review/candidate/edit":
                self.send_json(
                    review_edit(
                        str(payload.get("candidate_id", "")).strip(),
                        str(payload.get("relation_type", "")).strip(),
                        str(payload.get("claim_text", "")).strip(),
                        str(payload.get("confidence", "")).strip() or "0.50",
                        str(payload.get("review_note", "")).strip(),
                        str(payload.get("status", "")).strip(),
                    )
                )
                return
            self.send_error(404, "Not found")
        except Exception as exc:
            self.send_error(500, str(exc))

    def api_response(self, path: str, query_string: str) -> object:
        if path.startswith("/api/workspace/"):
            return self.workspace_response(path, query_string)
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
        if path == "/api/stats":
            return psql_json(QUERIES["stats"]) or {}
        if path == "/api/search":
            query = parse_qs(query_string).get("q", [""])[0].strip()
            return psql_json(QUERIES["search"], {"query": query}) if query else []
        raise ValueError("Unknown API path")

    def workspace_response(self, path: str, query_string: str) -> object:
        if path == "/api/workspace/graph":
            query = parse_qs(query_string)
            node_key = query.get("node_key", ["legal_instrument:cn_company_law"])[0]
            to_node_key = query.get("to_node_key", [""])[0]
            return graph_view(node_key, to_node_key)
        if path == "/api/workspace/review":
            query = parse_qs(query_string)
            status = query.get("status", ["pending"])[0]
            candidate_id = query.get("candidate_id", [""])[0]
            return review_view(status, candidate_id)
        if path == "/api/workspace/reader":
            query = parse_qs(query_string)
            version = query.get("version", ["cn_company_law_2023"])[0]
            article = parse_int(query.get("article", ["1"])[0], 1)
            return reader_view(version, article)
        if path == "/api/workspace/instrument-reader":
            query = parse_qs(query_string)
            slug = query.get("slug", ["cn_civil_code"])[0]
            unit = parse_int(query.get("unit", ["1"])[0], 1)
            return instrument_reader_view(slug, unit)
        if path == "/api/workspace/compare":
            query = parse_qs(query_string)
            left = query.get("left", ["cn_company_law_2018"])[0]
            right = query.get("right", ["cn_company_law_2023"])[0]
            article = parse_int(query.get("article", ["47"])[0], 47)
            return compare_view(left, right, article)
        if path == "/api/workspace/home":
            return home_view()
        if path == "/api/workspace/search":
            query = parse_qs(query_string).get("q", [""])[0].strip()
            return search_view(query)
        if path == "/api/workspace/instrument":
            query = parse_qs(query_string)
            slug = query.get("slug", ["cn_company_law"])[0]
            return instrument_view(slug)
        if path == "/api/workspace/domain":
            query = parse_qs(query_string)
            slug = query.get("slug", ["commercial-organization"])[0]
            return domain_view(slug)
        if path == "/api/workspace/topic":
            query = parse_qs(query_string)
            slug = query.get("slug", ["capital-credit"])[0]
            return topic_view(slug)
        raise ValueError("Unknown workspace API path")

    def serve_static(self, path: str) -> bool:
        if not STATIC_DIR.is_dir():
            return False
        relative = path.lstrip("/") or "index.html"
        candidate = (STATIC_DIR / relative).resolve()
        if STATIC_DIR not in candidate.parents and candidate != STATIC_DIR:
            return False
        if not candidate.is_file():
            candidate = STATIC_DIR / "index.html"
            if not candidate.is_file():
                return False
        content_type, _ = mimetypes.guess_type(str(candidate))
        data = candidate.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type or "application/octet-stream")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)
        return True

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
