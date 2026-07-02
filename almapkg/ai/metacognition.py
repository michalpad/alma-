"""אלמה — שכבת מטה-קוגניציה (לומד עצמאי). מבוסס EEF: תכנון-ניטור-הערכה.
מינון חכם: מטה-קוגניציה היא תבלין, לא מנה עיקרית. תקרה קשיחה גם לזורמים."""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import random


class MetaMoment(str, Enum):
    PLAN = "plan"
    PREDICT = "predict"
    MONITOR = "monitor"
    EVALUATE = "evaluate"
    REFLECT = "reflect"


AGE_BUDGET = {
    "a_b": {"max_moments": 2, "prefer_emotional": True},
    "c_d": {"max_moments": 3, "prefer_emotional": False},
    "e_f": {"max_moments": 4, "prefer_emotional": False},
}
HARD_CEILING_PER_SESSION = 4
MIN_CLEAN_RUN_BETWEEN_MOMENTS = 4


@dataclass
class MetaState:
    age_band: str = "c_d"
    moments_used: int = 0
    since_last_moment: int = 999
    skips: int = 0
    engaged_responses: int = 0
    plan_done_for_topic: bool = False
    consecutive_errors: int = 0

    @property
    def budget(self) -> int:
        base = AGE_BUDGET.get(self.age_band, AGE_BUDGET["c_d"])["max_moments"]
        if self.skips >= 2:
            base = max(1, base - 1)
        if self.engaged_responses >= 3 and self.skips == 0:
            base = base + 1
        return min(base, HARD_CEILING_PER_SESSION)

    @property
    def exhausted(self) -> bool:
        return self.moments_used >= self.budget


@dataclass
class MetaContext:
    is_topic_start: bool = False
    is_session_end: bool = False
    just_failed_repeatedly: bool = False
    just_succeeded_hard: bool = False
    difficulty_is_challenge: bool = False


def decide_moment(state: MetaState, ctx: MetaContext) -> Optional[MetaMoment]:
    if state.exhausted and not ctx.is_session_end:
        return None
    if state.since_last_moment < MIN_CLEAN_RUN_BETWEEN_MOMENTS and not ctx.is_session_end:
        return None
    if ctx.is_topic_start and not state.plan_done_for_topic:
        return MetaMoment.PLAN
    if ctx.just_failed_repeatedly:
        return MetaMoment.MONITOR
    if ctx.just_succeeded_hard and ctx.difficulty_is_challenge:
        return MetaMoment.EVALUATE
    if ctx.is_session_end and state.moments_used < state.budget:
        return MetaMoment.REFLECT
    return None


def register_moment_shown(state: MetaState, moment: MetaMoment) -> None:
    state.moments_used += 1
    state.since_last_moment = 0
    if moment == MetaMoment.PLAN:
        state.plan_done_for_topic = True


def register_question_answered(state: MetaState, correct: bool) -> None:
    state.since_last_moment += 1
    if correct:
        state.consecutive_errors = 0
    else:
        state.consecutive_errors += 1


def register_child_response(state: MetaState, engaged: bool) -> None:
    if engaged:
        state.engaged_responses += 1
    else:
        state.skips += 1


_PHRASES = {
    MetaMoment.PLAN: {"emotional": ["איזה כיף, נושא חדש! בא לך לנסות לבד או שנתחיל יחד?"],
                      "verbal": ["לפני שמתחילים — איך בא לך לגשת לזה?", "מה כבר אתה יודע שיכול לעזור פה?"]},
    MetaMoment.PREDICT: {"emotional": ["מה הניחוש שלך — קל או קצת מאתגר?"],
                         "verbal": ["כמה אתה בטוח שתצליח? נראה אם צדקת!"]},
    MetaMoment.MONITOR: {"emotional": ["רגע, בוא ננשום. נסתכל שוב יחד על הדרך?"],
                         "verbal": ["הדרך שבחרת עובדת, או ננסה דרך אחרת?", "בוא נבדוק את עצמנו — איפה זה הסתבך?"]},
    MetaMoment.EVALUATE: {"emotional": ["יפה מאוד! ספר לי — איך הצלחת?"],
                          "verbal": ["כל הכבוד! איך הגעת לתשובה?", "פתרת יפה — איזו דרך עזרה לך?"]},
    MetaMoment.REFLECT: {"emotional": ["סיימנו להיום! מה הכי אהבת?"],
                         "verbal": ["לפני שמסיימים — מה היה הכי קל, ומה עוד נתרגל?", "מה למדת היום על איך אתה לומד?"]},
}


