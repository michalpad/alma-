"""
============================================================
 אלמה — מנוע פגישת ההיכרות (Placement)
============================================================
איך כל ילד מתחיל: לא "מבחן" אלא *פגישת היכרות* חמה ואדפטיבית
שמגלה את הרמה האמיתית שלו — בלי תלות בכיתה, בלי תיוג קבוע.

מבוסס מחקר (ALEKS, My Math Academy, Knowledge Tracing):
  1. הכיתה היא רק *ניחוש פתיחה*, לא גזר דין (נמנעים מ"מיינדסט קבוע").
  2. אדפטיבי בזמן אמת: ענה נכון -> קשה יותר; טעה -> קל יותר.
  3. קצר: 8-12 שאלות, מתכנס מהר לרמה.
  4. התוצאה: אילו נושאים כבר נשלטו + מאיפה להתחיל ללמד.
  5. ההערכה לא נגמרת כאן — ממשיכה תוך כדי תרגול (knowledge tracing).

הטון: חם, סקרן, לא מאיים. "בואו נכיר!" ולא "מבחן".
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


# ============================================================
#  רמות במסלול — סדר עולה של נושאים (נגזר מעצי הלמידה)
# ============================================================
# כל "רמה" מייצגת נקודה ברצף הלמידה. במערכת האמיתית זה נטען
# מעצי הלמידה במסד; כאן המבנה שמנוע ההיכרות עובד מולו.
@dataclass
class LevelProbe:
    """נקודת-בדיקה ברצף: נושא + הרמה היחסית שלו."""
    node_id: str
    title: str
    rank: int          # מיקום ברצף הקושי (0 = הכי בסיסי)


# ============================================================
#  תוצאת ההיכרות
# ============================================================
@dataclass
class PlacementResult:
    start_node_id: Optional[str] = None    # מאיפה להתחיל ללמד
    start_title: str = ""
    mastered_ranks: set = field(default_factory=set)  # ranks שהילד כבר שולט
    confidence: float = 0.0                # ביטחון ההערכה 0..1
    questions_asked: int = 0
    # הודעה חמה לילד על התוצאה
    say: str = ""


# ============================================================
#  מנוע ההיכרות האדפטיבי
# ============================================================
# כמה שאלות לכל היותר (לא מתישים ילד) ולכל הפחות (כדי להיות בטוחים)
MAX_PROBES = 12
MIN_PROBES = 6
# כמה תשובות עוקבות באותו כיוון מספיקות כדי "להתכנס"
CONVERGENCE_RUN = 3


@dataclass
class PlacementSession:
    """
    מנהל פגישת היכרות אדפטיבית. עובד על רצף LevelProbe ממוין לפי rank.
    הרעיון: חיפוש בינארי "רך" — מתחילים בניחוש הכיתה, וצועדים מעלה/מטה
    עד שמוצאים את הגבול בין "שולט" ל"עוד לא".
    """
    probes: list                       # רשימת LevelProbe ממוינת לפי rank
    grade_hint_rank: int = 0            # ניחוש פתיחה לפי הכיתה
    # מצב פנימי
    low: int = 0                       # גבול תחתון של החיפוש
    high: int = 0                      # גבול עליון
    current: int = 0                   # האינדקס הנבדק כעת
    mastered_ranks: set = field(default_factory=set)
    asked: int = 0
    _consec_correct: int = 0
    _consec_wrong: int = 0
    _started: bool = False

    def start(self) -> LevelProbe:
        """מתחילים בניחוש הכיתה (או באמצע אם אין ניחוש)."""
        self.low = 0
        self.high = len(self.probes) - 1
        # נקודת הפתיחה: הניחוש לפי כיתה, אך בתוך הטווח
        self.current = max(0, min(self.grade_hint_rank, self.high))
        self._started = True
        return self.probes[self.current]

    def answer(self, correct: bool) -> Optional[LevelProbe]:
        """
        מעבד תשובה ומחזיר את שאלת ההיכרות הבאה — או None אם סיימנו.
        אדפטיבי: נכון -> עולים; טעות -> יורדים. מתכנסים לגבול.
        """
        if not self._started:
            self.start()
        self.asked += 1

        if correct:
            # שולט בנקודה הזו — וכנראה גם בכל מה שמתחתיה
            for i in range(self.current + 1):
                self.mastered_ranks.add(self.probes[i].rank)
            self.low = self.current + 1
            self._consec_correct += 1
            self._consec_wrong = 0
        else:
            # עוד לא שם — הגבול העליון יורד
            self.high = self.current - 1
            self._consec_wrong += 1
            self._consec_correct = 0

        # תנאי עצירה
        if self._should_stop():
            return None

        # אם הטווח נסגר אך עוד לא הגענו למינימום שאלות -> שאלות אימות
        # סביב הגבול שמצאנו, כדי לוודא שהרמה יציבה ולא מקרית.
        if self.low > self.high:
            return self._verification_probe()

        # נקודת הבדיקה הבאה — אמצע הטווח שנותר (חיפוש בינארי רך)
        self.current = (self.low + self.high) // 2
        return self.probes[self.current]

    def _verification_probe(self) -> Optional[LevelProbe]:
        """
        אחרי שהתכנסנו אך לפני MIN_PROBES — שואלים שוב סביב הגבול
        (פעם מעל, פעם מתחת) כדי לאמת שההערכה יציבה ולא מקרית.
        """
        boundary = self.low  # הנושא הראשון שעדיין לא נשלט
        # מתחלפים: בודקים את הגבול עצמו ואת הסמוך לו
        if self.asked % 2 == 0 and boundary < len(self.probes):
            self.current = min(boundary, len(self.probes) - 1)
        else:
            self.current = max(0, min(boundary - 1, len(self.probes) - 1))
        return self.probes[self.current]

    def _should_stop(self) -> bool:
        if self.asked >= MAX_PROBES:
            return True
        if self.asked < MIN_PROBES:
            return False  # תמיד שואלים לפחות MIN — לאמינות
        # אחרי MIN: עוצרים כשהטווח סגור
        if self.low > self.high:
            return True
        return False

    def result(self) -> PlacementResult:
        """בונה את תוצאת ההיכרות — מאיפה להתחיל, ומה כבר נשלט."""
        # נקודת ההתחלה: הנושא הראשון שעדיין לא נשלט
        start_idx = 0
        for i, p in enumerate(self.probes):
            if p.rank not in self.mastered_ranks:
                start_idx = i
                break
        else:
            start_idx = len(self.probes) - 1  # שולט בהכל

        start = self.probes[start_idx]
        # ביטחון: ככל ששאלנו יותר וסגרנו טווח — בטוחים יותר
        span = len(self.probes)
        confidence = min(1.0, 0.4 + 0.6 * (self.asked / MAX_PROBES))

        n_mastered = len(self.mastered_ranks)
        if n_mastered == 0:
            say = "נעים להכיר! מצאתי בדיוק מאיפה כיף להתחיל. קדימה!"
        elif start_idx >= len(self.probes) - 1:
            say = "וואו, אתה כבר שולט בהמון! בוא נמשיך הלאה לדברים חדשים."
        else:
            say = f"מצאתי! אתה כבר יודע כמה דברים יפה. נתחיל מ'{start.title}' — בדיוק במקום הנכון."

        return PlacementResult(
            start_node_id=start.node_id,
            start_title=start.title,
            mastered_ranks=set(self.mastered_ranks),
            confidence=round(confidence, 2),
            questions_asked=self.asked,
            say=say,
        )


# ============================================================
#  ניחוש פתיחה לפי כיתה (רק נקודת התחלה, לא גזר דין)
# ============================================================
def grade_to_start_rank(grade: int, total_probes: int) -> int:
    """
    ממפה כיתה (1-6) לניחוש פתיחה ברצף. זה *רק* איפה מתחילים את
    ההיכרות — המנוע יתקן מעלה/מטה לפי הביצועים בפועל.
    """
    if grade <= 1:
        return 0
    # פריסה גסה: כל כיתה ~שישית מהרצף (כיתות א-ו)
    frac = (grade - 1) / 6.0
    return max(0, min(int(frac * total_probes), total_probes - 1))


def opening_message(age_band: str) -> str:
    """ההזמנה לפגישת ההיכרות — חמה, לא מאיימת. בלי 'מבחן'."""
    if age_band == "a_b":
        return "היי! בואו נכיר. אשאל אותך כמה דברים קצרים כדי לדעת מאיפה הכי כיף להתחיל."
    return "נעים להכיר! לפני שמתחילים, אשאל אותך כמה שאלות קצרות — ככה אדע בדיוק מאיפה להתחיל איתך. אין כאן נכון או לא נכון, רק היכרות."
