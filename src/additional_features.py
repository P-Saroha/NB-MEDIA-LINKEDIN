import re
from typing import List, Dict, Set
from collections import Counter

class HashtagResearch:
    """Research and suggest hashtags for LinkedIn posts"""
    
    # Nikit Bassi's common hashtags and related ones
    NICHE_HASHTAGS = {
        'automation': ['#automation', '#automate', '#workflow', '#process', '#productivity'],
        'linkedin': ['#LinkedIn', '#LinkedInGrowth', '#LinkedInTips', '#LinkedInStrategy'],
        'entrepreneurship': ['#Entrepreneurship', '#Startup', '#Business', '#Founder', '#BusinessOwner'],
        'growth': ['#GrowthHacking', '#Growth', '#Scaling', '#Scale', '#Expansion'],
        'content': ['#ContentMarketing', '#ContentCreation', '#Content', '#Copywriting', '#Writing'],
        'personal_brand': ['#PersonalBrand', '#Brand', '#Branding', '#PersonalBranding', '#Positioning'],
        'marketing': ['#Marketing', '#DigitalMarketing', '#MarketingStrategy', '#B2B', '#B2BMarketing'],
        'ai': ['#AI', '#ArtificialIntelligence', '#MachineLearning', '#Technology', '#Tech'],
        'strategy': ['#Strategy', '#StrategicPlanning', '#BusinessStrategy', '#Planning'],
        'sales': ['#Sales', '#SalesStrategy', '#B2BSales', '#SalesLeadership', '#Selling']
    }
    
    @classmethod
    def extract_hashtags_from_content(cls, content: str) -> List[str]:
        """Extract hashtags already mentioned in content"""
        hashtags = re.findall(r'#\w+', content)
        return list(set(hashtags))  # Remove duplicates
    
    @classmethod
    def suggest_hashtags(cls, topic: str, content: str = None, num_suggestions: int = 5) -> List[str]:
        """
        Suggest relevant hashtags based on topic and content
        
        Args:
            topic: Main topic of the post
            content: Full post content (optional)
            num_suggestions: Number of hashtags to suggest
            
        Returns:
            List of suggested hashtags
        """
        
        suggested = set()
        topic_lower = topic.lower()
        content_lower = (content or '').lower()
        
        # Match keywords to hashtag categories
        for category, hashtags in cls.NICHE_HASHTAGS.items():
            for keyword in [topic_lower, content_lower]:
                if category.replace('_', ' ') in keyword or category.replace('_', '') in keyword:
                    suggested.update(hashtags)
        
        # If not enough suggestions, look for partial matches
        if len(suggested) < num_suggestions:
            for category, hashtags in cls.NICHE_HASHTAGS.items():
                for word in topic.split():
                    if word.lower() in category:
                        suggested.update(hashtags)
        
        # Default hashtags if still not enough
        if len(suggested) < num_suggestions:
            suggested.update(['#LinkedIn', '#Entrepreneurship', '#Growth', '#Strategy', '#Innovation'])
        
        # Return limited list, sorted by relevance
        return sorted(list(suggested))[:num_suggestions]
    
    @classmethod
    def get_trending_hashtags_in_niche(cls) -> Dict[str, List[str]]:
        """Get trending hashtags by category"""
        return cls.NICHE_HASHTAGS
    
    @classmethod
    def hashtag_combination_analysis(cls, posts: List[str]) -> Dict[str, int]:
        """Analyze which hashtags appear most frequently together"""
        
        hashtag_pairs = []
        
        for post in posts:
            hashtags = re.findall(r'#\w+', post)
            if len(hashtags) > 1:
                for i in range(len(hashtags) - 1):
                    pair = f"{hashtags[i]} {hashtags[i+1]}"
                    hashtag_pairs.append(pair)
        
        # Count frequency
        counter = Counter(hashtag_pairs)
        return dict(counter.most_common(10))
    
    @classmethod
    def validate_hashtags(cls, hashtags: List[str]) -> Dict:
        """Validate and provide feedback on hashtag selection"""
        
        analysis = {
            'valid_count': 0,
            'invalid_count': 0,
            'recommendations': [],
            'hashtags': hashtags
        }
        
        for hashtag in hashtags:
            if hashtag.startswith('#') and len(hashtag) > 1:
                analysis['valid_count'] += 1
            else:
                analysis['invalid_count'] += 1
        
        # Check count (LinkedIn optimal is 3-5)
        if len(hashtags) < 3:
            analysis['recommendations'].append("Consider adding more hashtags (3-5 recommended)")
        elif len(hashtags) > 10:
            analysis['recommendations'].append("Too many hashtags, consider reducing to 5-8")
        
        # Check for diversity
        unique_categories = set()
        for hashtag in hashtags:
            for category in cls.NICHE_HASHTAGS:
                if hashtag in cls.NICHE_HASHTAGS[category]:
                    unique_categories.add(category)
                    break
        
        if len(unique_categories) < 2:
            analysis['recommendations'].append("Consider diverse hashtags from different categories")
        
        analysis['diversity_score'] = len(unique_categories) / len(cls.NICHE_HASHTAGS)
        
        return analysis


