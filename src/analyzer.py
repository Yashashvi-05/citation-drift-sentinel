import os
import json
import time
import dotenv
from groq import Groq

dotenv.load_dotenv()

def analyze_drift(claim: str, archived_text: str, live_text: str, escalated: bool = False) -> dict:
    try:
        client = Groq(timeout=15.0)
        
        escalation_instruction = ""
        if escalated:
            escalation_instruction = "\n\nCRITICAL SYSTEM OVERRIDE: Your previous evaluation had LOW CONFIDENCE. You must meticulously double-check the texts and your logical steps to ensure absolute correctness."

        system_prompt = f"""You are an AI tasked with analyzing citation drift.
You will be provided with a 'Claim', an 'Archived Text' (what the citation originally said), and a 'Live Text' (what the citation currently says).
Your task is to evaluate:
1. Does the Archived Text support the Claim?
2. Does the Live Text support the Claim?

You must also assign a confidence level ("low", "medium", or "high") to your evaluation.

You MUST extract exact, verbatim substrings from the text to populate these. Do not paraphrase. If no quote supports the verdict, output null.

You must output your analysis in JSON format exactly matching this schema:
{{
  "archived_supports_claim": bool,
  "live_supports_claim": bool,
  "drift_detected": bool,
  "live_quote": "string" | null,
  "archived_quote": "string" | null,
  "confidence": "low" | "medium" | "high",
  "reasoning": "string"
}}

'drift_detected' should be true ONLY if 'archived_supports_claim' is true AND 'live_supports_claim' is false.{escalation_instruction}"""

        user_prompt = f"""Claim: {claim}

Archived Text: {archived_text}
---
Live Text: {live_text}"""

        for attempt in range(3):
            try:
                response = client.chat.completions.create(
                    model="qwen/qwen3.8-27b",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.0
                )
                
                content = response.choices[0].message.content
                result = json.loads(content)
                
                # Programmatic Quote Verification
                result["quote_verified"] = True
                live_quote = result.get("live_quote")
                if live_quote and (not isinstance(live_quote, str) or live_quote not in live_text):
                    result["quote_verified"] = False
                archived_quote = result.get("archived_quote")
                if archived_quote and (not isinstance(archived_quote, str) or archived_quote not in archived_text):
                    result["quote_verified"] = False
                
                # Enforce the logic programmatically just in case
                if not live_text:
                    result["dead_link"] = True
                    result["live_supports_claim"] = False
                    
                if result.get("archived_supports_claim") and not result.get("live_supports_claim"):
                    result["drift_detected"] = True
                    
                if "confidence" not in result:
                    result["confidence"] = "medium"
                    
                return result
                
            except Exception as e:
                print(f"WARNING: Groq API attempt {attempt + 1} failed: {e}")
                time.sleep(2 ** attempt)
                continue
                
        # Exhausted 3 attempts
        return {
            "archived_supports_claim": False,
            "live_supports_claim": False,
            "drift_detected": False,
            "confidence": "error",
            "error": True,
            "reasoning": "API failure/exhaustion after 3 attempts."
        }
        
    except Exception as e:
        return {
            "archived_supports_claim": False,
            "live_supports_claim": False,
            "drift_detected": False,
            "confidence": "error",
            "error": True,
            "reasoning": f"Setup error occurred during analysis: {str(e)}"
        }

if __name__ == "__main__":
    fake_claim = "The project is maintained by a 5-member steering council."
    fake_archived_text = "Following the reorganization in January 2019, the project is maintained by a 5-member steering council elected by the core developers."
    fake_live_text = "The project is now maintained by a single BDFL who oversees all major decisions."
    
    print("Testing Agent 3: Drift Analyzer")
    print(f"Claim: {fake_claim}")
    print("-" * 40)
    
    result = analyze_drift(fake_claim, fake_archived_text, fake_live_text)
    print(json.dumps(result, indent=2))
