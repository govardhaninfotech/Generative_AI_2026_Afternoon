"""
 Milestone 10 - Complete API (History + Eval Summary + Polish)
=================================================================
GOAL: Add the final endpoints and polish the API.
      This is the complete production-ready AI Chat API.

BUILD ON: Milestone 09 solution

TASKS:
  1. GET /chat/history?session_id=xyz
        Returns full conversation history for a session from DB
  2. DELETE /chat/history?session_id=xyz
        Clears conversation memory for a session
  3. GET /eval/summary
        Average eval scores across ALL conversations
        Best and worst performing sessions
  4. Add global exception handler - consistent error format
  5. Add CORS middleware - allow Streamlit frontend to connect
  6. Polish /health - include total chats, total sessions, model name

EXPECTED GET /chat/history:
  {
    "session_id": "test-123",
    "total": 6,
    "messages": [
      {"role": "user",      "content": "What is FastAPI?", "created_at": "..."},
      {"role": "assistant", "content": "FastAPI is...",     "created_at": "..."}
    ]
  }

EXPECTED GET /eval/summary:
  {
    "total_evaluations": 24,
    "avg_relevance"    : 0.87,
    "avg_coherence"    : 0.84,
    "avg_conciseness"  : 0.79,
    "avg_overall"      : 0.83,
    "best_session"     : "session-abc",
    "worst_session"    : "session-xyz"
  }

HINT:
  GET /chat/history:
    SELECT role, content, created_at
    FROM conversation_memory
    WHERE session_id=?
    ORDER BY id

  DELETE /chat/history:
    DELETE FROM conversation_memory WHERE session_id=?

  GET /eval/summary:
    SELECT AVG(relevance), AVG(coherence),
           AVG(conciseness), AVG(overall_score)
    FROM eval_logs

  CORS:
    from fastapi.middleware.cors import CORSMiddleware
    app.add_middleware(CORSMiddleware,
        allow_origins=["http://localhost:8501"],  # Streamlit
        allow_methods=["*"], allow_headers=["*"])

  Global exception handler:
    from fastapi import Request
    from fastapi.responses import JSONResponse

    @app.exception_handler(Exception)
    async def global_handler(request: Request, exc: Exception):
        return JSONResponse(status_code=500,
            content={"success": False, "error": str(exc)})
"""

#  Copy full M09 solution here 
# Then add the tasks below


#  TASK 1: GET /chat/history 
#  @app.get("/chat/history")
#  def get_history(session_id: str, user: str = Depends(verify_api_key)):
#        conn = get_connection()
#        rows = conn.execute(
#            "SELECT role, content, created_at FROM conversation_memory WHERE session_id=? ORDER BY id",
#            (session_id,)
#        ).fetchall()
#        conn.close()
#        return {
#            "session_id": session_id,
#            "total"     : len(rows),
#            "messages"  : [dict(r) for r in rows],
#        }


#  TASK 2: DELETE /chat/history 
#  @app.delete("/chat/history")
#  def clear_history(session_id: str, user: str = Depends(verify_api_key)):
#        conn = get_connection()
#        deleted = conn.execute(
#            "DELETE FROM conversation_memory WHERE session_id=?", (session_id,)
#        ).rowcount
#        conn.commit()
#        conn.close()
#        return {"message": f"Cleared {deleted} messages for session {session_id}"}


#  TASK 3: GET /eval/summary 
#  @app.get("/eval/summary", dependencies=[Depends(verify_api_key)])
#  def eval_summary():
#        conn  = get_connection()
#        stats = conn.execute("""
#            SELECT COUNT(*) as total,
#                   AVG(relevance)     as avg_rel,
#                   AVG(coherence)     as avg_coh,
#                   AVG(conciseness)   as avg_con,
#                   AVG(overall_score) as avg_overall
#            FROM eval_logs
#        """).fetchone()
#
#        # Best session (highest avg overall)
#        best = conn.execute("""
#            SELECT c.session_id, AVG(e.overall_score) as avg_score
#            FROM eval_logs e JOIN chat_logs c ON c.id = e.chat_log_id
#            GROUP BY c.session_id ORDER BY avg_score DESC LIMIT 1
#        """).fetchone()
#
#        # Worst session
#        worst = conn.execute("""
#            SELECT c.session_id, AVG(e.overall_score) as avg_score
#            FROM eval_logs e JOIN chat_logs c ON c.id = e.chat_log_id
#            GROUP BY c.session_id ORDER BY avg_score ASC LIMIT 1
#        """).fetchone()
#
#        conn.close()
#        return {
#            "total_evaluations": stats["total"],
#            "avg_relevance"    : round(stats["avg_rel"]     or 0, 2),
#            "avg_coherence"    : round(stats["avg_coh"]     or 0, 2),
#            "avg_conciseness"  : round(stats["avg_con"]     or 0, 2),
#            "avg_overall"      : round(stats["avg_overall"] or 0, 2),
#            "best_session"     : best["session_id"]  if best  else None,
#            "worst_session"    : worst["session_id"] if worst else None,
#        }


#  TASK 4: Global exception handler 
#  from fastapi.responses import JSONResponse
#  @app.exception_handler(Exception)
#  async def global_handler(request: Request, exc: Exception):
#        logger.error(f"Unhandled error: {exc}")
#        return JSONResponse(
#            status_code=500,
#            content={"success": False, "error": "Internal server error"}
#        )


#  TASK 5: CORS middleware 
#  from fastapi.middleware.cors import CORSMiddleware
#  app.add_middleware(
#        CORSMiddleware,
#        allow_origins    = ["http://localhost:8501"],
#        allow_methods    = ["*"],
#        allow_headers    = ["*"],
#        allow_credentials= True,
#    )


#  TASK 6: Polish /health 
#  Update /health to include:
#    - total_chats    : SELECT COUNT(*) FROM chat_logs
#    - total_sessions : SELECT COUNT(DISTINCT session_id) FROM chat_logs
#    - model          : MODEL
#    - avg_eval_score : SELECT AVG(overall_score) FROM eval_logs
