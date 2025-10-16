"""
Pydantic models for FewKnow analysis.
Defines structured data schemas for LLM outputs and API responses.
"""

from typing import List, Dict
from pydantic import BaseModel
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


class RedditAnalysis(BaseModel):
    """Output from LLM Call 1 - Reddit analysis"""
    sentiment_timeline: List[SentimentPeriod]
    top_themes: List[Theme]
    notable_insights: List[InsightfulPost]
    contrarian_takes: List[str]
    worry_vs_optimism: Dict[str, List[str]]
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
