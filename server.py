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

# ایمپورت کردن گراف از فایل ایجنت‌ها
from agent import app as agent_graph 

load_dotenv(override=True)

app = FastAPI(
    title="Crypto Autonomous Agent API",
    description="API for the LangGraph ReAct Agent (Brazilian Market)",
    version="1.0.0"
)

# ⚠️ نکته پروداکشن: الان روی "*" است که برای تست عالیه. 
# اما وقتی دیپلوی کردی، باید آدرس دامنه Next.js خودت (مثلا https://myapp.vercel.app) رو اینجا بذاری.
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
    thread_id: str # 🔴 اضافه شد: برای اینکه حافظه چت‌های کاربران قاطی نشه!

# ==========================================
# Endpoint اصلی
# ==========================================
@app.post("/api/chat")
async def chat_endpoint(
    request: ChatRequest, 
    creds: HTTPAuthorizationCredentials = Depends(clerk_guard) # 🔴 اضافه شد: بادیگارد Clerk
):
    """
    Main endpoint to chat with the Autonomous Crypto Agent.
    Requires Clerk Authentication.
    """
    
    # شناسایی دقیق کاربر (برای لاگ‌گیری یا محدود کردن دسترسی)
    user_id = creds.decoded["sub"]
    print(f"👤 User {user_id} is asking a question in thread {request.thread_id}...")
    
    # آماده‌سازی دیتای ورودی
    initial_state = {
        "messages": [HumanMessage(content=request.question)]
    }

    # 🔴 اضافه شد: ساخت شماره پرونده اختصاصی برای این چت تا حافظه LangGraph درست کار کند
    config = {"configurable": {"thread_id": request.thread_id}}

    async def event_stream():
        # ارسال config به گراف برای حفظ حافظه
        async for event in agent_graph.astream_events(initial_state, config=config, version="v2"):
            
            if event["event"] == "on_chat_model_stream":
                chunk_text = event["data"]["chunk"].content
                
                if chunk_text:
                    yield f"data: {json.dumps({'text': chunk_text})}\n\n"
        
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")

if __name__ == "__main__":
    print("🚀 Starting FastAPI server on port 8000...")
    uvicorn.run(app, host="0.0.0.0", port=8000)