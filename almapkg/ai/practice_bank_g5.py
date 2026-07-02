"""
ALMA — בנק תרגול מלא לכיתה ה' (מתמטיקה).
מכסה את כל נושאי כיתה ה' מתכנית הלימודים, בכל רמות הקושי.
כל מחולל מחשב את תשובתו הנכונה -> נכונות מובטחת בשרת.

נושאים (תואם 06_מתמטיקה_כיתה_ה.sql):
  מספרים טבעיים: ארבע פעולות וחוקי הפעולות, סדר פעולות ואומדן
  שברים: צמצום והרחבה, חיבור וחיסור שברים
  שברים עשרוניים: הכרה, פעולות והשוואה, מעבר שבר<->עשרוני, אחוז היכרות
  גאומטריה: מרובעים (תכונות/מיון/הכלה), סימטריה וריצוף, שטח ונוסחאות
  חקר נתונים: ייצוג וניתוח, ממוצע
"""
from __future__ import annotations

import random
from fractions import Fraction
from math import gcd

from .practice_engine import Question, QType, Difficulty, Template

# ---- מזהי צמתים (כיתה ה') ----
N_OPS = "e1000000-0000-4000-8000-000000000010"      # ארבע פעולות וחוקי הפעולות
N_ORDER = "e1000000-0000-4000-8000-000000000020"    # סדר פעולות ואומדן
N_REDUCE = "e2000000-0000-4000-8000-000000000010"   # צמצום והרחבה
N_FRACADD = "e2000000-0000-4000-8000-000000000020"  # חיבור/חיסור שברים
N_DEC = "e3000000-0000-4000-8000-000000000010"      # הכרת השבר העשרוני
N_DECOP = "e3000000-0000-4000-8000-000000000020"    # פעולות והשוואה בעשרוני
N_CONV = "e3000000-0000-4000-8000-000000000030"     # מעבר שבר<->עשרוני
N_PCT = "e3000000-0000-4000-8000-000000000040"      # אחוז - היכרות
N_QUAD = "e4000000-0000-4000-8000-000000000010"     # מרובעים
N_SYM = "e4000000-0000-4000-8000-000000000020"      # סימטריה וריצוף
N_AREA = "e4000000-0000-4000-8000-000000000030"     # גבהים, שטח ונוסחאות
N_DATA = "e5000000-0000-4000-8000-000000000010"     # חקר נתונים


def _mc(rng, correct, lo=0, hi=100000, k=4, spread=(-100, -10, -5, -2, -1, 1, 2, 5, 10, 100)):
    opts = {correct}; g = 0
    while len(opts) < k and g < 120:
        v = correct + rng.choice(spread); g += 1
        if lo <= v <= hi:
            opts.add(v)
    opts = list(opts); rng.shuffle(opts)
    return opts


# ============================================================
#  מספרים טבעיים: ארבע פעולות וחוקי הפעולות
# ============================================================
def gen_ops(rng, qt):
    op = rng.choice(["+", "-", "*"])
    if op == "+":
        a, b = rng.randint(1000, 99000), rng.randint(1000, 9000)
        ans = a + b
    elif op == "-":
        a = rng.randint(10000, 99000); b = rng.randint(1000, a - 1)
        ans = a - b
    else:
        a, b = rng.randint(12, 99), rng.randint(12, 99)
        ans = a * b
    return Question(QType.OPEN_NUMERIC, Difficulty.MEDIUM,
                    prompt=f"כַּמָּה זֶה {a} {op.replace('*','×')} {b}?", answer=ans)


def gen_law(rng, qt):
    # חוק הפילוג: a×(b+c) = a×b + a×c
    a = rng.randint(3, 9); b = rng.randint(10, 40); c = rng.randint(2, 9)
    ans = a * (b + c)
    return Question(QType.OPEN_NUMERIC, Difficulty.CHALLENGE,
                    prompt=f"לְפִי חֹק הַפִּילּוּג: {a} × ({b} + {c}) = ?", answer=ans)


# ============================================================
#  סדר פעולות ואומדן
# ============================================================
def gen_order(rng, qt):
    a = rng.randint(2, 9); b = rng.randint(2, 9); c = rng.randint(2, 20)
    ans = c + a * b   # כפל לפני חיבור
    return Question(QType.OPEN_NUMERIC, Difficulty.MEDIUM,
                    prompt=f"לְפִי סֵדֶר הַפְּעוּלוֹת: {c} + {a} × {b} = ?", answer=ans)


def gen_estimate(rng, qt):
    a = rng.randint(180, 820); b = rng.randint(180, 820)
    ra, rb = round(a, -2), round(b, -2)
    ans = ra + rb
    opts = _mc(rng, ans, lo=200, hi=2000, spread=(-200, -100, 100, 200))
    return Question(QType.MULTIPLE_CHOICE, Difficulty.MEDIUM,
                    prompt=f"אֹמֶד (עִגּוּל לְמֵאוֹת): {a} + {b} קָרוֹב בְּיוֹתֵר לְ...",
                    answer=ans, options=[str(o) for o in opts])


