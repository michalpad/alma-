"""
============================================================
 אלמה — שכבת אבטחה 1: רישום גישה (Audit Logging)
============================================================
דרישה מפורשת של COPPA/FERPA/GDPR: כל גישה למידע של תלמיד
חייבת להיות מתועדת — מי, מתי, לאיזה מידע, ואיזו פעולה.
זה מאפשר: (א) לזהות גישה חריגה, (ב) להוכיח עמידה בתקנות
באודיט, (ג) לחקור אירוע אבטחה.

עקרון: המידע שנרשם ב-audit הוא *מינימלי* — מזהי-טוקן, לא
תוכן אישי. הלוג עצמו לא אמור להיות מאגר PII נוסף.
"""
from __future__ import annotations

import datetime as _dt
import json
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional


class AuditAction(str, Enum):
    VIEW = "view"           # צפייה במידע תלמיד
    CREATE = "create"       # יצירת רשומה
    UPDATE = "update"       # עדכון
    DELETE = "delete"       # מחיקה
    EXPORT = "export"       # ייצוא מידע (רגיש במיוחד)
    LOGIN = "login"         # כניסה למערכת
    CONSENT = "consent"     # מתן/שינוי הסכמה


class ActorRole(str, Enum):
    PARENT = "parent"
    TEACHER = "teacher"
    SCHOOL_ADMIN = "school_admin"
    STUDENT = "student"
    SYSTEM = "system"


@dataclass
class AuditEvent:
    """
    רשומת audit אחת. שים לב: משתמשים ב*מזהים* (actor_id, subject_id)
    ולא בשמות/מיילים — הלוג לא נועד להיות מאגר מידע אישי.
    """
    timestamp: str
    action: AuditAction
    actor_role: ActorRole
    actor_id: str                 # מזהה-טוקן של מבצע הפעולה (לא שם)
    subject_id: Optional[str]     # מזהה-טוקן של התלמיד שאליו המידע שייך
    resource: str                 # מה נגע (למשל "progress", "profile")
    success: bool = True
    ip_hash: Optional[str] = None # hash של IP (לא IP גולמי — פרטיות)
    detail: Optional[str] = None  # תיאור קצר, בלי תוכן אישי

    def to_json(self) -> str:
        d = asdict(self)
        d["action"] = self.action.value
        d["actor_role"] = self.actor_role.value
        return json.dumps(d, ensure_ascii=False)


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat()


def _hash_ip(ip: Optional[str]) -> Optional[str]:
    """ממיר IP ל-hash חד-כיווני — מאפשר לזהות דפוסים בלי לשמור IP גולמי."""
    if not ip:
        return None
    import hashlib
    return hashlib.sha256(ip.encode("utf-8")).hexdigest()[:16]


class AuditLogger:
    """
    מתעד גישה למידע תלמידים. ה-sink (יעד הכתיבה) מוזרק — במערכת
    האמיתית זה כותב לטבלה ייעודית/שירות לוגים מאובטח (append-only),
    לא לקובץ מקומי. כאן ברירת מחדל: איסוף בזיכרון + hook לכתיבה.
    """
    def __init__(self, sink=None):
        # sink(event: AuditEvent) -> None ; אם None, שומר בזיכרון (לבדיקות)
        self._sink = sink
        self._buffer: list = []

    def log(self, action: AuditAction, actor_role: ActorRole, actor_id: str,
            resource: str, subject_id: Optional[str] = None,
            success: bool = True, ip: Optional[str] = None,
            detail: Optional[str] = None) -> AuditEvent:
        event = AuditEvent(
            timestamp=_now(), action=action, actor_role=actor_role,
            actor_id=actor_id, subject_id=subject_id, resource=resource,
            success=success, ip_hash=_hash_ip(ip), detail=detail,
        )
        if self._sink:
            self._sink(event)
        else:
            self._buffer.append(event)
        return event

    @property
    def events(self) -> list:
        return list(self._buffer)

    def events_for_subject(self, subject_id: str) -> list:
        """כל הגישות למידע של תלמיד מסוים — לשקיפות מול הורה/אודיט."""
        return [e for e in self._buffer if e.subject_id == subject_id]


# עוזר: לעטוף פעולה רגישה כך שתירשם אוטומטית
def audited(logger: AuditLogger, action: AuditAction, actor_role: ActorRole,
            actor_id: str, resource: str, subject_id: Optional[str] = None):
    """
    דקורטור לפעולות שנוגעות במידע תלמיד. רושם הצלחה/כשל אוטומטית.
    שימוש:
        @audited(logger, AuditAction.VIEW, role, uid, "progress", sid)
        def get_progress(...): ...
    """
    def wrap(fn):
        def inner(*args, **kwargs):
            try:
                result = fn(*args, **kwargs)
                logger.log(action, actor_role, actor_id, resource, subject_id, success=True)
                return result
            except Exception:
                logger.log(action, actor_role, actor_id, resource, subject_id, success=False)
                raise
        return inner
    return wrap
