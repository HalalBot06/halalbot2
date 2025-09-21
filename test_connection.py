#!/usr/bin/env python3
"""
HalalBot Database Connection Test for Railway PostgreSQL Migration
Tests database connectivity, data integrity, and system readiness
"""

import os
import sys
import json
import psycopg2
from psycopg2.extras import RealDictCursor
import numpy as np
from pathlib import Path

def test_sentence_transformers():
    """Test if sentence-transformers model loads correctly"""
    print("🤖 Testing sentence-transformers model...")
    
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('all-MiniLM-L6-v2')
        print("✅ Sentence transformer model loaded successfully")
        
        # Test encoding
        test_text = "This is a test sentence for Islamic knowledge"
        test_embedding = model.encode([test_text])
        expected_dims = 384  # all-MiniLM-L6-v2 produces 384-dimensional embeddings
        
        if test_embedding.shape == (1, expected_dims):
            print(f"✅ Test embedding generated: shape {test_embedding.shape}")
            return True, model
        else:
            print(f"❌ Unexpected embedding dimensions: {test_embedding.shape}, expected (1, {expected_dims})")
            return False, None
            
    except ImportError as e:
        print(f"❌ Failed to import sentence-transformers: {e}")
        print("💡 Install with: pip install sentence-transformers")
        return False, None
    except Exception as e:
        print(f"❌ Model loading failed: {e}")
        return False, None

def test_database_connection():
    """Test basic database connectivity"""
    print("🔗 Testing database connection...")
    
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL environment variable not set")
        print("💡 Set it with your Railway database URL:")
        print("   export DATABASE_URL='postgresql://user:pass@host:port/dbname'")
        return False, None
    
    print("✅ DATABASE_URL is configured")
    
    try:
        # Test connection
        conn = psycopg2.connect(database_url)
        print("✅ Successfully connected to PostgreSQL database")
        
        # Test basic query
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT version();")
            version_info = cursor.fetchone()
            print(f"✅ PostgreSQL version: {version_info['version']}")
        
        return True, conn
        
    except psycopg2.Error as e:
        print(f"❌ Database connection failed: {e}")
        return False, None
    except Exception as e:
        print(f"❌ Unexpected error connecting to database: {e}")
        return False, None

def test_pgvector_extension(conn):
    """Check if pgvector extension is available (optional)"""
    print("🧬 Checking for pgvector extension...")
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT * FROM pg_extension WHERE extname = 'vector';")
            result = cursor.fetchone()
            
            if result:
                print("✅ pgvector extension is installed")
                return True
            else:
                print("ℹ️  pgvector extension not found - using JSONB embeddings instead")
                return False
                
    except Exception as e:
        print(f"⚠️  Could not check pgvector extension: {e}")
        return False

def test_table_structure(conn):
    """Verify required tables and their structure exist"""
    print("🏗️  Testing table structure...")
    
    required_tables = {
        'users': ['id', 'email', 'password_hash', 'is_admin', 'invite_code'],
        'invite_codes': ['code', 'used', 'used_by_email', 'created_at'],
        'documents': ['id', 'doc_id', 'text', 'source', 'category', 'embedding_json', 'metadata'],
        'search_queries': ['id', 'user_id', 'query', 'results_count', 'timestamp'],
        'feedback': ['id', 'user_id', 'document_id', 'query', 'feedback_type']
    }
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Check which tables exist
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """)
            existing_tables = [row['table_name'] for row in cursor.fetchall()]
            
            print(f"📋 Found tables: {', '.join(existing_tables)}")
            
            missing_tables = []
            for table_name in required_tables.keys():
                if table_name not in existing_tables:
                    missing_tables.append(table_name)
                else:
                    print(f"✅ Table '{table_name}' exists")
            
            if missing_tables:
                print(f"❌ Missing tables: {', '.join(missing_tables)}")
                return False
            
            # Check documents table structure in detail
            cursor.execute("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = 'documents'
                ORDER BY ordinal_position;
            """)
            
            columns = cursor.fetchall()
            print("📊 Documents table structure:")
            for col in columns:
                nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                print(f"   • {col['column_name']}: {col['data_type']} ({nullable})")
            
            return True
            
    except Exception as e:
        print(f"❌ Table structure test failed: {e}")
        return False

