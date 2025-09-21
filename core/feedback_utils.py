# feedback_utils.py
"""
HalalBot Feedback System
Handles user feedback collection, score adjustments, and answer quality improvement

Features:
- Database-first feedback logging with JSON backup
- Score penalty system for poor performing content
- Text hashing for consistent document identification
- Analytics and feedback summaries
- Integration with search result ranking
"""

import json
import os
import hashlib
from datetime import datetime
from typing import Optional, Dict, List, Tuple
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.append(str(Path(__file__).parent.parent))

try:
    from config.database import get_db_manager
    DATABASE_AVAILABLE = True
except ImportError:
    print("Warning: Database not available, using JSON-only mode")
    DATABASE_AVAILABLE = False

# --- CONFIGURATION ---
FEEDBACK_LOG_FILE = "feedback_log.jsonl"
ADJUSTMENTS_FILE = "feedback_adjustments.json"
PENALTY_PER_DOWNVOTE = 0.02
MAX_PENALTY = 0.3
BACKUP_ENABLED = True

# --- CORE UTILITIES ---

def hash_text(text: str) -> str:
    """
    Generate consistent hash for text content
    
    Args:
        text: Document text to hash
        
    Returns:
        SHA256 hash string
    """
    if not text or not isinstance(text, str):
        return ""
    
    # Normalize text before hashing (remove extra whitespace, consistent encoding)
    normalized_text = " ".join(text.strip().split())
    return hashlib.sha256(normalized_text.encode('utf-8')).hexdigest()


def get_user_id(email: str) -> Optional[int]:
    """
    Get user ID from email for database operations
    
    Args:
        email: User email address
        
    Returns:
        User ID if found, None otherwise
    """
    if not DATABASE_AVAILABLE or not email:
        return None
    
    try:
        db = get_db_manager()
        result = db.execute_query(
            "SELECT id FROM users WHERE email = %s", 
            (email,), 
            fetch=True
        )
        return result[0]['id'] if result else None
    except Exception as e:
        print(f"Error getting user ID: {e}")
        return None


def get_document_id(text_hash: str) -> Optional[int]:
    """
    Get document ID from text hash
    
    Args:
        text_hash: Hash of document text
        
    Returns:
        Document ID if found, None otherwise
    """
    if not DATABASE_AVAILABLE or not text_hash:
        return None
    
    try:
        db = get_db_manager()
        
        # Try to find document by matching text hash
        # Note: This requires storing text hashes in the database
        # For now, we'll use a simpler approach with text matching
        result = db.execute_query(
            "SELECT id FROM documents WHERE encode(sha256(text::bytea), 'hex') = %s LIMIT 1",
            (text_hash,),
            fetch=True
        )
        return result[0]['id'] if result else None
    except Exception as e:
        print(f"Error getting document ID: {e}")
        return None


# --- DATABASE FEEDBACK OPERATIONS ---

def log_feedback_to_database(user_email: str, document_text: str, query: str, 
                           feedback_type: str) -> bool:
    """
    Log feedback to PostgreSQL database
    
    Args:
        user_email: Email of user providing feedback
        document_text: Text content that was rated
        query: Original search query
        feedback_type: 'up' or 'down'
        
    Returns:
        True if successful, False otherwise
    """
    if not DATABASE_AVAILABLE:
        return False
    
    try:
        db = get_db_manager()
        user_id = get_user_id(user_email)
        text_hash = hash_text(document_text)
        document_id = get_document_id(text_hash)
        
        # Insert feedback record
        db.execute_query("""
            INSERT INTO feedback (user_id, document_id, query, feedback_type, timestamp)
            VALUES (%s, %s, %s, %s, %s)
        """, (user_id, document_id, query, feedback_type, datetime.now()))
        
        return True
        
    except Exception as e:
        print(f"Error logging feedback to database: {e}")
        return False


