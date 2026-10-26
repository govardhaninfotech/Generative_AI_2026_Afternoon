"""
 Milestone 10 - Complete Production AI Chat API - SOLUTION
=============================================================
Run: uvicorn solution:app --reload
Docs: http://127.0.0.1:8000/docs
"""

import os, time, sqlite3, uuid, logging, hashlib, secrets
from typing import Optional
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Header, HTTPException, Depends
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, field_validator
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.messages import HumanMessage, AIMessage

load_dotenv()

#  Logging 
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-8s | %(message)s",
    handlers=[logging.StreamHandler(),
              RotatingFileHandler("app.log",maxBytes=5*1024*1024,backupCount=3,encoding="utf-8")])
logger = logging.getLogger(__name__)

DB_PATH   = "chat.db"
MODEL     = "llama-3.3-70b-versatile"
ADMIN_KEY = os.getenv("ADMIN_API_KEY","admin-secret-change-in-production")

#  DB 
def get_connection():
    conn=sqlite3.connect(DB_PATH); conn.row_factory=sqlite3.Row; return conn

def init_db():
    conn=get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS api_keys (id INTEGER PRIMARY KEY AUTOINCREMENT, key_hash TEXT NOT NULL UNIQUE, user_name TEXT NOT NULL, is_active INTEGER NOT NULL DEFAULT 1, created_at TEXT DEFAULT (datetime('now')));
        CREATE TABLE IF NOT EXISTS chat_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT, user_key TEXT, user_message TEXT, ai_response TEXT, model_used TEXT, prompt_tokens INTEGER DEFAULT 0, output_tokens INTEGER DEFAULT 0, duration_ms REAL DEFAULT 0, created_at TEXT DEFAULT (datetime('now')));
        CREATE TABLE IF NOT EXISTS eval_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, chat_log_id INTEGER, relevance REAL, coherence REAL, conciseness REAL, overall_score REAL, eval_feedback TEXT, created_at TEXT DEFAULT (datetime('now')));
        CREATE TABLE IF NOT EXISTS conversation_memory (id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT, role TEXT, content TEXT, created_at TEXT DEFAULT (datetime('now')));
        CREATE TABLE IF NOT EXISTS request_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, request_id TEXT, session_id TEXT, user_key TEXT, endpoint TEXT, method TEXT, status_code INTEGER, duration_ms REAL, created_at TEXT DEFAULT (datetime('now')));
        CREATE INDEX IF NOT EXISTS idx_mem_session ON conversation_memory(session_id);
        CREATE INDEX IF NOT EXISTS idx_chat_session ON chat_logs(session_id);
    """)
    conn.commit(); conn.close()

def save_request_log(rid,sid,ukey,ep,method,status,dur):
    conn=get_connection(); conn.execute("INSERT INTO request_logs (request_id,session_id,user_key,endpoint,method,status_code,duration_ms) VALUES (?,?,?,?,?,?,?)",(rid,sid,ukey,ep,method,status,round(dur,2))); conn.commit(); conn.close()

def save_chat(sid,ukey,um,ar,model,ti,to,dur):
    conn=get_connection(); cur=conn.execute("INSERT INTO chat_logs (session_id,user_key,user_message,ai_response,model_used,prompt_tokens,output_tokens,duration_ms) VALUES (?,?,?,?,?,?,?,?)",(sid,ukey,um,ar,model,ti,to,dur)); conn.commit(); cid=cur.lastrowid; conn.close(); return cid

def save_eval(cid,s):
    conn=get_connection(); cur=conn.execute("INSERT INTO eval_logs (chat_log_id,relevance,coherence,conciseness,overall_score,eval_feedback) VALUES (?,?,?,?,?,?)",(cid,s.get("relevance",0),s.get("coherence",0),s.get("conciseness",0),s.get("overall",0),s.get("feedback",""))); conn.commit(); eid=cur.lastrowid; conn.close(); return eid

def load_history(sid):
    conn=get_connection(); rows=conn.execute("SELECT role,content FROM conversation_memory WHERE session_id=? ORDER BY id",(sid,)).fetchall(); conn.close()
    return [HumanMessage(content=r["content"]) if r["role"]=="user" else AIMessage(content=r["content"]) for r in rows]

def save_message(sid,role,content):
    conn=get_connection(); conn.execute("INSERT INTO conversation_memory (session_id,role,content) VALUES (?,?,?)",(sid,role,content)); conn.commit(); conn.close()

def hash_key(key): return hashlib.sha256(key.encode()).hexdigest()

async def verify_api_key(x_api_key: str = Header(...)) -> str:
    hashed=hash_key(x_api_key); conn=get_connection()
    row=conn.execute("SELECT user_name FROM api_keys WHERE key_hash=? AND is_active=1",(hashed,)).fetchone(); conn.close()
    if not row: raise HTTPException(403,"Invalid or missing API key")
    return row["user_name"]

#  App 
app = FastAPI(title="AI Chat API",
              description="Production-grade conversational AI with LangChain, SQLite logging, and prompt eval",
              version="1.0.0")

# TASK 5: CORS
app.add_middleware(CORSMiddleware,
    allow_origins=["http://localhost:8501","http://localhost:3000"],
    allow_methods=["*"], allow_headers=["*"], allow_credentials=True)

# TASK 4: Global exception handlers
@app.exception_handler(Exception)
async def global_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error on {request.url}: {exc}")
    return JSONResponse(status_code=500, content={"success":False,"error":"Internal server error"})

@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    errors=[{"field":"→".join(str(x) for x in e["loc"]),"message":e["msg"]} for e in exc.errors()]
    return JSONResponse(status_code=422, content={"success":False,"error":"Validation failed","details":errors})

@app.exception_handler(HTTPException)
async def http_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"success":False,"error":exc.detail})

@app.on_event("startup")
def startup():
    init_db()
    conn=get_connection(); count=conn.execute("SELECT COUNT(*) FROM api_keys").fetchone()[0]
    if count==0: conn.execute("INSERT INTO api_keys (key_hash,user_name) VALUES (?,?)",(hash_key(ADMIN_KEY),"admin")); conn.commit(); logger.info("✅ Admin key seeded")
    conn.close(); logger.info(" AI Chat API started")

@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    rid=str(uuid.uuid4())[:8]; sid=request.headers.get("X-Session-ID","unknown"); ukey=request.headers.get("X-API-Key","none")[:8]+"..."
    logger.info(f"[{rid}] ->  {request.method} {request.url.path}")
    start=time.time(); response=await call_next(request); duration=(time.time()-start)*1000
    logger.info(f"[{rid}] <-  {response.status_code} | {duration:.0f}ms")
    save_request_log(rid,sid,ukey,str(request.url.path),request.method,response.status_code,duration)
    response.headers["X-Request-ID"]=rid; return response

#  Models 
class ChatRequest(BaseModel):
    message: str; session_id: str
    @field_validator("message")
    @classmethod
    def mv(cls,v):
        if not v.strip(): raise ValueError("empty")
        if len(v)>2000:   raise ValueError("too long")
        return v.strip()

class ChatResponse(BaseModel):
    session_id: str; user_message: str; ai_response: str
    model_used: str; duration_ms: float; eval_score: Optional[float]=None

class GenerateKeyRequest(BaseModel):
    user_name: str

#  LLM 
SYSTEM="You are an expert AI assistant for a FastAPI and LangChain course. Be concise and technical."
llm=ChatGroq(model=MODEL,temperature=0.7,max_retries=3)
eval_llm=ChatGroq(model=MODEL,temperature=0.1,max_retries=3)
eval_chain=(ChatPromptTemplate.from_messages([("system","Evaluator. Return ONLY JSON. No markdown."),("human","Q:{question}\nA:{answer}\nReturn:{{'relevance':0.0,'coherence':0.0,'conciseness':0.0,'feedback':'...'}}")])|eval_llm|JsonOutputParser())
chain=(ChatPromptTemplate.from_messages([("system",SYSTEM),MessagesPlaceholder(variable_name="history"),("human","{input}")])|llm|StrOutputParser())

def run_eval(question, answer, chat_id):
    try:
        s=eval_chain.invoke({"question":question,"answer":answer})
        overall=round((s.get("relevance",0)+s.get("coherence",0)+s.get("conciseness",0))/3,2); s["overall"]=overall; save_eval(chat_id,s); return overall
    except: return None

#  AUTH 
@app.post("/auth/generate-key")
def generate_key(request: GenerateKeyRequest, x_api_key: str = Header(...)):
    if x_api_key != ADMIN_KEY: raise HTTPException(403,"Admin key required")
    new_key=secrets.token_urlsafe(32); hashed=hash_key(new_key)
    conn=get_connection()
    try: conn.execute("INSERT INTO api_keys (key_hash,user_name) VALUES (?,?)",(hashed,request.user_name)); conn.commit()
    except sqlite3.IntegrityError: raise HTTPException(409,"Key exists")
    finally: conn.close()
    logger.info(f"New key for: {request.user_name}")
    return {"api_key":new_key,"user_name":request.user_name,"message":"Store safely - not shown again"}

#  CHAT 
@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest, user: str = Depends(verify_api_key)):
    history=load_history(request.session_id); start=time.time()
    reply=chain.invoke({"input":request.message,"history":history}); duration=(time.time()-start)*1000
    save_message(request.session_id,"user",request.message); save_message(request.session_id,"assistant",reply)
    chat_id=save_chat(request.session_id,user,request.message,reply,MODEL,0,0,round(duration,2))
    return ChatResponse(session_id=request.session_id,user_message=request.message,ai_response=reply,model_used=MODEL,duration_ms=round(duration,2),eval_score=run_eval(request.message,reply,chat_id))

@app.post("/chat/stream")
async def chat_stream(request: ChatRequest, user: str = Depends(verify_api_key)):
    history=load_history(request.session_id)
    async def generate():
        full=""; start=time.time()
        async for chunk in chain.astream({"input":request.message,"history":history}):
            yield f"data: {chunk}\n\n"; full+=chunk
        duration=(time.time()-start)*1000
        save_message(request.session_id,"user",request.message); save_message(request.session_id,"assistant",full)
        chat_id=save_chat(request.session_id,user,request.message,full,MODEL,0,0,round(duration,2))
        run_eval(request.message,full,chat_id)
        yield "data: [DONE]\n\n"
    return StreamingResponse(generate(),media_type="text/event-stream")

# TASK 1: GET /chat/history
@app.get("/chat/history")
def get_history(session_id: str, user: str = Depends(verify_api_key)):
    conn=get_connection()
    rows=conn.execute("SELECT role,content,created_at FROM conversation_memory WHERE session_id=? ORDER BY id",(session_id,)).fetchall()
    conn.close()
    return {"session_id":session_id,"total":len(rows),"messages":[dict(r) for r in rows]}

# TASK 2: DELETE /chat/history
@app.delete("/chat/history")
def clear_history(session_id: str, user: str = Depends(verify_api_key)):
    conn=get_connection(); deleted=conn.execute("DELETE FROM conversation_memory WHERE session_id=?",(session_id,)).rowcount; conn.commit(); conn.close()
    return {"message":f"Cleared {deleted} messages for session {session_id}"}

#  LOGS 
@app.get("/logs", dependencies=[Depends(verify_api_key)])
def get_logs(limit: int=20, offset: int=0):
    conn=get_connection(); rows=conn.execute("SELECT * FROM request_logs ORDER BY id DESC LIMIT ? OFFSET ?",(limit,offset)).fetchall(); total=conn.execute("SELECT COUNT(*) FROM request_logs").fetchone()[0]; conn.close()
    return {"total":total,"items":[dict(r) for r in rows]}

@app.get("/logs/chat", dependencies=[Depends(verify_api_key)])
def get_chat_logs(limit: int=20, offset: int=0):
    conn=get_connection(); rows=conn.execute("SELECT c.id,c.session_id,c.user_key,c.user_message,c.ai_response,c.duration_ms,c.created_at,e.overall_score,e.eval_feedback FROM chat_logs c LEFT JOIN eval_logs e ON e.chat_log_id=c.id ORDER BY c.id DESC LIMIT ? OFFSET ?",(limit,offset)).fetchall(); total=conn.execute("SELECT COUNT(*) FROM chat_logs").fetchone()[0]; conn.close()
    return {"total":total,"items":[dict(r) for r in rows]}

# TASK 3: GET /eval/summary
@app.get("/eval/summary", dependencies=[Depends(verify_api_key)])
def eval_summary():
    conn=get_connection()
    stats=conn.execute("SELECT COUNT(*) as total, AVG(relevance) as avg_rel, AVG(coherence) as avg_coh, AVG(conciseness) as avg_con, AVG(overall_score) as avg_overall FROM eval_logs").fetchone()
    best =conn.execute("SELECT c.session_id, AVG(e.overall_score) as avg_score FROM eval_logs e JOIN chat_logs c ON c.id=e.chat_log_id GROUP BY c.session_id ORDER BY avg_score DESC LIMIT 1").fetchone()
    worst=conn.execute("SELECT c.session_id, AVG(e.overall_score) as avg_score FROM eval_logs e JOIN chat_logs c ON c.id=e.chat_log_id GROUP BY c.session_id ORDER BY avg_score ASC LIMIT 1").fetchone()
    conn.close()
    return {"total_evaluations":stats["total"],"avg_relevance":round(stats["avg_rel"] or 0,2),"avg_coherence":round(stats["avg_coh"] or 0,2),"avg_conciseness":round(stats["avg_con"] or 0,2),"avg_overall":round(stats["avg_overall"] or 0,2),"best_session":best["session_id"] if best else None,"worst_session":worst["session_id"] if worst else None}

# TASK 6: Polished /health
@app.get("/health")
def health():
    try:
        conn=get_connection(); conn.execute("SELECT 1")
        total_chats   =conn.execute("SELECT COUNT(*) FROM chat_logs").fetchone()[0]
        total_sessions=conn.execute("SELECT COUNT(DISTINCT session_id) FROM chat_logs").fetchone()[0]
        avg_eval      =conn.execute("SELECT AVG(overall_score) FROM eval_logs").fetchone()[0]
        conn.close(); db="connected"
    except Exception as e: db=f"error: {e}"; total_chats=0; total_sessions=0; avg_eval=0
    return {"status":"ok","api":"running","database":db,"model":MODEL,"version":"1.0.0","total_chats":total_chats,"total_sessions":total_sessions,"avg_eval_score":round(avg_eval or 0,2)}
