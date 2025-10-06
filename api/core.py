"""
Core analysis logic for FewKnow.
Clean, reusable functions without CLI dependencies.
"""

import os
from datetime import datetime, timedelta
from typing import List, Dict
from pathlib import Path
import yfinance as yf
import asyncpraw
from asyncpraw.models.comment_forest import MoreComments
from anthropic import Anthropic
import instructor
import json
import logging
import requests

from models import RedditAnalysis, InsightReport

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# ENVIRONMENT SETUP
# ============================================================================

def load_env_file():
    """Load environment variables from .env file"""
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()


# ============================================================================
# DATA COLLECTION FUNCTIONS
# ============================================================================

def validate_ticker(ticker: str) -> Dict:
    """
    Validate ticker exists and get basic company info.
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        Dictionary with company info
        
    Raises:
        ValueError: If ticker is invalid or not found
        Exception: If critical error occurs during validation
    """
    logger.info(f"Validating ticker {ticker}...")
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        if not info or 'symbol' not in info:
            logger.warning(f"Ticker {ticker} not found")
            raise ValueError(f"Ticker '{ticker}' not found or invalid")
            
        company_info = {
            'ticker': ticker.upper(),
            'name': info.get('longName', ticker),
            'sector': info.get('sector', 'Unknown'),
            'industry': info.get('industry', 'Unknown')
        }
        
        logger.info(f"Found: {company_info['name']} ({company_info['sector']})")
        return company_info
        
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Error validating ticker: {e}")
        raise


def get_earnings_metadata(ticker: str) -> Dict:
    """
    Fetch last earnings date and key metrics.
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        Dictionary with earnings metadata
        
    Raises:
        Exception: If critical error occurs during data fetch
    """
    logger.info(f"Fetching earnings metadata for {ticker}...")
    try:
        stock = yf.Ticker(ticker)
        
        # Get earnings dates
        earnings_dates = stock.earnings_dates
        if earnings_dates is None or len(earnings_dates) == 0:
            logger.warning("No earnings dates found, using alternative method...")
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
        
        logger.info(f"Last earnings: {metadata['date']}")
        return metadata
        
    except Exception as e:
        logger.error(f"Error fetching earnings metadata: {e}")
        raise


def get_sector_etf(sector: str) -> str:
    """Map sector to corresponding ETF ticker"""
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
    """
    Analyze price performance since earnings vs benchmarks.
    
    Args:
        ticker: Stock ticker symbol
        earnings_date: Last earnings date (YYYY-MM-DD format)
        sector: Company sector
        
    Returns:
        Dictionary with performance metrics
        
    Raises:
        ValueError: If no price data is available
        Exception: If critical error occurs during analysis
    """
    logger.info(f"Analyzing price performance since {earnings_date}...")
    
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
            logger.warning("No price data available")
            raise ValueError(f"No price data available for {ticker} since {earnings_date}")
        
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
        
        logger.info(f"Performance: {performance['since_earnings']} (vs S&P 500: {performance['vs_sp500']})")
        return performance
        
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Error analyzing price performance: {e}")
        raise


