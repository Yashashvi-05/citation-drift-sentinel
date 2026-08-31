import streamlit as st
import pandas as pd
import json
import glob
import os
import streamlit.components.v1 as components

st.set_page_config(layout="wide", page_title="Citation Drift Sentinel")

st.title("🛡️ Citation Drift Sentinel")
st.markdown("""
This dashboard provides a read-only view of the Sentinel evaluation pipeline. 
To ensure reproducibility without exhausting free-tier LLM limits, these results are statically served from our locked `evaluation_results.jsonl` cache and Phase B visualizations.

**Project Highlights**:
* Automated pipeline for detecting temporal and semantic citation drift.
* Tiered Wayback Machine fallback chain (CDX API to Availability API).
* Verbatim Quote Guardrails using strict substring verification.
* Validated against a synthetic Adversarial Evaluation Suite.
""")

data = []
try:
    with open("evaluation_results.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            try:
                data.append(json.loads(line.strip()))
            except json.JSONDecodeError:
                st.warning("Skipped a corrupted line in evaluation_results.jsonl.")
                continue
except FileNotFoundError:
    st.warning("No evaluation_results.jsonl found. Run the pipeline locally first.")

if data:
    df = pd.DataFrame(data)
    
    # Top-level metrics mapped strictly to the real JSONL schema
    total_analyzed = len(df)
    
    if "sentinel_status" in df.columns:
        drift_detected = len(df[df["sentinel_status"] == "DRIFT DETECTED"])
        verified = len(df[df["sentinel_status"] == "VERIFIED"])
    else:
        drift_detected = 0
        verified = 0
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Analyzed", total_analyzed)
    col2.metric("Drift Detected", drift_detected)
    col3.metric("Verified", verified)
    col4.metric("Live API Calls", 0, "Cached Run")
    
    st.subheader("Raw Evaluation Data")
    # Reorder columns to surface the most critical data first using actual schema keys
    cols = [
        "article", 
        "citation_url", 
        "claim", 
        "sentinel_status", 
        "baseline_live_supports", 
        "sentinel_live_supports", 
        "timestamp_reliable"
    ]
    display_cols = [c for c in cols if c in df.columns] + [c for c in df.columns if c not in cols]
    st.dataframe(df[display_cols], use_container_width=True)

st.subheader("Visual Evidence (Diffs)")
st.markdown("Below are the line-by-line visual comparisons for identified citation drift:")

html_files = sorted(glob.glob("drift_visualization_*.html"))
if not html_files:
    st.info("No HTML diff visualizations found.")
else:
    for file in html_files:
        st.markdown(f"**{os.path.basename(file)}**")
        try:
            with open(file, "r", encoding="utf-8") as f:
                html_data = f.read()
            components.html(html_data, height=400, scrolling=True)
        except Exception as e:
            st.error(f"Error loading {file}: {e}")