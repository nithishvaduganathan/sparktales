"""
Script to create the document_chunks table for RAG
"""
from app.database import engine
from sqlalchemy import text

def create_table():
    with engine.connect() as conn:
        # Create the document_chunks table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS document_chunks (
                id SERIAL PRIMARY KEY,
                course_id INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
                resource_id INTEGER NOT NULL REFERENCES course_resources(id) ON DELETE CASCADE,
                page_number INTEGER NOT NULL,
                chunk_index INTEGER NOT NULL,
                content TEXT NOT NULL,
                embedding TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """))
        
        # Create indexes
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_document_chunks_course_id 
            ON document_chunks(course_id)
        """))
        
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_document_chunks_resource_id 
            ON document_chunks(resource_id)
        """))
        
        conn.commit()
        print("✅ document_chunks table created successfully!")
        
        # Verify table exists
        result = conn.execute(text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'document_chunks'
        """))
        columns = result.fetchall()
        print(f"Table columns: {[col[0] for col in columns]}")

if __name__ == "__main__":
    create_table()
