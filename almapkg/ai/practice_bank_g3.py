"""
ALMA — בנק תרגול מלא לכיתה ג' (מתמטיקה).
מכסה את כל נושאי כיתה ג' מתכנית הלימודים, בכל רמות הקושי.
כל מחולל מחשב את תשובתו הנכונה -> נכונות מובטחת בשרת.

נושאים (תואם math_grade3_curriculum.sql):
  מספרים: מבנה עשרוני עד 10,000, גימטרייה, סדרות
  פעולות: חיבור/חיסור בהרבבה, לוח הכפל 10×10, סימני התחלקות 2/5/10,
          חילוק עם שארית, חוק הפילוג וסדר פעולות, כפל/חילוק בהרבבה, עיגול
  גאומטריה: זוויות, מיון משולשים
  שטח: השוואה ומדידה, שטח מלבן
  תיבות: פריסה
  זמן: שעות ודקות
  חקר נתונים: כולל דיאגרמה כפולה
"""
from __future__ import annotations

import random

from .practice_engine import Question, QType, Difficulty, Template

# ---- מזהי צמתים (כיתה ג') ----
N_DEC = "c1000000-0000-4000-8000-000000000010"     # מבנה עשרוני עד 10,000
N_GIM = "c1000000-0000-4000-8000-000000000020"     # גימטרייה
N_SEQ = "c1000000-0000-4000-8000-000000000030"     # סדרות
N_ADDSUB = "c2000000-0000-4000-8000-000000000010"  # חיבור/חיסור בהרבבה
N_MUL = "c2000000-0000-4000-8000-000000000020"     # לוח הכפל 10×10
N_DIVRULE = "c2000000-0000-4000-8000-000000000030" # סימני התחלקות 2/5/10
N_REM = "c2000000-0000-4000-8000-000000000040"     # חילוק עם שארית
N_DIST = "c2000000-0000-4000-8000-000000000050"    # חוק הפילוג וסדר פעולות
N_MULBIG = "c2000000-0000-4000-8000-000000000060"  # כפל/חילוק בהרבבה
N_ROUND = "c2000000-0000-4000-8000-000000000070"   # עיגול
N_ANG = "c3000000-0000-4000-8000-000000000010"     # זוויות
N_TRI = "c3000000-0000-4000-8000-000000000020"     # מיון משולשים
N_AREACMP = "c4000000-0000-4000-8000-000000000010" # שטח — השוואה ומדידה
N_AREA = "c4000000-0000-4000-8000-000000000020"    # שטח מלבן
N_NET = "c5000000-0000-4000-8000-000000000010"     # פריסת תיבה
N_TIME = "c6000000-0000-4000-8000-000000000010"    # שעות ודקות
N_DATA = "c7000000-0000-4000-8000-000000000010"    # חקר נתונים


def _mc(rng, correct, lo=0, hi=10000, k=4, spread=(-100, -10, -5, -2, -1, 1, 2, 5, 10, 100)):
    opts = {correct}; g = 0
    while len(opts) < k and g < 100:
        v = correct + rng.choice(spread); g += 1
        if lo <= v <= hi:
            opts.add(v)
    opts = list(opts); rng.shuffle(opts)
    return opts