def get_feedback_stats_from_database(text_hash: str) -> Dict[str, int]:
    """
    Get feedback statistics from database for a document
    
    Args:
        text_hash: Hash of document text
        
    Returns:
        Dictionary with thumbs_up and thumbs_down counts
    """
    if not DATABASE_AVAILABLE:
        return {"thumbs_up": 0, "thumbs_down": 0}
    
    try:
        db = get_db_manager()
        document_id = get_document_id(text_hash)
        
        if not document_id:
            return {"thumbs_up": 0, "thumbs_down": 0}
        
        # Get feedback counts
        result = db.execute_query("""
            SELECT 
                feedback_type,
                COUNT(*) as count
            FROM feedback 
            WHERE document_id = %s 
            GROUP BY feedback_type
        """, (document_id,), fetch=True)
        
        stats = {"thumbs_up": 0, "thumbs_down": 0}
        for row in result:
            if row['feedback_type'] == 'up':
                stats['thumbs_up'] = row['count']
            elif row['feedback_type'] == 'down':
                stats['thumbs_down'] = row['count']
        
        return stats
        
    except Exception as e:
        print(f"Error getting feedback stats from database: {e}")
        return {"thumbs_up": 0, "thumbs_down": 0}


# --- JSON BACKUP OPERATIONS ---

