import requests
import json
from typing import List, Dict, Optional
from datetime import datetime
from src.utils import load_config, save_research_topic

class AutoResearch:
    """Automatically discover trending topics relevant to Nikit's niche"""
    
    def __init__(self):
        self.config = load_config()
        self.newsapi_key = self.config.get('newsapi_key', '')
        self.relevant_keywords = self.config.get('research_topics', [])
    
    def get_trending_topics(self) -> List[Dict]:
        """Fetch trending topics from news APIs"""
        
        topics = []
        
        # Try NewsAPI
        if self.newsapi_key and self.newsapi_key != 'YOUR_NEWSAPI_KEY':
            topics.extend(self._fetch_from_newsapi())
        
        # Add manual trending topics (can be hardcoded or from API)
        topics.extend(self._get_manual_trending_topics())
        
        return topics
    
    def _fetch_from_newsapi(self) -> List[Dict]:
        """Fetch trending news from NewsAPI"""
        topics = []
        
        try:
            base_url = "https://newsapi.org/v2/everything"
            
            # Search for each relevant keyword
            for keyword in self.relevant_keywords:
                params = {
                    'q': keyword,
                    'apiKey': self.newsapi_key,
                    'sortBy': 'publishedAt',
                    'language': 'en',
                    'pageSize': 5
                }
                
                response = requests.get(base_url, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    for article in data.get('articles', []):
                        topic = {
                            'topic': article.get('title', 'Untitled'),
                            'source': 'NewsAPI',
                            'description': article.get('description', ''),
                            'url': article.get('url', ''),
                            'published_at': article.get('publishedAt', ''),
                            'relevance_score': 0.8
                        }
                        topics.append(topic)
            
            print(f"✓ Fetched {len(topics)} topics from NewsAPI")
            
        except Exception as e:
            print(f"❌ Error fetching from NewsAPI: {str(e)}")
        
        return topics
    
    def _get_manual_trending_topics(self) -> List[Dict]:
        """Get manually curated trending topics (demo data)"""
        
        manual_topics = [
            {
                'topic': 'How AI is Changing LinkedIn Automation in 2024',
                'source': 'Manual',
                'description': 'Latest trends in LinkedIn automation using AI and machine learning',
                'relevance_score': 0.95
            },
            {
                'topic': 'The Future of Content Automation: AI-Powered Tools',
                'source': 'Manual',
                'description': 'Emerging AI tools for content creation and automation workflows',
                'relevance_score': 0.93
            },
            {
                'topic': '5 Content Marketing Strategies That Actually Work in 2024',
                'source': 'Manual',
                'description': 'Proven content marketing tactics for personal brands and entrepreneurs',
                'relevance_score': 0.88
            },
            {
                'topic': 'Scaling Your Personal Brand Without the Burnout',
                'source': 'Manual',
                'description': 'Sustainable strategies for growing your personal brand and influence',
                'relevance_score': 0.85
            },
            {
                'topic': 'Building a Profitable Automation Agency: What Works',
                'source': 'Manual',
                'description': 'Business strategies for automation service providers and consultants',
                'relevance_score': 0.82
            },
            {
                'topic': 'LinkedIn Algorithm Updates: What Changed and How to Adapt',
                'source': 'Manual',
                'description': 'Recent LinkedIn algorithm changes and optimization strategies',
                'relevance_score': 0.90
            },
            {
                'topic': 'Email vs. LinkedIn: Which Channel Wins for B2B Growth?',
                'source': 'Manual',
                'description': 'Comparative analysis of email marketing and LinkedIn for business growth',
                'relevance_score': 0.80
            },
            {
                'topic': 'The Psychology of LinkedIn Posts: What Makes People Engage?',
                'source': 'Manual',
                'description': 'Understanding engagement psychology and how to write viral LinkedIn posts',
                'relevance_score': 0.87
            }
        ]
        
        return manual_topics
    
    def filter_relevant_topics(self, topics: List[Dict], score_threshold: float = 0.75) -> List[Dict]:
        """Filter topics by relevance score"""
        
        relevant = [t for t in topics if t.get('relevance_score', 0) >= score_threshold]
        return sorted(relevant, key=lambda x: x.get('relevance_score', 0), reverse=True)
    
    def save_topics_to_db(self, topics: List[Dict]):
        """Save discovered topics to database for processing"""
        
        for topic in topics:
            save_research_topic(
                topic=topic.get('topic', ''),
                source=topic.get('source', 'unknown'),
                description=topic.get('description', ''),
                relevance_score=topic.get('relevance_score', 0.5)
            )
        
        print(f"✓ Saved {len(topics)} topics to database")
    
    def identify_content_gaps(self) -> List[str]:
        """Identify content gaps based on trending topics and existing content"""
        
        gaps = [
            'AI tools for LinkedIn automation',
            'Personal brand monetization strategies',
            'Content calendar planning templates',
            'LinkedIn DM outreach best practices',
            'Building an audience from zero followers',
            'Viral post formulas that actually work',
            'Scaling content production without burnout'
        ]
        
        return gaps
    
    def generate_post_ideas(self, topics: List[Dict], num_ideas: int = 5) -> List[Dict]:
        """Generate post ideas from trending topics"""
        
        post_ideas = []
        
        for i, topic in enumerate(topics[:num_ideas]):
            idea = {
                'id': f"idea_{i+1}",
                'main_topic': topic.get('topic', ''),
                'source': topic.get('source', ''),
                'description': topic.get('description', ''),
                'angle_1': f"How to leverage {topic.get('topic', '')} for personal growth",
                'angle_2': f"The hidden opportunity in {topic.get('topic', '')}",
                'angle_3': f"Why {topic.get('topic', '')} matters to creators and entrepreneurs",
                'hook': f"Here's what you need to know about {topic.get('topic', '')}",
                'relevance_score': topic.get('relevance_score', 0)
            }
            post_ideas.append(idea)
        
        return post_ideas
