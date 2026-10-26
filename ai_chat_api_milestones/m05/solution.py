"""
Milestone 05 - SQLite Logging - SOLUTION
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

# TASK 1: DB functions
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS chat_logs (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id    TEXT    NOT NULL,
            user_message  TEXT    NOT NULL,
            ai_response   TEXT    NOT NULL,
            model_used    TEXT    NOT NULL,
            prompt_tokens INTEGER DEFAULT 0,
            output_tokens INTEGER DEFAULT 0,
            duration_ms   REAL    DEFAULT 0,
            created_at    TEXT    DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS eval_logs (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_log_id   INTEGER NOT NULL,
            relevance     REAL    NOT NULL,
            coherence     REAL    NOT NULL,
            conciseness   REAL    NOT NULL,
            overall_score REAL    NOT NULL,
            eval_feedback TEXT,
            created_at    TEXT    DEFAULT (datetime('now')),
            FOREIGN KEY (chat_log_id) REFERENCES chat_logs(id)
        );
        CREATE TABLE IF NOT EXISTS conversation_memory (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT    NOT NULL,
            role       TEXT    NOT NULL,
            content    TEXT    NOT NULL,
            created_at TEXT    DEFAULT (datetime('now'))
        );
    """)
    conn.commit()
    conn.close()
    print(" Database ready")

# TASK 2: save_chat
def save_chat(session_id, user_msg, ai_reply, model,
              tokens_in, tokens_out, duration_ms) -> int:
    conn   = get_connection()
    cursor = conn.execute(
        """INSERT INTO chat_logs
           (session_id, user_message, ai_response, model_used,
            prompt_tokens, output_tokens, duration_ms)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (session_id, user_msg, ai_reply, model,
         tokens_in, tokens_out, duration_ms)
    )
    conn.commit()
    chat_id = cursor.lastrowid
    conn.close()
    return chat_id

# TASK 3: save_eval
def save_eval(chat_log_id, scores: dict) -> int:
    conn   = get_connection()
    cursor = conn.execute(
        """INSERT INTO eval_logs
           (chat_log_id, relevance, coherence, conciseness,
            overall_score, eval_feedback)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (chat_log_id,
         scores.get("relevance",    0),
         scores.get("coherence",    0),
         scores.get("conciseness",  0),
         scores.get("overall",      0),
         scores.get("feedback",    ""))
    )
    conn.commit()
    eval_id = cursor.lastrowid
    conn.close()
    return eval_id

# TASK 4: load_history and save_message
def load_history(session_id: str) -> list:
    conn = get_connection()
    rows = conn.execute(
        "SELECT role, content FROM conversation_memory WHERE session_id=? ORDER BY id",
        (session_id,)
    ).fetchall()
    conn.close()
    messages = []
    for row in rows:
        if row["role"] == "user":
            messages.append(HumanMessage(content=row["content"]))
        else:
            messages.append(AIMessage(content=row["content"]))
    return messages

def save_message(session_id: str, role: str, content: str):
    conn = get_connection()
    conn.execute(
        "INSERT INTO conversation_memory (session_id, role, content) VALUES (?, ?, ?)",
        (session_id, role, content)
    )
    conn.commit()
    conn.close()


# Setup
init_db()

SYSTEM_PROMPT = """
You are an expert AI assistant for a FastAPI and LangChain course.
You remember everything in this conversation. Be concise and technical.
"""

llm      = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.7, max_retries=3)
eval_llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.1, max_retries=3)

eval_chain = (
    ChatPromptTemplate.from_messages([
        ("system", "You are an evaluator. Return ONLY JSON. No markdown."),
        ("human",  "Question: {question}\nAnswer: {answer}\n"
                   "Score 0.0-1.0: relevance, coherence, conciseness. One sentence feedback.\n"
                   'Return: {{"relevance":0.0,"coherence":0.0,"conciseness":0.0,"feedback":"..."}}'),
    ])
    | eval_llm | JsonOutputParser()
)

prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{input}"),
])
chain = prompt | llm | StrOutputParser()

# Chat loop
print("AI Chat (with DB logging) - type 'exit' to quit")
print("-" * 50)

while True:
    user_input = input("\nYou: ").strip()

    if user_input.lower() == "exit":
        print("Goodbye!")
        break

    if not user_input:
        continue

    history  = load_history(SESSION_ID)
    start    = time.time()
    reply    = chain.invoke({"input": user_input, "history": history})
    elapsed  = (time.time() - start) * 1000

    # Get token usage
    raw      = llm.invoke([HumanMessage(content=user_input)])
    tokens   = raw.usage_metadata

    print(f"AI : {reply}")

    save_message(SESSION_ID, "user",      user_input)
    save_message(SESSION_ID, "assistant", reply)

    chat_id = save_chat(
        SESSION_ID, user_input, reply,
        "llama-3.3-70b-versatile",
        tokens.get("input_tokens",  0),
        tokens.get("output_tokens", 0),
        round(elapsed, 2)
    )

    try:
        scores  = eval_chain.invoke({"question": user_input, "answer": reply})
        overall = round((scores.get("relevance",0)+scores.get("coherence",0)+scores.get("conciseness",0))/3, 2)
        scores["overall"] = overall
        eval_id = save_eval(chat_id, scores)
        print(f" Overall: {overall:.2f} | Feedback: {scores.get('feedback','')[:60]}")
        print(f" Saved to DB (chat_id={chat_id}, eval_id={eval_id})")
    except Exception as e:
        print(f"Eval error: {e}")

    print(f"[History from DB: {len(history)+2} messages]")
