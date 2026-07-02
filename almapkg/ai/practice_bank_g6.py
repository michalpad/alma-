"""
ALMA — בנק תרגול מלא לכיתה ו' (מתמטיקה).
מכסה את כל נושאי כיתה ו' מתכנית הלימודים, בכל רמות הקושי.
כל מחולל מחשב את תשובתו הנכונה -> נכונות מובטחת בשרת.

נושאים (תואם 07_מתמטיקה_כיתה_ו.sql):
  עולם המספרים: ארבע פעולות וסדר, יחסי הכלה בין קבוצות המספרים
  שברים פשוטים: כפל שברים, חילוק שברים, חלק של כמות
  שברים עשרוניים: כפל/חילוק ב-10/100, כפל/חילוק עשרוני, מחזורי/צפיפות
  אחוזים: חישוב אחוז וערך האחוז
  יחס: הגדרת היחס, חלוקה לפי יחס (חשיבה פרופורציונית)
  גאומטריה: מעגל ועיגול, נפח ויחידות נפח, גופים ופריסות
"""
from __future__ import annotations

import random
from fractions import Fraction
from math import gcd

from .practice_engine import Question, QType, Difficulty, Template

# ---- מזהי צמתים (כיתה ו') ----
N_OPS = "f1000000-0000-4000-8000-000000000010"       # ארבע פעולות וסדר
N_SETS = "f1000000-0000-4000-8000-000000000020"      # יחסי הכלה בין קבוצות
N_FMUL = "f2000000-0000-4000-8000-000000000010"      # כפל שברים
N_FDIV = "f2000000-0000-4000-8000-000000000020"      # חילוק שברים
N_PART = "f2000000-0000-4000-8000-000000000030"      # חלק של כמות
N_DEC10 = "f3000000-0000-4000-8000-000000000010"     # כפל/חילוק ב-10/100
N_DECMUL = "f3000000-0000-4000-8000-000000000020"    # כפל/חילוק עשרוני
N_DECREP = "f3000000-0000-4000-8000-000000000030"    # מחזורי/צפיפות
N_PCT = "f4000000-0000-4000-8000-000000000010"       # חישוב אחוז
N_RATIO = "f5000000-0000-4000-8000-000000000010"     # הגדרת היחס
N_RATIODIV = "f5000000-0000-4000-8000-000000000020"  # חלוקה לפי יחס
N_CIRCLE = "f6000000-0000-4000-8000-000000000010"    # מעגל ועיגול
N_VOL = "f6000000-0000-4000-8000-000000000020"       # נפח
N_SOLIDS = "f6000000-0000-4000-8000-000000000030"    # גופים ופריסות


def _mc(rng, correct, lo=0, hi=100000, k=4, spread=(-100, -10, -5, -2, -1, 1, 2, 5, 10, 100)):
    opts = {correct}; g = 0
    while len(opts) < k and g < 120:
        v = correct + rng.choice(spread); g += 1
        if lo <= v <= hi:
            opts.add(v)
    opts = list(opts); rng.shuffle(opts)
    return opts


# ============================================================
#  עולם המספרים: פעולות וסדר, יחסי הכלה
# ============================================================
def gen_order(rng, qt):
    a = rng.randint(2, 12); b = rng.randint(2, 12); c = rng.randint(2, 30); d = rng.randint(2, 9)
    ans = c + a * b - d      # כפל קודם
    return Question(QType.OPEN_NUMERIC, Difficulty.MEDIUM,
                    prompt=f"לְפִי סֵדֶר הַפְּעוּלוֹת: {c} + {a} × {b} - {d} = ?", answer=ans)


def gen_sets(rng, qt):
    q = rng.choice([
        ("הַאִם הַמִּסְפָּר 7 שַׁיָּךְ לַמִּסְפָּרִים הַטִּבְעִיִּים?", "כן"),
        ("הַאִם 1/2 הוּא מִסְפָּר טִבְעִי?", "לא"),
        ("הַאִם כָּל מִסְפָּר טִבְעִי הוּא גַּם מִסְפָּר שָׁלֵם?", "כן"),
    ])
    return Question(QType.MULTIPLE_CHOICE, Difficulty.CHALLENGE,
                    prompt=q[0], answer=q[1], options=["כן", "לא"])


