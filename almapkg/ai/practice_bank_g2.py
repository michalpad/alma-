"""
ALMA — בנק תרגול מלא לכיתה ב' (מתמטיקה).
מכסה את כל נושאי כיתה ב' מתכנית הלימודים, בכל רמות הקושי.
כל מחולל מחשב את תשובתו הנכונה -> נכונות מובטחת בשרת.

נושאים (תואם math_grade2_curriculum.sql):
  מספרים: מבנה עשרוני עד 1,000, ספירה ומנייה, זוגיות, סדרות
  פעולות: חיבור/חיסור עד 100, תכונות, כפל/חילוק, תכונות כפל/חילוק
  גאומטריה: מצולעים ומשולשים, זווית ישרה
  מדידות אורך: יחידות, קווים שבורים, היקף
  גופים: גופים, השוואת נפחים, מבנים מקוביות
  זמן: שעות שלמות וחצאי שעות
  חקר נתונים
"""
from __future__ import annotations

import random

from .practice_engine import Question, QType, Difficulty, Template

# ---- מזהי צמתים (מתוך עץ כיתה ב') ----
N_DEC = "b1000000-0000-4000-8000-000000000010"     # מבנה עשרוני עד 1,000
N_CNT = "b1000000-0000-4000-8000-000000000020"     # ספירה ומנייה עד 1,000
N_EVEN = "b1000000-0000-4000-8000-000000000030"    # זוגיים/אי-זוגיים
N_SEQ = "b1000000-0000-4000-8000-000000000040"     # סדרות
N_ADDSUB = "b2000000-0000-4000-8000-000000000010"  # חיבור/חיסור עד 100
N_ASPROP = "b2000000-0000-4000-8000-000000000020"  # תכונות חיבור/חיסור
N_MULDIV = "b2000000-0000-4000-8000-000000000030"  # כפל וחילוק
N_MDPROP = "b2000000-0000-4000-8000-000000000040"  # תכונות כפל/חילוק
N_POLY = "b3000000-0000-4000-8000-000000000010"    # מצולעים ומשולשים
N_RIGHT = "b3000000-0000-4000-8000-000000000020"   # זווית ישרה
N_LEN = "b4000000-0000-4000-8000-000000000010"     # מדידת אורך
N_BROKEN = "b4000000-0000-4000-8000-000000000020"  # קווים שבורים
N_PERIM = "b4000000-0000-4000-8000-000000000030"   # היקף
N_SOLID = "b5000000-0000-4000-8000-000000000010"   # גופים
N_VOL = "b5000000-0000-4000-8000-000000000020"     # השוואת נפחים
N_CUBES = "b5000000-0000-4000-8000-000000000030"   # מבנים מקוביות
N_TIME = "b6000000-0000-4000-8000-000000000010"    # שעות וחצאי שעות
N_DATA = "b7000000-0000-4000-8000-000000000010"    # חקר נתונים


def _mc(rng, correct, lo=0, hi=1000, k=4, spread=(-10, -5, -2, -1, 1, 2, 5, 10)):
    opts = {correct}; g = 0
    while len(opts) < k and g < 80:
        v = correct + rng.choice(spread); g += 1
        if lo <= v <= hi:
            opts.add(v)
    opts = list(opts); rng.shuffle(opts)
    return opts


# ============================================================
#  מספרים: מבנה עשרוני עד 1,000
# ============================================================
def gen_dec_value(rng, qt):
    """ערך הספרה לפי מיקומה (מאות/עשרות/יחידות)."""
    n = rng.randint(100, 999)
    h, t, u = n // 100, (n // 10) % 10, n % 10
    place = rng.choice(["מֵאוֹת", "עֲשָׂרוֹת", "יְחִידוֹת"])
    ans = {"מֵאוֹת": h, "עֲשָׂרוֹת": t, "יְחִידוֹת": u}[place]
    return Question(qt if qt == QType.OPEN_NUMERIC else QType.OPEN_NUMERIC, Difficulty.MEDIUM,
                    prompt=f"בַּמִּסְפָּר {n}, כַּמָּה {place} יֵשׁ?", answer=ans,
                    explain=f"{n} = {h} מֵאוֹת, {t} עֲשָׂרוֹת, {u} יְחִידוֹת.")


