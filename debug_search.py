#!/usr/bin/env python3
"""
IMMEDIATE DEBUG: Find why wudu search returns 0 results
This script will pinpoint the exact issue in your search pipeline
"""

import numpy as np
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

try:
    from sentence_transformers import SentenceTransformer
    from config.database import get_db_manager
    print("✅ Imports successful")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)


def debug_wudu_search():
    """Debug the specific 'wudu' search issue step by step"""
    print("🔍 DEBUGGING WUDU SEARCH - STEP BY STEP")
    print("=" * 60)
    
    # Step 1: Load model and generate query embedding
    print("\n1️⃣ LOADING MODEL AND GENERATING QUERY EMBEDDING")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    query = "wudu"
    query_embedding = model.encode([query])[0].tolist()
    
    print(f"✅ Query: '{query}'")
    print(f"✅ Query embedding length: {len(query_embedding)}")
    print(f"✅ Query embedding sample: {query_embedding[:5]}")
    print(f"✅ Query embedding type: {type(query_embedding[0])}")
    
    # Step 2: Check database connection and document count
    print("\n2️⃣ CHECKING DATABASE")
    db = get_db_manager()
    
    # Total documents
    total_docs = db.execute_query("SELECT COUNT(*) as count FROM documents", fetch=True)[0]['count']
    print(f"✅ Total documents in database: {total_docs:,}")
    
    # Documents with embeddings
    with_embeddings = db.execute_query(
        "SELECT COUNT(*) as count FROM documents WHERE embedding_json IS NOT NULL", 
        fetch=True
    )[0]['count']
    print(f"✅ Documents with embeddings: {with_embeddings:,}")
    
    # Documents with valid embedding length
    valid_embeddings = db.execute_query(
        "SELECT COUNT(*) as count FROM documents WHERE jsonb_array_length(embedding_json) = 384", 
        fetch=True
    )[0]['count']
    print(f"✅ Documents with 384-dim embeddings: {valid_embeddings:,}")
    
    # Step 3: Get the EXACT query that's being used in search
    print("\n3️⃣ TESTING EXACT SEARCH QUERY")
    
    # This is the exact query from your search service
    search_query = """
    SELECT 
        id, doc_id, text, source, category, title, 
        embedding_json, metadata
    FROM documents 
    WHERE text IS NOT NULL 
    AND embedding_json IS NOT NULL
    AND length(text) > 10
    LIMIT 2000
    """
    
    print(f"🔍 Executing search query...")
    search_docs = db.execute_query(search_query, fetch=True)
    print(f"✅ Retrieved {len(search_docs)} documents from search query")
    
    # Step 4: Test embeddings from retrieved documents
    print("\n4️⃣ TESTING RETRIEVED EMBEDDINGS")
    
    valid_count = 0
    embedding_issues = []
    similarity_scores = []
    
    def cosine_similarity(vec1, vec2):
        """Test cosine similarity calculation"""
        try:
            v1 = np.array(vec1, dtype=np.float32)
            v2 = np.array(vec2, dtype=np.float32)
            
            norm_v1 = np.linalg.norm(v1)
            norm_v2 = np.linalg.norm(v2)
            
            if norm_v1 == 0 or norm_v2 == 0:
                return 0.0
            
            dot_product = np.dot(v1, v2)
            similarity = dot_product / (norm_v1 * norm_v2)
            
            # Return raw cosine similarity (-1 to 1)
            return float(similarity)
            
        except Exception as e:
            return None
    
    print("Testing first 20 documents:")
    for i, doc in enumerate(search_docs[:20]):
        doc_embedding = doc['embedding_json']
        
        # Check embedding validity
        if not isinstance(doc_embedding, list):
            embedding_issues.append(f"Doc {doc['id']}: embedding is {type(doc_embedding)}, not list")
            continue
            
        if len(doc_embedding) != 384:
            embedding_issues.append(f"Doc {doc['id']}: embedding length is {len(doc_embedding)}, not 384")
            continue
            
        # Test similarity calculation
        similarity = cosine_similarity(query_embedding, doc_embedding)
        
        if similarity is None:
            embedding_issues.append(f"Doc {doc['id']}: similarity calculation failed")
            continue
            
        valid_count += 1
        similarity_scores.append(similarity)
        
        # Show first few results
        if i < 5:
            text_preview = doc['text'][:80] if doc['text'] else 'No text'
            print(f"  {i+1}. Doc {doc['id']} [{doc['category']}]: similarity={similarity:.6f}")
            print(f"      Text: {text_preview}...")
    
    print(f"\n✅ Valid embeddings in sample: {valid_count}/20")
    
    if embedding_issues:
        print(f"\n❌ Embedding Issues Found:")
        for issue in embedding_issues[:5]:  # Show first 5 issues
            print(f"  • {issue}")
    
    # Step 5: Analyze similarity scores
    print("\n5️⃣ ANALYZING SIMILARITY SCORES")
    
    if similarity_scores:
        print(f"📊 Similarity Statistics:")
        print(f"  • Count: {len(similarity_scores)}")
        print(f"  • Min: {min(similarity_scores):.6f}")
        print(f"  • Max: {max(similarity_scores):.6f}")
        print(f"  • Average: {np.mean(similarity_scores):.6f}")
        print(f"  • Median: {np.median(similarity_scores):.6f}")
        
        # Test different thresholds
        thresholds = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5]
        print(f"\n🎯 Results by threshold (from {len(similarity_scores)} scores):")
        for threshold in thresholds:
            count = len([s for s in similarity_scores if s >= threshold])
            print(f"  • >= {threshold}: {count} results")
        
        # Show top similarities
        top_scores = sorted(similarity_scores, reverse=True)[:10]
        print(f"\n🏆 Top 10 similarity scores: {[f'{s:.6f}' for s in top_scores]}")
        
    else:
        print("❌ No valid similarity scores calculated!")
    
    # Step 6: Test with documents that should match "wudu"
    print("\n6️⃣ TESTING WITH WUDU-RELATED DOCUMENTS")
    
    wudu_query = """
    SELECT id, text, embedding_json, category
    FROM documents 
    WHERE (
        LOWER(text) LIKE '%wudu%' OR 
        LOWER(text) LIKE '%ablution%' OR
        LOWER(text) LIKE '%purification%'
    )
    AND embedding_json IS NOT NULL
    AND jsonb_array_length(embedding_json) = 384
    LIMIT 10
    """
    
    wudu_docs = db.execute_query(wudu_query, fetch=True)
    print(f"✅ Found {len(wudu_docs)} documents containing wudu/ablution terms")
    
    if wudu_docs:
        print("Testing similarity with wudu-related documents:")
        for i, doc in enumerate(wudu_docs[:5]):
            similarity = cosine_similarity(query_embedding, doc['embedding_json'])
            text_preview = doc['text'][:100] if doc['text'] else 'No text'
            print(f"  {i+1}. Doc {doc['id']} [{doc['category']}]: similarity={similarity:.6f}")
            print(f"      Text: {text_preview}...")
    
    # Step 7: Test with different query variations
    print("\n7️⃣ TESTING QUERY VARIATIONS")
    
    test_queries = ["wudu", "ablution", "purification", "washing", "cleanliness"]
    
    for test_query in test_queries:
        test_embedding = model.encode([test_query])[0].tolist()
        
        # Test with first valid document
        if search_docs and valid_count > 0:
            # Find first valid document
            for doc in search_docs[:10]:
                if isinstance(doc['embedding_json'], list) and len(doc['embedding_json']) == 384:
                    similarity = cosine_similarity(test_embedding, doc['embedding_json'])
                    print(f"  '{test_query}' vs Doc {doc['id']}: {similarity:.6f}")
                    break
    
    return {
        'total_docs': total_docs,
        'valid_embeddings': valid_count,
        'similarity_scores': similarity_scores,
        'embedding_issues': embedding_issues
    }


