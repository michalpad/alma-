"""
ALMA — בנק תרגול מלא לכיתה א' (מתמטיקה).
מכסה את כל ששת נושאי כיתה א' מתכנית הלימודים, בכל רמות הקושי,
בסטנדרט של משרד החינוך. כל מחולל מחשב את תשובתו הנכונה -> נכונות מובטחת.

נושאים (תואם math_grade1_curriculum.sql):
  1. ספירה עד 100
  2. מנייה עד 100
  3. קריאה וכתיבה של המספרים עד 100 וה-0
  4. סדרות
  5. ישר המספרים
  6. סדר המספרים עד 100
  (חיבור/חיסור בתחום ה-20 — בקובץ הנפרד practice_bank_g1_addsub.py)

עיקרון: מקסימום גיוון בכל פרמטר, פתוחות וסגורות, משחקיות, ובדיקת ידע אמיתית.
"""
from __future__ import annotations

import random

from .practice_engine import Question, QType, Difficulty, Template

# מזהי הצמתים מתוך עץ כיתה א'
N_COUNT = "10000000-0000-4000-8000-000000000010"   # ספירה עד 100
N_ENUM = "10000000-0000-4000-8000-000000000020"    # מנייה עד 100
N_READ = "10000000-0000-4000-8000-000000000030"    # קריאה וכתיבה
N_SEQ = "10000000-0000-4000-8000-000000000040"     # סדרות
N_LINE = "10000000-0000-4000-8000-000000000050"    # ישר המספרים
N_ORDER = "10000000-0000-4000-8000-000000000060"   # סדר המספרים

NUM_WORDS = {0: "אֶפֶס", 1: "אֶחָד", 2: "שְׁנַיִם", 3: "שְׁלוֹשָׁה", 4: "אַרְבָּעָה",
             5: "חֲמִשָּׁה", 6: "שִׁשָּׁה", 7: "שִׁבְעָה", 8: "שְׁמוֹנָה", 9: "תִּשְׁעָה",
             10: "עֲשָׂרָה", 20: "עֶשְׂרִים", 30: "שְׁלוֹשִׁים", 50: "חֲמִשִּׁים", 100: "מֵאָה"}


def _mc(rng, correct, lo=0, hi=100, k=4, spread=(-5, -2, -1, 1, 2, 5)):
    opts = {correct}
    g = 0
    while len(opts) < k and g < 60:
        v = correct + rng.choice(spread); g += 1
        if lo <= v <= hi:
            opts.add(v)
    opts = list(opts); rng.shuffle(opts)
    return opts


# ============================================================
#  1. ספירה עד 100
# ============================================================
def gen_count_next(rng, qt):
    """מה המספר הבא/הקודם — ספירה קדימה ואחורה."""
    fwd = rng.random() < 0.6
    n = rng.randint(1, 98)
    ans = n + 1 if fwd else n - 1
    word = "אַחֲרֵי" if fwd else "לִפְנֵי"
    if qt == QType.MULTIPLE_CHOICE:
        return Question(qt, Difficulty.EASY, prompt=f"אֵיזֶה מִסְפָּר בָּא {word} {n}?",
                        answer=ans, options=_mc(rng, ans, spread=(-2, -1, 1, 2)))
    return Question(QType.OPEN_NUMERIC, Difficulty.EASY,
                    prompt=f"אֵיזֶה מִסְפָּר בָּא {word} {n}?", answer=ans)


def gen_count_skip(rng, qt):
    """ספירה בדילוגים (2/5/10) — קדם-אלגברה לפי התכנית."""
    step = rng.choice([2, 5, 10])
    start = rng.choice([0, step, 2 * step])
    seq = [start + step * i for i in range(4)]
    nxt = seq[-1] + step
    return Question(QType.OPEN_NUMERIC, Difficulty.MEDIUM,
                    prompt=f"סִפְרוּ בְּדִילּוּגִים שֶׁל {step}: {seq[0]}, {seq[1]}, {seq[2]}, {seq[3]}, וּמָה הַבָּא?",
                    answer=nxt, explain=f"מוֹסִיפִים {step} בְּכָל פַּעַם.")


# ============================================================
#  2. מנייה עד 100
# ============================================================
def gen_enum_group(rng, qt):
    """מנייה בקבוצות (קיבוץ עשרוני) — כמה בסך הכול."""
    groups = rng.randint(2, 6)
    per = rng.choice([2, 5, 10])
    total = groups * per
    return Question(QType.OPEN_NUMERIC, Difficulty.MEDIUM,
                    prompt=f"יֵשׁ {groups} קְבוּצוֹת, וּבְכָל אַחַת {per} עֲצָמִים. כַּמָּה עֲצָמִים בְּסַךְ הַכֹּל?",
                    answer=total, explain=f"{groups} פְּעָמִים {per} זֶה {total}.")


