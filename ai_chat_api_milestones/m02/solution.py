"""
 Milestone 02 — System Prompt + Token Usage — SOLUTION
"""

import os, time
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

load_dotenv()

llm = ChatGroq(
    model       = "llama-3.3-70b-versatile",
    temperature = 0.7,
    max_retries = 3,
)

# TASK 1: Detailed system prompt
SYSTEM_PROMPT = """
You are an expert AI assistant for a FastAPI and LangChain development course.
Your audience is experienced software developers (Python, Node.js, Flutter).

Guidelines:
- Be concise and technical
- Use code examples when helpful
- Max 3 sentences unless a code example is needed
- Never be vague — give specific, actionable answers
"""

QUESTIONS = [
    "What is FastAPI?",
    "What is LangChain?",
    "What is a vector database?",
]

# TASKS 2-5: Loop, call, print
for i, question in enumerate(QUESTIONS, 1):
    print(f"\n── Question {i} ──")
    print(f"Q: {question}")

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=question),
    ]

    start    = time.time()
    response = llm.invoke(messages)
    elapsed  = time.time() - start

    print(f"A: {response.content}")

    tokens = response.usage_metadata
    print(f"\nTokens => prompt: {tokens['input_tokens']} | output: {tokens['output_tokens']} | total: {tokens['total_tokens']}")
    print(f"Time   => {elapsed:.2f}s")
