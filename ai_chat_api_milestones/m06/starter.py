"""
 Milestone 06 - Wrap in FastAPI
====================================
GOAL: Turn the CLI chatbot into a REST API endpoint.
      POST /chat -> accepts message + session_id, returns AI reply.

BUILD ON: Milestone 05 solution

TASKS:
  1. Create FastAPI app with title and description
  2. Call init_db() on startup using @app.on_event("startup")
  3. Define ChatRequest Pydantic model (message, session_id)
  4. Define ChatResponse Pydantic model (session_id, user_message,
     ai_response, model_used, duration_ms, eval_score)
  5. Create POST /chat endpoint - uses all logic from M05
  6. Create GET /health endpoint
  7. Test in Swagger UI: http://127.0.0.1:8000/docs

RUN:
  uvicorn starter:app --reload

EXPECTED SWAGGER TEST:
  POST /chat
  Body: {"message": "What is FastAPI?", "session_id": "test-123"}

  Response:
  {
    "session_id"  : "test-123",
    "user_message": "What is FastAPI?",
    "ai_response" : "FastAPI is a modern...",
    "model_used"  : "llama-3.3-70b-versatile",
    "duration_ms" : 823.4,
    "eval_score"  : 0.88
  }

HINT:
  from fastapi import FastAPI
  app = FastAPI(title="AI Chat API")

  @app.on_event("startup")
  def startup(): init_db()

  @app.post("/chat", response_model=ChatResponse)
  def chat(request: ChatRequest): ...
"""

import os, time
from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel, field_validator
from typing import Optional
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.messages import HumanMessage, AIMessage
import sqlite3

load_dotenv()

DB_PATH = "chat.db"

#  Copy DB functions from M05 
# (get_connection, init_db, save_chat, save_eval,
#  load_history, save_message)
#  Paste your M05 DB functions here


#  TASK 1: Create FastAPI app 
#  app = FastAPI(title=..., description=..., version=...)
app = None  #  replace


#  TASK 2: Startup event 
#  @app.on_event("startup")
#  def startup(): init_db()


#  TASK 3 & 4: Pydantic models 
class ChatRequest(BaseModel):
    message   : str
    session_id: str
    #  Add validators: message not empty, max 2000 chars


class ChatResponse(BaseModel):
    session_id  : str
    user_message: str
    ai_response : str
    model_used  : str
    duration_ms : float
    eval_score  : Optional[float] = None


#  LLM setup (copy from M04/M05) 
SYSTEM_PROMPT = """
You are an expert AI assistant for a FastAPI and LangChain course.
You remember everything in this conversation. Be concise and technical.
"""

llm      = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.7, max_retries=3)
eval_llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.1, max_retries=3)

eval_chain = (
    ChatPromptTemplate.from_messages([
        ("system", "You are an evaluator. Return ONLY JSON."),
        ("human",  "Question: {question}\nAnswer: {answer}\n"
                   'Score 0.0-1.0: relevance, coherence, conciseness. '
                   'Return: {{"relevance":0.0,"coherence":0.0,"conciseness":0.0,"feedback":"..."}}'),
    ])
    | eval_llm | JsonOutputParser()
)

prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    MessagesPlaceholder(variable_name="history"),
    ("human",  "{input}"),
])
chain  = prompt | llm | StrOutputParser()


#  TASK 5: POST /chat endpoint 
#  @app.post("/chat", response_model=ChatResponse)
#  def chat_endpoint(request: ChatRequest):
#        # load history, invoke chain, save to DB, eval, return response
#        pass


# TASK 6: GET /health endpoint 
#  @app.get("/health")
#  def health():
#        return {"status": "ok", "api": "running", "database": "connected"}
