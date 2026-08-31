# Reproducing the Phase 6 Benchmark

This guide provides the exact steps to reproduce the 15-citation benchmark dataset comparing the naive Baseline LLM against the Citation Drift Sentinel orchestration pipeline.

## 1. Clean Environment Setup
Open a PowerShell terminal and configure a clean virtual environment:

```powershell
cd D:\Projects\citation-drift-sentinel
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

## 2. API Configuration
You must provide a valid Groq API key to execute the language models.
Create a `.env` file in the project root and add your key:

```env
GROQ_API_KEY=your_api_key_here
```

## 3. Model Specifications
**CRITICAL:** To perfectly reproduce the Phase 6 Benchmark results, the exact model identifier used during the test must remain hardcoded in `src/analyzer.py` and `run_evaluation.py`.

* **Model Identifier:** `qwen/qwen3.8-27b`

Do not change this identifier, as different models (e.g., Llama 3) exhibit different reasoning behaviors and will shift the baseline comparison.

## 4. Execution
Run the automated evaluation harness. The script has built-in retry and pagination capping, but it will take a few minutes to traverse the deep Wikipedia histories and process the Wayback Machine queries.

```powershell
python run_evaluation.py
```

## 5. Judge Verification Procedures
Upon completion, the system will output a clean console table and incrementally write the full dataset to `evaluation_results.jsonl`.

To manually audit and verify the pipeline's classification accuracy:
1. Open `evaluation_results.jsonl`.
2. For each citation, compare the `archived_text_snippet` and `live_text_snippet` against the `claim`.
3. Check the `baseline_live_supports` boolean (the naive LLM's guess) against the `sentinel_live_supports` boolean (the Orchestrator's verified output). 
4. Confirm that missing live texts correctly resolved to the `DEAD_LINK` status and that the underlying taxonomy states (`VERIFIED`, `DRIFT DETECTED`, `ORIGINALLY INVALID`, `NEWLY SUPPORTED`) perfectly match the manual ground-truth evaluation of the snippets.

## ⚠️ API Quota Constraints (Groq Free Tier)
A full, un-cached evaluation run of the baseline dataset (15 citations) consumes approximately **199,000 tokens**. The Groq free tier imposes a strict limit of 200,000 tokens per day (TPD). 
Because of this, **a full live run can reliably be executed only once per day per API key.** Subsequent live runs on the same day will fail with a 429 Rate Limit error. To bypass this for testing, ensure the local `sentinel_cache.db` is present to intercept network calls.
