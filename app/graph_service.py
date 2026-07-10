from __future__ import annotations

from db_access import psql_json
from query_defs import QUERIES


def get_node(node_key: str) -> dict[str, object]:
    return psql_json(QUERIES["graph_node"], {"node_key": node_key}) or {}


def get_neighbors(node_key: str) -> list[dict[str, object]]:
    return psql_json(QUERIES["graph_neighbors"], {"node_key": node_key}) or []


def get_path(from_node_key: str, to_node_key: str) -> dict[str, object]:
    return psql_json(
        QUERIES["graph_path"],
        {"from_node_key": from_node_key, "to_node_key": to_node_key},
    ) or {"nodes": [], "edges": []}
