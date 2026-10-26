"""
Milestone 02 — System Prompt + Token Usage
===============================================
GOAL: Add a proper system prompt and inspect the response object.

BUILD ON: Milestone 01 solution

TASKS:
  1. Define a detailed system prompt for a chatbot persona
  2. Ask 3 different questions using the same system prompt
  3. Print response.content (the text)
  4. Print token usage after each response:
       Prompt tokens  : X
       Output tokens  : Y
       Total tokens   : Z
  5. Print time taken for each call (use time.time())

EXPECTED OUTPUT:
  ── Question 1 ──
  Q: What is FastAPI?
  A: FastAPI is a modern, fast web framework...

  Tokens → prompt: 45 | output: 67 | total: 112
  Time   → 0.82s

  ── Question 2 ──
  ...

HINT:
  response.usage_metadata gives you token counts
  response.usage_metadata["input_tokens"]
  response.usage_metadata["output_tokens"]
  response.usage_metadata["total_tokens"]
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

# ── TASK 1: Define a detailed system prompt ───────────────────
# Make it specific — a developer assistant for a FastAPI + AI course
#  SYSTEM_PROMPT = """..."""


# ── TASK 2-5: Ask 3 questions, print response + tokens + time ─
QUESTIONS = [
    "What is FastAPI?",
    "What is LangChain?",
    "What is a vector database?",
]

for i, question in enumerate(QUESTIONS, 1):
    print(f"\n── Question {i} ──")
    print(f"Q: {question}")

    #  Build messages list with SYSTEM_PROMPT + question
    messages = []  #  replace with your code

    #  Record start time
    start = 0  #  replace with time.time()

    #  Call llm.invoke(messages)
    response = None  #  replace with your code

    #  Calculate elapsed time
    elapsed = 0  #  replace with your code

    #  Print response content
    # print(f"A: {response.content}")

    #  Print token usage
    # print(f"\nTokens => prompt: X | output: Y | total: Z")

    #  Print time
    # print(f"Time   => {elapsed:.2f}s")
