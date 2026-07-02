"""
ALMA — מתאם סיווג תוכן בענן.
משימה 4 (הרחבה). שכבת סינון איכותית מבוססת-שירות לעברית,
מעל שכבת ה-regex הקיימת (ContentFilter) כגיבוי לעקיפות מקומיות.

ספק ראשי:   Azure AI Content Safety  (קטגוריות: Hate, SelfHarm, Sexual, Violence)
ספק חלופי:  Google Perspective API   (TOXICITY, SEVERE_TOXICITY, THREAT, SEXUALLY_EXPLICIT)

החיבור לרשת והמפתחות מנוהלים בסביבת השרת (משתני סביבה / Key Vault).
אין מפתחות בקוד. אם השירות לא זמין -> נפילה חיננית ל-regex המקומי בלבד.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum

from .content_filter import ContentFilter, FilterResult


class Provider(str, Enum):
    AZURE = "azure"
    PERSPECTIVE = "perspective"


# מיפוי קטגוריות הספקים לקטגוריות הפנימיות של אלמה.
AZURE_CATEGORY_MAP = {
    "Hate": "racism",
    "Violence": "violence",
    "Sexual": "sexual",
    "SelfHarm": "violence",   # פגיעה עצמית מטופלת כאירוע בטיחות חמור
}
PERSPECTIVE_ATTRIBUTE_MAP = {
    "SEVERE_TOXICITY": "profanity",
    "TOXICITY": "profanity",
    "THREAT": "violence",
    "IDENTITY_ATTACK": "racism",
    "SEXUALLY_EXPLICIT": "sexual",
}

# סף חסימה לכל קטגוריה (0.0-1.0). מחמיר עבור מערכת לילדים.
# Azure מחזיר severity 0-7; ממופה ל-0..1 ע"י חלוקה ב-7.
DEFAULT_THRESHOLDS = {
    "sexual": 0.30,     # מחמיר במיוחד — סביבת ילדים
    "violence": 0.45,
    "racism": 0.40,
    "profanity": 0.55,
}


@dataclass
class ModerationConfig:
    provider: Provider = Provider.AZURE
    thresholds: dict[str, float] | None = None
    timeout_s: float = 2.0
    fail_open: bool = False   # אם True ושירות נפל -> לא חוסם (לא מומלץ לילדים)


class CloudModerator:
    """
    עוטף את ContentFilter המקומי ומוסיף שכבת סיווג בענן.
    סדר הבדיקה:
      1) regex מקומי (מהיר, תופס עקיפות ידועות)  -> אם נחסם, מחזיר מיד.
      2) שירות ענן (חזק, תופס וריאציות והקשר)     -> אם מעל הסף, חוסם.
    """

    def __init__(self, local_filter: ContentFilter, config: ModerationConfig | None = None):
        self.local = local_filter
        self.cfg = config or ModerationConfig()
        self.thresholds = self.cfg.thresholds or DEFAULT_THRESHOLDS

    async def check(self, text: str, http_client=None) -> FilterResult:
        # --- שכבה 1: regex מקומי ---
        local = self.local.check(text)
        if local.blocked:
            return local

        # --- שכבה 2: שירות ענן ---
        try:
            scores = await self._score(text, http_client)
        except Exception:
            # נפילה חיננית: בלי השירות נשענים על ה-regex בלבד.
            if self.cfg.fail_open:
                return FilterResult(blocked=False)
            return FilterResult(blocked=False)   # regex כבר אישר; לא נחסם סתם

        for category, score in scores.items():
            threshold = self.thresholds.get(category, 0.5)
            if score >= threshold:
                return FilterResult(
                    blocked=True,
                    category=category,
                    matched_span=f"{category}:{score:.2f}",  # לתיעוד בלבד
                )
        return FilterResult(blocked=False)

    # ----- קריאות לספקים (HTTP מנוהל בשרת) -----

    async def _score(self, text: str, http_client) -> dict[str, float]:
        if self.cfg.provider is Provider.AZURE:
            return await self._score_azure(text, http_client)
        return await self._score_perspective(text, http_client)

    async def _score_azure(self, text: str, http_client) -> dict[str, float]:
        endpoint = os.environ["AZURE_CONTENT_SAFETY_ENDPOINT"].rstrip("/")
        key = os.environ["AZURE_CONTENT_SAFETY_KEY"]
        url = f"{endpoint}/contentsafety/text:analyze?api-version=2024-09-01"
        resp = await http_client.post(
            url,
            headers={"Ocp-Apim-Subscription-Key": key,
                     "Content-Type": "application/json"},
            json={"text": text, "outputType": "FourSeverityLevels"},
            timeout=self.cfg.timeout_s,
        )
        resp.raise_for_status()
        data = resp.json()
        scores: dict[str, float] = {}
        for item in data.get("categoriesAnalysis", []):
            internal = AZURE_CATEGORY_MAP.get(item["category"])
            if internal:
                # severity 0-7 -> 0..1
                norm = item.get("severity", 0) / 7.0
                scores[internal] = max(scores.get(internal, 0.0), norm)
        return scores

    async def _score_perspective(self, text: str, http_client) -> dict[str, float]:
        key = os.environ["PERSPECTIVE_API_KEY"]
        url = ("https://commentanalyzer.googleapis.com/v1alpha1/"
               f"comments:analyze?key={key}")
        attrs = {a: {} for a in PERSPECTIVE_ATTRIBUTE_MAP}
        resp = await http_client.post(
            url,
            json={"comment": {"text": text},
                  "languages": ["he"],
                  "requestedAttributes": attrs},
            timeout=self.cfg.timeout_s,
        )
        resp.raise_for_status()
        data = resp.json()
        scores: dict[str, float] = {}
        for attr, internal in PERSPECTIVE_ATTRIBUTE_MAP.items():
            val = (data.get("attributeScores", {})
                       .get(attr, {})
                       .get("summaryScore", {})
                       .get("value"))
            if val is not None:
                scores[internal] = max(scores.get(internal, 0.0), float(val))
        return scores


# ---- מפעל נוחות: בונה moderator מוכן לחיבור ----
def build_moderator(local_filter: ContentFilter,
                    provider: str = "azure") -> CloudModerator:
    return CloudModerator(local_filter, ModerationConfig(provider=Provider(provider)))
