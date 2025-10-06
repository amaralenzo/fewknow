"""
FastAPI backend for FewKnow web application.
Provides REST API endpoints and WebSocket for real-time analysis updates.
"""

import os
from typing import Optional, Dict
from datetime import datetime
from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uuid
import logging
import json
import asyncio

# Import from local modules (absolute imports since this is the entry point)
from core import (
    validate_ticker,
    get_earnings_metadata,
    analyze_price_performance,
    collect_reddit_data,
    collect_news_articles,
    analyze_reddit_with_llm,
    generate_insight_report,
    load_env_file,
)
from models import RedditAnalysis, InsightReport

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_env_file()

# Initialize FastAPI app
app = FastAPI(
    title="FewKnow API",
    description="Post-earnings performance analysis API",
    version="1.0.0"
)

# CORS middleware to allow Next.js frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for analysis results (in production, use Redis or database)
# Each entry: {job_id: {"result": data, "expires_at": datetime}}
analysis_cache = {}
analysis_status = {}

# Cache expiration settings
CACHE_TTL_HOURS = 24  # Results expire after 24 hours

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, job_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[job_id] = websocket
        logger.info(f"WebSocket connected for job {job_id}")

    def disconnect(self, job_id: str):
        if job_id in self.active_connections:
            del self.active_connections[job_id]
            logger.info(f"WebSocket disconnected for job {job_id}")

    async def send_update(self, job_id: str, message: dict):
        if job_id in self.active_connections:
            try:
                await self.active_connections[job_id].send_json(message)
            except Exception as e:
                logger.error(f"Error sending to WebSocket {job_id}: {e}")
                self.disconnect(job_id)

manager = ConnectionManager()

# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class AnalysisRequest(BaseModel):
    ticker: str

class AnalysisStatus(BaseModel):
    job_id: str
    status: str  # "pending", "processing", "completed", "failed"
    progress: str
    message: Optional[str] = None

class AnalysisResponse(BaseModel):
    job_id: str
    status: str
    ticker: str
    company_info: Optional[dict] = None
    earnings_metadata: Optional[dict] = None
    price_performance: Optional[dict] = None
    reddit_analysis: Optional[dict] = None
    insight_report: Optional[dict] = None
    error: Optional[str] = None

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def cleanup_expired_cache():
    """Remove expired entries from cache"""
    now = datetime.now()
    expired_jobs = []
    
    # Find expired entries
    for job_id, entry in analysis_cache.items():
        if isinstance(entry, dict) and "expires_at" in entry:
            if entry["expires_at"] < now:
                expired_jobs.append(job_id)
    
    # Remove expired entries
    for job_id in expired_jobs:
        logger.info(f"Removing expired cache entry for job {job_id}")
        analysis_cache.pop(job_id, None)
        analysis_status.pop(job_id, None)
    
    if expired_jobs:
        logger.info(f"Cleaned up {len(expired_jobs)} expired cache entries")

async def update_status(job_id: str, status: str, progress: str, message: str = None):
    """Update analysis status and send to WebSocket if connected"""
    status_update = {
        "job_id": job_id,
        "status": status,
        "progress": progress,
        "message": message,
        "updated_at": datetime.now().isoformat()
    }
    analysis_status[job_id] = status_update
    logger.info(f"Job {job_id}: {progress} - {message}")
    
    # Send update via WebSocket
    await manager.send_update(job_id, {
        "type": "status",
        "data": status_update
    })

