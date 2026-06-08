"""
FastAPI Backend — LinkedIn Content Agent v2
REST API powered by Gemini 2.5 Flash + FAISS RAG
"""

from datetime import datetime
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agents.post_generator import generate_linkedin_post, generate_image_ideas
from agents.topic_research_agent import get_trending_topics

# ------------------------------------------------------------------
# App setup
# ------------------------------------------------------------------

app = FastAPI(
    title="LinkedIn Content Agent API",
    description="Generates LinkedIn posts in Nikit Bassi's style using Gemini 2.5 Flash + FAISS RAG",
    version="2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------------
# Request / Response models
# ------------------------------------------------------------------


class PostRequest(BaseModel):
    topic: str
    context: Optional[str] = ""
    style_guided: bool = True
    llm_provider: str = "google"


class PostResponse(BaseModel):
    post_content: str
    topic: str
    hashtags: List[str]
    image_ideas: List[str]
    length: int
    generation_model: str
    style_guided: bool


class TopicResponse(BaseModel):
    topics: List[Dict]
    total_count: int
    timestamp: str


class BatchRequest(BaseModel):
    num_posts: int = 5
    llm_provider: str = "google"


# ------------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------------


@app.get("/", tags=["Info"])
async def root():
    return {
        "name": "LinkedIn Content Agent API",
        "version": "2.0",
        "model": "gemini-2.5-flash",
        "description": "Generates LinkedIn posts in Nikit Bassi's style using FAISS RAG",
        "docs": "/docs",
        "status": "running",
    }


@app.get("/health", tags=["Info"])
async def health():
    import os
    from pathlib import Path

    faiss_ready = Path("faiss_index/faiss_index.bin").exists()
    data_ready = Path("data/nikit_posts_processed.json").exists()
    api_key_set = bool(os.getenv("GEMINI_API_KEY"))

    return {
        "status": "healthy",
        "version": "2.0",
        "components": {
            "api": "running",
            "faiss_index": "ready" if faiss_ready else "missing — run Phase 2",
            "training_data": "ready" if data_ready else "missing — run Phase 1",
            "gemini_api_key": "configured" if api_key_set else "missing — set GEMINI_API_KEY in .env",
        },
    }


@app.post("/api/v2/generate-post", response_model=PostResponse, tags=["Generation"])
async def generate_post(request: PostRequest):
    """Generate a single LinkedIn post from a topic."""
    if not request.topic.strip():
        raise HTTPException(status_code=400, detail="topic cannot be empty")
    try:
        result = generate_linkedin_post(
            topic=request.topic,
            context=request.context or "",
            llm_provider=request.llm_provider,
        )
        image_ideas = generate_image_ideas(result["post_content"], request.topic)
        return PostResponse(
            post_content=result["post_content"],
            topic=result["topic"],
            hashtags=result["hashtags"],
            image_ideas=image_ideas,
            length=result["length"],
            generation_model=result["generation_model"],
            style_guided=result["style_guided"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v2/research-topics", response_model=TopicResponse, tags=["Research"])
async def research_topics(num_topics: int = 5):
    """Discover trending topics relevant to Nikit's content niche."""
    try:
        topics = get_trending_topics(min(num_topics, 20))
        return TopicResponse(
            topics=topics,
            total_count=len(topics),
            timestamp=datetime.now().isoformat(),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v2/batch-generate", tags=["Generation"])
async def batch_generate(request: BatchRequest):
    """Auto-generate multiple posts from trending topics."""
    try:
        topics = get_trending_topics(request.num_posts)
        posts = []
        for topic_data in topics[: request.num_posts]:
            try:
                result = generate_linkedin_post(
                    topic=topic_data.get("title", ""),
                    context=topic_data.get("description", ""),
                    llm_provider=request.llm_provider,
                )
                image_ideas = generate_image_ideas(result["post_content"], topic_data.get("title", ""))
                posts.append(
                    {
                        "topic": result["topic"],
                        "post_content": result["post_content"],
                        "hashtags": result["hashtags"],
                        "image_ideas": image_ideas,
                        "source_topic": {
                            "title": topic_data.get("title"),
                            "category": topic_data.get("category"),
                            "relevance": topic_data.get("relevance"),
                        },
                    }
                )
            except Exception as e:
                posts.append({"topic": topic_data.get("title", ""), "error": str(e)})

        return {
            "status": "success",
            "posts_generated": len([p for p in posts if "error" not in p]),
            "posts": posts,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v2/stats", tags=["Stats"])
async def get_stats():
    """API usage stats."""
    from pathlib import Path
    import json

    post_count = 0
    try:
        with open("data/nikit_posts_processed.json", encoding="utf-8") as f:
            data = json.load(f)
        post_count = data.get("metadata", {}).get("total_posts", 0)
    except Exception:
        pass

    return {
        "training_posts": post_count,
        "model": "gemini-2.5-flash",
        "faiss_index": Path("faiss_index/faiss_index.bin").exists(),
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/api/v2/config", tags=["Config"])
async def get_config():
    import os
    return {
        "gemini_api_configured": bool(os.getenv("GEMINI_API_KEY")),
        "faiss_index_path": "faiss_index/faiss_index.bin",
        "training_data_path": "data/nikit_posts_processed.json",
        "model": "gemini-2.5-flash",
    }


# ------------------------------------------------------------------
# Run directly
# ------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
