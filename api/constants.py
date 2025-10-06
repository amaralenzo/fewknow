from enum import Enum


# ============================================================================
# ENUMS
# ============================================================================

class Sentiment(str, Enum):
    """Sentiment values"""
    BULLISH = "bullish"
    BEARISH = "bearish"
    MIXED = "mixed"


class Confidence(str, Enum):
    """Confidence levels"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Volatility(str, Enum):
    """Volatility levels"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# ============================================================================
# REDDIT DATA COLLECTION
# ============================================================================

# Maximum number of Reddit posts/comments to collect and process
MAX_REDDIT_POSTS = 50
MAX_REDDIT_SEARCH_LIMIT = 50  # Limit for each search query
MIN_POST_SCORE = 10  # Minimum score for a submission to be included
MIN_COMMENT_SCORE = 5  # Minimum score for a comment to be included
MIN_COMMENT_LENGTH = 100  # Minimum character length for quality comments
MAX_TEXT_LENGTH = 1000  # Maximum text length to store (truncate longer content)
MAX_SUBMISSIONS_FOR_COMMENTS = 30  # How many top submissions to extract comments from
MAX_COMMENTS_PER_SUBMISSION = 5  # Max comments to extract per submission
MAX_TOTAL_POSTS = 100  # Maximum total posts/comments to return


# ============================================================================
# NEWS DATA COLLECTION
# ============================================================================

MAX_NEWS_ARTICLES = 30  # Maximum news articles to include in LLM context
MAX_NEWS_DESCRIPTION_LENGTH = 500  # Truncate news descriptions to this length
NEWS_API_TIMEOUT = 10  # Timeout in seconds for news API requests


# ============================================================================
# LLM CONFIGURATION
# ============================================================================

# LLM model to use for analysis
LLM_MODEL = "claude-sonnet-4-5-20250929"

# Maximum tokens for each LLM call
LLM_REDDIT_ANALYSIS_MAX_TOKENS = 4000  # For Reddit sentiment analysis (Call 1)
LLM_INSIGHT_REPORT_MAX_TOKENS = 16000  # For final insight report (Call 2)

# Context limits
MAX_REDDIT_POSTS_FOR_LLM = 50  # How many posts to include in LLM context


# ============================================================================
# PRICE ANALYSIS
# ============================================================================

# Volatility thresholds (annualized percentage)
HIGH_VOLATILITY_THRESHOLD = 40  # Above this = high volatility
MEDIUM_VOLATILITY_THRESHOLD = 25  # Above this = medium volatility (below = low)

# Factor for annualizing volatility (trading days per year)
ANNUALIZATION_FACTOR = 252


# ============================================================================
# EARNINGS & FALLBACKS
# ============================================================================

# Days to look back if earnings date not found
DEFAULT_EARNINGS_DAYS_AGO = 90

# Maximum length for company guidance text
MAX_GUIDANCE_LENGTH = 500


# ============================================================================
# SUBREDDIT CONFIGURATION
# ============================================================================

# List of subreddits to search for retail sentiment
SUBREDDITS = ['wallstreetbets', 'stocks', 'investing']
