"""
ALMA — Pedagogy Orchestrator.
משימה 2. מחבר את החלקים: מרכיב הקשר -> קורא ל-LLM להקניה/רמז ->
מנתב דרך מכונת הרמזים -> מחזיר פלט מובנה (speech + board) לצד הלקוח.

קריאת ה-LLM היא דרך Anthropic API. כאן מובאת המעטפת הפדגוגית;
המפתח מנוהל בסביבת השרת ולא נכתב בקוד.
"""
from __future__ import annotations

import json

from .prompts import build_teaching_system_prompt, build_hint_system_prompt
from .hint_engine import HintState, on_answer

SUBJECT_HE = {"hebrew": "שפה (עברית)", "math": "מתמטיקה", "english": "אנגלית"}


def _parse_llm_json(raw: str) -> dict:
    """ה-LLM אמור להחזיר JSON נקי. מנקים backticks ליתר ביטחון."""
    cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    return json.loads(cleaned)


async def attach_audio(payload: dict, tts_engine, http_client=None) -> dict:
    """
    מקבל פלט הקנייה (steps[]) ומוסיף לכל שלב אודיו מנוקד מ-TTS.
    כל step יקבל שדה 'audio' (bytes) או 'browser_fallback' (טקסט).
    כך הלוח החי מנגן את הקול בסנכרון עם השרטוט, באיכות גבוהה.
    """
    for step in payload.get("steps", []) or []:
        say = step.get("say", "") if isinstance(step, dict) else ""
        if not say:
            continue
        result = await tts_engine.synthesize(say, http_client=http_client)
        if result.audio:
            step["audio_mime"] = result.mime
            step["audio"] = result.audio          # bytes — יקודד base64 בשכבת ה-API
            step["tts_provider"] = result.provider
        else:
            step["browser_fallback"] = result.browser_fallback_text
            step["tts_provider"] = "browser"
    return payload


async def generate_teaching(llm_call, *, grade: int, age_band: str,
                            gender: str, subject: str, topic_title: str,
                            interests: list[str], difficulties: list[str],
                            attempt: int = 0, previous_approaches: list = None) -> dict:
    """
    מייצר הקניה לנושא. llm_call היא פונקציה אסינכרונית שמקבלת
    (system, user) ומחזירה את הטקסט הגולמי מה-LLM.

    attempt: מספר הניסיון (0=ראשון). בכל ניסיון חוזר נבחרת גישת הוראה
    *שונה* מהקודמות, כדי שהילד יקבל הסבר אחר לגמרי.
    previous_approaches: הגישות שכבר נוסו (כדי לא לחזור עליהן).
    """
    from .prompts import choose_approach

    prev = previous_approaches or []
    approach = choose_approach(attempt, prev)
    is_reteach = attempt > 0

    system = build_teaching_system_prompt(
        grade, age_band, gender, SUBJECT_HE[subject],
        approach=approach, is_reteach=is_reteach)
    context_lines = [f"נושא ההקניה: {topic_title}"]
    if interests:
        context_lines.append("תחביבים של הילד/ה (שלב/י בדוגמאות אם מתאים): "
                             + ", ".join(interests))
    if difficulties:
        context_lines.append("קשיים ידועים (התייחס/י בעדינות): "
                             + ", ".join(difficulties))
    user = "\n".join(context_lines)

    raw = await llm_call(system, user)
    payload = _parse_llm_json(raw)
    _assert_no_answer_leak(payload)   # שכבת הגנה: ודא שאין דליפת תשובה גלויה

    # שכבת איכות: אם ההקנייה 'יבשה' מדי (רק עובדות), מבקשים פעם אחת
    # לשכתב עם יותר חשיבה מסדר גבוה — כדי שכל הקנייה תהיה ברמה הזו.
    if needs_deeper_thinking(payload):
        deeper_user = user + (
            "\n\nהערה חשובה: ההסבר הקודם היה יבש מדי. שכתב/י אותו כך שיכלול "
            "יותר חשיבה מסדר גבוה — חשיבה בקול רם, הסבר 'למה', קישור רעיונות, "
            "ודוגמה מהחיים. הדגם/י *איך חושבים*, לא רק את העובדה."
        )
        raw2 = await llm_call(system, deeper_user)
        payload2 = _parse_llm_json(raw2)
        _assert_no_answer_leak(payload2)
        # שומרים את הגרסה העמוקה יותר (גם אם עדיין לא מושלמת, היא טובה יותר)
        if assess_higher_order(payload2) >= assess_higher_order(payload):
            payload = payload2

    payload["approach"] = approach    # מחזירים איזו גישה שימשה (למעקב)
    payload["higher_order_score"] = round(assess_higher_order(payload), 2)
    return payload


