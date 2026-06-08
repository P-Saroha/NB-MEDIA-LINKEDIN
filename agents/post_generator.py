"""
Post Generator Agent
Generates LinkedIn posts in Nikit Bassi's style using Gemini 2.5 Flash + RAG.
"""

import os
import re
from typing import Dict, List

from dotenv import load_dotenv

load_dotenv()


class PostGeneratorAgent:
    """Generate LinkedIn posts using Gemini 2.5 Flash with FAISS-based style retrieval."""

    MODEL_NAME = "gemini-2.5-flash"

    def __init__(self, llm_provider: str = "google"):
        self.llm_provider = llm_provider
        self.client = None
        self._initialize_llm()

        # Lazy-import style factory to avoid loading FAISS at import time
        self._style_factory = None

    def _initialize_llm(self):
        if self.llm_provider == "google":
            try:
                from google import genai

                api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
                if api_key:
                    self.client = genai.Client(api_key=api_key)
                else:
                    print("Warning: GEMINI_API_KEY not set in .env — will use demo fallback.")
            except Exception as e:
                print(f"Warning: Could not initialise Gemini client: {e}")
        else:
            print(f"Warning: provider '{self.llm_provider}' not supported; using demo fallback.")

    @property
    def style_factory(self):
        if self._style_factory is None:
            from agents.style_retriever import StyleFactory
            self._style_factory = StyleFactory()
        return self._style_factory

    # ------------------------------------------------------------------
    # Core generation
    # ------------------------------------------------------------------

    def generate_post_sync(
        self,
        topic: str,
        context: str = "",
        style_guidance: bool = True,
    ) -> Dict:
        """Generate a LinkedIn post synchronously. Returns structured dict."""

        if style_guidance:
            prompt = self.style_factory.create_generation_prompt(topic, context)
        else:
            prompt = (
                f"Write a LinkedIn post in the style of Nikit Bassi about: {topic}\n\n"
                + (context if context else "")
            )

        if self.llm_provider == "google" and self.client:
            post_content = self._generate_with_gemini(prompt)
        else:
            post_content = self._demo_post(topic)

        hashtags = self._extract_hashtags(post_content)
        image_ideas = self._generate_image_ideas(topic, post_content)

        return {
            "post_content": post_content,
            "topic": topic,
            "hashtags": hashtags,
            "image_ideas": image_ideas,
            "length": len(post_content),
            "generation_model": self.MODEL_NAME if (self.client and self.llm_provider == "google") else "demo",
            "style_guided": style_guidance,
        }

    def _generate_with_gemini(self, prompt: str) -> str:
        try:
            from google.genai import types

            config = types.GenerateContentConfig(
                temperature=0.75,
                top_p=0.95,
                max_output_tokens=700,
                # Disable thinking budget so all tokens go to output
                thinking_config=types.ThinkingConfig(thinking_budget=0),
            )
            
            full_prompt = f"""
You are a LinkedIn ghostwriter.

Your task is NOT to pretend to be Nikit Bassi.

Your task is to write in the style of Nikit Bassi.

Rules:

- Never claim personal experiences.
- Never write "I built NB Media".
- Never write "At NB Media".
- Never invent achievements.
- Do not roleplay as Nikit.

Most Nikit posts follow:

1. Strong hook
2. Introduce founder/company
3. Explain opportunity
4. Numbered breakdown
5. Results or metrics
6. End with a question

Writing style:

- Simple English
- Short paragraphs
- Heavy whitespace
- Specific numbers
- Founder stories
- Startup breakdowns
- Business opportunities

Use the retrieved examples below as your style reference.

{prompt}
"""

            response = self.client.models.generate_content(
                model=self.MODEL_NAME,
                contents=full_prompt,
                config=config,
            )
            return response.text.strip()
        except Exception as e:
            print(f"Gemini generation error: {e}")
            return self._demo_post("")

    def _demo_post(self, topic: str) -> str:
        """Fallback post when no API key is available."""
        return (
            f"This founder built a successful business around {topic}.\n\n"
            "Most people focus on tools.\n\n"
            "They focused on the problem.\n\n"
            "Here's what they did:\n\n"
            "1. Found a painful bottleneck\n"
            "2. Built a simple solution\n"
            "3. Validated demand\n"
            "4. Scaled with systems\n\n"
            "The opportunity wasn't the technology.\n"
            "It was solving a real business problem.\n\n"
            "What opportunity do you see in your industry?\n\n"
            "#ai #founders #startups #business"
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _extract_hashtags(self, content: str) -> List[str]:
        return list(set(re.findall(r"#\w+", content)))

    def _generate_image_ideas(self, topic: str, post_content: str) -> List[str]:
        """Keyword-based image idea suggestions."""
        ideas = []
        text = (topic + " " + post_content).lower()

        if any(w in text for w in ["growth", "increase", "revenue", "scale", "8-figure"]):
            ideas.append("📈 Chart or infographic showing growth trajectory")
        if any(w in text for w in ["automation", "workflow", "n8n", "make", "zapier"]):
            ideas.append("⚙️ Workflow diagram showing the automation pipeline")
        if any(w in text for w in ["steps", "framework", "how to", "guide", "numbered"]):
            ideas.append("📊 Step-by-step carousel or numbered-list infographic")
        if any(w in text for w in ["before", "after", "transformation", "change", "used to"]):
            ideas.append("🔄 Before/After comparison visual")
        if any(w in text for w in ["team", "people", "culture", "retreat", "office"]):
            ideas.append("👥 Behind-the-scenes team photo or candid shot")
        if any(w in text for w in ["ai", "tool", "gemini", "chatgpt", "claude", "software"]):
            ideas.append("🤖 Screenshot or demo of the AI tool in action")

        if not ideas:
            ideas.append("📸 Quote card with the key insight from the post")
            ideas.append("🎯 Scroll-stopping hook image with bold text overlay")

        return ideas[:3]


# ------------------------------------------------------------------
# Public wrappers (used by api/main.py)
# ------------------------------------------------------------------

def generate_linkedin_post(
    topic: str,
    context: str = "",
    llm_provider: str = "google",
) -> Dict:
    """Generate a LinkedIn post. Returns structured result dict."""
    agent = PostGeneratorAgent(llm_provider=llm_provider)
    return agent.generate_post_sync(topic, context)


def generate_image_ideas(post_content: str, topic: str = "") -> list:
    """Generate image content ideas for a post."""
    agent = PostGeneratorAgent.__new__(PostGeneratorAgent)
    agent.client = None
    agent._style_factory = None
    agent.llm_provider = "google"
    return agent._generate_image_ideas(topic, post_content)