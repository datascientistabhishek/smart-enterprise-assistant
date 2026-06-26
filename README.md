# AI Enterprise Assistant

A modular, LLM-powered enterprise assistant built with **FastAPI + LangChain tool calling + Groq (free tier)**.
Answers employee questions and performs business actions like creating tickets, fetching employee info, and generating reports.

---

## Quick Start

```bash
# 1. Clone / extract the project
cd ai-assistant

# 2. Create a Python 3.12 virtual environment
python3.12 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set your Groq API key (free at https://console.groq.com)
cp .env.example .env
# Edit .env and paste your key

# 5. Run the server
uvicorn app.main:app --reload

# 6. Open docs
# http://localhost:8000/docs

# Optional: run the Streamlit UI in a second terminal
streamlit run streamlit_app.py
```

## Python Version

This project is currently set up for Python 3.12. Python 3.14 is not supported by the pinned `pydantic-core` build in `requirements.txt`.

---

## Project Structure

```
ai-assistant/
├── app/
│   ├── main.py              ← FastAPI app + router registration
│   ├── core/
│   │   ├── config.py        ← Groq client, model settings
│   │   ├── memory.py        ← Conversation memory manager (per-session)
│   │   └── prompts.py       ← All LLM system prompts (central)
│   ├── agents/
│   │   └── assistant_agent.py ← LLM reasoning loop (call Groq → parse → act)
│   ├── actions/
│   │   ├── business_actions.py ← Business action handlers
│   │   └── langchain_tools.py  ← LangChain tool wrappers
│   └── routes/
│       ├── schemas.py       ← Pydantic request/response models + validation
│       └── api.py           ← All API endpoints
├── data/
│   ├── mock_db.py           ← Static company policies + seed data
│   └── sqlite_db.py         ← SQLite persistence for employees, tickets, reports
├── tests/
│   └── test_api.py          ← Normal + challenging test inputs
├── .env.example
├── requirements.txt
└── README.md
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/ask` | Main chat endpoint |
| `GET`  | `/api/v1/tickets` | List all tickets |
| `GET`  | `/api/v1/reports` | List all generated reports |
| `GET`  | `/api/v1/employees` | List employees |
| `DELETE` | `/api/v1/session/{id}` | Clear conversation memory |
| `GET`  | `/api/v1/health` | Health check |

---

## Test Inputs

### Test 1 — Normal Business Query
```bash
curl -X POST http://localhost:8000/api/v1/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the WFH policy?", "session_id": "demo"}'
```

### Test 2 — Challenging Query (triggers ticket creation)
```bash
curl -X POST http://localhost:8000/api/v1/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "My laptop screen is black and I have a demo in 1 hour!", "session_id": "demo"}'
```

### Test 3 — Memory (follow-up question)
```bash
# First message
curl -X POST http://localhost:8000/api/v1/ask \
  -d '{"question": "How many leave days do I have?", "session_id": "s1"}'

# Follow-up — the AI remembers the context
curl -X POST http://localhost:8000/api/v1/ask \
  -d '{"question": "Can I carry them forward?", "session_id": "s1"}'
```

### Run all tests
```bash
python tests/test_api.py
```

---

## Business Actions Supported

| Action | Trigger Example |
|--------|----------------|
| Create Ticket | "My VPN is not working" |
| Fetch Employee Info | "Tell me about employee EMP001" |
| Generate Report | "Generate a headcount report for Engineering" |

---

## Persistence

The assistant now stores employees, tickets, and reports in SQLite at `data/assistant.db`.
The SQLite layer uses SQLAlchemy ORM models, and tickets/reports created through LangChain tools are persisted there while the API endpoints read from the same database.

## Engineering Improvement: Conversation Memory

The app maintains per-session conversation history using an in-memory `MemoryManager`.
Each session_id gets its own message list. The last 10 messages are sent to the LLM on every request, enabling multi-turn conversations.

**Tradeoff:** In-memory storage is fast but non-persistent. In production, replace with Redis or PostgreSQL.

---

## Model Used
- **Provider:** Groq (free tier)
- **Model:** `llama-3.1-8b-instant`
- **Why Groq:** Fast inference available on the free tier. Llama 3.1 8B handles business Q&A and tool calling reliably.

## Implementation
- The assistant uses LangChain's Groq chat model with tool calling.
- Ticket creation, employee lookup, and report generation are exposed as LangChain tools.
- Session history is still stored in memory for short multi-turn conversations.

## Streamlit UI
- `streamlit_app.py` provides a simple chat interface for the FastAPI backend.
- It shows live tickets, reports, employees, and health status from the API.
