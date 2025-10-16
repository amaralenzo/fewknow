"""
Test script to estimate context size for generate_insight_report
"""
import json
from typing import List, Dict
from pydantic import BaseModel, Field
from enum import Enum

# Minimal models for testing
class Sentiment(str, Enum):
    BULLISH='bullish'
    BEARISH='bearish'
    MIXED='mixed'

class Confidence(str, Enum):
    HIGH='high'
    MEDIUM='medium'
    LOW='low'

class SentimentPeriod(BaseModel):
    period: str
    sentiment: Sentiment
    confidence: Confidence
    key_drivers: List[str]

class Theme(BaseModel):
    theme: str
    mention_count: int
    sentiment: Sentiment
    example_quotes: List[str]

class InsightfulPost(BaseModel):
    date: str
    content_summary: str
    why_notable: str
    score: int

class RedditAnalysis(BaseModel):
    sentiment_timeline: List[SentimentPeriod]
    top_themes: List[Theme]
    notable_insights: List[InsightfulPost]
    contrarian_takes: List[str]
    worry_vs_optimism: Dict[str, List[str]]
    overall_summary: str

# Create realistic example
reddit_analysis = RedditAnalysis(
    sentiment_timeline=[
        SentimentPeriod(
            period='Week 1-2 (July 30 - Aug 13)',
            sentiment=Sentiment.BULLISH,
            confidence=Confidence.HIGH,
            key_drivers=['earnings beat expectations', 'strong AI revenue growth', 'positive guidance']
        ),
        SentimentPeriod(
            period='Week 3-4 (Aug 14 - Aug 27)',
            sentiment=Sentiment.MIXED,
            confidence=Confidence.MEDIUM,
            key_drivers=['antitrust concerns', 'market volatility', 'valuation questions']
        ),
        SentimentPeriod(
            period='Week 5-10 (Aug 28 - Oct 15)',
            sentiment=Sentiment.BEARISH,
            confidence=Confidence.MEDIUM,
            key_drivers=['broader tech selloff', 'macro concerns', 'profit taking']
        )
    ],
    top_themes=[
        Theme(
            theme='AI Monetization Concerns',
            mention_count=67,
            sentiment=Sentiment.BEARISH,
            example_quotes=[
                'They are spending billions on AI but where is the revenue?',
                'Reality Labs is burning cash',
                'AI promises vs actual returns not adding up'
            ]
        ),
        Theme(
            theme='Regulatory Headwinds',
            mention_count=52,
            sentiment=Sentiment.BEARISH,
            example_quotes=[
                'EU regulations will hurt their business model',
                'Antitrust issues mounting',
                'Privacy concerns in multiple countries'
            ]
        ),
        Theme(
            theme='User Engagement Decline',
            mention_count=45,
            sentiment=Sentiment.BEARISH,
            example_quotes=[
                'Facebook usage declining among younger demos',
                'Instagram losing to TikTok',
                'Threads failed to maintain momentum'
            ]
        ),
        Theme(
            theme='Valuation Disconnect',
            mention_count=38,
            sentiment=Sentiment.MIXED,
            example_quotes=[
                'Trading at high multiples despite slowing growth',
                'Still cheaper than other mega caps',
                'Forward P/E looks reasonable if they execute'
            ]
        ),
        Theme(
            theme='Advertising Market Strength',
            mention_count=29,
            sentiment=Sentiment.BULLISH,
            example_quotes=[
                'Ad revenue beat shows demand is strong',
                'Digital advertising taking share from traditional',
                'Reels monetization working better than expected'
            ]
        )
    ],
    notable_insights=[
        InsightfulPost(
            date='2025-08-05',
            content_summary='Detailed breakdown of Reality Labs losses and why they might be worth it long-term despite burning $4B per quarter',
            why_notable='Quantified analysis with industry comparisons',
            score=1234
        ),
        InsightfulPost(
            date='2025-08-18',
            content_summary='Analysis of Meta vs Google AI competition showing Meta is behind in monetization but ahead in open-source strategy',
            why_notable='Contrarian take with data',
            score=892
        ),
        InsightfulPost(
            date='2025-09-12',
            content_summary='User engagement data showing Instagram Reels growth offsetting Facebook decline',
            why_notable='Insider perspective with numbers not in earnings report',
            score=756
        ),
        InsightfulPost(
            date='2025-10-01',
            content_summary='Regulatory analysis showing EU fine risk is overblown and already priced in',
            why_notable='Legal expert perspective',
            score=623
        )
    ],
    contrarian_takes=[
        'Stock is actually undervalued if you exclude Reality Labs losses',
        'Market is wrong about advertising weakness - digital shift is accelerating',
        'AI spending will pay off bigger than cloud did for AWS',
        'User decline narrative is overblown - monetization per user is what matters'
    ],
    worry_vs_optimism={
        'worries': [
            'Reality Labs burning $4B+ per quarter with no clear path to profitability',
            'Regulatory risks mounting in EU and US',
            'Competition from TikTok hurting engagement',
            'AI spending seems like defensive capex not offensive growth',
            'User growth stagnant in key markets'
        ],
        'optimism': [
            'Ad business remains incredibly strong and profitable',
            'Reels monetization exceeding expectations',
            'WhatsApp and Instagram have huge untapped monetization potential',
            'AI investments could create new revenue streams',
            'Still trades cheaper than GOOGL and MSFT on FCF basis'
        ]
    },
    overall_summary='The Reddit community is divided on Meta post-earnings. Bulls point to strong ad revenue and improving Reels monetization, while bears focus on Reality Labs cash burn, regulatory risks, and questions about AI ROI. The stock underperformance relative to sector is attributed more to macro concerns and profit-taking than company-specific issues, though skepticism about metaverse spending persists.'
)

