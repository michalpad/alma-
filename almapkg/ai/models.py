"""
ALMA — מודלים (Pydantic) לישויות הליבה.
משימה 1: ייצוג מבני של פרופיל, עץ למידה ולוג למידה.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ----- enums משותפים -----

class Subject(str, Enum):
    HEBREW = "hebrew"
    MATH = "math"
    ENGLISH = "english"


class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"


class AgeBand(str, Enum):
    """שכבת גיל — קובעת את זמני ההשהיה הקוליים."""
    A_B = "a-b"   # כיתות א-ב → 5.0 שניות
    C_D = "c-d"   # כיתות ג-ד → 3.5 שניות
    E_F = "e-f"   # כיתות ה-ו → 2.5 שניות


class NodeStatus(str, Enum):
    LOCKED = "locked"
    AVAILABLE = "available"
    IN_PROGRESS = "in_progress"
    MASTERED = "mastered"


class QuestionType(str, Enum):
    OPEN = "open"
    CLOSED = "closed"
    GAME = "game"
    QUIZ = "quiz"


# ----- פרופיל תלמיד -----

class Student(BaseModel):
    student_id: UUID
    username: str
    display_name: str
    gender: Gender
    assigned_grade: int = Field(ge=1, le=6)
    age_band: AgeBand
    voice_choice: Gender = Gender.FEMALE
    last_active_at: Optional[datetime] = None


class SubjectProgress(BaseModel):
    student_id: UUID
    subject: Subject
    current_node_id: Optional[UUID] = None
    mastery_level: int = 0


# ----- עץ למידה -----

class LearningNode(BaseModel):
    node_id: UUID
    subject: Subject
    title: str
    description: Optional[str] = None
    grade_level: Optional[int] = None
    sequence_order: int
    parent_node_id: Optional[UUID] = None
    complexity: int = 1
    prerequisites: list[UUID] = Field(default_factory=list)


class StudentNodeStatus(BaseModel):
    student_id: UUID
    node_id: UUID
    status: NodeStatus = NodeStatus.LOCKED
    success_rate: float = 0.0
    started_at: Optional[datetime] = None
    mastered_at: Optional[datetime] = None


# ----- לוג למידה -----

class LearningLogEntry(BaseModel):
    student_id: UUID
    node_id: UUID
    subject: Subject
    question_text: Optional[str] = None
    question_type: Optional[QuestionType] = None
    student_answer: Optional[str] = None
    is_correct: Optional[bool] = None
    hints_used: int = Field(default=0, ge=0, le=4)
    response_mode: Optional[str] = None
    time_taken_ms: Optional[int] = None


# ----- הקשר שמורכב עבור ה-LLM בכל turn -----

class StudentContext(BaseModel):
    """כל מה ש-Pedagogy Orchestrator מרכיב לפני קריאה ל-LLM."""
    student: Student
    subject: Subject
    current_node: Optional[LearningNode] = None
    recent_mistakes: list[str] = Field(default_factory=list)
    relevant_interests: list[str] = Field(default_factory=list)
    known_difficulties: list[str] = Field(default_factory=list)
    current_hint_level: int = Field(default=0, ge=0, le=4)
