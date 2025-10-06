"""
FewKnow API Package
Post-earnings performance analysis API
"""

from .core import (
    load_env_file,
    validate_ticker,
    get_earnings_metadata,
    analyze_price_performance,
    collect_reddit_data,
    analyze_reddit_with_llm,
    generate_insight_report,
)

from .models import (
    SentimentPeriod,
    Theme,
    InsightfulPost,
    RedditAnalysis,
    Event,
    InsightReport,
)

__all__ = [
    # Core functions
    'load_env_file',
    'validate_ticker',
    'get_earnings_metadata',
    'analyze_price_performance',
    'collect_reddit_data',
    'analyze_reddit_with_llm',
    'generate_insight_report',
    
    # Models
    'SentimentPeriod',
    'Theme',
    'InsightfulPost',
    'RedditAnalysis',
    'Event',
    'InsightReport',
]
