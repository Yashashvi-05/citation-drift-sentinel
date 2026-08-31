import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
from snapshot import fetch_snapshots
import memory

def main():
    db_path = "temp_fallback.db"
    os.environ['SENTINEL_DB_PATH'] = db_path
    memory.DB_PATH = db_path
    memory.init_db()
    
    url = "http://massless.org/default.php"
    timestamp = "2010-01-01T00:00:00Z"
    
    print(f"Testing Wayback fallback logic for: {url}")
    
    # This will trigger Tier 2 or 3 and print the success tier to stdout
    result = fetch_snapshots(url, timestamp)
    
    meta = result.get('snapshot_metadata')
    if meta:
        print(f"Final resolved URL: {meta['url']}")
    else:
        print("Failed to resolve URL across all tiers.")
        
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except:
            pass

if __name__ == "__main__":
    main()
