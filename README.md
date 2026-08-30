# Citation Drift Sentinel

Citation Drift Sentinel is an automated, multi-agent architecture designed to detect "citation drift" in Wikipedia articles. It harvests citations, identifies their insertion dates, retrieves historical snapshots of the linked sources via the Internet Archive, and uses an LLM to determine if the current live source still supports the originally cited claim.

## Core Architecture

The Sentinel operates via four core components:

* **Harvester (Agent 1):** Scrapes Wikipedia articles for citations using the Wikipedia Action API and `mwparserfromhell`. It maps external URLs to the specific sentences (claims) preceding them and approximates the citation insertion date using the article's revision history.
* **Snapshotter (Agent 2):** Connects to the Internet Archive's Wayback Availability API. It retrieves the closest historical snapshot of the citation matching its insertion date and the current live version, gracefully handling missing or stale snapshots (gap > 365 days).
* **Analyzer (Agent 3):** Uses a Groq-powered LLM (`qwen/qwen3.8-27b`) to evaluate the claim against both the archived text and the live text. It is designed with rate-limit safety (exponential backoff) and a confidence-based escalation mechanism that forces a meticulous re-evaluation if the initial confidence is low.
* **Orchestrator (Phase 4):** Coordinates the flow between Harvester, Snapshotter, and Analyzer. It enforces strict data-shape consistency, wraps operations in crash-safe logic, and maps the final LLM output into a rigid 4-state taxonomy.

## 4-State Taxonomy

The system maps LLM analysis into four distinct statuses:

* **VERIFIED:** The archived text supports the claim, AND the live text still supports the claim.
* **DRIFT DETECTED:** The archived text supports the claim, BUT the live text no longer supports the claim.
* **ORIGINALLY INVALID:** The archived text NEVER supported the claim, and the live text does not either.
* **NEWLY SUPPORTED:** The archived text did not support the claim, but the live text now does.

## Known Limitations

* **Wikipedia API Pagination Limit:** The initial "quiet article" workaround (restricting checks to low-edit articles to bypass the `rvlimit=50` ceiling) was tested empirically and abandoned, as 4 out of 5 tech-history candidates (including Google Reader and Vine) immediately hit the limit. Instead, true `rvcontinue` pagination was implemented. To balance deep-history accuracy against runaway API loops on heavily edited articles, pagination is bounded by a 10-batch safety cap (up to 500 revisions per citation). If a citation's insertion point is found within this cap, it is flagged with `timestamp_reliable: True`. If the cap is exhausted before the insertion point is found, the timestamp defaults to the oldest revision fetched and is flagged as unreliable.
* **LLM Confidence Blindspot:** During testing, the LLM's self-reported confidence failed to naturally trigger the escalation branch, even when it exhibited genuine reasoning gaps (e.g., falsely verifying an unsupported claim). This architectural finding necessitates moving away from relying on self-reported confidence as an escalation trigger in future iterations.

## Setup Instructions

Reproducing this project requires a free Groq API key.

1. **Clone and Setup Virtual Environment:**
   ```powershell
   python -m venv venv
   .\venv\Scripts\activate
   ```

2. **Install Dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables:**
   Create a `.env` file in the project root and add your Groq API key:
   ```env
   GROQ_API_KEY=your_api_key_here
   ```

## Usage

To run the Sentinel orchestrator across the configured test article:

```powershell
python src/main.py
```

## Testing

The project includes a robust test suite covering staleness math, taxonomy mapping, and API error handling. Run the tests using:

```powershell
python -m unittest discover -s tests
```
