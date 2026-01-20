#!/usr/bin/env python3
"""
HalalBot Database Search Service - FIXED AND OPTIMIZED
PostgreSQL-based semantic search to replace FAISS index

FIXES APPLIED:
- Removed 2000 document limit (now searches all 29k+ documents)
- Fixed cosine similarity calculation with proper normalization
- Lowered default minimum score from 0.5 to 0.05 based on debug analysis
- Added better error handling and debugging output
- Optimized database queries for better performance
- FIXED: Sorting now prioritizes SCORE over category

This module provides semantic search functionality using PostgreSQL and 
cosine similarity calculations for Islamic knowledge documents.
"""

import numpy as np
import json
import sys
from typing import List, Dict, Optional, Tuple
from pathlib import Path

# Import dependencies
try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    print("⚠️  sentence-transformers not installed. Run: pip install sentence-transformers")
    sys.exit(1)

# Add project root to path for imports
sys.path.append(str(Path(__file__).parent.parent))

try:
    from config.database import get_db_manager
    from utils.text_processing import clean_text
except ImportError as e:
    print(f"⚠️  Import error: {e}")
    print("Make sure you have the required modules in config/ and utils/")


class DatabaseSearchService:
    """
    FIXED PostgreSQL-based semantic search service for Islamic documents
    
    Provides cosine similarity search with category filtering and
    intelligent ranking for Quran, Hadith, Fatwa, and other sources.
    
    Key improvements:
    - No arbitrary document limits
    - Proper similarity score handling
    - Better error handling and debugging
    - Optimized for 29k+ document collection
    - FIXED: Score-first sorting with category as tiebreaker
    """
    
    def __init__(self, debug_mode: bool = False):
        """Initialize the search service with model and database connection"""
        self.debug_mode = debug_mode
        
        try:
            # Load the sentence transformer model
            if self.debug_mode:
                print("🤖 Loading sentence transformer model...")
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            if self.debug_mode:
                print("✅ Model loaded successfully")
            
            # Get database manager
            self.db = get_db_manager()
            if self.debug_mode:
                print("✅ Database connection established")
            
        except Exception as e:
            print(f"❌ Failed to initialize search service: {e}")
            raise
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        FIXED: Calculate cosine similarity between two vectors with proper handling
        
        Args:
            vec1: First vector (query embedding)
            vec2: Second vector (document embedding)
            
        Returns:
            Cosine similarity score (raw -1 to 1, as shown working in debug)
        """
        try:
            # Convert to numpy arrays for efficient computation
            v1 = np.array(vec1, dtype=np.float32)
            v2 = np.array(vec2, dtype=np.float32)
            
            # Calculate norms
            norm_v1 = np.linalg.norm(v1)
            norm_v2 = np.linalg.norm(v2)
            
            # Avoid division by zero
            if norm_v1 == 0 or norm_v2 == 0:
                return 0.0
            
            # Calculate cosine similarity
            dot_product = np.dot(v1, v2)
            similarity = dot_product / (norm_v1 * norm_v2)
            
            # Return raw cosine similarity (-1 to 1)
            # This matches what worked in debug analysis
            return float(similarity)
            
        except Exception as e:
            if self.debug_mode:
                print(f"⚠️  Error calculating cosine similarity: {e}")
            return 0.0
    
    def cosine_similarity_normalized(self, vec1: List[float], vec2: List[float]) -> float:
        """
        ALTERNATIVE: Normalized cosine similarity (0 to 1 range)
        Use this if you prefer 0-1 range for easier threshold setting
        """
        try:
            v1 = np.array(vec1, dtype=np.float32)
            v2 = np.array(vec2, dtype=np.float32)
            
            norm_v1 = np.linalg.norm(v1)
            norm_v2 = np.linalg.norm(v2)
            
            if norm_v1 == 0 or norm_v2 == 0:
                return 0.0
            
            dot_product = np.dot(v1, v2)
            cosine_sim = dot_product / (norm_v1 * norm_v2)
            
            # Normalize -1,1 to 0,1 range
            normalized = (cosine_sim + 1) / 2
            
            return float(normalized)
            
        except Exception as e:
            if self.debug_mode:
                print(f"⚠️  Error calculating normalized cosine similarity: {e}")
            return 0.0
    
    def build_search_query(self, source_filter: Optional[str] = None) -> Tuple[str, Dict]:
        """
        FIXED: Build optimized SQL query for document retrieval (NO LIMITS)
        
        Args:
            source_filter: Category filter (quran-only, hadith-only, etc.)
            
        Returns:
            Tuple of (SQL query, filter parameters)
        """
        base_query = """
        SELECT 
            id, doc_id, text, source, category, title, 
            embedding_json, metadata
        FROM documents 
        WHERE text IS NOT NULL 
        AND embedding_json IS NOT NULL
        AND LENGTH(TRIM(text)) > 20
        AND jsonb_array_length(embedding_json) = 384
        """
        
        params = {}
        
        # Add category filtering
        if source_filter:
            filter_mapping = {
                "quran-only": "quran",
                "hadith-only": "hadith",
                "fatwa-only": "fatwa",
                "zakat-only": "zakat",
                "other-only": "other"
            }
            
            if source_filter in filter_mapping:
                base_query += " AND category = %(category)s"
                params['category'] = filter_mapping[source_filter]
        
        # REMOVED: No more arbitrary LIMIT 2000
        # Now searches ALL valid documents for best results
        
        return base_query, params
    
    def calculate_category_priority(self, category: str) -> int:
        """
        Get priority ranking for Islamic source categories
        
        Args:
            category: Document category
            
        Returns:
            Priority value (lower is higher priority)
        """
        priority_map = {
            "quran": 0,    # Highest priority - Direct word of Allah
            "hadith": 1,   # Second - Prophetic traditions
            "fatwa": 2,    # Third - Scholarly rulings
            "zakat": 3,    # Fourth - Specific zakat guidance
            "other": 4     # Lowest - General Islamic content
        }
        return priority_map.get(category, 5)
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        min_score: float = 0.05,  # FIXED: Lowered from 0.5 to 0.05 based on debug
        source_filter: Optional[str] = None
    ) -> List[Dict]:
        """
        OPTIMIZED: Perform semantic search on Islamic documents
        
        Args:
            query: Search query text
            top_k: Maximum number of results to return
            min_score: Minimum similarity score threshold (lowered to 0.05)
            source_filter: Optional category filter
            
        Returns:
            List of search results with scores and metadata
        """
        try:
            # Generate query embedding
            if self.debug_mode:
                print(f"🔍 Searching for: '{query}' with min_score={min_score}")
            query_embedding = self.model.encode([query])[0].tolist()
            
            # Build and execute database query (now gets ALL valid documents)
            sql_query, params = self.build_search_query(source_filter)
            documents = self.db.execute_query(sql_query, params, fetch=True)
            
            if self.debug_mode:
                print(f"📚 Retrieved {len(documents)} documents from database")
            
            # Calculate similarities and filter results
            scored_results = []
            similarities_calculated = 0
            processing_errors = 0
            similarity_stats = []
            
            for doc in documents:
                try:
                    # Get document embedding (already a list from JSONB)
                    doc_embedding = doc['embedding_json']
                    
                    # Quick validation (we know from debug all should be valid)
                    if not isinstance(doc_embedding, list) or len(doc_embedding) != 384:
                        continue
                    
                    # Calculate similarity
                    similarity = self.cosine_similarity(query_embedding, doc_embedding)
                    similarities_calculated += 1
                    similarity_stats.append(similarity)
                    
                    # Debug: Show first few results
                    if self.debug_mode and similarities_calculated <= 5:
                        text_preview = doc['text'][:80] if doc['text'] else 'No text'
                        print(f"  📄 Doc {doc['id']}: similarity={similarity:.6f} | {text_preview}...")
                    
                    # Apply minimum score threshold
                    if similarity < min_score:
                        continue
                    
                    # Clean and format text
                    cleaned_text = clean_text(doc['text']) if doc['text'] else ''
                    if len(cleaned_text.strip()) < 20:  # Skip very short texts
                        continue
                    
                    # Create result object
                    result = {
                        'id': doc['id'],
                        'doc_id': doc['doc_id'],
                        'text': cleaned_text,
                        'source': doc['source'] or 'unknown',
                        'category': doc['category'] or 'other',
                        'title': doc['title'],
                        'score': similarity,
                        'base_score': similarity,
                        'metadata': doc['metadata'] or {}
                    }
                    
                    scored_results.append(result)
                    
                except Exception as e:
                    processing_errors += 1
                    if self.debug_mode and processing_errors <= 3:
                        print(f"⚠️  Error processing document {doc.get('id', 'unknown')}: {e}")
                    continue
            
            # Debug: Print similarity statistics
            if self.debug_mode and similarity_stats:
                print(f"📊 Similarity statistics:")
                print(f"   • Documents processed: {similarities_calculated}")
                print(f"   • Similarity range: {min(similarity_stats):.6f} to {max(similarity_stats):.6f}")
                print(f"   • Average similarity: {np.mean(similarity_stats):.6f}")
                print(f"   • Results above threshold: {len(scored_results)}")
            
            # ============================================================
            # FIXED SORTING: Score first, category as tiebreaker only
            # ============================================================
            # Previously: category priority first, then score (WRONG!)
            # Now: score first (descending), then category priority (ascending)
            # This ensures the most relevant documents appear first,
            # regardless of whether they're Quran, Hadith, etc.
            # ============================================================
            scored_results.sort(
                key=lambda x: (
                    -x['score'],  # Score first (descending - higher is better)
                    self.calculate_category_priority(x['category'])  # Category as tiebreaker
                )
            )
            
            # Return top results
            final_results = scored_results[:top_k]
            
            if self.debug_mode:
                print(f"✅ Found {len(final_results)} relevant results")
            
            return final_results
            
        except Exception as e:
            print(f"❌ Search failed: {e}")
            if self.debug_mode:
                import traceback
                traceback.print_exc()
            return []
    
    def search_with_stats(self, query: str, top_k: int = 5, min_score: float = 0.05,
                         source_filter: Optional[str] = None) -> Tuple[List[Dict], Dict]:
        """
        Search with detailed statistics for debugging and optimization
        
        Returns:
            Tuple of (results, statistics)
        """
        # Temporarily enable debug mode
        original_debug = self.debug_mode
        self.debug_mode = True
        
        results = self.search(query, top_k, min_score, source_filter)
        
        # Generate additional stats
        stats = {
            'query': query,
            'results_count': len(results),
            'min_score_used': min_score,
            'source_filter': source_filter,
            'top_k': top_k
        }
        
        self.debug_mode = original_debug
        return results, stats
    
    def get_search_stats(self) -> Dict:
        """
        Get statistics about the document collection
        
        Returns:
            Dictionary with collection statistics
        """
        try:
            stats_query = """
            SELECT 
                category,
                COUNT(*) as count,
                AVG(LENGTH(text)) as avg_length,
                COUNT(CASE WHEN embedding_json IS NOT NULL THEN 1 END) as with_embeddings
            FROM documents 
            WHERE text IS NOT NULL
            GROUP BY category
            ORDER BY count DESC
            """
            
            results = self.db.execute_query(stats_query, fetch=True)
            
            stats = {
                'total_documents': sum(row['count'] for row in results),
                'total_with_embeddings': sum(row['with_embeddings'] for row in results),
                'categories': {
                    row['category']: {
                        'count': row['count'],
                        'with_embeddings': row['with_embeddings'],
                        'avg_length': int(row['avg_length']) if row['avg_length'] else 0
                    }
                    for row in results
                }
            }
            
            return stats
            
        except Exception as e:
            print(f"⚠️  Failed to get search stats: {e}")
            return {'total_documents': 0, 'total_with_embeddings': 0, 'categories': {}}


# --- COMPATIBILITY FUNCTIONS ---
# These functions maintain compatibility with the existing codebase

def search_faiss(
    query: str,
    top_k: int = 5,
    min_score: float = 0.05,  # FIXED: Changed default from 0.5 to 0.05
    source_filter: Optional[str] = None
) -> List[Dict]:
    """
    FIXED: Drop-in replacement for the original FAISS search function
    
    Args:
        query: Search query text
        top_k: Maximum number of results
        min_score: Minimum similarity threshold (now defaults to 0.05)
        source_filter: Category filter
        
    Returns:
        List of search results compatible with existing code
    """
    try:
        service = DatabaseSearchService(debug_mode=False)
        return service.search(query, top_k, min_score, source_filter)
    except Exception as e:
        print(f"❌ Search service error: {e}")
        return []


# Singleton instance for better performance (avoid reloading model)
_search_service_instance = None

def get_search_service() -> DatabaseSearchService:
    """Get or create singleton search service instance"""
    global _search_service_instance
    if _search_service_instance is None:
        _search_service_instance = DatabaseSearchService(debug_mode=False)
    return _search_service_instance


def format_markdown_response(query: str, results: List[Dict]) -> str:
    """
    Format search results as markdown for display
    
    Args:
        query: Original search query
        results: List of search results
        
    Returns:
        Formatted markdown string
    """
    if not results:
        return f"\n**🔍 Query:** _{query}_\n\n_No relevant answers found._"
    
    # Header with query
    output = f"\n**🔍 Query:** _{query}_\n\n"
    
    # Format each result
    for i, result in enumerate(results, 1):
        # Get source display name
        source_display = result.get('source', 'Unknown')
        if result.get('title'):
            source_display = f"{result['title']} ({source_display})"
        
        # Add category emoji
        category_emojis = {
            'quran': '📖',
            'hadith': '📜',
            'fatwa': '⚖️',
            'zakat': '💰',
            'other': '📚'
        }
        emoji = category_emojis.get(result.get('category', 'other'), '📚')
        
        # Format result with improved score display
        output += f"**{i}.** {result['text']}\n"
        output += f"{emoji} **Source:** `{source_display}`\n"
        output += f"🧠 **Score:** `{result['score']:.4f}`\n\n"
    
    return output


# --- TESTING AND DEBUGGING ---

def test_search_service():
    """ENHANCED: Test the search service with sample queries and proper thresholds"""
    print("🧪 Testing FIXED Database Search Service...")
    
    test_queries = [
        ("wudu", 0.05),
        ("prayer times", 0.05),
        ("zakat calculation", 0.05),
        ("marriage in Islam", 0.05),
        ("fasting rules", 0.05),
        ("ablution", 0.05)
    ]
    
    try:
        service = DatabaseSearchService(debug_mode=True)
        
        # Get stats
        stats = service.get_search_stats()
        print(f"📊 Collection stats: {stats}")
        
        # Test searches with proper thresholds
        for query, min_score in test_queries:
            print(f"\n{'='*60}")
            print(f"🔍 Testing query: '{query}' with min_score={min_score}")
            print(f"{'='*60}")
            
            results = service.search(query, top_k=5, min_score=min_score)
            print(f"✅ Found {len(results)} results")
            
            for i, result in enumerate(results[:3], 1):
                print(f"  {i}. [{result['category']}] Score: {result['score']:.4f}")
                print(f"     {result['text'][:100]}...")
        
        print("\n🎉 All tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


def debug_specific_query(query: str = "wudu"):
    """Debug a specific query with detailed output"""
    print(f"🔍 DEBUGGING SPECIFIC QUERY: '{query}'")
    print("="*60)
    
    try:
        service = DatabaseSearchService(debug_mode=True)
        results, stats = service.search_with_stats(query, top_k=10, min_score=0.01)
        
        print(f"\n📊 Search Statistics:")
        for key, value in stats.items():
            print(f"   • {key}: {value}")
        
        if results:
            print(f"\n🏆 Top Results:")
            for i, result in enumerate(results, 1):
                print(f"  {i}. [{result['category']}] Score: {result['score']:.6f}")
                print(f"     {result['text'][:150]}...")
                print()
        else:
            print("\n❌ No results found")
            
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    """Entry point for testing and debugging"""
    import argparse
    
    parser = argparse.ArgumentParser(description="HalalBot Database Search Service - FIXED")
    parser.add_argument("--test", action="store_true", help="Run test queries")
    parser.add_argument("--debug", type=str, help="Debug specific query")
    parser.add_argument("--query", type=str, help="Search for specific query")
    parser.add_argument("--top-k", type=int, default=5, help="Number of results")
    parser.add_argument("--min-score", type=float, default=0.05, help="Minimum score (default: 0.05)")
    parser.add_argument("--filter", type=str, help="Category filter")
    
    args = parser.parse_args()
    
    if args.test:
        test_search_service()
    elif args.debug:
        debug_specific_query(args.debug)
    elif args.query:
        print(f"🔍 Searching for: '{args.query}'")
        results = search_faiss(args.query, args.top_k, args.min_score, args.filter)
        print(format_markdown_response(args.query, results))
    else:
        print("🚀 HalalBot Search Service - FIXED VERSION")
        print("Options:")
        print("  --test          : Run comprehensive tests")
        print("  --debug 'query' : Debug specific query")
        print("  --query 'text'  : Search for text")
        print("\nExample: python search_service.py --query 'wudu' --min-score 0.05")
