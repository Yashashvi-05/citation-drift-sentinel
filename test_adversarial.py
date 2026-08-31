import os
from src.analyzer import analyze_drift

def run_adversarial_suite():
    print("=== RUNNING ADVERSARIAL EVALUATION SUITE ===\n")
    results = []

    # Case 1: Subtle Date Shift (Temporal Precision)
    print("Test Case 1: Subtle Date Mutation (Dec 15 vs Dec 16)")
    claim_1 = "Yahoo Groups to shut down on December 15, 2020"
    live_1 = "Yahoo Groups to shut down on December 16, 2020 following platform updates."
    archived_1 = "Yahoo Groups to shut down on December 15, 2020 as previously announced."
    
    res_1 = analyze_drift(claim=claim_1, archived_text=archived_1, live_text=live_1)
    
    drift_1 = res_1.get("drift_detected", False)
    quote_ver_1 = res_1.get("quote_verified", False)
    print(f"  -> Drift Detected: {drift_1} (Expected: True)")
    print(f"  -> Quote Verified: {quote_ver_1}")
    print(f"  -> Reasoning: {res_1.get('reasoning')}\n")
    results.append(drift_1)

    # Case 2: Negation Inversion (Polarity Hijack)
    print("Test Case 2: Negation Injection ('will NOT be shut down')")
    claim_2 = "Yahoo Groups will be shut down"
    live_2 = "Yahoo Groups will NOT be shut down and operations continue normally."
    archived_2 = "Yahoo Groups will be shut down permanently in December."

    res_2 = analyze_drift(claim=claim_2, archived_text=archived_2, live_text=live_2)
    
    drift_2 = res_2.get("drift_detected", False)
    quote_ver_2 = res_2.get("quote_verified", False)
    print(f"  -> Drift Detected: {drift_2} (Expected: True)")
    print(f"  -> Quote Verified: {quote_ver_2}")
    print(f"  -> Reasoning: {res_2.get('reasoning')}\n")
    results.append(drift_2)

    # Summary
    passed = sum(results)
    print(f"=== SUMMARY: {passed}/{len(results)} Adversarial Cases Passed ===")
    if passed == len(results):
        print("✅ Adversarial Evaluation Passed: Agent is robust against subtle mutations.")
    else:
        print("⚠️ Adversarial Warning: One or more subtle shifts were missed.")

if __name__ == "__main__":
    run_adversarial_suite()
