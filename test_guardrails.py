import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
from analyzer import analyze_drift

def main():
    claim = "Yahoo Groups to shut down on December 15, 2020"
    live_text = "Help for your Yahoo Account. You have been redirected to this page because the page you requested was not found."
    archived_text = "Yahoo Groups to shut down on December 15, 2020. We are announcing that Yahoo Groups will be shut down and all content will be permanently removed."
    
    print("Testing Verbatim Quote Guardrails (Programmatic Verification)...\n")
    
    result = analyze_drift(claim, archived_text, live_text)
    
    print(json.dumps(result, indent=2))
    
    if result.get("quote_verified"):
        print("\n✅ SUCCESS: Quotes are verified verbatim substrings!")
    else:
        print("\n❌ FAILURE: Hallucination detected! A quote was not found as a strict substring.")

if __name__ == "__main__":
    main()