# ============================================================
#  מבנה עשרוני עד 10,000
# ============================================================
def gen_dec_value(rng, qt):
    n = rng.randint(1000, 9999)
    digits = {"אֲלָפִים": n // 1000, "מֵאוֹת": (n // 100) % 10,
              "עֲשָׂרוֹת": (n // 10) % 10, "יְחִידוֹת": n % 10}
    place = rng.choice(list(digits))
    return Question(QType.OPEN_NUMERIC, Difficulty.MEDIUM,
                    prompt=f"בַּמִּסְפָּר {n}, כַּמָּה {place} יֵשׁ?", answer=digits[place],
                    explain=f"{n} = {digits['אֲלָפִים']} אֲלָפִים, {digits['מֵאוֹת']} מֵאוֹת, {digits['עֲשָׂרוֹת']} עֲשָׂרוֹת, {digits['יְחִידוֹת']} יְחִידוֹת.")


def gen_dec_x10(rng, qt):
    """הגדלה/הקטנה פי 10 ו-100."""
    n = rng.randint(2, 90)
    factor = rng.choice([10, 100])
    return Question(QType.OPEN_NUMERIC, Difficulty.MEDIUM,
                    prompt=f"כַּמָּה זֶה {n} כָּפוּל {factor}?", answer=n * factor,
                    payload={"formula": f"{n} × {factor} ="})


def gen_dec_compare(rng, qt):
    a = rng.randint(1000, 9999); b = rng.randint(1000, 9999)
    while a == b:
        b = rng.randint(1000, 9999)
    return Question(QType.MULTIPLE_CHOICE, Difficulty.EASY,
                    prompt=f"אֵיזֶה סִימָן מַתְאִים?  {a} __ {b}",
                    answer=">" if a > b else "<", options=[">", "<"],
                    payload={"cmp_a": a, "cmp_b": b})


# ============================================================
#  גימטרייה (ערכי אותיות א-ת)
# ============================================================
GIMATRIA = {"א": 1, "ב": 2, "ג": 3, "ד": 4, "ה": 5, "ו": 6, "ז": 7, "ח": 8, "ט": 9,
            "י": 10, "כ": 20, "ל": 30, "מ": 40, "נ": 50, "ס": 60, "ע": 70, "פ": 80, "צ": 90,
            "ק": 100, "ר": 200, "ש": 300, "ת": 400}


def gen_gim_letter(rng, qt):
    letter = rng.choice(list(GIMATRIA))
    return Question(QType.OPEN_NUMERIC, Difficulty.EASY,
                    prompt=f"מַה הַעֵרֶךְ הַגִּימַטְרִי שֶׁל הָאוֹת {letter}?",
                    answer=GIMATRIA[letter])


def gen_gim_word(rng, qt):
    words = ["אַבָּא", "אִמָּא", "יָד", "דָּג", "גַּן", "אָב"]
    word = rng.choice(words)
    bare = word.replace("ָ", "").replace("ַ", "").replace("ּ", "").replace("ִ", "").replace("ְ", "")
    total = sum(GIMATRIA.get(c, 0) for c in bare)
    return Question(QType.OPEN_NUMERIC, Difficulty.MEDIUM,
                    prompt=f"מַה הַעֵרֶךְ הַגִּימַטְרִי שֶׁל הַמִּלָּה \"{word}\"?",
                    answer=total, explain="מְחַבְּרִים אֶת עֶרְכֵי הָאוֹתִיּוֹת.")


# ============================================================
#  סדרות
# ============================================================
def gen_seq_missing(rng, qt):
    step = rng.choice([10, 20, 25, 50, 100, 250, 500])
    start = rng.randint(0, 500)
    seq = [start + step * i for i in range(5)]
    hole = rng.randint(1, 3)
    shown = [str(x) if i != hole else "___" for i, x in enumerate(seq)]
    return Question(QType.FILL_BLANK, Difficulty.MEDIUM,
                    prompt="אֵיזֶה מִסְפָּר חָסֵר?  " + ", ".join(shown),
                    answer=seq[hole], explain=f"הַסִּדְרָה עוֹלָה בְּ-{step}.")


def gen_seq_mult(rng, qt):
    """סדרת מכפלות."""
    base = rng.randint(2, 9)
    seq = [base * i for i in range(1, 5)]
    return Question(QType.OPEN_NUMERIC, Difficulty.CHALLENGE,
                    prompt=f"הַמְשִׁיכוּ אֶת סִדְרַת הַמַּכְפֵּלוֹת: {seq[0]}, {seq[1]}, {seq[2]}, {seq[3]}, וּמָה הַבָּא?",
                    answer=base * 5, explain=f"מַכְפֵּלוֹת שֶׁל {base}.")


# ============================================================
#  חיבור וחיסור בהרבבה
# ============================================================
def gen_add_big(rng, qt):
    a = rng.randint(100, 4999); b = rng.randint(100, 4999)
    return Question(QType.OPEN_NUMERIC, Difficulty.MEDIUM, prompt="פִּתְרוּ אֶת הַתַּרְגִּיל:",
                    answer=a + b, payload={"formula": f"{a} + {b} ="})


def gen_sub_big(rng, qt):
    a = rng.randint(1000, 9999); b = rng.randint(100, a)
    return Question(QType.OPEN_NUMERIC, Difficulty.MEDIUM, prompt="פִּתְרוּ אֶת הַתַּרְגִּיל:",
                    answer=a - b, payload={"formula": f"{a} − {b} ="})


def gen_missing_big(rng, qt):
    a = rng.randint(100, 5000); ans = rng.randint(100, 4000); total = a + ans
    return Question(QType.FILL_BLANK, Difficulty.CHALLENGE, prompt="אֵיזֶה מִסְפָּר חָסֵר?",
                    answer=ans, payload={"formula": f"{a} + ___ = {total}"})


# ============================================================
#  לוח הכפל 10×10
# ============================================================
def gen_mul_table(rng, qt):
    a = rng.randint(2, 10); b = rng.randint(2, 10)
    ans = a * b
    if qt == QType.MULTIPLE_CHOICE:
        return Question(qt, Difficulty.MEDIUM, prompt="מַהִי הַמַּכְפֵּלָה?", answer=ans,
                        options=_mc(rng, ans, hi=100, spread=(-a, a, -b, b, -1, 1, 2)),
                        payload={"formula": f"{a} × {b} ="})
    return Question(QType.OPEN_NUMERIC, Difficulty.MEDIUM, prompt="פִּתְרוּ:",
                    answer=ans, payload={"formula": f"{a} × {b} ="})


def gen_div_table(rng, qt):
    b = rng.randint(2, 10); q = rng.randint(2, 10)
    a = b * q
    return Question(QType.OPEN_NUMERIC, Difficulty.MEDIUM, prompt="פִּתְרוּ אֶת הַחִלּוּק:",
                    answer=q, payload={"formula": f"{a} ÷ {b} ="}, explain=f"כִּי {b} × {q} = {a}.")


# ============================================================
#  סימני התחלקות ב-2, ב-5 וב-10
# ============================================================
def gen_divrule(rng, qt):
    d = rng.choice([2, 5, 10])
    n = rng.randint(10, 200)
    divisible = (n % d == 0)
    return Question(QType.TRUE_FALSE, Difficulty.MEDIUM,
                    prompt=f"נָכוֹן אוֹ לֹא נָכוֹן? הַמִּסְפָּר {n} מִתְחַלֵּק בְּ-{d} לְלֹא שְׁאֵרִית.",
                    answer=divisible,
                    explain=f"בּוֹדְקִים אֶת סִפְרַת הַיְחִידוֹת.")


# ============================================================
#  חילוק עם שארית
# ============================================================
def gen_remainder(rng, qt):
    b = rng.randint(2, 9)
    q = rng.randint(2, 9)
    r = rng.randint(1, b - 1)
    a = b * q + r
    ask_q = rng.random() < 0.5
    if ask_q:
        return Question(QType.OPEN_NUMERIC, Difficulty.CHALLENGE,
                        prompt=f"בַּחִלּוּק {a} ÷ {b}, מַהִי הַמָּנָה (הַחֵלֶק הַשָּׁלֵם)?",
                        answer=q, explain=f"{b} נִכְנָס {q} פְּעָמִים בְּ-{a}, וְנִשְׁאָר {r}.")
    return Question(QType.OPEN_NUMERIC, Difficulty.CHALLENGE,
                    prompt=f"בַּחִלּוּק {a} ÷ {b}, מַהִי הַשְּׁאֵרִית?",
                    answer=r, explain=f"{b} × {q} = {b*q}, וְ-{a} פָּחוֹת {b*q} זֶה {r}.")


# ============================================================
#  חוק הפילוג וסדר פעולות
# ============================================================
def gen_order_ops(rng, qt):
    a = rng.randint(2, 9); b = rng.randint(2, 9); c = rng.randint(2, 9)
    # כפל לפני חיבור
    ans = a + b * c
    return Question(QType.OPEN_NUMERIC, Difficulty.CHALLENGE,
                    prompt="פִּתְרוּ לְפִי סֵדֶר הַפְּעוּלוֹת (כֶּפֶל לִפְנֵי חִבּוּר):",
                    answer=ans, payload={"formula": f"{a} + {b} × {c} ="},
                    explain=f"קֹדֶם {b}×{c}={b*c}, וְאָז + {a}.")


def gen_distribute(rng, qt):
    a = rng.randint(2, 9); b = rng.randint(10, 20)
    ans = a * b
    return Question(QType.OPEN_NUMERIC, Difficulty.CHALLENGE,
                    prompt=f"הֵעָזְרוּ בְּחוֹק הַפִּילּוּג: {a} × {b}. מַהִי הַתּוֹצָאָה?",
                    answer=ans, explain=f"{a}×{b} = {a}×{b//10*10} + {a}×{b%10}.")


# ============================================================
#  כפל וחילוק בהרבבה (×10/100/1000)
# ============================================================
def gen_mul_big(rng, qt):
    a = rng.randint(2, 9); factor = rng.choice([10, 100, 1000])
    return Question(QType.OPEN_NUMERIC, Difficulty.MEDIUM, prompt="פִּתְרוּ:",
                    answer=a * factor, payload={"formula": f"{a} × {factor} ="})


def gen_mul_tens(rng, qt):
    a = rng.randint(2, 9); tens = rng.choice([20, 30, 40, 50, 200, 300])
    return Question(QType.OPEN_NUMERIC, Difficulty.MEDIUM, prompt="פִּתְרוּ:",
                    answer=a * tens, payload={"formula": f"{a} × {tens} ="})


def gen_div_big(rng, qt):
    factor = rng.choice([10, 100]); q = rng.randint(2, 9)
    a = factor * q
    return Question(QType.OPEN_NUMERIC, Difficulty.MEDIUM, prompt="פִּתְרוּ:",
                    answer=q, payload={"formula": f"{a} ÷ {factor} ="})


# ============================================================
#  עיגול מספרים
# ============================================================
def gen_round(rng, qt):
    target = rng.choice([10, 100])
    n = rng.randint(target + 5, 9999)
    rounded = round(n / target) * target
    word = "עֲשֶׂרֶת" if target == 10 else "מֵאָה"
    return Question(QType.OPEN_NUMERIC, Difficulty.MEDIUM,
                    prompt=f"עַגְּלוּ אֶת {n} לַ{word} הַקְּרוֹבָה.",
                    answer=rounded, explain=f"בּוֹדְקִים אִם לְעַגֵּל מַעְלָה אוֹ מַטָּה.")


# ============================================================
#  זוויות
# ============================================================
def gen_angle(rng, qt):
    angles = {"חַדָּה": "קְטַנָּה מִזָּוִית יְשָׁרָה", "יְשָׁרָה": "כְּמוֹ פִּנַּת דַּף",
              "קְהָה": "גְּדוֹלָה מִזָּוִית יְשָׁרָה", "שְׁטוּחָה": "יְשָׁרָה לְגַמְרֵי, כְּמוֹ קַו"}
    name = rng.choice(list(angles))
    return Question(QType.MULTIPLE_CHOICE, Difficulty.MEDIUM,
                    prompt=f"זָוִית שֶׁהִיא {angles[name]} נִקְרֵאת:",
                    answer=name, options=list(angles.keys()))


# ============================================================
#  מיון משולשים
# ============================================================
def gen_triangle(rng, qt):
    qs = [("מְשֻׁלָּשׁ שֶׁיֵּשׁ בּוֹ זָוִית יְשָׁרָה נִקְרָא:", "יְשַׁר-זָוִית",
           ["יְשַׁר-זָוִית", "חַד-זָוִיּוֹת", "קְהֵה-זָוִית"]),
          ("מְשֻׁלָּשׁ שֶׁכָּל זָוִיּוֹתָיו חַדּוֹת נִקְרָא:", "חַד-זָוִיּוֹת",
           ["יְשַׁר-זָוִית", "חַד-זָוִיּוֹת", "קְהֵה-זָוִית"])]
    prompt, ans, opts = rng.choice(qs)
    return Question(QType.MULTIPLE_CHOICE, Difficulty.MEDIUM, prompt=prompt, answer=ans, options=opts)


# ============================================================
#  שטח — השוואה ומדידה / שטח מלבן
# ============================================================
def gen_area_count(rng, qt):
    w = rng.randint(2, 8); h = rng.randint(2, 8)
    return Question(QType.OPEN_NUMERIC, Difficulty.EASY,
                    prompt=f"מַלְבֵּן מְכֻסֶּה מִשְׁבְּצוֹת: {w} בְּשׁוּרָה, {h} שׁוּרוֹת. כַּמָּה מִשְׁבְּצוֹת בְּסַךְ הַכֹּל?",
                    answer=w * h, explain=f"{w} × {h} = {w*h}.")


def gen_area_rect(rng, qt):
    w = rng.randint(2, 12); h = rng.randint(2, 12)
    return Question(QType.OPEN_NUMERIC, Difficulty.MEDIUM,
                    prompt=f"מַהוּ שֶׁטַח מַלְבֵּן שֶׁאָרְכּוֹ {w} סֶ\"מ וְרָחְבּוֹ {h} סֶ\"מ?",
                    answer=w * h, explain=f"שֶׁטַח מַלְבֵּן = אֹרֶךְ × רֹחַב = {w}×{h}.",
                    payload={"formula": f"{w} × {h} ="})


# ============================================================
#  פריסת תיבה
# ============================================================
def gen_net(rng, qt):
    return Question(QType.MULTIPLE_CHOICE, Difficulty.MEDIUM,
                    prompt="כַּמָּה פֵּאוֹת יֵשׁ בִּפְרִישָׂה שֶׁל תֵּבָה?",
                    answer=6, options=[4, 5, 6, 8])


# ============================================================
#  מדידת זמן בשעות ובדקות
# ============================================================
def gen_time(rng, qt):
    h = rng.randint(1, 12); m = rng.choice([0, 15, 30, 45])
    ans = f"{h}:{m:02d}"
    distract = {f"{h}:{(m+15)%60:02d}", f"{(h%12)+1}:{m:02d}", f"{h}:{(m+30)%60:02d}"}
    opts = list(distract | {ans})[:4]
    if ans not in opts:
        opts[0] = ans
    rng.shuffle(opts)
    return Question(QType.MULTIPLE_CHOICE, Difficulty.MEDIUM,
                    prompt=f"הַשָּׁעוֹן מַרְאֶה {h} וְ-{m} דַּקּוֹת. אֵיךְ כּוֹתְבִים?",
                    answer=ans, options=opts, payload={"clock_h": h, "clock_m": m})


def gen_time_duration(rng, qt):
    start = rng.randint(1, 8); dur = rng.randint(1, 4)
    return Question(QType.OPEN_NUMERIC, Difficulty.MEDIUM,
                    prompt=f"הַשִּׁעוּר הִתְחִיל בְּשָׁעָה {start} וְנִמְשַׁךְ {dur} שָׁעוֹת. בְּאֵיזוֹ שָׁעָה הִסְתַּיֵּם?",
                    answer=start + dur, explain=f"{start} + {dur} = {start+dur}.")


# ============================================================
#  חקר נתונים (כולל דיאגרמה כפולה)
# ============================================================
def gen_data(rng, qt):
    cats = rng.sample(["א", "ב", "ג", "ד"], 3)
    vals = [rng.randint(5, 30) for _ in cats]
    ask = rng.choice(["diff", "total", "most"])
    data_str = ", ".join(f"{c}={v}" for c, v in zip(cats, vals))
    if ask == "diff":
        i, j = 0, 1
        return Question(QType.OPEN_NUMERIC, Difficulty.MEDIUM,
                        prompt=f"בַּדִּיאַגְרַמָּה: {data_str}. בְּכַמָּה {cats[i]} גָּדוֹל מִ-{cats[j]}? (אוֹ לְהֵפֶךְ, הַפֶּרֶשׁ)",
                        answer=abs(vals[i] - vals[j]))
    if ask == "total":
        return Question(QType.OPEN_NUMERIC, Difficulty.MEDIUM,
                        prompt=f"בַּדִּיאַגְרַמָּה: {data_str}. מַה הַסַּךְ הַכּוֹלֵל?",
                        answer=sum(vals))
    return Question(QType.MULTIPLE_CHOICE, Difficulty.EASY,
                    prompt=f"בַּדִּיאַגְרַמָּה: {data_str}. אֵיזֶה הֲכִי הַרְבֵּה?",
                    answer=cats[vals.index(max(vals))], options=cats)


# ============================================================
#  רישום
# ============================================================
def build_templates() -> list:
    return [
        Template("dec_value3", N_DEC, Difficulty.MEDIUM, [QType.OPEN_NUMERIC], gen_dec_value),
        Template("dec_x10", N_DEC, Difficulty.MEDIUM, [QType.OPEN_NUMERIC], gen_dec_x10),
        Template("dec_compare3", N_DEC, Difficulty.EASY, [QType.MULTIPLE_CHOICE], gen_dec_compare),
        Template("gim_letter", N_GIM, Difficulty.EASY, [QType.OPEN_NUMERIC], gen_gim_letter),
        Template("gim_word", N_GIM, Difficulty.MEDIUM, [QType.OPEN_NUMERIC], gen_gim_word),
        Template("seq3_missing", N_SEQ, Difficulty.MEDIUM, [QType.FILL_BLANK], gen_seq_missing),
        Template("seq3_mult", N_SEQ, Difficulty.CHALLENGE, [QType.OPEN_NUMERIC], gen_seq_mult),
        Template("add_big", N_ADDSUB, Difficulty.MEDIUM, [QType.OPEN_NUMERIC], gen_add_big),
        Template("sub_big", N_ADDSUB, Difficulty.MEDIUM, [QType.OPEN_NUMERIC], gen_sub_big),
        Template("missing_big", N_ADDSUB, Difficulty.CHALLENGE, [QType.FILL_BLANK], gen_missing_big),
        Template("mul_table", N_MUL, Difficulty.MEDIUM, [QType.OPEN_NUMERIC, QType.MULTIPLE_CHOICE], gen_mul_table),
        Template("div_table", N_MUL, Difficulty.MEDIUM, [QType.OPEN_NUMERIC], gen_div_table),
        Template("divrule", N_DIVRULE, Difficulty.MEDIUM, [QType.TRUE_FALSE], gen_divrule),
        Template("remainder", N_REM, Difficulty.CHALLENGE, [QType.OPEN_NUMERIC], gen_remainder),
        Template("order_ops", N_DIST, Difficulty.CHALLENGE, [QType.OPEN_NUMERIC], gen_order_ops),
        Template("distribute", N_DIST, Difficulty.CHALLENGE, [QType.OPEN_NUMERIC], gen_distribute),
        Template("mul_big", N_MULBIG, Difficulty.MEDIUM, [QType.OPEN_NUMERIC], gen_mul_big),
        Template("mul_tens", N_MULBIG, Difficulty.MEDIUM, [QType.OPEN_NUMERIC], gen_mul_tens),
        Template("div_big", N_MULBIG, Difficulty.MEDIUM, [QType.OPEN_NUMERIC], gen_div_big),
        Template("round3", N_ROUND, Difficulty.MEDIUM, [QType.OPEN_NUMERIC], gen_round),
        Template("angle", N_ANG, Difficulty.MEDIUM, [QType.MULTIPLE_CHOICE], gen_angle),
        Template("triangle3", N_TRI, Difficulty.MEDIUM, [QType.MULTIPLE_CHOICE], gen_triangle),
        Template("area_count", N_AREACMP, Difficulty.EASY, [QType.OPEN_NUMERIC], gen_area_count),
        Template("area_rect", N_AREA, Difficulty.MEDIUM, [QType.OPEN_NUMERIC], gen_area_rect),
        Template("net", N_NET, Difficulty.MEDIUM, [QType.MULTIPLE_CHOICE], gen_net),
        Template("time3", N_TIME, Difficulty.MEDIUM, [QType.MULTIPLE_CHOICE], gen_time),
        Template("time_dur", N_TIME, Difficulty.MEDIUM, [QType.OPEN_NUMERIC], gen_time_duration),
        Template("data3", N_DATA, Difficulty.MEDIUM, [QType.MULTIPLE_CHOICE, QType.OPEN_NUMERIC], gen_data),
    ]


def templates_for_node(node_id: str) -> list:
    return [t for t in build_templates() if t.node_id == node_id]
