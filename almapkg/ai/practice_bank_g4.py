"""
ALMA — בנק תרגול מלא לכיתה ד' (מתמטיקה).
מכסה את כל נושאי כיתה ד' מתכנית הלימודים, בכל רמות הקושי.
כל מחולל מחשב את תשובתו הנכונה -> נכונות מובטחת בשרת.

נושאים (תואם math_grade4_curriculum.sql):
  מספרים עד מיליון
  פעולות: חיבור/חיסור, כפל, חילוק, סימני התחלקות 3/6/9, סדר פעולות
  שברים: הכרת שברים ומשמעויותיו, פעולות בשברים
  גאומטריה: מקבילות/מאונכות, אלכסונים, מרובעים, יחידות אורך
  שטח פנים של תיבה, לוח שנה, חקר נתונים (דיאגרמת עוגה)
"""
from __future__ import annotations

import random
from fractions import Fraction
from math import gcd

from .practice_engine import Question, QType, Difficulty, Template

# ---- מזהי צמתים (כיתה ד') ----
N_MIL = "d1000000-0000-4000-8000-000000000010"     # מספרים עד מיליון
N_ADDSUB = "d2000000-0000-4000-8000-000000000010"  # חיבור/חיסור עד מיליון
N_MUL = "d2000000-0000-4000-8000-000000000020"     # כפל
N_DIV = "d2000000-0000-4000-8000-000000000030"     # חילוק
N_DIVRULE = "d2000000-0000-4000-8000-000000000040" # סימני התחלקות 3/6/9
N_ORDER = "d2000000-0000-4000-8000-000000000050"   # סדר פעולות
N_FRAC = "d3000000-0000-4000-8000-000000000010"    # הכרת שברים
N_FRACOP = "d3000000-0000-4000-8000-000000000020"  # פעולות בשברים
N_PARA = "d4000000-0000-4000-8000-000000000010"    # מקבילות/מאונכות
N_DIAG = "d4000000-0000-4000-8000-000000000020"    # אלכסונים
N_QUAD = "d4000000-0000-4000-8000-000000000030"    # מרובעים
N_LEN = "d4000000-0000-4000-8000-000000000040"     # יחידות אורך
N_SURF = "d5000000-0000-4000-8000-000000000010"    # שטח פנים של תיבה
N_CAL = "d6000000-0000-4000-8000-000000000010"     # לוח שנה
N_DATA = "d7000000-0000-4000-8000-000000000010"    # חקר נתונים / עוגה


def _mc(rng, correct, lo=0, hi=1000000, k=4, spread=(-1000, -100, -10, -2, -1, 1, 2, 10, 100, 1000)):
    opts = {correct}; g = 0
    while len(opts) < k and g < 120:
        v = correct + rng.choice(spread); g += 1
        if lo <= v <= hi:
            opts.add(v)
    opts = list(opts); rng.shuffle(opts)
    return opts


