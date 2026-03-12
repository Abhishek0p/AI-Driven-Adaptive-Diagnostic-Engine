"""API router for question management (admin/debug)."""

from fastapi import APIRouter, HTTPException

from app.database import get_questions_collection
from app.seed import seed_database

router = APIRouter(prefix="/api/questions", tags=["Questions"])


@router.get("/")
async def list_questions():
    """List all questions in the database (admin/debug endpoint)."""
    collection = get_questions_collection()
    questions = []

    async for q in collection.find().sort("difficulty", 1):
        q["_id"] = str(q["_id"])
        questions.append(q)

    return {
        "count": len(questions),
        "questions": questions,
    }


@router.post("/seed")
async def trigger_seed():
    """Seed the database with GRE-style questions."""
    try:
        count = await seed_database()
        return {"message": f"Successfully seeded {count} questions", "count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Seeding failed: {str(e)}")
