# LinkedIn Content Creation Agent
### Generating Posts in the Style of Nikit Bassi (Founder, NB Media)

---

## Overview

An AI-powered LinkedIn Content Creation Agent that generates posts mimicking the writing style of **Nikit Bassi**, Founder of NB Media.

Rather than fine-tuning a model, the system uses **Retrieval-Augmented Generation (RAG)**:
- 132 historical LinkedIn posts are processed, embedded, and indexed using **FAISS**
- Relevant posts are retrieved at generation time to guide **Gemini 2.5 Flash**
- A structured style profile captures tone, hooks, CTAs, and formatting patterns

---

## Features

### 1. Style Learning via RAG
- Processes 132 original Nikit Bassi LinkedIn posts
- Generates embeddings using **Sentence Transformers**
- Stores and queries embeddings via **FAISS**
- Retrieves contextually similar posts during generation

### 2. Automatic Style Analysis
Extracts and outputs a structured style profile covering:
- Writing patterns and tone
- Hook structures
- CTA formats
- Topic categories
- Formatting preferences

### 3. User Topic Workflow
| Stage | Description |
|-------|-------------|
| **Input** | User enters a topic |
| **Retrieval** | Similar posts fetched from FAISS index |
| **Context** | Style profile loaded |
| **Generation** | Post created via Gemini 2.5 Flash |
| **Output** | LinkedIn post + hashtags + image ideas |

### 4. Auto Research Workflow
Discovers trending topics via **Google News RSS feeds** across:
- AI & Automation
- Startups & Business
- Marketing

Outputs trending topics, content opportunities, and LinkedIn-ready angles.

### 5. Image Idea Generator
For every generated post, suggests:
- Carousel ideas
- Visual concepts
- Content structure recommendations

---

## Tech Stack

| Category | Tools |
|----------|-------|
| Language | Python |
| Backend API | FastAPI |
| Frontend UI | Streamlit |
| LLM | Google Gemini 2.5 Flash |
| Embeddings | Sentence Transformers |
| Vector Store | FAISS |
| Data | Pandas |
| Validation | Pydantic |

---

## Project Structure

```
linkedin_agent/
├── agents/              # Core agent logic
├── api/                 # FastAPI routes and endpoints
├── config/              # Configuration and environment settings
├── data/                # Raw LinkedIn post dataset
├── data_processing/     # Post cleaning and preprocessing
├── embeddings/          # Embedding generation scripts
├── faiss_index/         # Stored FAISS vector index
├── ingestion/           # Data ingestion pipeline
├── scraper/             # Google News RSS scraper
├── ui/                  # Streamlit app
├── requirements.txt
└── README.md
```

---

## Setup & Installation

### 1. Clone the Repository
```bash
git clone <repo_url>
cd NB-MEDIA-LINKEDIN
```

### 2. Create a Virtual Environment
```bash
python -m venv myenv
myenv\Scripts\activate        # Windows
# source myenv/bin/activate   # macOS/Linux
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a `.env` file in the project root:
```env
GEMINI_API_KEY=your_api_key_here
```

### 5. Start the FastAPI Backend
```bash
uvicorn api.main:app --reload
```
API docs available at: `http://localhost:8000/docs`

### 6. Launch the Streamlit UI
```bash
streamlit run ui/app.py
```
UI available at: `http://localhost:8501`

---

## System Workflow

```
Dataset (132 LinkedIn Posts)
        ↓
  Data Processing
        ↓
  Style Analysis  ──────────────────────────┐
        ↓                                   │
  Embeddings Generation                     │
        ↓                                   │
   FAISS Index                              │
        ↓                                   │
   RAG Retriever  ←──── User Topic Input    │
        ↓                                   │
  Gemini 2.5 Flash ←── Style Profile ───────┘
        ↓
  LinkedIn Post + Hashtags + Image Ideas
```

---

## Example Output

**Input Topic:**
> *"Why most AI automation agencies fail"*

**Generated Output:**
- ✅ LinkedIn post (in Nikit Bassi's style)
- ✅ Relevant hashtags
- ✅ Image/carousel ideas

**Powered by:** RAG retrieval + Style profile + Gemini 2.5 Flash

---

## Assignment Requirements

| Requirement | Status |
|-------------|--------|
| Style Learning (RAG) | ✅ Completed |
| User Input Workflow | ✅ Completed |
| Auto Research Workflow | ✅ Completed |
| LinkedIn Post Generation | ✅ Completed |
| Image Idea Generation | ✅ Completed |
| FastAPI Backend | ✅ Completed |
| Streamlit UI | ✅ Completed |

---

## Future Improvements

- [ ] LinkedIn auto-posting integration
- [ ] Analytics dashboard for post performance
- [ ] Content calendar with scheduling
- [ ] A/B testing of hook variants
- [ ] Advanced engagement prediction model