def phrase_for(moment: MetaMoment, age_band: str, rng: random.Random) -> str:
    bank = _PHRASES[moment]
    prefer_emotional = AGE_BUDGET.get(age_band, AGE_BUDGET["c_d"])["prefer_emotional"]
    pool = bank["emotional"] if (prefer_emotional and bank.get("emotional")) else bank["verbal"]
    return rng.choice(pool)


DIM_WEIGHTS = {"strategy": 0.30, "explain": 0.30, "self_correct": 0.20, "calibration": 0.20}
_MATURITY_OPPORTUNITIES = 8


@dataclass
class IndependenceProfile:
    strategy_taken: int = 0
    strategy_offered: int = 0
    explain_given: int = 0
    explain_asked: int = 0
    correct_self_fixed: int = 0
    errors_total: int = 0
    calib_accurate: int = 0
    calib_total: int = 0
    score_history: list = field(default_factory=list)

    def _ratio(self, used, opp):
        return (used / opp) if opp else 0.0

    @property
    def dimensions(self):
        return {"strategy": self._ratio(self.strategy_taken, self.strategy_offered),
                "explain": self._ratio(self.explain_given, self.explain_asked),
                "self_correct": self._ratio(self.correct_self_fixed, self.errors_total),
                "calibration": self._ratio(self.calib_accurate, self.calib_total)}

    @property
    def total_opportunities(self):
        return self.strategy_offered + self.explain_asked + self.errors_total + self.calib_total

    @property
    def is_mature(self):
        return self.total_opportunities >= _MATURITY_OPPORTUNITIES

    @property
    def score(self):
        d = self.dimensions
        return round(sum(d[k] * DIM_WEIGHTS[k] for k in DIM_WEIGHTS) * 100)

    @property
    def level(self):
        if not self.is_mature:
            return "מתחילים להכיר"
        s = self.score
        if s >= 75: return "לומד עצמאי"
        if s >= 50: return "בדרך לעצמאות"
        if s >= 25: return "צומח ומתנסה"
        return "צעדים ראשונים"

    def snapshot(self):
        self.score_history.append(self.score)

    @property
    def growth(self):
        if len(self.score_history) < 2:
            return None
        return self.score_history[-1] - self.score_history[-2]


def parent_insight(profile: IndependenceProfile, child_name: str = "הילד/ה") -> str:
    if not profile.is_mature:
        return f"{child_name} בתחילת הדרך — אלמה לומדת להכיר איך הוא/היא חושב/ת. עוד מעט נראה תמונה מלאה."
    dims = profile.dimensions
    strongest = max(dims, key=dims.get)
    weakest = min(dims, key=dims.get)
    label = {"strategy": "בוחר/ת דרך לפתרון בעצמו/ה", "explain": "מסביר/ה איך הגיע/ה לתשובה",
             "self_correct": "מזהה טעויות ומתקן/ת לבד", "calibration": "יודע/ת להעריך את עצמו/ה"}
    growth = profile.growth
    grow_txt = f" ועלה/תה ב-{growth} נקודות מהפעם הקודמת — צמיחה יפה!" if (growth and growth > 0) else ""
    return (f"{child_name} חזק/ה במיוחד בלזה ש{label[strongest]}{grow_txt} "
            f"השלב הבא יהיה לתרגל יותר ש{label[weakest]} — ואלמה כבר עוזרת לו/ה בזה.")