def gen_dec_build(rng, qt):
    """הרכבת מספר ממאות/עשרות/יחידות."""
    h, t, u = rng.randint(1, 9), rng.randint(0, 9), rng.randint(0, 9)
    ans = h * 100 + t * 10 + u
    return Question(QType.OPEN_NUMERIC, Difficulty.MEDIUM,
                    prompt=f"אֵיזֶה מִסְפָּר מוּרְכָּב מִ-{h} מֵאוֹת, {t} עֲשָׂרוֹת וְ-{u} יְחִידוֹת?",
                    answer=ans, explain=f"{h} מֵאוֹת וְ-{t} עֲשָׂרוֹת וְ-{u} יְחִידוֹת זֶה {ans}.")


def gen_dec_compare(rng, qt):
    a = rng.randint(100, 999); b = rng.randint(100, 999)
    while a == b:
        b = rng.randint(100, 999)
    ans = ">" if a > b else "<"
    return Question(QType.MULTIPLE_CHOICE, Difficulty.EASY,
                    prompt=f"אֵיזֶה סִימָן מַתְאִים?  {a} __ {b}", answer=ans,
                    options=[">", "<"], payload={"cmp_a": a, "cmp_b": b})


# ============================================================
#  ספירה ומנייה עד 1,000
# ============================================================
def gen_cnt_skip(rng, qt):
    step = rng.choice([10, 25, 50, 100])
    start = rng.choice([0, step, 2 * step, 3 * step])
    seq = [start + step * i for i in range(4)]
    return Question(QType.OPEN_NUMERIC, Difficulty.MEDIUM,
                    prompt=f"סִפְרוּ בְּדִילּוּגִים שֶׁל {step}: {seq[0]}, {seq[1]}, {seq[2]}, {seq[3]}, וּמָה הַבָּא?",
                    answer=seq[-1] + step, explain=f"מוֹסִיפִים {step} בְּכָל פַּעַם.")


def gen_cnt_next(rng, qt):
    fwd = rng.random() < 0.6
    n = rng.randint(1, 998)
    ans = n + 1 if fwd else n - 1
    word = "אַחֲרֵי" if fwd else "לִפְנֵי"
    return Question(QType.OPEN_NUMERIC, Difficulty.EASY,
                    prompt=f"אֵיזֶה מִסְפָּר בָּא {word} {n}?", answer=ans)


# ============================================================
#  זוגיים ואי-זוגיים
# ============================================================
def gen_even(rng, qt):
    n = rng.randint(1, 200)
    is_even = (n % 2 == 0)
    ask_even = rng.random() < 0.5
    target = is_even if ask_even else (not is_even)
    word = "זוּגִי" if ask_even else "אִי-זוּגִי"
    return Question(QType.TRUE_FALSE, Difficulty.EASY,
                    prompt=f"נָכוֹן אוֹ לֹא נָכוֹן? הַמִּסְפָּר {n} הוּא {word}.",
                    answer=target, explain=f"{n} מִתְחַלֵּק בְּ-2 לְלֹא שְׁאֵרִית?" if ask_even else "")


def gen_even_pick(rng, qt):
    """בחירת המספר הזוגי/אי-זוגי מבין כמה."""
    want_even = rng.random() < 0.5
    pool = rng.sample(range(1, 100), 4)
    # נוודא שיש לפחות אחד מתאים; נחליף אם אין
    matches = [x for x in pool if (x % 2 == 0) == want_even]
    if not matches:
        pool[0] = pool[0] + 1 if (pool[0] % 2 == 0) != want_even else pool[0]
        matches = [x for x in pool if (x % 2 == 0) == want_even]
    ans = matches[0]
    word = "זוּגִי" if want_even else "אִי-זוּגִי"
    return Question(QType.MULTIPLE_CHOICE, Difficulty.MEDIUM,
                    prompt=f"אֵיזֶה מִסְפָּר הוּא {word}?", answer=ans, options=rng.sample(pool, len(pool)))


