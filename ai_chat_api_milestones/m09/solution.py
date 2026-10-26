"""
 Milestone 09 - API Key Auth - SOLUTION
Run: uvicorn solution:app --reload
"""

import os, time, sqlite3, uuid, logging, hashlib, secrets
from typing import Optional
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Header, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, field_validator
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.messages import HumanMessage, AIMessage

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-8s | %(message)s",
    handlers=[logging.StreamHandler(), RotatingFileHandler("app.log",maxBytes=5*1024*1024,backupCount=3,encoding="utf-8")])
logger = logging.getLogger(__name__)

DB_PATH      = "chat.db"
MODEL        = "llama-3.3-70b-versatile"
ADMIN_KEY    = os.getenv("ADMIN_API_KEY", "admin-secret-change-in-production")

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
    """)
    conn.commit(); conn.close()

def save_request_log(req_id,sid,ukey,ep,method,status,dur):
    conn=get_connection(); conn.execute("INSERT INTO request_logs (request_id,session_id,user_key,endpoint,method,status_code,duration_ms) VALUES (?,?,?,?,?,?,?)",(req_id,sid,ukey,ep,method,status,round(dur,2))); conn.commit(); conn.close()

def save_chat(sid,ukey,um,ar,model,ti,to,dur):
    conn=get_connection(); cur=conn.execute("INSERT INTO chat_logs (session_id,user_key,user_message,ai_response,model_used,prompt_tokens,output_tokens,duration_ms) VALUES (?,?,?,?,?,?,?,?)",(sid,ukey,um,ar,model,ti,to,dur)); conn.commit(); cid=cur.lastrowid; conn.close(); return cid

def save_eval(cid,s):
    conn=get_connection(); cur=conn.execute("INSERT INTO eval_logs (chat_log_id,relevance,coherence,conciseness,overall_score,eval_feedback) VALUES (?,?,?,?,?,?)",(cid,s.get("relevance",0),s.get("coherence",0),s.get("conciseness",0),s.get("overall",0),s.get("feedback",""))); conn.commit(); eid=cur.lastrowid; conn.close(); return eid

def load_history(sid):
    conn=get_connection(); rows=conn.execute("SELECT role,content FROM conversation_memory WHERE session_id=? ORDER BY id",(sid,)).fetchall(); conn.close()
    return [HumanMessage(content=r["content"]) if r["role"]=="user" else AIMessage(content=r["content"]) for r in rows]

def save_message(sid,role,content):
    conn=get_connection(); conn.execute("INSERT INTO conversation_memory (session_id,role,content) VALUES (?,?,?)",(sid,role,content)); conn.commit(); conn.close()

#  TASK 2: hash_key ─
def hash_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()

#  TASK 4: verify_api_key ─
async def verify_api_key(x_api_key: str = Header(...)) -> str:
    hashed = hash_key(x_api_key)
    conn   = get_connection()
    row    = conn.execute("SELECT user_name FROM api_keys WHERE key_hash=? AND is_active=1", (hashed,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=403, detail="Invalid or missing API key")
    return row["user_name"]

#  App 
app = FastAPI(title="AI Chat API", version="1.0.0")

@app.on_event("startup")
def startup():
    init_db()
    # Seed admin key if no keys exist
    conn  = get_connection()
    count = conn.execute("SELECT COUNT(*) FROM api_keys").fetchone()[0]
    if count == 0:
        conn.execute("INSERT INTO api_keys (key_hash, user_name) VALUES (?,?)", (hash_key(ADMIN_KEY), "admin"))
        conn.commit()
        logger.info(" Admin key seeded")
    conn.close()

@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    req_id=str(uuid.uuid4())[:8]; session_id=request.headers.get("X-Session-ID","unknown"); user_key=request.headers.get("X-API-Key","none")[:8]+"..."
    logger.info(f"[{req_id}] ->  {request.method} {request.url.path}")
    start=time.time(); response=await call_next(request); duration=(time.time()-start)*1000
    logger.info(f"[{req_id}] <-  {response.status_code} | {duration:.0f}ms")
    save_request_log(req_id,session_id,user_key,str(request.url.path),request.method,response.status_code,duration)
    response.headers["X-Request-ID"]=req_id; return response

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
SYSTEM="You are an expert AI assistant for a FastAPI and LangChain course. Be concise."
llm=ChatGroq(model=MODEL,temperature=0.7,max_retries=3)
eval_llm=ChatGroq(model=MODEL,temperature=0.1,max_retries=3)
eval_chain=(ChatPromptTemplate.from_messages([("system","Evaluator. Return ONLY JSON."),("human","Q:{question}\nA:{answer}\nReturn:{{'relevance':0.0,'coherence':0.0,'conciseness':0.0,'feedback':'...'}}")])|eval_llm|JsonOutputParser())
chain=(ChatPromptTemplate.from_messages([("system",SYSTEM),MessagesPlaceholder(variable_name="history"),("human","{input}")])|llm|StrOutputParser())

#  TASK 3: POST /auth/generate-key 
@app.post("/auth/generate-key")
def generate_key(request: GenerateKeyRequest, x_api_key: str = Header(...)):
    if x_api_key != ADMIN_KEY:
        raise HTTPException(403, "Admin key required")
    new_key = secrets.token_urlsafe(32)
    hashed  = hash_key(new_key)
    conn    = get_connection()
    try:
        conn.execute("INSERT INTO api_keys (key_hash, user_name) VALUES (?,?)", (hashed, request.user_name))
        conn.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(409, "Key already exists")
    finally:
        conn.close()
    logger.info(f"New API key generated for: {request.user_name}")
    return {"api_key": new_key, "user_name": request.user_name, "message": "Store safely - not shown again"}

#  TASK 5: Protected endpoints ─
@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest, user: str = Depends(verify_api_key)):
    history=load_history(request.session_id); start=time.time()
    reply=chain.invoke({"input":request.message,"history":history}); duration=(time.time()-start)*1000
    save_message(request.session_id,"user",request.message); save_message(request.session_id,"assistant",reply)
    chat_id=save_chat(request.session_id,user,request.message,reply,MODEL,0,0,round(duration,2))
    eval_score=None
    try:
        s=eval_chain.invoke({"question":request.message,"answer":reply})
        overall=round((s.get("relevance",0)+s.get("coherence",0)+s.get("conciseness",0))/3,2); s["overall"]=overall; save_eval(chat_id,s); eval_score=overall
    except: pass
    return ChatResponse(session_id=request.session_id,user_message=request.message,ai_response=reply,model_used=MODEL,duration_ms=round(duration,2),eval_score=eval_score)

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
        try:
            s=eval_chain.invoke({"question":request.message,"answer":full})
            overall=round((s.get("relevance",0)+s.get("coherence",0)+s.get("conciseness",0))/3,2); s["overall"]=overall; save_eval(chat_id,s)
        except: pass
        yield "data: [DONE]\n\n"
    return StreamingResponse(generate(),media_type="text/event-stream")

@app.get("/logs", dependencies=[Depends(verify_api_key)])
def get_logs(limit: int=20, offset: int=0):
    conn=get_connection(); rows=conn.execute("SELECT * FROM request_logs ORDER BY id DESC LIMIT ? OFFSET ?",(limit,offset)).fetchall(); total=conn.execute("SELECT COUNT(*) FROM request_logs").fetchone()[0]; conn.close()
    return {"total":total,"items":[dict(r) for r in rows]}

@app.get("/logs/chat", dependencies=[Depends(verify_api_key)])
def get_chat_logs(limit: int=20, offset: int=0):
    conn=get_connection(); rows=conn.execute("SELECT c.id,c.session_id,c.user_key,c.user_message,c.ai_response,c.duration_ms,c.created_at,e.overall_score,e.eval_feedback FROM chat_logs c LEFT JOIN eval_logs e ON e.chat_log_id=c.id ORDER BY c.id DESC LIMIT ? OFFSET ?",(limit,offset)).fetchall(); total=conn.execute("SELECT COUNT(*) FROM chat_logs").fetchone()[0]; conn.close()
    return {"total":total,"items":[dict(r) for r in rows]}

@app.get("/health")
def health():
    try: conn=get_connection(); conn.execute("SELECT 1"); conn.close(); db="connected"
    except: db="error"
    return {"status":"ok","api":"running","database":db}
