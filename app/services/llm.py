"""LLM integration for generating personalized study plans using Google Gemini."""

import json

from google import genai

from app.config import settings


async def generate_study_plan(
    student_name: str,
    ability_score: float,
    responses: list[dict],
    total_correct: int,
    total_questions: int,
) -> dict:
    """Generate a personalized 3-step study plan using Google Gemini.

    Falls back to a template-based plan if no API key is configured.

    Args:
        student_name: The student's name
        ability_score: Final ability estimate (0-1)
        responses: List of response records with topic, difficulty, is_correct
        total_correct: Number of correct answers
        total_questions: Total questions answered

    Returns:
        Study plan dict with steps and encouragement
    """
    # Analyze performance by topic
    topic_stats: dict[str, dict] = {}
    for r in responses:
        topic = r["topic"]
        if topic not in topic_stats:
            topic_stats[topic] = {"correct": 0, "total": 0, "difficulties": []}
        topic_stats[topic]["total"] += 1
        topic_stats[topic]["difficulties"].append(r["difficulty"])
        if r["is_correct"]:
            topic_stats[topic]["correct"] += 1

    # Identify weak topics (below 50% accuracy)
    weak_topics = []
    for topic, stats in topic_stats.items():
        accuracy = stats["correct"] / stats["total"] if stats["total"] > 0 else 0
        if accuracy < 0.5:
            weak_topics.append({
                "topic": topic,
                "accuracy": round(accuracy * 100),
                "avg_difficulty": round(sum(stats["difficulties"]) / len(stats["difficulties"]), 2),
            })

    # If no Gemini API key, use template-based fallback
    if not settings.GEMINI_API_KEY:
        return _fallback_study_plan(student_name, ability_score, weak_topics)

    # Generate LLM-powered study plan
    return await _gemini_study_plan(
        student_name, ability_score, weak_topics, topic_stats,
        total_correct, total_questions,
    )


async def _gemini_study_plan(
    student_name: str,
    ability_score: float,
    weak_topics: list[dict],
    topic_stats: dict,
    total_correct: int,
    total_questions: int,
) -> dict:
    """Generate study plan via Google Gemini API."""
    client = genai.Client(api_key=settings.GEMINI_API_KEY)

    prompt = f"""You are an expert educational tutor. A student just completed an adaptive GRE practice test.

Student: {student_name}
Final Ability Score: {ability_score:.2f} (scale 0-1, where 1 is expert level)
Overall Accuracy: {total_correct}/{total_questions} ({round(total_correct/total_questions*100)}%)

Performance by Topic:
{json.dumps(dict(topic_stats), indent=2, default=str)}

Weak Areas (below 50% accuracy):
{json.dumps(weak_topics, indent=2)}

Generate a personalized 3-step study plan in the following JSON format:
{{
    "study_plan": [
        {{
            "step": "Step 1",
            "topic": "<topic to focus on>",
            "action": "<specific, actionable study recommendation>"
        }},
        {{
            "step": "Step 2",
            "topic": "<topic to focus on>",
            "action": "<specific, actionable study recommendation>"
        }},
        {{
            "step": "Step 3",
            "topic": "<topic to focus on>",
            "action": "<specific, actionable study recommendation>"
        }}
    ],
    "encouragement": "<a brief motivational message tailored to their performance>"
}}

Focus on their weakest areas first. Be specific with study actions (e.g., "Practice 10 quadratic equation problems focusing on factoring" not "Study algebra").
Return ONLY the JSON, no other text."""

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
        )

        content = response.text.strip()
        # Strip markdown code fences if present
        if content.startswith("```"):
            content = content.split("\n", 1)[1]
            content = content.rsplit("```", 1)[0]

        plan_data = json.loads(content)

        return {
            "student_name": student_name,
            "final_ability_score": round(ability_score, 4),
            "weak_topics": [wt["topic"] for wt in weak_topics],
            "study_plan": plan_data.get("study_plan", []),
            "encouragement": plan_data.get("encouragement", "Keep up the great work!"),
        }
    except Exception as e:
        print(f"⚠️  Gemini API call failed: {e}. Using fallback plan.")
        return _fallback_study_plan(student_name, ability_score, weak_topics)


def _fallback_study_plan(
    student_name: str,
    ability_score: float,
    weak_topics: list[dict],
) -> dict:
    """Template-based study plan when no LLM is available."""
    study_steps = []

    if not weak_topics:
        study_steps = [
            {
                "step": "Step 1",
                "topic": "Advanced Problem Solving",
                "action": "Challenge yourself with GRE-level problems at difficulty 0.8+ to push your ceiling higher.",
            },
            {
                "step": "Step 2",
                "topic": "Timed Practice",
                "action": "Take a full-length timed practice test to build speed and stamina under exam conditions.",
            },
            {
                "step": "Step 3",
                "topic": "Review & Consolidation",
                "action": "Review any tricky questions from this session and create flashcards for key concepts.",
            },
        ]
    else:
        for i, wt in enumerate(weak_topics[:3]):
            topic = wt["topic"]
            accuracy = wt["accuracy"]

            if accuracy == 0:
                action = f"Start with foundational {topic} concepts. Work through 15 practice problems at easy difficulty."
            elif accuracy < 30:
                action = f"Review core {topic} formulas and rules. Practice 10 problems at moderate difficulty, focusing on understanding each step."
            else:
                action = f"You're close in {topic}! Focus on the tricky sub-topics you missed. Do 10 targeted problems and review solutions carefully."

            study_steps.append({
                "step": f"Step {i + 1}",
                "topic": topic,
                "action": action,
            })

        while len(study_steps) < 3:
            study_steps.append({
                "step": f"Step {len(study_steps) + 1}",
                "topic": "General Review",
                "action": "Take another adaptive practice test to measure improvement and identify remaining gaps.",
            })

    if ability_score >= 0.7:
        encouragement = f"Excellent work, {student_name}! Your ability score of {ability_score:.2f} shows strong mastery. Keep refining those advanced skills!"
    elif ability_score >= 0.4:
        encouragement = f"Good effort, {student_name}! You're building a solid foundation at {ability_score:.2f}. Focus on the steps above and you'll see rapid improvement."
    else:
        encouragement = f"Great start, {student_name}! Every expert was once a beginner. Follow the plan above consistently, and your score will climb steadily."

    return {
        "student_name": student_name,
        "final_ability_score": round(ability_score, 4),
        "weak_topics": [wt["topic"] for wt in weak_topics],
        "study_plan": study_steps,
        "encouragement": encouragement,
    }
