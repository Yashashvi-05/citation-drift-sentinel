import requests
import time
from datetime import datetime
from bs4 import BeautifulSoup

USER_AGENT = "CitationDriftSentinelBot/1.0 (https://github.com/citation-drift-sentinel; dev@sentinel.org)"

def make_api_request(url: str, params: dict = None, timeout: int = 10) -> requests.Response:
    headers = {"User-Agent": USER_AGENT}
    for attempt in range(3):
        try:
            response = requests.get(url, params=params, headers=headers, timeout=timeout)
            if response.status_code == 429 or 500 <= response.status_code < 600:
                time.sleep(2 ** attempt)
                continue
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)
    # Fallback to raise in case loop finishes without return (e.g. 500s all 3 times)
    response.raise_for_status()
    return response

def extract_clean_text(html_content: str) -> str:
    # LIMITATION: Archived Wayback pages include Internet Archive's own injected toolbar/banner HTML.
    # This injected text could eat into the 5000-character extraction limit and crowd out real article content.
    # Needs review against real archived text.
    soup = BeautifulSoup(html_content, 'html.parser')
    for tag in soup(["script", "style"]):
        tag.decompose()
    text = soup.get_text(separator=' ', strip=True)
    return text[:5000]

def get_wayback_snapshot(url: str, iso_timestamp: str) -> dict:
    try:
        dt = datetime.strptime(iso_timestamp[:19], "%Y-%m-%dT%H:%M:%S")
    except ValueError:
        dt = datetime.utcnow()
        
    target_date = dt.strftime("%Y%m%d")
    
    api_url = "http://archive.org/wayback/available"
    params = {
        "url": url,
        "timestamp": target_date
    }
    
    try:
        response = make_api_request(api_url, params=params)
        data = response.json()
    except Exception:
        return None
        
    snapshots = data.get("archived_snapshots", {})
    closest = snapshots.get("closest")
    
    if not closest or not closest.get("available"):
        return None
        
    snapshot_url = closest.get("url")
    snapshot_timestamp = closest.get("timestamp")
    
    try:
        snap_dt = datetime.strptime(snapshot_timestamp, "%Y%m%d%H%M%S")
        delta = abs((snap_dt - dt).days)
    except ValueError:
        delta = 0
        
    is_stale_snapshot = delta > 365
    
    return {
        "url": snapshot_url,
        "timestamp": snapshot_timestamp,
        "gap_days": delta,
        "is_stale": is_stale_snapshot
    }

def fetch_snapshots(url: str, insertion_date: str) -> dict:
    live_text = ""
    archived_text = ""
    snapshot_metadata = None
    
    try:
        live_response = make_api_request(url)
        live_text = extract_clean_text(live_response.text)
    except Exception:
        pass
        
    try:
        snapshot_metadata = get_wayback_snapshot(url, insertion_date)
        if snapshot_metadata and snapshot_metadata.get("url"):
            # Ensure URL has http/https
            wayback_url = snapshot_metadata["url"]
            if wayback_url.startswith("http://") and not wayback_url.startswith("https://"):
                # sometimes wayback gives http instead of https, standard
                pass
            archived_response = make_api_request(wayback_url)
            archived_text = extract_clean_text(archived_response.text)
    except Exception:
        pass
        
    return {
        "live_text": live_text,
        "archived_text": archived_text,
        "snapshot_metadata": snapshot_metadata
    }

if __name__ == "__main__":
    url = "https://github.com"
    # Forcing a massive gap: GitHub didn't exist in 1990.
    target_date = "1990-01-01T12:00:00Z"
    
    print(f"Testing URL: {url} at {target_date}")
    results = fetch_snapshots(url, target_date)
    print(f"Snapshot Metadata: {results.get('snapshot_metadata')}")