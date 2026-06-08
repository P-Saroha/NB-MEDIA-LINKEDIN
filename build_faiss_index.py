"""
Build FAISS Index with Real LinkedIn Posts
Converts processed LinkedIn posts into embeddings and stores in FAISS vector database
"""

import json
import numpy as np
import faiss
from pathlib import Path
from typing import List, Dict, Tuple
from sentence_transformers import SentenceTransformer
import pickle

print("\n" + "="*70)
print("Building FAISS Vector Index with Real LinkedIn Posts")
print("="*70 + "\n")

# Load processed posts
print("📥 Loading processed LinkedIn posts...")
processed_file = r"f:\Projects\NB-Media\data\nikit_posts_processed.json"

try:
    with open(processed_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    posts = data['posts']
    print(f"✅ Loaded {len(posts)} posts")
except Exception as e:
    print(f"❌ Error loading posts: {e}")
    exit(1)

# Initialize embedding model
print("\n🧠 Loading Sentence Transformers model...")
print("   (First time: ~100MB download, ~30 seconds)")

try:
    model = SentenceTransformer('all-MiniLM-L6-v2')
    print("✅ Model loaded successfully")
except Exception as e:
    print(f"❌ Error loading model: {e}")
    exit(1)

# Generate embeddings
print("\n📊 Generating embeddings for all posts...")
print("   (This may take a minute...)")

try:
    # Extract post texts
    texts = [post['text'] for post in posts]
    
    # Generate embeddings
    embeddings = model.encode(texts, show_progress_bar=True)
    embeddings = np.array(embeddings, dtype='float32')
    
    print(f"✅ Generated {len(embeddings)} embeddings")
    print(f"   Embedding dimension: {embeddings.shape[1]}")
except Exception as e:
    print(f"❌ Error generating embeddings: {e}")
    exit(1)

# Create FAISS index
print("\n🔧 Creating FAISS index...")

try:
    # Create L2 distance index
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    
    # Add embeddings to index
    index.add(embeddings)
    
    print(f"✅ FAISS index created")
    print(f"   Posts indexed: {index.ntotal}")
except Exception as e:
    print(f"❌ Error creating index: {e}")
    exit(1)

# Save index and metadata
print("\n💾 Saving index and metadata...")

try:
    # Create output directory
    index_dir = Path(r"f:\Projects\NB-Media\faiss_index")
    index_dir.mkdir(exist_ok=True)
    
    # Save FAISS index
    faiss.write_index(index, str(index_dir / "nikit_posts.index"))
    print(f"✅ FAISS index saved to: {index_dir / 'nikit_posts.index'}")
    
    # Save embeddings
    with open(index_dir / "embeddings.pkl", 'wb') as f:
        pickle.dump(embeddings, f)
    print(f"✅ Embeddings saved")
    
    # Save post metadata (without full text to save space)
    metadata = []
    for post in posts:
        metadata.append({
            'id': post['id'],
            'url': post['url'],
            'text_preview': post['text'][:200],  # First 200 chars
            'word_count': post['word_count'],
            'character_count': post['character_count'],
            'engagement': post['engagement'],
            'hashtags': post['hashtags'],
            'style': post['style'],
            'performance': post['performance']
        })
    
    with open(index_dir / "metadata.pkl", 'wb') as f:
        pickle.dump(metadata, f)
    print(f"✅ Metadata saved")
    
    # Save full posts for reference
    with open(index_dir / "posts_full.json", 'w', encoding='utf-8') as f:
        json.dump(posts, f, indent=2, ensure_ascii=False)
    print(f"✅ Full posts saved")
    
except Exception as e:
    print(f"❌ Error saving files: {e}")
    exit(1)

# Print summary
print("\n" + "="*70)
print("📈 INDEX BUILDING COMPLETE")
print("="*70)
print(f"\nIndex Statistics:")
print(f"  • Total posts indexed: {len(posts)}")
print(f"  • Embedding dimension: {dimension}")
print(f"  • Index type: L2 (Euclidean distance)")
print(f"  • Total embeddings: {index.ntotal}")

# Calculate some stats
avg_engagement = sum(p['engagement']['likes'] for p in posts) / len(posts)
print(f"\nPost Statistics:")
print(f"  • Average likes: {avg_engagement:.1f}")
print(f"  • Average word count: {sum(p['word_count'] for p in posts) / len(posts):.0f}")
print(f"  • Posts with images: {sum(1 for p in posts if p['has_image'])}")

# Test search
print(f"\n🔍 Testing FAISS search...")

try:
    test_query = "AI startup funding"
    query_embedding = model.encode([test_query], show_progress_bar=False)[0]
    query_embedding = np.array([query_embedding], dtype='float32')
    
    distances, indices = index.search(query_embedding, k=3)
    
    print(f"✅ Test search successful")
    print(f"\nTop 3 results for query: '{test_query}'")
    for i, idx in enumerate(indices[0]):
        post = posts[idx]
        print(f"  {i+1}. {post['text'][:80]}...")
        print(f"     Likes: {post['engagement']['likes']}, Distance: {distances[0][i]:.3f}")
    
except Exception as e:
    print(f"❌ Error testing search: {e}")

print("\n" + "="*70)
print("✅ FAISS Index ready for V2 RAG system!")
print("="*70)
print(f"\nNext: Update V2 to use this index")
print(f"  • api/main.py will load from: faiss_index/")
print(f"  • ui/app.py will query the index")
print(f"  • Much better style accuracy with 100 real posts!")
print("\n")
