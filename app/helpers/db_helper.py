import sqlite3
from config import Config
import logging

class DBHelper:
    @staticmethod
    def get_connection():
        """Get a connection to the SQLite database."""
        config = Config()
        db_path = config.SQLALCHEMY_DATABASE_URI.replace('sqlite:///', '')
        try:
            conn = sqlite3.connect(db_path)
            # Enable row factory to access columns by name
            conn.row_factory = sqlite3.Row
            return conn
        except sqlite3.Error as e:
            logging.error(f"Database connection error: {e}")
            return None
            
    @staticmethod
    def execute_query(query, params=None, fetchall=False, fetchone=False, commit=False):
        """Execute a query and return results or commit changes."""
        conn = DBHelper.get_connection()
        if not conn:
            return None
            
        try:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
                
            if commit:
                conn.commit()
                return cursor.lastrowid
                
            if fetchall:
                return cursor.fetchall()
                
            if fetchone:
                return cursor.fetchone()
                
            return True
        except sqlite3.Error as e:
            logging.error(f"Query execution error: {e}")
            logging.error(f"Query: {query}")
            if params:
                logging.error(f"Params: {params}")
            return None
        finally:
            conn.close()