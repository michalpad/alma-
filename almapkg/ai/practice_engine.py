"""
ALMA — מנוע התרגול.
אחרי ההקנייה, לכל נושא מיוצרת כמות תרגול מספקת בקושי עולה. מעבר לנושא
הבא רק כשהתלמיד שולט ב-90% מהשאלות. עיקרון מנחה: מקסימום גיוון בכל
פרמטר (סוג שאלה, הקשר, מספרים, עטיפת משחק) ובדיקת ידע אמיתית.

ארכיטקטורה (שילוב בטוח):
  • בנק תבניות מאומתות — נכונות מתמטית ומדורגות בקושי (הגרעין הבטוח).
  • וריאציה ע"י ה-LLM — מייצר אינסוף גרסאות מתבנית בטוחה (גיוון).
  • אימות תשובה דטרמיניסטי בשרת — לעולם לא סומכים על ה-LLM לציון נכונות.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Optional


# ============================================================
#  סוגי שאלות — פתוחות וסגורות, מגוון רחב
# ============================================================
class QType(str, Enum):
    MULTIPLE_CHOICE = "multiple_choice"   # סגורה: בחירה מ-2-4
    OPEN_NUMERIC = "open_numeric"         # פתוחה: הקלדת מספר
    OPEN_TEXT = "open_text"               # פתוחה: הקלדת מילה/ביטוי
    TRUE_FALSE = "true_false"             # סגורה: נכון/לא נכון
    MATCH_PAIRS = "match_pairs"           # התאמה בין זוגות
    ORDER_SEQUENCE = "order_sequence"     # סידור ברצף הנכון
    FILL_BLANK = "fill_blank"             # השלמת החסר בתרגיל
    DRAG_DROP = "drag_drop"               # גרירה (משחקי)
    TAP_COLLECT = "tap_collect"           # לחיצה/איסוף (משחקי)


# שיוך סוג שאלה -> האם "משחקי" (לעטיפה ויזואלית מהנה)
GAMELIKE = {QType.MATCH_PAIRS, QType.ORDER_SEQUENCE, QType.DRAG_DROP, QType.TAP_COLLECT}


# ============================================================
#  רמות קושי (קל -> בינוני -> אתגר)
# ============================================================
class Difficulty(int, Enum):
    EASY = 1
    MEDIUM = 2
    CHALLENGE = 3


# ============================================================
#  כמות תרגול מספקת + שער 90%
# ============================================================
PASS_THRESHOLD = 0.90               # שער מעבר לנושא הבא
MIN_QUESTIONS_PER_TOPIC = 10        # מינימום שאלות לנושא (כמות מספקת)
# פיזור הקושי: רוב קל/בינוני, אתגר בסוף
DIFFICULTY_MIX = {
    Difficulty.EASY: 0.40,
    Difficulty.MEDIUM: 0.40,
    Difficulty.CHALLENGE: 0.20,
}


@dataclass
class Question:
    """שאלה בודדה מוכנה להצגה."""
    qtype: QType
    difficulty: Difficulty
    prompt: str                       # ניסוח השאלה (מנוקד, לקול)
    answer: object                    # התשובה הנכונה (לאימות בשרת בלבד)
    options: list = field(default_factory=list)   # לשאלות סגורות
    payload: dict = field(default_factory=dict)    # נתוני משחק/התאמה/גרירה
    template_id: str = ""             # מאיזו תבנית נוצרה (למעקב)
    explain: str = ""                 # הסבר קצר (לאחר מענה)


@dataclass
class PracticeSession:
    """מצב סשן תרגול לנושא. נשמר ב-Redis."""
    node_id: str
    asked: int = 0
    correct: int = 0
    # תור השאלות (קושי עולה); נבנה מראש אך יכול להתרחב אם צריך תרגול נוסף
    queue: list = field(default_factory=list)
    history: list = field(default_factory=list)   # (template_id, difficulty, ok)

    @property
    def accuracy(self) -> float:
        return (self.correct / self.asked) if self.asked else 0.0

    @property
    def mastered(self) -> bool:
        # שולטים רק אחרי כמות מספקת ובדיוק 90%+
        return self.asked >= MIN_QUESTIONS_PER_TOPIC and self.accuracy >= PASS_THRESHOLD


# ============================================================
#  בנק תבניות — כל תבנית יודעת לייצר וריאציות מאומתות
#  (כאן ליבה גנרית; תבניות ספציפיות נטענות לפי נושא)
# ============================================================
@dataclass
class Template:
    """
    תבנית שאלה מאומתת. generate() מחזיר Question מוכנה עם תשובה נכונה
    מחושבת בשרת — כך הנכונות מובטחת ואינה תלויה ב-LLM.
    """
    template_id: str
    node_id: str
    difficulty: Difficulty
    supported_types: list            # אילו QType התבנית יכולה ללבוש
    generator: Callable              # (rng, qtype) -> Question

    def generate(self, rng: random.Random, qtype: Optional[QType] = None) -> Question:
        qt = qtype or rng.choice(self.supported_types)
        q = self.generator(rng, qt)
        q.template_id = self.template_id
        q.difficulty = self.difficulty
        return q


# ============================================================
#  אימות תשובה — דטרמיניסטי, בשרת. לעולם לא דרך ה-LLM.
# ============================================================
def check_answer(question: Question, student_answer) -> bool:
    """משווה את תשובת התלמיד לתשובה הנכונה, לפי סוג השאלה."""
    a = question.answer
    if question.qtype in (QType.OPEN_NUMERIC, QType.FILL_BLANK):
        try:
            return abs(float(student_answer) - float(a)) < 1e-9
        except (TypeError, ValueError):
            return False
    if question.qtype == QType.OPEN_TEXT:
        return _norm(student_answer) == _norm(a)
    if question.qtype == QType.TRUE_FALSE:
        return bool(student_answer) == bool(a)
    if question.qtype == QType.MULTIPLE_CHOICE:
        return student_answer == a
    if question.qtype in (QType.MATCH_PAIRS, QType.ORDER_SEQUENCE, QType.DRAG_DROP):
        return list(student_answer or []) == list(a or [])
    if question.qtype == QType.TAP_COLLECT:
        # אוסף נכון אם הקבוצה תואמת (סדר לא משנה)
        return sorted(student_answer or []) == sorted(a or [])
    return False


def _norm(s) -> str:
    """נרמול טקסט עברי להשוואה: רווחים, ניקוד, סופיות."""
    import re
    s = str(s).strip()
    s = re.sub(r"[\u0591-\u05C7]", "", s)        # הסרת ניקוד
    s = re.sub(r"\s+", " ", s)
    finals = {"ך": "כ", "ם": "מ", "ן": "נ", "ף": "פ", "ץ": "צ"}
    return "".join(finals.get(c, c) for c in s)


# ============================================================
#  בניית תור התרגול — כמות מספקת, קושי עולה, גיוון מקסימלי
# ============================================================
def build_practice_queue(templates: list, rng: random.Random,
                         n: int = MIN_QUESTIONS_PER_TOPIC) -> list:
    """
    בונה תור שאלות בקושי עולה עם גיוון מרבי:
    - פיזור קושי לפי DIFFICULTY_MIX
    - גיוון סוגי שאלות (לא אותו סוג פעמיים ברצף)
    - גיוון תבניות (לא ממצים תבנית אחת)
    """
    by_diff = {d: [t for t in templates if t.difficulty == d] for d in Difficulty}
    counts = {d: max(1, round(n * DIFFICULTY_MIX[d])) for d in Difficulty}

    queue, last_type = [], None
    # סדר עולה: קל -> בינוני -> אתגר
    for d in (Difficulty.EASY, Difficulty.MEDIUM, Difficulty.CHALLENGE):
        pool = by_diff.get(d) or []
        if not pool:
            continue
        for _ in range(counts[d]):
            tpl = rng.choice(pool)
            # בחר סוג שונה מהקודם לגיוון
            types = [qt for qt in tpl.supported_types if qt != last_type] or tpl.supported_types
            qt = rng.choice(types)
            q = tpl.generate(rng, qt)
            queue.append(q)
            last_type = qt
    return queue


# ============================================================
#  קידום הסשן אחרי מענה
# ============================================================
@dataclass
class PracticeStep:
    action: str           # 'next' | 'retry_same' | 'mastered' | 'more_practice'
    question: Optional[Question] = None
    accuracy: float = 0.0
    asked: int = 0


def on_practice_answer(session: PracticeSession, question: Question,
                       student_answer, *, used_hint: bool = False) -> PracticeStep:
    """
    מעדכן את הסשן אחרי מענה ומחזיר את הצעד הבא.
    - אם נעזר ברמז: שאלה נוספת מאותה רמת קושי (כלל מנוע הרמזים).
    - מעבר לנושא הבא רק כשמושג שער 90% אחרי כמות מספקת.
    """
    ok = check_answer(question, student_answer)
    session.asked += 1
    if ok:
        session.correct += 1
    session.history.append((question.template_id, int(question.difficulty), ok))

    # אם נעזר ברמז ופתר — שאלה חוזרת מאותה רמת קושי (לא מתקדמים)
    if used_hint and ok:
        return PracticeStep(action="retry_same", accuracy=session.accuracy, asked=session.asked)

    # נגמר התור?
    if not session.queue:
        if session.mastered:
            return PracticeStep(action="mastered", accuracy=session.accuracy, asked=session.asked)
        # עוד לא שולטים — צריך עוד תרגול
        return PracticeStep(action="more_practice", accuracy=session.accuracy, asked=session.asked)

    nxt = session.queue.pop(0)
    return PracticeStep(action="next", question=nxt, accuracy=session.accuracy, asked=session.asked)


# ============================================================
#  שכבת הווריאציה של הבינה (ליבת המערכת)
#  הבינה מנסחת מחדש שאלה מאומתת. הנכונות לעולם לא נפגעת:
#  רק שדה ה-prompt מוחלף; answer/options/payload נשמרים מהתבנית.
# ============================================================
async def vary_question(question: Question, llm_call, *,
                        grade: int, age_band: str, gender: str,
                        subject_he: str, interests: Optional[list] = None) -> Question:
    """
    מקבל שאלה מאומתת, ומחזיר אותה עם ניסוח טרי ומותאם אישית מהבינה.
    אם הבינה נכשלת או מחזירה פלט לא תקין — חוזרים לניסוח המקורי (fail-safe).
    הנכונות נשמרת תמיד: התשובה והאפשרויות לא משתנות.
    """
    import json
    from .prompts import build_practice_variation_prompt

    system = build_practice_variation_prompt(grade, age_band, gender, subject_he)
    payload_in = {
        "prompt": question.prompt,
        "qtype": question.qtype.value,
        "interests": interests or [],
    }
    try:
        raw = await llm_call(system, json.dumps(payload_in, ensure_ascii=False))
        cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        data = json.loads(cleaned)
        new_prompt = (data.get("prompt") or "").strip()
        # אימות בסיסי: ניסוח לא ריק ולא חושף את התשובה
        if new_prompt and not _leaks_answer(new_prompt, question.answer):
            # מחליפים *רק* את הניסוח. כל השאר נשאר מהתבנית המאומתת.
            question.prompt = new_prompt
    except Exception:
        pass  # fail-safe: נשארים עם הניסוח המקורי המאומת
    return question


def _leaks_answer(prompt: str, answer) -> bool:
    """שכבת הגנה: דוחה ניסוח שמכיל את התשובה המספרית במפורש."""
    if isinstance(answer, (int, float)):
        import re
        # אם המספר המדויק של התשובה מופיע כמילה נפרדת בניסוח — חשד לדליפה
        return bool(re.search(rf"(?<!\d){int(answer)}(?!\d)", prompt))
    return False
