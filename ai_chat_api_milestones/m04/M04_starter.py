"""
Milestone 04 — Prompt Evaluation
======================================
GOAL: After every LLM reply, automatically score it using a second LLM call.
      Scores: relevance, coherence, conciseness (each 0.0 to 1.0)

BUILD ON: Milestone 03 solution

TASKS:
  1. Create an eval_llm (same model, temperature=0.1 for consistency)
  2. Build an eval prompt that scores a response on 3 dimensions
  3. Build eval_chain that returns a JSON with scores
  4. Create evaluate(question, answer) function that returns EvalResult
  5. After every chat reply — call evaluate() and print scores

EXPECTED OUTPUT:
  You: What is dependency injection?
  AI : Dependency injection is a design pattern where...

   Eval Scores:
     Relevance   : 0.92
     Coherence   : 0.88
     Conciseness : 0.75
     Overall     : 0.85
     Feedback    : Response directly answers the question but could be shorter

     1) get the prompt from the user
     2) hit the llm
     3) parse the output in string
     4) eval the outcome
      - ChatGroq object
      - prompt 
        - system prompt : AI Eval => generate res in given json format
        - User prompt : User Question : ...., AI Response : ....
     - hit the llm
     - disp the eval resp

HINT:
  Use JsonOutputParser to get structured scores
  The eval prompt should include: {question} and {answer}
  Ask the LLM to return ONLY JSON:
  {
    "relevance": 0.0-1.0,
    "coherence": 0.0-1.0,
    "conciseness": 0.0-1.0,
    "feedback": "one sentence"
  }
"""

import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain.memory import ConversationBufferWindowMemory

load_dotenv()

SYSTEM_PROMPT = """
You are an expert AI assistant for a FastAPI and LangChain development course.
You remember everything discussed in this conversation.
Be concise and technical. Give code examples when helpful.
"""

# Main chat LLM
llm = ChatGroq(
    model       = "llama-3.3-70b-versatile",
    temperature = 0.7,
    max_retries = 3,
)

# ── TASK 1: Eval LLM ─────────────────────────────────────────
# Use lower temperature for consistent scoring
#  eval_llm = ChatGroq(model=..., temperature=0.1, max_retries=3)
eval_llm = None  #  replace


# ── TASK 2 & 3: Eval chain ───────────────────────────────────
# Build a chain that takes {question} and {answer}
# Returns JSON with relevance, coherence, conciseness, feedback
#  eval_prompt = ChatPromptTemplate.from_messages([...])
#  eval_chain  = eval_prompt | eval_llm | JsonOutputParser()
eval_chain = None  #  replace


# ── TASK 4: evaluate() function ──────────────────────────────
def evaluate(question: str, answer: str) -> dict:
    """
    Score an LLM response on 3 dimensions.
    Returns: {"relevance": float, "coherence": float,
              "conciseness": float, "overall": float, "feedback": str}
    """
    if eval_chain is None:
        return {}

    try:
        #  Call eval_chain with question and answer
        scores = {}  #  replace with eval_chain.invoke(...)

        #  Calculate overall as average of 3 scores
        overall = 0.0  #  replace

        scores["overall"] = round(overall, 2)
        return scores
    except Exception as e:
        print(f"Eval failed: {e}")
        return {}


# ── Memory + Chat chain (from M03) ────────────────────────────
memory = ConversationBufferWindowMemory(k=10, return_messages=True)
prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{input}"),
])


chain  = prompt | llm | StrOutputParser()

# ── TASK 5: Chat loop with eval ──────────────────────────────
print("AI Chat Assistant with Eval (type 'exit' to quit)")
print("─" * 50)

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

    #  Call evaluate() and print scores
    # scores = evaluate(user_input, reply)
    # if scores:
    #     print(f"\n Eval Scores:")
    #     print(f"   Relevance   : {scores.get('relevance', 0):.2f}")
    #     print(f"   Coherence   : {scores.get('coherence', 0):.2f}")
    #     print(f"   Conciseness : {scores.get('conciseness', 0):.2f}")
    #     print(f"   Overall     : {scores.get('overall', 0):.2f}")
    #     print(f"   Feedback    : {scores.get('feedback', '')}")