def gen_enum_tap(rng, qt):
    """משחק ספירה: לחצו על N עצמים."""
    target = rng.randint(3, 10)
    return Question(QType.TAP_COLLECT, Difficulty.EASY,
                    prompt=f"לַחֲצוּ עַל {target} עֲצָמִים.",
                    answer=list(range(target)),
                    payload={"bank": target + rng.randint(3, 6)})


# ============================================================
#  3. קריאה וכתיבה של המספרים
# ============================================================
def gen_read_word(rng, qt):
    """התאמה בין מספר במילים לספרה."""
    n = rng.choice([3, 4, 5, 6, 7, 8, 9, 10])
    return Question(QType.MULTIPLE_CHOICE, Difficulty.EASY,
                    prompt=f"אֵיזֶה מִסְפָּר כָּתוּב כָּאן: \"{NUM_WORDS[n]}\"?",
                    answer=n, options=_mc(rng, n, lo=0, hi=12, spread=(-2, -1, 1, 2)))


def gen_read_tens_units(rng, qt):
    """מבנה עשרוני: כמה עשרות וכמה יחידות."""
    n = rng.randint(11, 99)
    tens, units = divmod(n, 10)
    ask_tens = rng.random() < 0.5
    if ask_tens:
        return Question(QType.OPEN_NUMERIC, Difficulty.MEDIUM,
                        prompt=f"בַּמִּסְפָּר {n}, כַּמָּה עֲשָׂרוֹת יֵשׁ?", answer=tens,
                        explain=f"בְּ-{n} יֵשׁ {tens} עֲשָׂרוֹת וְ-{units} יְחִידוֹת.")
    return Question(QType.OPEN_NUMERIC, Difficulty.MEDIUM,
                    prompt=f"בַּמִּסְפָּר {n}, כַּמָּה יְחִידוֹת יֵשׁ?", answer=units,
                    explain=f"בְּ-{n} יֵשׁ {tens} עֲשָׂרוֹת וְ-{units} יְחִידוֹת.")


# ============================================================
#  4. סדרות
# ============================================================
def gen_seq_missing(rng, qt):
    """השלמת איבר חסר בסדרה חשבונית."""
    step = rng.choice([1, 2, 5, 10])
    start = rng.randint(0, 20)
    seq = [start + step * i for i in range(5)]
    hole = rng.randint(1, 3)
    missing = seq[hole]
    shown = [str(x) if i != hole else "___" for i, x in enumerate(seq)]
    return Question(QType.FILL_BLANK, Difficulty.MEDIUM,
                    prompt="אֵיזֶה מִסְפָּר חָסֵר בַּסִּדְרָה?  " + ", ".join(shown),
                    answer=missing, explain=f"הַסִּדְרָה עוֹלָה בְּ-{step} בְּכָל פַּעַם.")


def gen_seq_rule(rng, qt):
    """זיהוי חוקיות: באיזה דילוג הסדרה עולה."""
    step = rng.choice([2, 3, 5, 10])
    start = rng.randint(1, 10)
    seq = [start + step * i for i in range(4)]
    return Question(QType.OPEN_NUMERIC, Difficulty.CHALLENGE,
                    prompt=f"בְּכַמָּה עוֹלָה הַסִּדְרָה בְּכָל פַּעַם?  {seq[0]}, {seq[1]}, {seq[2]}, {seq[3]}",
                    answer=step, explain=f"כָּל מִסְפָּר גָּדוֹל בְּ-{step} מֵהַקּוֹדֵם.")


# ============================================================
#  5. ישר המספרים
# ============================================================
def gen_line_place(rng, qt):
    """איזה מספר מסומן על הישר (בין שתי שנתות)."""
    n = rng.randint(2, 98)
    return Question(QType.OPEN_NUMERIC, Difficulty.EASY,
                    prompt=f"עַל יְשַׁר הַמִּסְפָּרִים, אֵיזֶה מִסְפָּר נִמְצָא בֵּין {n-1} לְבֵין {n+1}?",
                    answer=n, explain=f"בֵּין {n-1} לְ-{n+1} נִמְצָא {n}.")


def gen_line_distance(rng, qt):
    """מרחק בין שני מספרים על הישר (הכנה לחיבור/חיסור)."""
    a = rng.randint(1, 15); b = a + rng.randint(1, 10)
    return Question(QType.OPEN_NUMERIC, Difficulty.MEDIUM,
                    prompt=f"כַּמָּה צְעָדִים יֵשׁ עַל הַיָּשָׁר מִ-{a} עַד {b}?",
                    answer=b - a, explain=f"מִ-{a} עַד {b} יֵשׁ {b-a} צְעָדִים.")


