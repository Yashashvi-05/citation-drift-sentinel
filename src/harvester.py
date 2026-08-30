import requests
import mwparserfromhell
import re
import time
from typing import List, Dict

USER_AGENT = "CitationDriftSentinelBot/1.0 (https://github.com/citation-drift-sentinel; dev@sentinel.org)"
BASE_URL = "https://en.wikipedia.org/w/api.php"

def make_api_request(params: dict) -> dict:
    headers = {"User-Agent": USER_AGENT}
    for attempt in range(3):
        try:
            response = requests.get(BASE_URL, params=params, headers=headers)
            if response.status_code == 429:
                time.sleep(2 ** attempt)
                continue
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)
    return {}

def fetch_wikitext(title: str) -> str:
    params = {
        "action": "parse",
        "page": title,
        "prop": "wikitext",
        "format": "json"
    }
    data = make_api_request(params)
    if "parse" in data and "wikitext" in data["parse"]:
        return data["parse"]["wikitext"]["*"]
    return ""

def extract_citations_and_claims(wikitext: str) -> List[Dict]:
    parsed = mwparserfromhell.parse(wikitext)
    refs = parsed.filter_tags(matches=lambda node: str(node.tag).lower() == "ref")
    marker_map = {}
    
    for idx, ref in enumerate(refs):
        url = None
        ref_raw = str(ref.contents) if ref.contents else ""
        
        if ref.contents:
            for tpl in ref.contents.filter_templates():
                if tpl.has("url"):
                    url = str(tpl.get("url").value).strip()
                    break
            if not url:
                for link in ref.contents.filter_external_links():
                    url = str(link.url).strip()
                    break
                    
        if not url:
            match = re.search(r'(https?://[^\s|\]<>{}]+)', ref_raw)
            if match:
                url = match.group(1)
                
        if url:
            marker = f"__REF_MARKER_{idx}__"
            marker_map[marker] = {
                "url": url,
                "ref_raw": str(ref)
            }
            try:
                parsed.replace(ref, marker)
            except ValueError:
                pass

    try:
        plain_text = parsed.strip_code()
    except Exception:
        plain_text = str(parsed)
        
    final_results = []
    for marker, data in marker_map.items():
        idx = plain_text.find(marker)
        if idx != -1:
            preceding_text = plain_text[:idx]
            sentences = re.split(r'(?<=[.!?])\s+', preceding_text)
            claim = sentences[-1].strip() if sentences else preceding_text.strip()
            if len(claim) < 5:
                claim = preceding_text[-200:].strip()
            claim = claim.replace('\n', ' ').strip()
            claim = re.sub(r'__REF_MARKER_\d+__', '', claim).strip()
            
            final_results.append({
                "claim": claim,
                "url": data["url"],
                "ref_raw": data["ref_raw"]
            })
    return final_results

def fetch_citation_timestamp(title: str, citation_url: str) -> tuple:
    params = {
        "action": "query",
        "prop": "revisions",
        "titles": title,
        "rvprop": "ids|timestamp|content",
        "rvslots": "main",
        "rvlimit": 50,
        "rvdir": "older",
        "format": "json"
    }
    
    oldest_timestamp = None
    oldest_revid = None
    
    for attempt in range(10):
        data = make_api_request(params)
        pages = data.get("query", {}).get("pages", {})
        if not pages:
            break
        page = list(pages.values())[0]
        revisions = page.get("revisions", [])
        if not revisions:
            break
            
        earliest_timestamp = None
        earliest_revid = None
        for rev in revisions:
            content = rev.get("slots", {}).get("main", {}).get("*", "")
            if citation_url in content:
                earliest_timestamp = rev.get("timestamp")
                earliest_revid = rev.get("revid")
            else:
                break
                
        if earliest_timestamp:
            oldest_timestamp = earliest_timestamp
            oldest_revid = earliest_revid
            if earliest_timestamp != revisions[-1].get("timestamp"):
                return oldest_timestamp, True, oldest_revid
        else:
            if oldest_timestamp:
                return oldest_timestamp, True, oldest_revid
            else:
                return revisions[0].get("timestamp", ""), False, revisions[0].get("revid")
                
        rvcontinue = data.get("continue", {}).get("rvcontinue")
        if not rvcontinue:
            return oldest_timestamp, True, oldest_revid
            
        params["rvcontinue"] = rvcontinue
        
    return oldest_timestamp or "", False, oldest_revid

def harvest_citations(title: str) -> List[Dict]:
    wikitext = fetch_wikitext(title)
    if not wikitext:
        return []
        
    extracted = extract_citations_and_claims(wikitext)
    
    results = []
    for item in extracted:
        insertion_date, reliable, revid = fetch_citation_timestamp(title, item["url"])
        results.append({
            "claim": item["claim"],
            "url": item["url"],
            "ref_raw": item["ref_raw"],
            "insertion_date": insertion_date,
            "timestamp_reliable": reliable,
            "revid": revid
        })
    return results

if __name__ == "__main__":
    title = "Python (programming language)"
    print(f"Harvesting citations for: {title}")
    citations = harvest_citations(title)
    
    for i, c in enumerate(citations[:6]):
        print(f"\n--- Citation {i+1} ---")
        print(f"Claim: {c['claim']}")
        print(f"URL: {c['url']}")
        print(f"Insertion Date: {c['insertion_date']}")
        print(f"Reliable: {c.get('timestamp_reliable')}")
