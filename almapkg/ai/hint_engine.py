"""
ALMA — מכונת מצבים לרמזים מדורגים.
משימה 2. הדירוג דטרמיניסטי (בשרת), ה-LLM רק מנסח את הרמז ברמה הנתונה.

חוקים מהאפיון:
- ארבע רמות רמז קבועות (1→4), כל טעות מעלה רמה.
- כשתלמיד נעזר ברמז כדי לפתור — חובה שאלה נוספת מאותה רמת קושי בדיוק,
  ורק לאחר מענה נכון עליה ממשיכים הלאה.
"""
from __future__ import annotations

from dataclasses import dataclass, field

MAX_HINT_LEVEL = 4


@dataclass
class HintState:
    """State לכל שאלה פעילה. נשמר ב-Redis למשך הסשן."""
    node_id: str
    current_level: int = 0          # 0 = טרם ניתן רמז
    hints_used_this_q: int = 0
    # דגל: התלמיד נעזר ברמז -> חייב שאלה חוזרת מאותה רמה לפני התקדמות
    must_repeat_same_level: bool = False
    repeat_difficulty: int = 0      # רמת הקושי שיש לחזור עליה


@dataclass
class HintDecision:
    """תוצאת ההחלטה — מה השרת עושה אחרי ניסיון של תלמיד."""
    action: str                     # 'give_hint' | 'next_same_level' | 'advance' | 'celebrate'
    hint_level: int = 0
    message_key: str = ""
    state: HintState = field(default=None)  # type: ignore


def on_answer(state: HintState, is_correct: bool) -> HintDecision:
    """
    נקרא אחרי כל ניסיון מענה. מחזיר את הצעד הבא.

    זרימה:
    - תשובה שגויה -> העלאת רמת רמז (עד 4) והפעלת רמז.
    - תשובה נכונה אחרי שימוש ברמז -> חובה שאלה נוספת מאותה רמה (must_repeat).
    - תשובה נכונה ללא רמז, או הצלחה בשאלה החוזרת -> התקדמות.
    """
    # --- מענה נכון ---
    if is_correct:
        if state.must_repeat_same_level:
            # סיים בהצלחה את השאלה החוזרת -> אפשר להתקדם
            state.must_repeat_same_level = False
            state.current_level = 0
            state.hints_used_this_q = 0
            return HintDecision(action="advance", state=state)

        if state.hints_used_this_q > 0:
            # נעזר ברמז כדי לפתור -> חובה שאלה נוספת מאותה רמה
            state.must_repeat_same_level = True
            state.repeat_difficulty = max(state.repeat_difficulty, 1)
            level_just_used = state.current_level
            state.current_level = 0
            state.hints_used_this_q = 0
            return HintDecision(
                action="next_same_level",
                hint_level=level_just_used,
                message_key="repeat_same_level",
                state=state,
            )

        # פתר/ה לבד ללא רמז -> התקדמות
        state.current_level = 0
        return HintDecision(action="advance", state=state)

    # --- מענה שגוי -> מדרגים רמז כלפי מעלה ---
    next_level = min(state.current_level + 1, MAX_HINT_LEVEL)
    state.current_level = next_level
    state.hints_used_this_q += 1
    return HintDecision(
        action="give_hint",
        hint_level=next_level,
        message_key="hint",
        state=state,
    )


def reset_for_new_question(state: HintState, keep_repeat: bool = False) -> HintState:
    """איפוס בין שאלות. אם must_repeat דלוק — שומרים אותו עד שהתלמיד יצליח."""
    state.current_level = 0
    state.hints_used_this_q = 0
    if not keep_repeat:
        state.must_repeat_same_level = False
        state.repeat_difficulty = 0
    return state
