"""
 Milestone 06  FastAPI Endpoint  SOLUTION
Run: uvicorn solution:app --reload
"""

import os, time, sqlite3
from typing import Optional
from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel, field_validator
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.messages import HumanMessage, AIMessage

load_dotenv()

DB_PATH = "chat.db"

#  DB functions
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS chat_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT, user_message TEXT, ai_response TEXT,
            model_used TEXT, prompt_tokens INTEGER DEFAULT 0,
            output_tokens INTEGER DEFAULT 0, duration_ms REAL DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now'))
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
        CREATE TABLE IF NOT EXISTS request_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT,
            endpoint TEXT, method TEXT, status_code INTEGER,
            duration_ms REAL, created_at TEXT DEFAULT (datetime('now'))
        );
    """)
    conn.commit()
    conn.close()

def save_chat(session_id, user_msg, ai_reply, model, ti, to, dur) -> int:
    conn = get_connection()
    cur  = conn.execute(
        "INSERT INTO chat_logs (session_id,user_message,ai_response,model_used,prompt_tokens,output_tokens,duration_ms) VALUES (?,?,?,?,?,?,?)",
        (session_id, user_msg, ai_reply, model, ti, to, dur)
    )
    conn.commit(); chat_id = cur.lastrowid; conn.close()
    return chat_id

def save_eval(chat_log_id, scores) -> int:
    conn = get_connection()
    cur  = conn.execute(
        "INSERT INTO eval_logs (chat_log_id,relevance,coherence,conciseness,overall_score,eval_feedback) VALUES (?,?,?,?,?,?)",
        (chat_log_id, scores.get("relevance",0), scores.get("coherence",0),
         scores.get("conciseness",0), scores.get("overall",0), scores.get("feedback",""))
    )
    conn.commit(); eval_id = cur.lastrowid; conn.close()
    return eval_id

def load_history(session_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT role, content FROM conversation_memory WHERE session_id=? ORDER BY id",
        (session_id,)
    ).fetchall()
    conn.close()
    return [HumanMessage(content=r["content"]) if r["role"]=="user" else AIMessage(content=r["content"]) for r in rows]

def save_message(session_id, role, content):
    conn = get_connection()
    conn.execute("INSERT INTO conversation_memory (session_id,role,content) VALUES (?,?,?)", (session_id, role, content))
    conn.commit(); conn.close()


#  TASK 1: FastAPI app 
app = FastAPI(
    title       = "AI Chat API",
    description = "LangChain-powered conversational AI with logging and eval",
    version     = "1.0.0",
)

#  TASK 2: Startup 
@app.on_event("startup")
def startup():
    init_db()
    print(" Database ready")

#  TASK 3 & 4: Models 
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
    session_id  : str
    user_message: str
    ai_response : str
    model_used  : str
    duration_ms : float
    eval_score  : Optional[float] = None

#  LLM setup
SYSTEM_PROMPT = "You are an expert AI assistant for a FastAPI and LangChain course. Be concise and technical."

llm      = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.7, max_retries=3)
eval_llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.1, max_retries=3)

eval_chain = (
    ChatPromptTemplate.from_messages([
        ("system", "You are an evaluator. Return ONLY JSON. No markdown."),
        ("human",  "Question: {question}\nAnswer: {answer}\n"
                   'Score 0.0-1.0: relevance, coherence, conciseness. '
                   'Return: {{"relevance":0.0,"coherence":0.0,"conciseness":0.0,"feedback":"..."}}'),
    ]) | eval_llm | JsonOutputParser()
)

prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    MessagesPlaceholder(variable_name="history"),
    ("human",  "{input}"),
])
chain = prompt | llm | StrOutputParser()

# TASK 5: POST /chat 
@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest):
    history  = load_history(request.session_id)
    start    = time.time()
    reply    = chain.invoke({"input": request.message, "history": history})
    duration = (time.time() - start) * 1000

    save_message(request.session_id, "user",      request.message)
    save_message(request.session_id, "assistant", reply)

    chat_id = save_chat(
        request.session_id, request.message, reply,
        "llama-3.3-70b-versatile", 0, 0, round(duration, 2)
    )

    eval_score = None
    try:
        scores     = eval_chain.invoke({"question": request.message, "answer": reply})
        overall    = round((scores.get("relevance",0)+scores.get("coherence",0)+scores.get("conciseness",0))/3, 2)
        scores["overall"] = overall
        save_eval(chat_id, scores)
        eval_score = overall
    except: pass

    return ChatResponse(
        session_id   = request.session_id,
        user_message = request.message,
        ai_response  = reply,
        model_used   = "llama-3.3-70b-versatile",
        duration_ms  = round(duration, 2),
        eval_score   = eval_score,
    )

# TASK 6: GET /health 
@app.get("/health")
def health():
    try:
        conn = get_connection()
        conn.execute("SELECT 1"); conn.close()
        db = "connected"
    except: db = "error"
    return {"status": "ok", "api": "running", "database": db, "version": "1.0.0"}
