"""
Milestone 05 - SQLite Logging
===================================
GOAL: Save every chat + eval result to SQLite database.
      Memory also persisted in DB - survives server restart.

BUILD ON: Milestone 04 solution

TASKS:
  1. Create database.py with:
       - get_connection()
       - init_db() - creates chat_logs, eval_logs, conversation_memory tables
  2. After every reply - save to chat_logs table
  3. After every eval  - save to eval_logs table
  4. Load conversation history from DB instead of in-memory
  5. Print " Saved to DB (id=X)" after each save

EXPECTED OUTPUT:
  You: What is FastAPI?
  AI : FastAPI is a modern web framework...
  Overall: 0.87
Saved to DB (chat_id=1, eval_id=1)
  [History loaded from DB: 2 messages]

DATABASE TABLES:
  chat_logs  (id, session_id, user_message, ai_response, model_used,
              prompt_tokens, output_tokens, duration_ms, created_at)
  eval_logs  (id, chat_log_id, relevance, coherence, conciseness,
              overall_score, eval_feedback, created_at)
  conversation_memory (id, session_id, role, content, created_at)

HINT:
  import sqlite3
  conn = sqlite3.connect("chat.db")
  conn.row_factory = sqlite3.Row

  cursor = conn.execute(
      "INSERT INTO chat_logs (session_id, user_message, ...) VALUES (?, ?, ...)",
      (session_id, user_message, ...)
  )
  conn.commit()
  chat_id = cursor.lastrowid
"""

import os, time, sqlite3
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.messages import HumanMessage, AIMessage

load_dotenv()

SESSION_ID = "dev-session-001"
DB_PATH    = "chat.db"

# - TASK 1: database.py functions (write inline here first) ──

def get_connection():
    #  Create and return SQLite connection with row_factory
    pass  #  replace

def init_db():
    #  Create all three tables if they don't exist
    # chat_logs, eval_logs, conversation_memory
    pass  #  replace

#  TASK 2: save_chat() 
def save_chat(session_id, user_msg, ai_reply, model, tokens_in,
              tokens_out, duration_ms) -> int:
    """Save chat to DB, return the new row id."""
    #  INSERT into chat_logs
    #  Return cursor.lastrowid
    pass  #  replace

#  TASK 3: save_eval() 
def save_eval(chat_log_id, scores: dict) -> int:
    """Save eval scores to DB, return the new row id."""
    #  INSERT into eval_logs
    #  Return cursor.lastrowid
    pass  #  replace

#  TASK 4: load_history() and save_message() 
def load_history(session_id: str) -> list:
    """Load conversation history from DB for a session."""
    #  SELECT from conversation_memory WHERE session_id=?
    #  Return list of HumanMessage / AIMessage objects
    pass  #  replace

def save_message(session_id: str, role: str, content: str):
    """Save one message to conversation_memory."""
    #  INSERT into conversation_memory
    pass  #  replace


#  Setup 
init_db()

SYSTEM_PROMPT = """
You are an expert AI assistant for a FastAPI and LangChain course.
You remember everything in this conversation. Be concise and technical.
"""

llm      = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.7,  max_retries=3)
eval_llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.1,  max_retries=3)

eval_chain = (
    ChatPromptTemplate.from_messages([
        ("system", "You are an evaluator. Return ONLY JSON."),
        ("human",  """Question: {question}\nResponse: {answer}\n
Score 0.0-1.0: relevance, coherence, conciseness. Add feedback.
Return: {{"relevance":0.0,"coherence":0.0,"conciseness":0.0,"feedback":"..."}}"""),
    ])
    | eval_llm
    | JsonOutputParser()
)

prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    MessagesPlaceholder(variable_name="history"),
    ("human",  "{input}"),
])
chain  = prompt | llm | StrOutputParser()


#  Chat loop with DB logging 
print(" AI Chat (with DB logging) - type 'exit' to quit")
print("-" * 50)

while True:
    user_input = input("\nYou: ").strip()

    if user_input.lower() == "exit":
        print("Goodbye!")
        break

    if not user_input:
        continue

    #  Load history from DB
    history = []  #  replace with load_history(SESSION_ID)

    start    = time.time()
    response = llm.invoke(
        [HumanMessage(content=user_input)]  # simplified - use full chain after DB works
    )
    elapsed  = (time.time() - start) * 1000
    reply    = response.content
    tokens   = response.usage_metadata

    print(f"AI : {reply}")

    #  Save message to conversation_memory
    # save_message(SESSION_ID, "user", user_input)
    # save_message(SESSION_ID, "assistant", reply)

    #  Save to chat_logs
    # chat_id = save_chat(SESSION_ID, user_input, reply, ...)

    #  Evaluate and save
    # scores  = eval_chain.invoke({"question": user_input, "answer": reply})
    # overall = round((scores["relevance"]+scores["coherence"]+scores["conciseness"])/3, 2)
    # eval_id = save_eval(chat_id, {**scores, "overall": overall})

    #  Print confirmation
    # print(f" Saved to DB (chat_id={chat_id}, eval_id={eval_id})")
    # print(f"[History loaded from DB: {len(history)} messages]")