# Create realistic news articles
news_articles = []
for i in range(30):
    news_articles.append({
        'title': f'Meta Platforms Reports Q3 Earnings Beat - Analysis of Key Metrics and Future Outlook {i+1}',
        'description': 'Meta Platforms Inc reported better-than-expected third quarter earnings with revenue growth driven by strong advertising demand and improved monetization of Reels. The company also announced increased AI spending plans and provided guidance that slightly exceeded analyst expectations. However, Reality Labs continued to post significant losses.' * 2,  # ~400 chars
        'source': 'Financial Times',
        'date': '2025-08-01',
        'url': 'https://example.com/article',
        'author': 'Tech Reporter'
    })

# Calculate sizes
company_info = {'name': 'Meta Platforms, Inc.', 'sector': 'Communication Services'}
earnings_metadata = {
    'date': '2025-07-30',
    'eps_actual': 5.16,
    'eps_estimate': 4.73,
    'revenue': 39070000000,
    'guidance': 'Company expects continued strong advertising demand with some headwinds from regulatory changes in Europe.' * 3
}
price_performance = {
    'since_earnings': '2.5%',
    'vs_sp500': '-1.9%',
    'vs_sector': '-0.8%',
    'sector_etf': 'XLC',
    'max_drawdown': '-8.3%',
    'current_price': '$523.45',
    'volatility': 'medium',
    'volatility_pct': '32.1%'
}

context = {
    'company': company_info['name'],
    'ticker': 'META',
    'sector': company_info['sector'],
    'last_earnings': earnings_metadata,
    'price_performance': price_performance,
    'reddit_analysis': reddit_analysis.model_dump(),
    'news_articles': news_articles[:30],
    'news_articles_count': 244,
    'top_reddit_posts': [
        {'title': 'META earnings discussion', 'date': '2025-08-01', 'url': 'https://reddit.com/r/wallstreetbets/xyz', 'score': 2341, 'subreddit': 'wallstreetbets'}
    ] * 5
}

# Test with indent=2 (current)
context_json_indented = json.dumps(context, indent=2, default=str)
print(f"\n=== WITH indent=2 ===")
print(f"Total chars: {len(context_json_indented):,}")
print(f"Estimated tokens: ~{len(context_json_indented)//4:,}")

# Test without indent (proposed)
context_json_compact = json.dumps(context, default=str)
print(f"\n=== WITHOUT indent (compact) ===")
print(f"Total chars: {len(context_json_compact):,}")
print(f"Estimated tokens: ~{len(context_json_compact)//4:,}")
print(f"Savings: {len(context_json_indented) - len(context_json_compact):,} chars (~{(len(context_json_indented) - len(context_json_compact))//4:,} tokens)")

# Breakdown
reddit_json = json.dumps(reddit_analysis.model_dump(), indent=2)
news_json = json.dumps(news_articles[:30], indent=2)
metadata_json = json.dumps({
    'last_earnings': earnings_metadata,
    'price_performance': price_performance
}, indent=2)

print(f"\n=== BREAKDOWN (with indent=2) ===")
print(f"Reddit analysis: {len(reddit_json):,} chars (~{len(reddit_json)//4:,} tokens)")
print(f"30 News articles: {len(news_json):,} chars (~{len(news_json)//4:,} tokens)")
print(f"Metadata: {len(metadata_json):,} chars (~{len(metadata_json)//4:,} tokens)")

# Test with fewer news articles
for count in [20, 15, 10]:
    context_test = context.copy()
    context_test['news_articles'] = news_articles[:count]
    test_json = json.dumps(context_test, default=str)  # compact
    print(f"\n=== WITH {count} news articles (compact) ===")
    print(f"Total chars: {len(test_json):,}")
    print(f"Estimated tokens: ~{len(test_json)//4:,}")
    
# Estimate prompt size
prompt_instructions = """Your formatting instructions and all the other text in your prompt"""
print(f"\n=== PROMPT ESTIMATE ===")
print(f"Prompt instructions: ~2,000 chars (~500 tokens)")
print(f"\n=== TOTAL INPUT ESTIMATE (30 articles, compact JSON) ===")
compact_30 = len(json.dumps(context, default=str))
print(f"Context: ~{compact_30//4:,} tokens")
print(f"Prompt text: ~500 tokens")
print(f"TOTAL INPUT: ~{compact_30//4 + 500:,} tokens")
print(f"\n=== TOTAL INPUT ESTIMATE (15 articles, compact JSON) ===")
context_15 = context.copy()
context_15['news_articles'] = news_articles[:15]
compact_15 = len(json.dumps(context_15, default=str))
print(f"Context: ~{compact_15//4:,} tokens")
print(f"Prompt text: ~500 tokens")
print(f"TOTAL INPUT: ~{compact_15//4 + 500:,} tokens")