# ============================================================
#  שברים: צמצום והרחבה
# ============================================================
def gen_reduce(rng, qt):
    d = rng.randint(2, 6); base_n = rng.randint(1, 4); base_d = base_n + rng.randint(1, 5)
    n, den = base_n * d, base_d * d
    g = gcd(n, den)
    ans_n, ans_d = n // g, den // g
    return Question(QType.OPEN_TEXT, Difficulty.MEDIUM,
                    prompt=f"צַמְצְמוּ אֶת הַשֶּׁבֶר {n}/{den} לַצּוּרָה הַפְּשׁוּטָה בְּיוֹתֵר (כִּתְבוּ כְּ- מוֹנֶה/מְכַנֶּה):",
                    answer=f"{ans_n}/{ans_d}")


def gen_expand(rng, qt):
    n = rng.randint(1, 4); d = n + rng.randint(1, 5); f = rng.randint(2, 5)
    ans = n * f
    return Question(QType.OPEN_NUMERIC, Difficulty.EASY,
                    prompt=f"הַרְחִיבוּ: {n}/{d} = ?/{d * f}. מַהוּ הַמּוֹנֶה הֶחָדָשׁ?", answer=ans)


# ============================================================
#  חיבור וחיסור שברים
# ============================================================
def gen_fracadd(rng, qt):
    d = rng.choice([4, 5, 6, 8, 10, 12])
    a = rng.randint(1, d - 1); b = rng.randint(1, d - 1)
    op = rng.choice(["+", "-"])
    if op == "-" and a < b:
        a, b = b, a
    res = Fraction(a, d) + (Fraction(b, d) if op == "+" else -Fraction(b, d))
    ans = f"{res.numerator}/{res.denominator}" if res.denominator != 1 else str(res.numerator)
    return Question(QType.OPEN_TEXT, Difficulty.MEDIUM,
                    prompt=f"חַשְּׁבוּ (כִּתְבוּ מוֹנֶה/מְכַנֶּה): {a}/{d} {op} {b}/{d} =",
                    answer=ans)


def gen_fracadd_diff(rng, qt):
    # מכנים שונים אך קרובים (אחד כפולה של השני)
    d1 = rng.choice([2, 3, 4]); d2 = d1 * rng.choice([2, 3])
    a = rng.randint(1, d1 - 1) if d1 > 1 else 1
    b = rng.randint(1, d2 - 1)
    res = Fraction(a, d1) + Fraction(b, d2)
    ans = f"{res.numerator}/{res.denominator}" if res.denominator != 1 else str(res.numerator)
    return Question(QType.OPEN_TEXT, Difficulty.CHALLENGE,
                    prompt=f"חַבְּרוּ (מְכַנֶּה מְשֻׁתָּף): {a}/{d1} + {b}/{d2} =",
                    answer=ans)


# ============================================================
#  שברים עשרוניים
# ============================================================
def gen_dec_read(rng, qt):
    whole = rng.randint(0, 9); tenths = rng.randint(0, 9); hund = rng.randint(0, 9)
    val = f"{whole}.{tenths}{hund}"
    place = rng.choice(["עֲשִׂירִיּוֹת", "מֵאִיּוֹת"])
    ans = tenths if place == "עֲשִׂירִיּוֹת" else hund
    return Question(QType.OPEN_NUMERIC, Difficulty.MEDIUM,
                    prompt=f"בַּמִּסְפָּר {val}, מַהִי סִפְרַת הָ{place}?", answer=ans)


def gen_dec_op(rng, qt):
    a = round(rng.uniform(1, 50), 1); b = round(rng.uniform(1, 30), 1)
    op = rng.choice(["+", "-"])
    if op == "-" and a < b:
        a, b = b, a
    ans = round(a + b if op == "+" else a - b, 1)
    return Question(QType.OPEN_NUMERIC, Difficulty.MEDIUM,
                    prompt=f"חַשְּׁבוּ: {a} {op} {b} =", answer=ans)


def gen_dec_compare(rng, qt):
    a = round(rng.uniform(0.1, 9.9), 2); b = round(rng.uniform(0.1, 9.9), 2)
    while a == b:
        b = round(rng.uniform(0.1, 9.9), 2)
    ans = ">" if a > b else "<"
    return Question(QType.MULTIPLE_CHOICE, Difficulty.EASY,
                    prompt=f"אֵיזֶה סִימָן מַתְאִים? {a} __ {b}",
                    answer=ans, options=[">", "<"])


