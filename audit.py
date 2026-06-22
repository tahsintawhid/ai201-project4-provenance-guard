from db import get_connection
from datetime import datetime, timezone


def write_log_entry(
    content_id: str,
    creator_id: str,
    content_preview: str,
    llm_score: float,
    stylometric_score: float | None,
    combined_score: float,
    attribution_result: str,
    confidence_label: str,
    transparency_label: str,
    status: str = "reviewed"
):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO audit_log (
            content_id, submitted_at, content_preview,
            llm_score, stylometric_score, combined_score,
            attribution_result, confidence_label, transparency_label, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        content_id,
        datetime.now(timezone.utc).isoformat(),
        content_preview,
        llm_score,
        stylometric_score,
        combined_score,
        attribution_result,
        confidence_label,
        transparency_label,
        status
    ))
    conn.commit()
    conn.close()


def get_log(limit: int = 50) -> list:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            al.id,
            al.content_id,
            al.submitted_at,
            al.content_preview,
            al.llm_score,
            al.stylometric_score,
            al.combined_score,
            al.attribution_result,
            al.confidence_label,
            al.transparency_label,
            al.status,
            a.creator_reasoning,
            a.appealed_at
        FROM audit_log al
        LEFT JOIN appeals a ON al.content_id = a.content_id
        ORDER BY al.submitted_at DESC
        LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def update_status(content_id: str, new_status: str) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE audit_log SET status = ? WHERE content_id = ?
    """, (new_status, content_id))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0


def write_appeal(content_id: str, creator_reasoning: str) -> bool:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id FROM appeals WHERE content_id = ? AND status = 'under_review'
    """, (content_id,))
    existing = cursor.fetchone()
    if existing:
        conn.close()
        return False

    cursor.execute("""
        INSERT INTO appeals (content_id, appealed_at, creator_reasoning, status)
        VALUES (?, ?, ?, 'under_review')
    """, (
        content_id,
        datetime.now(timezone.utc).isoformat(),
        creator_reasoning
    ))
    conn.commit()
    conn.close()
    return True
