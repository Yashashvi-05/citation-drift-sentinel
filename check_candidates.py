import requests
import json

USER_AGENT = "CitationDriftSentinelBot/1.0 (dev@sentinel.org)"
BASE_URL = "https://en.wikipedia.org/w/api.php"

def check_candidates(titles):
    print(f"{'Article Title':<30} | {'Count (<=50)':<13} | {'Hits 50-Ceiling?':<16} | {'Oldest Revision Date':<20} | {'Safe for Eval?'}")
    print("-" * 105)
    
    for title in titles:
        params = {
            "action": "query",
            "prop": "revisions",
            "titles": title,
            "rvprop": "ids|timestamp",
            "rvlimit": 50,
            "rvdir": "older",
            "format": "json"
        }
        
        try:
            response = requests.get(BASE_URL, params=params, headers={"User-Agent": USER_AGENT})
            response.raise_for_status()
            data = response.json()
            
            pages = data.get("query", {}).get("pages", {})
            page = list(pages.values())[0]
            
            if "missing" in page:
                print(f"{title:<30} | {'0':<13} | {'No':<16} | {'N/A':<20} | {'No (Missing)'}")
                continue
                
            revisions = page.get("revisions", [])
            count = len(revisions)
            
            # Check if there is a 'continue' token which indicates there are more revisions older than our limit
            hits_ceiling = "continue" in data
            
            if count > 0:
                oldest_rev = revisions[-1].get("timestamp", "N/A")
            else:
                oldest_rev = "N/A"
                
            safe = "No" if hits_ceiling else "Yes"
            
            print(f"{title[:29]:<30} | {count:<13} | {'Yes' if hits_ceiling else 'No':<16} | {oldest_rev:<20} | {safe}")
            
        except Exception as e:
            print(f"{title:<30} | Error: {str(e)[:50]}")

if __name__ == "__main__":
    CANDIDATES = [
    "Google Reader",
    "Yahoo! Groups",
    "Windows Phone",
    "Vine (service)",
    "Myspace"
]
    check_candidates(CANDIDATES)