def gen_dec_round(rng, qt):
    val = round(rng.uniform(1, 99), 2)
    ans = round(val)
    return Question(QType.OPEN_NUMERIC, Difficulty.MEDIUM,
                    prompt=f"עַגְּלוּ אֶת {val} לַמִּסְפָּר הַשָּׁלֵם הַקָּרוֹב:", answer=ans)


# ============================================================
#  מעבר שבר <-> עשרוני
# ============================================================
def gen_conv(rng, qt):
    d, dec = rng.choice([(2, "0.5"), (4, "0.25"), (5, "0.2"), (10, "0.1"), (100, "0.01")])
    n = 1
    return Question(QType.OPEN_TEXT, Difficulty.MEDIUM,
                    prompt=f"כִּתְבוּ אֶת הַשֶּׁבֶר {n}/{d} כְּשֶׁבֶר עֶשְׂרוֹנִי:", answer=dec)


# ============================================================
#  אחוז - היכרות
# ============================================================
def gen_pct_intro(rng, qt):
    # אחוז כחלק ממאה: X% מתוך 100
    pct = rng.choice([10, 20, 25, 50, 75])
    ans = pct
    return Question(QType.OPEN_NUMERIC, Difficulty.EASY,
                    prompt=f"{pct}% מִתּוֹךְ 100 שָׁוֶה לְ...?", answer=ans)


def gen_pct_frac(rng, qt):
    pct, frac = rng.choice([(50, "1/2"), (25, "1/4"), (10, "1/10"), (20, "1/5"), (75, "3/4")])
    return Question(QType.OPEN_TEXT, Difficulty.MEDIUM,
                    prompt=f"אֵיזֶה שֶׁבֶר פָּשׁוּט שָׁוֶה לְ- {pct}%? (מוֹנֶה/מְכַנֶּה)", answer=frac)


# ============================================================
#  גאומטריה: מרובעים
# ============================================================
def gen_quad(rng, qt):
    q = rng.choice([
        ("לְאֵיזֶה מְרֻבָּע כָּל הַזָּוִיּוֹת יְשָׁרוֹת וְכָל הַצְּלָעוֹת שָׁווֹת?", "ריבוע",
         ["ריבוע", "מלבן", "מקבילית", "טרפז"]),
        ("לְאֵיזֶה מְרֻבָּע יֵשׁ שְׁתֵּי זוּגוֹת צְלָעוֹת מַקְבִּילוֹת וְכָל הַזָּוִיּוֹת יְשָׁרוֹת?", "מלבן",
         ["מלבן", "מעוין", "טרפז", "משולש"]),
        ("לְאֵיזֶה מְרֻבָּע יֵשׁ בְּדִיּוּק זוּג אֶחָד שֶׁל צְלָעוֹת מַקְבִּילוֹת?", "טרפז",
         ["טרפז", "ריבוע", "מלבן", "מקבילית"]),
    ])
    return Question(QType.MULTIPLE_CHOICE, Difficulty.MEDIUM,
                    prompt=q[0], answer=q[1], options=q[2])


def gen_quad_incl(rng, qt):
    # קשרי הכלה: כל ריבוע הוא גם...
    q = rng.choice([
        ("נָכוֹן אוֹ לֹא נָכוֹן: כָּל רִבּוּעַ הוּא גַּם מַלְבֵּן.", "נכון"),
        ("נָכוֹן אוֹ לֹא נָכוֹן: כָּל מַלְבֵּן הוּא רִבּוּעַ.", "לא נכון"),
        ("נָכוֹן אוֹ לֹא נָכוֹן: כָּל רִבּוּעַ הוּא גַּם מְעֻיָּן.", "נכון"),
    ])
    return Question(QType.MULTIPLE_CHOICE, Difficulty.CHALLENGE,
                    prompt=q[0], answer=q[1], options=["נכון", "לא נכון"])


# ============================================================
#  שטח ונוסחאות
# ============================================================
def gen_area_rect(rng, qt):
    w = rng.randint(3, 20); h = rng.randint(3, 20)
    ans = w * h
    return Question(QType.OPEN_NUMERIC, Difficulty.MEDIUM,
                    prompt=f"מַהוּ שֶׁטַח מַלְבֵּן שֶׁאָרְכּוֹ {w} וְרָחְבּוֹ {h}?", answer=ans)


def gen_area_tri(rng, qt):
    base = rng.choice([4, 6, 8, 10, 12]); h = rng.choice([3, 5, 7, 9])
    ans = base * h // 2 if (base * h) % 2 == 0 else base * h / 2
    return Question(QType.OPEN_NUMERIC, Difficulty.CHALLENGE,
                    prompt=f"מַהוּ שֶׁטַח מְשֻׁלָּשׁ שֶׁבְּסִיסוֹ {base} וְגָבְהוֹ {h}? (בָּסִיס × גֹּבַהּ ÷ 2)",
                    answer=ans)