# ============================================================
#  סדרות (כיתה ב')
# ============================================================
def gen_seq_missing(rng, qt):
    step = rng.choice([2, 5, 10, 25, 50, 100])
    start = rng.randint(0, 50)
    seq = [start + step * i for i in range(5)]
    hole = rng.randint(1, 3)
    shown = [str(x) if i != hole else "___" for i, x in enumerate(seq)]
    return Question(QType.FILL_BLANK, Difficulty.MEDIUM,
                    prompt="אֵיזֶה מִסְפָּר חָסֵר?  " + ", ".join(shown),
                    answer=seq[hole], explain=f"הַסִּדְרָה עוֹלָה בְּ-{step}.")


def gen_seq_rule(rng, qt):
    step = rng.choice([2, 5, 10, 25, 50])
    start = rng.randint(1, 30)
    seq = [start + step * i for i in range(4)]
    return Question(QType.OPEN_NUMERIC, Difficulty.CHALLENGE,
                    prompt=f"בְּכַמָּה עוֹלָה הַסִּדְרָה?  {seq[0]}, {seq[1]}, {seq[2]}, {seq[3]}",
                    answer=step, explain=f"כָּל מִסְפָּר גָּדוֹל בְּ-{step}.")


# ============================================================
#  חיבור וחיסור בתחום ה-100
# ============================================================
def gen_add100(rng, qt):
    a = rng.randint(10, 89); b = rng.randint(1, 99 - a)
    ans = a + b
    if qt == QType.MULTIPLE_CHOICE:
        return Question(qt, Difficulty.EASY, prompt="מַהוּ הַפִּתְרוֹן?", answer=ans,
                        options=_mc(rng, ans, hi=100, spread=(-5, -2, -1, 1, 2, 5)),
                        payload={"formula": f"{a} + {b} ="})
    return Question(QType.OPEN_NUMERIC, Difficulty.EASY, prompt="פִּתְרוּ אֶת הַתַּרְגִּיל:",
                    answer=ans, payload={"formula": f"{a} + {b} ="})


def gen_sub100(rng, qt):
    a = rng.randint(20, 100); b = rng.randint(1, a)
    ans = a - b
    if qt == QType.MULTIPLE_CHOICE:
        return Question(qt, Difficulty.EASY, prompt="מַהוּ הַפִּתְרוֹן?", answer=ans,
                        options=_mc(rng, ans, hi=100, spread=(-5, -2, -1, 1, 2, 5)),
                        payload={"formula": f"{a} − {b} ="})
    return Question(QType.OPEN_NUMERIC, Difficulty.EASY, prompt="פִּתְרוּ אֶת הַתַּרְגִּיל:",
                    answer=ans, payload={"formula": f"{a} − {b} ="})


def gen_word100(rng, qt):
    a = rng.randint(10, 60); b = rng.randint(5, 39)
    add = rng.random() < 0.6
    ans = a + b if add else abs(a - b)
    item = rng.choice(["שְׁקָלִים", "כַּדּוּרִים", "מַדְבֵּקוֹת", "נְקֻדּוֹת", "סְפָרִים"])
    if add:
        prompt = f"הָיוּ {a} {item}, וְנוֹסְפוּ עוֹד {b}. כַּמָּה {item} יֵשׁ עַכְשָׁו?"
    else:
        hi, lo = max(a, b), min(a, b)
        prompt = f"הָיוּ {hi} {item}, וְנִלְקְחוּ {lo}. כַּמָּה {item} נִשְׁאֲרוּ?"
        ans = hi - lo
    return Question(QType.OPEN_NUMERIC, Difficulty.MEDIUM, prompt=prompt, answer=ans)


