"""
============================================================
 אלמה — שכבת אופטימיזציית עלויות (Cost Optimizer)
============================================================
ממקסמת את שולי הרווח בלי לפגוע באיכות. שלושה מנגנונים,
מבוססי-מחקר (חיסכון מצטבר של 60-80%):

  1. ניתוב מודלים (Model Routing) — כל משימה מקבלת את המודל
     הזול ביותר ש*עדיין נותן איכות מלאה* לאותה משימה. משימה
     כבדה (הוראה, חשיבה) -> מודל חזק; פשוטה (בדיקה, ניתוב) -> זול.

  2. רמזי caching (Cache Hints) — מסמן איזה חלק מהקריאה קבוע
     (הפרומפט) כדי שספק ה-API יזכה בהנחת caching (עד 90%).

  3. הגבלת אורך פלט (Output Budget) — פלט יקר פי 6 מקלט, אז לכל
     משימה תקרת פלט הגיונית. ממוקד = גם זול וגם פדגוגית טוב יותר.

עיקרון-על: חיסכון לעולם לא בא על חשבון איכות. משימה כבדה תמיד
מקבלת מודל חזק. אנחנו מונעים בזבוז, לא מקצצים באיכות.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


# ============================================================
#  שכבות המודל — מהחזק/יקר לזול/מהיר
# ============================================================
class ModelTier(str, Enum):
    HEAVY = "heavy"     # מודל חזק — הוראה, הסבר, חשיבה מסדר גבוה
    LIGHT = "light"     # מודל בינוני — רמזים, שיחה קצרה
    MICRO = "micro"     # מודל זול מאוד — בדיקות, ניתוב, סיווג


# מיפוי לשמות מודלים בפועל. ניתן להחליף ספק בקלות (Gemini/Claude)
# בלי לגעת בשאר הקוד — רק כאן.
MODEL_BY_TIER = {
    # ברירת מחדל: Gemini (המשתלם ביותר להתחלה)
    "gemini": {
        ModelTier.HEAVY: "gemini-3-pro",         # הוראה איכותית
        ModelTier.LIGHT: "gemini-3-flash",       # רמזים, שיחה
        ModelTier.MICRO: "gemini-3.1-flash-lite",# בדיקות פשוטות
    },
    "claude": {
        ModelTier.HEAVY: "claude-sonnet-4-6",
        ModelTier.LIGHT: "claude-haiku-4-5-20251001",
        ModelTier.MICRO: "claude-haiku-4-5-20251001",
    },
}


# ============================================================
#  1) ניתוב משימות למודל הנכון
# ============================================================
class TaskKind(str, Enum):
    TEACH = "teach"             # הקנייה — כבד (איכות קריטית)
    RETEACH = "reteach"         # הסבר חוזר — כבד
    HINT = "hint"               # רמז — בינוני
    CONVERSATION = "conversation"  # שיחה עם הילד — בינוני
    CHECK_ANSWER = "check"      # בדיקת תשובה — זעיר (לרוב לא צריך LLM בכלל)
    CLASSIFY = "classify"       # סיווג/ניתוב — זעיר
    SUMMARIZE = "summarize"     # סיכום קצר — זעיר


# איזו שכבת מודל לכל סוג משימה. הכלל: איכות ההוראה קדושה (HEAVY),
# והחיסכון בא מהמשימות הפשוטות שממילא לא צריכות מודל חזק.
_TASK_TIER = {
    TaskKind.TEACH: ModelTier.HEAVY,
    TaskKind.RETEACH: ModelTier.HEAVY,
    TaskKind.HINT: ModelTier.LIGHT,
    TaskKind.CONVERSATION: ModelTier.LIGHT,
    TaskKind.CHECK_ANSWER: ModelTier.MICRO,
    TaskKind.CLASSIFY: ModelTier.MICRO,
    TaskKind.SUMMARIZE: ModelTier.MICRO,
}


def route_model(task: TaskKind, provider: str = "gemini") -> str:
    """מחזיר את שם המודל הזול ביותר שנותן איכות מלאה למשימה."""
    tier = _TASK_TIER.get(task, ModelTier.HEAVY)  # ברירת מחדל בטוחה: חזק
    return MODEL_BY_TIER[provider][tier]


def tier_for(task: TaskKind) -> ModelTier:
    return _TASK_TIER.get(task, ModelTier.HEAVY)


# ============================================================
#  2) הגבלת אורך פלט לכל משימה (פלט יקר פי ~6 מקלט)
# ============================================================
# תקרות פלט הגיוניות (tokens). ממוקד = זול *וגם* פדגוגית טוב יותר —
# ילד לא צריך קיר טקסט. הערכים נדיבים מספיק לאיכות מלאה.
_OUTPUT_BUDGET = {
    TaskKind.TEACH: 700,        # הקנייה מלאה אך ממוקדת
    TaskKind.RETEACH: 700,
    TaskKind.HINT: 120,         # רמז קצר במכוון
    TaskKind.CONVERSATION: 200,
    TaskKind.CHECK_ANSWER: 30,
    TaskKind.CLASSIFY: 20,
    TaskKind.SUMMARIZE: 200,
}


def output_budget(task: TaskKind) -> int:
    """תקרת אורך פלט למשימה — חוסך בפלט היקר בלי לפגוע באיכות."""
    return _OUTPUT_BUDGET.get(task, 700)


# ============================================================
#  3) רמזי caching — סימון החלק הקבוע לזכייה בהנחה
# ============================================================
@dataclass
class CallPlan:
    """
    תוכנית קריאה מלאה ומאופטמת ל-LLM. אוגדת את כל ההחלטות:
    איזה מודל, כמה פלט, ומה קבוע (cacheable) לחיסכון.
    """
    model: str
    tier: ModelTier
    max_output_tokens: int
    cache_system_prompt: bool     # לסמן את הפרומפט כקבוע -> הנחת caching
    task: TaskKind


def plan_call(task: TaskKind, provider: str = "gemini",
              system_prompt_is_stable: bool = True) -> CallPlan:
    """
    בונה תוכנית קריאה מאופטמת: המודל הזול-מספיק, תקרת פלט,
    וסימון caching. זו נקודת הכניסה שהאורקסטרטור משתמש בה.
    """
    return CallPlan(
        model=route_model(task, provider),
        tier=tier_for(task),
        max_output_tokens=output_budget(task),
        # caching משתלם רק כשהפרומפט קבוע וחוזר (הקנייה/רמז — כן)
        cache_system_prompt=system_prompt_is_stable and task in (
            TaskKind.TEACH, TaskKind.RETEACH, TaskKind.HINT, TaskKind.CONVERSATION
        ),
        task=task,
    )


# ============================================================
#  אומדן חיסכون — כלי שקיפות לניהול
# ============================================================
# מחירים יחסיים (ליחידה) לפי שכבה — לצורך הערכת חיסכון בלבד.
_REL_PRICE = {ModelTier.HEAVY: 1.0, ModelTier.LIGHT: 0.17, ModelTier.MICRO: 0.05}


def estimate_savings(task_mix: dict) -> dict:
    """
    מקבל תמהיל משימות {TaskKind: count} ומחזיר כמה חוסך הניתוב
    לעומת שימוש במודל חזק לכל המשימות. כלי שקיפות למנהל.
    """
    naive = 0.0    # הכול על מודל חזק
    routed = 0.0   # עם ניתוב
    for task, count in task_mix.items():
        naive += count * _REL_PRICE[ModelTier.HEAVY]
        routed += count * _REL_PRICE[tier_for(task)]
    saving_pct = (1 - routed / naive) * 100 if naive else 0
    return {
        "naive_cost_units": round(naive, 2),
        "routed_cost_units": round(routed, 2),
        "saving_percent": round(saving_pct, 1),
    }
