"""
============================================================
 אלמה — מנוע המסע (משחקיות מבוססת-מחקר)
============================================================
"מסע אלמה": הילד מתקדם דרך עולם לימודי — כל נושא הוא תחנה,
כל מיומנות שנשלטת פותחת את הדרך הלאה.

עקרונות מנחים (ממחקר משחוק לילדים):
  1. מוטיבציה פנימית, לא פרסים מנותקים — הכיף מההתקדמות והמסוגלוּת.
     (נמנעים מ"אפקט הצדקת-היתר" ששוחק עניין; Lepper et al.)
  2. התקדמות נראית לעין — הילד *רואה* את עצמו גדל (מפה, תחנות).
  3. רצף אישי (streak) מול עצמו — לא תחרות מול אחרים
     (תחרות עלולה לדכא מוטיבציה פנימית בגיל צעיר).
  4. "נצחונות קטנים" — אבני דרך שמזוהות וחוגגות מסוגלוּת.
  5. טון התפתחותי ומעודד — לעולם לא ענישה או השוואה שלילית.

המודול עצמאי ונקי; מנוע התרגול/המסכים קוראים לו.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import datetime as _dt


# ============================================================
#  מצב תחנה במסע
# ============================================================
class StationState(str, Enum):
    LOCKED = "locked"        # עוד לא נפתחה (נדרשת תחנה קודמת)
    AVAILABLE = "available"  # פתוחה, אפשר להתחיל
    IN_PROGRESS = "active"   # בתהליך למידה
    MASTERED = "mastered"    # נשלטה (90%+) — פותחת את הבאה


@dataclass
class Station:
    """תחנה אחת במסע — מקבילה לנושא לימוד (learning_node)."""
    node_id: str
    title: str
    state: StationState = StationState.LOCKED
    progress: float = 0.0    # 0..1 התקדמות בתוך התחנה

    @property
    def is_open(self) -> bool:
        return self.state in (StationState.AVAILABLE, StationState.IN_PROGRESS, StationState.MASTERED)


# ============================================================
#  אבני דרך ("נצחונות קטנים") — מזוהות אוטומטית
# ============================================================
class MilestoneType(str, Enum):
    FIRST_STATION = "first_station"      # התחנה הראשונה שנשלטה אי פעם
    STATION_DONE = "station_done"        # כל השלמת תחנה
    STREAK_3 = "streak_3"                # 3 ימים ברצף
    STREAK_7 = "streak_7"                # שבוע ברצף
    AREA_DONE = "area_done"              # אזור שלם (קבוצת תחנות) הושלם
    COMEBACK = "comeback"                # חזרה אחרי הפסקה — מחזקים, לא נוזפים


@dataclass
class Milestone:
    type: MilestoneType
    say: str                             # מה אלמה אומרת (בקול!) — חוגג מסוגלוּת
    gentle: bool = True                  # תמיד עדין ומכובד, לא רועש


# ניסוחים — חוגגים *מסוגלוּת ומאמץ*, לא "פרס". מותאמי-גיל, בלי ניקוד.
# שים לב: מדגישים את מה שהילד *עשה* ("ראית איך..."), לא תגמול חיצוני.
_MILESTONE_SAY = {
    MilestoneType.FIRST_STATION: {
        "a_b": "הגעת לתחנה הראשונה במסע! ראית שאתה יכול?",
        "c_d": "התחנה הראשונה שלך במסע הושלמה — וראית בעצמך שאתה מסוגל!",
    },
    MilestoneType.STATION_DONE: {
        "a_b": "סיימת את התחנה! המסע ממשיך הלאה.",
        "c_d": "תחנה הושלמה — שלטת בנושא הזה. הדרך הבאה נפתחת!",
    },
    MilestoneType.STREAK_3: {
        "a_b": "שלושה ימים ברצף! איזו התמדה יפה.",
        "c_d": "שלושה ימים ברצף של תרגול — ההתמדה הזו היא מה שמקדם אותך.",
    },
    MilestoneType.STREAK_7: {
        "a_b": "שבוע שלם ברצף! אתה אלוף התמדה.",
        "c_d": "שבוע שלם ברצף — זו בדיוק הדרך שבה לומדים באמת. כל הכבוד!",
    },
    MilestoneType.AREA_DONE: {
        "a_b": "סיימת אזור שלם במפה! מסע מרשים.",
        "c_d": "השלמת אזור שלם במסע — הסתכל אחורה וראה כמה התקדמת!",
    },
    MilestoneType.COMEBACK: {
        "a_b": "כיף שחזרת! בוא נמשיך מאיפה שהיינו.",
        "c_d": "טוב לראות אותך שוב! נמשיך את המסע מאיפה שעצרנו.",
    },
}


def milestone_phrase(mtype: MilestoneType, age_band: str) -> str:
    bank = _MILESTONE_SAY.get(mtype, {})
    return bank.get(age_band, bank.get("c_d", ""))


# ============================================================
#  רצף אישי (streak) — מול עצמך, לא מול אחרים
# ============================================================
@dataclass
class Streak:
    current: int = 0                     # ימים רצופים נוכחיים
    longest: int = 0                     # השיא האישי
    last_active: Optional[str] = None    # תאריך פעילות אחרון (ISO)

    def record_activity(self, today: Optional[str] = None) -> dict:
        """
        מעדכן רצף לפי יום פעילות. מחזיר מה קרה (לזיהוי אבני דרך).
        רצף = ימים *רצופים*. פספוס יום מאפס בעדינות (בלי ענישה).
        """
        today = today or _dt.date.today().isoformat()
        result = {"continued": False, "reset": False, "comeback": False, "same_day": False}

        if self.last_active is None:
            self.current = 1
        else:
            last = _dt.date.fromisoformat(self.last_active)
            cur = _dt.date.fromisoformat(today)
            gap = (cur - last).days
            if gap == 0:
                result["same_day"] = True
                return result            # כבt נספר היום, לא משנים
            elif gap == 1:
                self.current += 1
                result["continued"] = True
            else:
                # פספוס — מאפסים בעדינות, ומסמנים "חזרה" (לחיזוק, לא נזיפה)
                self.current = 1
                result["reset"] = True
                if gap >= 3:
                    result["comeback"] = True

        self.last_active = today
        self.longest = max(self.longest, self.current)
        return result


# ============================================================
#  מנוע המסע — הלב
# ============================================================
@dataclass
class JourneyProgress:
    """המצב המלא של מסע הילד — נשמר במסד."""
    stations: list = field(default_factory=list)   # רשימת Station לפי סדר
    streak: Streak = field(default_factory=Streak)
    age_band: str = "c_d"
    ever_mastered_any: bool = False

    def station_by_id(self, node_id: str) -> Optional[Station]:
        for s in self.stations:
            if s.node_id == node_id:
                return s
        return None

    @property
    def mastered_count(self) -> int:
        return sum(1 for s in self.stations if s.state == StationState.MASTERED)

    @property
    def total(self) -> int:
        return len(self.stations)

    @property
    def percent_complete(self) -> int:
        return round(100 * self.mastered_count / self.total) if self.total else 0

    @property
    def current_station(self) -> Optional[Station]:
        """התחנה הפעילה — בתהליך, או הראשונה הזמינה."""
        for s in self.stations:
            if s.state == StationState.IN_PROGRESS:
                return s
        for s in self.stations:
            if s.state == StationState.AVAILABLE:
                return s
        return None

    def unlock_initial(self) -> None:
        """פותח את התחנה הראשונה אם הכל נעול (תחילת מסע)."""
        if self.stations and all(s.state == StationState.LOCKED for s in self.stations):
            self.stations[0].state = StationState.AVAILABLE

    def complete_station(self, node_id: str) -> list:
        """
        מסמן תחנה כנשלטה, פותח את הבאה, ומחזיר אבני דרך שזוהו.
        זה הרגע המשמעותי — חוגגים מסוגלוּת.
        """
        milestones: list = []
        st = self.station_by_id(node_id)
        if not st or st.state == StationState.MASTERED:
            return milestones

        st.state = StationState.MASTERED
        st.progress = 1.0

        # אבן דרך: התחנה הראשונה אי פעם
        if not self.ever_mastered_any:
            self.ever_mastered_any = True
            milestones.append(Milestone(MilestoneType.FIRST_STATION,
                                        milestone_phrase(MilestoneType.FIRST_STATION, self.age_band)))
        else:
            milestones.append(Milestone(MilestoneType.STATION_DONE,
                                        milestone_phrase(MilestoneType.STATION_DONE, self.age_band)))

        # פתיחת התחנה הבאה ברצף
        idx = self.stations.index(st)
        if idx + 1 < len(self.stations):
            nxt = self.stations[idx + 1]
            if nxt.state == StationState.LOCKED:
                nxt.state = StationState.AVAILABLE

        return milestones

    def record_day(self, today: Optional[str] = None) -> list:
        """מעדכן רצף ומחזיר אבני דרך של רצף/חזרה."""
        milestones: list = []
        r = self.streak.record_activity(today)
        if r.get("comeback"):
            milestones.append(Milestone(MilestoneType.COMEBACK,
                                        milestone_phrase(MilestoneType.COMEBACK, self.age_band)))
        if r.get("continued"):
            if self.streak.current == 3:
                milestones.append(Milestone(MilestoneType.STREAK_3,
                                            milestone_phrase(MilestoneType.STREAK_3, self.age_band)))
            elif self.streak.current == 7:
                milestones.append(Milestone(MilestoneType.STREAK_7,
                                            milestone_phrase(MilestoneType.STREAK_7, self.age_band)))
        return milestones


# ============================================================
#  נצחונות קטנים (micro-wins) — בתוך התרגול, לא רק בסופו
# ------------------------------------------------------------
#  עיקרון: תחושת התקדמות *מתמשכת*. רגעים קטנים של עידוד לאורך
#  הדרך — אך עדין, לא חגיגה על כל תשובה (זה מתיש ושוחק ערך).
# ============================================================
class MicroWinType(str, Enum):
    STREAK_IN_SESSION = "streak_in_session"   # רצף תשובות נכונות בסשן
    HALFWAY = "halfway"                        # חצי הדרך ליעד הנושא
    PERSONAL_BEST = "personal_best"            # שיא אישי חדש בנושא
    BOUNCE_BACK = "bounce_back"                # התאוששות אחרי טעות


@dataclass
class MicroWin:
    type: MicroWinType
    say: str
    subtle: bool = True       # תמיד עדין — חיזוק קצר, לא חגיגה גדולה


# כמה תשובות נכונות ברצף מזכות ב"נצחון קטן" (לא כל תשובה!)
_STREAK_TRIGGER = 3
# אחרי נצחון רצף — לא עוד אחד עד שעובר המרווח הזה (שלא יהיה מתיש)
_MIN_GAP_BETWEEN_MICROWINS = 4


@dataclass
class SessionMomentum:
    """עוקב אחרי המומנטום בתוך סשן תרגול — לזיהוי נצחונות קטנים."""
    correct_streak: int = 0
    answered: int = 0
    target: int = 10                      # יעד שאלות לנושא
    since_last_win: int = 99
    best_streak: int = 0
    just_recovered: bool = False          # ענה נכון מיד אחרי טעות
    _halfway_done: bool = False

    def on_answer(self, correct: bool) -> Optional[MicroWin]:
        """מעבד תשובה ומחזיר נצחון קטן אם מגיע — אחרת None (הרוב)."""
        self.answered += 1
        self.since_last_win += 1

        if correct:
            prev = self.correct_streak
            self.correct_streak += 1
            self.best_streak = max(self.best_streak, self.correct_streak)
            self.just_recovered = (prev == 0 and self.answered > 1)
        else:
            self.correct_streak = 0
            self.just_recovered = False
            return None   # אף פעם לא "חוגגים" טעות — רק לא ענישה

        # חצי הדרך ליעד — ציון דרך חשוב, מקבל עדיפות (לא נחסם)
        if not self._halfway_done and self.answered >= self.target // 2:
            self._halfway_done = True
            self.since_last_win = 0
            return MicroWin(MicroWinType.HALFWAY, "כבר חצי הדרך! ממשיכים יפה.")

        # שמירת מרווח — שלא יהיה מתיש (חל על רצף, לא על ציוני דרך)
        if self.since_last_win < _MIN_GAP_BETWEEN_MICROWINS:
            return None

        # רצף נכונות בתוך הסשן
        if self.correct_streak == _STREAK_TRIGGER:
            self.since_last_win = 0
            return MicroWin(MicroWinType.STREAK_IN_SESSION,
                            f"{_STREAK_TRIGGER} נכונות ברצף! אתה בקצב מצוין.")

        return None   # המצב הנפוץ — אין נצחון, פשוט ממשיכים

    @property
    def progress(self) -> float:
        """התקדמות לעבר היעד 0..1 — למד ההתקדמות החי."""
        return min(1.0, self.answered / self.target) if self.target else 0.0
