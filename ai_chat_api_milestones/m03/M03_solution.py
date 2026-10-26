"""
 Milestone 03 — Memory — SOLUTION
"""

import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
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

# TASK 1: Create memory
memory = ConversationBufferWindowMemory(k=10, return_messages=True)

# TASK 2: Build prompt
prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{input}"),
])

parser = StrOutputParser()

# TASK 3: Build chain
chain = prompt | llm | parser

# TASKS 4 & 5: Chat loop
print(" AI Chat Assistant (type 'exit' to quit)")
print("─" * 45)

while True:
    user_input = input("\nYou: ").strip()

    if user_input.lower() == "exit":
        print("Goodbye!")
        break

    if not user_input:
        continue

    history = memory.load_memory_variables({})["history"]
    reply   = chain.invoke({"input": user_input, "history": history})
    memory.save_context({"input": user_input}, {"output": reply})

    print(f"AI : {reply}")
    print(f"[{len(memory.chat_memory.messages)} messages in memory]")
