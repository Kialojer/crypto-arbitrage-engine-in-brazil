import os
import json
import uvicorn
from fastapi import FastAPI, Depends
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi_clerk_auth import ClerkConfig, ClerkHTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from agent import app as agent_graph


load_dotenv(override=True)

app = FastAPI(
    title="CRYPTO BRL ECHANGE",
    description="API for the LangGraph ReAct Agent (Brazilian Market)",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# تنظیمات Clerk
clerk_config = ClerkConfig(jwks_url=os.getenv("CLERK_JWKS_URL"))
clerk_guard = ClerkHTTPBearer(clerk_config)

# ==========================================
# مدل ورودی (Pydantic)
# ==========================================
class ChatRequest(BaseModel):
    question: str
    thread_id: str 

@app.post("/api/chat")
async def chat_endpoint(
    request: ChatRequest, 
    creds: HTTPAuthorizationCredentials = Depends(clerk_guard)
):
    user_id = creds.decoded["sub"]
    print(f"👤 User {user_id} requested stream...")
    
    initial_state = {
        "messages": [HumanMessage(content=request.question)]
    }
    
    config = {"configurable": {"thread_id": user_id}}

    async def event_stream():
     
        async for event in agent_graph.astream_events(initial_state, config=config, version="v2"):
                
                if event["event"] == "on_chat_model_stream":
                    chunk_text = event["data"]["chunk"].content
                    
                    if chunk_text:
                        yield f"data: {json.dumps({'text': chunk_text})}\n\n"
            
            yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")

if __name__ == "__main__":
    uvicorn.run(app)

