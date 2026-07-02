"""
ALMA — סינון תוכן פוגעני.
משימה 4. זיהוי דטרמיניסטי של שפה פוגענית (אלימות, גזענות, מיניות, קללות)
שמפעיל הודעת חסימה ונעילת 3 דקות.

עקרון: הלוגיקה כאן גנרית. דפוסי המילים עצמם מנוהלים ברשימה חיצונית
(blocklist) שמתוחזקת בנפרד ע"י צוות הבטיחות וניתנת לעדכון בלי שינוי קוד.
כך נמנעת הטמעת תוכן פוגעני בקוד עצמו, והרשימה נשמרת מצומצמת וממוקדת.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

BLOCK_MESSAGE = "המערכת אינה מאפשרת התנהלות בשפה פוגענית או לא נאותה"

# קטגוריות לסיווג האירוע (לתיעוד בלבד; כולן מובילות לחסימה).
CATEGORIES = ("profanity", "violence", "racism", "sexual")


@dataclass
class FilterResult:
    blocked: bool
    category: str = ""
    matched_span: str = ""   # לתיעוד פנימי / ביקורת, לא מוצג לתלמיד


def _normalize(text: str) -> str:
    """
    נרמול להקשחת הסינון מול עקיפות נפוצות:
    - הסרת ניקוד וסימני טעמים
    - איחוד רווחים
    - הסרת תווים מפרידים בתוך מילים (l3tt3r-spacing, נקודות/קווים)
    """
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.lower()
    # הסרת מפרידים שמשמשים להסוואה: . - _ * רווחים כפולים
    text = re.sub(r"[\.\-_\*]+", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


class ContentFilter:
    """
    מקבל רשימת דפוסים מקובצת לפי קטגוריה. כל דפוס הוא regex.
    הרשימה מוזרקת מבחוץ (dependency injection) — לא מוטמעת כאן.
    """

    def __init__(self, patterns_by_category: dict[str, list[str]]):
        self._compiled: dict[str, list[re.Pattern]] = {}
        for cat, pats in patterns_by_category.items():
            self._compiled[cat] = [re.compile(p) for p in pats]

    def check(self, text: str) -> FilterResult:
        norm = _normalize(text)
        for cat, patterns in self._compiled.items():
            for pat in patterns:
                m = pat.search(norm)
                if m:
                    return FilterResult(blocked=True, category=cat,
                                        matched_span=m.group(0))
        return FilterResult(blocked=False)


# ---- מפעל ברירת מחדל ----
# בפרודקשן: הרשימה נטענת מקובץ מאובטח / שירות ניהול רשימות.
# כאן מוגדרת מעטפת ריקה כך שאין תוכן פוגעני בקוד; הצוות מזין את הדפוסים.
def load_filter(patterns_source: dict[str, list[str]] | None = None) -> ContentFilter:
    return ContentFilter(patterns_source or {c: [] for c in CATEGORIES})
