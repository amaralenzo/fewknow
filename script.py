import os
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pathlib import Path
from pydantic import BaseModel, Field
import yfinance as yf
import praw
from anthropic import Anthropic
import instructor
import json
from collections import defaultdict

# Load environment variables from .env file if it exists
def load_env_file():
    """Load environment variables from .env file"""
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

load_env_file()

# ============================================================================
# DATA MODELS (using Pydantic for structured outputs)
# ============================================================================

class SentimentPeriod(BaseModel):
    """Sentiment analysis for a time period"""
    period: str
    sentiment: str  # bullish, bearish, mixed
    confidence: str  # high, medium, low
    key_drivers: List[str]

class Theme(BaseModel):
    """Recurring theme from Reddit discussions"""
    theme: str
    mention_count: int
    sentiment: str
    example_quotes: List[str]

class InsightfulPost(BaseModel):
    """Notable Reddit post with insights"""
    date: str
    content_summary: str
    why_notable: str
    score: int

class RedditAnalysis(BaseModel):
    """Output from LLM Call 1 - Reddit analysis"""
    sentiment_timeline: List[SentimentPeriod]
    top_themes: List[Theme]
    notable_insights: List[InsightfulPost]
    contrarian_takes: List[str]
    worry_vs_optimism: Dict[str, List[str]]
    overall_summary: str

class Event(BaseModel):
    """Timeline event"""
    date: str
    description: str
    source: str

class InsightReport(BaseModel):
    """Final output from LLM Call 2"""
    headline: str
    story: str
    retail_perspective: str
    the_gap: str
    whats_next: str
    key_dates: List[Event]
    sources: List[str]

# ============================================================================
# DATA COLLECTION FUNCTIONS
# ============================================================================

def validate_ticker(ticker: str) -> Optional[Dict]:
    """Validate ticker exists and get basic company info"""
    print(f"🔍 Validating ticker {ticker}...")
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        if not info or 'symbol' not in info:
            print(f"❌ Ticker {ticker} not found")
            return None
            
        company_info = {
            'ticker': ticker.upper(),
            'name': info.get('longName', ticker),
            'sector': info.get('sector', 'Unknown'),
            'industry': info.get('industry', 'Unknown')
        }
        
        print(f"✅ Found: {company_info['name']} ({company_info['sector']})")
        return company_info
        
    except Exception as e:
        print(f"❌ Error validating ticker: {e}")
        return None

