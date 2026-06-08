from typing import Optional, Dict
from src.post_generator import PostGenerator
from src.auto_research import AutoResearch
from src.utils import save_post, get_unprocessed_topics, mark_topic_processed
import json

class ContentInput:
    """Handle both user input and auto-research content workflows"""
    
    def __init__(self):
        self.post_generator = PostGenerator()
        self.auto_research = AutoResearch()
    
    def process_user_input(self, topic: str, context: str = None) -> Dict:
        """
        Process user-provided topic and generate a LinkedIn post
        
        Args:
            topic: The topic provided by user
            context: Optional additional context
            
        Returns:
            Generated post with all details
        """
        
        print(f"\n📝 Processing user input: '{topic}'")
        
        # Validate input
        if not topic or len(topic.strip()) < 3:
            return {
                'status': 'error',
                'message': 'Topic must be at least 3 characters long'
            }
        
        # Generate post
        result = self.post_generator.generate_post(topic, context)
        
        if result:
            # Save to database
            post_id = self.post_generator.save_generated_post(
                topic=topic,
                post_content=result['post_content'],
                image_ideas=result['image_ideas'],
                hashtags=result['hashtags']
            )
            
            result['post_id'] = post_id
            result['status'] = 'success'
            result['source'] = 'user_input'
            
            return result
        
        return {
            'status': 'error',
            'message': 'Failed to generate post'
        }
    
    def process_auto_research(self, num_ideas: int = 5) -> Dict:
        """
        Automatically discover trending topics and generate posts
        
        Args:
            num_ideas: Number of post ideas to generate
            
        Returns:
            List of generated posts from trending topics
        """
        
        print("\n🔍 Starting auto-research workflow...")
        
        # Get trending topics
        topics = self.auto_research.get_trending_topics()
        print(f"✓ Found {len(topics)} topics")
        
        # Filter relevant topics
        relevant_topics = self.auto_research.filter_relevant_topics(topics)
        print(f"✓ Filtered to {len(relevant_topics)} relevant topics")
        
        # Save topics to database
        self.auto_research.save_topics_to_db(relevant_topics[:num_ideas])
        
        # Generate post ideas
        post_ideas = self.auto_research.generate_post_ideas(relevant_topics, num_ideas)
        
        return {
            'status': 'success',
            'source': 'auto_research',
            'topics_found': len(topics),
            'relevant_topics': len(relevant_topics),
            'post_ideas': post_ideas
        }
    
    def auto_generate_posts_from_ideas(self, limit: int = 5) -> Dict:
        """
        Automatically generate LinkedIn posts from unprocessed research topics
        
        Args:
            limit: Maximum number of posts to generate
            
        Returns:
            Summary of generated posts
        """
        
        print(f"\n⚡ Auto-generating posts from topics...")
        
        # Get unprocessed topics
        topics = get_unprocessed_topics(limit)
        
        if not topics:
            print("No unprocessed topics found. Run auto-research first.")
            return {
                'status': 'info',
                'message': 'No topics to process'
            }
        
        generated_posts = []
        
        for topic in topics:
            try:
                print(f"  → Generating post for: {topic['topic'][:50]}...")
                
                # Generate post
                result = self.post_generator.generate_post(
                    topic=topic['topic'],
                    context=topic.get('description', '')
                )
                
                # Save post
                post_id = self.post_generator.save_generated_post(
                    topic=topic['topic'],
                    post_content=result['post_content'],
                    image_ideas=result['image_ideas'],
                    hashtags=result['hashtags']
                )
                
                # Mark topic as processed
                mark_topic_processed(topic['id'])
                
                generated_posts.append({
                    'topic_id': topic['id'],
                    'post_id': post_id,
                    'topic': topic['topic'],
                    'status': 'generated'
                })
                
                print(f"    ✓ Post generated (ID: {post_id})")
            
            except Exception as e:
                print(f"    ❌ Error: {str(e)}")
        
        return {
            'status': 'success',
            'generated_count': len(generated_posts),
            'generated_posts': generated_posts
        }
    
    def interactive_workflow(self):
        """Interactive workflow for user to choose between modes"""
        
        print("\n" + "="*60)
        print("LinkedIn Content Agent - Interactive Workflow")
        print("="*60)
        
        print("\nChoose a mode:")
        print("1. User Input - Provide a topic and generate a post")
        print("2. Auto-Research - Discover trending topics and generate post ideas")
        print("3. Auto-Generate - Generate posts from previously discovered topics")
        print("4. Exit")
        
        choice = input("\nSelect option (1-4): ").strip()
        
        if choice == '1':
            topic = input("\nEnter your topic (e.g., 'LinkedIn automation', 'AI tools'): ").strip()
            context = input("Optional context (press Enter to skip): ").strip()
            
            result = self.process_user_input(topic, context if context else None)
            
            if result.get('status') == 'success':
                self._display_post_result(result)
            else:
                print(f"\n❌ Error: {result.get('message', 'Unknown error')}")
        
        elif choice == '2':
            num_ideas = input("\nHow many ideas to generate? (default: 5): ").strip()
            num_ideas = int(num_ideas) if num_ideas.isdigit() else 5
            
            result = self.process_auto_research(num_ideas)
            
            print(f"\n✓ Found {result.get('relevant_topics', 0)} relevant topics")
            print("\nTop Post Ideas:")
            
            for idea in result.get('post_ideas', [])[:3]:
                print(f"\n  📌 {idea['main_topic']}")
                print(f"     Relevance: {idea.get('relevance_score', 0):.0%}")
                print(f"     Hook: {idea['hook']}")
        
        elif choice == '3':
            limit = input("\nHow many posts to generate? (default: 5): ").strip()
            limit = int(limit) if limit.isdigit() else 5
            
            result = self.auto_generate_posts_from_ideas(limit)
            
            print(f"\n✓ Generated {result.get('generated_count', 0)} posts")
            print(f"Total posts saved: {len(result.get('generated_posts', []))}")
        
        elif choice == '4':
            print("\nGoodbye!")
        
        else:
            print("\n❌ Invalid option. Please try again.")
    
    def _display_post_result(self, result: Dict):
        """Pretty print a generated post result"""
        
        print("\n" + "="*60)
        print("✓ POST GENERATED SUCCESSFULLY")
        print("="*60)
        
        print(f"\n📝 POST CONTENT:\n")
        print(result.get('post_content', ''))
        
        print(f"\n🎯 HASHTAGS:")
        hashtags = result.get('hashtags', [])
        if hashtags:
            print(f"   {' '.join(hashtags)}")
        
        print(f"\n🖼️  IMAGE IDEAS:")
        image_ideas = result.get('image_ideas', [])
        for i, idea in enumerate(image_ideas, 1):
            print(f"   {i}. {idea}")
        
        print(f"\n📊 POST ID: {result.get('post_id', 'N/A')}")
        print(f"💾 Status: {result.get('status', 'draft')}")
        print(f"📍 Source: {result.get('source', 'unknown')}")
        
        if result.get('note'):
            print(f"\n⚠️  {result['note']}")
        
        print("\n" + "="*60)
