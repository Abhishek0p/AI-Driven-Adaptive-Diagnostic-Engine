# 🧠 Adaptive Diagnostic Engine

A **1-Dimension Adaptive Testing** system that determines student proficiency using **IRT (Item Response Theory)**. Dynamically selects GRE-style questions based on previous answers and generates AI-powered personalized study plans.

## Tech Stack

- **Backend:** Python 3.11+ / FastAPI
- **Database:** MongoDB (via Motor async driver)
- **AI:** Google Gemini 2.0 Flash (with template-based fallback)
- **Algorithm:** 2-Parameter Logistic IRT Model

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- MongoDB running locally (`mongodb://localhost:27017`) or a MongoDB Atlas URI

### Setup

```bash
# 1. Clone and enter the project
cd "highscores assignment"

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
copy .env.example .env
# Edit .env with your MongoDB URI and Gemini API key

# 5. Seed the database (22 GRE-style questions)
python -m app.seed

# 6. Run the server
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`  
Swagger docs: `http://localhost:8000/docs`

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/` | Health check |
| `GET`  | `/api/questions` | List all questions (admin) |
| `POST` | `/api/questions/seed` | Seed database with questions |
| `POST` | `/api/session/start` | Start a new test session |
| `GET`  | `/api/session/{id}/next-question` | Get next adaptive question |
| `POST` | `/api/session/{id}/submit-answer` | Submit answer, get ability update |
| `GET`  | `/api/session/{id}/results` | Get final test results |
| `GET`  | `/api/session/{id}/study-plan` | Generate AI study plan |

### Example Flow

```bash
# 1. Start a session
curl -X POST http://localhost:8000/api/session/start \
  -H "Content-Type: application/json" \
  -d '{"student_name": "Alice"}'

# 2. Get next question (returns adaptive question)
curl http://localhost:8000/api/session/<SESSION_ID>/next-question

# 3. Submit answer
curl -X POST http://localhost:8000/api/session/<SESSION_ID>/submit-answer \
  -H "Content-Type: application/json" \
  -d '{"selected_answer": "B"}'

# 4. After completing all questions, get results
curl http://localhost:8000/api/session/<SESSION_ID>/results

# 5. Get AI-generated study plan
curl http://localhost:8000/api/session/<SESSION_ID>/study-plan
```

---

## 🧮 Adaptive Algorithm Logic

### IRT Model (2-Parameter Logistic)

The system uses **Item Response Theory** to adaptively estimate student ability:

**1. Probability of Correct Response:**
```
P(correct | θ, b, a) = 1 / (1 + exp(-a × (θ - b)))
```
- `θ` = student ability (0.0 – 1.0)
- `b` = question difficulty (0.1 – 1.0)
- `a` = question discrimination (how well the question differentiates ability levels)

**2. Ability Update (Newton-Raphson MLE):**
```
gradient    = a × (response - P)
information = a² × P × (1 - P)
θ_new       = θ_old + lr × (gradient / information)
```
- Clamped delta (±0.3 max) prevents wild jumps
- Learning rate of 0.4 balances convergence speed and stability

**3. Question Selection (Fisher Information Maximization):**
```
I(θ) = a² × P(θ) × (1 - P(θ))
```
The system picks the unused question that **maximizes Fisher Information** at the student's current ability level. This naturally selects questions whose difficulty is close to the student's ability — the most diagnostic region.

### How It Works in Practice

1. Student starts at **ability = 0.5** (baseline)
2. System picks the question most informative at θ = 0.5
3. **Correct answer** → ability increases → next question is harder
4. **Incorrect answer** → ability decreases → next question is easier
5. After 10 questions, the ability score converges to the student's true proficiency

---

## 🤖 AI Study Plan Generation

After the test, the `/study-plan` endpoint analyzes:
- Topics where accuracy was below 50%
- Difficulty levels reached per topic
- Overall ability trajectory

This data is sent to **Google Gemini 2.0 Flash** which generates a **personalized 3-step study plan**. If no API key is configured, a rule-based fallback generates reasonable recommendations.

---

## 📁 Project Structure

```
app/
├── main.py              # FastAPI app entry point
├── config.py             # Environment-based settings
├── database.py           # Async MongoDB connection (Motor)
├── seed.py               # Database seeder (22 GRE questions)
├── models/
│   ├── question.py       # Question schemas
│   └── session.py        # Session & response schemas
├── routers/
│   ├── questions.py      # Question admin endpoints
│   ├── session.py        # Test session endpoints
│   └── insights.py       # AI study plan endpoint
└── services/
    ├── adaptive.py       # IRT engine & question selection
    └── llm.py            # OpenAI integration & fallback
```

---

## 🤖 AI Log

### How AI Tools Were Used
- **Cursor AI (Antigravity):** Used for full-stack code generation — project scaffolding, FastAPI boilerplate, MongoDB schema design, IRT algorithm implementation, and OpenAI prompt engineering.
- **Key acceleration:** The IRT math (probability functions, Newton-Raphson updates, Fisher Information) was generated with AI assistance and then reviewed for mathematical correctness.

### Challenges AI Couldn't Solve
- **Tuning the learning rate:** The balance between convergence speed and stability (lr=0.4, delta clamped to ±0.3) required manual experimentation to ensure the algorithm doesn't oscillate.
- **Question bank quality:** AI generated the question content, but the difficulty ratings and discrimination parameters needed human judgment to ensure they correspond to actual GRE difficulty levels.

---

## 📋 Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MONGODB_URL` | `mongodb://localhost:27017` | MongoDB connection string |
| `DATABASE_NAME` | `adaptive_testing` | Database name |
| `GEMINI_API_KEY` | (empty) | Google Gemini API key (optional — fallback works without it) |
| `QUESTIONS_PER_TEST` | `10` | Number of questions per test session |
