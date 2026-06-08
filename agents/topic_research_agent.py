"""
Topic Research Agent
Discovers trending topics relevant to Nikit's niche.
Sources: Google News RSS feeds + curated manual topics.
"""

import asyncio
from datetime import datetime
from typing import Dict, List

try:
    import feedparser
    _FEEDPARSER_AVAILABLE = True
except ImportError:
    _FEEDPARSER_AVAILABLE = False


# Google News RSS feeds for Nikit's niche
_RSS_FEEDS = {
    "ai_automation": "https://news.google.com/rss/search?q=AI+automation+business&ceid=IN:en&hl=en-IN",
    "founders_startups": "https://news.google.com/rss/search?q=startup+founder+India&ceid=IN:en&hl=en-IN",
    "ai_tools": "https://news.google.com/rss/search?q=AI+tools+productivity&ceid=US:en&hl=en",
    "linkedin_growth": "https://news.google.com/rss/search?q=LinkedIn+personal+branding&ceid=US:en&hl=en",
}

# Curated fallback topics (always available, represent Nikit's core themes)
_MANUAL_TOPICS = [
    {
        "title": "How AI is changing the economics of agency work in 2026",
        "description": "AI tools are letting 5-person teams operate like 50-person agencies. The cost structure of running a media or marketing agency has fundamentally shifted.",
        "category": "ai_automation",
        "relevance": 0.96,
        "source": "Manual",
    },
    {
        "title": "The founder who turned a ₹6 lakh AI investment into 200+ hours saved monthly",
        "description": "Building internal AI tools vs. relying on SaaS subscriptions — the ROI case for in-house automation in content agencies.",
        "category": "ai_tools",
        "relevance": 0.94,
        "source": "Manual",
    },
    {
        "title": "Why most AI automation businesses will fail this year",
        "description": "Selling 'automation' is a race to the bottom. The winners will be those selling transformations tied to specific business outcomes in niche industries.",
        "category": "ai_automation",
        "relevance": 0.92,
        "source": "Manual",
    },
    {
        "title": "Indian founders are running the world's top AI companies — and what that means",
        "description": "From Perplexity to Anthropic, Indian-origin founders are leading the AI revolution. What does this signal for India's next generation of builders?",
        "category": "founders_startups",
        "relevance": 0.90,
        "source": "Manual",
    },
    {
        "title": "The LinkedIn algorithm in 2026: what's actually working right now",
        "description": "Comments and dwell time matter more than likes. Authenticity beats growth-hacking. Here's the updated playbook for growing on LinkedIn.",
        "category": "linkedin_growth",
        "relevance": 0.88,
        "source": "Manual",
    },
    {
        "title": "Scaling from 5 to 50 employees without losing culture",
        "description": "The management mistakes most founders make when scaling fast, and the capsule team structure that actually works.",
        "category": "founders_startups",
        "relevance": 0.86,
        "source": "Manual",
    },
    {
        "title": "Voice AI is about to replace human call centres in India",
        "description": "Startups like Bolna and Giga are processing millions of calls with AI. India's billion-call-per-day economy is the next frontier.",
        "category": "ai_automation",
        "relevance": 0.85,
        "source": "Manual",
    },
    {
        "title": "No-code AI tools that solo founders are using to replace entire engineering teams",
        "description": "Lovable, Replit, Cursor — the stack that lets non-technical founders build real products. The barrier to building software has collapsed.",
        "category": "ai_tools",
        "relevance": 0.84,
        "source": "Manual",
    },
]


def _parse_rss_topic(entry: dict, category: str) -> Dict:
    return {
        "title": entry.get("title", ""),
        "description": entry.get("summary", entry.get("title", ""))[:300],
        "link": entry.get("link", ""),
        "published": entry.get("published", datetime.now().isoformat()),
        "category": category,
        "source": "Google News",
        "relevance": 0.78,
    }


async def _fetch_rss_topics(num_per_feed: int = 2) -> List[Dict]:
    """Fetch topics from Google News RSS. Non-blocking, silently skips on error."""
    if not _FEEDPARSER_AVAILABLE:
        return []

    topics = []
    for category, url in list(_RSS_FEEDS.items())[:2]:  # limit to 2 feeds to keep it fast
        try:
            parsed = feedparser.parse(url)
            for entry in parsed.entries[:num_per_feed]:
                if entry.get("title"):
                    topics.append(_parse_rss_topic(entry, category))
        except Exception:
            pass  # network errors are non-fatal
    return topics


def generate_post_angles(topic: Dict) -> List[Dict]:
    """Generate 5 content angles for a topic."""
    title = topic.get("title", "")
    return [
        {
            "angle": "educational",
            "hook": f"Here's what most people don't understand about {title}",
            "approach": "Break down the mechanics — teach something concrete",
        },
        {
            "angle": "personal_story",
            "hook": f"I learned this the hard way about {title}",
            "approach": "Share a personal experience or mistake related to the topic",
        },
        {
            "angle": "contrarian",
            "hook": f"Everyone's wrong about {title}",
            "approach": "Challenge the conventional wisdom with data or examples",
        },
        {
            "angle": "actionable",
            "hook": f"3 things you can do today about {title}",
            "approach": "Give immediate, step-by-step actions readers can take",
        },
        {
            "angle": "trend_analysis",
            "hook": f"Why {title} matters for your business right now",
            "approach": "Connect the trend to real business impact with numbers",
        },
    ]


class TopicResearchAgent:
    """Discover trending topics relevant to Nikit's content niche."""

    async def research_topics(self, num_topics: int = 5) -> List[Dict]:
        """Fetch from RSS feeds and supplement with manual topics."""
        rss_topics = await _fetch_rss_topics(num_per_feed=2)

        # Fill remainder with manual topics
        combined = rss_topics.copy()
        needed = max(0, num_topics - len(combined))
        combined.extend(_MANUAL_TOPICS[:needed + 3])  # add a buffer

        # Sort by relevance
        combined.sort(key=lambda x: x.get("relevance", 0), reverse=True)
        return combined[:num_topics]

    async def get_trending_topics(self, num_topics: int = 5) -> List[Dict]:
        """Get topics enriched with content angles."""
        topics = await self.research_topics(num_topics)
        for topic in topics:
            topic["angles"] = generate_post_angles(topic)
        return topics

    def filter_relevant_topics(self, topics: List[Dict], min_relevance: float = 0.75) -> List[Dict]:
        return [t for t in topics if t.get("relevance", 0) >= min_relevance]


# ------------------------------------------------------------------
# Synchronous public wrapper
# ------------------------------------------------------------------

def get_trending_topics(num_topics: int = 5) -> List[Dict]:
    """Get trending topics synchronously with angles."""
    agent = TopicResearchAgent()
    try:
        return asyncio.run(agent.get_trending_topics(num_topics))
    except RuntimeError:
        # Already inside an event loop (e.g. FastAPI)
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            fut = pool.submit(asyncio.run, agent.get_trending_topics(num_topics))
            return fut.result()