def gen_missing100(rng, qt):
    a = rng.randint(10, 70); ans = rng.randint(1, 99 - a); total = a + ans
    return Question(QType.FILL_BLANK, Difficulty.MEDIUM, prompt="אֵיזֶה מִסְפָּר חָסֵר?",
                    answer=ans, payload={"formula": f"{a} + ___ = {total}"})


# ============================================================
#  תכונות חיבור וחיסור (חוק החילוף, פעולות הפוכות)
# ============================================================
def gen_commute(rng, qt):
    a = rng.randint(5, 40); b = rng.randint(5, 40)
    # a + b = b + ? -> a
    return Question(QType.FILL_BLANK, Difficulty.MEDIUM,
                    prompt="הַשְׁלִימוּ לְפִי חוֹק הַחִלּוּף:",
                    answer=a, payload={"formula": f"{a} + {b} = {b} + ___"},
                    explain="בְּחִבּוּר אֶפְשָׁר לְהַחְלִיף אֶת סֵדֶר הַמְּחֻבָּרִים.")


def gen_inverse(rng, qt):
    a = rng.randint(10, 50); b = rng.randint(1, a)
    # a - b = c  ->  c + b = a ; שאלה: a - ? = c, given c
    c = a - b
    return Question(QType.FILL_BLANK, Difficulty.CHALLENGE,
                    prompt="הַשְׁלִימוּ (חִבּוּר וְחִסּוּר הֲפוּכִים):",
                    answer=b, payload={"formula": f"{a} − ___ = {c}"},
                    explain=f"כִּי {c} + {b} = {a}.")


# ============================================================
#  כפל וחילוק (כפולות 2,5,10 וכו')
# ============================================================
def gen_mul(rng, qt):
    a = rng.choice([2, 3, 4, 5, 10]); b = rng.randint(1, 10)
    ans = a * b
    if qt == QType.MULTIPLE_CHOICE:
        return Question(qt, Difficulty.MEDIUM, prompt="מַהִי הַמַּכְפֵּלָה?", answer=ans,
                        options=_mc(rng, ans, hi=100, spread=(-a, a, -2 * a, 2 * a, -1, 1)),
                        payload={"formula": f"{a} × {b} ="})
    return Question(QType.OPEN_NUMERIC, Difficulty.MEDIUM, prompt="פִּתְרוּ אֶת תַּרְגִּיל הַכֶּפֶל:",
                    answer=ans, payload={"formula": f"{a} × {b} ="})


def gen_div(rng, qt):
    b = rng.choice([2, 5, 10]); q = rng.randint(1, 10)
    a = b * q  # חילוק ללא שארית
    return Question(QType.OPEN_NUMERIC, Difficulty.MEDIUM, prompt="פִּתְרוּ אֶת תַּרְגִּיל הַחִלּוּק:",
                    answer=q, payload={"formula": f"{a} ÷ {b} ="},
                    explain=f"כִּי {b} × {q} = {a}.")


def gen_mul_groups(rng, qt):
    """כפל כקבוצות שוות (משמעות הכפל)."""
    groups = rng.randint(2, 6); per = rng.randint(2, 9)
    ans = groups * per
    item = rng.choice(["פְּרָחִים", "עוּגִיּוֹת", "כַּדּוּרִים", "בַּלּוֹנִים"])
    return Question(QType.OPEN_NUMERIC, Difficulty.EASY,
                    prompt=f"יֵשׁ {groups} אֲגַרְטְלִים, וּבְכָל אֶחָד {per} {item}. כַּמָּה {item} בְּסַךְ הַכֹּל?",
                    answer=ans, explain=f"{groups} פְּעָמִים {per} זֶה {ans}.")


