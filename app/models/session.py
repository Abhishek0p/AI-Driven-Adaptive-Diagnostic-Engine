"""Pydantic models for user test sessions."""

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field


class ResponseRecord(BaseModel):
    """Record of a single question response."""

    question_id: str
    selected_answer: str
    is_correct: bool
    difficulty: float
    topic: str
    ability_after: float = Field(
        ..., description="Student's ability score after this response"
    )


class SessionCreate(BaseModel):
    """Request body to start a new session."""

    student_name: str = Field(
        ..., min_length=1, max_length=100, description="Student's name"
    )


class SubmitAnswerRequest(BaseModel):
    """Request body to submit an answer."""

    selected_answer: str = Field(
        ..., pattern=r"^[A-D]$", description="Selected option (A/B/C/D)"
    )


class SubmitAnswerResponse(BaseModel):
    """Response after submitting an answer."""

    is_correct: bool
    correct_answer: str
    ability_score: float = Field(..., description="Updated ability estimate")
    questions_remaining: int
    message: str


class SessionInDB(BaseModel):
    """Session as stored in MongoDB."""

    id: str = Field(..., alias="_id")
    student_name: str
    ability_score: float = 0.5
    current_question_index: int = 0
    responses: list[ResponseRecord] = []
    status: str = "in_progress"  # in_progress | completed
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None

    class Config:
        populate_by_name = True


class SessionResults(BaseModel):
    """Final test results summary."""

    session_id: str
    student_name: str
    final_ability_score: float
    total_questions: int
    correct_count: int
    accuracy: float
    topic_breakdown: dict[str, dict]
    responses: list[ResponseRecord]
    status: str


class StudyPlan(BaseModel):
    """LLM-generated personalized study plan."""

    student_name: str
    final_ability_score: float
    weak_topics: list[str]
    study_plan: list[dict[str, str]] = Field(
        ..., description="List of study steps with 'step', 'topic', 'action'"
    )
    encouragement: str