# ============================================================
#  כפל שברים
# ============================================================
def gen_fmul(rng, qt):
    n1 = rng.randint(1, 5); d1 = rng.randint(2, 8)
    n2 = rng.randint(1, 5); d2 = rng.randint(2, 8)
    res = Fraction(n1, d1) * Fraction(n2, d2)
    ans = f"{res.numerator}/{res.denominator}" if res.denominator != 1 else str(res.numerator)
    return Question(QType.OPEN_TEXT, Difficulty.MEDIUM,
                    prompt=f"חַשְּׁבוּ (מוֹנֶה/מְכַנֶּה): {n1}/{d1} × {n2}/{d2} =", answer=ans)


def gen_fmul_whole(rng, qt):
    w = rng.randint(2, 8); n = rng.randint(1, 5); d = rng.randint(2, 8)
    res = w * Fraction(n, d)
    ans = f"{res.numerator}/{res.denominator}" if res.denominator != 1 else str(res.numerator)
    return Question(QType.OPEN_TEXT, Difficulty.EASY,
                    prompt=f"חַשְּׁבוּ (מוֹנֶה/מְכַנֶּה): {w} × {n}/{d} =", answer=ans)


# ============================================================
#  חילוק שברים
# ============================================================
def gen_fdiv(rng, qt):
    n1 = rng.randint(1, 5); d1 = rng.randint(2, 8)
    n2 = rng.randint(1, 5); d2 = rng.randint(2, 8)
    res = Fraction(n1, d1) / Fraction(n2, d2)
    ans = f"{res.numerator}/{res.denominator}" if res.denominator != 1 else str(res.numerator)
    return Question(QType.OPEN_TEXT, Difficulty.CHALLENGE,
                    prompt=f"חַשְּׁבוּ (מוֹנֶה/מְכַנֶּה): {n1}/{d1} : {n2}/{d2} =", answer=ans)


# ============================================================
#  חלק של כמות
# ============================================================
def gen_part(rng, qt):
    d = rng.choice([2, 3, 4, 5, 6]); n = rng.randint(1, d - 1)
    whole = d * rng.randint(2, 12)   # מתחלק יפה
    ans = whole * n // d
    return Question(QType.OPEN_NUMERIC, Difficulty.MEDIUM,
                    prompt=f"כַּמָּה הוּא {n}/{d} מִתּוֹךְ {whole}?", answer=ans)


def gen_part_reverse(rng, qt):
    # נתון החלק, מצא את השלם: אם 1/4 מכמות הוא X, מהי הכמות?
    d = rng.choice([2, 3, 4, 5]); part = rng.randint(2, 15)
    ans = part * d
    return Question(QType.OPEN_NUMERIC, Difficulty.CHALLENGE,
                    prompt=f"1/{d} מִכַּמּוּת מְסֻיֶּמֶת הוּא {part}. מַהִי הַכַּמּוּת הַשְּׁלֵמָה?", answer=ans)


# ============================================================
#  שברים עשרוניים: כפל/חילוק ב-10/100
# ============================================================
def gen_dec10(rng, qt):
    val = round(rng.uniform(1, 90), 2)
    mult = rng.choice([10, 100])
    op = rng.choice(["×", ":"])
    ans = round(val * mult, 4) if op == "×" else round(val / mult, 4)
    return Question(QType.OPEN_NUMERIC, Difficulty.MEDIUM,
                    prompt=f"חַשְּׁבוּ: {val} {op} {mult} =", answer=ans)


# ============================================================
#  כפל/חילוק עשרוני
# ============================================================
def gen_decmul(rng, qt):
    a = round(rng.uniform(0.2, 9.9), 1); b = round(rng.uniform(0.2, 9.9), 1)
    ans = round(a * b, 2)
    return Question(QType.OPEN_NUMERIC, Difficulty.CHALLENGE,
                    prompt=f"חַשְּׁבוּ: {a} × {b} =", answer=ans)


def gen_decdiv(rng, qt):
    b = round(rng.uniform(0.2, 5), 1)
    q = rng.randint(2, 20)
    a = round(b * q, 2)
    ans = q
    return Question(QType.OPEN_NUMERIC, Difficulty.CHALLENGE,
                    prompt=f"חַשְּׁבוּ: {a} : {b} =", answer=ans)