# ============================================================
#  תכונות כפל וחילוק (חוק החילוף בכפל, קשר הפוך)
# ============================================================
def gen_mul_commute(rng, qt):
    a = rng.randint(2, 9); b = rng.randint(2, 9)
    return Question(QType.FILL_BLANK, Difficulty.MEDIUM,
                    prompt="הַשְׁלִימוּ לְפִי חוֹק הַחִלּוּף בַּכֶּפֶל:",
                    answer=a, payload={"formula": f"{a} × {b} = {b} × ___"},
                    explain="בַּכֶּפֶל אֶפְשָׁר לְהַחְלִיף אֶת סֵדֶר הַגּוֹרְמִים.")


def gen_muldiv_inverse(rng, qt):
    b = rng.choice([2, 3, 4, 5]); q = rng.randint(2, 9)
    a = b * q
    return Question(QType.FILL_BLANK, Difficulty.CHALLENGE,
                    prompt="הַשְׁלִימוּ (כֶּפֶל וְחִלּוּק הֲפוּכִים):",
                    answer=q, payload={"formula": f"{a} ÷ {b} = ___"},
                    explain=f"כִּי {b} × {q} = {a}.")


# ============================================================
#  גאומטריה: מצולעים ומשולשים
# ============================================================
def gen_poly_sides(rng, qt):
    shapes = [("מְשֻׁלָּשׁ", 3), ("מְרֻבָּע", 4), ("מְחֻמָּשׁ", 5), ("מְשֻׁשֶּׁה", 6)]
    name, sides = rng.choice(shapes)
    ask_sides = rng.random() < 0.5
    if ask_sides:
        return Question(QType.OPEN_NUMERIC, Difficulty.EASY,
                        prompt=f"כַּמָּה צְלָעוֹת יֵשׁ לְ{name}?", answer=sides)
    # זיהוי שם לפי מספר צלעות
    return Question(QType.MULTIPLE_CHOICE, Difficulty.MEDIUM,
                    prompt=f"אֵיךְ נִקְרָא מְצוּלָע בַּעַל {sides} צְלָעוֹת?",
                    answer=name, options=rng.sample([s[0] for s in shapes], 4))


def gen_triangle(rng, qt):
    kinds = ["שְׁוֵה-צְלָעוֹת", "שְׁוֵה-שׁוֹקַיִם", "שׁוֹנֵה-צְלָעוֹת"]
    return Question(QType.MULTIPLE_CHOICE, Difficulty.MEDIUM,
                    prompt="מְשֻׁלָּשׁ שֶׁכָּל שְׁלוֹשׁ צְלָעוֹתָיו שָׁווֹת נִקְרָא:",
                    answer="שְׁוֵה-צְלָעוֹת", options=kinds + ["יְשַׁר-זָוִית"])


# ============================================================
#  זווית ישרה
# ============================================================
def gen_right_angle(rng, qt):
    angles = [("חַדָּה", "קְטַנָּה מִזָּוִית יְשָׁרָה"), ("יְשָׁרָה", "כְּמוֹ פִּנַּת דַּף"),
              ("קְהָה", "גְּדוֹלָה מִזָּוִית יְשָׁרָה")]
    name, desc = rng.choice(angles)
    return Question(QType.MULTIPLE_CHOICE, Difficulty.MEDIUM,
                    prompt=f"זָוִית שֶׁהִיא {desc} נִקְרֵאת:",
                    answer=name, options=["חַדָּה", "יְשָׁרָה", "קְהָה"])


# ============================================================
#  מדידת אורך
# ============================================================
def gen_length_unit(rng, qt):
    items = [("עִפָּרוֹן", "סֶנְטִימֶטְרִים"), ("חֶדֶר", "מֶטְרִים"), ("סֵפֶר", "סֶנְטִימֶטְרִים")]
    item, unit = rng.choice(items)
    return Question(QType.MULTIPLE_CHOICE, Difficulty.EASY,
                    prompt=f"בְּאֵיזוֹ יְחִידָה נָכוֹן לִמְדֹּד {item}?",
                    answer=unit, options=["מֶטְרִים", "סֶנְטִימֶטְרִים", "קִילוֹמֶטְרִים"])