# ============================================================
#  6. סדר המספרים (השוואה < > =, וסידור)
# ============================================================
def gen_order_compare(rng, qt):
    a = rng.randint(0, 100); b = rng.randint(0, 100)
    while a == b:
        b = rng.randint(0, 100)
    ans = ">" if a > b else "<"
    return Question(QType.MULTIPLE_CHOICE, Difficulty.EASY,
                    prompt=f"אֵיזֶה סִימָן מַתְאִים?  {a} __ {b}",
                    answer=ans, options=[">", "<"],
                    payload={"cmp_a": a, "cmp_b": b},
                    explain="הַסִּימָן הַפָּתוּחַ פּוֹנֶה אֶל הַמִּסְפָּר הַגָּדוֹל.")


def gen_order_sort(rng, qt):
    """סידור מספרים מהקטן לגדול (משחקי, גרירה)."""
    vals = rng.sample(range(0, 100), 4)
    return Question(QType.ORDER_SEQUENCE, Difficulty.CHALLENGE,
                    prompt="סַדְּרוּ אֶת הַמִּסְפָּרִים מֵהַקָּטָן לַגָּדוֹל:",
                    answer=sorted(vals), payload={"tiles": rng.sample(vals, len(vals))},
                    explain="מַתְחִילִים מֵהַמִּסְפָּר הַקָּטָן בְּיוֹתֵר.")


def gen_order_biggest(rng, qt):
    """מצאו את הגדול/הקטן ביותר."""
    vals = rng.sample(range(0, 100), 4)
    biggest = rng.random() < 0.5
    ans = max(vals) if biggest else min(vals)
    word = "הַגָּדוֹל" if biggest else "הַקָּטָן"
    return Question(QType.MULTIPLE_CHOICE, Difficulty.MEDIUM,
                    prompt=f"אֵיזֶה הוּא הַמִּסְפָּר {word} בְּיוֹתֵר?",
                    answer=ans, options=rng.sample(vals, len(vals)),
                    explain=f"{ans} הוּא {word} בְּיוֹתֵר מִבֵּין הַמִּסְפָּרִים.")


# ============================================================
#  רישום כל התבניות
# ============================================================
def build_templates() -> list:
    return [
        # ספירה
        Template("count_next", N_COUNT, Difficulty.EASY,
                 [QType.MULTIPLE_CHOICE, QType.OPEN_NUMERIC], gen_count_next),
        Template("count_skip", N_COUNT, Difficulty.MEDIUM, [QType.OPEN_NUMERIC], gen_count_skip),
        # מנייה
        Template("enum_group", N_ENUM, Difficulty.MEDIUM, [QType.OPEN_NUMERIC], gen_enum_group),
        Template("enum_tap", N_ENUM, Difficulty.EASY, [QType.TAP_COLLECT], gen_enum_tap),
        # קריאה וכתיבה
        Template("read_word", N_READ, Difficulty.EASY, [QType.MULTIPLE_CHOICE], gen_read_word),
        Template("read_tens_units", N_READ, Difficulty.MEDIUM, [QType.OPEN_NUMERIC], gen_read_tens_units),
        # סדרות
        Template("seq_missing", N_SEQ, Difficulty.MEDIUM, [QType.FILL_BLANK], gen_seq_missing),
        Template("seq_rule", N_SEQ, Difficulty.CHALLENGE, [QType.OPEN_NUMERIC], gen_seq_rule),
        # ישר המספרים
        Template("line_place", N_LINE, Difficulty.EASY, [QType.OPEN_NUMERIC], gen_line_place),
        Template("line_distance", N_LINE, Difficulty.MEDIUM, [QType.OPEN_NUMERIC], gen_line_distance),
        # סדר המספרים
        Template("order_compare", N_ORDER, Difficulty.EASY, [QType.MULTIPLE_CHOICE], gen_order_compare),
        Template("order_biggest", N_ORDER, Difficulty.MEDIUM, [QType.MULTIPLE_CHOICE], gen_order_biggest),
        Template("order_sort", N_ORDER, Difficulty.CHALLENGE, [QType.ORDER_SEQUENCE], gen_order_sort),
    ]


# מיפוי נושא -> תבניות (לבחירת תרגול לפי הצומת שהתלמיד נמצא בו)
def templates_for_node(node_id: str) -> list:
    return [t for t in build_templates() if t.node_id == node_id]