# ============================================================
#  מחזורי / צפיפות
# ============================================================
def gen_density(rng, qt):
    # בין שני שברים עשרוניים תמיד יש עוד — מושג הצפיפות
    a = round(rng.uniform(0.1, 0.8), 1)
    b = round(a + 0.1, 1)
    mid = round((a + b) / 2, 2)
    return Question(QType.OPEN_NUMERIC, Difficulty.CHALLENGE,
                    prompt=f"אֵיזֶה מִסְפָּר עֶשְׂרוֹנִי נִמְצָא בְּדִיּוּק בָּאֶמְצַע בֵּין {a} לְ- {b}?", answer=mid)


# ============================================================
#  אחוזים
# ============================================================
def gen_pct_of(rng, qt):
    pct = rng.choice([10, 20, 25, 50, 75])
    whole = rng.choice([20, 40, 60, 80, 100, 200])
    ans = whole * pct // 100
    return Question(QType.OPEN_NUMERIC, Difficulty.MEDIUM,
                    prompt=f"כַּמָּה הוּא {pct}% מִתּוֹךְ {whole}?", answer=ans)


def gen_pct_find(rng, qt):
    whole = rng.choice([20, 40, 50, 100, 200]); pct = rng.choice([10, 25, 50])
    part = whole * pct // 100
    ans = pct
    return Question(QType.OPEN_NUMERIC, Difficulty.CHALLENGE,
                    prompt=f"{part} הוּא אֵיזֶה אָחוּז מִתּוֹךְ {whole}? (כִּתְבוּ אֶת הַמִּסְפָּר בִּלְבַד)", answer=ans)


# ============================================================
#  יחס וחשיבה פרופורציונית
# ============================================================
def gen_ratio(rng, qt):
    # יחס שווה ערך: 2:3 = 4:? 
    a = rng.randint(1, 5); b = rng.randint(1, 5); k = rng.randint(2, 5)
    ans = b * k
    return Question(QType.OPEN_NUMERIC, Difficulty.MEDIUM,
                    prompt=f"הַשְׁלִימוּ אֶת הַיַּחַס הַשָּׁוֶה: {a}:{b} = {a * k}:?", answer=ans)


def gen_ratio_div(rng, qt):
    # חלוקה לפי יחס: חלק כמות לפי יחס נתון
    total = rng.choice([10, 15, 20, 25, 30, 12, 18])
    r1 = rng.randint(1, 3); r2 = rng.randint(1, 3)
    while (total % (r1 + r2)) != 0:
        total += (r1 + r2) - (total % (r1 + r2))
    part1 = total * r1 // (r1 + r2)
    return Question(QType.OPEN_NUMERIC, Difficulty.CHALLENGE,
                    prompt=f"חִלְּקוּ {total} לְפִי הַיַּחַס {r1}:{r2}. מַהוּ הַחֵלֶק הָרִאשׁוֹן?", answer=part1)


# ============================================================
#  מעגל ועיגול
# ============================================================
def gen_circle(rng, qt):
    r = rng.randint(2, 20)
    ans = r * 2      # קוטר = רדיוס × 2
    return Question(QType.OPEN_NUMERIC, Difficulty.EASY,
                    prompt=f"רַדְיוּס שֶׁל עִגּוּל הוּא {r}. מַהוּ הַקֹּטֶר?", answer=ans)


def gen_circle_r(rng, qt):
    diam = rng.choice([4, 6, 8, 10, 12, 14, 20])
    ans = diam // 2
    return Question(QType.OPEN_NUMERIC, Difficulty.EASY,
                    prompt=f"קֹטֶר שֶׁל עִגּוּל הוּא {diam}. מַהוּ הָרַדְיוּס?", answer=ans)


# ============================================================
#  נפח
# ============================================================
def gen_volume(rng, qt):
    a = rng.randint(2, 12); b = rng.randint(2, 12); c = rng.randint(2, 12)
    ans = a * b * c
    return Question(QType.OPEN_NUMERIC, Difficulty.MEDIUM,
                    prompt=f"מַהוּ נֶפַח תֵּיבָה שֶׁמִּדּוֹתֶיהָ {a} × {b} × {c}?", answer=ans)


