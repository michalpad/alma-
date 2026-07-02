"""
============================================================
 אלמה — שכבת אבטחה 2: הצפנת שדות ומדיניות שמירה
============================================================
שני מנגנונים משלימים:

  1. הצפנת שדות רגישים (field-level encryption) — מעל להצפנת
     המסד של Supabase, שדות רגישים במיוחד מוצפנים גם ברמת
     היישום, כך שגם מי שיש לו גישה למסד לא רואה אותם בגלוי.

  2. מדיניות שמירה ומחיקה — COPPA/GDPR אוסרים שמירה אינסופית.
     כל סוג מידע מקבל חלון שמירה, ואחריו נמחק/מפוסאודנם.
     כולל "זכות למחיקה" (GDPR erasure / COPPA parental deletion).

הערה: המפתח להצפנה נטען ממשתנה סביבה (ALMA_FIELD_KEY) — לעולם
לא מהקוד. אם המפתח חסר, ההצפנה נכשלת בבירור (fail-closed).
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import os
import datetime as _dt
from dataclasses import dataclass
from enum import Enum
from typing import Optional


# ============================================================
#  1) הצפנת שדות רגישים
# ============================================================
# הערה: זו הצפנה סימטרית קלה מבוססת ספריית התקן (hashlib/hmac)
# ל-XOR-stream עם נגזרת מפתח. בפרודקשן מומלץ להחליף ב-AES-GCM
# (cryptography.fernet) — הממשק כאן זהה כדי שההחלפה תהיה קלה.
_KEY_ENV = "ALMA_FIELD_KEY"


def _get_key() -> bytes:
    """טוען את מפתח ההצפנה מהסביבה. נכשל בבירור אם חסר (fail-closed)."""
    k = os.environ.get(_KEY_ENV)
    if not k:
        raise RuntimeError(
            f"מפתח ההצפנה ({_KEY_ENV}) לא מוגדר בסביבה. "
            "אין להצפין/לפענח בלי מפתח. הגדר משתנה סביבה מאובטח."
        )
    return hashlib.sha256(k.encode("utf-8")).digest()


def _keystream(key: bytes, nonce: bytes, length: int) -> bytes:
    """יוצר זרם מפתח דטרמיניסטי מהמפתח וה-nonce (HMAC-CTR)."""
    out = bytearray()
    counter = 0
    while len(out) < length:
        block = hmac.new(key, nonce + counter.to_bytes(8, "big"), hashlib.sha256).digest()
        out.extend(block)
        counter += 1
    return bytes(out[:length])


def encrypt_field(plaintext: str) -> str:
    """מצפין ערך רגיש. מחזיר מחרוזת base64 (nonce+cipher+tag)."""
    if plaintext is None:
        return None
    key = _get_key()
    nonce = os.urandom(12)
    data = plaintext.encode("utf-8")
    cipher = bytes(a ^ b for a, b in zip(data, _keystream(key, nonce, len(data))))
    tag = hmac.new(key, nonce + cipher, hashlib.sha256).digest()[:16]  # אימות שלמות
    return base64.b64encode(nonce + cipher + tag).decode("ascii")


def decrypt_field(token: str) -> str:
    """מפענח ערך. מאמת שלמות (tag) — אם שונה, זורק שגיאה."""
    if token is None:
        return None
    key = _get_key()
    raw = base64.b64decode(token.encode("ascii"))
    nonce, cipher, tag = raw[:12], raw[12:-16], raw[-16:]
    expected = hmac.new(key, nonce + cipher, hashlib.sha256).digest()[:16]
    if not hmac.compare_digest(tag, expected):
        raise ValueError("אימות שלמות נכשל — הנתון שונה או פגום.")
    data = bytes(a ^ b for a, b in zip(cipher, _keystream(key, nonce, len(cipher))))
    return data.decode("utf-8")


def pseudonymize(value: str, salt: str = "alma") -> str:
    """
    הופך מזהה אישי למזהה-טוקן יציב (חד-כיווני). משמש כשצריך לשמור
    רשומה לצרכים חינוכיים אך בלי המזהה האישי הגלוי (GDPR pseudonymization).
    """
    return hashlib.sha256((salt + ":" + value).encode("utf-8")).hexdigest()[:24]


# ============================================================
#  2) מדיניות שמירה ומחיקה
# ============================================================
class DataCategory(str, Enum):
    PROGRESS = "progress"         # התקדמות לימודית
    PRACTICE_LOG = "practice_log" # תשובות/ניסיונות
    VOICE = "voice"               # הקלטות קול (רגיש מאוד)
    ANALYTICS = "analytics"       # נתוני שימוש מצרפיים
    ACCOUNT = "account"           # פרטי חשבון בסיסיים


# חלונות שמירה (בימים) לכל סוג מידע. אחרי החלון — מחיקה/פסאודונום.
# מבוסס עקרון: לשמור רק כמה שנחוץ למטרה החינוכית.
RETENTION_DAYS = {
    DataCategory.VOICE: 7,          # קול נמחק מהר — הרגיש ביותר
    DataCategory.PRACTICE_LOG: 365, # שנת לימודים
    DataCategory.PROGRESS: 365 * 2, # שנתיים (המשכיות לימודית)
    DataCategory.ANALYTICS: 90,     # מצרפי, קצר
    DataCategory.ACCOUNT: None,     # כל עוד המנוי פעיל (נמחק בסגירת חשבון)
}


@dataclass
class RetentionItem:
    category: DataCategory
    created_on: str               # ISO date

    def expires_on(self) -> Optional[str]:
        days = RETENTION_DAYS.get(self.category)
        if days is None:
            return None            # ללא תפוגה אוטומטית (נמחק בסגירת חשבון)
        base = _dt.date.fromisoformat(self.created_on)
        return (base + _dt.timedelta(days=days)).isoformat()

    def is_expired(self, today: Optional[str] = None) -> bool:
        exp = self.expires_on()
        if exp is None:
            return False
        today = today or _dt.date.today().isoformat()
        return today >= exp


def items_to_purge(items: list, today: Optional[str] = None) -> list:
    """מחזיר את הפריטים שהגיע זמנם להימחק (עבר חלון השמירה)."""
    return [it for it in items if it.is_expired(today)]


# ============================================================
#  זכות למחיקה (GDPR erasure / COPPA parental deletion)
# ============================================================
@dataclass
class ErasureRequest:
    """
    בקשת מחיקה מהורה/בית ספר. מודל מחיקה דו-שכבתי (לפי המחקר):
      - מידע צרכני לא-חובה: מחיקה מלאה ומיידית.
      - רשומות שחובה לשמור: פסאודונום חזק (לא מחיקה מלאה).
    """
    subject_id: str
    requested_on: str
    requested_by_role: str        # parent / school_admin
    full_delete_categories: list  # מה נמחק לגמרי
    pseudonymize_categories: list # מה עובר פסאודונום (חובה חוקית לשמור)
    completed: bool = False

    def plan(self) -> dict:
        return {
            "subject": self.subject_id,
            "delete": [c.value if isinstance(c, DataCategory) else c for c in self.full_delete_categories],
            "pseudonymize": [c.value if isinstance(c, DataCategory) else c for c in self.pseudonymize_categories],
        }
