# Citation Drift Sentinel

Citation Drift Sentinel is an automated, multi-agent architecture designed to detect "citation drift" in Wikipedia articles. It harvests citations, identifies their insertion dates, retrieves historical snapshots of the linked sources via the Internet Archive, and uses an LLM to determine if the current live source still supports the originally cited claim.

## The Problem
Wikipedia editors who patrol high-traffic or contentious articles rely on citations to back every factual claim. But a citation that was accurate the day it was added can silently stop being accurate later — the source page gets rewritten, redirected, or taken down entirely — while the Wikipedia claim stays frozen, still presented as "supported."

This is **citation drift**, and it's distinct from ordinary link rot: a dead link is obvious and gets flagged automatically. A link that's still *alive* but no longer supports the claim it was cited for is invisible. There is currently no scalable way for an editor to detect this short of manually rereading every source on every article they watch — indefinitely.

Naive automated approaches make this worse, not better: a single-pass LLM check against the *current* live page has no way to distinguish "this claim was never true" from "this claim was true and the source changed underneath it." In practice, that means naive verification tools risk falsely flagging honest editors for citing sources that decayed long after they cited them correctly.

## Live Demo
* **Deployed Dashboard:** [https://citation-drift-sentinel-dyswhg8n3ff38ttgk7ssts.streamlit.app/](https://citation-drift-sentinel-dyswhg8n3ff38ttgk7ssts.streamlit.app/) — explore the full 15-citation dataset, benchmark comparison, and visual diffs live, with zero setup.
* **Video Walkthrough:** [link once uploaded]
* **Full Evidence:** [`BENCHMARK_REPORT.md`](./BENCHMARK_REPORT.md) · [`ESCALATION_TRACE.log`](./ESCALATION_TRACE.log) · [`evaluation_results.jsonl`](./evaluation_results.jsonl) (raw dataset)

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

## Improvement Changelog

Every iteration below was driven by a real failure discovered during evaluation, not planned in advance.

| Stage | What we tried | What we found | Decision |
|---|---|---|---|
| Baseline | Single-pass LLM check against the live page only, no archive, no memory, no verification | Cannot distinguish "never true" from "was true, source changed" | Established starting point for comparison |
| Iteration 1 | Fixed insertion-date lookup: fetch each citation's revision history once per article instead of once per citation | Eliminated a Wikipedia API rate-limit storm (HTTP 429) caused by redundant calls | Kept — this became the base for the pagination cache |
| Iteration 2 | Added `rvcontinue` pagination (capped at 10 batches/500 revisions) to find true citation insertion dates | The original 50-revision-lookback approach silently returned wrong dates on heavily-edited articles; confirmed via manual cross-check against Wikipedia's actual edit history | Kept, with `timestamp_reliable` flag for transparency on the cap |
| Iteration 3 | Fixed status-determination logic to derive verdicts directly from `archived_supports_claim`/`live_supports_claim` instead of a single `drift_detected` boolean | Caught a real case where the LLM's own reasoning showed a claim was never supported, but the old logic still labeled it "VERIFIED" | Kept — this is now the 4-state taxonomy |
| Iteration 4 | Added `DEAD_LINK` as its own terminal status instead of merging fetch failures into a generic error | Realized dead sources are a distinct, meaningful finding (source death), not noise — the naive baseline throws an unhandled exception on these | Kept — dead-link handling is now a scored category in our benchmark |
| Iteration 5 | Added a confidence-based escalation retry in the Analyzer | Verified the retry mechanism genuinely changes verdicts when triggered (forced test case), though see Hot Take below | Kept |
| Iteration 6 | Added a persistent SQLite memory layer with content-hash caching | Found and fixed a negative-caching bug where transient API failures were being permanently cached as errors | Kept, with error states explicitly excluded from caching |
| Iteration 7 | Added verbatim quote guardrails with programmatic substring verification | Ensures a "supporting quote" from the LLM is checked against the actual source text, not trusted on its word | Kept |
| Iteration 8 | Added an adversarial evaluation suite (subtle date mutation, negation injection) | Confirmed the Analyzer's reasoning genuinely catches both cases, rather than doing lazy semantic matching | Kept |
| Final | Combined pipeline, deployed as a public dashboard | 15/15 citations processed cleanly with full traceable evidence | Current state |

## Known Limitations

* **Wikipedia API Pagination Limit:** The initial "quiet article" workaround (restricting checks to low-edit articles to bypass the `rvlimit=50` ceiling) was tested empirically and abandoned, as 4 out of 5 tech-history candidates (including Google Reader and Vine) immediately hit the limit. Instead, true `rvcontinue` pagination was implemented. To balance deep-history accuracy against runaway API loops on heavily edited articles, pagination is bounded by a 10-batch safety cap (up to 500 revisions per citation). If a citation's insertion point is found within this cap, it is flagged with `timestamp_reliable: True`. If the cap is exhausted before the insertion point is found, the timestamp defaults to the oldest revision fetched and is flagged as unreliable.
* **Wayback Machine Cache:** The local SQLite Wayback cache is implemented in `src/snapshot.py` to prevent API rate limits and ensure temporal safety, but it is currently preempted by the higher-level evaluation cache in our locked dataset and remains unexercised in the standard run.

## Hot Take

The LLM's self-reported `confidence` field does not reliably track whether it's actually correct. Across every real (non-forced) citation we tested, the model returned "high" confidence — including on a citation where its own written reasoning showed a genuine logic gap (it correctly noted the source text didn't support the claim, but still labeled the result "high confidence VERIFIED" due to a separate mapping bug we later fixed).

Our confidence-based escalation retry works when it's manually triggered — a forced test case showed the escalated pass catching an error the first pass missed. But because the model almost never self-reports low confidence in practice, that safety net rarely fires on its own. This is a real, measured finding, not a hypothetical: **if you're building agentic verification and betting on an LLM's self-reported confidence as your quality gate, verify that the model's confidence is actually calibrated to its correctness before trusting it as a trigger.** A better design would likely escalate whenever `archived_supports_claim` and `live_supports_claim` disagree, regardless of stated confidence — since that's the case where a second, more careful pass matters most.

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
