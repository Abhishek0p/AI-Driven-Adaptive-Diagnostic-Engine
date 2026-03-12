"""IRT-based adaptive testing engine.

Implements 1-Parameter Logistic IRT model for:
1. Estimating probability of correct response
2. Updating student ability (theta) after each response
3. Selecting the next optimal question
"""

import math
from typing import Optional


def probability_correct(theta: float, difficulty: float, discrimination: float = 1.0) -> float:
    """Calculate probability of correct response using 2PL IRT model.

    P(correct | θ, b, a) = 1 / (1 + exp(-a * (θ - b)))

    Args:
        theta: Student's current ability estimate
        difficulty: Question difficulty parameter (b)
        discrimination: Question discrimination parameter (a)

    Returns:
        Probability of correct response [0, 1]
    """
    exponent = -discrimination * (theta - difficulty)
    # Clamp to prevent overflow
    exponent = max(-10, min(10, exponent))
    return 1.0 / (1.0 + math.exp(exponent))


def update_ability(
    theta: float,
    response: int,
    difficulty: float,
    discrimination: float = 1.0,
    learning_rate: float = 0.4,
) -> float:
    """Update ability estimate using Newton-Raphson-inspired MLE step.

    θ_new = θ_old + lr * Σ a_i * (x_i - P_i)

    Where:
        x_i = 1 (correct) or 0 (incorrect)
        P_i = probability of correct response
        a_i = discrimination parameter

    Args:
        theta: Current ability estimate
        response: 1 for correct, 0 for incorrect
        difficulty: Question difficulty
        discrimination: Question discrimination
        learning_rate: Step size for update (controls convergence speed)

    Returns:
        Updated ability estimate, clamped to [0, 1]
    """
    p = probability_correct(theta, difficulty, discrimination)

    # Newton-Raphson-style update
    # Gradient: a * (response - P)
    gradient = discrimination * (response - p)

    # Information (second derivative): a^2 * P * (1 - P)
    information = discrimination ** 2 * p * (1 - p)

    # Avoid division by zero
    if information < 1e-6:
        information = 1e-6

    # MLE step: θ_new = θ + (gradient / information) * learning_rate
    delta = learning_rate * (gradient / information)

    # Clamp delta to prevent wild jumps
    delta = max(-0.3, min(0.3, delta))

    new_theta = theta + delta

    # Clamp ability to valid range [0, 1]
    return round(max(0.05, min(0.95, new_theta)), 4)


def fisher_information(theta: float, difficulty: float, discrimination: float = 1.0) -> float:
    """Calculate Fisher Information for a question at given ability level.

    I(θ) = a² * P(θ) * (1 - P(θ))

    Higher information = question is more diagnostic at this ability level.

    Args:
        theta: Student's current ability
        difficulty: Question difficulty
        discrimination: Question discrimination

    Returns:
        Fisher information value
    """
    p = probability_correct(theta, difficulty, discrimination)
    return discrimination ** 2 * p * (1 - p)


def select_next_question(
    theta: float,
    available_questions: list[dict],
    asked_ids: Optional[set] = None,
) -> Optional[dict]:
    """Select the next question that maximizes Fisher Information.

    This picks the question that is most informative at the student's
    current ability level — typically the one whose difficulty is closest
    to the student's ability.

    Args:
        theta: Student's current ability estimate
        available_questions: List of question dicts from DB
        asked_ids: Set of already-asked question IDs to exclude

    Returns:
        The best question dict, or None if no questions available
    """
    if asked_ids is None:
        asked_ids = set()

    # Filter out already-asked questions
    candidates = [
        q for q in available_questions
        if str(q["_id"]) not in asked_ids
    ]

    if not candidates:
        return None

    # Pick question with maximum Fisher Information at current ability
    best_question = max(
        candidates,
        key=lambda q: fisher_information(
            theta,
            q["difficulty"],
            q.get("discrimination", 1.0),
        ),
    )

    return best_question
