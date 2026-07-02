"""
ALMA — שכבת גישה לנתונים (Repository).
משימה 1: שאילתות הליבה — ניהול state, דרישות קדם, לוגיקת מעבר 90%, נעילת בטיחות.

משתמש ב-asyncpg (PostgreSQL). כל פונקציה מקבלת חיבור/pool.
ההמרה ל-pgvector של תחביבים נעשית בשכבת ה-AI ומוזנת כאן כרשימת float.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

import asyncpg

PASS_THRESHOLD = 90.0          # אחוז הצלחה נדרש למעבר שלב
SAFETY_LOCK_MINUTES = 3        # נעילת בטיחות


# ============================================================
#  פרופיל תלמיד
# ============================================================

async def get_student(conn: asyncpg.Connection, student_id: UUID) -> Optional[asyncpg.Record]:
    return await conn.fetchrow(
        "SELECT * FROM students WHERE student_id = $1", student_id
    )


async def get_subject_progress(
    conn: asyncpg.Connection, student_id: UUID, subject: str
) -> Optional[asyncpg.Record]:
    return await conn.fetchrow(
        """SELECT * FROM subject_progress
           WHERE student_id = $1 AND subject = $2""",
        student_id, subject,
    )


# ============================================================
#  עץ למידה ודרישות קדם
# ============================================================

async def get_prerequisites(
    conn: asyncpg.Connection, node_id: UUID
) -> list[asyncpg.Record]:
    """כל צמתי הקדם הישירים של נושא."""
    return await conn.fetch(
        """SELECT n.*
           FROM node_prerequisites p
           JOIN learning_nodes n ON n.node_id = p.prerequisite_id
           WHERE p.node_id = $1""",
        node_id,
    )


async def unmet_prerequisites(
    conn: asyncpg.Connection, student_id: UUID, node_id: UUID
) -> list[asyncpg.Record]:
    """
    צמתי קדם שהתלמיד עדיין לא שולט בהם (status != 'mastered').
    אם הרשימה ריקה — מותר להתחיל את הנושא.
    אחרת — המערכת משלימה קודם את הידע החסר.
    """
    return await conn.fetch(
        """SELECT n.*
           FROM node_prerequisites p
           JOIN learning_nodes n ON n.node_id = p.prerequisite_id
           LEFT JOIN student_node_status s
             ON s.node_id = p.prerequisite_id AND s.student_id = $1
           WHERE p.node_id = $2
             AND (s.status IS NULL OR s.status <> 'mastered')""",
        student_id, node_id,
    )


async def next_node_in_sequence(
    conn: asyncpg.Connection, student_id: UUID, subject: str
) -> Optional[asyncpg.Record]:
    """
    הצומת הבא בסדר תכנית הלימודים שהתלמיד עדיין לא שלט בו.
    הסדר נקבע ע"י sequence_order — ללא קשר לכיתה שהתלמיד רשום בה.
    """
    return await conn.fetchrow(
        """SELECT n.*
           FROM learning_nodes n
           LEFT JOIN student_node_status s
             ON s.node_id = n.node_id AND s.student_id = $1
           WHERE n.subject = $2
             AND (s.status IS NULL OR s.status <> 'mastered')
           ORDER BY n.sequence_order
           LIMIT 1""",
        student_id, subject,
    )


# ============================================================
#  לוג למידה + לוגיקת מעבר 90%
# ============================================================

async def log_attempt(conn: asyncpg.Connection, entry: dict) -> None:
    await conn.execute(
        """INSERT INTO learning_log
           (student_id, node_id, subject, question_text, question_type,
            student_answer, is_correct, hints_used, response_mode, time_taken_ms)
           VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)""",
        entry["student_id"], entry["node_id"], entry["subject"],
        entry.get("question_text"), entry.get("question_type"),
        entry.get("student_answer"), entry.get("is_correct"),
        entry.get("hints_used", 0), entry.get("response_mode"),
        entry.get("time_taken_ms"),
    )


async def current_success_rate(
    conn: asyncpg.Connection, student_id: UUID, node_id: UUID,
    window: int = 20
) -> float:
    """אחוז הצלחה על חלון ה-N הניסיונות האחרונים בצומת."""
    row = await conn.fetchrow(
        """SELECT ROUND(100.0 * AVG((is_correct)::int), 2) AS pct
           FROM (
             SELECT is_correct FROM learning_log
             WHERE student_id = $1 AND node_id = $2
             ORDER BY created_at DESC LIMIT $3
           ) recent""",
        student_id, node_id, window,
    )
    return float(row["pct"]) if row and row["pct"] is not None else 0.0


async def try_advance_node(
    conn: asyncpg.Connection, student_id: UUID, node_id: UUID
) -> bool:
    """
    בודק אם התלמיד עבר את סף 90% בצומת ומסמן 'mastered' אם כן.
    מחזיר True אם הצומת הושלם.
    """
    rate = await current_success_rate(conn, student_id, node_id)
    if rate >= PASS_THRESHOLD:
        await conn.execute(
            """INSERT INTO student_node_status
                 (student_id, node_id, status, success_rate, mastered_at)
               VALUES ($1, $2, 'mastered', $3, now())
               ON CONFLICT (student_id, node_id)
               DO UPDATE SET status='mastered',
                             success_rate=$3,
                             mastered_at=now()""",
            student_id, node_id, rate,
        )
        return True
    # עדכון אחוז ביניים מבלי לפתוח שלב
    await conn.execute(
        """INSERT INTO student_node_status
             (student_id, node_id, status, success_rate, started_at)
           VALUES ($1, $2, 'in_progress', $3, now())
           ON CONFLICT (student_id, node_id)
           DO UPDATE SET success_rate=$3,
                         status = CASE WHEN student_node_status.status='locked'
                                       THEN 'in_progress'
                                       ELSE student_node_status.status END""",
        student_id, node_id, rate,
    )
    return False


# ============================================================
#  בטיחות — נעילת 3 דקות persistent
# ============================================================

async def is_locked(
    conn: asyncpg.Connection, student_id: UUID
) -> Optional[datetime]:
    """מחזיר את חותמת סיום הנעילה אם התלמיד נעול כעת, אחרת None."""
    row = await conn.fetchrow(
        """SELECT lock_until FROM safety_events
           WHERE student_id = $1 AND lock_until > now()
           ORDER BY lock_until DESC LIMIT 1""",
        student_id,
    )
    return row["lock_until"] if row else None


async def trigger_safety_lock(
    conn: asyncpg.Connection, student_id: UUID,
    event_type: str, raw_flagged: str
) -> datetime:
    """רושם אירוע בטיחות ומפעיל נעילת 3 דקות. מחזיר את חותמת סיום הנעילה."""
    lock_until = datetime.now(timezone.utc) + timedelta(minutes=SAFETY_LOCK_MINUTES)
    await conn.execute(
        """INSERT INTO safety_events
             (student_id, event_type, raw_flagged, lock_until)
           VALUES ($1, $2, $3, $4)""",
        student_id, event_type, raw_flagged, lock_until,
    )
    return lock_until


# ============================================================
#  אחזור סמנטי — תחביבים רלוונטיים להקשר הנוכחי (pgvector)
# ============================================================

async def relevant_interests(
    conn: asyncpg.Connection, student_id: UUID,
    query_embedding: list[float], k: int = 3
) -> list[str]:
    rows = await conn.fetch(
        """SELECT note
           FROM student_interests
           WHERE student_id = $1
           ORDER BY embedding <=> $2
           LIMIT $3""",
        student_id, query_embedding, k,
    )
    return [r["note"] for r in rows]
