import sqlite3
import os

def migrate_database():
    """
    Migrate the database to include the new search_query and search_type columns
    Also migrate existing data from email_searched to search_query
    """
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'dark_web_scanner.db')
    
    # Connect to the database
    print(f"Connecting to database at {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if the columns already exist
        cursor.execute("PRAGMA table_info(search_history)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        # Add search_query column if it doesn't exist
        if 'search_query' not in column_names:
            print("Adding search_query column...")
            cursor.execute("ALTER TABLE search_history ADD COLUMN search_query TEXT")
            # Migrate data from email_searched to search_query
            cursor.execute("UPDATE search_history SET search_query = email_searched")
        else:
            print("search_query column already exists")
        
        # Add search_type column if it doesn't exist
        if 'search_type' not in column_names:
            print("Adding search_type column...")
            cursor.execute("ALTER TABLE search_history ADD COLUMN search_type TEXT DEFAULT 'email' NOT NULL")
        else:
            print("search_type column already exists")
        
        # Commit the changes
        conn.commit()
        print("Database migration completed successfully")
        
    except Exception as e:
        conn.rollback()
        print(f"Error during migration: {str(e)}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()
