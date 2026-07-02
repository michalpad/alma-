"""
ALMA — ניהול זמני השהיה לתשובה קולית.
משימה 2. זמן ההמתנה נקבע לפי שכבת הגיל:
  כיתות א-ב: 5.0 שניות | ג-ד: 3.5 שניות | ה-ו: 2.5 שניות.

כלל מהאפיון: אם הילד התחיל לדבר אך לא סיים, נותנים לו הזדמנות נוספת
לפני שמעודדים שוב או נותנים רמז. כן מוגדר זיהוי דובר יחיד להתעלמות מרעשי רקע.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass

# זמני המתנה בסיסיים (שניות) לפי שכבת גיל.
TIMEOUT_BY_AGE_BAND = {
    "a-b": 5.0,
    "c-d": 3.5,
    "e-f": 2.5,
}

# חלון חסד נוסף אם הילד התחיל לדבר אך עוד לא סיים.
GRACE_EXTENSION = 1.5


@dataclass
class VoiceTurnResult:
    outcome: str          # 'answered' | 'silence' | 'partial_then_timeout'
    transcript: str = ""


async def wait_for_voice_answer(
    age_band: str,
    stt_stream,                # אובייקט STT עם flags: speech_started, is_final, text
    speaker_id_locked: bool = True,
) -> VoiceTurnResult:
    """
    ממתין לתשובה קולית בזמן המותאם לגיל.

    - אם הילד לא התחיל לדבר עד תום הזמן -> 'silence' (המערכת תעודד שוב).
    - אם התחיל לדבר אך לא סיים -> מאריכים בחלון חסד אחד לפני timeout.
    - מתעלם מרעשי רקע ע"י נעילת דובר יחיד (speaker_id_locked).
    """
    base = TIMEOUT_BY_AGE_BAND[age_band]
    elapsed = 0.0
    step = 0.1
    grace_given = False

    while True:
        await asyncio.sleep(step)
        elapsed += step

        # התעלמות מרעשי רקע: רק קלט מהדובר הנעול נחשב.
        if speaker_id_locked and not stt_stream.speaker_matches:
            continue

        if stt_stream.is_final:
            return VoiceTurnResult(outcome="answered", transcript=stt_stream.text)

        if elapsed >= base:
            # הילד התחיל לדבר אך לא סיים -> חלון חסד נוסף, פעם אחת
            if stt_stream.speech_started and not grace_given:
                grace_given = True
                base += GRACE_EXTENSION
                continue
            if stt_stream.speech_started:
                return VoiceTurnResult(
                    outcome="partial_then_timeout", transcript=stt_stream.text
                )
            return VoiceTurnResult(outcome="silence")


def timeout_for(age_band: str) -> float:
    """ערך הזמן הבסיסי — שימושי גם לצד הלקוח (טיימר ויזואלי)."""
    return TIMEOUT_BY_AGE_BAND[age_band]
