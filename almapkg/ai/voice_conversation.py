"""אלמה — שיחה קולית דו-כיוונית. הילד מדבר, אלמה מקשיבה ומגיבה כמורה."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class STTProvider(str, Enum):
    AZURE = "azure"
    BROWSER = "browser"


@dataclass
class STTConfig:
    provider: STTProvider = STTProvider.AZURE
    language: str = "he-IL"
    max_listen_seconds: float = 5.0
    min_confidence: float = 0.45


@dataclass
class STTResult:
    text: str = ""
    confidence: float = 0.0
    provider: str = "azure"
    low_confidence: bool = False
    browser_fallback: bool = False

    @property
    def heard_something(self) -> bool:
        return bool(self.text.strip())


async def transcribe(audio, cfg: Optional[STTConfig] = None, http_client=None) -> STTResult:
    cfg = cfg or STTConfig()
    if http_client is None:
        return STTResult(provider="browser", browser_fallback=True)
    return STTResult(provider=str(cfg.provider.value))


def gentle_retry_prompt(age_band: str) -> str:
    if age_band == "a_b":
        return "לא שמעתי טוב — תגיד/י לי שוב, לאט?"
    return "רגע, לא קלטתי טוב. אפשר להגיד לי שוב?"


class ExplanationVerdict(str, Enum):
    SOUND = "sound"
    PARTIAL = "partial"
    MISCONCEPTION = "miscon"
    UNCLEAR = "unclear"


@dataclass
class TeacherResponse:
    verdict: ExplanationVerdict
    say: str
    affirms: bool = False
    extends: bool = False
    corrects: bool = False
    invites_more: bool = False
    advance_to_next: bool = False
    drop_level: bool = False


def fallback_teacher_response(age_band: str) -> TeacherResponse:
    say = ("יפה שסיפרת לי איך חשבת! בוא נמשיך."
           if age_band == "a_b" else
           "אהבתי לשמוע איך חשבת על זה. בוא נמשיך הלאה.")
    return TeacherResponse(verdict=ExplanationVerdict.PARTIAL, say=say,
                           affirms=True, advance_to_next=True)


def parse_teacher_response(raw: dict, age_band: str) -> TeacherResponse:
    try:
        verdict = ExplanationVerdict(raw.get("verdict", "partial"))
        say = str(raw.get("say", "")).strip()
        if not say:
            return fallback_teacher_response(age_band)
        return TeacherResponse(
            verdict=verdict, say=say,
            affirms=bool(raw.get("affirms", False)),
            extends=bool(raw.get("extends", False)),
            corrects=bool(raw.get("corrects", False)),
            invites_more=bool(raw.get("invites_more", False)),
        )
    except (ValueError, AttributeError, TypeError):
        return fallback_teacher_response(age_band)


MAX_EXPLANATION_ATTEMPTS = 2
_NOT_THERE_YET = {ExplanationVerdict.MISCONCEPTION, ExplanationVerdict.UNCLEAR}


@dataclass
class ConversationTurnState:
    attempts: int = 0
    resolved: bool = False
    released: bool = False

    def register(self, verdict: ExplanationVerdict) -> None:
        self.attempts += 1
        if verdict not in _NOT_THERE_YET:
            self.resolved = True

    @property
    def should_release(self) -> bool:
        return (not self.resolved) and (self.attempts >= MAX_EXPLANATION_ATTEMPTS)


def graceful_release_response(age_band: str, drop_level: bool = True) -> TeacherResponse:
    if age_band == "a_b":
        say = "זה בסדר גמור! בוא נראה את זה יחד פעם אחת, וממשיכים לתרגיל הבא. אתה מצוין!"
    else:
        say = "לא נורא בכלל — נראה את זה יחד, וממשיכים הלאה. אתה בדרך הנכונה!"
    return TeacherResponse(verdict=ExplanationVerdict.PARTIAL, say=say,
                           affirms=True, extends=True, advance_to_next=True, drop_level=drop_level)


def next_response(raw_llm: dict, state: ConversationTurnState, age_band: str) -> TeacherResponse:
    resp = parse_teacher_response(raw_llm, age_band)
    state.register(resp.verdict)
    if state.should_release and not state.released:
        state.released = True
        return graceful_release_response(age_band, drop_level=True)
    if state.resolved:
        resp.advance_to_next = True
        return resp
    return resp
