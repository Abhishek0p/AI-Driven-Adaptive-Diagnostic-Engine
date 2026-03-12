"""Seed MongoDB with 20+ GRE-style questions across multiple topics."""

import asyncio

from app.database import connect_db, close_db, get_questions_collection

SEED_QUESTIONS = [
    # ── Algebra (5 questions) ──────────────────────────────────────────────
    {
        "text": "If 3x + 7 = 22, what is the value of x?",
        "options": ["A) 3", "B) 5", "C) 7", "D) 10"],
        "correct_answer": "B",
        "difficulty": 0.2,
        "topic": "Algebra",
        "tags": ["linear-equations", "basic"],
        "discrimination": 1.0,
    },
    {
        "text": "Solve for y: 2y² - 8 = 0",
        "options": ["A) ±1", "B) ±2", "C) ±4", "D) ±8"],
        "correct_answer": "B",
        "difficulty": 0.4,
        "topic": "Algebra",
        "tags": ["quadratic-equations"],
        "discrimination": 1.2,
    },
    {
        "text": "If f(x) = 2x² - 3x + 1, what is f(3)?",
        "options": ["A) 8", "B) 10", "C) 12", "D) 14"],
        "correct_answer": "B",
        "difficulty": 0.5,
        "topic": "Algebra",
        "tags": ["functions", "evaluation"],
        "discrimination": 1.1,
    },
    {
        "text": "Which of the following is a factor of x² - 5x + 6?",
        "options": ["A) (x - 1)", "B) (x - 2)", "C) (x - 4)", "D) (x + 3)"],
        "correct_answer": "B",
        "difficulty": 0.6,
        "topic": "Algebra",
        "tags": ["factoring", "polynomials"],
        "discrimination": 1.3,
    },
    {
        "text": "If log₂(x) = 5, what is x?",
        "options": ["A) 10", "B) 16", "C) 25", "D) 32"],
        "correct_answer": "D",
        "difficulty": 0.8,
        "topic": "Algebra",
        "tags": ["logarithms", "advanced"],
        "discrimination": 1.4,
    },
    # ── Arithmetic (4 questions) ───────────────────────────────────────────
    {
        "text": "What is 15% of 240?",
        "options": ["A) 24", "B) 30", "C) 36", "D) 42"],
        "correct_answer": "C",
        "difficulty": 0.15,
        "topic": "Arithmetic",
        "tags": ["percentages", "basic"],
        "discrimination": 0.9,
    },
    {
        "text": "What is the least common multiple of 12 and 18?",
        "options": ["A) 24", "B) 36", "C) 48", "D) 72"],
        "correct_answer": "B",
        "difficulty": 0.3,
        "topic": "Arithmetic",
        "tags": ["lcm", "number-theory"],
        "discrimination": 1.0,
    },
    {
        "text": "A store increases a $80 item by 25%, then offers a 20% discount. Final price?",
        "options": ["A) $76", "B) $78", "C) $80", "D) $84"],
        "correct_answer": "C",
        "difficulty": 0.55,
        "topic": "Arithmetic",
        "tags": ["percentages", "word-problems"],
        "discrimination": 1.2,
    },
    {
        "text": "If a:b = 3:5 and b:c = 2:7, what is a:c?",
        "options": ["A) 3:7", "B) 6:35", "C) 6:7", "D) 5:14"],
        "correct_answer": "B",
        "difficulty": 0.7,
        "topic": "Arithmetic",
        "tags": ["ratios", "proportions"],
        "discrimination": 1.3,
    },
    # ── Geometry (4 questions) ─────────────────────────────────────────────
    {
        "text": "What is the area of a triangle with base 10 and height 6?",
        "options": ["A) 16", "B) 30", "C) 60", "D) 45"],
        "correct_answer": "B",
        "difficulty": 0.1,
        "topic": "Geometry",
        "tags": ["area", "triangle", "basic"],
        "discrimination": 0.8,
    },
    {
        "text": "A circle has a radius of 7. What is its circumference? (Use π ≈ 22/7)",
        "options": ["A) 22", "B) 44", "C) 154", "D) 88"],
        "correct_answer": "B",
        "difficulty": 0.3,
        "topic": "Geometry",
        "tags": ["circles", "circumference"],
        "discrimination": 1.0,
    },
    {
        "text": "In a right triangle, if one leg is 5 and the hypotenuse is 13, what is the other leg?",
        "options": ["A) 8", "B) 10", "C) 12", "D) 11"],
        "correct_answer": "C",
        "difficulty": 0.45,
        "topic": "Geometry",
        "tags": ["pythagorean-theorem"],
        "discrimination": 1.1,
    },
    {
        "text": "A cylinder has radius 3 and height 10. What is its volume?",
        "options": ["A) 30π", "B) 60π", "C) 90π", "D) 120π"],
        "correct_answer": "C",
        "difficulty": 0.65,
        "topic": "Geometry",
        "tags": ["volume", "cylinder", "3d-geometry"],
        "discrimination": 1.2,
    },
    # ── Vocabulary (4 questions) ───────────────────────────────────────────
    {
        "text": "Choose the word most similar in meaning to 'Benevolent':",
        "options": ["A) Hostile", "B) Kind", "C) Indifferent", "D) Cautious"],
        "correct_answer": "B",
        "difficulty": 0.2,
        "topic": "Vocabulary",
        "tags": ["synonyms", "basic"],
        "discrimination": 1.0,
    },
    {
        "text": "Choose the antonym of 'Ephemeral':",
        "options": ["A) Permanent", "B) Fleeting", "C) Fragile", "D) Obscure"],
        "correct_answer": "A",
        "difficulty": 0.5,
        "topic": "Vocabulary",
        "tags": ["antonyms", "intermediate"],
        "discrimination": 1.1,
    },
    {
        "text": "Select the word that best completes: 'The professor's _____ lecture left students confused.'",
        "options": ["A) lucid", "B) abstruse", "C) animated", "D) concise"],
        "correct_answer": "B",
        "difficulty": 0.75,
        "topic": "Vocabulary",
        "tags": ["sentence-completion", "advanced"],
        "discrimination": 1.3,
    },
    {
        "text": "'Sycophant' most nearly means:",
        "options": ["A) Critic", "B) Flatterer", "C) Philosopher", "D) Revolutionary"],
        "correct_answer": "B",
        "difficulty": 0.85,
        "topic": "Vocabulary",
        "tags": ["definitions", "advanced"],
        "discrimination": 1.5,
    },
    # ── Reading Comprehension (4 questions) ────────────────────────────────
    {
        "text": "Passage: 'The industrial revolution fundamentally altered economic structures.' What does 'altered' mean here?",
        "options": ["A) Maintained", "B) Changed", "C) Destroyed", "D) Created"],
        "correct_answer": "B",
        "difficulty": 0.15,
        "topic": "Reading Comprehension",
        "tags": ["vocabulary-in-context", "basic"],
        "discrimination": 0.9,
    },
    {
        "text": "Passage: 'Despite criticism, the policy was lauded by economists for reducing inflation.' The author's tone is:",
        "options": ["A) Dismissive", "B) Neutral", "C) Supportive", "D) Angry"],
        "correct_answer": "C",
        "difficulty": 0.45,
        "topic": "Reading Comprehension",
        "tags": ["tone", "inference"],
        "discrimination": 1.1,
    },
    {
        "text": "Passage: 'The paradox of thrift suggests that individual saving can harm collective prosperity.' This implies:",
        "options": [
            "A) Saving is always beneficial",
            "B) Individual and collective interests can conflict",
            "C) Thrift leads to inflation",
            "D) Prosperity requires spending",
        ],
        "correct_answer": "B",
        "difficulty": 0.7,
        "topic": "Reading Comprehension",
        "tags": ["inference", "critical-reasoning"],
        "discrimination": 1.3,
    },
    {
        "text": "Passage: 'Quantum entanglement defies locality — measuring one particle instantaneously affects its partner, regardless of distance.' The author assumes the reader understands:",
        "options": [
            "A) Classical mechanics",
            "B) The principle of locality",
            "C) String theory",
            "D) Thermodynamics",
        ],
        "correct_answer": "B",
        "difficulty": 0.9,
        "topic": "Reading Comprehension",
        "tags": ["assumption", "advanced-inference"],
        "discrimination": 1.5,
    },
    # ── Data Interpretation (1 bonus question) ─────────────────────────────
    {
        "text": "A dataset has values: 3, 7, 7, 2, 9, 1, 7. What is the mode?",
        "options": ["A) 3", "B) 5", "C) 7", "D) 9"],
        "correct_answer": "C",
        "difficulty": 0.25,
        "topic": "Data Interpretation",
        "tags": ["statistics", "mode", "basic"],
        "discrimination": 0.9,
    },
]


async def seed_database() -> int:
    """Seed the questions collection. Returns count of inserted documents."""
    await connect_db()
    collection = get_questions_collection()

    # Clear existing questions
    await collection.delete_many({})

    # Insert seed questions
    result = await collection.insert_many(SEED_QUESTIONS)
    count = len(result.inserted_ids)

    # Create index on difficulty for efficient adaptive queries
    await collection.create_index("difficulty")
    await collection.create_index("topic")

    print(f"🌱 Seeded {count} questions into the database")
    await close_db()
    return count


if __name__ == "__main__":
    asyncio.run(seed_database())