# ============================================================
#  מספרים עד מיליון
# ============================================================
def gen_mil_value(rng, qt):
    n = rng.randint(10000, 999999)
    places = {"מֵאוֹת אֲלָפִים": n // 100000, "עֲשֶׂרֶת אֲלָפִים": (n // 10000) % 10,
              "אֲלָפִים": (n // 1000) % 10, "מֵאוֹת": (n // 100) % 10,
              "עֲשָׂרוֹת": (n // 10) % 10, "יְחִידוֹת": n % 10}
    place = rng.choice(list(places))
    return Question(QType.OPEN_NUMERIC, Difficulty.MEDIUM,
                    prompt=f"בַּמִּסְפָּר {n:,}, מַהִי סִפְרַת הָ{place}?".replace(",", ","),
                    answer=places[place])


def gen_mil_compare(rng, qt):
    a = rng.randint(10000, 999999); b = rng.randint(10000, 999999)
    while a == b:
        b = rng.randint(10000, 999999)
    return Question(QType.MULTIPLE_CHOICE, Difficulty.EASY,
                    prompt=f"אֵיזֶה סִימָן מַתְאִים?  {a:,} __ {b:,}",
                    answer=">" if a > b else "<", options=[">", "<"],
                    payload={"cmp_a": a, "cmp_b": b})


# ============================================================
#  חיבור וחיסור עד מיליון
# ============================================================
def gen_add_mil(rng, qt):
    a = rng.randint(1000, 500000); b = rng.randint(1000, 499999)
    return Question(QType.OPEN_NUMERIC, Difficulty.MEDIUM, prompt="פִּתְרוּ אֶת הַתַּרְגִּיל:",
                    answer=a + b, payload={"formula": f"{a} + {b} ="})


def gen_sub_mil(rng, qt):
    a = rng.randint(10000, 999999); b = rng.randint(1000, a)
    return Question(QType.OPEN_NUMERIC, Difficulty.MEDIUM, prompt="פִּתְרוּ אֶת הַתַּרְגִּיל:",
                    answer=a - b, payload={"formula": f"{a} − {b} ="})


# ============================================================
#  כפל
# ============================================================
def gen_mul2x1(rng, qt):
    a = rng.randint(11, 99); b = rng.randint(2, 9)
    return Question(QType.OPEN_NUMERIC, Difficulty.MEDIUM, prompt="פִּתְרוּ אֶת תַּרְגִּיל הַכֶּפֶל:",
                    answer=a * b, payload={"formula": f"{a} × {b} ="})


def gen_mul3x1(rng, qt):
    a = rng.randint(101, 999); b = rng.randint(2, 9)
    return Question(QType.OPEN_NUMERIC, Difficulty.CHALLENGE, prompt="פִּתְרוּ אֶת תַּרְגִּיל הַכֶּפֶל:",
                    answer=a * b, payload={"formula": f"{a} × {b} ="})


def gen_mul2x2(rng, qt):
    a = rng.randint(11, 40); b = rng.randint(11, 30)
    return Question(QType.OPEN_NUMERIC, Difficulty.CHALLENGE, prompt="פִּתְרוּ אֶת תַּרְגִּיל הַכֶּפֶל:",
                    answer=a * b, payload={"formula": f"{a} × {b} ="})


# ============================================================
#  חילוק (כולל חילוק ארוך)
# ============================================================
def gen_div_long(rng, qt):
    b = rng.randint(2, 9); q = rng.randint(20, 200)
    a = b * q
    return Question(QType.OPEN_NUMERIC, Difficulty.CHALLENGE, prompt="פִּתְרוּ אֶת הַחִלּוּק:",
                    answer=q, payload={"formula": f"{a} ÷ {b} ="}, explain=f"כִּי {b} × {q} = {a}.")


def gen_div_tens(rng, qt):
    factor = rng.choice([10, 100]); q = rng.randint(2, 50)
    a = factor * q
    return Question(QType.OPEN_NUMERIC, Difficulty.MEDIUM, prompt="פִּתְרוּ:",
                    answer=q, payload={"formula": f"{a} ÷ {factor} ="})


# ============================================================
#  סימני התחלקות ב-3, ב-6 וב-9
# ============================================================
def gen_divrule369(rng, qt):
    d = rng.choice([3, 6, 9])
    n = rng.randint(10, 300)
    return Question(QType.TRUE_FALSE, Difficulty.CHALLENGE,
                    prompt=f"נָכוֹן אוֹ לֹא נָכוֹן? הַמִּסְפָּר {n} מִתְחַלֵּק בְּ-{d} לְלֹא שְׁאֵרִית.",
                    answer=(n % d == 0),
                    explain=f"לְהִתְחַלְּקוּת בְּ-{d}: סְכוּם הַסְּפָרוֹת.")


def gen_digit_sum(rng, qt):
    n = rng.randint(100, 9999)
    return Question(QType.OPEN_NUMERIC, Difficulty.MEDIUM,
                    prompt=f"מַה סְכוּם הַסְּפָרוֹת שֶׁל {n}? (עוֹזֵר לִבְדֹּק הִתְחַלְּקוּת)",
                    answer=sum(int(c) for c in str(n)))


# ============================================================
#  סדר פעולות (4 פעולות)
# ============================================================
def gen_order4(rng, qt):
    a = rng.randint(2, 9); b = rng.randint(2, 9); c = rng.randint(2, 9)
    use_paren = rng.random() < 0.5
    if use_paren:
        ans = (a + b) * c
        return Question(QType.OPEN_NUMERIC, Difficulty.CHALLENGE,
                        prompt="פִּתְרוּ (שִׂימוּ לֵב לַסּוֹגְרַיִם):",
                        answer=ans, payload={"formula": f"({a} + {b}) × {c} ="},
                        explain="קֹדֶם מָה שֶׁבַּסּוֹגְרַיִם.")
    ans = a + b * c
    return Question(QType.OPEN_NUMERIC, Difficulty.CHALLENGE,
                    prompt="פִּתְרוּ לְפִי סֵדֶר הַפְּעוּלוֹת:",
                    answer=ans, payload={"formula": f"{a} + {b} × {c} ="},
                    explain="כֶּפֶל לִפְנֵי חִבּוּר.")


# ============================================================
#  הכרת שברים ומשמעויותיו
# ============================================================
def gen_frac_part(rng, qt):
    """איזה חלק צבוע — מונה מתוך מכנה."""
    den = rng.randint(2, 8); num = rng.randint(1, den)
    return Question(QType.OPEN_TEXT, Difficulty.EASY,
                    prompt=f"עוּגָה חֻלְּקָה לְ-{den} חֲלָקִים שָׁוִים, וְ-{num} מֵהֶם נִצְבְּעוּ. אֵיזֶה שֶׁבֶר צָבוּעַ? (כִּתְבוּ בְּצוּרָה כְּמוֹ 1/2)",
                    answer=f"{num}/{den}", explain=f"{num} חֲלָקִים מִתּוֹךְ {den}.")


def gen_frac_compare(rng, qt):
    """השוואת שברי יחידה — ככל שהמכנה גדול, השבר קטן."""
    d1 = rng.randint(2, 9); d2 = rng.randint(2, 9)
    while d1 == d2:
        d2 = rng.randint(2, 9)
    # שבר יחידה: 1/d. הגדול = המכנה הקטן
    bigger = f"1/{min(d1, d2)}"
    return Question(QType.MULTIPLE_CHOICE, Difficulty.MEDIUM,
                    prompt=f"אֵיזֶה שֶׁבֶר גָּדוֹל יוֹתֵר?",
                    answer=bigger, options=[f"1/{d1}", f"1/{d2}"],
                    explain="כְּכָל שֶׁמְּחַלְּקִים לְיוֹתֵר חֲלָקִים, כָּל חֵלֶק קָטָן יוֹתֵר.")


def gen_frac_whole(rng, qt):
    """כמה רבעים/שלישים בשלם."""
    den = rng.choice([2, 3, 4, 5])
    return Question(QType.OPEN_NUMERIC, Difficulty.MEDIUM,
                    prompt=f"כַּמָּה חֲלָקִים שֶׁל 1/{den} יֵשׁ בְּשָׁלֵם אֶחָד?",
                    answer=den, explain=f"שָׁלֵם = {den} חֲלָקִים שֶׁל 1/{den}.")


# ============================================================
#  פעולות בשברים (מכנים שווים)
# ============================================================
def gen_frac_add(rng, qt):
    den = rng.randint(3, 10)
    a = rng.randint(1, den - 1); b = rng.randint(1, den - a) if den - a > 1 else 1
    num = a + b
    # תשובה כשבר (ייתכן שלם אם num==den)
    if num == den:
        ans = "1"
    else:
        ans = f"{num}/{den}"
    return Question(QType.OPEN_TEXT, Difficulty.CHALLENGE,
                    prompt=f"כַּמָּה זֶה {a}/{den} + {b}/{den}? (מְחַבְּרִים מוֹנִים, הַמְּכַנֶּה נִשְׁאָר)",
                    answer=ans, explain=f"{a}+{b}={num}, מֵעַל {den}.")


def gen_frac_sub(rng, qt):
    den = rng.randint(3, 10)
    a = rng.randint(2, den); b = rng.randint(1, a - 1)
    num = a - b
    ans = "0" if num == 0 else f"{num}/{den}"
    return Question(QType.OPEN_TEXT, Difficulty.CHALLENGE,
                    prompt=f"כַּמָּה זֶה {a}/{den} − {b}/{den}?",
                    answer=ans, explain=f"{a}−{b}={num}, מֵעַל {den}.")


# ============================================================
#  מקבילות ומאונכות
# ============================================================
def gen_para(rng, qt):
    qs = [("שְׁנֵי יְשָׁרִים שֶׁלְּעוֹלָם לֹא נִפְגָּשִׁים נִקְרָאִים:", "מַקְבִּילִים",
           ["מַקְבִּילִים", "מְאֻנָּכִים", "נֶחְתָּכִים"]),
          ("שְׁנֵי יְשָׁרִים שֶׁנִּפְגָּשִׁים וְיוֹצְרִים זָוִית יְשָׁרָה נִקְרָאִים:", "מְאֻנָּכִים",
           ["מַקְבִּילִים", "מְאֻנָּכִים", "מְקֻוָּקְוִים"])]
    prompt, ans, opts = rng.choice(qs)
    return Question(QType.MULTIPLE_CHOICE, Difficulty.MEDIUM, prompt=prompt, answer=ans, options=opts)


# ============================================================
#  אלכסונים במצולעים
# ============================================================
def gen_diagonals(rng, qt):
    # מספר אלכסונים: n(n-3)/2
    shapes = [("מְשֻׁלָּשׁ", 3), ("מְרֻבָּע", 4), ("מְחֻמָּשׁ", 5), ("מְשֻׁשֶּׁה", 6)]
    name, n = rng.choice(shapes)
    diag = n * (n - 3) // 2
    return Question(QType.OPEN_NUMERIC, Difficulty.CHALLENGE,
                    prompt=f"כַּמָּה אֲלַכְסוֹנִים יֵשׁ בְּ{name}?",
                    answer=diag, explain="אֲלַכְסוֹן מְחַבֵּר שְׁנֵי קָדְקֳדִים לֹא סְמוּכִים.")


# ============================================================
#  מרובעים
# ============================================================
def gen_quad(rng, qt):
    qs = [("לְאֵיזֶה מְרֻבָּע כָּל הַצְּלָעוֹת שָׁווֹת וְכָל הַזָּוִיּוֹת יְשָׁרוֹת?", "רִבּוּעַ",
           ["רִבּוּעַ", "מַלְבֵּן", "מְעֻיָּן", "טְרַפֵּז"]),
          ("לְאֵיזֶה מְרֻבָּע יֵשׁ שְׁנֵי זוּגוֹת צְלָעוֹת מַקְבִּילוֹת וְכָל הַזָּוִיּוֹת יְשָׁרוֹת?", "מַלְבֵּן",
           ["רִבּוּעַ", "מַלְבֵּן", "מְעֻיָּן", "טְרַפֵּז"]),
          ("לְאֵיזֶה מְרֻבָּע רַק זוּג אֶחָד שֶׁל צְלָעוֹת מַקְבִּילוֹת?", "טְרַפֵּז",
           ["רִבּוּעַ", "מַלְבֵּן", "מְעֻיָּן", "טְרַפֵּז"])]
    prompt, ans, opts = rng.choice(qs)
    return Question(QType.MULTIPLE_CHOICE, Difficulty.MEDIUM, prompt=prompt, answer=ans, options=opts)


# ============================================================
#  מעבר בין יחידות אורך
# ============================================================
def gen_len_convert(rng, qt):
    conv = rng.choice([("מֶטְרִים", "סֶנְטִימֶטְרִים", 100), ("קִילוֹמֶטְרִים", "מֶטְרִים", 1000),
                       ("סֶנְטִימֶטְרִים", "מִילִימֶטְרִים", 10)])
    big, small, factor = conv
    n = rng.randint(2, 9)
    return Question(QType.OPEN_NUMERIC, Difficulty.MEDIUM,
                    prompt=f"כַּמָּה {small} יֵשׁ בְּ-{n} {big}?",
                    answer=n * factor, explain=f"בְּ-{big} אֶחָד יֵשׁ {factor} {small}.")


# ============================================================
#  שטח פנים של תיבה
# ============================================================
def gen_surface(rng, qt):
    a = rng.randint(2, 6); b = rng.randint(2, 6); c = rng.randint(2, 6)
    surf = 2 * (a * b + b * c + a * c)
    return Question(QType.OPEN_NUMERIC, Difficulty.CHALLENGE,
                    prompt=f"מַהוּ שֶׁטַח הַפָּנִים שֶׁל תֵּבָה בְּמִדּוֹת {a}×{b}×{c}?",
                    answer=surf, explain=f"2×({a}×{b}+{b}×{c}+{a}×{c}).")


def gen_cube_surface(rng, qt):
    a = rng.randint(2, 9)
    return Question(QType.OPEN_NUMERIC, Difficulty.MEDIUM,
                    prompt=f"מַהוּ שֶׁטַח הַפָּנִים שֶׁל קֻבִּיָּה שֶׁאֹרֶךְ מִקְצוֹעָהּ {a}?",
                    answer=6 * a * a, explain=f"לְקֻבִּיָּה 6 פֵּאוֹת: 6×{a}×{a}.")


# ============================================================
#  לוח שנה וחישובי זמן
# ============================================================
def gen_calendar(rng, qt):
    ask = rng.choice(["week", "month_days", "year"])
    if ask == "week":
        w = rng.randint(2, 8)
        return Question(QType.OPEN_NUMERIC, Difficulty.MEDIUM,
                        prompt=f"כַּמָּה יָמִים יֵשׁ בְּ-{w} שָׁבוּעוֹת?",
                        answer=w * 7, explain="בְּשָׁבוּעַ 7 יָמִים.")
    if ask == "month_days":
        return Question(QType.OPEN_NUMERIC, Difficulty.EASY,
                        prompt="כַּמָּה חֳדָשִׁים יֵשׁ בְּשָׁנָה?", answer=12)
    months = rng.randint(2, 6)
    return Question(QType.OPEN_NUMERIC, Difficulty.MEDIUM,
                    prompt=f"כַּמָּה שָׁבוּעוֹת בְּעֵרֶךְ יֵשׁ בְּ-{months} חֳדָשִׁים? (4 שָׁבוּעוֹת לְחֹדֶשׁ)",
                    answer=months * 4)


# ============================================================
#  חקר נתונים (כולל דיאגרמת עוגה)
# ============================================================
def gen_data_pie(rng, qt):
    total = rng.choice([20, 40, 60, 80, 100])
    half = total // 2
    quarter = total // 4
    ask = rng.choice(["half", "quarter"])
    if ask == "half":
        return Question(QType.OPEN_NUMERIC, Difficulty.MEDIUM,
                        prompt=f"בְּדִיאַגְרַמַּת עוּגָה, חֵצִי מִתּוֹךְ {total} תַּלְמִידִים בָּחֲרוּ כָּחֹל. כַּמָּה תַּלְמִידִים זֶה?",
                        answer=half, explain=f"חֵצִי מִ-{total} זֶה {half}.")
    return Question(QType.OPEN_NUMERIC, Difficulty.MEDIUM,
                    prompt=f"בְּדִיאַגְרַמַּת עוּגָה, רֶבַע מִתּוֹךְ {total} תַּלְמִידִים בָּחֲרוּ יָרֹק. כַּמָּה זֶה?",
                    answer=quarter, explain=f"רֶבַע מִ-{total} זֶה {quarter}.")


def gen_data_bar(rng, qt):
    cats = rng.sample(["א", "ב", "ג", "ד"], 3)
    vals = [rng.randint(10, 50) for _ in cats]
    data_str = ", ".join(f"{c}={v}" for c, v in zip(cats, vals))
    return Question(QType.OPEN_NUMERIC, Difficulty.MEDIUM,
                    prompt=f"בַּדִּיאַגְרַמָּה: {data_str}. מַה הַסַּךְ הַכּוֹלֵל?",
                    answer=sum(vals))


# ============================================================
#  רישום
# ============================================================
def build_templates() -> list:
    return [
        Template("mil_value", N_MIL, Difficulty.MEDIUM, [QType.OPEN_NUMERIC], gen_mil_value),
        Template("mil_compare", N_MIL, Difficulty.EASY, [QType.MULTIPLE_CHOICE], gen_mil_compare),
        Template("add_mil", N_ADDSUB, Difficulty.MEDIUM, [QType.OPEN_NUMERIC], gen_add_mil),
        Template("sub_mil", N_ADDSUB, Difficulty.MEDIUM, [QType.OPEN_NUMERIC], gen_sub_mil),
        Template("mul2x1", N_MUL, Difficulty.MEDIUM, [QType.OPEN_NUMERIC], gen_mul2x1),
        Template("mul3x1", N_MUL, Difficulty.CHALLENGE, [QType.OPEN_NUMERIC], gen_mul3x1),
        Template("mul2x2", N_MUL, Difficulty.CHALLENGE, [QType.OPEN_NUMERIC], gen_mul2x2),
        Template("div_long", N_DIV, Difficulty.CHALLENGE, [QType.OPEN_NUMERIC], gen_div_long),
        Template("div_tens", N_DIV, Difficulty.MEDIUM, [QType.OPEN_NUMERIC], gen_div_tens),
        Template("divrule369", N_DIVRULE, Difficulty.CHALLENGE, [QType.TRUE_FALSE], gen_divrule369),
        Template("digit_sum", N_DIVRULE, Difficulty.MEDIUM, [QType.OPEN_NUMERIC], gen_digit_sum),
        Template("order4", N_ORDER, Difficulty.CHALLENGE, [QType.OPEN_NUMERIC], gen_order4),
        Template("frac_part", N_FRAC, Difficulty.EASY, [QType.OPEN_TEXT], gen_frac_part),
        Template("frac_compare", N_FRAC, Difficulty.MEDIUM, [QType.MULTIPLE_CHOICE], gen_frac_compare),
        Template("frac_whole", N_FRAC, Difficulty.MEDIUM, [QType.OPEN_NUMERIC], gen_frac_whole),
        Template("frac_add", N_FRACOP, Difficulty.CHALLENGE, [QType.OPEN_TEXT], gen_frac_add),
        Template("frac_sub", N_FRACOP, Difficulty.CHALLENGE, [QType.OPEN_TEXT], gen_frac_sub),
        Template("para", N_PARA, Difficulty.MEDIUM, [QType.MULTIPLE_CHOICE], gen_para),
        Template("diagonals", N_DIAG, Difficulty.CHALLENGE, [QType.OPEN_NUMERIC], gen_diagonals),
        Template("quad", N_QUAD, Difficulty.MEDIUM, [QType.MULTIPLE_CHOICE], gen_quad),
        Template("len_convert", N_LEN, Difficulty.MEDIUM, [QType.OPEN_NUMERIC], gen_len_convert),
        Template("surface", N_SURF, Difficulty.CHALLENGE, [QType.OPEN_NUMERIC], gen_surface),
        Template("cube_surface", N_SURF, Difficulty.MEDIUM, [QType.OPEN_NUMERIC], gen_cube_surface),
        Template("calendar", N_CAL, Difficulty.MEDIUM, [QType.OPEN_NUMERIC], gen_calendar),
        Template("data_pie", N_DATA, Difficulty.MEDIUM, [QType.OPEN_NUMERIC], gen_data_pie),
        Template("data_bar", N_DATA, Difficulty.MEDIUM, [QType.OPEN_NUMERIC], gen_data_bar),
    ]


def templates_for_node(node_id: str) -> list:
    return [t for t in build_templates() if t.node_id == node_id]
