"""
Style Retriever
Retrieves similar posts from the FAISS index and extracts style patterns
for use as RAG context in post generation.
"""

import json
from pathlib import Path
from typing import Dict, List

from ingestion.faiss_pipeline import LinkedInFaissPipeline

FAISS_INDEX_PATH = Path("faiss_index/faiss_index.bin")
METADATA_PATH = Path("faiss_index/metadata.pkl")
STYLE_GUIDE_PATH = Path("data/nikit_style_guide_updated.json")


class StyleRetriever:
    """Retrieve similar posts from FAISS and extract writing patterns."""

    def __init__(self):
        self.pipeline = LinkedInFaissPipeline(
            index_path=FAISS_INDEX_PATH,
            metadata_path=METADATA_PATH,
        )
        self._style_guide: Dict = {}
        self._load_style_guide()

    def _load_style_guide(self):
        try:
            with open(STYLE_GUIDE_PATH, "r", encoding="utf-8") as f:
                self._style_guide = json.load(f)
        except FileNotFoundError:
            print("Warning: style guide not found. Run Phase 1 first.")
            self._style_guide = {}

    def retrieve_similar_posts(self, topic: str, k: int = 3) -> List[Dict]:
        """
        Search FAISS index for posts similar to the given topic.
        Returns list of post dicts with content, likes, url.
        """
        try:
            results = self.pipeline.search(query=topic, top_k=k)
            return results
        except FileNotFoundError:
            print("Warning: FAISS index not found. Run Phase 2 first.")
            return []
        except Exception as e:
            print(f"Warning: retrieval failed: {e}")
            return []

    def extract_style_patterns(self, retrieved_posts: List[Dict]) -> Dict:
        """
        Build a style pattern summary from retrieved posts + style guide.
        Used to prime the LLM prompt.
        """
        guide = self._style_guide

        # Derive patterns from the style guide (backed by real data)
        structure = [
            "Hook (bold statement or provocative question)",
            "Story / Personal context",
            "Key insight or numbered framework",
            "Actionable takeaway",
            "Closing question CTA",
        ]

        tone_markers = [
            "Here's what I learned...",
            "Here's how...",
            "Here's the thing:",
            "Most people get this wrong:",
            "I used to think... but then...",
            "The real opportunity here is...",
            "What actually works:",
        ]

        # Use top hashtags from the style guide
        top_hashtags = list(guide.get("common_hashtags", {}).keys())[:8]
        if not top_hashtags:
            top_hashtags = ["#ai", "#founders", "#startups", "#entrepreneurship"]

        avg_words = guide.get("average_post_length_words", 260)

        return {
            "structure": structure,
            "tone_markers": tone_markers,
            "paragraph_style": f"Short paragraphs (2-3 sentences max), ~{avg_words} words total",
            "emoji_suggestions": ["📈", "🚀", "💡", "⚡", "🎯", "✨", "▷", "→"],
            "hashtag_suggestions": top_hashtags,
            "uses_numbered_lists": guide.get("uses_numbered_lists_pct", 43) > 30,
            "uses_arrow_lists": guide.get("uses_arrow_lists_pct", 0) > 20,
            "always_ends_with_question": guide.get("has_question_pct", 83) > 70,
        }

    def get_style_guide_for_topic(self, topic: str) -> Dict:
        """
        Main entry point: retrieve similar posts + build style guidance for a topic.
        Returns a dict ready to be passed into the generation prompt.
        """
        similar_posts = self.retrieve_similar_posts(topic, k=3)
        patterns = self.extract_style_patterns(similar_posts)

        return {
            "topic": topic,
            "similar_post_count": len(similar_posts),
            "style_patterns": patterns,
            "retrieval_results": similar_posts,
            "generation_prompt_additions": self._build_generation_prompt(topic, patterns, similar_posts),
        }

    def _build_generation_prompt(self, topic: str, patterns: Dict, retrieved_posts: List[Dict]) -> str:
        """Build the RAG-enriched prompt addition for Gemini."""

        few_shot_block = ""
        if retrieved_posts:
            few_shot_block = "\n--- REFERENCE POSTS FROM NIKIT'S ACTUAL LINKEDIN ---\n"
            for i, post in enumerate(retrieved_posts[:2], 1):
                content = post.get("content", "").strip()
                if content:
                    # Truncate to first 400 chars to keep context tight
                    excerpt = content[:400] + ("..." if len(content) > 400 else "")
                    few_shot_block += f"\nExample {i} (engagement score: {post.get('engagement_score', 0)}):\n{excerpt}\n"

        structure_str = " → ".join(patterns["structure"])
        tone_str = ", ".join(f'"{t}"' for t in patterns["tone_markers"][:4])
        hashtags_str = " ".join(patterns["hashtag_suggestions"][:5])

        prompt = f"""You are Nikit Bassi, Founder of NB Media — an AI-powered 8-figure content agency.
Write a high-retention LinkedIn post about: {topic}

{few_shot_block}

WRITING STRUCTURE TO FOLLOW:
{structure_str}

TONE & VOICE:
- First-person, direct, confident, slightly casual
- Use phrases like: {tone_str}
- Reference your real experience building NB Media when relevant
- {patterns['paragraph_style']}
- Use 1-2 emojis max: {', '.join(patterns['emoji_suggestions'][:3])}

FORMATTING:
- Use numbered lists or → arrows for frameworks/steps (Nikit does this ~43% of posts)
- Keep paragraphs to 2-3 sentences maximum
- End with a thought-provoking question to drive comments

HASHTAGS (add 3-4 at the end):
{hashtags_str}

IMPORTANT:
- Never sound like a generic AI assistant
- Start IMMEDIATELY with the hook — no warm-up
- Be specific with numbers, names, examples (e.g. "₹6 lakhs", "200+ hours/month", "8-figure agency")
- This post will be published directly on LinkedIn

Write the post now:"""

        return prompt


# ------------------------------------------------------------------
# Convenience factory (used by agents/post_generator.py)
# ------------------------------------------------------------------

class StyleFactory:
    """Thin wrapper kept for backward compatibility with post_generator.py."""

    def __init__(self):
        self._retriever = StyleRetriever()

    def create_generation_prompt(self, topic: str, context: str = "") -> str:
        guide = self._retriever.get_style_guide_for_topic(topic)
        base_prompt = guide["generation_prompt_additions"]
        if context:
            base_prompt += f"\n\nADDITIONAL CONTEXT FROM USER:\n{context}"
        return base_prompt
