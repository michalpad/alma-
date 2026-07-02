"""
============================================================
 אלמה — מנוע המנוי (Subscription)
============================================================
מודל: שבוע התנסות חינם *בלי כרטיס אשראי*. אחרי שבוע — המנוי
נחסם אוטומטית, ונפתח שוב רק עם תשלום.

מסלולים:
  - יחיד (ילד אחד):   69 ₪ רגיל / 49 ₪ מבצע (ללא התחייבות)
  - משפחתי (עד 4):    119 ₪ לחודש

הערה חשובה: מנוע זה מנהל *מצב* ו*לוגיקה* בלבד. החיוב עצמו נעשה
דרך ספק סליקה חיצוני (Stripe/Tranzila/וכו') — המנוע חושף נקודות
חיבור (mark_paid וכו') שספק הסליקה קורא להן. אלמה לעולם לא
מעבדת או שומרת פרטי אשראי בעצמה.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import datetime as _dt


# ============================================================
#  מסלולי מנוי
# ============================================================
class Plan(str, Enum):
    SINGLE = "single"       # ילד אחד
    FAMILY = "family"       # עד 4 ילדים


# מחירים (בשקלים לחודש). regular=מחיר רגיל, promo=מבצע ללא התחייבות.
PLAN_PRICING = {
    Plan.SINGLE: {"regular": 69, "promo": 49, "max_children": 1},
    Plan.FAMILY: {"regular": 177, "promo": 119, "max_children": 3},
}

TRIAL_DAYS = 7


# ============================================================
#  מצב המנוי
# ============================================================
class SubStatus(str, Enum):
    TRIAL = "trial"         # בתוך שבוע ההתנסות
    ACTIVE = "active"       # מנוי בתשלום פעיל
    LOCKED = "locked"       # ההתנסות נגמרה / התשלום פג — חסום


@dataclass
class Subscription:
    """מצב המנוי של משתמש. נשמר במסד."""
    status: SubStatus = SubStatus.TRIAL
    trial_start: Optional[str] = None      # תאריך התחלת ההתנסות (ISO)
    plan: Optional[Plan] = None            # המסלול שנבחר (כשמשלמים)
    paid_until: Optional[str] = None       # עד מתי שולם (ISO)
    children_count: int = 1

    # --- התחלת התנסות (בלי אשראי!) ---
    def start_trial(self, today: Optional[str] = None) -> None:
        self.status = SubStatus.TRIAL
        self.trial_start = today or _dt.date.today().isoformat()

    def trial_days_left(self, today: Optional[str] = None) -> int:
        if not self.trial_start:
            return TRIAL_DAYS
        today = today or _dt.date.today().isoformat()
        start = _dt.date.fromisoformat(self.trial_start)
        cur = _dt.date.fromisoformat(today)
        elapsed = (cur - start).days
        return max(0, TRIAL_DAYS - elapsed)

    # --- בדיקת גישה (הלב) ---
    def refresh(self, today: Optional[str] = None) -> SubStatus:
        """
        מעדכן את הסטטוס לפי התאריך. נקרא בכל כניסה.
        - אם בהתנסות והשבוע נגמר -> נחסם.
        - אם פעיל והתשלום פג -> נחסם.
        """
        today = today or _dt.date.today().isoformat()
        if self.status == SubStatus.TRIAL:
            if self.trial_days_left(today) <= 0:
                self.status = SubStatus.LOCKED
        elif self.status == SubStatus.ACTIVE:
            if self.paid_until and today > self.paid_until:
                self.status = SubStatus.LOCKED
        return self.status

    @property
    def has_access(self) -> bool:
        """האם מותר להשתמש במערכת כרגע."""
        return self.status in (SubStatus.TRIAL, SubStatus.ACTIVE)

    # --- נקודת חיבור לספק הסליקה ---
    # ספק הסליקה (החיצוני) קורא לזה *אחרי* חיוב מוצלח. אלמה עצמה
    # לא רואה פרטי אשראי — רק מקבלת אישור שהתשלום עבר.
    def mark_paid(self, plan: Plan, children_count: int = 1,
                  today: Optional[str] = None, months: int = 1) -> None:
        today = today or _dt.date.today().isoformat()
        cur = _dt.date.fromisoformat(today)
        # חודש = 30 יום (פשטות; ספק הסליקה הוא מקור האמת לחידושים)
        self.paid_until = (cur + _dt.timedelta(days=30 * months)).isoformat()
        self.plan = plan
        self.children_count = min(children_count, PLAN_PRICING[plan]["max_children"])
        self.status = SubStatus.ACTIVE


# ============================================================
#  עזרי תצוגה
# ============================================================
def price_label(plan: Plan, promo: bool = True) -> str:
    """מחזיר תווית מחיר לתצוגה."""
    p = PLAN_PRICING[plan]
    amount = p["promo"] if promo else p["regular"]
    return f"{amount} ₪ לחודש"


def trial_banner(sub: Subscription, today: Optional[str] = None) -> Optional[str]:
    """באנר עדין לתצוגה במהלך ההתנסות. None אם לא רלוונטי."""
    if sub.status != SubStatus.TRIAL:
        return None
    left = sub.trial_days_left(today)
    if left <= 0:
        return None
    if left == 1:
        return "היום הוא היום האחרון להתנסות החינמית!"
    return f"נשארו {left} ימים להתנסות החינמית"


def can_add_child(sub: Subscription) -> bool:
    """האם אפשר להוסיף עוד ילד למנוי (לפי המסלול)."""
    if sub.plan is None:
        return sub.children_count < 1
    return sub.children_count < PLAN_PRICING[sub.plan]["max_children"]