async def run_analysis(job_id: str, ticker: str):
    """Run the full analysis pipeline asynchronously"""
    try:
        # Initialize status immediately
        await update_status(job_id, "processing", "0%", "Starting analysis...")
        
        # Initialize result
        result = {
            "job_id": job_id,
            "status": "processing",
            "ticker": ticker
        }
        
        # Step 1: Validate ticker
        await update_status(job_id, "processing", "10%", "Validating ticker...")
        company_info = validate_ticker(ticker)
        if not company_info:
            raise ValueError(f"Invalid ticker: {ticker}")
        result["company_info"] = company_info
        
        # Step 2: Get earnings metadata
        await update_status(job_id, "processing", "25%", "Fetching earnings data...")
        earnings_metadata = get_earnings_metadata(ticker)
        if not earnings_metadata:
            raise ValueError("Could not fetch earnings data")
        result["earnings_metadata"] = earnings_metadata
        
        # Step 3: Analyze price performance
        await update_status(job_id, "processing", "35%", "Analyzing price performance...")
        price_performance = analyze_price_performance(
            ticker,
            earnings_metadata['date'],
            company_info['sector']
        )
        result["price_performance"] = price_performance
        
        # Step 4: Collect news articles
        await update_status(job_id, "processing", "45%", "Fetching recent news...")
        news_articles = collect_news_articles(
            ticker,
            company_info['name'],
            earnings_metadata['date']
        )
        result["news_articles"] = news_articles
        
        # Step 5: Collect Reddit data
        await update_status(job_id, "processing", "60%", "Collecting Reddit discussions...")
        reddit_posts = await collect_reddit_data(
            ticker,
            company_info['name'],
            earnings_metadata['date']
        )
        
        # Continue even if no Reddit data (instead of failing)
        if not reddit_posts:
            logger.warning(f"No Reddit data found for {ticker}, skipping sentiment analysis")
            result["reddit_analysis"] = None
            result["insight_report"] = None
            
            # Generate a simple report without Reddit data
            await update_status(job_id, "processing", "90%", "Finalizing report...")
            
            # Create minimal insight report
            from models import InsightReport, Event
            
            # Build story with news if available
            story_parts = [
                f"Price performance analysis for {company_info['name']} since earnings on {earnings_metadata['date']}. ",
                f"Stock has moved {price_performance.get('since_earnings', 'N/A')} since last earnings report."
            ]
            
            if news_articles and len(news_articles) > 0:
                story_parts.append(f" {len(news_articles)} news articles were published during this period, providing context for market movements.")
                sources = ["Yahoo Finance", "yfinance API", "NewsAPI"]
            else:
                story_parts.append(" No Reddit discussion data was available for this ticker during the analysis period.")
                sources = ["Yahoo Finance", "yfinance API"]
            
            minimal_report = InsightReport(
                headline=f"{ticker}: Analysis Complete (Limited Data Available)",
                story="".join(story_parts),
                retail_perspective="No retail investor discussion data available for this period.",
                the_gap="Insufficient data to identify gaps between official narrative and retail sentiment.",
                whats_next=f"Monitor upcoming earnings reports and price action relative to sector performance ({price_performance.get('sector_etf', 'N/A')}).",
                key_dates=[
                    Event(
                        date=earnings_metadata['date'],
                        description="Last earnings report",
                        source="Yahoo Finance"
                    )
                ],
                sources=sources
            )
            result["insight_report"] = minimal_report.model_dump()
        else:
            # Step 6: Analyze Reddit with LLM
            await update_status(job_id, "processing", "75%", "Analyzing sentiment with AI...")
            reddit_analysis = analyze_reddit_with_llm(
                reddit_posts,
                ticker,
                earnings_metadata['date']
            )
            result["reddit_analysis"] = reddit_analysis.model_dump()
            
            # Step 7: Generate insight report (with news articles if available)
            await update_status(job_id, "processing", "85%", "Generating insights...")
            insight_report = generate_insight_report(
                company_info,
                earnings_metadata,
                price_performance,
                reddit_analysis,
                ticker,
                news_articles=news_articles if news_articles else None
            )
            result["insight_report"] = insight_report.model_dump()
        
        # Complete
        result["status"] = "completed"
        
        # Store with expiration timestamp
        from datetime import timedelta
        analysis_cache[job_id] = {
            "result": result,
            "expires_at": datetime.now() + timedelta(hours=CACHE_TTL_HOURS)
        }
        
        await update_status(job_id, "completed", "100%", "Analysis complete!")
        
        # Send final result via WebSocket
        await manager.send_update(job_id, {
            "type": "result",
            "data": result
        })
        
    except Exception as e:
        # Catch all exceptions
        error_msg = str(e) if str(e) else f"{type(e).__name__} occurred"
        logger.error(f"Analysis failed for job {job_id}: {error_msg}", exc_info=True)
        
        result = {
            "job_id": job_id,
            "status": "failed",
            "ticker": ticker,
            "error": error_msg
        }
        
        # Store failed results with expiration (shorter TTL for failures)
        from datetime import timedelta
        analysis_cache[job_id] = {
            "result": result,
            "expires_at": datetime.now() + timedelta(hours=1)  # Failed results expire faster
        }
        
        await update_status(job_id, "failed", "0%", f"Error: {error_msg}")
        
        # Send error via WebSocket
        await manager.send_update(job_id, {
            "type": "error",
            "data": {"error": error_msg}
        })

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "FewKnow API",
        "status": "running",
        "version": "1.0.0"
    }