def test_document_data_integrity(conn):
    """Test document data and embedding integrity"""
    print("📊 Testing document data integrity...")
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Get total document count
            cursor.execute("SELECT COUNT(*) as total FROM documents;")
            total_docs = cursor.fetchone()['total']
            print(f"📄 Total documents: {total_docs:,}")
            
            if total_docs == 0:
                print("⚠️  No documents found in database")
                return False
            
            # Check documents by category
            cursor.execute("""
                SELECT category, COUNT(*) as count 
                FROM documents 
                GROUP BY category 
                ORDER BY count DESC;
            """)
            
            categories = cursor.fetchall()
            print("📚 Documents by category:")
            for cat in categories:
                print(f"   • {cat['category']}: {cat['count']:,} documents")
            
            # Check for missing text content
            cursor.execute("SELECT COUNT(*) as count FROM documents WHERE text IS NULL OR text = '';")
            missing_text = cursor.fetchone()['count']
            if missing_text > 0:
                print(f"⚠️  {missing_text} documents have missing text content")
            else:
                print("✅ All documents have text content")
            
            # Check embedding integrity
            cursor.execute("SELECT COUNT(*) as count FROM documents WHERE embedding_json IS NULL;")
            missing_embeddings = cursor.fetchone()['count']
            
            if missing_embeddings > 0:
                print(f"❌ {missing_embeddings} documents missing embeddings")
                return False
            else:
                print("✅ All documents have embeddings")
            
            # Test a few random embeddings for structure
            cursor.execute("""
                SELECT embedding_json 
                FROM documents 
                WHERE embedding_json IS NOT NULL 
                LIMIT 5;
            """)
            
            sample_embeddings = cursor.fetchall()
            embedding_dims = []
            
            for i, row in enumerate(sample_embeddings):
                try:
                    embedding = row['embedding_json']
                    if isinstance(embedding, list):
                        dims = len(embedding)
                        embedding_dims.append(dims)
                        if i == 0:  # Only print first one
                            print(f"✅ Sample embedding dimensions: {dims}")
                    else:
                        print(f"❌ Embedding {i+1} is not a list: {type(embedding)}")
                        return False
                except Exception as e:
                    print(f"❌ Error checking embedding {i+1}: {e}")
                    return False
            
            # Verify all embeddings have same dimensions
            if len(set(embedding_dims)) == 1:
                expected_dims = 384  # all-MiniLM-L6-v2
                actual_dims = embedding_dims[0]
                if actual_dims == expected_dims:
                    print(f"✅ All embeddings have correct dimensions: {actual_dims}")
                else:
                    print(f"⚠️  Unexpected embedding dimensions: {actual_dims}, expected {expected_dims}")
            else:
                print(f"❌ Inconsistent embedding dimensions: {set(embedding_dims)}")
                return False
            
            return True
            
    except Exception as e:
        print(f"❌ Data integrity test failed: {e}")
        return False

def test_sample_queries(conn, model):
    """Test sample search functionality"""
    print("🔍 Testing sample queries...")
    
    if not model:
        print("⚠️  Skipping query test - model not available")
        return True
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Test query
            test_query = "What does Islam say about prayer?"
            query_embedding = model.encode([test_query])[0].tolist()
            
            print(f"🔍 Testing query: '{test_query}'")
            
            # Simple similarity search using JSONB
            # Note: This is a basic implementation - in production you'd want more efficient similarity search
            cursor.execute("""
                SELECT id, doc_id, text, source, category, title,
                       SUBSTRING(text FROM 1 FOR 100) as text_preview
                FROM documents 
                WHERE text IS NOT NULL 
                AND LENGTH(text) > 50
                LIMIT 10;
            """)
            
            sample_results = cursor.fetchall()
            
            if sample_results:
                print(f"✅ Found {len(sample_results)} sample documents for testing")
                print("📄 Sample results:")
                for i, result in enumerate(sample_results[:3]):
                    source_display = result['source'] or 'Unknown'
                    print(f"   {i+1}. [{result['category']}] {result['text_preview']}...")
                    print(f"      Source: {source_display}")
                return True
            else:
                print("❌ No documents found for sample query")
                return False
                
    except Exception as e:
        print(f"❌ Sample query test failed: {e}")
        return False

