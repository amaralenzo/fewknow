# FewKnow

**"few understand what actually happened since last earnings."**

A web application that analyzes post-earnings stock performance by combining financial data, Reddit sentiment, and AI-powered synthesis to surface insights you won't find only on Yahoo Finance.

## What It Does

Enter a stock ticker and FewKnow generates an insight report that:
- Compares price performance against S&P 500 and sector benchmarks
- Fetches company news articles from the past year (via Finnhub)
- Analyzes retail investor discussions from Reddit (r/wallstreetbets, r/stocks, r/investing)
- Uses dual-LLM pipeline to synthesize official narratives vs. community sentiment
- Identifies gaps between what companies say and what actually happened
- Provides forward-looking perspective on what to watch next

## Quick Start

### 1. Environment Setup

Create a `.env` file in the project root:

```bash
# Required
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Optional (Finnhub for company news and earnings data - falls back gracefully if missing)
FINNHUB_API_KEY=your_finnhub_api_key_here

# Optional (falls back to minimal report without Reddit data)
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
REDDIT_USER_AGENT=FewKnow/1.0
```

Get API keys:
- **Anthropic**: [console.anthropic.com](https://console.anthropic.com/)
- **Finnhub** (optional): [finnhub.io](https://finnhub.io/) (free tier: 60 calls/min, 1 year historical news)
- **Reddit**: [reddit.com/prefs/apps](https://www.reddit.com/prefs/apps) (create app → select "script")

### 2. Install Dependencies

**Backend:**
```bash
cd api
pip install -r requirements.txt
```

**Frontend:**
```bash
cd web
npm install
```

### 3. Run the Application

**Start backend** (from `api/` directory):
```bash
uvicorn server:app --reload --port 8000
```

**Start frontend** (from `web/` directory):
```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) and enter a stock ticker.

## Architecture

**Backend** (FastAPI + Python):
- `core.py`: Data pipeline (yfinance for financials, asyncpraw for Reddit, instructor for structured LLM outputs)
- `server.py`: REST API + WebSocket server for real-time progress updates
- `models.py`: Pydantic schemas for type-safe LLM responses

**Frontend** (Next.js 14 + TypeScript):
- Real-time WebSocket connection for live analysis progress
- LocalStorage-based history to revisit past analyses
- Built with Tailwind CSS and shadcn/ui components

**Analysis Pipeline:**
```
Ticker Input → Validate → Fetch Earnings + Prices → Fetch News Articles → Scrape Reddit → 
LLM Analysis 1 (Reddit Sentiment) → LLM Analysis 2 (Synthesis w/ News) → 
WebSocket Stream → Display Report
```

## Tech Stack

**Backend:**
- FastAPI (REST + WebSocket)
- yfinance (stock data)
- Finnhub (company news & earnings)
- asyncpraw (Reddit API)
- Anthropic Claude (Sonnet 4.5)
- instructor + Pydantic (structured LLM outputs)

**Frontend:**
- Next.js 14 (App Router)
- TypeScript
- Tailwind CSS + shadcn/ui
- WebSocket client

## Limitations

- Works best with earnings from the last 3 months (yfinance limitation)
- Finnhub free tier limited to US stocks (works well for our use case)
- Reddit data quality varies by ticker popularity (NVDA works well, obscure stocks may have limited discussion)
- In-memory caching (results lost on server restart; would use Redis for production)
- Reddit API free tier has rate limits (60 requests/min)

## What could I add more?

If I had more time, I would:
- Replace in-memory cache with Redis for persistence
- Add retry logic for Reddit API rate limits
- Implement caching for expensive yfinance calls
- Add proper unit tests
- Support custom date ranges (not just since last earnings)
- Add more data sources (Twitter/X, earnings call transcripts, etc.)
- PDF export functionality
- Daily report functionality
- Markdown formatting for results