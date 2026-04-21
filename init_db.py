import os
import psycopg2
from dotenv import load_dotenv

# Load database credentials from .env file
load_dotenv()

def initialize_database():
    print("Connecting to PostgreSQL...")
    try:
        conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
        cur = conn.cursor()

        print("Updating database architecture for click/scan tracking...")

        # 0. Drop old tables for this reset
        cur.execute('DROP TABLE IF EXISTS scan_events CASCADE;')
        cur.execute('DROP TABLE IF EXISTS tracking_events CASCADE;')
        cur.execute('DROP TABLE IF EXISTS projects CASCADE;')


        # 1. Create the Projects Table (Now with UUID)
        cur.execute('''
            CREATE TABLE projects (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name VARCHAR(100) UNIQUE NOT NULL,
                destination_url TEXT NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        ''')

        # 2. Create the Unified Tracking Events Table
        cur.execute('''
            CREATE TABLE tracking_events (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
                interaction_type VARCHAR(10) NOT NULL CHECK (interaction_type IN ('scan', 'click')),
                target_company VARCHAR(100) DEFAULT 'General',
                user_agent TEXT,
                tracked_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        ''')

        # 3. Seed the database with our initial projects
        # we don't pass an ID anymore. The database generates it!
        cur.execute('''
            INSERT INTO projects (name, destination_url) 
            VALUES 
                ('Personal Portfolio Website with Gabina', 'https://iamnaween.com'),
                ('AlgoFinance', 'https://algofinance.ca')
            ON CONFLICT (name) DO UPDATE 
            SET destination_url = EXCLUDED.destination_url;
        ''')

        conn.commit()
        print("Success! Database architecture is initialized with dynamic UUIDs.")

    except Exception as e:
        print(f"Error initializing database: {e}")
        
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    initialize_database()