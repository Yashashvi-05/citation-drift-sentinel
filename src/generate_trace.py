import os
import sys
import json
import time
from contextlib import redirect_stdout

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harvester import harvest_citations
from snapshot import fetch_snapshots
from analyzer import analyze_drift
from main import determine_status
import memory

def evaluate_citation(target_url, target_claim, debug=True):
    memory.init_db()
    print("Harvesting Yahoo Groups to find the correct insertion date...")
    citations = harvest_citations("Yahoo Groups", limit=10)
    
    citation = next((c for c in citations if target_url in c.get('url', '')), None)
    if not citation:
        print("Could not find the target citation in the harvested list.")
        return
        
    insertion_date = citation.get('insertion_date')
    print(f"Found insertion date: {insertion_date}")
    
    print(f"--- Citation ---")
    print(f"Claim: {target_claim}")
    print(f"URL: {target_url}")
    
    result = fetch_snapshots(target_url, insertion_date)
    meta = result.get('snapshot_metadata') or {}
    
    if not meta or meta.get('is_stale'):
        print("WARNING: Snapshot is missing or stale (>365 days).")
        return
        
    if not result.get('archived_text'):
        print("WARNING: Archived text could not be extracted.")
        return
        
    # Force bypass of get_cache to guarantee live LLM hit for the trace
    analysis = analyze_drift(target_claim, result['archived_text'], result['live_text'], escalated=False)
    if debug:
        print(f"RAW JSON (Pass 1):\n{json.dumps(analysis, indent=2)}")
        
    status_text = determine_status(analysis)
    if status_text == "API ERROR":
        print(f"Status: API ERROR")
        print(f"Reasoning: {analysis.get('reasoning')}\n")
        return
        
    if analysis.get('confidence') == "low":
        print("Low confidence detected, escalating prompt...")
        analysis = analyze_drift(target_claim, result['archived_text'], result['live_text'], escalated=True)
        if debug:
            print(f"RAW JSON (Pass 2 - Escalated):\n{json.dumps(analysis, indent=2)}")
            
        status_text = determine_status(analysis)
        
    confidence = analysis.get('confidence', 'unknown')
    reasoning = analysis.get('reasoning', 'No reasoning provided')
    
    print(f"Status: {status_text}")
    print(f"Confidence: {confidence.upper()}")
    print(f"Reasoning: {reasoning}\n")


def generate_trace():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    trace_path = os.path.join(base_dir, 'ESCALATION_TRACE.log')
    temp_db = os.path.join(base_dir, 'temp_trace.db')

    print("Generating live escalation trace (1 citation)...")

    # Force a live API call by pointing the cache to a temporary, empty database
    os.environ['SENTINEL_DB_PATH'] = temp_db 
    memory.DB_PATH = temp_db

    # We use Yahoo Groups because we know it triggers the historical fallback
    url = "https://help.yahoo.com/kb/groups/SLN35505.html"
    claim = "Yahoo Groups to shut down on December 15, 2020"

    with open(trace_path, 'w', encoding='utf-8') as f:
        f.write("=== AGENT ESCALATION & ORCHESTRATION TRACE ===\n")
        f.write("Target: Yahoo Groups (SLN35505.html)\n")
        f.write("-" * 60 + "\n")
        with redirect_stdout(f):
            try:
                evaluate_citation(url, claim, debug=True)
            except Exception as e:
                print(f"Error during trace generation: {e}")

    # Clean up the temporary cache
    if os.path.exists(temp_db):
        try:
            os.remove(temp_db)
        except:
            pass

    print(f"Trace log generated successfully at {trace_path}")

if __name__ == '__main__':
    generate_trace()
