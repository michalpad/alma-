"""
ALMA — בנק תבניות לדוגמה: חיבור וחיסור בתחום ה-20 (כיתה א').
מדגים את עיקרון השילוב: תבניות מאומתות (נכונות מתמטית) שמייצרות
וריאציות מגוונות בכל פרמטר — מספרים, הקשר, סוג שאלה, עטיפת משחק.

כל generator מחשב את התשובה הנכונה בעצמו -> נכונות מובטחת בשרת.
"""
from __future__ import annotations

import random

from .practice_engine import Question, QType, Difficulty, Template

NODE = "20000000-0000-4000-8000-000000000020"  # חיבור וחיסור בתחום ה-20

# הקשרים מגוונים לשאלות מילוליות (גיוון בהקשר)
CONTEXTS = [
    ("תַּפּוּחִים", "בַּסַּל"), ("בָּלוֹנִים", "בַּמְּסִבָּה"),
    ("עִפְרוֹנוֹת", "בַּקַּלְמָר"), ("פְּרָחִים", "בָּאֲגַרְטֵל"),
    ("כַּדּוּרִים", "בַּקֻּפְסָה"), ("דְּגֵי זָהָב", "בָּאַקְוַרְיוּם"),
]
NUM_WORDS = {1: "אֶחָד", 2: "שְׁנַיִם", 3: "שְׁלוֹשָׁה", 4: "אַרְבָּעָה",
             5: "חֲמִשָּׁה", 6: "שִׁשָּׁה", 7: "שִׁבְעָה", 8: "שְׁמוֹנָה",
             9: "תִּשְׁעָה", 10: "עֲשָׂרָה"}


def _mc_options(rng, correct, lo=0, hi=20, k=4):
    """מסיח סגור: אפשרויות מגוונות סביב התשובה הנכונה."""
    opts = {correct}
    while len(opts) < k:
        d = rng.choice([-3, -2, -1, 1, 2, 3])
        v = correct + d
        if lo <= v <= hi:
            opts.add(v)
    opts = list(opts)
    rng.shuffle(opts)
    return opts


# ---------- תבנית 1: חיבור פשוט (קל) ----------
def gen_add_easy(rng, qtype):
    a, b = rng.randint(1, 9), rng.randint(1, 9)
    while a + b > 20:
        a, b = rng.randint(1, 9), rng.randint(1, 9)
    ans = a + b

    if qtype == QType.OPEN_NUMERIC:
        return Question(qtype, Difficulty.EASY,
                        prompt=f"כַּמָּה זֶה {a} וְעוֹד {b}?", answer=ans,
                        explain=f"{a} וְעוֹד {b} זֶה {ans}.")
    if qtype == QType.MULTIPLE_CHOICE:
        return Question(qtype, Difficulty.EASY,
                        prompt=f"כַּמָּה זֶה {a} + {b}?", answer=ans,
                        options=_mc_options(rng, ans))
    if qtype == QType.FILL_BLANK:
        return Question(qtype, Difficulty.EASY,
                        prompt=f"הַשְׁלִימוּ: {a} + {b} = ___", answer=ans)
    if qtype == QType.TRUE_FALSE:
        shown = ans if rng.random() < 0.5 else ans + rng.choice([-2, -1, 1, 2])
        return Question(qtype, Difficulty.EASY,
                        prompt=f"נָכוֹן אוֹ לֹא נָכוֹן? {a} + {b} = {shown}",
                        answer=(shown == ans))
    # ברירת מחדל
    return Question(QType.OPEN_NUMERIC, Difficulty.EASY,
                    prompt=f"כַּמָּה זֶה {a} + {b}?", answer=ans)


# ---------- תבנית 2: חיסור פשוט (קל) ----------
def gen_sub_easy(rng, qtype):
    a = rng.randint(2, 20)
    b = rng.randint(1, a)
    ans = a - b
    if qtype == QType.MULTIPLE_CHOICE:
        return Question(qtype, Difficulty.EASY,
                        prompt=f"כַּמָּה זֶה {a} פָּחוֹת {b}?", answer=ans,
                        options=_mc_options(rng, ans))
    return Question(QType.OPEN_NUMERIC, Difficulty.EASY,
                    prompt=f"כַּמָּה זֶה {a} - {b}?", answer=ans,
                    explain=f"{a} פָּחוֹת {b} זֶה {ans}.")


