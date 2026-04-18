import os
import psycopg2
from dotenv import load_dotenv

# Load database credentials from .env file
load_dotenv()

def initialize_database():
    print("Connecting to PostgreSQL...")
    try:
        conn = psycopg2.connect(
            host=os.environ.get('DB_HOST', '127.0.0.1'),
            database=os.environ.get('DB_NAME'),
            user=os.environ.get('DB_USER'),
            password=os.environ.get('DB_PASSWORD')
        )
        cur = conn.cursor()

        print("Wiping old tables and creating new UUID architecture...")


        # 1. Create the Projects Table (Now with UUID)
        cur.execute('''
            CREATE TABLE projects (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name VARCHAR(100) UNIQUE NOT NULL,
                destination_url TEXT NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        ''')

        # 2. Create the Scan Events Table (Now with UUID)
        cur.execute('''
            CREATE TABLE scan_events (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
                target_company VARCHAR(100) DEFAULT 'General',
                user_agent TEXT,
                scanned_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        ''')

        # 3. Seed the database
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