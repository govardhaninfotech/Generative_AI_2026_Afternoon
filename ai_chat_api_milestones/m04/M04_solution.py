"""
Milestone 04 - Prompt Evaluation - SOLUTION
"""

import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_classic.memory import ConversationBufferWindowMemory

load_dotenv()

SYSTEM_PROMPT = """
You are an expert AI assistant for a FastAPI and LangChain development course.
You remember everything discussed in this conversation.
Be concise and technical. Give code examples when helpful.
"""

llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.7, max_retries=3)

# TASK 1: Eval LLM
eval_llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.1, max_retries=3)

# TASKS 2 & 3: Eval chain
EVAL_SYSTEM = """
You are an expert evaluator of AI responses.
Score the given response on three dimensions.
Return ONLY a JSON object - no markdown, no explanation.
"""

EVAL_HUMAN = """
Question : {question}
Response : {answer}

Score each dimension from 0.0 to 1.0:
  relevance   : Does the response directly answer the question?
  coherence   : Is the response well-structured and logical?
  conciseness : Is the response appropriately brief without missing key points?
  feedback    : One sentence explaining the main strength or weakness.

Return ONLY this JSON:
{{"relevance": 0.0, "coherence": 0.0, "conciseness": 0.0, "feedback": "..."}}
"""

eval_prompt = ChatPromptTemplate.from_messages([
    ("system", EVAL_SYSTEM),
    ("human",  EVAL_HUMAN),
])

eval_chain = eval_prompt | eval_llm | JsonOutputParser()

# TASK 4: evaluate() function
def evaluate(question: str, answer: str) -> dict:
    try:
        scores  = eval_chain.invoke({"question": question, "answer": answer})
        overall = round((
            scores.get("relevance",   0) +
            scores.get("coherence",   0) +
            scores.get("conciseness", 0)
        ) / 3, 2)
        scores["overall"] = overall
        return scores
    except Exception as e:
        print(f"Eval failed: {e}")
        return {}

# Memory + chain
memory = ConversationBufferWindowMemory(k=10, return_messages=True)
prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    MessagesPlaceholder(variable_name="history"),
    ("human",  "{input}"),
])
chain  = prompt | llm | StrOutputParser()

# TASK 5: Chat loop with eval
print("AI Chat Assistant with Eval (type 'exit' to quit)")
print("-" * 50)

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

    scores = evaluate(user_input, reply)
    if scores:
        print(f"\n Eval Scores:")
        print(f"   Relevance   : {scores.get('relevance',   0):.2f}")
        print(f"   Coherence   : {scores.get('coherence',   0):.2f}")
        print(f"   Conciseness : {scores.get('conciseness', 0):.2f}")
        print(f"   Overall     : {scores.get('overall',     0):.2f}")
        print(f"   Feedback    : {scores.get('feedback', '')}")
