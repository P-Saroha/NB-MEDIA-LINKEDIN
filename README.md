# LinkedIn Content Creation Agent (Nikit Bassi Style)

## Overview

This project is an AI-powered LinkedIn Content Creation Agent that generates posts in the writing style of Nikit Bassi (Founder of NB Media).

The system uses Retrieval-Augmented Generation (RAG) instead of model fine-tuning. Historical LinkedIn posts are processed, embedded, indexed with FAISS, and retrieved during generation to guide Gemini 2.5 Flash.

---

## Features

### 1. Style Learning (RAG)

* Processed 132 original Nikit Bassi LinkedIn posts
* Generated embeddings using Sentence Transformers
* Stored embeddings in FAISS
* Retrieves similar posts during generation

### 2. Style Analysis

Automatically extracts:

* Writing patterns
* Hook structures
* CTA formats
* Topic categories
* Formatting preferences

Outputs a structured style profile.

### 3. User Topic Workflow

Input:

* User enters a topic

Process:

* Retrieve similar posts from FAISS
* Load style profile
* Generate LinkedIn post using Gemini 2.5 Flash

Output:

* LinkedIn post
* Hashtags
* Image ideas

### 4. Auto Research Workflow

Uses Google News RSS feeds to discover:

* AI
* Startups
* Business
* Marketing
* Automation

Outputs:

* Trending topics
* Content opportunities
* LinkedIn angles

### 5. Image Idea Generator

For each generated post:

* Carousel ideas
* Visual concepts
* Content structure suggestions

---

## Tech Stack

* Python
* FastAPI
* Streamlit
* Google Gemini 2.5 Flash
* Sentence Transformers
* FAISS
* Pandas
* Pydantic

---

## Project Structure

linkedin_agent/

├── agents/
├── api/
├── config/
├── data/
├── data_processing/
├── embeddings/
├── faiss_index/
├── ingestion/
├── scraper/
├── ui/
├── requirements.txt
└── README.md

---

## Setup

### 1. Clone Repository

git clone <repo_url>

cd NB-MEDIA-LINKEDIN

### 2. Create Virtual Environment

python -m venv myenv

myenv\Scripts\activate

### 3. Install Dependencies

pip install -r requirements.txt

### 4. Configure Environment Variables

Create .env

GEMINI_API_KEY=YOUR_API_KEY

### 5. Run FastAPI

uvicorn api.main:app --reload

API:

http://localhost:8000/docs

### 6. Run Streamlit

streamlit run ui/app.py

UI:

http://localhost:8501

---

## Workflow

Dataset
↓
Data Processing
↓
Style Analysis
↓
Embeddings
↓
FAISS Index
↓
Retriever
↓
Gemini 2.5 Flash
↓
LinkedIn Post

---

## Example Output

Input Topic:

"Why most AI automation agencies fail"

Output:

* LinkedIn post
* Hashtags
* Image ideas

Generated using:

* RAG retrieval
* Style profile
* Gemini 2.5 Flash

---

## Assignment Requirements Covered

| Requirement              | Status |
| ------------------------ | ------ |
| Style Learning           | ✅      |
| User Input Workflow      | ✅      |
| Auto Research Workflow   | ✅      |
| LinkedIn Post Generation | ✅      |
| Image Ideas              | ✅      |
| FastAPI API              | ✅      |
| Streamlit UI             | ✅      |

---

## Future Improvements

* LinkedIn auto-posting
* Analytics dashboard
* Content calendar
* A/B testing of hooks
* Advanced engagement prediction
