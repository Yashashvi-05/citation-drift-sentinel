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

## Phase 6 Benchmark Results

Based on a 15-citation evaluation dataset across heavily edited tech-history articles, the Sentinel was benchmarked against a naive, single-pass LLM (Baseline). 

Comparing the baseline against the Sentinel's orchestration exposes three distinct limitations of standard LLM fact-checking:

* **20% Raw Accuracy Disagreements (2/10 viable citations):** The baseline's evaluation of the live text was flatly wrong. It either failed to extract support that existed (False Negative) or lazily validated support that was never there (False Positive). Sentinel caught and corrected both.
* **20% Structural Blind-Spot Findings (2/10 viable citations):** The baseline correctly evaluated the live page as unsupported, but falsely penalized the Wikipedia editor. Because it lacks historical memory, it could not detect that the claim was perfectly valid when inserted and had simply decayed over time (Citation Drift). Sentinel's Wayback Machine integration proved historical validity.
* **9% Dead-Link Handling (1/11 classified citations):** When a source was completely dead (404), the baseline pipeline threw a null exception. Sentinel gracefully caught and categorized this as a `DEAD_LINK`, preserving critical metadata about internet decay rather than discarding the data.

## Known Limitations

* **Wikipedia API Pagination Limit:** The initial "quiet article" workaround (restricting checks to low-edit articles to bypass the `rvlimit=50` ceiling) was tested empirically and abandoned, as 4 out of 5 tech-history candidates (including Google Reader and Vine) immediately hit the limit. Instead, true `rvcontinue` pagination was implemented. To balance deep-history accuracy against runaway API loops on heavily edited articles, pagination is bounded by a 10-batch safety cap (up to 500 revisions per citation). If a citation's insertion point is found within this cap, it is flagged with `timestamp_reliable: True`. If the cap is exhausted before the insertion point is found, the timestamp defaults to the oldest revision fetched and is flagged as unreliable.
* **LLM Confidence Blindspot:** During testing, the LLM's self-reported confidence failed to naturally trigger the escalation branch, even when it exhibited genuine reasoning gaps (e.g., falsely verifying an unsupported claim). This architectural finding necessitates moving away from relying on self-reported confidence as an escalation trigger in future iterations.
* **Wayback Machine Cache:** The local SQLite Wayback cache is implemented in `src/snapshot.py` to prevent API rate limits and ensure temporal safety, but it is currently preempted by the higher-level evaluation cache in our locked dataset and remains unexercised in the standard run.

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
