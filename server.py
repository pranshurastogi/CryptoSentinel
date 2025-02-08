from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from contextlib import asynccontextmanager
import json

# Import the ResearchBot and related components
from agent import ResearchBot, AgentState  # Assuming your original code is in research_bot.py

# Create state handler for bot instances
class BotStateManager:
    def __init__(self):
        self.bot_instances = {}

    def get_or_create_bot(self, session_id: str) -> ResearchBot:
        if session_id not in self.bot_instances:
            self.bot_instances[session_id] = ResearchBot()
        return self.bot_instances[session_id]

    def clear_bot(self, session_id: str):
        if session_id in self.bot_instances:
            del self.bot_instances[session_id]

# Initialize state manager
bot_manager = BotStateManager()

# Request models
class QueryRequest(BaseModel):
    query: str
    session_id: str

class TradingDecisionRequest(BaseModel):
    decision: str
    session_id: str

class FollowupRequest(BaseModel):
    question: str
    session_id: str

# Response models
class AnalysisResponse(BaseModel):
    result: str
    has_trading_prompt: bool = False
    error: Optional[str] = None

# Create FastAPI app
app = FastAPI(title="Research Bot API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with your frontend domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/analyze", response_model=AnalysisResponse)
async def analyze_project(request: QueryRequest):
    try:
        bot = bot_manager.get_or_create_bot(request.session_id)
        result = bot.process_initial_query(request.query)
        
        # Check if result contains trading prompt
        has_trading_prompt = "Would you like me to buy this token for you?" in result
        
        return AnalysisResponse(
            result=result,
            has_trading_prompt=has_trading_prompt
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/trading-decision", response_model=AnalysisResponse)
async def process_trading(request: TradingDecisionRequest):
    try:
        bot = bot_manager.get_or_create_bot(request.session_id)
        if not bot.state:
            raise HTTPException(status_code=400, detail="No active analysis session")
            
        result = bot.process_trading_decision(request.decision)
        
        # Clear bot state after trading decision
        bot_manager.clear_bot(request.session_id)
        
        return AnalysisResponse(result=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/followup", response_model=AnalysisResponse)
async def process_followup(request: FollowupRequest):
    try:
        bot = bot_manager.get_or_create_bot(request.session_id)
        if not bot.state:
            raise HTTPException(status_code=400, detail="No active analysis session")
            
        result = bot.process_followup(request.question)
        return AnalysisResponse(result=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/reset")
async def reset_session(request: Dict[str, str]):
    try:
        session_id = request.get("session_id")
        if not session_id:
            raise HTTPException(status_code=400, detail="Session ID required")
            
        bot_manager.clear_bot(session_id)
        return {"status": "success", "message": "Session reset successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)  # Changed from main:app to server:app