# ---------- תבנית 3: שאלה מילולית בהקשר (בינוני) ----------
def gen_word_medium(rng, qtype):
    item, place = rng.choice(CONTEXTS)
    a, b = rng.randint(2, 10), rng.randint(1, 8)
    ans = a + b
    prompt = (f"הָיוּ {a} {item} {place}, וְהוֹסִיפוּ עוֹד {b}. "
              f"כַּמָּה {item} יֵשׁ עַכְשָׁו?")
    if qtype == QType.MULTIPLE_CHOICE:
        return Question(qtype, Difficulty.MEDIUM, prompt=prompt, answer=ans,
                        options=_mc_options(rng, ans))
    return Question(QType.OPEN_NUMERIC, Difficulty.MEDIUM, prompt=prompt,
                    answer=ans, explain=f"{a} וְעוֹד {b} זֶה {ans}.")


# ---------- תבנית 4: השלמת הנעלם (בינוני) ----------
def gen_missing_medium(rng, qtype):
    a = rng.randint(1, 9)
    ans = rng.randint(1, 20 - a)
    total = a + ans
    return Question(QType.FILL_BLANK, Difficulty.MEDIUM,
                    prompt=f"הַשְׁלִימוּ אֶת הַמִּסְפָּר הֶחָסֵר: {a} + ___ = {total}",
                    answer=ans, explain=f"{total} פָּחוֹת {a} זֶה {ans}.")


# ---------- תבנית 5: סידור רצף (אתגר, משחקי) ----------
def gen_order_challenge(rng, qtype):
    base = rng.randint(1, 6)
    vals = sorted(rng.sample(range(base, base + 12), 4))
    shuffled = vals[:]
    rng.shuffle(shuffled)
    return Question(QType.ORDER_SEQUENCE, Difficulty.CHALLENGE,
                    prompt="סַדְּרוּ אֶת הַמִּסְפָּרִים מֵהַקָּטָן לַגָּדוֹל:",
                    answer=vals, payload={"tiles": shuffled},
                    explain="מְסַדְּרִים מֵהַמִּסְפָּר הַקָּטָן בְּיוֹתֵר לַגָּדוֹל בְּיוֹתֵר.")


# ---------- תבנית 6: התאמת זוגות (אתגר, משחקי) ----------
def gen_match_challenge(rng, qtype):
    pairs = []
    used = set()
    while len(pairs) < 3:
        a, b = rng.randint(1, 9), rng.randint(1, 9)
        if a + b <= 20 and (a + b) not in used:
            used.add(a + b)
            pairs.append((f"{a} + {b}", a + b))
    left = [p[0] for p in pairs]
    right = [p[1] for p in pairs]
    rng.shuffle(right)
    return Question(QType.MATCH_PAIRS, Difficulty.CHALLENGE,
                    prompt="הַתְאִימוּ כָּל תַּרְגִּיל לַתּוֹצָאָה שֶׁלּוֹ:",
                    answer=[p[1] for p in pairs],
                    payload={"left": left, "right": right, "pairs": pairs},
                    explain="פּוֹתְרִים כָּל תַּרְגִּיל וּמְחַבְּרִים לַתּוֹצָאָה הַנְּכוֹנָה.")


# ---------- רישום התבניות ----------
def build_templates() -> list:
    return [
        Template("add_easy", NODE, Difficulty.EASY,
                 [QType.OPEN_NUMERIC, QType.MULTIPLE_CHOICE, QType.FILL_BLANK, QType.TRUE_FALSE],
                 gen_add_easy),
        Template("sub_easy", NODE, Difficulty.EASY,
                 [QType.OPEN_NUMERIC, QType.MULTIPLE_CHOICE], gen_sub_easy),
        Template("word_medium", NODE, Difficulty.MEDIUM,
                 [QType.OPEN_NUMERIC, QType.MULTIPLE_CHOICE], gen_word_medium),
        Template("missing_medium", NODE, Difficulty.MEDIUM,
                 [QType.FILL_BLANK], gen_missing_medium),
        Template("order_challenge", NODE, Difficulty.CHALLENGE,
                 [QType.ORDER_SEQUENCE], gen_order_challenge),
        Template("match_challenge", NODE, Difficulty.CHALLENGE,
                 [QType.MATCH_PAIRS], gen_match_challenge),
    ]
