import sqlite3
import json
from datetime import datetime

DATABASE_NAME = "ai_overview_analysis.db"

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row  # Access columns by name
    return conn

def init_db():
    """Initializes the database schema."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Table for keywords
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS keywords (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        keyword TEXT UNIQUE NOT NULL,
        client_id INTEGER, -- Placeholder for multi-client support
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Table for SERP results
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS serp_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        keyword_id INTEGER NOT NULL,
        search_datetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        raw_serp_data TEXT, -- Store the full JSON response from SerpData
        ai_overview_sources TEXT, -- JSON string of AI overview sources
        organic_results TEXT, -- JSON string of organic results
        people_also_ask TEXT, -- JSON string of PAA
        related_searches TEXT, -- JSON string of related searches
        ads_data TEXT, -- JSON string of ads data
        FOREIGN KEY (keyword_id) REFERENCES keywords (id)
    )
    """)

    # Table for LLM analysis results
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS analysis_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        serp_result_id INTEGER NOT NULL,
        analysis_type TEXT NOT NULL, -- e.g., 'ai_overview_opportunities', 'content_gaps'
        llm_model TEXT,
        insights TEXT, -- JSON string of insights from LLM
        recommendations TEXT, -- JSON string of recommendations
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (serp_result_id) REFERENCES serp_results (id)
    )
    """)
    conn.commit()
    conn.close()
    print("Database initialized successfully.")

def store_keyword(keyword, client_id=None):
    """Stores a new keyword and returns its ID. If keyword exists, returns existing ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO keywords (keyword, client_id) VALUES (?, ?)", (keyword, client_id))
        keyword_id = cursor.lastrowid
        conn.commit()
    except sqlite3.IntegrityError: # Keyword already exists
        cursor.execute("SELECT id FROM keywords WHERE keyword = ?", (keyword,))
        keyword_id = cursor.fetchone()["id"]
    finally:
        conn.close()
    return keyword_id

def store_serp_data(keyword_id, raw_serp_data, ai_overview_sources, organic_results, people_also_ask, related_searches, ads_data):
    """Stores SERP data linked to a keyword ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO serp_results (keyword_id, raw_serp_data, ai_overview_sources, organic_results, people_also_ask, related_searches, ads_data)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (keyword_id,
          json.dumps(raw_serp_data),
          json.dumps(ai_overview_sources),
          json.dumps(organic_results),
          json.dumps(people_also_ask),
          json.dumps(related_searches),
          json.dumps(ads_data)
          ))
    serp_result_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return serp_result_id

def store_llm_analysis(serp_result_id, analysis_type, llm_model, insights, recommendations):
    """Stores LLM analysis results."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO analysis_results (serp_result_id, analysis_type, llm_model, insights, recommendations)
    VALUES (?, ?, ?, ?, ?)
    """, (serp_result_id, analysis_type, llm_model, json.dumps(insights), json.dumps(recommendations)))
    analysis_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return analysis_id

def get_serp_results_by_keyword(keyword):
    """Retrieves all SERP results for a given keyword, ordered by most recent."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT sr.* FROM serp_results sr
    JOIN keywords k ON sr.keyword_id = k.id
    WHERE k.keyword = ?
    ORDER BY sr.search_datetime DESC
    """, (keyword,))
    results = cursor.fetchall()
    conn.close()
    return [dict(row) for row in results]


if __name__ == '__main__':
    init_db()
    # Example Usage
    kw_id = store_keyword("test keyword")
    print(f"Stored keyword 'test keyword' with ID: {kw_id}")

    kw_id_existing = store_keyword("test keyword")
    print(f"Attempting to store existing keyword 'test keyword', ID: {kw_id_existing}")

    # Dummy data for SERP and Analysis
    dummy_serp = {"results": {"organic_results": [{"title": "Test"}]}}
    dummy_ai_sources = [{"title": "AI Source 1"}]
    dummy_organic = [{"title": "Organic Result 1"}]
    dummy_paa = [{"question": "What is test?"}]
    dummy_related = ["test searches"]
    dummy_ads = [{"title": "Test Ad"}]

    serp_id = store_serp_data(kw_id, dummy_serp, dummy_ai_sources, dummy_organic, dummy_paa, dummy_related, dummy_ads)
    print(f"Stored SERP data with ID: {serp_id}")

    dummy_insights = {"gaps": ["gap1"], "opportunities": ["opp1"]}
    dummy_recs = {"actions": ["action1"]}
    analysis_id = store_llm_analysis(serp_id, "ai_overview_test", "claude-test", dummy_insights, dummy_recs)
    print(f"Stored LLM analysis with ID: {analysis_id}")

    retrieved_serps = get_serp_results_by_keyword("test keyword")
    print(f"\nRetrieved SERPs for 'test keyword':")
    for r_serp in retrieved_serps:
        print(f"  ID: {r_serp['id']}, Date: {r_serp['search_datetime']}")
        # print(f"  Raw Data: {json.loads(r_serp['raw_serp_data'])}") # Can be very verbose
        print(f"  AI Overview Sources: {json.loads(r_serp['ai_overview_sources'])}")
        # Further parsing of other JSON fields can be added here

    if not retrieved_serps:
        print("No SERP data found for 'test keyword'.")
