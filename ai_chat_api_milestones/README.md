# 🚀 AI Chat API — 10 Milestones

Build a production-ready AI Chat API step by step.
Every milestone adds one feature on top of the previous.

---

## Setup

```bash
pip install -r requirements.txt
cp .env.template .env
# Edit .env — add your GROQ_API_KEY from console.groq.com
```

---

## Milestone Map

| # | What you build | File | Concepts |
|---|---|---|---|
| M01 | First LLM call | `m01/starter.py` | ChatGroq, invoke, messages |
| M02 | System prompt + tokens | `m02/starter.py` | SystemMessage, usage_metadata |
| M03 | Memory — multi-turn chat | `m03/starter.py` | ConversationBufferWindowMemory |
| M04 | Prompt evaluation | `m04/starter.py` | JsonOutputParser, eval scores |
| M05 | SQLite logging | `m05/starter.py` | sqlite3, chat_logs, eval_logs |
| M06 | First FastAPI endpoint | `m06/starter.py` | FastAPI, POST /chat, Swagger |
| M07 | Streaming endpoint | `m07/starter.py` | astream, StreamingResponse, SSE |
| M08 | Request logging middleware | `m08/starter.py` | @middleware, RotatingFileHandler |
| M09 | API key authentication | `m09/starter.py` | hashlib, secrets, Depends |
| M10 | Complete API | `m10/starter.py` | history, eval summary, CORS |

---

## How to use each milestone

1. Open `mXX/starter.py`
2. Read the GOAL and TASKS at the top
3. Fill in the `# ✍️ Your code here` sections
4. Run and test
5. If stuck — read the HINTS in the starter file
6. Check `mXX/solution.py` only after trying yourself

---

## Running FastAPI (M06 onwards)

```bash
# From inside the milestone folder
uvicorn starter:app --reload

# Test in browser
open http://127.0.0.1:8000/docs
```

## Testing streaming (M07+)

```bash
curl -N -X POST http://localhost:8000/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message":"What is RAG?","session_id":"test-123"}'
```

## Testing with auth (M09+)

```bash
# Generate a key (use admin key from .env)
curl -X POST http://localhost:8000/auth/generate-key \
  -H "X-API-Key: admin-secret-change-in-production" \
  -H "Content-Type: application/json" \
  -d '{"user_name":"YourName"}'

# Use generated key
curl -X POST http://localhost:8000/chat \
  -H "X-API-Key: YOUR_GENERATED_KEY" \
  -H "Content-Type: application/json" \
  -d '{"message":"hello","session_id":"my-session"}'
```

---

## What you'll have at the end (M10)

```
POST   /auth/generate-key  → create API key (admin only)
POST   /chat               → send message, get AI reply + eval score
POST   /chat/stream        → same but streams tokens
GET    /chat/history       → conversation history from DB
DELETE /chat/history       → clear session memory
GET    /logs               → all request logs
GET    /logs/chat          → all chat logs with eval scores
GET    /eval/summary       → average scores, best/worst sessions
GET    /health             → API + DB + model status
```

Everything logged to SQLite. Every response evaluated. Every request authenticated.
