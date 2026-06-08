"""
LinkedIn Post Data Processing Pipeline
Processes dataset_linkedin-profile-posts_2026-06-08_10-29-48-888.json
into structured training data and style guide for the RAG pipeline.
"""

import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path


RAW_DATA_FILE = "dataset_linkedin-profile-posts_2026-06-08_10-29-48-888.json"
OUTPUT_DIR = Path("data")


class LinkedInDataProcessor:
    """Process raw LinkedIn post data into structured format for AI training."""

    def __init__(self, input_file: str = RAW_DATA_FILE):
        self.input_file = input_file
        self.raw_data: list = []
        self.processed_data: list = []

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    def load_raw_data(self) -> int:
        try:
            with open(self.input_file, "r", encoding="utf-8") as f:
                self.raw_data = json.load(f)
            print(f"Loaded {len(self.raw_data)} raw records")
            return len(self.raw_data)
        except Exception as e:
            print(f"Error loading data: {e}")
            return 0

    # ------------------------------------------------------------------
    # Filtering helpers
    # ------------------------------------------------------------------

    def _is_nikit_original(self, record: dict) -> bool:
        """Only keep posts written by Nikit himself (no reposts, no company posts)."""
        author = record.get("author", {})
        is_nikit = author.get("publicIdentifier") == "nikitbassi"
        is_repost = bool(record.get("repostedBy"))
        has_content = bool(record.get("content", "").strip())
        return is_nikit and not is_repost and has_content

    # ------------------------------------------------------------------
    # Style analysis helpers
    # ------------------------------------------------------------------

    def extract_hashtags(self, text: str) -> list:
        return re.findall(r"#\w+", text)

    def _detect_opening_style(self, text: str) -> str:
        first_line = text.split("\n")[0].lower()
        if "?" in first_line:
            return "question"
        if any(w in first_line for w in ["this", "here", "most", "best", "biggest", "i ", "we "]):
            return "hook"
        if text.startswith('"'):
            return "quote"
        if any(w in first_line for w in ["meet", "introducing", "founder", "ceo"]):
            return "introduction"
        return "statement"

    def _has_call_to_action(self, text: str) -> bool:
        cta_keywords = [
            "share your", "drop a", "let me know", "thoughts?", "comments?",
            "would you", "check out", "comment", "follow", "connect", "dm",
            "what do you think", "what would you", "curious to hear",
        ]
        return any(k in text.lower() for k in cta_keywords)

    def _detect_cta_type(self, text: str) -> str:
        t = text.lower()
        if "comment" in t:
            return "comment_trigger"
        if "share" in t:
            return "share_thoughts"
        if "dm" in t or "message" in t:
            return "direct_message"
        if "follow" in t or "subscribe" in t:
            return "follow_subscribe"
        return "engagement"

    def _detect_tone(self, text: str) -> str:
        t = text.lower()
        educational = ["learn", "teach", "guide", "how to", "step", "framework", "here's how"]
        motivational = ["you can", "possible", "opportunity", "success", "growth", "scale", "bet on yourself"]
        analytical = ["data", "analysis", "research", "found", "study", "metric", "revenue", "billion"]
        storytelling = ["i was", "i realised", "i spent", "i failed", "one day", "last week", "last year"]

        scores = {
            "educational": sum(1 for w in educational if w in t),
            "motivational": sum(1 for w in motivational if w in t),
            "analytical": sum(1 for w in analytical if w in t),
            "storytelling": sum(1 for w in storytelling if w in t),
        }
        best = max(scores, key=scores.get)
        return best if scores[best] > 1 else "neutral"

    def _detect_format(self, text: str) -> dict:
        return {
            "numbered_list": bool(re.search(r"^\d+\.", text, re.MULTILINE)),
            "arrow_list": bool(re.search(r"^→|^▷|^▶", text, re.MULTILINE)),
            "bullet_points": bool(re.search(r"^-\s", text, re.MULTILINE)),
            "has_question": "?" in text,
            "short_paragraphs": sum(1 for line in text.split("\n") if line.strip()),
            "emoji_count": len(re.findall(r"[\U0001F300-\U0001FAFF]", text)),
        }

    def _categorize_performance(self, likes: int) -> str:
        if likes >= 500:
            return "viral"
        if likes >= 100:
            return "high"
        if likes >= 30:
            return "medium"
        return "low"

    def analyze_post_style(self, text: str) -> dict:
        fmt = self._detect_format(text)
        return {
            "opening_style": self._detect_opening_style(text),
            "emoji_count": fmt["emoji_count"],
            "has_cta": self._has_call_to_action(text),
            "cta_type": self._detect_cta_type(text),
            "tone": self._detect_tone(text),
            "line_count": len(text.split("\n")),
            "numbered_list": fmt["numbered_list"],
            "arrow_list": fmt["arrow_list"],
            "bullet_points": fmt["bullet_points"],
            "has_question": fmt["has_question"],
        }

    # ------------------------------------------------------------------
    # Processing
    # ------------------------------------------------------------------

    def process_post(self, record: dict) -> dict:
        content = record.get("content", "")
        engagement = record.get("engagement", {})
        posted_at = record.get("postedAt", {})
        likes = engagement.get("likes", 0)

        return {
            "id": record.get("id"),
            "url": record.get("shareLinkedinUrl", record.get("linkedinUrl", "")),
            "text": content,
            "word_count": len(content.split()),
            "character_count": len(content),
            "posted_date": posted_at.get("date", ""),
            "engagement": {
                "likes": likes,
                "comments": engagement.get("comments", 0),
                "shares": engagement.get("shares", 0),
                "engagement_score": likes + engagement.get("comments", 0) * 3 + engagement.get("shares", 0) * 5,
            },
            "hashtags": self.extract_hashtags(content),
            "has_image": len(record.get("postImages", [])) > 0,
            "style": self.analyze_post_style(content),
            "performance": self._categorize_performance(likes),
        }

    def process_all(self) -> list:
        originals = [r for r in self.raw_data if self._is_nikit_original(r)]
        print(f"Filtering to {len(originals)} original Nikit posts (from {len(self.raw_data)} total)")

        self.processed_data = []
        for i, record in enumerate(originals, 1):
            try:
                self.processed_data.append(self.process_post(record))
            except Exception as e:
                print(f"  Warning: skipping post {i}: {e}")

        print(f"Processed {len(self.processed_data)} posts")
        return self.processed_data

    # ------------------------------------------------------------------
    # Saving
    # ------------------------------------------------------------------

    def save_json(self, output_file: str):
        if not self.processed_data:
            print("No data to save")
            return
        output = {
            "metadata": {
                "source": "LinkedIn Profile - Nikit Bassi",
                "author": "Nikit Bassi",
                "total_posts": len(self.processed_data),
                "processed_date": datetime.now().isoformat(),
                "average_engagement": sum(p["engagement"]["likes"] for p in self.processed_data) / len(self.processed_data),
            },
            "posts": self.processed_data,
        }
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        print(f"Saved processed data -> {output_file}")

    def generate_style_guide(self) -> dict:
        if not self.processed_data:
            return {}

        opening_styles = [p["style"]["opening_style"] for p in self.processed_data]
        tones = [p["style"]["tone"] for p in self.processed_data]
        cta_types = [p["style"]["cta_type"] for p in self.processed_data]
        all_hashtags: list = []
        for p in self.processed_data:
            all_hashtags.extend(p["hashtags"])

        # High-performing posts (viral + high)
        top_posts = [p for p in self.processed_data if p["performance"] in ("viral", "high")]
        top_tones = [p["style"]["tone"] for p in top_posts]
        top_openings = [p["style"]["opening_style"] for p in top_posts]

        return {
            "author": "Nikit Bassi",
            "total_posts_analyzed": len(self.processed_data),

            # Structural patterns
            "preferred_opening_style": Counter(opening_styles).most_common(1)[0][0],
            "opening_style_distribution": dict(Counter(opening_styles)),
            "preferred_tone": Counter(tones).most_common(1)[0][0],
            "tone_distribution": dict(Counter(tones)),

            # High-performer patterns
            "top_post_count": len(top_posts),
            "top_post_tone": Counter(top_tones).most_common(1)[0][0] if top_tones else "storytelling",
            "top_post_opening": Counter(top_openings).most_common(1)[0][0] if top_openings else "hook",

            # Engagement stats
            "average_post_length_words": round(sum(p["word_count"] for p in self.processed_data) / len(self.processed_data)),
            "average_engagement_likes": round(sum(p["engagement"]["likes"] for p in self.processed_data) / len(self.processed_data)),
            "performance_distribution": dict(Counter(p["performance"] for p in self.processed_data)),

            # Content patterns
            "uses_numbered_lists_pct": round(sum(1 for p in self.processed_data if p["style"]["numbered_list"]) / len(self.processed_data) * 100, 1),
            "uses_arrow_lists_pct": round(sum(1 for p in self.processed_data if p["style"]["arrow_list"]) / len(self.processed_data) * 100, 1),
            "has_question_pct": round(sum(1 for p in self.processed_data if p["style"]["has_question"]) / len(self.processed_data) * 100, 1),
            "has_cta_pct": round(sum(1 for p in self.processed_data if p["style"]["has_cta"]) / len(self.processed_data) * 100, 1),
            "avg_emoji_count": round(sum(p["style"]["emoji_count"] for p in self.processed_data) / len(self.processed_data), 2),

            # Hashtag patterns
            "common_hashtags": dict(Counter(all_hashtags).most_common(20)),
            "avg_hashtags_per_post": round(sum(len(p["hashtags"]) for p in self.processed_data) / len(self.processed_data), 1),

            # CTA patterns
            "common_cta_types": dict(Counter(cta_types).most_common(5)),
        }

    def save_style_guide(self, output_file: str):
        guide = self.generate_style_guide()
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(guide, f, indent=2, ensure_ascii=False)
        print(f"Saved style guide -> {output_file}")


