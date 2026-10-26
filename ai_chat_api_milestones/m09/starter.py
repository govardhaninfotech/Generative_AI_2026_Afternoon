"""
 Milestone 09 - API Key Authentication
==========================================
GOAL: Secure all endpoints with API key authentication.
      Only requests with a valid X-API-Key header are allowed.

BUILD ON: Milestone 08 solution

TASKS:
  1. Add api_keys table to init_db()
  2. Create hash_key(key) function using hashlib.sha256
  3. Create POST /auth/generate-key endpoint (admin only)
  4. Create verify_api_key(key) function - checks DB
  5. Create @require_api_key decorator using the verify function
  6. Apply @require_api_key to: /chat, /chat/stream, /logs, /logs/chat

ADMIN KEY (from .env):
  ADMIN_API_KEY=admin-secret-change-in-production

TEST:
  # Without key -> 403
  curl -X POST http://localhost:8000/chat \
    -H "Content-Type: application/json" \
    -d '{"message":"hello","session_id":"test"}'

  # Generate a key (using admin key)
  curl -X POST http://localhost:8000/auth/generate-key \
    -H "X-API-Key: admin-secret-change-in-production" \
    -H "Content-Type: application/json" \
    -d '{"user_name":"Raj"}'

  # Use the generated key
  curl -X POST http://localhost:8000/chat \
    -H "X-API-Key: generated-key-here" \
    -H "Content-Type: application/json" \
    -d '{"message":"hello","session_id":"test"}'

HINT:
  import hashlib, secrets

  def hash_key(key: str) -> str:
      return hashlib.sha256(key.encode()).hexdigest()

  def generate_api_key() -> str:
      return secrets.token_urlsafe(32)

  from fastapi import Header, HTTPException
  async def verify_api_key(x_api_key: str = Header(...)):
      hashed = hash_key(x_api_key)
      conn = get_connection()
      row  = conn.execute(
          "SELECT * FROM api_keys WHERE key_hash=? AND is_active=1",
          (hashed,)
      ).fetchone()
      conn.close()
      if not row:
          raise HTTPException(status_code=403, detail="Invalid API key")
      return row["user_name"]
"""

import hashlib, secrets
from fastapi import Header, HTTPException, Depends
from pydantic import BaseModel

#  Copy full M08 solution here 


#  TASK 1: Add api_keys table to init_db 
#  Add this to init_db():
# CREATE TABLE IF NOT EXISTS api_keys (
#     id         INTEGER PRIMARY KEY AUTOINCREMENT,
#     key_hash   TEXT    NOT NULL UNIQUE,
#     user_name  TEXT    NOT NULL,
#     is_active  INTEGER NOT NULL DEFAULT 1,
#     created_at TEXT    DEFAULT (datetime('now'))
# );


#  TASK 2: hash_key() 
def hash_key(key: str) -> str:
    #  Return SHA256 hash of the key
    pass  #  replace


#  TASK 3: POST /auth/generate-key 
class GenerateKeyRequest(BaseModel):
    user_name: str

#  @app.post("/auth/generate-key")
#  def generate_key(request: GenerateKeyRequest,
#                      x_api_key: str = Header(...)):
#        # Check x_api_key == os.getenv("ADMIN_API_KEY")
#        # If not -> raise HTTPException(403, "Admin only")
#        # Generate new key with secrets.token_urlsafe(32)
#        # Hash it and save to api_keys table
#        # Return the raw key to user (only shown once!)
#        pass


#  TASK 4: verify_api_key() 
async def verify_api_key(x_api_key: str = Header(...)) -> str:
    #  Hash the key
    #  Query api_keys WHERE key_hash=? AND is_active=1
    #  If not found -> raise HTTPException(403, "Invalid API key")
    #  Return user_name
    pass  #  replace


#  TASK 5: Apply to endpoints 
#  Add user: str = Depends(verify_api_key) to:
#    - chat_endpoint
#    - chat_stream
#    - get_logs
#    - get_chat_logs
#
# Example:
# @app.post("/chat", response_model=ChatResponse)
# def chat_endpoint(request: ChatRequest,
#                   user: str = Depends(verify_api_key)):  # ← add this
#     ...
