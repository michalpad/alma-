"""
ALMA — שומר נושא (Topic Guard) / נוקשות פדגוגית.
משימה 4. אם התלמיד מסיט את השיחה לנושא שאינו חומר הלימוד,
המערכת חותכת בעדינות-נוקשות ומחזירה מיד לחומר. ללא נעילה.

איזון פדגוגי: שאלות תפעול לגיטימיות ("מתי הפסקה?", "אני עייף") אינן
הסטה — הן זוכות למענה קצר וחזרה. רק שיחת חולין/הסחה ממשית מופנית בחזרה.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

# מילות עוגן שמרמזות על קשר לחומר הלימוד (אינן ממצות — רמז בלבד).
ON_TASK_HINTS = re.compile(
    r"(תשובה|שאלה|תרגיל|לא הבנתי|אפשר עוד|רמז|נכון|למה|איך פותרים|"
    r"מספר|מילה|אות|לקרוא|לכתוב|חשבון|דקדוק)"
)

# פניות תפעול לגיטימיות — מענה קצר, לא נחשב הסחה.
OPERATIONAL = re.compile(
    r"(הפסקה|עייף|עייפה|שירותים|מים|כמה זמן|לסיים|להפסיק|מספיק להיום)"
)

# סמני שיחת-חולין / הסחה ברורה.
OFF_TOPIC = re.compile(
    r"(משחק|יוטיוב|טיקטוק|חבר|חברה|בא לי לשחק|משעמם|ספר לי בדיחה|"
    r"מה השם שלך|בן כמה אתה|אתה רובוט|בוא נדבר על)"
)


@dataclass
class TopicDecision:
    state: str           # 'on_task' | 'operational' | 'off_topic' | 'uncertain'
    redirect: bool       # האם להחזיר לחומר
    reply_hint: str = "" # רמז לניסוח התגובה (ה-LLM מנסח בפועל)


def classify_topic(text: str) -> TopicDecision:
    """
    סיווג מהיר מבוסס-כללים. במקרי ספק מחזיר 'uncertain'
    כדי שה-Orchestrator יפנה לסיווג קצר ב-LLM.
    """
    t = text.strip()
    if OFF_TOPIC.search(t):
        return TopicDecision(
            state="off_topic", redirect=True,
            reply_hint="החזר/י בעדינות אך בנחישות לחומר הלימוד. משפט אחד קצר, "
                       "חם, ואז שאלה הקשורה לנושא הנלמד.",
        )
    if OPERATIONAL.search(t):
        return TopicDecision(
            state="operational", redirect=False,
            reply_hint="ענה/י קצר ואדיב לפנייה התפעולית, ואז חזור/חזרי לחומר.",
        )
    if ON_TASK_HINTS.search(t):
        return TopicDecision(state="on_task", redirect=False)
    # קצר מאוד או לא ברור -> ספק
    if len(t.split()) <= 2:
        return TopicDecision(state="on_task", redirect=False)
    return TopicDecision(state="uncertain", redirect=False)


# פרומפט קצר לסיווג ספק ע"י LLM (זול, פלט מילה אחת).
LLM_TOPIC_CLASSIFIER_PROMPT = (
    "סווג/י את הודעת התלמיד למילה אחת בלבד: "
    "'on_task' אם קשורה לחומר הלימוד, 'off_topic' אם זו שיחת חולין/הסחה, "
    "'operational' אם זו בקשת תפעול (הפסקה/עייפות). "
    "החזר/י רק את המילה."
)


async def resolve_topic(text: str, llm_call=None) -> TopicDecision:
    """סיווג מהיר; אם 'uncertain' ויש llm_call — מבקש הכרעה קצרה."""
    decision = classify_topic(text)
    if decision.state != "uncertain" or llm_call is None:
        return decision
    raw = (await llm_call(LLM_TOPIC_CLASSIFIER_PROMPT, text)).strip().lower()
    if "off" in raw:
        return TopicDecision(state="off_topic", redirect=True,
                             reply_hint="החזר/י בנחישות ובחום לחומר הלימוד.")
    if "oper" in raw:
        return TopicDecision(state="operational", redirect=False,
                             reply_hint="מענה קצר ואז חזרה לחומר.")
    return TopicDecision(state="on_task", redirect=False)
