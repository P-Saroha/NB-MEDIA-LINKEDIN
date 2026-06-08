import openai
from typing import Dict, List, Tuple
from src.utils import load_config, load_system_prompt, load_style_guide, save_post
import json

class PostGenerator:
    """Generate LinkedIn posts in Nikit Bassi's style using OpenAI API"""
    
    def __init__(self):
        self.config = load_config()
        self.system_prompt = load_system_prompt()
        self.style_guide = load_style_guide()
        
        # Set OpenAI API key
        api_key = self.config.get('openai_api_key', '')
        if api_key and api_key != 'YOUR_OPENAI_API_KEY':
            openai.api_key = api_key
        else:
            print("⚠️  Warning: OpenAI API key not configured. Set it in config/config.json")
    
    def generate_post(self, topic: str, context: str = None) -> Dict:
        """
        Generate a LinkedIn post for the given topic
        
        Args:
            topic: The main topic for the post
            context: Additional context or specific direction
            
        Returns:
            Dict with generated post, image ideas, and hashtags
        """
        
        try:
            # Prepare the prompt
            full_prompt = self.system_prompt.replace("{topic}", topic)
            if context:
                full_prompt += f"\n\nADDITIONAL CONTEXT: {context}"
            
            # Call OpenAI API
            response = openai.ChatCompletion.create(
                model=self.config.get('post_generation', {}).get('model', 'gpt-3.5-turbo'),
                messages=[
                    {
                        "role": "system",
                        "content": "You are a LinkedIn content expert who creates posts in the style of Nikit Bassi."
                    },
                    {
                        "role": "user",
                        "content": full_prompt
                    }
                ],
                temperature=self.config.get('post_generation', {}).get('temperature', 0.7),
                max_tokens=self.config.get('post_generation', {}).get('max_tokens', 500)
            )
            
            post_content = response.choices[0].message.content
            
            # Extract hashtags and generate image ideas
            hashtags = self._extract_hashtags(post_content)
            image_ideas = self._generate_image_ideas(topic, post_content)
            
            return {
                'post_content': post_content,
                'hashtags': hashtags,
                'image_ideas': image_ideas,
                'topic': topic,
                'status': 'draft'
            }
        
        except Exception as e:
            print(f"❌ Error generating post: {str(e)}")
            # Fallback to demo mode if API fails
            return self._generate_demo_post(topic, context)
    
    def _extract_hashtags(self, post_content: str) -> List[str]:
        """Extract hashtags from post content"""
        import re
        hashtags = re.findall(r'#\w+', post_content)
        return list(set(hashtags))  # Remove duplicates
    
    def _generate_image_ideas(self, topic: str, post_content: str) -> List[str]:
        """Generate visual content ideas based on the post"""
        
        image_ideas = []
        
        # Analyze post for image suggestions
        if any(word in post_content.lower() for word in ['growth', 'increase', 'boost', 'improve']):
            image_ideas.append("📈 Chart showing growth/metrics with upward trend")
        
        if any(word in post_content.lower() for word in ['automation', 'workflow', 'process']):
            image_ideas.append("⚙️ Workflow diagram or automation process visualization")
        
        if any(word in post_content.lower() for word in ['strategy', 'steps', 'guide', 'how']):
            image_ideas.append("📊 Step-by-step infographic or numbered list visualization")
        
        if any(word in post_content.lower() for word in ['before', 'after', 'transformation', 'change']):
            image_ideas.append("🔄 Before/After comparison slide")
        
        if any(word in post_content.lower() for word in ['tips', 'lessons', 'insights', 'learn']):
            image_ideas.append("💡 Key takeaways or tips carousel")
        
        if any(word in post_content.lower() for word in ['ai', 'technology', 'tool', 'software']):
            image_ideas.append("🤖 Technology/Tool screenshot or demo image")
        
        # Default images
        if not image_ideas:
            image_ideas.append("📸 Quote image with key insight")
            image_ideas.append("🎯 Call-to-action image encouraging engagement")
        
        return image_ideas[:3]  # Return top 3 ideas
    
    def _generate_demo_post(self, topic: str, context: str = None) -> Dict:
        """Generate a demo post when API is not available"""
        
        demo_posts = {
            'automation': """Here's what most people miss about LinkedIn automation 🎯

I used to spend 3 hours every day managing LinkedIn outreach. That's 15 hours a week.

Then I realized: I could automate the repetitive parts and focus on authentic connections.

Here's what changed everything:

1. Use tools to schedule content (not for engagement - that's still manual)
2. Automate prospecting workflows with smart filters
3. Create templates for first messages (but personalize the first line)
4. Use CRM integration to track conversations

The key insight: Automation isn't about being less human. It's about being more strategic with your time.

What's the most time-consuming part of your LinkedIn strategy?

#automation #LinkedIn #Entrepreneurship #GrowthHacking""",
            
            'content': """The best content creators follow this 80/20 rule 📝

80% of my time: Understanding my audience's problems
20% of my time: Writing and formatting

Most people reverse this.

They spend weeks perfecting the post format, but never really understand who they're writing for. That's backwards.

Here's what actually works:

1. Spend time in the comments of posts in your niche
2. Note the patterns in what people struggle with
3. Create content that solves THOSE problems
4. Stop worrying about the perfect template

Your authentic voice > perfect formatting

What's the main problem your audience faces right now?

#ContentMarketing #LinkedIn #Growth #Strategy #PersonalBrand""",
            
            'linkedin': """Most LinkedIn growth strategies fail for one reason 🚀

People try to copy what worked for someone else.

But your audience is different. Your experience is different. Your background is different.

I spent 2 years trying to write like other creators. My growth was flat.

The moment I stopped copying and started sharing MY unique perspective, everything changed.

Here's the framework that works:

1. Share your actual journey, not a highlight reel
2. Talk about what you're learning, not just what you know
3. Ask genuine questions to your audience
4. Respond to EVERY comment for the first week

Authenticity scales. Eventually.

What's one thing you know that others in your field don't?

#LinkedIn #PersonalBrand #Growth #Authenticity #Entrepreneurship"""
        }
        
        # Try to match topic to a demo post
        post_content = None
        for key, post in demo_posts.items():
            if key.lower() in topic.lower():
                post_content = post
                break
        
        # If no match, use a generic one
        if not post_content:
            post_content = demo_posts['linkedin']
        
        hashtags = self._extract_hashtags(post_content)
        image_ideas = self._generate_image_ideas(topic, post_content)
        
        return {
            'post_content': post_content,
            'hashtags': hashtags,
            'image_ideas': image_ideas,
            'topic': topic,
            'status': 'draft',
            'note': '⚠️ Demo post generated (API not available)'
        }
    
    def save_generated_post(self, topic: str, post_content: str, 
                           image_ideas: List[str], hashtags: List[str]) -> int:
        """Save generated post to database"""
        
        post_id = save_post(
            title=f"Post about {topic}",
            content=post_content,
            topic=topic,
            source='generated',
            image_ideas=json.dumps(image_ideas),
            hashtags=json.dumps(hashtags),
            status='draft'
        )
        
        return post_id