def gen_length_convert(rng, qt):
    m = rng.randint(1, 5)
    return Question(QType.OPEN_NUMERIC, Difficulty.MEDIUM,
                    prompt=f"כַּמָּה סֶנְטִימֶטְרִים יֵשׁ בְּ-{m} מֶטְרִים?",
                    answer=m * 100, explain="בְּמֶטֶר אֶחָד יֵשׁ 100 סֶנְטִימֶטְרִים.")


# ============================================================
#  קווים שבורים
# ============================================================
def gen_broken_line(rng, qt):
    segs = [rng.randint(2, 12) for _ in range(rng.randint(3, 4))]
    total = sum(segs)
    return Question(QType.OPEN_NUMERIC, Difficulty.MEDIUM,
                    prompt=f"קַו שָׁבוּר בָּנוּי מִקְּטָעִים בְּאֹרֶךְ {', '.join(map(str, segs))} סֶ\"מ. מָה אָרְכּוֹ הַכּוֹלֵל?",
                    answer=total, explain="מְחַבְּרִים אֶת אָרְכֵי כָּל הַקְּטָעִים.")


# ============================================================
#  היקף מצולעים
# ============================================================
def gen_perimeter(rng, qt):
    shape = rng.choice(["מְרֻבָּע", "מְשֻׁלָּשׁ"])
    if shape == "מְרֻבָּע":
        side = rng.randint(2, 15)
        return Question(QType.OPEN_NUMERIC, Difficulty.MEDIUM,
                        prompt=f"מָה הַהֶקֵּף שֶׁל רִבּוּעַ שֶׁאֹרֶךְ צַלְעוֹ {side} סֶ\"מ?",
                        answer=side * 4, explain=f"בְּרִבּוּעַ כָּל 4 הַצְּלָעוֹת שָׁווֹת: {side}×4.")
    a, b, c = rng.randint(2, 9), rng.randint(2, 9), rng.randint(2, 9)
    return Question(QType.OPEN_NUMERIC, Difficulty.MEDIUM,
                    prompt=f"מָה הַהֶקֵּף שֶׁל מְשֻׁלָּשׁ שֶׁצְּלָעוֹתָיו {a}, {b}, {c} סֶ\"מ?",
                    answer=a + b + c, explain="מְחַבְּרִים אֶת כָּל הַצְּלָעוֹת.")


# ============================================================
#  גופים
# ============================================================
def gen_solid_id(rng, qt):
    solids = ["קֻבִּיָּה", "תֵּבָה", "כַּדּוּר", "גָּלִיל", "חֲרוּט", "פִּירָמִידָה"]
    descriptions = {
        "קֻבִּיָּה": "גּוּף שֶׁכָּל פֵּאוֹתָיו רִבּוּעִים שָׁוִים",
        "כַּדּוּר": "גּוּף עָגֹל לְגַמְרֵי, בְּלִי פֵּאוֹת יְשָׁרוֹת",
        "גָּלִיל": "גּוּף עִם שְׁנֵי עִגּוּלִים בַּקְּצָווֹת",
    }
    name = rng.choice(list(descriptions.keys()))
    distractors = rng.sample([s for s in solids if s != name], 3)
    options = distractors + [name]
    rng.shuffle(options)
    return Question(QType.MULTIPLE_CHOICE, Difficulty.MEDIUM,
                    prompt=f"אֵיזֶה גּוּף מַתְאִים לַתֵּאוּר: {descriptions[name]}?",
                    answer=name, options=options)


def gen_solid_faces(rng, qt):
    return Question(QType.OPEN_NUMERIC, Difficulty.EASY,
                    prompt="כַּמָּה פֵּאוֹת יֵשׁ לְקֻבִּיָּה?", answer=6,
                    explain="לְקֻבִּיָּה יֵשׁ 6 פֵּאוֹת רִבּוּעִיּוֹת.")


