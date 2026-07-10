from __future__ import annotations

from db_access import psql_exec, psql_json
from query_defs import QUERIES


def list_candidates(status: str = "pending") -> list[dict[str, object]]:
    return psql_json(QUERIES["candidate_list"], {"status": status}) or []


def get_candidate(candidate_id: str) -> dict[str, object]:
    return psql_json(QUERIES["candidate_detail"], {"candidate_id": candidate_id}) or {}


def accept_candidate(candidate_id: str) -> dict[str, object]:
    sql = """
        WITH chosen AS (
          SELECT *
          FROM relation_candidates
          WHERE id::text = %(candidate_id)s
            AND status IN ('pending', 'needs_edit', 'accepted')
          LIMIT 1
        ),
        inserted AS (
          INSERT INTO legal_relations (
            subject_type, subject_id, object_type, object_id, relation_type,
            claim_text, source_id, confidence, evidence_level, notes
          )
          SELECT
            subject_type, subject_id, object_type, object_id, relation_type,
            claim_text, proposed_source_id, confidence,
            CASE WHEN confidence >= 0.85 THEN 'official' ELSE 'professional' END,
            'accepted from relation_candidates'
          FROM chosen
          WHERE proposed_source_id IS NOT NULL
          ON CONFLICT (subject_type, subject_id, object_type, object_id, relation_type)
          DO UPDATE SET
            claim_text = EXCLUDED.claim_text,
            source_id = EXCLUDED.source_id,
            confidence = EXCLUDED.confidence,
            evidence_level = EXCLUDED.evidence_level,
            notes = EXCLUDED.notes
          RETURNING id
        )
        UPDATE relation_candidates rc
        SET
          status = 'accepted',
          reviewed_at = now(),
          accepted_relation_id = (SELECT id FROM inserted LIMIT 1),
          review_note = COALESCE(rc.review_note, '')
        WHERE rc.id::text = %(candidate_id)s
          AND EXISTS (SELECT 1 FROM inserted)
        ;
    """
    psql_exec(sql, {"candidate_id": candidate_id})
    return get_candidate(candidate_id)


def reject_candidate(candidate_id: str, review_note: str = "") -> dict[str, object]:
    sql = """
        UPDATE relation_candidates
        SET
          status = 'rejected',
          review_note = NULLIF(%(review_note)s, ''),
          reviewed_at = now()
        WHERE id::text = %(candidate_id)s;
    """
    psql_exec(sql, {"candidate_id": candidate_id, "review_note": review_note})
    return get_candidate(candidate_id)


def edit_candidate(
    candidate_id: str,
    relation_type: str,
    claim_text: str,
    confidence: str,
    review_note: str = "",
) -> dict[str, object]:
    sql = """
        UPDATE relation_candidates
        SET
          relation_type = %(relation_type)s,
          claim_text = %(claim_text)s,
          confidence = %(confidence)s::numeric(3,2),
          review_note = NULLIF(%(review_note)s, ''),
          status = 'needs_edit',
          reviewed_at = now()
        WHERE id::text = %(candidate_id)s;
    """
    psql_exec(
        sql,
        {
            "candidate_id": candidate_id,
            "relation_type": relation_type,
            "claim_text": claim_text,
            "confidence": confidence,
            "review_note": review_note,
        },
    )
    return get_candidate(candidate_id)
