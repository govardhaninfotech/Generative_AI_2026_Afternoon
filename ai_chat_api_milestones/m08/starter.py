"""
Milestone 08  Request Logging Middleware
=============================================
GOAL: Log every API request to SQLite automatically.
      Add GET /logs to view request history.

BUILD ON: Milestone 07 solution

TASKS:
  1. Add @app.middleware("http") that logs every request to request_logs table:
       endpoint, method, status_code, duration_ms, session_id (from header)
  2. Also write to a rotating log file (app.log)
  3. Add GET /logs endpoint  returns last 20 request logs from DB
  4. Add GET /logs/chat  returns chat logs with eval scores joined

REQUEST_LOGS TABLE (already in init_db from M06):
  id, session_id, endpoint, method, status_code, duration_ms, created_at

EXPECTED GET /logs response:
  {
    "total": 15,
    "items": [
      {"id":1, "endpoint":"/chat", "method":"POST",
       "status_code":200, "duration_ms":832.1, "created_at":"..."},
      ...
    ]
  }

HINT:
  @app.middleware("http")
  async def logging_middleware(request: Request, call_next):
      start    = time.time()
      response = await call_next(request)
      duration = (time.time()-start)*1000
      session_id = request.headers.get("X-Session-ID", "unknown")
      # save to request_logs
      return response

  import logging
  from logging.handlers import RotatingFileHandler
  handler = RotatingFileHandler("app.log", maxBytes=5*1024*1024, backupCount=3)
"""

import logging
from logging.handlers import RotatingFileHandler
from fastapi import Request

#  Setup rotating file logger 
#  Configure logging with RotatingFileHandler
#  log to both terminal (StreamHandler) and file (RotatingFileHandler)
#  format: "%(asctime)s | %(levelname)-8s | %(message)s"


#  Copy full M07 solution here 
#  paste M07 solution.py content here


#  TASK 1 & 2: Add middleware 
#  @app.middleware("http")
#  async def logging_middleware(request: Request, call_next):
#        import uuid
#        req_id   = str(uuid.uuid4())[:8]
#        start    = time.time()
#
#        # Log incoming request
#        # logger.info(f"[{req_id}] -> {request.method} {request.url.path}")
#
#        response = await call_next(request)
#        duration = (time.time()-start)*1000
#
#        # Log outgoing response
#        # logger.info(f"[{req_id}] <- {response.status_code} | {duration:.0f}ms")
#
#        # Save to request_logs table
#        # session_id = request.headers.get("X-Session-ID", "unknown")
#        # save_request_log(...)
#
#        response.headers["X-Request-ID"] = req_id
#        return response


#  TASK 3: GET /logs 
#  @app.get("/logs")
#  def get_logs(limit: int = 20, offset: int = 0):
#        conn = get_connection()
#        rows = conn.execute(
#            "SELECT * FROM request_logs ORDER BY id DESC LIMIT ? OFFSET ?",
#            (limit, offset)
#        ).fetchall()
#        conn.close()
#        return {"total": len(rows), "items": [dict(r) for r in rows]}


#  TASK 4: GET /logs/chat 
#  @app.get("/logs/chat")
#  def get_chat_logs(limit: int = 20, offset: int = 0):
#        # JOIN chat_logs with eval_logs on chat_log_id
#        # Return: session_id, user_message, ai_response,
#        #         duration_ms, overall_score, created_at
#        pass
