"""
🏁 Milestone 01 — First LLM Call — SOLUTION
"""

import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

# TASK 1: Load .env
load_dotenv()

# TASK 2: Create LLM object
llm = ChatGroq(
    model       = "llama-3.3-70b-versatile",
    temperature = 0.7,
    max_retries = 3,
)

# TASK 3: Define messages
messages = [
    SystemMessage(content="You are a helpful assistant."),
    HumanMessage(content="What is LangChain in 2 sentences?"),
]

# TASK 4: Call .invoke()
response = llm.invoke(messages)

# TASK 5: Print response
print("LLM Response:")
print(response.content)
print("\nDone!")
