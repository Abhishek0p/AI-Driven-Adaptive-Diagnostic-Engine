"""API router for adaptive test sessions."""

from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, HTTPException

from app.config import settings
from app.database import get_sessions_collection, get_questions_collection
from app.models.session import (
    SessionCreate,
    SubmitAnswerRequest,
    SubmitAnswerResponse,
    SessionResults,
)
from app.services.adaptive import (
    select_next_question,
    update_ability,
    probability_correct,
)
from app.models.question import QuestionOut

router = APIRouter(prefix="/api/session", tags=["Session"])


@router.post("/start")
async def start_session(body: SessionCreate):
    """Start a new adaptive test session.

    The student begins at a baseline ability of 0.5.
    """
    sessions = get_sessions_collection()

    session_doc = {
        "student_name": body.student_name,
        "ability_score": 0.5,
        "current_question_index": 0,
        "responses": [],
        "status": "in_progress",
        "created_at": datetime.now(timezone.utc),
        "completed_at": None,
    }

    result = await sessions.insert_one(session_doc)

    return {
        "session_id": str(result.inserted_id),
        "student_name": body.student_name,
        "ability_score": 0.5,
        "total_questions": settings.QUESTIONS_PER_TEST,
        "message": f"Test started! You will answer {settings.QUESTIONS_PER_TEST} adaptive questions.",
    }


@router.get("/{session_id}/next-question", response_model=QuestionOut)
async def get_next_question(session_id: str):
    """Get the next adaptively-selected question for the session.

    Uses Fisher Information maximization to pick the most
    informative question at the student's current ability level.
    """
    sessions = get_sessions_collection()
    questions_coll = get_questions_collection()

    # Validate session ID
    try:
        obj_id = ObjectId(session_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid session ID format")

    # Get session
    session = await sessions.find_one({"_id": obj_id})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session["status"] == "completed":
        raise HTTPException(
            status_code=400,
            detail="Test is already completed. Use GET /results to see your results.",
        )

    # Check if all questions have been answered
    if session["current_question_index"] >= settings.QUESTIONS_PER_TEST:
        raise HTTPException(
            status_code=400,
            detail="All questions have been answered. Use GET /results to see your results.",
        )

    # Get all questions from DB
    all_questions = await questions_coll.find().to_list(length=100)

    # Get IDs of already-asked questions
    asked_ids = {r["question_id"] for r in session["responses"]}

    # Select next question using adaptive algorithm
    next_q = select_next_question(
        theta=session["ability_score"],
        available_questions=all_questions,
        asked_ids=asked_ids,
    )

    if not next_q:
        # No more questions available — auto-complete
        await sessions.update_one(
            {"_id": obj_id},
            {
                "$set": {
                    "status": "completed",
                    "completed_at": datetime.now(timezone.utc),
                }
            },
        )
        raise HTTPException(
            status_code=400,
            detail="No more questions available. Test completed early.",
        )

    return QuestionOut(
        id=str(next_q["_id"]),
        text=next_q["text"],
        options=next_q["options"],
        difficulty=next_q["difficulty"],
        topic=next_q["topic"],
        question_number=session["current_question_index"] + 1,
        total_questions=settings.QUESTIONS_PER_TEST,
    )


@router.post("/{session_id}/submit-answer", response_model=SubmitAnswerResponse)
async def submit_answer(session_id: str, body: SubmitAnswerRequest):
    """Submit an answer to the current question and get updated ability score.

    The ability score is updated using IRT-based maximum likelihood estimation.
    """
    sessions = get_sessions_collection()
    questions_coll = get_questions_collection()

    # Validate session
    try:
        obj_id = ObjectId(session_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid session ID format")

    session = await sessions.find_one({"_id": obj_id})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session["status"] == "completed":
        raise HTTPException(status_code=400, detail="Test is already completed")

    # Determine the current question (re-select using adaptive algorithm)
    all_questions = await questions_coll.find().to_list(length=100)
    asked_ids = {r["question_id"] for r in session["responses"]}

    current_q = select_next_question(
        theta=session["ability_score"],
        available_questions=all_questions,
        asked_ids=asked_ids,
    )

    if not current_q:
        raise HTTPException(status_code=400, detail="No current question found")

    # Check answer
    is_correct = body.selected_answer.upper() == current_q["correct_answer"].upper()

    # Update ability using IRT
    new_ability = update_ability(
        theta=session["ability_score"],
        response=1 if is_correct else 0,
        difficulty=current_q["difficulty"],
        discrimination=current_q.get("discrimination", 1.0),
    )

    # Build response record
    response_record = {
        "question_id": str(current_q["_id"]),
        "selected_answer": body.selected_answer.upper(),
        "is_correct": is_correct,
        "difficulty": current_q["difficulty"],
        "topic": current_q["topic"],
        "ability_after": new_ability,
    }

    new_index = session["current_question_index"] + 1
    questions_remaining = settings.QUESTIONS_PER_TEST - new_index

    # Check if test is complete
    update_fields: dict = {
        "ability_score": new_ability,
        "current_question_index": new_index,
    }
    if questions_remaining <= 0:
        update_fields["status"] = "completed"
        update_fields["completed_at"] = datetime.now(timezone.utc)

    await sessions.update_one(
        {"_id": obj_id},
        {
            "$set": update_fields,
            "$push": {"responses": response_record},
        },
    )

    # Build message
    if is_correct:
        message = f"✅ Correct! Ability updated: {new_ability:.4f}"
    else:
        message = (
            f"❌ Incorrect. The correct answer was {current_q['correct_answer']}. "
            f"Ability updated: {new_ability:.4f}"
        )

    if questions_remaining <= 0:
        message += " | 🎉 Test complete! GET /results to see your summary."

    return SubmitAnswerResponse(
        is_correct=is_correct,
        correct_answer=current_q["correct_answer"],
        ability_score=new_ability,
        questions_remaining=max(0, questions_remaining),
        message=message,
    )


@router.get("/{session_id}/results", response_model=SessionResults)
async def get_results(session_id: str):
    """Get final test results and performance breakdown.

    Only available after the test is completed.
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
            detail="Test is still in progress. Complete all questions first.",
        )

    responses = session["responses"]
    correct_count = sum(1 for r in responses if r["is_correct"])
    total = len(responses)

    # Topic breakdown
    topic_breakdown: dict = {}
    for r in responses:
        topic = r["topic"]
        if topic not in topic_breakdown:
            topic_breakdown[topic] = {"correct": 0, "total": 0, "avg_difficulty": 0.0}
        topic_breakdown[topic]["total"] += 1
        topic_breakdown[topic]["avg_difficulty"] += r["difficulty"]
        if r["is_correct"]:
            topic_breakdown[topic]["correct"] += 1

    for topic_data in topic_breakdown.values():
        topic_data["avg_difficulty"] = round(
            topic_data["avg_difficulty"] / topic_data["total"], 2
        )
        topic_data["accuracy"] = (
            round(topic_data["correct"] / topic_data["total"] * 100, 1)
            if topic_data["total"] > 0
            else 0
        )

    return SessionResults(
        session_id=session_id,
        student_name=session["student_name"],
        final_ability_score=round(session["ability_score"], 4),
        total_questions=total,
        correct_count=correct_count,
        accuracy=round(correct_count / total * 100, 1) if total > 0 else 0,
        topic_breakdown=topic_breakdown,
        responses=responses,
        status=session["status"],
    )