# ============================================================
#  השוואת נפחים / מבנים מקוביות
# ============================================================
def gen_cubes_count(rng, qt):
    layers = rng.randint(2, 4); per = rng.randint(2, 6)
    ans = layers * per
    return Question(QType.OPEN_NUMERIC, Difficulty.MEDIUM,
                    prompt=f"מִגְדָּל בָּנוּי מִ-{layers} שְׁכָבוֹת, וּבְכָל שִׁכְבָה {per} קֻבִּיּוֹת. כַּמָּה קֻבִּיּוֹת בַּמִּגְדָּל?",
                    answer=ans, explain=f"{layers} פְּעָמִים {per} זֶה {ans}.")


# ============================================================
#  זמן: שעות שלמות וחצאי שעות
# ============================================================
def gen_time(rng, qt):
    h = rng.randint(1, 12)
    half = rng.random() < 0.5
    if half:
        ans = f"{h}:30"
        prompt = f"הַשָּׁעוֹן מַרְאֶה {h} וָחֵצִי. אֵיךְ כּוֹתְבִים זֹאת?"
        opts = [f"{h}:30", f"{h}:00", f"{(h % 12) + 1}:30", f"{h}:15"]
    else:
        ans = f"{h}:00"
        prompt = f"הַשָּׁעוֹן מַרְאֶה {h} בְּדִיּוּק. אֵיךְ כּוֹתְבִים זֹאת?"
        opts = [f"{h}:00", f"{h}:30", f"{(h % 12) + 1}:00", f"{h}:45"]
    rng.shuffle(opts)
    return Question(QType.MULTIPLE_CHOICE, Difficulty.MEDIUM, prompt=prompt, answer=ans, options=opts,
                    payload={"clock_h": h, "clock_m": 30 if half else 0})


# ============================================================
#  חקר נתונים
# ============================================================
def gen_data_read(rng, qt):
    cats = rng.sample(["אָדֹם", "כָּחֹל", "יָרֹק", "צָהֹב"], 3)
    vals = [rng.randint(2, 12) for _ in cats]
    idx = rng.randint(0, len(cats) - 1)
    ask = rng.choice(["most", "value", "total"])
    if ask == "most":
        ans_cat = cats[vals.index(max(vals))]
        return Question(QType.MULTIPLE_CHOICE, Difficulty.EASY,
                        prompt="בַּדִּיאַגְרַמָּה: " + ", ".join(f"{c}={v}" for c, v in zip(cats, vals)) + ". אֵיזֶה הֲכִי הַרְבֵּה?",
                        answer=ans_cat, options=cats)
    if ask == "total":
        return Question(QType.OPEN_NUMERIC, Difficulty.MEDIUM,
                        prompt="בַּדִּיאַגְרַמָּה: " + ", ".join(f"{c}={v}" for c, v in zip(cats, vals)) + ". כַּמָּה בְּסַךְ הַכֹּל?",
                        answer=sum(vals))
    return Question(QType.OPEN_NUMERIC, Difficulty.EASY,
                    prompt="בַּדִּיאַגְרַמָּה: " + ", ".join(f"{c}={v}" for c, v in zip(cats, vals)) + f". כַּמָּה {cats[idx]}?",
                    answer=vals[idx])


