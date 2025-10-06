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
- **Finnhub**: [finnhub.io](https://finnhub.io/)
- **Reddit**: [reddit.com/prefs/apps](https://www.reddit.com/prefs/apps) (create app → select "script" → put localhost as redirect)

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

- Works best with earnings from the last month (reddit limitation)
- Finnhub free tier limited to US stocks (still good enough for our use case)
- Reddit data quality varies by ticker popularity (NVDA works well, obscure stocks may have limited discussion)
- In-memory caching (results lost on server restart; would use Redis for production)
- Reddit and Finnhub's APIs have rate limits (60 requests/min, good enough for one user only)

## What could I add more?

If I had more time, I would:
- Replace in-memory cache with Redis for persistence
- Implement caching for yfinance, reddit, and finnhub calls instead of just the final analysis
- Add proper unit tests
- Support custom date ranges (not just since last earnings)
- Add more data sources (Twitter/X, earnings call transcripts, etc.)
- PDF export functionality
- Daily report functionality
- Markdown formatting for results

## Issues faced

### Planning
Because I haven't done any similar projects, I had to research a lot before beginning to code. My first barrier was trying to understand what is the better way to **ground the LLM call with current data**. RAG is too complex (and even unecessary) for this type of application and using APIs like Perplexity may make it too easy (therefore escaping the idea behind actually coding this). In the end I ended up just going for a simple **"context engineering"** idea of including the information in the prompt given to the LLM call.

I also spent a good chunk of time thinking about **what could differentiate this app from just looking at Yahoo Finance**. Because I am taking information directly from Yahoo Finance through `yfinance` (couldn't escape it, it's good!), I decided to go a different route and use informal means of communication to get a good grasp on retail investors' thoughts through Reddit. After implementing it and seeing it work, I reached a very interesting problem: today, Oct 6, **AMD announced a partnership with OpenAI** that made its stock surge a lot. However, due to the way that I filter Reddit posts (requiring a certain amount of upvotes), there wasn't any posts about this partnership, so it wasn't mentioned. I realized that **depending SOLELY on Reddit to get news** (because `yfinance` doesn't allow to get the news that show up in Yahoo Finacne) was definitely not a good idea, so I started also using **Finnhub** to get recent news about the company.

### LLM
Choosing between what provider to use as the 'analysis tool' for this project was definitely not a quantitative challenge. No benchmarks are able to capture this, as it definitely is **"vibes-based"**. In order to choose one, I went to **LMArena** and looked at the Text leaderboard and also used the site to do side by side comparisons between the top 5 models. In the end, I felt like **sonnet 4.5** was the clear winner, with **gemini 2.5 pro** standing at a solid 2nd place for a *much* cheaper price. I also tested sonnet 4.5 in both **thinking** and **non-thinking**, and while thinking showed itself superior, I took the decision that being faster would be better in this use case, so I went with non-thinking.

### Implementation
I first started with a **CLI script** to test if my plan for the app worked. After getting everything running, I refacactored to a webapp (**FastAPI + Next.js**). The choice of Frameworks was solely due to my previous experiences/knowledge on them. Something I hadn't used much before, but decided to do for fun, was doing **websockets** for real-time updates!

WebSocket definitely gave me some trouble. There was a **race condition** problem where analysis would start before the WebSocket connected, so the frontend would miss the first progress updates and jump straight to 60% (because it was only at that point that it was able to connect). Fixed by adding a **500ms delay** after initializing the job status. definitely not the correct solution, but works for this. I think the correct solution is to just wait for the WebSocket to connect to only then start the analysis.

One interesting part of the implementation process was that, in the middle of testing, I **accidentally refreshed my page** while the analysis was running and that showed a big issue. The backend kept processing, but WebSocket disconnected and I lost my result because the job ID wasn't stored anywhere. To fix, I added **job tracking in the localStorage** so the app can resume tracking if someone refreshes. The loading information functionality doesn't work great in these cases, unfortunately.

Another big implementation decision I had to take was related **Reddit's time filtering**. Using `time_filter='month'` gives focused results but misses posts about earnings that were >30 days ago. Using `'year'` gets all posts but can end up being dominated by old viral post. and after filtering for date, I would end up with no posts (even if they did exist). I added implementing **dynamic filtering** based on how old the earnings date, where if its less than 30 days, I use `'month'`, otherwise I use `'year'`. This is not a perfect solution, because it is still possible to end up with no posts when the earnings is old and there are many viral posts in the last year, but I found that it is not a common occurence.

Finally, in the middle of the implementation I added a **history feature** because I wanted to compare past analyses without re-running everything. After each analysis, I just store them in **localStorage**, so no backend persistence.