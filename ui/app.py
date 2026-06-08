"""
Streamlit UI — LinkedIn Content Agent
Connects to the FastAPI backend at localhost:8000
"""

import json
from datetime import datetime
from typing import List

import requests
import streamlit as st

# ------------------------------------------------------------------
# Config
# ------------------------------------------------------------------

API_BASE = "http://localhost:8000/api/v2"

st.set_page_config(
    page_title="NB Media — LinkedIn Content Agent",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Session state
if "generated_posts" not in st.session_state:
    st.session_state.generated_posts = []


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def api_health() -> dict:
    try:
        r = requests.get("http://localhost:8000/health", timeout=3)
        return r.json() if r.status_code == 200 else {}
    except Exception:
        return {}


def call_generate(topic: str, context: str, provider: str = "google") -> dict:
    r = requests.post(
        f"{API_BASE}/generate-post",
        json={"topic": topic, "context": context, "llm_provider": provider, "style_guided": True},
        timeout=60,
    )
    r.raise_for_status()
    return r.json()


def call_research(num: int) -> list:
    r = requests.get(f"{API_BASE}/research-topics", params={"num_topics": num}, timeout=20)
    r.raise_for_status()
    return r.json().get("topics", [])


def call_batch(num: int, provider: str = "google") -> list:
    r = requests.post(
        f"{API_BASE}/batch-generate",
        json={"num_posts": num, "llm_provider": provider},
        timeout=180,
    )
    r.raise_for_status()
    return r.json().get("posts", [])


# ------------------------------------------------------------------
# Sidebar
# ------------------------------------------------------------------

with st.sidebar:
    st.image("https://media.licdn.com/dms/image/v2/D5603AQHVTKHGTUycew/profile-displayphoto-shrink_800_800/profile-displayphoto-shrink_800_800/0/1718200724277", width=80)
    st.title("NB Media\nContent Agent")
    st.markdown("**Nikit Bassi's LinkedIn voice,\npowered by Gemini 2.5 Flash + FAISS RAG**")
    st.markdown("---")

    # Health check
    health = api_health()
    if health:
        components = health.get("components", {})
        st.success("API Online")
        st.caption(f"Model: {health.get('version', '2.0')}")
        for k, v in components.items():
            status_label = "Ready" if "ready" in v or "running" in v or "configured" in v else "Warning"
            st.caption(f"{status_label} - {k}: {v}")
    else:
        st.error("API Offline\nStart with: `uvicorn api.main:app --port 8000`")

    st.markdown("---")
    provider = st.selectbox("LLM Provider", ["google"], help="Gemini 2.5 Flash")

    if st.session_state.generated_posts:
        st.markdown(f"**Posts this session:** {len(st.session_state.generated_posts)}")

# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------

st.title("LinkedIn Content Agent")
st.caption("Generate authentic LinkedIn posts in Nikit Bassi's exact style")

tab1, tab2, tab3, tab4 = st.tabs(
    ["Generate Post", "Research Topics", "Batch Generate", "Session Stats"]
)

# ── Tab 1: Single post generation ──────────────────────────────────
with tab1:
    st.header("Generate a Post")

    col1, col2 = st.columns([3, 1])
    with col1:
        topic = st.text_input(
            "Topic *",
            placeholder="e.g. Why most AI automation businesses fail",
        )
    with col2:
        st.write("")
        st.write("")
        generate_btn = st.button("Generate", type="primary", use_container_width=True)

    context = st.text_area(
        "Additional context (optional)",
        placeholder="e.g. Focus on the Indian startup ecosystem, mention NB Media's experience",
        height=80,
    )

    if generate_btn:
        if not topic.strip():
            st.warning("Please enter a topic.")
        else:
            with st.spinner("Retrieving similar posts from FAISS index + generating with Gemini 2.5 Flash..."):
                try:
                    data = call_generate(topic, context, provider)
                    st.session_state.generated_posts.append(
                        {"timestamp": datetime.now().isoformat(), "topic": topic, "data": data}
                    )
                    st.success("Post generated!")

                    # Display post
                    st.markdown("### Generated Post")
                    with st.container():
                        st.markdown(data["post_content"])

                    c1, c2 = st.columns(2)
                    with c1:
                        st.subheader("Hashtags")
                        st.code(" ".join(data["hashtags"]) if data["hashtags"] else "(none extracted)")
                    with c2:
                        st.subheader("Image Ideas")
                        for idea in data.get("image_ideas", []):
                            st.markdown(f"- {idea}")

                    mc1, mc2, mc3 = st.columns(3)
                    mc1.metric("Characters", data["length"])
                    mc2.metric("Model", data["generation_model"])
                    mc3.metric("RAG-guided", "Yes" if data["style_guided"] else "No")

                    st.download_button(
                        "Download as JSON",
                        json.dumps(data, indent=2, ensure_ascii=False),
                        file_name=f"post_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json",
                    )
                except Exception as e:
                    st.error(f"Generation failed: {e}")

# ── Tab 2: Research topics ─────────────────────────────────────────
with tab2:
    st.header("Research Trending Topics")
    st.caption("Pulls from Google News RSS + curated Nikit-niche topics")

    num_topics = st.slider("Number of topics", 3, 15, 5)
    research_btn = st.button("Research Topics", type="primary")

    if research_btn:
        with st.spinner("Fetching trending topics..."):
            try:
                topics = call_research(num_topics)
                st.success(f"Found {len(topics)} topics")

                for i, t in enumerate(topics, 1):
                    with st.expander(f"{i}. {t.get('title', 'N/A')}", expanded=(i <= 2)):
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.markdown(f"**Description:** {t.get('description', '')}")
                            st.caption(f"Source: {t.get('source', '?')} | Category: {t.get('category', '?')}")
                        with col2:
                            st.metric("Relevance", f"{int(t.get('relevance', 0) * 100)}%")

                        if t.get("angles"):
                            st.markdown("**Content Angles:**")
                            for angle in t["angles"][:3]:
                                st.markdown(f"- **{angle['angle'].replace('_', ' ').title()}:** {angle['hook']}")

                        if st.button(f"Generate post for topic {i}", key=f"gen_{i}"):
                            with st.spinner("Generating..."):
                                try:
                                    result = call_generate(t["title"], t.get("description", ""), provider)
                                    st.session_state.generated_posts.append(
                                        {"timestamp": datetime.now().isoformat(), "topic": t["title"], "data": result}
                                    )
                                    st.success("Post generated! See Session Stats tab.")
                                    with st.container():
                                        st.markdown(result["post_content"])
                                except Exception as e:
                                    st.error(str(e))
            except Exception as e:
                st.error(f"Research failed: {e}")

# ── Tab 3: Batch generate ──────────────────────────────────────────
with tab3:
    st.header("Batch Generate Posts")
    st.caption("Auto-generates multiple posts from trending topics in one go")

    batch_n = st.slider("Number of posts", 2, 8, 3)
    batch_btn = st.button("Generate Batch", type="primary")

    if batch_btn:
        with st.spinner(f"Generating {batch_n} posts... (this may take ~{batch_n * 15}s)"):
            try:
                posts = call_batch(batch_n, provider)
                ok_posts = [p for p in posts if "error" not in p]
                st.success(f"Generated {len(ok_posts)} / {len(posts)} posts")

                for i, post in enumerate(posts, 1):
                    if "error" in post:
                        st.error(f"Post {i} failed: {post['error']}")
                        continue
                    with st.expander(f"Post {i}: {post.get('topic', '')[:60]}...", expanded=(i == 1)):
                        with st.container():
                            st.markdown(post["post_content"])
                        st.code(" ".join(post.get("hashtags", [])), language="text")
                        for idea in post.get("image_ideas", []):
                            st.caption(f"Image Idea: {idea}")
                        st.download_button(
                            "Download",
                            json.dumps(post, indent=2, ensure_ascii=False),
                            file_name=f"batch_post_{i}.json",
                            mime="application/json",
                            key=f"dl_{i}",
                        )
                        st.session_state.generated_posts.append(
                            {"timestamp": datetime.now().isoformat(), "topic": post.get("topic", ""), "data": post}
                        )
            except Exception as e:
                st.error(f"Batch generation failed: {e}")

# ── Tab 4: Session stats ───────────────────────────────────────────
with tab4:
    st.header("Session Statistics")

    if not st.session_state.generated_posts:
        st.info("No posts generated yet this session.")
    else:
        total = len(st.session_state.generated_posts)
        total_chars = sum(p["data"].get("length", 0) for p in st.session_state.generated_posts)
        avg_chars = total_chars // total if total else 0

        c1, c2, c3 = st.columns(3)
        c1.metric("Posts Generated", total)
        c2.metric("Total Characters", f"{total_chars:,}")
        c3.metric("Avg Post Length", f"{avg_chars} chars")

        st.markdown("### Recent Posts")
        for entry in reversed(st.session_state.generated_posts[-10:]):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"**{entry['topic'][:70]}**")
                preview = entry["data"].get("post_content", "")[:120]
                st.caption(preview + "...")
            with col2:
                ts = entry["timestamp"].split("T")[0]
                st.caption(ts)
            st.sidebar.markdown("---") if False else st.write("")

# ------------------------------------------------------------------
# Footer
# ------------------------------------------------------------------
st.markdown("---")
st.caption(
    "NB Media LinkedIn Content Agent v2.0 · "
    "Gemini 2.5 Flash + FAISS RAG · "
    "132 real Nikit Bassi posts as training data"
)