# ------------------------------------------------------------------
# CLI entry point
# ------------------------------------------------------------------

def main():
    print("\n" + "=" * 60)
    print("LinkedIn Post Data Processing Pipeline")
    print("=" * 60 + "\n")

    processor = LinkedInDataProcessor()

    print("Step 1: Loading raw data...")
    count = processor.load_raw_data()
    if count == 0:
        return

    print("\nStep 2: Processing posts...")
    processor.process_all()

    print("\nStep 3: Saving outputs...")
    OUTPUT_DIR.mkdir(exist_ok=True)
    processor.save_json(str(OUTPUT_DIR / "nikit_posts_processed.json"))

    print("\nStep 4: Generating style guide...")
    processor.save_style_guide(str(OUTPUT_DIR / "nikit_style_guide_updated.json"))

    # Print summary
    guide = processor.generate_style_guide()
    print("\n" + "=" * 60)
    print("STYLE GUIDE SUMMARY")
    print("=" * 60)
    print(f"  Posts analyzed:       {guide['total_posts_analyzed']}")
    print(f"  Preferred tone:       {guide['preferred_tone']}")
    print(f"  Preferred opening:    {guide['preferred_opening_style']}")
    print(f"  Avg word count:       {guide['average_post_length_words']}")
    print(f"  Avg likes:            {guide['average_engagement_likes']}")
    print(f"  Uses numbered lists:  {guide['uses_numbered_lists_pct']}%")
    print(f"  Has question CTA:     {guide['has_question_pct']}%")
    print(f"  Avg emojis/post:      {guide['avg_emoji_count']}")
    print(f"  Avg hashtags/post:    {guide['avg_hashtags_per_post']}")
    print(f"  Top hashtags: {', '.join(list(guide['common_hashtags'].keys())[:6])}")
    print(f"  Performance: {guide['performance_distribution']}")
    print("\nPhase 1 complete!")


if __name__ == "__main__":
    main()
