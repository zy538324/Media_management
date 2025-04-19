import sqlite3
import os
from config import Config

def init_db():
    """Initialize the SQLite database with schema"""
    config = Config()
    db_path = config.SQLALCHEMY_DATABASE_URI.replace('sqlite:///', '')
    
    # Create directory if it doesn't exist
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir)
    
    # Connect to SQLite database (will create if not exists)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Execute schema SQL
    with open('schema.sql', 'r') as f:
        schema_sql = f.read()
        
    # Split the SQL into separate statements
    statements = schema_sql.split(';')
    for statement in statements:
        statement = statement.strip()
        if statement:
            try:
                cursor.execute(statement)
            except sqlite3.Error as e:
                print(f"Error executing statement: {e}")
                print(f"Statement: {statement}")
    
    conn.commit()
    conn.close()
    print(f"Database initialized at {db_path}")

if __name__ == "__main__":
    init_db()