class ContentCalendar:
    """Manage LinkedIn content calendar"""
    
    def __init__(self, db_conn=None):
        self.db_conn = db_conn
    
    @staticmethod
    def get_calendar_view(posts: List[Dict], days: int = 30) -> Dict:
        """
        Generate calendar view of posts
        
        Args:
            posts: List of post dictionaries with created_at timestamps
            days: Number of days to show in calendar
            
        Returns:
            Calendar structure organized by date
        """
        
        calendar = {}
        
        for post in posts:
            created_at = post.get('created_at', '')
            if created_at:
                date = created_at.split()[0]  # Extract date part
                if date not in calendar:
                    calendar[date] = []
                calendar[date].append(post)
        
        return calendar
    
    @staticmethod
    def suggest_posting_schedule(posts: List[Dict]) -> Dict:
        """
        Suggest optimal posting schedule based on content and day of week
        
        Returns:
            Recommended posting schedule
        """
        
        schedule = {
            'Monday': {
                'optimal_times': ['9:00 AM', '12:00 PM', '5:00 PM'],
                'reason': 'High engagement at week start'
            },
            'Tuesday': {
                'optimal_times': ['8:00 AM', '1:00 PM', '6:00 PM'],
                'reason': 'Peak engagement mid-week'
            },
            'Wednesday': {
                'optimal_times': ['9:00 AM', '12:00 PM', '3:00 PM'],
                'reason': 'Mid-week professional check-in'
            },
            'Thursday': {
                'optimal_times': ['8:30 AM', '11:00 AM', '5:30 PM'],
                'reason': 'Pre-weekend engagement'
            },
            'Friday': {
                'optimal_times': ['9:00 AM', '12:00 PM'],
                'reason': 'Weekend wind-down mode'
            },
            'Saturday': {
                'optimal_times': ['10:00 AM', '3:00 PM'],
                'reason': 'Casual weekend browsing'
            },
            'Sunday': {
                'optimal_times': ['9:00 AM', '2:00 PM'],
                'reason': 'Sunday planning and inspiration'
            }
        }
        
        return schedule
    
    @staticmethod
    def analyze_content_distribution(posts: List[Dict]) -> Dict:
        """Analyze content distribution across topics"""
        
        topics_count = {}
        
        for post in posts:
            topic = post.get('topic', 'Unknown')
            topics_count[topic] = topics_count.get(topic, 0) + 1
        
        total = len(posts)
        
        distribution = {
            'total_posts': total,
            'topics': {},
            'most_common_topic': None,
            'least_common_topic': None
        }
        
        for topic, count in sorted(topics_count.items(), key=lambda x: x[1], reverse=True):
            distribution['topics'][topic] = {
                'count': count,
                'percentage': (count / total * 100) if total > 0 else 0
            }
        
        if distribution['topics']:
            distribution['most_common_topic'] = max(topics_count, key=topics_count.get)
            distribution['least_common_topic'] = min(topics_count, key=topics_count.get)
        
        return distribution
    
    @staticmethod
    def generate_monthly_plan(num_posts: int = 20) -> Dict:
        """Generate a monthly content plan template"""
        
        weeks = [
            {
                'week': 1,
                'theme': 'Automation & Efficiency',
                'posts_planned': num_posts // 4,
                'content_types': [
                    'How-to / Tutorial',
                    'Case Study / Results',
                    'Motivation / Inspiration',
                    'Trend Discussion'
                ]
            },
            {
                'week': 2,
                'theme': 'Growth & Strategy',
                'posts_planned': num_posts // 4,
                'content_types': [
                    'Personal Story',
                    'Industry Insight',
                    'Challenge / Problem Solving',
                    'Quick Tip'
                ]
            },
            {
                'week': 3,
                'theme': 'Personal Brand & Positioning',
                'posts_planned': num_posts // 4,
                'content_types': [
                    'Lesson Learned',
                    'Contrarian Take',
                    'Announcement',
                    'Engagement / Question'
                ]
            },
            {
                'week': 4,
                'theme': 'Tools & Resources',
                'posts_planned': num_posts // 4,
                'content_types': [
                    'Tool Review',
                    'Resource List',
                    'Behind-the-scenes',
                    'Recap / Reflection'
                ]
            }
        ]
        
        return {
            'month': 'Monthly Plan',
            'total_posts': num_posts,
            'weeks': weeks,
            'posting_frequency': f"{num_posts} posts across 4 weeks"
        }
