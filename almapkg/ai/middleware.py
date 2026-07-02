"""
ALMA — Safety Middleware.
משימה 4. שכבת הבטיחות הראשונה בשרשרת הבקשה. סדר ההרצה:

  1) בדיקת נעילה פעילה (אם נעול -> חסום, אל תעבד).
  2) סינון תוכן פוגעני -> חסימה + נעילת 3 דקות + הודעה.
  3) שמירת נושא -> אם הסחה, סמן redirect (ללא נעילה).

רק קלט שעבר הכל ממשיך ל-Pedagogy Orchestrator.
משתמש בפונקציות ה-repository ממשימה 1 (is_locked, trigger_safety_lock).
"""
from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from .content_filter import ContentFilter, BLOCK_MESSAGE
from .topic_guard import resolve_topic, TopicDecision


@dataclass
class GateResult:
    allow: bool                 # האם להעביר ל-Orchestrator
    student_message: str = ""   # הודעה להציג/להקריא לתלמיד (אם נחסם)
    redirect_to_lesson: bool = False
    redirect_hint: str = ""
    locked_until_iso: str = ""


async def safety_gate(
    *,
    conn,                       # asyncpg connection
    student_id: UUID,
    text: str,
    content_filter: ContentFilter,
    repo,                       # מודול repository ממשימה 1
    llm_call=None,
    moderator=None,             # CloudModerator אופציונלי (שכבת ענן)
    http_client=None,           # לקוח HTTP אסינכרוני לשירות הענן
) -> GateResult:
    # --- 1) נעילה פעילה? ---
    lock = await repo.is_locked(conn, student_id)
    if lock is not None:
        return GateResult(
            allow=False,
            student_message=BLOCK_MESSAGE,
            locked_until_iso=lock.isoformat(),
        )

    # --- 2) סינון תוכן פוגעני ---
    # אם הוגדר moderator -> שכבת regex + ענן; אחרת regex מקומי בלבד.
    if moderator is not None:
        fr = await moderator.check(text, http_client=http_client)
    else:
        fr = content_filter.check(text)
    if fr.blocked:
        lock_until = await repo.trigger_safety_lock(
            conn, student_id, event_type=fr.category, raw_flagged=fr.matched_span
        )
        return GateResult(
            allow=False,
            student_message=BLOCK_MESSAGE,
            locked_until_iso=lock_until.isoformat(),
        )

    # --- 3) שמירת נושא (ללא נעילה) ---
    topic: TopicDecision = await resolve_topic(text, llm_call=llm_call)
    if topic.redirect:
        return GateResult(
            allow=True,                 # ממשיכים, אך עם הוראת חזרה לחומר
            redirect_to_lesson=True,
            redirect_hint=topic.reply_hint,
        )
    if topic.state == "operational":
        return GateResult(allow=True, redirect_hint=topic.reply_hint)

    return GateResult(allow=True)