async def reteach(llm_call, *, grade: int, age_band: str, gender: str,
                  subject: str, topic_title: str, interests: list[str],
                  difficulties: list[str], previous_approaches: list) -> dict:
    """
    הסבר חוזר כשהילד לא הבין — בדרך שונה מכל הקודמות.
    קיצור נוח: קורא ל-generate_teaching עם attempt לפי כמה כבר נוסו.
    """
    return await generate_teaching(
        llm_call, grade=grade, age_band=age_band, gender=gender,
        subject=subject, topic_title=topic_title, interests=interests,
        difficulties=difficulties,
        attempt=len(previous_approaches) or 1,
        previous_approaches=previous_approaches)


async def generate_hint(llm_call, state: HintState, *, gender: str,
                        subject: str, question_text: str,
                        student_answer: str) -> dict:
    """
    מנתב טעות דרך מכונת המצבים ומייצר את הרמז ברמה שנקבעה בשרת.
    מחזיר dict עם speech + hint_level, או סימון להמשך אם אין צורך ברמז.
    """
    decision = on_answer(state, is_correct=False)   # הגענו לכאן כי הייתה טעות
    level = decision.hint_level
    system = build_hint_system_prompt(level, gender, SUBJECT_HE[subject])
    user = (f"השאלה: {question_text}\n"
            f"תשובת התלמיד/ה (שגויה): {student_answer}\n"
            f"נסח/י רמז ברמה {level} בלבד. אל תחשוף/י את התשובה.")
    raw = await llm_call(system, user)
    payload = _parse_llm_json(raw)
    payload["hint_level"] = level
    return payload


def _assert_no_answer_leak(payload: dict) -> None:
    """
    בדיקה בסיסית: דגלים מילוליים שמרמזים על חשיפת תשובה ישירה.
    אינה מחליפה בדיקת תוכן מלאה — שכבת הגנה נוספת בלבד.
    תומכת גם בפלט הקנייה (steps[].say) וגם בפלט רמז (speech).
    """
    segments = []
    if isinstance(payload.get("speech"), str):
        segments.append(payload["speech"])
    for step in payload.get("steps", []) or []:
        if isinstance(step, dict) and isinstance(step.get("say"), str):
            segments.append(step["say"])

    red_flags = ["התשובה היא", "התשובה הנכונה היא", "הפתרון הוא"]
    for text in segments:
        if any(flag in text for flag in red_flags):
            raise ValueError("LLM output appears to reveal the answer — rejected.")


# מילות-סימן לחשיבה מסדר גבוה — אם הקנייה כוללת אותן, היא "חושבת",
# לא רק מונה עובדות. רשימה מכוונת-ריקול (לזיהוי, לא לאכיפת ניסוח).
_HIGHER_ORDER_MARKERS = [
    "למה", "מדוע", "כי ", "הסיבה", "בגלל",          # הסבר ה"למה"
    "נחשוב", "תחשבו", "בואו נ", "שימו לב",            # חשיבה בקול רם
    "זוכרים", "כמו ש", "בעצם", "כלומר", "זה אומר",   # קישור רעיונות
    "תארו לעצמכם", "דמיינו", "למשל", "לדוגמה",        # יישום מהחיים
]


def assess_higher_order(payload: dict) -> float:
    """
    מעריך עד כמה ההקנייה מדגימה חשיבה מסדר גבוה (0..1), לפי נוכחות
    סימני חשיבה לאורך השלבים. ציון נמוך => ההקנייה 'יבשה' מדי.
    זו הערכה היוריסטית (לא מושלמת) — שכבת איכות, לא שיפוט מוחלט.
    """
    steps = payload.get("steps", []) or []
    if not steps:
        return 0.0
    steps_with_thinking = 0
    for step in steps:
        say = step.get("say", "") if isinstance(step, dict) else ""
        if any(marker in say for marker in _HIGHER_ORDER_MARKERS):
            steps_with_thinking += 1
    return steps_with_thinking / len(steps)


# סף מינימלי: לפחות חלק זה מהשלבים צריכים להדגים חשיבה (לא רק עובדות)
HIGHER_ORDER_MIN = 0.4


def needs_deeper_thinking(payload: dict) -> bool:
    """האם ההקנייה 'יבשה' מדי ודורשת רענון עם יותר חשיבה מסדר גבוה."""
    return assess_higher_order(payload) < HIGHER_ORDER_MIN
