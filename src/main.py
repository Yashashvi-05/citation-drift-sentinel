import time
import json
from harvester import harvest_citations
from snapshot import fetch_snapshots
from analyzer import analyze_drift

def determine_status(analysis: dict) -> str:
    if analysis.get('error'):
        return "API ERROR"
        
    archived_supports = analysis.get('archived_supports_claim')
    live_supports = analysis.get('live_supports_claim')
    
    if archived_supports and live_supports:
        return "VERIFIED"
    elif archived_supports and not live_supports:
        return "DRIFT DETECTED"
    elif not archived_supports and not live_supports:
        return "ORIGINALLY INVALID"
    else:
        return "NEWLY SUPPORTED"

def run_sentinel(article_title: str, max_citations: int = 5, debug: bool = False):
    print("=" * 60)
    print(f"CITATION DRIFT SENTINEL: Initializing run for '{article_title}'")
    print("=" * 60)
    
    print("Fetching citations and resolving historical timestamps...")
    try:
        citations = harvest_citations(article_title)[:max_citations]
    except Exception as e:
        print(f"CRITICAL: Failed to harvest citations: {e}")
        return
        
    print(f"Harvested {len(citations)} citations to analyze.\n")
    
    for idx, citation in enumerate(citations):
        try:
            claim = citation.get('claim', '')
            url = citation.get('url', '')
            insertion_date = citation.get('insertion_date', '')
            
            print(f"--- Citation {idx + 1} ---")
            print(f"Claim: {claim}")
            print(f"URL: {url}")
            
            result = fetch_snapshots(url, insertion_date)
            
            meta = result.get('snapshot_metadata') or {}
            
            if not meta or meta.get('is_stale'):
                print("WARNING: Snapshot is missing or stale (>365 days). Skipping analysis.\n")
                continue
                
            if not result.get('archived_text') or not result.get('live_text'):
                print("WARNING: Live or archived text could not be extracted. Skipping analysis.\n")
                continue
                
            analysis = analyze_drift(claim, result['archived_text'], result['live_text'], escalated=False)
            if debug:
                print(f"RAW JSON (Pass 1):\n{json.dumps(analysis, indent=2)}")
                
            status_text = determine_status(analysis)
            if status_text == "API ERROR":
                print(f"Status: API ERROR")
                print(f"Reasoning: {analysis.get('reasoning')}\n")
                continue
            
            if analysis.get('confidence') == "low":
                print("Low confidence detected, escalating prompt...")
                analysis = analyze_drift(claim, result['archived_text'], result['live_text'], escalated=True)
                if debug:
                    print(f"RAW JSON (Pass 2 - Escalated):\n{json.dumps(analysis, indent=2)}")
                    
                status_text = determine_status(analysis)
                if status_text == "API ERROR":
                    print(f"Status: API ERROR")
                    print(f"Reasoning: {analysis.get('reasoning')}\n")
                    continue
                
            confidence = analysis.get('confidence', 'unknown')
            reasoning = analysis.get('reasoning', 'No reasoning provided')
            
            print(f"Status: {status_text}")
            print(f"Confidence: {confidence.upper()}")
            print(f"Reasoning: {reasoning}\n")
            
            time.sleep(2)
            
        except Exception as e:
            print(f"ERROR: Failed to process citation {idx + 1}: {e}\n")
            continue

if __name__ == "__main__":
    run_sentinel("Python (programming language)", max_citations=3, debug=False)
