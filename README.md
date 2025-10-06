# FewKnow - Post-Earnings Performance Analyzer

**"few understand what actually happened since last earnings."**

Analyze post-earnings performance by connecting official guidance, actual events, price movements, and retail sentiment (Reddit) to surface insights you can't get from Yahoo Finance.

## Features

- **Earnings Analysis**: Fetches earnings dates, EPS, revenue, and guidance
- **Price Performance**: Compares stock performance vs S&P 500 and sector benchmarks
- **Reddit Sentiment**: Analyzes retail investor discussions from r/wallstreetbets, r/stocks, r/investing
- **AI-Powered Insights**: Uses Claude (Anthropic) to synthesize data and surface non-obvious patterns
- **Timeline View**: Shows what happened week-by-week since earnings

## What Makes This Different

FewKnow surfaces insights you can't get from traditional sources:
- ✅ Connects expectations vs reality
- ✅ Explains "why" not just "what"
- ✅ Identifies what Reddit spotted before Wall Street
- ✅ Highlights gaps between official narratives and reality
- ✅ Provides forward-looking perspective

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up API Keys

Create a `.env` file in the project root:

```bash
# Required: Anthropic API key for LLM analysis
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Optional: Reddit API credentials (uses mock data if not provided)
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
REDDIT_USER_AGENT=FewKnow/1.0
```

**Getting API Keys:**

- **Anthropic API**: Get from [console.anthropic.com](https://console.anthropic.com/)
- **Reddit API** (optional): 
  1. Go to [reddit.com/prefs/apps](https://www.reddit.com/prefs/apps)
  2. Click "create app"
  3. Select "script"
  4. Copy client ID and secret

### 3. Load Environment Variables

The script will automatically look for a `.env` file. Alternatively, export variables:

```bash
export ANTHROPIC_API_KEY="your_key"
export REDDIT_CLIENT_ID="your_id"
export REDDIT_CLIENT_SECRET="your_secret"
export REDDIT_USER_AGENT="FewKnow/1.0"
```

## Example Output

```
================================================================================
📊 FEWKNOW INSIGHT REPORT
================================================================================

🎯 NVDA: Strong Beat Masked Underlying Weakness - Reddit Spotted It First

--------------------------------------------------------------------------------

📖 THE STORY
--------------------------------------------------------------------------------
On the surface, NVDA's latest earnings looked like a home run: 10% EPS beat, 
guidance raised, and an immediate stock rally of 15%. The official narrative 
was simple - strong execution, growing demand, bright future ahead...

--------------------------------------------------------------------------------

💬 RETAIL PERSPECTIVE
--------------------------------------------------------------------------------
Reddit's analysis was surprisingly sophisticated and ahead of the curve. While 
r/wallstreetbets had the expected 'moon mission' posts immediately after 
earnings, the most upvoted comments were actually skeptical...

--------------------------------------------------------------------------------

🔍 THE GAP
--------------------------------------------------------------------------------
The most striking gap is between what the company emphasized (strong beat, 
raised guidance) and what actually mattered (quality of revenue growth, margin 
trends, regulatory risks)...

--------------------------------------------------------------------------------

🔮 WHAT'S NEXT
--------------------------------------------------------------------------------
Three things to watch before next earnings:
1. Regulatory developments - Any news about restrictions...
2. Margin trends - If next quarter shows continued compression...
3. Insider trading activity - More selling would confirm bearish thesis...
```

## How It Works

### Data Flow

1. **Validate Ticker** → Verify ticker exists using yfinance
2. **Fetch Earnings Data** → Get last earnings date, EPS, revenue, guidance
3. **Price Analysis** → Calculate returns vs SPY, sector, volatility, drawdown
4. **Reddit Collection** → Scrape relevant posts/comments from key subreddits
5. **LLM Analysis #1** → Analyze Reddit sentiment, extract themes (Claude)
6. **LLM Analysis #2** → Synthesize all data into insight report (Claude)
7. **Display Report** → Present findings with citations

### Tech Stack

- **yfinance**: Earnings dates and price data
- **praw**: Reddit API wrapper
- **anthropic**: Claude LLM API
- **instructor**: Structured LLM outputs
- **pydantic**: Data validation and schemas

## Mock Mode

If Reddit API credentials are not provided, the script will use mock data to demonstrate functionality. This allows you to test without setting up Reddit API access.

## Limitations

- Requires last earnings to be within ~3 months (yfinance limitation)
- Reddit data quality depends on ticker popularity
- LLM analysis requires Anthropic API credits
- Free tier rate limits may apply

## Success Criteria

A good FewKnow report should:
- ✅ Surface insights you couldn't get from 5 min of Googling
- ✅ Show specific causality (X happened because Y)
- ✅ Reveal what retail sentiment shows
- ✅ Identify gaps between official narrative and reality
- ✅ Make you want to try it with multiple tickers