def get_earnings_metadata(ticker: str) -> Optional[Dict]:
    """Fetch last earnings date and key metrics"""
    print(f"📊 Fetching earnings metadata...")
    try:
        stock = yf.Ticker(ticker)
        
        # Get earnings dates
        earnings_dates = stock.earnings_dates
        if earnings_dates is None or len(earnings_dates) == 0:
            print("⚠️  No earnings dates found, using alternative method...")
            # Fallback: use calendar
            calendar = stock.calendar
            if calendar is not None and not calendar.empty:
                last_earnings_date = datetime.now() - timedelta(days=90)  # Assume last quarter
            else:
                last_earnings_date = datetime.now() - timedelta(days=90)
        else:
            # Get most recent earnings date
            # Convert to timezone-naive datetime by replacing tzinfo with None
            last_earnings_date = earnings_dates.index[0].to_pydatetime().replace(tzinfo=None)
            now = datetime.now()
            if last_earnings_date > now:
                # If it's a future date, get the second one
                if len(earnings_dates) > 1:
                    last_earnings_date = earnings_dates.index[1].to_pydatetime().replace(tzinfo=None)
        
        # Get earnings history
        earnings = stock.earnings_history
        eps_actual = None
        eps_estimate = None
        
        if earnings is not None and not earnings.empty:
            latest = earnings.iloc[0]
            eps_actual = latest.get('EPS Actual', None)
            eps_estimate = latest.get('EPS Estimate', None)
        
        # Get financial data
        info = stock.info
        revenue = info.get('totalRevenue', 'N/A')
        
        metadata = {
            'date': last_earnings_date.strftime('%Y-%m-%d'),
            'eps_actual': eps_actual,
            'eps_estimate': eps_estimate,
            'revenue': revenue,
            'guidance': info.get('longBusinessSummary', 'No guidance available')[:500]
        }
        
        print(f"✅ Last earnings: {metadata['date']}")
        return metadata
        
    except Exception as e:
        print(f"❌ Error fetching earnings metadata: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def get_sector_etf(sector: str) -> str:
    """Map sector to corresponding ETF"""
    sector_map = {
        'Technology': 'XLK',
        'Financial Services': 'XLF',
        'Healthcare': 'XLV',
        'Consumer Cyclical': 'XLY',
        'Consumer Defensive': 'XLP',
        'Energy': 'XLE',
        'Utilities': 'XLU',
        'Real Estate': 'XLRE',
        'Materials': 'XLB',
        'Industrials': 'XLI',
        'Communication Services': 'XLC',
    }
    return sector_map.get(sector, 'SPY')

def analyze_price_performance(ticker: str, earnings_date: str, sector: str) -> Dict:
    """Analyze price performance since earnings vs benchmarks"""
    print(f"📈 Analyzing price performance since {earnings_date}...")
    
    try:
        start_date = datetime.strptime(earnings_date, '%Y-%m-%d')
        end_date = datetime.now()
        
        # Fetch data for stock and benchmarks
        stock = yf.Ticker(ticker)
        spy = yf.Ticker('SPY')
        sector_etf_ticker = get_sector_etf(sector)
        sector_etf = yf.Ticker(sector_etf_ticker)
        
        # Get historical data
        stock_data = stock.history(start=start_date, end=end_date)
        spy_data = spy.history(start=start_date, end=end_date)
        sector_data = sector_etf.history(start=start_date, end=end_date)
        
        if stock_data.empty:
            print("⚠️  No price data available")
            return {}
        
        # Calculate returns
        stock_return = ((stock_data['Close'].iloc[-1] / stock_data['Close'].iloc[0]) - 1) * 100
        spy_return = ((spy_data['Close'].iloc[-1] / spy_data['Close'].iloc[0]) - 1) * 100
        sector_return = ((sector_data['Close'].iloc[-1] / sector_data['Close'].iloc[0]) - 1) * 100
        
        # Calculate volatility (annualized)
        stock_volatility = stock_data['Close'].pct_change().std() * (252 ** 0.5) * 100
        
        # Calculate max drawdown
        cumulative = (1 + stock_data['Close'].pct_change()).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = ((cumulative - running_max) / running_max) * 100
        max_drawdown = drawdown.min()
        
        performance = {
            'since_earnings': f"{stock_return:.1f}%",
            'vs_sp500': f"{stock_return - spy_return:.1f}%",
            'vs_sector': f"{stock_return - sector_return:.1f}%",
            'sector_etf': sector_etf_ticker,
            'max_drawdown': f"{max_drawdown:.1f}%",
            'current_price': f"${stock_data['Close'].iloc[-1]:.2f}",
            'volatility': 'high' if stock_volatility > 40 else 'medium' if stock_volatility > 25 else 'low',
            'volatility_pct': f"{stock_volatility:.1f}%"
        }
        
        print(f"✅ Performance: {performance['since_earnings']} (vs S&P 500: {performance['vs_sp500']})")
        return performance
        
    except Exception as e:
        print(f"❌ Error analyzing price performance: {e}")
        return {}

def collect_reddit_data(ticker: str, company_name: str, earnings_date: str) -> List[Dict]:
    """Collect Reddit posts and comments about the ticker"""
    print(f"🔍 Collecting Reddit data...")
    
    # Check for Reddit credentials
    if not all([os.getenv('REDDIT_CLIENT_ID'), 
                os.getenv('REDDIT_CLIENT_SECRET'), 
                os.getenv('REDDIT_USER_AGENT')]):
        print("❌ Reddit credentials not found in environment variables.")
        print("   Required: REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT")
        sys.exit(1)
    
    try:
        reddit = praw.Reddit(
            client_id=os.getenv('REDDIT_CLIENT_ID'),
            client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
            user_agent=os.getenv('REDDIT_USER_AGENT')
        )
        
        subreddits = ['wallstreetbets', 'stocks', 'investing']
        all_posts = []
        
        start_date = datetime.strptime(earnings_date, '%Y-%m-%d')
        start_timestamp = start_date.timestamp()
        
        # Search queries
        queries = [f"${ticker}", company_name]
        
        for subreddit_name in subreddits:
            subreddit = reddit.subreddit(subreddit_name)
            
            for query in queries:
                try:
                    # Search posts
                    for submission in subreddit.search(query, time_filter='month', limit=50):
                        # Check if post is after earnings date
                        if submission.created_utc < start_timestamp:
                            continue
                        
                        # Filter by score
                        if submission.score < 10:
                            continue
                        
                        # Skip automod and low-quality posts
                        if 'automod' in submission.author.name.lower():
                            continue
                        
                        post_data = {
                            'type': 'submission',
                            'date': datetime.fromtimestamp(submission.created_utc).strftime('%Y-%m-%d'),
                            'title': submission.title,
                            'text': submission.selftext[:1000],
                            'score': submission.score,
                            'url': f"https://reddit.com{submission.permalink}",
                            'subreddit': subreddit_name
                        }
                        
                        all_posts.append(post_data)
                        
                        # Get top comments
                        submission.comments.replace_more(limit=0)
                        for comment in submission.comments[:5]:
                            if comment.score >= 5 and len(comment.body) > 100:
                                comment_data = {
                                    'type': 'comment',
                                    'date': datetime.fromtimestamp(comment.created_utc).strftime('%Y-%m-%d'),
                                    'title': f"Comment on: {submission.title[:50]}...",
                                    'text': comment.body[:1000],
                                    'score': comment.score,
                                    'url': f"https://reddit.com{submission.permalink}",
                                    'subreddit': subreddit_name
                                }
                                all_posts.append(comment_data)
                                
                except Exception as e:
                    print(f"⚠️  Error searching {subreddit_name} for '{query}': {e}")
                    continue
        
        # Sort by score and limit
        all_posts.sort(key=lambda x: x['score'], reverse=True)
        all_posts = all_posts[:100]
        
        print(f"✅ Collected {len(all_posts)} Reddit posts/comments")
        return all_posts
        
    except Exception as e:
        print(f"❌ Error with Reddit API: {e}")
        sys.exit(1)

# ============================================================================
# LLM ANALYSIS FUNCTIONS
# ============================================================================

def analyze_reddit_with_llm(reddit_posts: List[Dict], ticker: str, earnings_date: str) -> RedditAnalysis:
    """LLM Call 1: Analyze Reddit sentiment and extract themes"""
    print(f"🤖 Analyzing Reddit data with LLM...")
    
    if not os.getenv('ANTHROPIC_API_KEY'):
        print("❌ ANTHROPIC_API_KEY not found in environment variables.")
        sys.exit(1)
    
    try:
        # Initialize Anthropic client with instructor
        client = instructor.from_anthropic(Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY')))
        
        # Prepare posts for context
        posts_text = "\n\n".join([
            f"[{post['date']}] [{post['subreddit']}] Score: {post['score']}\n"
            f"Title: {post['title']}\n"
            f"Content: {post['text'][:500]}..."
            for post in reddit_posts[:50]  # Limit to top 50 to fit context
        ])
        
        prompt = f"""You are analyzing Reddit discussion about {ticker} since their last earnings on {earnings_date}.

Here are {len(reddit_posts)} posts and comments from r/wallstreetbets, r/stocks, and r/investing:

{posts_text}

Extract the following:
1. Sentiment trajectory over time (weekly breakdown if possible)
2. Top 5 recurring themes or concerns mentioned
3. 3-5 most insightful posts (with dates and brief summary)
4. Contrarian or surprising perspectives
5. Comparison: what retail is worried about vs what they're optimistic about

Focus on:
- Detecting sarcasm and irony (common in WSB)
- Grouping similar concerns across different phrasings
- Identifying temporal patterns (sentiment shifts)
- Surfacing quality insights over noise

Output your analysis in the structured format provided."""

        response = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}],
            response_model=RedditAnalysis
        )
        
        print(f"✅ Reddit analysis complete")
        return response
        
    except Exception as e:
        print(f"❌ Error in LLM analysis: {e}")
        sys.exit(1)