def suggest_immediate_fixes(debug_results):
    """Suggest immediate fixes based on debug results"""
    print("\n💡 IMMEDIATE FIXES NEEDED")
    print("=" * 60)
    
    if not debug_results['similarity_scores']:
        print("🚨 CRITICAL: No similarity scores calculated!")
        print("   → Check embedding format and calculation")
        print("   → Verify embeddings are actual numbers, not strings")
        return
    
    max_similarity = max(debug_results['similarity_scores'])
    avg_similarity = np.mean(debug_results['similarity_scores'])
    
    print(f"📊 Your similarity scores range: {min(debug_results['similarity_scores']):.6f} to {max_similarity:.6f}")
    print(f"📊 Average similarity: {avg_similarity:.6f}")
    
    if max_similarity < 0.3:
        print("\n🔧 FIXES:")
        print("1. Your cosine similarity calculation might be wrong")
        print("2. Try this corrected calculation:")
        print("""
def cosine_similarity(vec1, vec2):
    v1 = np.array(vec1, dtype=np.float32)
    v2 = np.array(vec2, dtype=np.float32)
    
    # Calculate cosine similarity
    dot_product = np.dot(v1, v2)
    norm_v1 = np.linalg.norm(v1)
    norm_v2 = np.linalg.norm(v2)
    
    if norm_v1 == 0 or norm_v2 == 0:
        return 0.0
    
    similarity = dot_product / (norm_v1 * norm_v2)
    
    # Cosine similarity is naturally -1 to 1
    # For search, we want 0 to 1, so normalize:
    return (similarity + 1) / 2
        """)
        print(f"3. Set min_score to {max(0.1, avg_similarity * 0.8):.2f}")
    
    if debug_results['embedding_issues']:
        print(f"\n🚨 EMBEDDING ISSUES:")
        print(f"   Found {len(debug_results['embedding_issues'])} embedding problems")
        print("   → Some embeddings may be corrupted")
    
    print(f"\n🎯 RECOMMENDED SETTINGS:")
    print(f"   • min_score: {max(0.05, avg_similarity * 0.5):.3f}")
    print(f"   • Remove LIMIT 2000 to search all {debug_results['total_docs']:,} documents")
    print(f"   • Add WHERE jsonb_array_length(embedding_json) = 384 to filter valid embeddings")


def main():
    """Run the complete debug analysis"""
    try:
        debug_results = debug_wudu_search()
        suggest_immediate_fixes(debug_results)
        
        print("\n" + "=" * 60)
        print("🎯 QUICK TEST: Run this query in your database:")
        print("=" * 60)
        print("""
SELECT 
    id, 
    SUBSTRING(text, 1, 100) as text_preview,
    category,
    jsonb_array_length(embedding_json) as embedding_length
FROM documents 
WHERE LOWER(text) LIKE '%wudu%'
AND embedding_json IS NOT NULL
LIMIT 5;
        """)
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()