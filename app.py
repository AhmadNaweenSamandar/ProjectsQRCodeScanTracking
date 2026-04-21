import os
import uuid
import psycopg2
from flask import Flask, redirect, request, abort
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

def get_db_connection():
    """Establish a fresh connection to the database for each request."""
    return psycopg2.connect(os.environ.get('DATABASE_URL'))
    

def is_valid_uuid(val):
    """Utility to prevent server crashes from invalid UUID formats."""
    try:
        uuid.UUID(str(val))
        return True
    except ValueError:
        return False

@app.route('/track/<project_id>')
def track_and_redirect(project_id):
    """
    The main interceptor route. 
    Expects URLs like: /track/your-uuid?target=Shopify&source=click
    """
    # 1. Security Check: Ensure the ID is a valid UUID format
    if not is_valid_uuid(project_id):
        abort(400, description="Invalid Project ID format.")

    # 2. Extract Analytics Metadata
    target_company = request.args.get('target', 'General')
    user_agent = request.headers.get('User-Agent', 'Unknown Device')
    
    # Extract the interaction type. Default to 'scan' if missing.
    raw_source = request.args.get('source', 'scan').lower()
    
    # 3. Database Guardrail: Ensure it perfectly matches our CHECK constraint
    interaction_type = 'click' if raw_source == 'click' else 'scan'

    conn = None
    try:
        conn = get_db_connection()
        
        with conn.cursor() as cur:
            # 4. Look up the destination URL for this project
            cur.execute('SELECT destination_url FROM projects WHERE id = %s;', (project_id,))
            result = cur.fetchone()
            
            if result is None:
                abort(404, description="Project not found in database.")
                
            destination_url = result[0]
            
            # 5. Log the specific interaction event into our new table!
            cur.execute(
                '''
                INSERT INTO tracking_events (project_id, interaction_type, target_company, user_agent)
                VALUES (%s, %s, %s, %s);
                ''',
                (project_id, interaction_type, target_company, user_agent)
            )
            
            conn.commit()
            
            print(f"[ANALYTICS] Logged {interaction_type.upper()} for {target_company} -> Redirecting to {destination_url}")
            
            # 6. Bounce the user to their final destination
            return redirect(destination_url, code=302)

    except Exception as e:
        print(f"[ERROR] Database operation failed: {e}")
        abort(500, description="Internal Server Error while processing tracking event.")
        
    finally:
        if conn is not None:
            conn.close()

if __name__ == '__main__':
    print("Starting QR Tracking Server on port 5001...")
    app.run(debug=True, port=5001)