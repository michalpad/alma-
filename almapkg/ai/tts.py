"""
ALMA — שכבת הקראה (Text-to-Speech).
קול עברי איכותי ומדויק לילדים. עיקרון מנחה: ה-LLM מחזיר טקסט מנוקד מלא
(speech), והמנוע הוגה לפי הניקוד — כך נפתרת בעיית ההגייה השגויה בעברית.

ספקים:
  • Azure Neural TTS  — דיוק הגייה גבוה דרך SSML + שליטה בפונמות וניקוד.
                        ברירת מחדל לדיוק. קולות עבריים נוירוניים.
  • ElevenLabs        — הטון האנושי והחם ביותר. מועדף כשרוצים חמימות מקסימלית.
  • Browser (fallback) — Web Speech API. רק כשאין רשת/מפתח. איכות נמוכה.

המפתחות מנוהלים בסביבת השרת (משתני סביבה / Key Vault). אין מפתחות בקוד.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class TTSProvider(str, Enum):
    AZURE = "azure"
    ELEVENLABS = "elevenlabs"
    BROWSER = "browser"


# ============================================================
#  פרופילי קול מותאמים-גיל לילדי יסודי
#  קצב איטי יותר וטון חם לצעירים; טבעי יותר למבוגרים.
# ============================================================
@dataclass
class VoiceProfile:
    # Azure: שם קול נוירוני עברי. שני קולות עבריים עיקריים: Avri (זכר), Hila (נקבה).
    azure_voice_male: str = "he-IL-AvriNeural"
    azure_voice_female: str = "he-IL-HilaNeural"
    # ElevenLabs: מזהי קול (multilingual v2 תומך עברית). מוזרק מבחוץ.
    eleven_voice_male: str = ""
    eleven_voice_female: str = ""
    # כוונון פרוזודיה לפי שכבת גיל
    rate: float = 1.0     # 1.0 = רגיל; <1 איטי יותר
    pitch: float = 0.0    # סמיטונים; חיובי = גבוה/צעיר יותר


# התאמת פרוזודיה לפי שכבת גיל (תואם age_band מהמערכת)
AGE_PROSODY = {
    "a-b": VoiceProfile(rate=0.85, pitch=2.0),   # כיתות א-ב: איטי וחם
    "c-d": VoiceProfile(rate=0.92, pitch=1.0),   # כיתות ג-ד
    "e-f": VoiceProfile(rate=0.98, pitch=0.0),   # כיתות ה-ו: כמעט טבעי
}


@dataclass
class TTSConfig:
    provider: TTSProvider = TTSProvider.AZURE
    age_band: str = "c-d"
    gender: str = "female"          # קול ברירת מחדל (תואם voice_choice של התלמיד)
    timeout_s: float = 8.0
    # פרופיל קול; אם None — נגזר מ-AGE_PROSODY
    profile: Optional[VoiceProfile] = None
    eleven_ids: dict = field(default_factory=dict)  # {"male": id, "female": id}


@dataclass
class TTSResult:
    audio: bytes = b""              # אודיו מקודד (mp3/wav) — מנוגן בצד הלקוח
    mime: str = "audio/mpeg"
    provider: str = ""
    # אם נופלים ל-browser, אין אודיו — הלקוח משמיע מקומית מהטקסט:
    browser_fallback_text: str = ""


# ============================================================
#  עזרי ניקוד / SSML
# ============================================================
NIQQUD_RE = re.compile(r"[\u0591-\u05C7]")  # טווח סימני הניקוד והטעמים


def has_niqqud(text: str) -> bool:
    """בודק אם הטקסט מנוקד — תנאי לדיוק הגייה גבוה."""
    return bool(NIQQUD_RE.search(text))


def _xml_escape(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;")
             .replace(">", "&gt;").replace('"', "&quot;"))


def build_ssml(text: str, voice: str, rate: float, pitch: float) -> str:
    """
    בונה SSML ל-Azure. שולח את הטקסט המנוקד כמות שהוא — מנוע Azure
    מכבד את הניקוד העברי. prosody שולט בקצב ובגובה לטון חם ומותאם-גיל.
    """
    rate_pct = f"{int((rate - 1) * 100):+d}%"      # למשל -15%
    pitch_st = f"{pitch:+.0f}st"                     # סמיטונים
    safe = _xml_escape(text)
    return (
        '<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" '
        'xml:lang="he-IL">'
        f'<voice name="{voice}">'
        f'<prosody rate="{rate_pct}" pitch="{pitch_st}">{safe}</prosody>'
        '</voice></speak>'
    )


# ============================================================
#  מנוע ההקראה
# ============================================================
class TTSEngine:
    def __init__(self, config: Optional[TTSConfig] = None):
        self.cfg = config or TTSConfig()
        self.profile = self.cfg.profile or AGE_PROSODY.get(
            self.cfg.age_band, VoiceProfile())

    def _voice_name(self) -> str:
        p = self.profile
        if self.cfg.provider is TTSProvider.AZURE:
            return p.azure_voice_female if self.cfg.gender == "female" else p.azure_voice_male
        # ElevenLabs — מזהים מוזרקים דרך config.eleven_ids
        return self.cfg.eleven_ids.get(self.cfg.gender, "")

    async def synthesize(self, text: str, http_client=None) -> TTSResult:
        """
        ממיר טקסט (רצוי מנוקד) לאודיו. בוחר ספק לפי config, עם נפילה
        חיננית ל-browser אם השירות לא זמין.
        """
        if not text or not text.strip():
            return TTSResult(provider="none")

        try:
            if self.cfg.provider is TTSProvider.AZURE:
                return await self._azure(text, http_client)
            if self.cfg.provider is TTSProvider.ELEVENLABS:
                return await self._elevenlabs(text, http_client)
        except Exception:
            # נפילה חיננית: הלקוח ישמיע דרך Web Speech API מהטקסט.
            return TTSResult(provider="browser", browser_fallback_text=text)

        return TTSResult(provider="browser", browser_fallback_text=text)

    # ----- Azure Neural TTS (דיוק הגייה דרך SSML מנוקד) -----
    async def _azure(self, text: str, http_client) -> TTSResult:
        region = os.environ["AZURE_TTS_REGION"]
        key = os.environ["AZURE_TTS_KEY"]
        url = f"https://{region}.tts.speech.microsoft.com/cognitiveservices/v1"
        ssml = build_ssml(text, self._voice_name(),
                          self.profile.rate, self.profile.pitch)
        resp = await http_client.post(
            url,
            headers={
                "Ocp-Apim-Subscription-Key": key,
                "Content-Type": "application/ssml+xml",
                # פורמט אודיו איכותי
                "X-Microsoft-OutputFormat": "audio-24khz-96kbitrate-mono-mp3",
                "User-Agent": "alma-tts",
            },
            content=ssml.encode("utf-8"),
            timeout=self.cfg.timeout_s,
        )
        resp.raise_for_status()
        return TTSResult(audio=resp.content, mime="audio/mpeg", provider="azure")

    # ----- ElevenLabs (הטון החם והאנושי ביותר) -----
    async def _elevenlabs(self, text: str, http_client) -> TTSResult:
        key = os.environ["ELEVENLABS_API_KEY"]
        voice_id = self._voice_name()
        if not voice_id:
            raise ValueError("ElevenLabs voice id missing for gender "
                             f"{self.cfg.gender}")
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        resp = await http_client.post(
            url,
            headers={"xi-api-key": key, "Content-Type": "application/json"},
            json={
                "text": text,
                "model_id": "eleven_multilingual_v2",   # תומך עברית
                "voice_settings": {
                    # יציבות גבוהה לעקביות, similarity לחמימות,
                    # style מתון לטון מורה ידידותי ולא דרמטי
                    "stability": 0.55,
                    "similarity_boost": 0.80,
                    "style": 0.25,
                    "use_speaker_boost": True,
                },
            },
            timeout=self.cfg.timeout_s,
        )
        resp.raise_for_status()
        return TTSResult(audio=resp.content, mime="audio/mpeg",
                         provider="elevenlabs")


# ============================================================
#  מפעל נוחות — בונה מנוע מוכן לחיבור
# ============================================================
def build_tts(provider: str = "azure", *, age_band: str = "c-d",
              gender: str = "female", eleven_ids: Optional[dict] = None) -> TTSEngine:
    """
    בונה מנוע TTS. דוגמה:
        engine = build_tts("azure", age_band="a-b", gender="female")
        result = await engine.synthesize(nikud_text, http_client=httpx_client)
        # result.audio -> לנגן בצד הלקוח; אם provider=='browser' -> fallback
    """
    cfg = TTSConfig(
        provider=TTSProvider(provider),
        age_band=age_band,
        gender=gender,
        eleven_ids=eleven_ids or {},
    )
    return TTSEngine(cfg)