# ============================================================
#  סימטריה
# ============================================================
def gen_symmetry(rng, qt):
    shape, axes = rng.choice([("רִבּוּעַ", 4), ("מַלְבֵּן", 2), ("מְשֻׁלָּשׁ שְׁוֵה־צְלָעוֹת", 3),
                              ("מַעְגָּל", "אֵינְסוֹף")])
    ans = str(axes)
    if axes == "אֵינְסוֹף":
        return Question(QType.MULTIPLE_CHOICE, Difficulty.MEDIUM,
                        prompt=f"כַּמָּה צִירֵי סִימֶטְרִיָּה יֵשׁ לְ{shape}?",
                        answer="אינסוף", options=["2", "4", "אינסוף"])
    return Question(QType.OPEN_NUMERIC, Difficulty.MEDIUM,
                    prompt=f"כַּמָּה צִירֵי סִימֶטְרִיָּה יֵשׁ לְ{shape}?", answer=axes)


# ============================================================
#  חקר נתונים: ממוצע
# ============================================================
def gen_average(rng, qt):
    n = rng.choice([3, 4, 5])
    vals = [rng.randint(2, 20) for _ in range(n)]
    # נוודא שהסכום מתחלק כדי לקבל ממוצע שלם
    total = sum(vals)
    while total % n != 0:
        vals[0] += 1; total = sum(vals)
    ans = total // n
    return Question(QType.OPEN_NUMERIC, Difficulty.MEDIUM,
                    prompt=f"מַהוּ הַמְּמֻצָּע שֶׁל הַמִּסְפָּרִים {', '.join(map(str, vals))}?", answer=ans)


# ============================================================
#  רישום התבניות
# ============================================================
def build_templates():
    return [
        Template("g5_ops", N_OPS, Difficulty.MEDIUM, [QType.OPEN_NUMERIC], gen_ops),
        Template("g5_law", N_OPS, Difficulty.CHALLENGE, [QType.OPEN_NUMERIC], gen_law),
        Template("g5_order", N_ORDER, Difficulty.MEDIUM, [QType.OPEN_NUMERIC], gen_order),
        Template("g5_estimate", N_ORDER, Difficulty.MEDIUM, [QType.MULTIPLE_CHOICE], gen_estimate),
        Template("g5_reduce", N_REDUCE, Difficulty.MEDIUM, [QType.OPEN_TEXT], gen_reduce),
        Template("g5_expand", N_REDUCE, Difficulty.EASY, [QType.OPEN_NUMERIC], gen_expand),
        Template("g5_fracadd", N_FRACADD, Difficulty.MEDIUM, [QType.OPEN_TEXT], gen_fracadd),
        Template("g5_fracadd_diff", N_FRACADD, Difficulty.CHALLENGE, [QType.OPEN_TEXT], gen_fracadd_diff),
        Template("g5_dec_read", N_DEC, Difficulty.MEDIUM, [QType.OPEN_NUMERIC], gen_dec_read),
        Template("g5_dec_op", N_DECOP, Difficulty.MEDIUM, [QType.OPEN_NUMERIC], gen_dec_op),
        Template("g5_dec_compare", N_DECOP, Difficulty.EASY, [QType.MULTIPLE_CHOICE], gen_dec_compare),
        Template("g5_dec_round", N_DECOP, Difficulty.MEDIUM, [QType.OPEN_NUMERIC], gen_dec_round),
        Template("g5_conv", N_CONV, Difficulty.MEDIUM, [QType.OPEN_TEXT], gen_conv),
        Template("g5_pct_intro", N_PCT, Difficulty.EASY, [QType.OPEN_NUMERIC], gen_pct_intro),
        Template("g5_pct_frac", N_PCT, Difficulty.MEDIUM, [QType.OPEN_TEXT], gen_pct_frac),
        Template("g5_quad", N_QUAD, Difficulty.MEDIUM, [QType.MULTIPLE_CHOICE], gen_quad),
        Template("g5_quad_incl", N_QUAD, Difficulty.CHALLENGE, [QType.MULTIPLE_CHOICE], gen_quad_incl),
        Template("g5_area_rect", N_AREA, Difficulty.MEDIUM, [QType.OPEN_NUMERIC], gen_area_rect),
        Template("g5_area_tri", N_AREA, Difficulty.CHALLENGE, [QType.OPEN_NUMERIC], gen_area_tri),
        Template("g5_symmetry", N_SYM, Difficulty.MEDIUM, [QType.OPEN_NUMERIC, QType.MULTIPLE_CHOICE], gen_symmetry),
        Template("g5_average", N_DATA, Difficulty.MEDIUM, [QType.OPEN_NUMERIC], gen_average),
    ]
