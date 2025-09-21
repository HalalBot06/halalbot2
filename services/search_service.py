#!/usr/bin/env python3
"""
HalalBot Database Search Service
PostgreSQL-based semantic search to replace FAISS index

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
    PostgreSQL-based semantic search service for Islamic documents
    
    Provides cosine similarity search with category filtering and
    intelligent ranking for Quran, Hadith, Fatwa, and other sources.
    """
    
    def __init__(self):
        """Initialize the search service with model and database connection"""
        try:
            # Load the sentence transformer model
            print("🤖 Loading sentence transformer model...")
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            print("✅ Model loaded successfully")
            
            # Get database manager
            self.db = get_db_manager()
            print("✅ Database connection established")
            
        except Exception as e:
            print(f"❌ Failed to initialize search service: {e}")
            raise
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors
        
        Args:
            vec1: First vector (query embedding)
            vec2: Second vector (document embedding)
            
        Returns:
            Cosine similarity score (0-1, higher is better)
        """
        try:
            # Convert to numpy arrays for efficient computation
            v1 = np.array(vec1, dtype=np.float32)
            v2 = np.array(vec2, dtype=np.float32)
            
            # Calculate cosine similarity
            dot_product = np.dot(v1, v2)
            norm_v1 = np.linalg.norm(v1)
            norm_v2 = np.linalg.norm(v2)
            
            # Avoid division by zero
            if norm_v1 == 0 or norm_v2 == 0:
                return 0.0
            
            similarity = dot_product / (norm_v1 * norm_v2)
            
            # Ensure similarity is in valid range [0, 1]
            return max(0.0, min(1.0, float(similarity)))
            
        except Exception as e:
            print(f"⚠️  Error calculating cosine similarity: {e}")
            return 0.0
    
    def build_search_query(self, source_filter: Optional[str] = None) -> Tuple[str, Dict]:
        """
        Build the SQL query for document retrieval with optional filtering
        
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
        AND length(text) > 10
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
        
        # Limit initial retrieval for performance
        base_query += " LIMIT 2000"
        
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
        min_score: float = 0.5, 
        source_filter: Optional[str] = None
    ) -> List[Dict]:
        """
        Perform semantic search on Islamic documents
        
        Args:
            query: Search query text
            top_k: Maximum number of results to return
            min_score: Minimum similarity score threshold
            source_filter: Optional category filter
            
        Returns:
            List of search results with scores and metadata
        """
        try:
            # Generate query embedding
            print(f"🔍 Searching for: '{query}'")
            query_embedding = self.model.encode([query])[0].tolist()
            
            # Build and execute database query
            sql_query, params = self.build_search_query(source_filter)
            documents = self.db.execute_query(sql_query, params, fetch=True)
            
            print(f"📚 Retrieved {len(documents)} documents from database")
            
            # Calculate similarities and filter results
            scored_results = []
            
            for doc in documents:
                try:
                    # Get document embedding (already a list from JSONB)
                    doc_embedding = doc['embedding_json']
                    if not doc_embedding or len(doc_embedding) != 384:
                        continue
                    
                    # Calculate similarity
                    similarity = self.cosine_similarity(query_embedding, doc_embedding)
                    
                    # Apply minimum score threshold
                    if similarity < min_score:
                        continue
                    
                    # Clean and format text
                    cleaned_text = clean_text(doc['text']) if doc['text'] else ''
                    if len(cleaned_text) < 20:  # Skip very short texts
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
                    print(f"⚠️  Error processing document {doc.get('id', 'unknown')}: {e}")
                    continue
            
            # Sort results by priority and score
            scored_results.sort(
                key=lambda x: (
                    self.calculate_category_priority(x['category']),  # Category priority first
                    -x['score']  # Then by score (descending)
                )
            )
            
            # Return top results
            final_results = scored_results[:top_k]
            
            print(f"✅ Found {len(final_results)} relevant results")
            
            return final_results
            
        except Exception as e:
            print(f"❌ Search failed: {e}")
            import traceback
            traceback.print_exc()
            return []
    
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
                AVG(LENGTH(text)) as avg_length
            FROM documents 
            WHERE text IS NOT NULL
            GROUP BY category
            ORDER BY count DESC
            """
            
            results = self.db.execute_query(stats_query, fetch=True)
            
            stats = {
                'total_documents': sum(row['count'] for row in results),
                'categories': {
                    row['category']: {
                        'count': row['count'],
                        'avg_length': int(row['avg_length']) if row['avg_length'] else 0
                    }
                    for row in results
                }
            }
            
            return stats
            
        except Exception as e:
            print(f"⚠️  Failed to get search stats: {e}")
            return {'total_documents': 0, 'categories': {}}


# --- COMPATIBILITY FUNCTIONS ---
# These functions maintain compatibility with the existing codebase

def search_faiss(
    query: str, 
    top_k: int = 5, 
    min_score: float = 0.5, 
    source_filter: Optional[str] = None
) -> List[Dict]:
    """
    Drop-in replacement for the original FAISS search function
    
    Args:
        query: Search query text
        top_k: Maximum number of results
        min_score: Minimum similarity threshold
        source_filter: Category filter
        
    Returns:
        List of search results compatible with existing code
    """
    try:
        service = DatabaseSearchService()
        return service.search(query, top_k, min_score, source_filter)
    except Exception as e:
        print(f"❌ Search service error: {e}")
        return []


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
        
        # Format result
        output += f"**{i}.** {result['text']}\n"
        output += f"{emoji} **Source:** `{source_display}`\n"
        output += f"🧠 **Score:** `{result['score']:.2f}`\n\n"
    
    return output


# --- TESTING AND DEBUGGING ---

def test_search_service():
    """Test the search service with sample queries"""
    print("🧪 Testing Database Search Service...")
    
    test_queries = [
        "prayer times",
        "zakat calculation", 
        "marriage in Islam",
        "fasting rules"
    ]
    
    try:
        service = DatabaseSearchService()
        
        # Get stats
        stats = service.get_search_stats()
        print(f"📊 Collection stats: {stats}")
        
        # Test searches
        for query in test_queries:
            print(f"\n🔍 Testing query: '{query}'")
            results = service.search(query, top_k=3, min_score=0.3)
            print(f"✅ Found {len(results)} results")
            
            for i, result in enumerate(results[:2], 1):
                print(f"  {i}. [{result['category']}] {result['text'][:100]}... (score: {result['score']:.3f})")
        
        print("\n✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    """Entry point for testing and debugging"""
    import argparse
    
    parser = argparse.ArgumentParser(description="HalalBot Database Search Service")
    parser.add_argument("--test", action="store_true", help="Run test queries")
    parser.add_argument("--query", type=str, help="Search for specific query")
    parser.add_argument("--top-k", type=int, default=5, help="Number of results")
    parser.add_argument("--min-score", type=float, default=0.5, help="Minimum score")
    parser.add_argument("--filter", type=str, help="Category filter")
    
    args = parser.parse_args()
    
    if args.test:
        test_search_service()
    elif args.query:
        results = search_faiss(args.query, args.top_k, args.min_score, args.filter)
        print(format_markdown_response(args.query, results))
    else:
        print("Use --test to run tests or --query 'your query' to search")