def collect_news_articles(ticker: str, company_name: str, earnings_date: str) -> List[Dict]:
    """
    Collect news articles about the company since earnings using Finnhub.
    
    Args:
        ticker: Stock ticker symbol
        company_name: Full company name
        earnings_date: Last earnings date (YYYY-MM-DD format)
        
    Returns:
        List of news articles with headline, description, source, date, URL
        
    Raises:
        ValueError: If Finnhub API key is missing
        Exception: If API call fails
    """
    logger.info(f"Collecting news articles for {ticker}...")
    
    api_key = os.getenv('FINNHUB_API_KEY')
    if not api_key:
        logger.warning("FINNHUB_API_KEY not found, skipping news collection")
        return []
    
    try:
        # Parse earnings date
        start_date = datetime.strptime(earnings_date, '%Y-%m-%d')
        end_date = datetime.now()
        
        # Finnhub company-news endpoint
        # Free tier supports 1 year of historical news
        url = "https://finnhub.io/api/v1/company-news"
        
        params = {
            'symbol': ticker.upper(),
            'from': start_date.strftime('%Y-%m-%d'),
            'to': end_date.strftime('%Y-%m-%d'),
            'token': api_key
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Finnhub returns array directly (not wrapped in status object)
        if not isinstance(data, list):
            logger.error(f"Unexpected Finnhub response format: {type(data)}")
            return []
        
        articles = []
        for item in data:
            # Finnhub returns: category, datetime (unix timestamp), headline, id, image, related, source, summary, url
            headline = item.get('headline', '')
            summary = item.get('summary', '')
            
            # Skip articles without headline or summary
            if not headline or not summary:
                continue
            
            # Convert unix timestamp to datetime
            timestamp = item.get('datetime', 0)
            article_date = datetime.fromtimestamp(timestamp) if timestamp else datetime.now()
            
            articles.append({
                'title': headline,
                'description': summary[:500],  # Limit summary length
                'source': item.get('source', 'Unknown'),
                'date': article_date.strftime('%Y-%m-%d'),
                'url': item.get('url', ''),
                'author': item.get('source', 'Unknown')  # Finnhub doesn't provide author, use source
            })
        
        logger.info(f"Found {len(articles)} news articles for {ticker}")
        return articles
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching news from Finnhub: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error collecting news: {e}")
        return []
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching news from NewsAPI: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error collecting news: {e}")
        return []


async def _load_submission_comments(submission) -> None:
    """
    Helper to load comments for a submission.
    Handles errors gracefully and returns None if loading fails.
    """
    if not hasattr(submission, 'comments'):
        return None
    
    comments_forest = submission.comments
    
    if getattr(comments_forest, "_comments", None) is None:
        try:
            await submission.load()
        except Exception as load_error:
            logger.debug(f"Unable to load comments for {submission.id}: {load_error}")
            return None
        comments_forest = submission.comments
    
    if getattr(comments_forest, "_comments", None) is None:
        return None
    
    return comments_forest


async def _extract_quality_comments(submission, subreddit_name: str, max_comments: int = 5) -> List[Dict]:
    """
    Extract quality comments from a submission using BFS traversal.
    
    Args:
        submission: Reddit submission object
        subreddit_name: Name of the subreddit
        max_comments: Maximum number of comments to extract
        
    Returns:
        List of comment data dictionaries
    """
    comments_forest = await _load_submission_comments(submission)
    if not comments_forest:
        return []
    
    try:
        await comments_forest.replace_more(limit=0)
    except Exception as e:
        logger.debug(f"Error replacing MoreComments for {submission.id}: {e}")
        return []
    
    quality_comments = []
    comment_queue = list(getattr(comments_forest, "_comments", []) or [])
    
    while comment_queue and len(quality_comments) < max_comments:
        comment = comment_queue.pop(0)
        
        # Skip MoreComments objects
        if isinstance(comment, MoreComments):
            continue
        
        # Get comment attributes safely
        body = getattr(comment, "body", None)
        score = getattr(comment, "score", 0)
        created_utc = getattr(comment, "created_utc", None)
        
        # Filter low-quality comments
        if not body or score < 5 or len(body) <= 100:
            # Still queue up replies for potential higher-quality nested comments
            replies_forest = getattr(comment, "replies", None)
            if replies_forest and getattr(replies_forest, "_comments", None):
                comment_queue.extend(replies_forest._comments)
            continue
        
        # Add quality comment
        comment_data = {
            'type': 'comment',
            'date': datetime.fromtimestamp(created_utc).strftime('%Y-%m-%d') if created_utc else 'unknown',
            'title': f"Comment on: {submission.title[:50]}...",
            'text': body[:1000],
            'score': score,
            'url': f"https://reddit.com{submission.permalink}",
            'subreddit': subreddit_name
        }
        quality_comments.append(comment_data)
        
        # Queue up replies for BFS traversal
        replies_forest = getattr(comment, "replies", None)
        if replies_forest and getattr(replies_forest, "_comments", None):
            comment_queue.extend(replies_forest._comments)
    
    return quality_comments


async def collect_reddit_data(ticker: str, company_name: str, earnings_date: str) -> List[Dict]:
    """
    Collect Reddit posts and comments about the ticker.
    
    Args:
        ticker: Stock ticker symbol
        company_name: Full company name
        earnings_date: Last earnings date (YYYY-MM-DD format)
        
    Returns:
        List of Reddit posts/comments
        
    Raises:
        ValueError: If Reddit credentials are missing
        Exception: If Reddit API fails
    """
    logger.info(f"Collecting Reddit data for {ticker}...")
    
    # Check for Reddit credentials
    if not all([os.getenv('REDDIT_CLIENT_ID'), 
                os.getenv('REDDIT_CLIENT_SECRET'), 
                os.getenv('REDDIT_USER_AGENT')]):
        raise ValueError("Reddit credentials not found in environment variables. "
                        "Required: REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT")
    
    try:
        reddit = asyncpraw.Reddit(
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
        
        # Collect submissions first (fast), then process comments only for top posts
        submissions_to_process = []
        
        for subreddit_name in subreddits:
            subreddit = await reddit.subreddit(subreddit_name)
            
            for query in queries:
                try:
                    # Search posts
                    search_results = subreddit.search(query, time_filter='month', limit=50)
                    
                    if search_results is None:
                        logger.warning(f"No search results for '{query}' in {subreddit_name}")
                        continue
                    
                    async for submission in search_results:
                        # Check if post is after earnings date
                        if submission.created_utc < start_timestamp:
                            continue
                        
                        # Filter by score
                        if submission.score < 10:
                            continue
                        
                        # Skip automod and low-quality posts
                        if submission.author is None or 'automod' in submission.author.name.lower():
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
                        submissions_to_process.append((submission, subreddit_name))
                                
                except Exception as e:
                    logger.warning(f"Error searching {subreddit_name} for '{query}': {e}")
                    continue
        
        # Now process comments only for top submissions (by score)
        # Sort submissions by score and take top 30 to extract comments from
        submissions_to_process.sort(key=lambda x: x[0].score, reverse=True)
        top_submissions = submissions_to_process[:30]
        
        logger.info(f"Processing comments from top {len(top_submissions)} submissions...")
        
        for submission, subreddit_name in top_submissions:
            comments = await _extract_quality_comments(submission, subreddit_name, max_comments=5)
            all_posts.extend(comments)
        
        # Sort by score and limit
        all_posts.sort(key=lambda x: x['score'], reverse=True)
        all_posts = all_posts[:100]
        
        logger.info(f"Collected {len(all_posts)} Reddit posts/comments")
        
        # Close the Reddit session
        await reddit.close()
        
        # If no posts found, return empty list instead of raising error
        if not all_posts:
            logger.warning(f"No Reddit posts found for {ticker}")
            return []
        
        return all_posts
        
    except Exception as e:
        logger.error(f"Error with Reddit API: {e}")
        try:
            await reddit.close()
        except:
            pass
        raise


# ============================================================================
# LLM ANALYSIS FUNCTIONS
# ============================================================================

def analyze_reddit_with_llm(reddit_posts: List[Dict], ticker: str, earnings_date: str) -> RedditAnalysis:
    """
    Analyze Reddit sentiment and extract themes using LLM.
    
    Args:
        reddit_posts: List of Reddit posts/comments
        ticker: Stock ticker symbol
        earnings_date: Last earnings date
        
    Returns:
        RedditAnalysis object with structured sentiment data
        
    Raises:
        ValueError: If ANTHROPIC_API_KEY is missing
        Exception: If LLM call fails
    """
    logger.info(f"Analyzing Reddit data with LLM...")
    
    if not os.getenv('ANTHROPIC_API_KEY'):
        raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
    
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
        
        logger.info(f"Reddit analysis complete")
        return response
        
    except Exception as e:
        logger.error(f"Error in LLM analysis: {e}")
        raise


def generate_insight_report(
    company_info: Dict,
    earnings_metadata: Dict,
    price_performance: Dict,
    reddit_analysis: RedditAnalysis,
    ticker: str,
    news_articles: List[Dict] = None
) -> InsightReport:
    """
    Generate final insight report using LLM.
    
    Args:
        company_info: Company information dictionary
        earnings_metadata: Earnings data
        price_performance: Price performance metrics
        reddit_analysis: Reddit sentiment analysis
        ticker: Stock ticker symbol
        news_articles: Optional list of news articles from NewsAPI
        
    Returns:
        InsightReport object with final analysis
        
    Raises:
        ValueError: If ANTHROPIC_API_KEY is missing
        Exception: If LLM call fails
    """
    logger.info(f"Generating final insight report...")
    
    if not os.getenv('ANTHROPIC_API_KEY'):
        raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
    
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
        
        # Add news articles if available (limit to most recent 30 to avoid token overflow)
        if news_articles:
            # Sort by date (most recent first) and take top 30
            sorted_news = sorted(news_articles, key=lambda x: x.get('date', ''), reverse=True)
            context['news_articles'] = sorted_news[:30]
            context['news_articles_count'] = len(news_articles)  # Include total count for context
        
        context_json = json.dumps(context, indent=2, default=str)
        
        # Build prompt with conditional news section
        news_instruction = ""
        if news_articles and len(news_articles) > 0:
            news_count = len(news_articles)
            included_count = min(30, news_count)
            news_instruction = f"""
IMPORTANT: You have access to {included_count} of the most recent news articles (out of {news_count} total) published since earnings.
Use these to:
- Verify what Reddit discussions were referencing
- Identify official company announcements vs speculation
- Find events that explain price movements
- Cross-reference official narrative with community reaction
- Build a timeline of significant events
"""
        
        prompt = f"""You are a financial analyst writing an insight report for {ticker}.

Synthesize the following data to answer: "what actually happened since earnings?"

CONTEXT:
{context_json}
{news_instruction}

Focus on:
1. Expectation vs reality (what company said vs what happened)
2. Attribution (why did price move this way?)
3. News events and their impact (if news data available)
4. Retail sentiment signals (what is Reddit spotting? Are they right?)
5. Gaps and disconnects (official narrative vs street concerns vs actual news)
6. Forward-looking (what to watch before next earnings)

Requirements:
- Cite specific dates and sources
- Connect dots between news events, price movements, and sentiment
- Identify surprises or contrarian signals
- Avoid generic statements
- Be specific about causality
- Make it insightful - surface things not obvious from just looking at Yahoo Finance
- Structure lists with simple dashes or numbers

Output 4 sections:
1. The Story (narrative of what happened - 2-3 paragraphs)
2. Retail Perspective (what Reddit reveals that you wouldn't know otherwise)
3. The Gap (disconnects between official narrative, news events, and reality)
4. What's Next (forward-looking perspective on what to watch)

Also provide a punchy headline and timeline of key events."""

        response = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=16000,  # Increased for comprehensive reports with news analysis
            messages=[{"role": "user", "content": prompt}],
            response_model=InsightReport
        )
        
        logger.info(f"Insight report generated")
        return response
        
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        raise
