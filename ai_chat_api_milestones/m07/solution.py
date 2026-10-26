"""
 Milestone 07  Streaming Endpoint  SOLUTION
Run: uvicorn solution:app --reload
Test: curl -N -X POST http://localhost:8000/chat/stream \
        -H "Content-Type: application/json" \
        -d '{"message":"What is RAG?","session_id":"stream-test"}'
"""

import os, time, sqlite3
from typing import Optional
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, field_validator
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.messages import HumanMessage, AIMessage

load_dotenv()

DB_PATH = "chat.db"

#  DB functions (same as M06) 
def get_connection():
    conn = sqlite3.connect(DB_PATH); conn.row_factory = sqlite3.Row; return conn

def init_db():
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS chat_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT,
            user_message TEXT, ai_response TEXT, model_used TEXT,
            prompt_tokens INTEGER DEFAULT 0, output_tokens INTEGER DEFAULT 0,
            duration_ms REAL DEFAULT 0, created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS eval_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT, chat_log_id INTEGER,
            relevance REAL, coherence REAL, conciseness REAL,
            overall_score REAL, eval_feedback TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS conversation_memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT,
            role TEXT, content TEXT, created_at TEXT DEFAULT (datetime('now'))
        );
    """)
    conn.commit(); conn.close()

def save_chat(sid, umsg, areply, model, ti, to, dur):
    conn = get_connection()
    cur  = conn.execute("INSERT INTO chat_logs (session_id,user_message,ai_response,model_used,prompt_tokens,output_tokens,duration_ms) VALUES (?,?,?,?,?,?,?)", (sid,umsg,areply,model,ti,to,dur))
    conn.commit(); cid = cur.lastrowid; conn.close(); return cid

def save_eval(cid, s):
    conn = get_connection()
    cur  = conn.execute("INSERT INTO eval_logs (chat_log_id,relevance,coherence,conciseness,overall_score,eval_feedback) VALUES (?,?,?,?,?,?)", (cid,s.get("relevance",0),s.get("coherence",0),s.get("conciseness",0),s.get("overall",0),s.get("feedback","")))
    conn.commit(); eid = cur.lastrowid; conn.close(); return eid

def load_history(sid):
    conn = get_connection()
    rows = conn.execute("SELECT role,content FROM conversation_memory WHERE session_id=? ORDER BY id",(sid,)).fetchall()
    conn.close()
    return [HumanMessage(content=r["content"]) if r["role"]=="user" else AIMessage(content=r["content"]) for r in rows]

def save_message(sid, role, content):
    conn = get_connection()
    conn.execute("INSERT INTO conversation_memory (session_id,role,content) VALUES (?,?,?)",(sid,role,content))
    conn.commit(); conn.close()

#  App 
app = FastAPI(title="AI Chat API", version="1.0.0")

@app.on_event("startup")
def startup(): init_db()

class ChatRequest(BaseModel):
    message   : str
    session_id: str

    @field_validator("message")
    @classmethod
    def msg_valid(cls, v):
        if not v.strip(): raise ValueError("message cannot be empty")
        if len(v) > 2000: raise ValueError("message too long")
        return v.strip()

class ChatResponse(BaseModel):
    session_id: str; user_message: str; ai_response: str
    model_used: str; duration_ms: float; eval_score: Optional[float] = None

SYSTEM_PROMPT = "You are an expert AI assistant for a FastAPI and LangChain course. Be concise."
MODEL         = "llama-3.3-70b-versatile"

llm      = ChatGroq(model=MODEL, temperature=0.7, max_retries=3)
eval_llm = ChatGroq(model=MODEL, temperature=0.1, max_retries=3)

eval_chain = (
    ChatPromptTemplate.from_messages([
        ("system", "Evaluator. Return ONLY JSON."),
        ("human",  "Question:{question}\nAnswer:{answer}\n"
                   'Return:{{"relevance":0.0,"coherence":0.0,"conciseness":0.0,"feedback":"..."}}'),
    ]) | eval_llm | JsonOutputParser()
)

prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    MessagesPlaceholder(variable_name="history"),
    ("human",  "{input}"),
])
chain = prompt | llm | StrOutputParser()

#  POST /chat (non-streaming) 
@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest):
    history  = load_history(request.session_id)
    start    = time.time()
    reply    = chain.invoke({"input": request.message, "history": history})
    duration = (time.time()-start)*1000

    save_message(request.session_id, "user",      request.message)
    save_message(request.session_id, "assistant", reply)
    chat_id = save_chat(request.session_id, request.message, reply, MODEL, 0, 0, round(duration,2))

    eval_score = None
    try:
        s = eval_chain.invoke({"question": request.message, "answer": reply})
        overall = round((s.get("relevance",0)+s.get("coherence",0)+s.get("conciseness",0))/3, 2)
        s["overall"] = overall; save_eval(chat_id, s); eval_score = overall
    except: pass

    return ChatResponse(session_id=request.session_id, user_message=request.message,
        ai_response=reply, model_used=MODEL, duration_ms=round(duration,2), eval_score=eval_score)


#  POST /chat/stream (NEW) 
@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    history = load_history(request.session_id)

    async def generate():
        full_response = ""
        start         = time.time()

        # Stream tokens
        async for chunk in chain.astream({"input": request.message, "history": history}):
            yield f"data: {chunk}\n\n" 
            full_response += chunk

        duration = (time.time()-start)*1000

        # Save to DB after stream complete
        save_message(request.session_id, "user",      request.message)
        save_message(request.session_id, "assistant", full_response)
        chat_id = save_chat(request.session_id, request.message, full_response,
                            MODEL, 0, 0, round(duration,2))

        # Eval in background (non-blocking)
        try:
            s = eval_chain.invoke({"question": request.message, "answer": full_response})
            overall = round((s.get("relevance",0)+s.get("coherence",0)+s.get("conciseness",0))/3, 2)
            s["overall"] = overall
            save_eval(chat_id, s)
        except: pass

        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


#  GET /health 
@app.get("/health")
def health():
    try:
        conn = get_connection(); conn.execute("SELECT 1"); conn.close(); db = "connected"
    except: db = "error"
    return {"status":"ok","api":"running","database":db,"version":"1.0.0"}
