"""
Pydantic models for FewKnow analysis.
Defines structured data schemas for LLM outputs and API responses.
"""

from typing import List, Dict
from pydantic import BaseModel, Field
from constants import Sentiment, Confidence

# ============================================================================
# REDDIT ANALYSIS MODELS
# ============================================================================

class SentimentPeriod(BaseModel):
    """Sentiment analysis for a time period"""
    period: str
    sentiment: Sentiment
    confidence: Confidence
    key_drivers: List[str]


class Theme(BaseModel):
    """Recurring theme from Reddit discussions"""
    theme: str
    mention_count: int
    sentiment: Sentiment
    example_quotes: List[str]


class InsightfulPost(BaseModel):
    """Notable Reddit post with insights"""
    date: str
    content_summary: str
    why_notable: str
    score: int


class NotableQuote(BaseModel):
    """Notable quote from Reddit discussion"""
    quote: str
    author: str
    date: str
    subreddit: str
    score: int
    context: str = Field(description="Brief context explaining why this quote is notable")


class RedditAnalysis(BaseModel):
    """Output from LLM Call 1 - Reddit analysis"""
    sentiment_timeline: List[SentimentPeriod]
    top_themes: List[Theme] = Field(
        description='List of Theme objects (NOT a JSON string). Each theme must be a properly structured Theme object with theme, mention_count, sentiment, and example_quotes fields.'
    )
    notable_insights: List[InsightfulPost]
    notable_quotes: List[NotableQuote] = Field(
        description='List of 10 notable quotes from Reddit discussions. These should be actual verbatim quotes (not paraphrased) that are insightful, contrarian, funny, or particularly representative of community sentiment.'
    )
    contrarian_takes: List[str]
    worry_vs_optimism: Dict[str, List[str]] = Field(
        description='Dictionary with exactly two keys: "worries" and "optimism", each containing a list of string statements. Must be a valid JSON object, not a string.'
    )
    overall_summary: str


class RedditComment(BaseModel):
    """Individual Reddit comment"""
    author: str
    text: str
    score: int
    date: str
    url: str
    image_urls: List[str] = []


class RedditPost(BaseModel):
    """Reddit post with top comments"""
    subreddit: str
    author: str
    title: str
    text: str
    score: int
    date: str
    url: str
    comments: List[RedditComment]
    image_urls: List[str] = []


# ============================================================================
# INSIGHT REPORT MODELS
# ============================================================================

class Event(BaseModel):
    """Timeline event"""
    date: str
    description: str
    source: str


class NewsArticle(BaseModel):
    """News article metadata"""
    title: str
    description: str
    source: str
    date: str
    url: str
    author: str


class InsightReport(BaseModel):
    """Final output from LLM Call 2"""
    headline: str
    story: str
    retail_perspective: str
    the_gap: str
    whats_next: str
    key_dates: List[Event]
    sources: List[str]
    top_reddit_posts: List[RedditPost] = []
