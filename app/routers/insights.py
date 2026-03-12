"""API router for AI-powered insights and study plans."""

from bson import ObjectId
from fastapi import APIRouter, HTTPException

from app.database import get_sessions_collection
from app.services.llm import generate_study_plan
from app.models.session import StudyPlan

router = APIRouter(prefix="/api/session", tags=["AI Insights"])


@router.get("/{session_id}/study-plan", response_model=StudyPlan)
async def get_study_plan(session_id: str):
    """Generate a personalized 3-step study plan using AI.

    Analyzes the student's performance data (topics missed, difficulty
    levels reached) and generates tailored recommendations.

    Requires the test to be completed first. Uses OpenAI GPT-4o-mini
    if an API key is configured, otherwise falls back to a template-based plan.
    """
    sessions = get_sessions_collection()

    try:
        obj_id = ObjectId(session_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid session ID format")

    session = await sessions.find_one({"_id": obj_id})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail="Test must be completed before generating a study plan.",
        )

    responses = session["responses"]
    total_correct = sum(1 for r in responses if r["is_correct"])

    plan = await generate_study_plan(
        student_name=session["student_name"],
        ability_score=session["ability_score"],
        responses=responses,
        total_correct=total_correct,
        total_questions=len(responses),
    )

    return StudyPlan(**plan)
