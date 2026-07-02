"""
============================================================
 אלמה — רמות חשיבה (Cognitive Levels)
============================================================
מבוסס על הטקסונומיה של בלום, מותאם לילדי יסודי בשלוש רמות.
העיקרון (הוראת המוצר): ידע ≠ הבנה. ילד שיודע 7×8=56 בעל-פה
אינו בהכרח מבין כפל. המערכת בודחת *מורכבות*, לא רק שליטה מכנית.

שלוש הרמות (מהבסיס לעומק):
  1. שליטה (Remember)   — יודע את העובדה. "כמה זה 7×8?"
  2. הבנה (Understand)  — מסביר ומקשר. "אם 7×8=56, כמה 8×7? למה?"
  3. יישום (Apply)      — משתמש בידע במצב חדש. בעיה מילולית/אמיתית.

ציר זה *עצמאי* מרמת הקושי (Difficulty): שאלת-שליטה יכולה להיות
קשה, ושאלת-יישום יכולה להיות קלה. שני צירים שונים.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class CognitiveLevel(str, Enum):
    MASTERY = "mastery"            # שליטה — לזכור/לשלוף עובדה
    UNDERSTANDING = "understand"  # הבנה — להסביר, לקשר, "למה"
    APPLICATION = "apply"         # יישום — להשתמש במצב חדש/מילולי


# תיאור לכל רמה — לשימוש בתצוגה ובבניית פרומפטים
LEVEL_INFO = {
    CognitiveLevel.MASTERY: {
        "he": "שליטה",
        "desc": "יודע/ת את העובדה",
        "bloom": "לזכור",
        "example": "כמה זה 7 × 8?",
    },
    CognitiveLevel.UNDERSTANDING: {
        "he": "הבנה",
        "desc": "מסביר/ה ומקשר/ת",
        "bloom": "להבין",
        "example": "אם 7 × 8 = 56, כמה זה 8 × 7? ולמה?",
    },
    CognitiveLevel.APPLICATION: {
        "he": "יישום",
        "desc": "משתמש/ת בידע במצב חדש",
        "bloom": "ליישם",
        "example": "בכיתה 7 שולחנות, בכל אחד 8 ילדים. כמה ילדים בכיתה?",
    },
}


# ============================================================
#  תמהיל הרמות — כמה מכל רמה בנושא (לא רק שליטה מכנית!)
# ============================================================
# העיקרון: בסיס של שליטה, אבל *חובה* גם הבנה ויישום.
# התמהיל מותאם לגיל: לקטנים יותר שליטה, לגדולים יותר יישום.
LEVEL_MIX = {
    "a_b": {CognitiveLevel.MASTERY: 0.55, CognitiveLevel.UNDERSTANDING: 0.30, CognitiveLevel.APPLICATION: 0.15},
    "c_d": {CognitiveLevel.MASTERY: 0.45, CognitiveLevel.UNDERSTANDING: 0.30, CognitiveLevel.APPLICATION: 0.25},
    "e_f": {CognitiveLevel.MASTERY: 0.35, CognitiveLevel.UNDERSTANDING: 0.30, CognitiveLevel.APPLICATION: 0.35},
}

# מינימום שאלות מסדר-גבוה (הבנה+יישום) שחייבות להופיע בכל נושא,
# כדי ש"שליטה בנושא" תשקף הבנה אמיתית ולא רק שינון.
MIN_HIGHER_ORDER_FRACTION = 0.40


def mix_for_age(age_band: str) -> dict:
    return LEVEL_MIX.get(age_band, LEVEL_MIX["c_d"])


def build_level_queue(age_band: str, n_questions: int) -> list:
    """
    בונה רצף רמות-חשיבה ל-n שאלות בנושא, לפי התמהיל לגיל.
    מבטיח: (א) לפחות שאלה אחת מכל רמה, (ב) מינימום שאלות מסדר גבוה.
    מחזיר רשימת CognitiveLevel באורך n_questions.
    """
    mix = mix_for_age(age_band)
    counts = {lvl: max(1, round(frac * n_questions)) for lvl, frac in mix.items()}

    # התאמה ראשונית לאורך המבוקש (העיגול עלול לסטות)
    counts = _normalize_counts(counts, n_questions)

    # אכיפת מינימום מסדר-גבוה (הבנה + יישום) — על המספרים בפועל
    need_higher = max(2, round(MIN_HIGHER_ORDER_FRACTION * n_questions))
    higher = counts[CognitiveLevel.UNDERSTANDING] + counts[CognitiveLevel.APPLICATION]
    while higher < need_higher and counts[CognitiveLevel.MASTERY] > 1:
        # מעבירים שאלה משליטה ליישום, עד שמגיעים למינימום
        counts[CognitiveLevel.MASTERY] -= 1
        counts[CognitiveLevel.APPLICATION] += 1
        higher = counts[CognitiveLevel.UNDERSTANDING] + counts[CognitiveLevel.APPLICATION]

    # בניית הרצף לפי הספירות
    queue: list = []
    for lvl, c in counts.items():
        queue.extend([lvl] * c)

    # סדר פדגוגי
    return _interleave(queue)


def _normalize_counts(counts: dict, target: int) -> dict:
    """מתאים את סך הספירות ל-target בדיוק, תוך שמירת לפחות 1 מכל רמה."""
    total = sum(counts.values())
    levels = list(counts.keys())
    # אם יש עודף — מורידים מהגדול ביותר (לא מתחת ל-1)
    while total > target:
        biggest = max(levels, key=lambda l: counts[l])
        if counts[biggest] <= 1:
            break
        counts[biggest] -= 1
        total -= 1
    # אם חסר — מוסיפים לשליטה (הבסיס)
    while total < target:
        counts[CognitiveLevel.MASTERY] += 1
        total += 1
    return counts


def _interleave(queue: list) -> list:
    """
    מסדר כך שמתחילים בשליטה (ביטחון), ואז משלבים הבנה ויישום
    בהדרגה — לא כל שאלות העומק בסוף (מתיש) ולא בהתחלה (מרתיע).
    """
    mastery = [q for q in queue if q == CognitiveLevel.MASTERY]
    understand = [q for q in queue if q == CognitiveLevel.UNDERSTANDING]
    apply = [q for q in queue if q == CognitiveLevel.APPLICATION]

    result = []
    # מתחילים בשתי שאלות שליטה לחימום (אם יש)
    for _ in range(min(2, len(mastery))):
        result.append(mastery.pop(0))
    # ואז שוזרים את כולן לסירוגין
    pools = [mastery, understand, apply]
    while any(pools):
        for p in pools:
            if p:
                result.append(p.pop(0))
    return result


# ============================================================
#  בניית שאלת-עומק עם LLM — הנחיה לכל רמה
# ============================================================
def cognitive_prompt_guidance(level: CognitiveLevel) -> str:
    """הנחיה ל-LLM כיצד לנסח שאלה ברמת החשיבה המבוקשת."""
    if level == CognitiveLevel.MASTERY:
        return "שאלת שליטה: בקש/י את העובדה ישירות (לדוגמה: 'כמה זה 7×8?'). קצרה וברורה."
    if level == CognitiveLevel.UNDERSTANDING:
        return ("שאלת הבנה: בקש/י מהילד להסביר, לקשר, או לענות 'למה'. "
                "לדוגמה: 'אם 7×8=56, כמה זה 8×7? איך אתה יודע?' עורר/י חשיבה, לא שינון.")
    return ("שאלת יישום: נסח/י בעיה מילולית או מצב אמיתי שדורש להשתמש בידע. "
            "לדוגמה: 'בכיתה 7 שולחנות, בכל אחד 8 ילדים — כמה ילדים בכיתה?' "
            "ממשי וקרוב לעולם של הילד.")
