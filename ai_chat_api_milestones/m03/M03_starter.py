"""
 Milestone 03 — Memory (Multi-turn Conversation)
=====================================================
GOAL: Build a real multi-turn chatbot using ConversationBufferWindowMemory.
      The bot remembers previous messages within the session.

BUILD ON: Milestone 02 solution

TASKS:
  1. Import and create ConversationBufferWindowMemory (k=10)
  2. Build a ChatPromptTemplate with MessagesPlaceholder for history
  3. Build chain: prompt | llm | StrOutputParser
  4. Build a while loop — keep chatting until user types 'exit'
  5. Each turn:
       - Load history from memory
       - Invoke chain with input + history
       - Save context to memory
       - Print reply
       - Print message count in memory

EXPECTED OUTPUT:
   AI Chat Assistant (type 'exit' to quit)
  ─────────────────────────────────────────
  You: What is LangChain?
  AI : LangChain is a framework for building LLM-powered apps...
  [2 messages in memory]

  You: Can you give me an example?
  AI : Sure! For example, you can build a RAG pipeline...
       (notice it understood 'an example' refers to LangChain)
  [4 messages in memory]

  You: exit
  Goodbye!

HINT:
  from langchain.memory import ConversationBufferWindowMemory
  from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
  from langchain_core.output_parsers import StrOutputParser

  memory  = ConversationBufferWindowMemory(k=10, return_messages=True)
  history = memory.load_memory_variables({})["history"]
  memory.save_context({"input": user_msg}, {"output": reply})
"""

import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain.memory import ConversationBufferWindowMemory

load_dotenv()

SYSTEM_PROMPT = """
You are an expert AI assistant for a FastAPI and LangChain development course.
You remember everything discussed in this conversation.
Be concise and technical. Give code examples when helpful.
"""

llm = ChatGroq(
    model       = "llama-3.3-70b-versatile",
    temperature = 0.7,
    max_retries = 3,
)

# ── TASK 1: Create memory ─────────────────────────────────────
memory = None  #  replace


# ── TASK 2: Build prompt template ────────────────────────────
prompt = None  #  replace


# ── TASK 3: Build chain ───────────────────────────────────────
chain = None  #  replace


# ── TASK 4 & 5: Chat loop ─────────────────────────────────────
print("AI Chat Assistant (type 'exit' to quit)")
print("─" * 45)

while True:
    #  Get user input
    user_input = input("\nYou: ").strip()

    #  Check for exit
    if user_input.lower() == "exit":
        print("Goodbye!")
        break

    if not user_input:
        continue

    