@app.post("/api/analyze", response_model=AnalysisStatus)
async def start_analysis(request: AnalysisRequest, background_tasks: BackgroundTasks):
    """
    Start a new analysis job for a ticker.
    Returns a job ID to track progress.
    """
    ticker = request.ticker.upper().strip()
    
    if not ticker:
        raise HTTPException(status_code=400, detail="Ticker is required")
    
    # Cleanup expired cache entries before starting new job
    cleanup_expired_cache()
    
    # Generate unique job ID
    job_id = str(uuid.uuid4())
    
    # Initialize status
    await update_status(job_id, "pending", "0%", "Analysis queued...")
    
    # Start background task
    background_tasks.add_task(run_analysis, job_id, ticker)
    
    return AnalysisStatus(
        job_id=job_id,
        status="pending",
        progress="0%",
        message="Analysis started"
    )

@app.get("/api/status/{job_id}", response_model=AnalysisStatus)
async def get_status(job_id: str):
    """
    Get the status of an analysis job.
    """
    if job_id not in analysis_status:
        raise HTTPException(status_code=404, detail="Job not found")
    
    status = analysis_status[job_id]
    return AnalysisStatus(**status)

@app.get("/api/result/{job_id}", response_model=AnalysisResponse)
async def get_result(job_id: str):
    """
    Get the full results of a completed analysis.
    """
    if job_id not in analysis_cache:
        raise HTTPException(status_code=404, detail="Results not found or expired")
    
    entry = analysis_cache[job_id]
    
    # Check if expired
    if isinstance(entry, dict) and "expires_at" in entry:
        if entry["expires_at"] < datetime.now():
            # Remove expired entry
            analysis_cache.pop(job_id, None)
            analysis_status.pop(job_id, None)
            raise HTTPException(status_code=404, detail="Results expired")
        result = entry["result"]
    else:
        # Legacy format (backward compatibility)
        result = entry
    
    return AnalysisResponse(**result)

@app.get("/api/validate/{ticker}")
async def validate_ticker_endpoint(ticker: str):
    """
    Quick validation endpoint to check if a ticker exists.
    """
    ticker = ticker.upper().strip()
    company_info = validate_ticker(ticker)
    
    if not company_info:
        raise HTTPException(status_code=404, detail=f"Ticker {ticker} not found")
    
    return {
        "valid": True,
        "ticker": ticker,
        "company_info": company_info
    }

@app.websocket("/ws/{job_id}")
async def websocket_endpoint(websocket: WebSocket, job_id: str):
    """
    WebSocket endpoint for real-time analysis updates.
    Client connects with job_id and receives status updates in real-time.
    """
    await manager.connect(job_id, websocket)
    
    try:
        # Send current status if available
        if job_id in analysis_status:
            await websocket.send_json({
                "type": "status",
                "data": analysis_status[job_id]
            })
        
        # Send result if already completed
        if job_id in analysis_cache:
            entry = analysis_cache[job_id]
            # Extract result from new format or use legacy format
            result = entry["result"] if isinstance(entry, dict) and "result" in entry else entry
            await websocket.send_json({
                "type": "result",
                "data": result
            })
        
        # Keep connection alive and handle any client messages
        while True:
            try:
                # Wait for any message from client (like ping/pong)
                data = await websocket.receive_text()
                # Echo back to keep connection alive
                await websocket.send_json({"type": "pong"})
            except WebSocketDisconnect:
                break
            
    except Exception as e:
        logger.error(f"WebSocket error for job {job_id}: {e}")
    finally:
        manager.disconnect(job_id)

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", "8000"))
    
    print(f"""
    ================================================================================
    🚀 FewKnow API Server
    ================================================================================
    Server running on: http://localhost:{port}
    API Documentation: http://localhost:{port}/docs
    Health Check: http://localhost:{port}/
    ================================================================================
    """)
    
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )
