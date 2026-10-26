"""
 Milestone 07 - Streaming Endpoint
=======================================
GOAL: Add POST /chat/stream that streams tokens as they arrive.

BUILD ON: Milestone 06 solution

TASKS:
  1. Add POST /chat/stream endpoint
  2. Use chain.astream() inside an async generator
  3. Yield each token in SSE format: "data: {token}\n\n"
  4. After stream ends - save full response to DB + run eval
  5. Send final event: "data: [DONE]\n\n"
  6. Return StreamingResponse with media_type="text/event-stream"

TEST WITH CURL:
  curl -N -X POST http://localhost:8000/chat/stream \
    -H "Content-Type: application/json" \
    -d '{"message":"What is RAG?","session_id":"stream-test"}'

EXPECTED:
  data: RAG

  data:  stands

  data:  for

  data:  Retrieval

  ...

  data: [DONE]

HINT:
  from fastapi.responses import StreamingResponse

  @app.post("/chat/stream")
  async def chat_stream(request: ChatRequest):
      async def generate():
          full_response = ""
          async for chunk in chain.astream({...}):
              yield f"data: {chunk}\n\n"
              full_response += chunk
          # save to DB after stream ends
          yield "data: [DONE]\n\n"

      return StreamingResponse(generate(), media_type="text/event-stream")
"""

#  Copy your full M06 solution.py here first
# Then add the streaming endpoint below the existing /chat endpoint

from fastapi.responses import StreamingResponse

#  TASK 1-6: Add streaming endpoint 
#  @app.post("/chat/stream")
#  async def chat_stream(request: ChatRequest):
#        history = load_history(request.session_id)
#
#        async def generate():
#            full_response = ""
#
#            #  async for chunk in chain.astream(...)
#            #     yield f"data: {chunk}\n\n"
#            #     full_response += chunk
#
#            #  Save to DB after stream complete
#            # save_message(...)
#            # save_chat(...)
#
#            #  Run eval in background (don't block stream)
#            # try: eval ...
#
#            #  Send done signal
#            # yield "data: [DONE]\n\n"
#
#        return StreamingResponse(generate(), media_type="text/event-stream")