def log_feedback_to_json(user_email: str, document_text: str, query: str, 
                        feedback_type: str) -> None:
    """
    Log feedback to JSON file as backup
    
    Args:
        user_email: Email of user providing feedback
        document_text: Text content that was rated
        query: Original search query  
        feedback_type: 'up' or 'down'
    """
    try:
        entry = {
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "text_hash": hash_text(document_text),
            "vote": feedback_type,
            "user": user_email or "anonymous"
        }
        
        with open(FEEDBACK_LOG_FILE, "a", encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            
    except Exception as e:
        print(f"Error logging feedback to JSON: {e}")


def load_adjustments() -> Dict[str, Dict[str, int]]:
    """
    Load score adjustments from JSON file
    
    Returns:
        Dictionary mapping text hashes to vote counts
    """
    if not os.path.exists(ADJUSTMENTS_FILE):
        return {}
    
    try:
        with open(ADJUSTMENTS_FILE, "r", encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading adjustments: {e}")
        return {}


def save_adjustments(data: Dict[str, Dict[str, int]]) -> None:
    """
    Save score adjustments to JSON file
    
    Args:
        data: Dictionary mapping text hashes to vote counts
    """
    try:
        with open(ADJUSTMENTS_FILE, "w", encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving adjustments: {e}")


def update_json_adjustments(text_hash: str, vote: str) -> None:
    """
    Update JSON-based score adjustments
    
    Args:
        text_hash: Hash of document text
        vote: 'up' or 'down'
    """
    try:
        adj = load_adjustments()
        
        if text_hash not in adj:
            adj[text_hash] = {"thumbs_up": 0, "thumbs_down": 0}
        
        if vote == "up":
            adj[text_hash]["thumbs_up"] += 1
        elif vote == "down":
            adj[text_hash]["thumbs_down"] += 1
        
        save_adjustments(adj)
        
    except Exception as e:
        print(f"Error updating JSON adjustments: {e}")


# --- MAIN FEEDBACK FUNCTIONS ---

def log_feedback(query: str, text: str, vote: str, user_email: Optional[str] = None) -> bool:
    """
    Log user feedback for a search result
    
    Args:
        query: Original search query
        text: Document text that was rated
        vote: 'up' or 'down'
        user_email: Email of user providing feedback
        
    Returns:
        True if feedback was logged successfully
    """
    if not text or vote not in ['up', 'down']:
        return False
    
    user_email = user_email or "anonymous"
    text_hash = hash_text(text)
    
    # Log to database (primary)
    db_success = log_feedback_to_database(user_email, text, query, vote)
    
    # Log to JSON (backup)
    if BACKUP_ENABLED:
        log_feedback_to_json(user_email, text, query, vote)
        update_json_adjustments(text_hash, vote)
    
    return db_success or BACKUP_ENABLED


def get_vote_summary(text_hash: str) -> Optional[Dict[str, int]]:
    """
    Get vote summary for a document
    
    Args:
        text_hash: Hash of document text
        
    Returns:
        Dictionary with thumbs_up and thumbs_down counts, or None if not found
    """
    if not text_hash:
        return None
    
    # Try database first
    if DATABASE_AVAILABLE:
        stats = get_feedback_stats_from_database(text_hash)
        if stats['thumbs_up'] > 0 or stats['thumbs_down'] > 0:
            return stats
    
    # Fallback to JSON
    adj = load_adjustments()
    return adj.get(text_hash)


def get_score_penalty(text_hash: str) -> float:
    """
    Calculate score penalty based on downvotes
    
    Args:
        text_hash: Hash of document text
        
    Returns:
        Penalty value between 0.0 and MAX_PENALTY
    """
    if not text_hash:
        return 0.0
    
    votes = get_vote_summary(text_hash)
    if not votes:
        return 0.0
    
    downvotes = votes.get("thumbs_down", 0)
    penalty = min(PENALTY_PER_DOWNVOTE * downvotes, MAX_PENALTY)
    
    return penalty


def get_adjusted_score(base_score: float, text: str) -> float:
    """
    Get adjusted score based on user feedback
    
    Args:
        base_score: Original similarity score
        text: Document text content
        
    Returns:
        Adjusted score after applying feedback penalty
    """
    if not text:
        return base_score
    
    text_hash = hash_text(text)
    penalty = get_score_penalty(text_hash)
    adjusted = max(0.0, base_score - penalty)
    
    return adjusted


# --- ANALYTICS AND REPORTING ---

def get_feedback_analytics() -> Dict:
    """
    Get comprehensive feedback analytics
    
    Returns:
        Dictionary with various feedback statistics
    """
    analytics = {
        "total_feedback_count": 0,
        "upvotes": 0,
        "downvotes": 0,
        "documents_with_feedback": 0,
        "average_score_adjustment": 0.0,
        "top_penalized_documents": []
    }
    
    try:
        # Database analytics
        if DATABASE_AVAILABLE:
            db = get_db_manager()
            
            # Total feedback count
            result = db.execute_query("SELECT COUNT(*) as count FROM feedback", fetch=True)
            analytics["total_feedback_count"] = result[0]['count'] if result else 0
            
            # Vote breakdown
            result = db.execute_query("""
                SELECT feedback_type, COUNT(*) as count 
                FROM feedback 
                GROUP BY feedback_type
            """, fetch=True)
            
            for row in result:
                if row['feedback_type'] == 'up':
                    analytics["upvotes"] = row['count']
                elif row['feedback_type'] == 'down':
                    analytics["downvotes"] = row['count']
        
        # JSON backup analytics
        adjustments = load_adjustments()
        analytics["documents_with_feedback"] = len(adjustments)
        
        # Calculate penalties for top documents
        penalties = []
        for text_hash, votes in adjustments.items():
            penalty = get_score_penalty(text_hash)
            if penalty > 0:
                penalties.append({
                    "text_hash": text_hash,
                    "penalty": penalty,
                    "downvotes": votes.get("thumbs_down", 0),
                    "upvotes": votes.get("thumbs_up", 0)
                })
        
        # Sort by penalty and take top 10
        penalties.sort(key=lambda x: x['penalty'], reverse=True)
        analytics["top_penalized_documents"] = penalties[:10]
        
        # Average penalty
        if penalties:
            analytics["average_score_adjustment"] = sum(p['penalty'] for p in penalties) / len(penalties)
    
    except Exception as e:
        print(f"Error generating analytics: {e}")
    
    return analytics


def get_document_feedback_history(text: str) -> List[Dict]:
    """
    Get feedback history for a specific document
    
    Args:
        text: Document text content
        
    Returns:
        List of feedback entries for the document
    """
    if not DATABASE_AVAILABLE:
        return []
    
    try:
        db = get_db_manager()
        text_hash = hash_text(text)
        document_id = get_document_id(text_hash)
        
        if not document_id:
            return []
        
        result = db.execute_query("""
            SELECT f.feedback_type, f.query, f.timestamp, u.email
            FROM feedback f
            LEFT JOIN users u ON f.user_id = u.id
            WHERE f.document_id = %s
            ORDER BY f.timestamp DESC
            LIMIT 100
        """, (document_id,), fetch=True)
        
        return [dict(row) for row in result]
        
    except Exception as e:
        print(f"Error getting document feedback history: {e}")
        return []


# --- MAINTENANCE FUNCTIONS ---

def cleanup_old_feedback(days_old: int = 365) -> int:
    """
    Clean up old feedback entries
    
    Args:
        days_old: Remove feedback older than this many days
        
    Returns:
        Number of entries removed
    """
    if not DATABASE_AVAILABLE:
        return 0
    
    try:
        db = get_db_manager()
        
        result = db.execute_query("""
            DELETE FROM feedback 
            WHERE timestamp < NOW() - INTERVAL '%s days'
            RETURNING id
        """, (days_old,), fetch=True)
        
        removed_count = len(result) if result else 0
        print(f"Removed {removed_count} old feedback entries")
        
        return removed_count
        
    except Exception as e:
        print(f"Error cleaning up old feedback: {e}")
        return 0


def export_feedback_data(output_file: str = "feedback_export.json") -> bool:
    """
    Export all feedback data to JSON file
    
    Args:
        output_file: Path to output file
        
    Returns:
        True if export successful
    """
    try:
        export_data = {
            "export_timestamp": datetime.now().isoformat(),
            "analytics": get_feedback_analytics(),
            "adjustments": load_adjustments()
        }
        
        if DATABASE_AVAILABLE:
            db = get_db_manager()
            result = db.execute_query("""
                SELECT f.*, u.email as user_email
                FROM feedback f
                LEFT JOIN users u ON f.user_id = u.id
                ORDER BY f.timestamp DESC
            """, fetch=True)
            
            export_data["feedback_entries"] = [dict(row) for row in result]
        
        with open(output_file, "w", encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"Feedback data exported to {output_file}")
        return True
        
    except Exception as e:
        print(f"Error exporting feedback data: {e}")
        return False


# --- TESTING AND VALIDATION ---

def test_feedback_system():
    """Test the feedback system with sample data"""
    print("🧪 Testing HalalBot Feedback System...")
    
    # Test data
    test_query = "What is the importance of prayer in Islam?"
    test_text = "Prayer (Salah) is one of the five pillars of Islam and is mandatory for all Muslims."
    test_email = "test@example.com"
    
    # Test hashing
    text_hash = hash_text(test_text)
    print(f"✅ Text hash generated: {text_hash[:16]}...")
    
    # Test logging feedback
    success = log_feedback(test_query, test_text, "up", test_email)
    print(f"✅ Feedback logging: {'Success' if success else 'Failed'}")
    
    # Test score adjustment
    base_score = 0.85
    adjusted_score = get_adjusted_score(base_score, test_text)
    print(f"✅ Score adjustment: {base_score} -> {adjusted_score}")
    
    # Test vote summary
    votes = get_vote_summary(text_hash)
    print(f"✅ Vote summary: {votes}")
    
    # Test analytics
    analytics = get_feedback_analytics()
    print(f"✅ Analytics generated: {analytics['total_feedback_count']} total votes")
    
    print("🎉 Feedback system test completed!")


if __name__ == "__main__":
    # Run tests if called directly
    test_feedback_system()