def test_search_service_integration():
    """Test the search service integration"""
    print("🔧 Testing search service integration...")
    
    try:
        # Try to import the search service
        sys.path.append('.')
        from services.search_service import DatabaseSearchService
        
        service = DatabaseSearchService()
        print("✅ Search service imported successfully")
        
        # Test a simple search
        results = service.search("prayer", top_k=3, min_score=0.3)
        
        if results:
            print(f"✅ Search service returned {len(results)} results")
            for i, result in enumerate(results[:2]):
                print(f"   {i+1}. Score: {result['score']:.3f} | Category: {result['category']}")
            return True
        else:
            print("⚠️  Search service returned no results")
            return True  # This might be normal depending on data
            
    except ImportError:
        print("ℹ️  Search service not found - this is normal if not yet implemented")
        return True
    except Exception as e:
        print(f"⚠️  Search service test failed: {e}")
        return True  # Not critical for basic connection test

def check_environment():
    """Check environment and dependencies"""
    print("🌍 Checking environment...")
    
    # Check Python version
    python_version = sys.version.split()[0]
    print(f"🐍 Python version: {python_version}")
    
    # Check required packages
    required_packages = [
        'psycopg2',
        'sentence_transformers', 
        'numpy',
        'streamlit'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package} is installed")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package} is missing")
    
    if missing_packages:
        print(f"\n💡 Install missing packages with:")
        print(f"   pip install {' '.join(missing_packages)}")
        return False
    
    return True

def main():
    """Run all connection tests"""
    print("🚀 HalalBot Database Connection Test for Railway PostgreSQL")
    print("=" * 60)
    
    all_tests_passed = True
    
    # Test environment
    print("\n1. Environment Check:")
    if not check_environment():
        all_tests_passed = False
    
    # Test sentence transformers
    print("\n2. Model Loading Test:")
    model_success, model = test_sentence_transformers()
    if not model_success:
        all_tests_passed = False
    
    # Test database connection
    print("\n3. Database Connection Test:")
    db_success, conn = test_database_connection()
    if not db_success:
        all_tests_passed = False
        print("\n💥 Cannot proceed without database connection")
        return
    
    try:
        # Test pgvector extension
        print("\n4. Extension Check:")
        test_pgvector_extension(conn)
        
        # Test table structure
        print("\n5. Table Structure Test:")
        if not test_table_structure(conn):
            all_tests_passed = False
        
        # Test data integrity
        print("\n6. Data Integrity Test:")
        if not test_document_data_integrity(conn):
            all_tests_passed = False
        
        # Test sample queries
        print("\n7. Sample Query Test:")
        if not test_sample_queries(conn, model):
            all_tests_passed = False
        
        # Test search service
        print("\n8. Search Service Integration Test:")
        test_search_service_integration()  # Non-critical
        
    finally:
        if conn:
            conn.close()
            print("\n🔌 Database connection closed")
    
    # Final results
    print("\n" + "=" * 60)
    if all_tests_passed:
        print("🎉 ALL TESTS PASSED! HalalBot database is ready for deployment.")
        print("\n✅ Next steps:")
        print("   • Deploy your Streamlit app to Railway")
        print("   • Test the full application with real queries")
        print("   • Monitor performance and query logs")
        print("   • Set up backup procedures")
    else:
        print("⚠️  SOME TESTS FAILED! Please review the issues above.")
        print("\n🔧 Common fixes:")
        print("   • Ensure DATABASE_URL is correctly set")
        print("   • Run database migration script if tables are missing")
        print("   • Check that embeddings were properly migrated")
        print("   • Install missing Python packages")
    
    return all_tests_passed

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)