# ============================================================
#  רישום כל התבניות
# ============================================================
def build_templates() -> list:
    return [
        Template("dec_value", N_DEC, Difficulty.MEDIUM, [QType.OPEN_NUMERIC], gen_dec_value),
        Template("dec_build", N_DEC, Difficulty.MEDIUM, [QType.OPEN_NUMERIC], gen_dec_build),
        Template("dec_compare", N_DEC, Difficulty.EASY, [QType.MULTIPLE_CHOICE], gen_dec_compare),
        Template("cnt_skip", N_CNT, Difficulty.MEDIUM, [QType.OPEN_NUMERIC], gen_cnt_skip),
        Template("cnt_next", N_CNT, Difficulty.EASY, [QType.OPEN_NUMERIC], gen_cnt_next),
        Template("even_tf", N_EVEN, Difficulty.EASY, [QType.TRUE_FALSE], gen_even),
        Template("even_pick", N_EVEN, Difficulty.MEDIUM, [QType.MULTIPLE_CHOICE], gen_even_pick),
        Template("seq2_missing", N_SEQ, Difficulty.MEDIUM, [QType.FILL_BLANK], gen_seq_missing),
        Template("seq2_rule", N_SEQ, Difficulty.CHALLENGE, [QType.OPEN_NUMERIC], gen_seq_rule),
        Template("add100", N_ADDSUB, Difficulty.EASY, [QType.OPEN_NUMERIC, QType.MULTIPLE_CHOICE], gen_add100),
        Template("sub100", N_ADDSUB, Difficulty.EASY, [QType.OPEN_NUMERIC, QType.MULTIPLE_CHOICE], gen_sub100),
        Template("word100", N_ADDSUB, Difficulty.MEDIUM, [QType.OPEN_NUMERIC], gen_word100),
        Template("missing100", N_ADDSUB, Difficulty.MEDIUM, [QType.FILL_BLANK], gen_missing100),
        Template("commute", N_ASPROP, Difficulty.MEDIUM, [QType.FILL_BLANK], gen_commute),
        Template("inverse", N_ASPROP, Difficulty.CHALLENGE, [QType.FILL_BLANK], gen_inverse),
        Template("mul", N_MULDIV, Difficulty.MEDIUM, [QType.OPEN_NUMERIC, QType.MULTIPLE_CHOICE], gen_mul),
        Template("div", N_MULDIV, Difficulty.MEDIUM, [QType.OPEN_NUMERIC], gen_div),
        Template("mul_groups", N_MULDIV, Difficulty.EASY, [QType.OPEN_NUMERIC], gen_mul_groups),
        Template("mul_commute", N_MDPROP, Difficulty.MEDIUM, [QType.FILL_BLANK], gen_mul_commute),
        Template("muldiv_inverse", N_MDPROP, Difficulty.CHALLENGE, [QType.FILL_BLANK], gen_muldiv_inverse),
        Template("poly_sides", N_POLY, Difficulty.EASY, [QType.OPEN_NUMERIC, QType.MULTIPLE_CHOICE], gen_poly_sides),
        Template("triangle", N_POLY, Difficulty.MEDIUM, [QType.MULTIPLE_CHOICE], gen_triangle),
        Template("right_angle", N_RIGHT, Difficulty.MEDIUM, [QType.MULTIPLE_CHOICE], gen_right_angle),
        Template("length_unit", N_LEN, Difficulty.EASY, [QType.MULTIPLE_CHOICE], gen_length_unit),
        Template("length_convert", N_LEN, Difficulty.MEDIUM, [QType.OPEN_NUMERIC], gen_length_convert),
        Template("broken_line", N_BROKEN, Difficulty.MEDIUM, [QType.OPEN_NUMERIC], gen_broken_line),
        Template("perimeter", N_PERIM, Difficulty.MEDIUM, [QType.OPEN_NUMERIC], gen_perimeter),
        Template("solid_id", N_SOLID, Difficulty.MEDIUM, [QType.MULTIPLE_CHOICE], gen_solid_id),
        Template("solid_faces", N_SOLID, Difficulty.EASY, [QType.OPEN_NUMERIC], gen_solid_faces),
        Template("cubes_count", N_CUBES, Difficulty.MEDIUM, [QType.OPEN_NUMERIC], gen_cubes_count),
        Template("vol_cubes", N_VOL, Difficulty.MEDIUM, [QType.OPEN_NUMERIC], gen_cubes_count),
        Template("time", N_TIME, Difficulty.MEDIUM, [QType.MULTIPLE_CHOICE], gen_time),
        Template("data_read", N_DATA, Difficulty.EASY, [QType.MULTIPLE_CHOICE, QType.OPEN_NUMERIC], gen_data_read),
    ]


def templates_for_node(node_id: str) -> list:
    return [t for t in build_templates() if t.node_id == node_id]