def generate_insight_report(
    company_info: Dict,
    earnings_metadata: Dict,
    price_performance: Dict,
    reddit_analysis: RedditAnalysis,
    ticker: str
) -> InsightReport:
    """LLM Call 2: Generate final insight report"""
    print(f"🤖 Generating final insight report...")
    
    if not os.getenv('ANTHROPIC_API_KEY'):
        print("❌ ANTHROPIC_API_KEY not found in environment variables.")
        sys.exit(1)
    
    try:
        client = instructor.from_anthropic(Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY')))
        
        # Prepare structured context
        context = {
            'company': company_info['name'],
            'ticker': ticker,
            'sector': company_info['sector'],
            'last_earnings': earnings_metadata,
            'price_performance': price_performance,
            'reddit_analysis': reddit_analysis.model_dump()
        }
        
        context_json = json.dumps(context, indent=2, default=str)
        
        prompt = f"""You are a financial analyst writing an insight report for {ticker}.

Synthesize the following data to answer: "what actually happened since earnings?"

CONTEXT:
{context_json}

Focus on:
1. Expectation vs reality (what company said vs what happened)
2. Attribution (why did price move this way?)
3. Retail sentiment signals (what is Reddit spotting? Are they right?)
4. Gaps and disconnects (official narrative vs street concerns)
5. Forward-looking (what to watch before next earnings)

Requirements:
- Cite specific dates and sources
- Connect dots between events
- Identify surprises or contrarian signals
- Avoid generic statements
- Be specific about causality
- Make it insightful - surface things not obvious from just looking at Yahoo Finance

Output 4 sections:
1. The Story (narrative of what happened - 2-3 paragraphs)
2. Retail Perspective (what Reddit reveals that you wouldn't know otherwise)
3. The Gap (disconnects between official narrative and reality)
4. What's Next (forward-looking perspective on what to watch)

Also provide a punchy headline and timeline of key events."""

        response = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=8000,
            messages=[{"role": "user", "content": prompt}],
            response_model=InsightReport
        )
        
        print(f"✅ Insight report generated")
        return response
        
    except Exception as e:
        print(f"❌ Error generating report: {e}")
        sys.exit(1)

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def print_report(report: InsightReport):
    """Pretty print the final report"""
    print("\n" + "="*80)
    print("📊 FEWKNOW INSIGHT REPORT")
    print("="*80)
    print(f"\n🎯 {report.headline}")
    print("\n" + "-"*80)
    print("\n📖 THE STORY")
    print("-"*80)
    print(report.story)
    print("\n" + "-"*80)
    print("\n💬 RETAIL PERSPECTIVE")
    print("-"*80)
    print(report.retail_perspective)
    print("\n" + "-"*80)
    print("\n🔍 THE GAP")
    print("-"*80)
    print(report.the_gap)
    print("\n" + "-"*80)
    print("\n🔮 WHAT'S NEXT")
    print("-"*80)
    print(report.whats_next)
    print("\n" + "-"*80)
    print("\n📅 KEY TIMELINE")
    print("-"*80)
    for event in report.key_dates:
        print(f"  • {event.date}: {event.description}")
        print(f"    Source: {event.source}")
    print("\n" + "-"*80)
    print("\n📚 SOURCES")
    print("-"*80)
    for source in report.sources:
        print(f"  • {source}")
    print("\n" + "="*80 + "\n")

