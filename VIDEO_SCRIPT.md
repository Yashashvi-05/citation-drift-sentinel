# Citation Drift Sentinel: 5-Minute Pitch Script Outline

## 1. The Problem & The Baseline Blindspot (0:00 - 1:00)
* **Hook (15s):** Wikipedia is fighting a losing battle against source decay. When automated moderation systems use standard, single-pass LLMs to verify citations, they encounter a critical structural blind spot: the model only sees the live web as it exists *today*.
* **The Failure Modes (45s):** Demonstrate the baseline's core failure modes:
  * *Point 1 (Raw Accuracy):* It hallucinates support or misses relevant context in live pages.
  * *Point 2 (Dead Links):* It throws unhandled exceptions on 404s instead of categorizing source decay.
  * *Point 3 (The Structural Flaw):* It falsely penalizes legitimate editors when an external page is rewritten or redirected, because standard LLM pipelines lack temporal awareness.

## 2. The Demo: Citation Drift in Action (1:00 - 2:45)
* **The Yahoo Groups Case Study (50s):** Walk through the `help.yahoo.com` citation.
  * Show the Baseline evaluating the live URL and returning `False` (unsupported).
  * Show the Sentinel Harvester determining the insertion date via Wikipedia API revision pagination.
  * Show the Snapshotter retrieving the matching historical snapshot from the Wayback Machine.
* **The Verdict (55s):**
  * Show the Sentinel analyzing both the live text and the historical snapshot.
  * Output the taxonomy result: `DRIFT DETECTED`.
  * *Key Soundbite:* "The editor cited a valid source. The information decayed over time. The naive baseline flags the citation as invalid; Sentinel proves its historical validity."

## 3. Benchmark Dataset & Measured Results (2:45 - 4:00)
* **The Dataset (30s):** Present the 15-citation Phase 6 benchmark across heavily edited tech-history articles.
* **The Breakdown (45s):** Detail the baseline's shortcomings across 11 classifiable citations:
  * **20% Raw Accuracy Disagreements (2/10):** Sentinel corrected baseline hallucinations and missed extractions.
  * **20% Structural Blind-Spots (2/10):** Sentinel detected citation drift where baseline was architecturally incapable of evaluating historical validity.
  * **9% Dead Link Categorization (1/11):** Sentinel cleanly classified hard 404s as `DEAD_LINK` rather than discarding them as unhandled errors.

## 4. Implemented Engineering & Roadmap (4:00 - 5:00)
* **Current Core Architecture (30s):**
  * Highlight the O(1) in-memory revision cache (`_REVISION_CACHE`) eliminating redundant Wikipedia API pagination loops.
  * Highlight the rate-limit resilience and bounded backoff routines.
* **Planned Roadmap / Phase B & C (20s):**
  * *Planned:* Persistent SQLite memory layer to skip unchanged citation hashes across runs.
  * *Planned:* Side-by-side sentence-level visual diffing for human-in-the-loop verification.
* **Closing (10s):** "Temporal orchestration is not just an optimization—it is mandatory for reliable knowledge moderation."
