"""
============================================================
 אלמה — מדליות אליפות וצליל ניצחון (Rewards)
============================================================
שני מנגנונים, מבוססי-מחקר, שמחזקים *מסוגלוּת* (לא פרס מנותק):

  1. מדליית אליפות אישית — מדליית זהב לכל נושא שהושלם, במפה
     האישית של הילד. חוגגת מסוגלוּת אמיתית. אישית בלבד (לא תחרות).

  2. צליל ניצחון מעודן — צליל קצר ונעים על הצלחה, עם *דהיית
     גירויים*: ככל שהילד מתרגל יותר, הצליל נעשה עדין ונדיר יותר,
     כדי שלא ייהפך מתיש או קיטשי (מונע אפקט הצדקה-יתר ותלות).

עיקרון-על (מהמחקר): גיימיפיקציה משרתת את הלמידה, לא מחליפה אותה.
כל מנגנון מחזק "אני מסוגל" — לא נותן פרס על עצם ההשתתפות.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


# ============================================================
#  1) מדליות אליפות אישיות
# ============================================================
class MedalTier(str, Enum):
    GOLD = "gold"          # נושא שהושלם בשליטה מלאה (90%+ כולל הבנה)


@dataclass
class Medal:
    """מדליית אליפות על נושא שהושלם. אישית — נראית רק לילד עצמו."""
    topic_id: str
    topic_title: str
    tier: MedalTier = MedalTier.GOLD
    earned_on: Optional[str] = None        # תאריך ISO


@dataclass
class MedalCollection:
    """אוסף המדליות של ילד — האליפויות האישיות שלו במפה."""
    medals: list = field(default_factory=list)

    def award(self, topic_id: str, topic_title: str, today: Optional[str] = None) -> Optional[Medal]:
        """מעניק מדליה על נושא — אם עוד אין עליו. מחזיר את המדליה החדשה."""
        if any(m.topic_id == topic_id for m in self.medals):
            return None   # כבר יש מדליה על הנושא הזה
        medal = Medal(topic_id=topic_id, topic_title=topic_title, earned_on=today)
        self.medals.append(medal)
        return medal

    @property
    def count(self) -> int:
        return len(self.medals)

    def has_medal(self, topic_id: str) -> bool:
        return any(m.topic_id == topic_id for m in self.medals)

    def celebration_phrase(self, age_band: str) -> str:
        """משפט חגיגה כשמרוויחים מדליה — חוגג מסוגלוּת, מותאם גיל."""
        n = self.count
        if age_band == "a_b":
            return f"מדליית זהב! ראית שאתה מסוגל. יש לך כבר {n}!"
        return f"מדליית זהב על הנושא הזה! שלטת בו באמת. אספת {n} מדליות אליפות."


# ============================================================
#  2) צליל ניצחון מעודן — עם דהיית גירויים
# ============================================================
# רמות עוצמה לצליל. דוהה ככל שהילד מתרגל יותר (מונע התשה/קיטש).
class SoundLevel(str, Enum):
    FULL = "full"          # צליל מלא ונעים (בתחילת הדרך)
    SOFT = "soft"          # מעודן יותר (כשכבר מורגל)
    MINIMAL = "minimal"    # רמז דק בלבד (כשמיומן מאוד)
    OFF = "off"            # מושתק (בחירת המשתמש)


# כמה תשובות נכונות מצטברות עד שהצליל "דוהה" שלב (הרגל נוצר)
_FADE_AFTER = {SoundLevel.FULL: 30, SoundLevel.SOFT: 80}


@dataclass
class VictorySound:
    """
    מנהל את צליל הניצחון. עיקרון: צליל קצר ונעים על הצלחה, אך
    *דוהה בהדרגה* ככל שהילד צובר הצלחות — כדי שיישאר מתגמל ולא מתיש.
    הילד תמיד יכול להשתיק.
    """
    level: SoundLevel = SoundLevel.FULL
    total_successes: int = 0
    muted_by_user: bool = False

    def on_success(self) -> Optional[str]:
        """
        נקרא על כל תשובה נכונה. מחזיר את סוג הצליל לנגן (או None אם
        אין צליל כרגע). מעדכן את הדהייה לפי כמות ההצלחות.
        """
        self.total_successes += 1
        if self.muted_by_user or self.level == SoundLevel.OFF:
            return None

        # דהייה: אחרי מספיק הצלחות, יורדים שלב (ההרגל כבר קיים)
        if self.level == SoundLevel.FULL and self.total_successes >= _FADE_AFTER[SoundLevel.FULL]:
            self.level = SoundLevel.SOFT
        elif self.level == SoundLevel.SOFT and self.total_successes >= _FADE_AFTER[SoundLevel.SOFT]:
            self.level = SoundLevel.MINIMAL

        return self.level.value

    def mute(self) -> None:
        self.muted_by_user = True

    def unmute(self) -> None:
        self.muted_by_user = False

    @property
    def is_audible(self) -> bool:
        return not self.muted_by_user and self.level != SoundLevel.OFF


# פרופיל הצליל לכל רמה — נתונים שה-frontend משתמש בהם לנגינה.
# (תדר, משך) — צליל "קלינג" קצר ועולה, נעים ולא צורם.
SOUND_PROFILE = {
    SoundLevel.FULL:    {"duration_ms": 280, "gain": 0.18, "notes": [660, 880]},
    SoundLevel.SOFT:    {"duration_ms": 220, "gain": 0.12, "notes": [660, 880]},
    SoundLevel.MINIMAL: {"duration_ms": 160, "gain": 0.07, "notes": [880]},
}
