"""
Component verification script — run with: python verify_components.py
Tests every module without starting a server.
"""
import os, sys, ast, pathlib, json, traceback

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

tests = {}

# ── 1. FAISS pipeline ────────────────────────────────────────────
try:
    from ingestion.faiss_pipeline import LinkedInFaissPipeline
    p = LinkedInFaissPipeline()
    results = p.search("AI automation agency", top_k=3)
    assert len(results) == 3
    assert len(results[0]["content"]) > 50
    tests["faiss_search"] = ("PASS", f"{len(results)} results, top sim={round(results[0]['similarity_score'],3)}")
except Exception as e:
    tests["faiss_search"] = ("FAIL", str(e)[:120])

# ── 2. Style retriever ───────────────────────────────────────────
try:
    from agents.style_retriever import StyleRetriever, StyleFactory
    sr = StyleRetriever()
    guide = sr.get_style_guide_for_topic("building an AI team")
    assert guide["similar_post_count"] > 0
    assert len(guide["generation_prompt_additions"]) > 200
    sf = StyleFactory()
    prompt = sf.create_generation_prompt("AI tools for agencies")
    assert "Nikit Bassi" in prompt
    assert len(prompt) > 500
    tests["style_retriever"] = ("PASS", f"retrieved {guide['similar_post_count']} posts, prompt={len(prompt)} chars")
except Exception as e:
    tests["style_retriever"] = ("FAIL", str(e)[:120])

# ── 3. Topic research agent ──────────────────────────────────────
try:
    from agents.topic_research_agent import get_trending_topics
    topics = get_trending_topics(5)
    assert len(topics) >= 3
    assert all("title" in t for t in topics)
    assert all("angles" in t for t in topics)
    assert all(len(t["angles"]) == 5 for t in topics)
    tests["topic_research"] = ("PASS", f"{len(topics)} topics, first='{topics[0]['title'][:45]}'")
except Exception as e:
    tests["topic_research"] = ("FAIL", str(e)[:120])

# ── 4. Post generator (structure + demo fallback) ────────────────
try:
    from agents.post_generator import PostGeneratorAgent, generate_image_ideas
    # Test demo mode (no API key needed)
    agent = PostGeneratorAgent.__new__(PostGeneratorAgent)
    agent.client = None
    agent._style_factory = None
    agent.llm_provider = "demo"
    demo = agent._demo_post("AI automation")
    assert len(demo) > 100
    hashtags = agent._extract_hashtags(demo)
    assert len(hashtags) >= 2
    ideas = generate_image_ideas("We built an AI tool that saves 200 hours monthly", "AI tools")
    assert len(ideas) >= 2
    tests["post_generator"] = ("PASS", f"demo={len(demo)} chars, {len(hashtags)} hashtags, {len(ideas)} image ideas")
except Exception as e:
    tests["post_generator"] = ("FAIL", str(e)[:120])

# ── 5. Gemini API key present ────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv()
    key = os.getenv("GEMINI_API_KEY", "")
    placeholder = "your_gemini_api_key_here"
    valid = bool(key) and key != placeholder and len(key) > 10
    tests["gemini_key"] = ("PASS" if valid else "WARN", f"key={'set (len='+str(len(key))+')' if valid else 'NOT SET or placeholder'}")
except Exception as e:
    tests["gemini_key"] = ("FAIL", str(e)[:80])

# ── 6. Gemini generation (only if key valid) ─────────────────────
if tests.get("gemini_key", ("",))[0] == "PASS":
    try:
        from agents.post_generator import generate_linkedin_post
        result = generate_linkedin_post(topic="AI tools for agencies", context="focus on time savings")
        assert result["generation_model"] != "demo", "fell back to demo mode"
        assert result["length"] > 300, f"post too short: {result['length']}"
        assert len(result["hashtags"]) >= 1
        tests["gemini_generation"] = ("PASS", f"model={result['generation_model']}, len={result['length']}, hashtags={result['hashtags']}")
    except Exception as e:
        tests["gemini_generation"] = ("FAIL", str(e)[:120])
else:
    tests["gemini_generation"] = ("SKIP", "No valid GEMINI_API_KEY — set key to test live generation")

# ── 7. FastAPI app loads correctly ──────────────────────────────
try:
    from api.main import app
    routes = [r.path for r in app.routes]
    required = ["/health", "/api/v2/generate-post", "/api/v2/research-topics", "/api/v2/batch-generate", "/api/v2/stats", "/api/v2/config"]
    missing = [r for r in required if r not in routes]
    assert not missing, f"missing routes: {missing}"
    tests["fastapi_app"] = ("PASS", f"{len(routes)} routes, all required endpoints present")