def gen_volume_unit(rng, qt):
    q = rng.choice([
        ("כַּמָּה סֶנְטִימֶטְרִים מְעֻקָּבִים יֵשׁ בְּלִיטֶר אֶחָד?", 1000),
        ("קֻבִּיָּה שֶׁכָּל צֵלַע שֶׁלָּהּ 1 סֶמ. מַהוּ נַפְחָהּ (בְּסמ\"ק)?", 1),
    ])
    return Question(QType.OPEN_NUMERIC, Difficulty.MEDIUM, prompt=q[0], answer=q[1])


# ============================================================
#  גופים ופריסות
# ============================================================
def gen_solids(rng, qt):
    q = rng.choice([
        ("כַּמָּה פֵּאוֹת יֵשׁ לְקֻבִּיָּה?", 6),
        ("כַּמָּה קָדְקֹדִים יֵשׁ לְתֵיבָה?", 8),
        ("כַּמָּה מִקְצוֹעוֹת (צְלָעוֹת) יֵשׁ לְקֻבִּיָּה?", 12),
    ])
    return Question(QType.OPEN_NUMERIC, Difficulty.MEDIUM, prompt=q[0], answer=q[1])


# ============================================================
#  רישום התבניות
# ============================================================
def build_templates():
    return [
        Template("g6_order", N_OPS, Difficulty.MEDIUM, [QType.OPEN_NUMERIC], gen_order),
        Template("g6_sets", N_SETS, Difficulty.CHALLENGE, [QType.MULTIPLE_CHOICE], gen_sets),
        Template("g6_fmul", N_FMUL, Difficulty.MEDIUM, [QType.OPEN_TEXT], gen_fmul),
        Template("g6_fmul_whole", N_FMUL, Difficulty.EASY, [QType.OPEN_TEXT], gen_fmul_whole),
        Template("g6_fdiv", N_FDIV, Difficulty.CHALLENGE, [QType.OPEN_TEXT], gen_fdiv),
        Template("g6_part", N_PART, Difficulty.MEDIUM, [QType.OPEN_NUMERIC], gen_part),
        Template("g6_part_reverse", N_PART, Difficulty.CHALLENGE, [QType.OPEN_NUMERIC], gen_part_reverse),
        Template("g6_dec10", N_DEC10, Difficulty.MEDIUM, [QType.OPEN_NUMERIC], gen_dec10),
        Template("g6_decmul", N_DECMUL, Difficulty.CHALLENGE, [QType.OPEN_NUMERIC], gen_decmul),
        Template("g6_decdiv", N_DECMUL, Difficulty.CHALLENGE, [QType.OPEN_NUMERIC], gen_decdiv),
        Template("g6_density", N_DECREP, Difficulty.CHALLENGE, [QType.OPEN_NUMERIC], gen_density),
        Template("g6_pct_of", N_PCT, Difficulty.MEDIUM, [QType.OPEN_NUMERIC], gen_pct_of),
        Template("g6_pct_find", N_PCT, Difficulty.CHALLENGE, [QType.OPEN_NUMERIC], gen_pct_find),
        Template("g6_ratio", N_RATIO, Difficulty.MEDIUM, [QType.OPEN_NUMERIC], gen_ratio),
        Template("g6_ratio_div", N_RATIODIV, Difficulty.CHALLENGE, [QType.OPEN_NUMERIC], gen_ratio_div),
        Template("g6_circle", N_CIRCLE, Difficulty.EASY, [QType.OPEN_NUMERIC], gen_circle),
        Template("g6_circle_r", N_CIRCLE, Difficulty.EASY, [QType.OPEN_NUMERIC], gen_circle_r),
        Template("g6_volume", N_VOL, Difficulty.MEDIUM, [QType.OPEN_NUMERIC], gen_volume),
        Template("g6_volume_unit", N_VOL, Difficulty.MEDIUM, [QType.OPEN_NUMERIC], gen_volume_unit),
        Template("g6_solids", N_SOLIDS, Difficulty.MEDIUM, [QType.OPEN_NUMERIC], gen_solids),
    ]
