import sys
import os
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from harvester import fetch_wikitext, extract_citations_and_claims, fetch_citation_timestamp, make_api_request

batch_count = 0

def traced_api_request(params):
    global batch_count
    batch_count += 1
    
    data = make_api_request(params)
    
    pages = data.get("query", {}).get("pages", {})
    if pages:
        page = list(pages.values())[0]
        revisions = page.get("revisions", [])
        num_revs = len(revisions)
    else:
        num_revs = 0
        
    rvcontinue = data.get("continue", {}).get("rvcontinue", "None (End of history)")
    
    print(f"Batch {batch_count}: Received {num_revs} revisions. Next rvcontinue token: {rvcontinue}")
    return data

def run_test():
    title = "Vine (service)"
    print(f"Testing pagination trace for article: {title}")
    
    wikitext = fetch_wikitext(title)
    extracted = extract_citations_and_claims(wikitext)
    
    if not extracted:
        print("No citations found.")
        return
        
    target = extracted[0]
    print(f"\nTarget Citation URL: {target['url']}")
    print("-" * 50)
    
    global batch_count
    batch_count = 0
    
    with patch('harvester.make_api_request', side_effect=traced_api_request):
        insertion_date, reliable, revid = fetch_citation_timestamp(title, target["url"])
        
    print("-" * 50)
    print(f"Match logic completed! Selected Revision ID: {revid}")
    
    target["insertion_date"] = insertion_date
    target["timestamp_reliable"] = reliable
    target["revid"] = revid
    
    print("\nFinal Citation Payload:")
    for k, v in target.items():
        print(f"  {k}: {v}")

if __name__ == "__main__":
    run_test()
