import sys
import os
import json
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from harvester import harvest_citations
from snapshot import fetch_snapshots
from analyzer import analyze_drift
from main import determine_status
from groq import Groq
import dotenv

dotenv.load_dotenv()

def analyze_baseline(claim: str, live_text: str) -> bool:
    if not live_text:
        return None
        
    client = Groq(timeout=15.0)
    system_prompt = """You are an AI tasked with analyzing citation drift.
You will be provided with a 'Claim' and a 'Live Text' (what the citation currently says).
Evaluate if the Live Text supports the Claim.

You must output your analysis in JSON format exactly matching this schema:
{
  "live_supports_claim": bool
}"""

    user_prompt = f"Claim: {claim}\n\nLive Text: {live_text}"

    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model="qwen/qwen3.8-27b",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.0
            )
            content = response.choices[0].message.content
            result = json.loads(content)
            return result.get("live_supports_claim", False)
        except Exception as e:
            time.sleep(2 ** attempt)
            continue
            
    return None

import memory

def run_evaluation():
    memory.init_db()
    articles = [
        "Google Reader",
        "Yahoo Groups",
        "Windows Phone",
        "Vine (service)",
        "Myspace"
    ]
    
    output_file = "evaluation_results.jsonl"
    
    print(f"{'Article':<16} | {'Citation URL':<30} | {'Baseline Live Support':<21} | {'Sentinel Live Support':<21} | {'Sentinel Verdict':<20} | {'Reliable TS?'}")
    print("-" * 135)
    
    for article in articles:
        try:
            citations = harvest_citations(article, limit=3)
        except Exception as e:
            print(f"{article[:15]:<16} | {'ERROR: Harvester failed':<30} | {'-':<21} | {'-':<21} | {'ERROR':<20} | {'-'}")
            continue
            
        for citation in citations:
            claim = citation.get('claim', '')
            url = citation.get('url', '')
            insertion_date = citation.get('insertion_date', '')
            reliable = citation.get('timestamp_reliable', False)
            
            try:
                result = fetch_snapshots(url, insertion_date)
                live_text = result.get('live_text', '')
                archived_text = result.get('archived_text', '')
                meta = result.get('snapshot_metadata') or {}
                is_stale = meta.get('is_stale', False)
                
                cached = memory.get_cache(article, url, live_text, source='eval')
                if cached:
                    baseline_live = cached['baseline_live']
                    sentinel_live = cached['sentinel_live']
                    sentinel_archived = cached['sentinel_archived']
                    sentinel_status = cached['sentinel_status']
                    print("[Cache Hit (eval)]")
                else:
                    # Baseline Pass
                    baseline_live = analyze_baseline(claim, live_text)
                    
                    # Sentinel Pass
                    if not meta or is_stale or not archived_text:
                        sentinel_status = "ERROR"
                        sentinel_live = None
                        sentinel_archived = None
                    else:
                        analysis = analyze_drift(claim, archived_text, live_text, escalated=False)
                        if not analysis.get('error') and analysis.get('confidence') == "low":
                            analysis = analyze_drift(claim, archived_text, live_text, escalated=True)
                            
                        sentinel_status = determine_status(analysis)
                        if sentinel_status == "DEAD_LINK":
                            sentinel_live = None
                            sentinel_archived = analysis.get('archived_supports_claim', False)
                        elif sentinel_status == "API ERROR":
                            sentinel_live = None
                            sentinel_archived = None
                        else:
                            sentinel_live = analysis.get('live_supports_claim', False)
                            sentinel_archived = analysis.get('archived_supports_claim', False)
                        
                    if sentinel_status != "ERROR":
                        memory.set_cache(
                            article=article,
                            url=url,
                            live_text=live_text,
                            source='eval',
                            sentinel_status=sentinel_status,
                            sentinel_live=sentinel_live,
                            sentinel_archived=sentinel_archived,
                            baseline_live=baseline_live
                        )
                    
                payload = {
                    "article": article,
                    "citation_url": url,
                    "claim": claim,
                    "archived_text_snippet": archived_text[:500] if archived_text else "",
                    "live_text_snippet": live_text[:500] if live_text else "",
                    "baseline_live_supports": baseline_live,
                    "sentinel_live_supports": sentinel_live,
                    "sentinel_archived_supports": sentinel_archived,
                    "sentinel_status": sentinel_status,
                    "timestamp_reliable": reliable,
                    "is_stale": is_stale
                }
                
                with open(output_file, "a", encoding="utf-8") as f:
                    f.write(json.dumps(payload) + "\n")
                    
                b_str = str(baseline_live) if baseline_live is not None else "None"
                s_str = str(sentinel_live) if sentinel_status != "ERROR" else "None"
                ts_str = str(reliable)
                
                print(f"{article[:15]:<16} | {url[:29]:<30} | {b_str:<21} | {s_str:<21} | {sentinel_status:<20} | {ts_str}")
                
                time.sleep(2)
                
            except Exception as e:
                print(f"{article[:15]:<16} | {url[:29]:<30} | {'-':<21} | {'-':<21} | {'ERROR':<20} | {'-'}")

if __name__ == "__main__":
    run_evaluation()