except Exception as e:
    tests["fastapi_app"] = ("FAIL", str(e)[:120])

# ── 8. FastAPI endpoint logic (TestClient, no server needed) ─────
try:
    from fastapi.testclient import TestClient
    from api.main import app
    client = TestClient(app, raise_server_exceptions=False)

    # Health
    r = client.get("/health")
    assert r.status_code == 200
    h = r.json()
    assert h["status"] == "healthy"

    # Stats
    r = client.get("/api/v2/stats")
    assert r.status_code == 200

    # Config
    r = client.get("/api/v2/config")
    assert r.status_code == 200
    assert "gemini_api_configured" in r.json()

    # Research topics
    r = client.get("/api/v2/research-topics", params={"num_topics": 3})
    assert r.status_code == 200
    data = r.json()
    assert data["total_count"] >= 3
    assert len(data["topics"]) >= 3

    # Generate post (will use demo or gemini depending on key)
    r = client.post("/api/v2/generate-post", json={"topic": "AI productivity tools", "context": "", "style_guided": True})
    assert r.status_code == 200
    post_data = r.json()
    assert "post_content" in post_data
    assert post_data["length"] > 100
    assert isinstance(post_data["hashtags"], list)
    assert isinstance(post_data["image_ideas"], list) and len(post_data["image_ideas"]) >= 1

    tests["fastapi_endpoints"] = ("PASS", f"health/stats/config/research/generate all 200, post_len={post_data['length']}, model={post_data['generation_model']}")
except Exception as e:
    tests["fastapi_endpoints"] = ("FAIL", traceback.format_exc()[-200:])

# ── 9. Batch generate endpoint ───────────────────────────────────
try:
    from fastapi.testclient import TestClient
    from api.main import app
    client = TestClient(app, raise_server_exceptions=False)
    r = client.post("/api/v2/batch-generate", json={"num_posts": 2, "llm_provider": "google"})
    assert r.status_code == 200
    d = r.json()
    assert "posts" in d
    assert d["posts_generated"] >= 1
    tests["batch_generate"] = ("PASS", f"generated {d['posts_generated']}/{len(d['posts'])} posts")
except Exception as e:
    tests["batch_generate"] = ("FAIL", str(e)[:120])

# ── 10. Streamlit UI syntax ──────────────────────────────────────
try:
    with open("ui/app.py", encoding="utf-8") as f:
        src = f.read()
    ast.parse(src)
    line_count = src.count("\n")
    tests["streamlit_syntax"] = ("PASS", f"syntax valid, {line_count} lines")
except Exception as e:
    tests["streamlit_syntax"] = ("FAIL", str(e)[:120])

# ── 11. Data files ───────────────────────────────────────────────
data_files = {
    "processed_data":  "data/nikit_posts_processed.json",
    "style_guide":     "data/nikit_style_guide_updated.json",
    "faiss_index_bin": "faiss_index/faiss_index.bin",
    "faiss_metadata":  "faiss_index/metadata.pkl",
}
for key, path in data_files.items():
    exists = pathlib.Path(path).exists()
    size = pathlib.Path(path).stat().st_size if exists else 0
    tests[key] = ("PASS" if exists else "FAIL", f"{path} ({size//1024}KB)")

# ── 12. Processed data integrity ────────────────────────────────
try:
    with open("data/nikit_posts_processed.json", encoding="utf-8") as f:
        d = json.load(f)
    posts = d["posts"]
    assert len(posts) == 132, f"expected 132, got {len(posts)}"
    assert all("text" in p and "engagement" in p for p in posts)
    avg_likes = sum(p["engagement"]["likes"] for p in posts) / len(posts)
    tests["data_integrity"] = ("PASS", f"{len(posts)} posts, avg_likes={round(avg_likes,1)}")
except Exception as e:
    tests["data_integrity"] = ("FAIL", str(e)[:120])

# ── Print results ────────────────────────────────────────────────
print()
print("=" * 70)
print("COMPONENT VERIFICATION RESULTS")
print("=" * 70)
passes = fails = skips = 0
for name, (status, msg) in tests.items():
    icon = {"PASS": "✓", "FAIL": "✗", "WARN": "!", "SKIP": "-"}.get(status, "?")
    print(f"  {icon} [{status:4}] {name:<28} {msg[:55]}")
    if status == "PASS": passes += 1
    elif status == "FAIL": fails += 1
    elif status == "SKIP": skips += 1

print()
print(f"  Total: {len(tests)}  |  Pass: {passes}  |  Fail: {fails}  |  Skip: {skips}")
print("=" * 70)

# Save results for report
with open("verification_results.json", "w", encoding="utf-8") as f:
    json.dump(tests, f, indent=2)
print("  Saved -> verification_results.json")
