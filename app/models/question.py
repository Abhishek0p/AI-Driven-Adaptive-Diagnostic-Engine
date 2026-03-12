"""Pydantic models for GRE-style questions."""

from pydantic import BaseModel, Field


class QuestionBase(BaseModel):
    """Base schema for a question."""

    text: str = Field(..., description="The question stem")
    options: list[str] = Field(..., description="List of answer choices (A, B, C, D)")
    correct_answer: str = Field(..., description="The correct option letter (A/B/C/D)")
    difficulty: float = Field(
        ..., ge=0.1, le=1.0, description="Difficulty score from 0.1 (easy) to 1.0 (hard)"
    )
    topic: str = Field(..., description="Subject area (e.g., Algebra, Vocabulary)")
    tags: list[str] = Field(default_factory=list, description="Descriptive tags")
    discrimination: float = Field(
        default=1.0, ge=0.1, le=3.0, description="IRT discrimination parameter (a)"
    )


class QuestionInDB(QuestionBase):
    """Question as stored in MongoDB (includes _id as string)."""

    id: str = Field(..., alias="_id", description="MongoDB ObjectId as string")

    class Config:
        populate_by_name = True


class QuestionOut(BaseModel):
    """Question returned to the student (no correct answer revealed)."""

    id: str = Field(..., description="Question ID")
    text: str
    options: list[str]
    difficulty: float
    topic: str
    question_number: int = Field(..., description="Current question number in the test")
    total_questions: int = Field(..., description="Total questions in the test")
