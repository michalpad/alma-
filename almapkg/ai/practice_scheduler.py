"""
============================================================
 אלמה — מתזמן התרגול (Practice Scheduler)
============================================================
ארבעה שדרוגים מבוססי-מחקר שהופכים תרגול "שמרגיש טוב" לתרגול
שבונה שליטה עמוקה ועמידה בזמן:

  1. כמות אדפטיבית — 8-18 שאלות לפי ביצועי הילד (לא 10 קבוע).
     (מחקר: תלמיד רגיל צריך 8-18 חזרות; מחונן 1-4.)
  2. קריטריון שליטה חכם — 90% הכולל שאלות מסדר גבוה, לא רצף מכני.
     (מחקר: תרגול מרוכז יוצר "אשליית שליטה".)
  3. ערבוב (Interleaving) — שזירת נושאים שנלמדו, לתרגול *בחירת*
     אסטרטגיה. (מחקר: מכפיל ציוני מבחן; הילד לא מנחש אסטרטגיה מראש.)
  4. חזרה מרווחת (Spacing) — החזרת נושאים במרווחים גדלים.
     (מחקר: 60-70% זכירה טובה יותר בחודש; 80-90% בחצי שנה.)

המודול עצמאי ונקי; מנוע התרגול קורא לו.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import datetime as _dt


# ============================================================
#  1) כמות אדפטיבית — 8-18 לפי ביצועים
# ============================================================
MIN_Q = 8           # מינימום מוחלט (גם לתופס מהר)
MAX_Q = 18          # מקסימום (לפני שמסמנים "צריך עוד עזרה")
START_Q = 10        # נקודת פתיחה — נעה לפי ביצועים


@dataclass
class AdaptiveQuantity:
    """
    קובע כמה שאלות צריך, דינמית. תופס מהר -> פחות; מתקשה -> יותר.
    ההיגיון: כל תשובה נכונה ברצף מקרבת ליעד; טעות מרחיקה אותו מעט.
    """
    target: int = START_Q
    answered: int = 0
    correct: int = 0
    _streak: int = 0

    def record(self, correct: bool) -> None:
        self.answered += 1
        if correct:
            self.correct += 1
            self._streak += 1
            # רצף יפה -> אפשר לקצר (תופס מהר), אך לא מתחת למינימום
            if self._streak >= 4 and self.target > MIN_Q:
                self.target -= 1
        else:
            self._streak = 0
            # מתקשה -> צריך עוד תרגול, אך לא מעל המקסימום
            if self.target < MAX_Q:
                self.target += 1

    @property
    def done(self) -> bool:
        return self.answered >= self.target

    @property
    def needs_more_help(self) -> bool:
        """הגענו למקסימום ועדיין לא שולטים — אות לרדת רמה/לחזור להקנייה."""
        return self.answered >= MAX_Q and self.accuracy < 0.9

    @property
    def accuracy(self) -> float:
        return (self.correct / self.answered) if self.answered else 0.0


# ============================================================
#  2) קריטריון שליטה חכם — 90% *כולל* מסדר גבוה
# ============================================================
PASS_THRESHOLD = 0.90
# חובה: לפחות כך מהשאלות הנכונות חייבות להיות מסדר גבוה (הבנה/יישום),
# אחרת "שליטה" משקפת שינון מכני בלבד.
MIN_HIGHER_ORDER_CORRECT = 0.40


@dataclass
class MasteryCriterion:
    """
    שולט בנושא רק אם: (א) דיוק כללי >= 90%, וגם
    (ב) הוכיח הצלחה בשאלות מסדר גבוה (לא רק מכני).
    זה מונע "אשליית שליטה".
    """
    total: int = 0
    correct: int = 0
    higher_order_seen: int = 0
    higher_order_correct: int = 0

    def record(self, correct: bool, is_higher_order: bool) -> None:
        self.total += 1
        if correct:
            self.correct += 1
        if is_higher_order:
            self.higher_order_seen += 1
            if correct:
                self.higher_order_correct += 1

    @property
    def accuracy(self) -> float:
        return (self.correct / self.total) if self.total else 0.0

    @property
    def higher_order_accuracy(self) -> float:
        return (self.higher_order_correct / self.higher_order_seen) if self.higher_order_seen else 0.0

    @property
    def is_mastered(self) -> bool:
        # חייב גם דיוק כללי גבוה, וגם הוכחת הבנה (לא רק מכני)
        if self.accuracy < PASS_THRESHOLD:
            return False
        if self.higher_order_seen == 0:
            return False  # לא נבחנה הבנה -> עוד לא שליטה מלאה
        return self.higher_order_accuracy >= MIN_HIGHER_ORDER_CORRECT


# ============================================================
#  3) סבב מעורב (Mixed Round) — פעילות נפרדת, לא הפרעה באמצע
# ------------------------------------------------------------
#  עיקרון (לפי תובנת המשתמשת): לימוד נושא חדש תמיד נקי ורצוף —
#  בלי הפרעות. הערבוב קורה ב*סבב נפרד וממוסגר*, כל כמה סשנים:
#  "עכשיו חוזרים על כל מה שלמדנו — הכל יחד!". זה אתגר, לא בלבול.
#  ככל שהתלמיד לומד יותר נושאים, הסבב מתעשר (יותר נושאים בערבוב).
# ============================================================

# כל כמה סשני-נושא רגילים מגיע סבב מעורב אחד
MIXED_ROUND_EVERY = 3
# מינימום נושאים שנשלטו כדי שסבב מעורב יהיה בעל ערך
MIXED_ROUND_MIN_TOPICS = 2
# כמה שאלות בסבב מעורב (קצת יותר — זה אתגר סיכום)
MIXED_ROUND_QUESTIONS = 12


def is_mixed_round_due(sessions_since_last_mixed: int, mastered_count: int) -> bool:
    """האם הגיע הזמן לסבב מעורב — לפי קצב הסשנים ומספיק נושאים."""
    if mastered_count < MIXED_ROUND_MIN_TOPICS:
        return False
    return sessions_since_last_mixed >= MIXED_ROUND_EVERY


def mixed_round_opening(mastered_count: int, age_band: str) -> str:
    """ההנחיה הקצרה והמאתגרת שפותחת סבב מעורב — ישר לעניין."""
    if age_band == "a_b":
        return "אתגר הפתעה! עכשיו נתרגל את כל מה שלמדנו, הכל יחד. מוכן?"
    return (f"אתגר הסיכום! עד עכשיו למדת {mastered_count} נושאים — "
            f"עכשיו נערבב הכל יחד ונראה כמה אתה זוכר. קדימה!")


def build_mixed_round(mastered_topics: list, n_questions: int = MIXED_ROUND_QUESTIONS) -> list:
    """
    בונה סבב מעורב: שאלות מכל הנושאים שנשלטו, מעורבבות כך ששתי
    שאלות סמוכות לרוב מנושאים שונים (זה הלב — בחירת אסטרטגיה).
    הסבב כולו 'מעורב' מההתחלה — הילד יודע שזה אתגר ערבוב.
    ככל שיש יותר נושאים שנשלטו, הסבב מגוון יותר (מתעשר עם הקצב).
    """
    if not mastered_topics:
        return []
    # מחלקים את השאלות בין הנושאים שנשלטו (round-robin הוגן)
    plan = []
    for i in range(n_questions):
        plan.append(mastered_topics[i % len(mastered_topics)])
    # ערבוב כך ששתי שאלות סמוכות לא מאותו נושא (כשאפשר)
    return _spread_no_adjacent(plan)


def _spread_no_adjacent(plan: list) -> list:
    """מסדר רשימה כך ששני פריטים סמוכים לרוב שונים (מונע בלוקים)."""
    from collections import Counter
    counts = Counter(plan)
    result = []
    # בכל צעד בוחרים את הנושא הנפוץ ביותר שאינו האחרון שנבחר
    last = None
    for _ in range(len(plan)):
        # מועמדים ממוינים לפי כמה נשארו, למעט האחרון שנבחר
        candidates = sorted(counts.items(), key=lambda kv: -kv[1])
        picked = None
        for topic, c in candidates:
            if c > 0 and topic != last:
                picked = topic
                break
        if picked is None:  # נשאר רק הנושא האחרון — אין ברירה
            picked = next(t for t, c in counts.items() if c > 0)
        result.append(picked)
        counts[picked] -= 1
        last = picked
    return result


# ============================================================
#  4) חזרה מרווחת (Spacing) — להחזיר נושאים שנלמדו
# ============================================================
# מרווחים (בימים) שאחריהם נושא שנשלט חוזר לרענון קצר.
# מרווחים גדלים: ככל שהנושא יותר מבוסס, חוזרים אליו בתדירות נמוכה יותר.
SPACING_INTERVALS_DAYS = [1, 3, 7, 16, 35]


@dataclass
class SpacedItem:
    """נושא שנשלט וממתין לרענון מרווח."""
    topic: str
    mastered_on: str                  # תארי03 ISO שבו נשלט
    review_stage: int = 0             # באיזה מרווח אנחנו (אינדקס)
    last_review: Optional[str] = None

    def due_on(self) -> str:
        """התאריך הבא לרענון, לפי המרווח הנוכחי."""
        base = self.last_review or self.mastered_on
        base_date = _dt.date.fromisoformat(base)
        stage = min(self.review_stage, len(SPACING_INTERVALS_DAYS) - 1)
        gap = SPACING_INTERVALS_DAYS[stage]
        return (base_date + _dt.timedelta(days=gap)).isoformat()

    def is_due(self, today: Optional[str] = None) -> bool:
        today = today or _dt.date.today().isoformat()
        return today >= self.due_on()

    def record_review(self, today: Optional[str] = None) -> None:
        """אחרי רענון מוצלח — מתקדמים למרווח הבא (ארוך יותר)."""
        self.last_review = today or _dt.date.today().isoformat()
        if self.review_stage < len(SPACING_INTERVALS_DAYS) - 1:
            self.review_stage += 1


def topics_due_for_review(spaced_items: list, today: Optional[str] = None) -> list:
    """מחזיר את הנושאים שהגיע זמנם לרענון מרווח."""
    today = today or _dt.date.today().isoformat()
    return [it.topic for it in spaced_items if it.is_due(today)]


# ============================================================
#  מאחד הכול — תכנון סשן תרגול מלא
# ============================================================
@dataclass
class PracticePlan:
    """תוכנית סשן תרגול. סשן רגיל = נושא נקי ורצוף."""
    current_topic: str
    target_questions: int
    topic_per_question: list          # מאיזה נושא כל שאלה
    cognitive_per_question: list      # רמת חשיבה לכל שאלה
    is_mixed_round: bool = False      # האם זהו סבב מעורב (אתגר סיכום)
    opening_line: str = ""            # הנחיית פתיחה (לסבב מעורב)


def plan_regular_session(current_topic: str, age_band: str,
                         cognitive_queue_fn) -> PracticePlan:
    """
    סשן נושא רגיל — *נקי ורצוף*. כל השאלות מהנושא הנוכחי בלבד,
    בלי הפרעות (לפי תובנת המשתמשת: לימוד נושא חדש לא נקטע).
    הערבוב קורה בסבב נפרד (plan_mixed_round), לא כאן.
    """
    target = START_Q
    cognitive = cognitive_queue_fn(age_band, target)
    return PracticePlan(
        current_topic=current_topic,
        target_questions=target,
        topic_per_question=[current_topic] * target,   # נקי — נושא אחד
        cognitive_per_question=cognitive,
        is_mixed_round=False,
    )


def plan_mixed_round(mastered_topics: list, age_band: str,
                     cognitive_queue_fn) -> PracticePlan:
    """
    סבב מעורב — פעילות נפרדת וממוסגרת. מתחיל ישר בתרגול עם הנחיה
    מאתגרת, ומערבב את כל הנושאים שנשלטו. מתעשר ככל שיש יותר נושאים.
    """
    n = MIXED_ROUND_QUESTIONS
    topics = build_mixed_round(mastered_topics, n)
    cognitive = cognitive_queue_fn(age_band, len(topics))
    return PracticePlan(
        current_topic="(סבב מעורב)",
        target_questions=len(topics),
        topic_per_question=topics,
        cognitive_per_question=cognitive,
        is_mixed_round=True,
        opening_line=mixed_round_opening(len(mastered_topics), age_band),
    )