def main():
    """Main execution function"""
    print("\n" + "="*80)
    print("🚀 FEWKNOW - Post-Earnings Performance Analyzer")
    print("   'few understand what actually happened since last earnings.'")
    print("="*80 + "\n")
    
    # Get ticker from command line or prompt
    if len(sys.argv) > 1:
        ticker = sys.argv[1].upper()
    else:
        ticker = input("Enter ticker symbol: ").upper()
    
    print(f"\nAnalyzing {ticker}...\n")
    
    # Phase 1: Data Collection
    print("📦 PHASE 1: DATA COLLECTION")
    print("-"*80)
    
    # 1.1 Validate ticker
    company_info = validate_ticker(ticker)
    if not company_info:
        print("❌ Invalid ticker. Exiting.")
        return
    
    # 1.2 Get earnings metadata
    earnings_metadata = get_earnings_metadata(ticker)
    if not earnings_metadata:
        print("❌ Could not fetch earnings data. Exiting.")
        return
    
    # 1.3 Analyze price performance
    price_performance = analyze_price_performance(
        ticker, 
        earnings_metadata['date'], 
        company_info['sector']
    )
    
    # 1.4 Collect Reddit data
    reddit_posts = collect_reddit_data(
        ticker,
        company_info['name'],
        earnings_metadata['date']
    )
    
    if not reddit_posts:
        print("❌ No Reddit data found.")
        sys.exit(1)
    
    # Phase 2: Reddit Analysis
    print("\n🧠 PHASE 2: REDDIT ANALYSIS")
    print("-"*80)
    
    reddit_analysis = analyze_reddit_with_llm(
        reddit_posts,
        ticker,
        earnings_metadata['date']
    )
    
    # Phase 3: Synthesis
    print("\n✨ PHASE 3: INSIGHT SYNTHESIS")
    print("-"*80)
    
    insight_report = generate_insight_report(
        company_info,
        earnings_metadata,
        price_performance,
        reddit_analysis,
        ticker
    )
    
    # Display final report
    print_report(insight_report)
    
    print("✅ Analysis complete!")

if __name__ == "__main__":
    main()
