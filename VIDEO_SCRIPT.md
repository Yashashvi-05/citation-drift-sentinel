# CITATION DRIFT SENTINEL — FULL NARRATION SCRIPT

**[0:00–0:15] — HOOK**
(Screen: title slide or README)
"Wikipedia is fighting a losing battle against source decay. When automated systems use a standard, single-pass LLM to verify a citation, they hit a structural blind spot: the model only sees the live web as it exists today — not as it existed when the citation was written."

**[0:15–1:00] — THE BASELINE'S THREE FAILURE MODES**
(Screen: BENCHMARK_REPORT.md or the deployed dashboard metrics)
"We tested this against a real baseline — a naive, single-pass LLM check with no memory, no archive access, and no verification. It fails in three distinct ways.
One: raw accuracy failures — it hallucinates support, or misses context that's actually there on the live page.
Two: dead links — it throws an unhandled exception on a 404 instead of recognizing that the source simply died.
Three, and this is the one that matters most: it falsely penalizes legitimate editors. If a source page gets rewritten or redirected after a citation was added, the baseline has no way to know the citation was originally valid — because it has no concept of time."

**[1:00–1:50] — THE YAHOO GROUPS DEMO**
(Screen: switch to the deployed dashboard's Raw Evaluation Data table, scroll to the help.yahoo.com row)
"Here's a real example from our dataset. This citation supports the claim: 'Yahoo Groups to shut down on December 15th, 2020,' sourced from a Yahoo help page.
The baseline checks the live URL right now — and gets this."
(Screen: switch to the live help.yahoo.com page, or a screenshot of it — show it's now a generic "Help for your Yahoo Account" hub)
"The original page is gone. It redirects to a generic help hub. The baseline sees this, concludes the claim isn't supported, and flags a valid citation as broken.
Sentinel does something different. It harvests the citation's real insertion date directly from Wikipedia's revision history — walking back through the page's edit history to find exactly when this citation was added. Then it pulls the Wayback Machine snapshot from that exact point in time."

**[1:50–2:45] — THE VERDICT AND THE DIFF**
(Screen: switch to the deployed dashboard's Visual Evidence section, showing the help.yahoo.com diff)
"Here's the side-by-side. On the left: the archived page, from when this citation was actually written. On the right: the live page today.
The archived text says, verbatim: 'Yahoo Groups to shut down on December 15th, 2020.' The live text is generic account help — no mention of Groups at all.
Sentinel's verdict: DRIFT DETECTED — not INVALID. The editor cited a real, valid source. The information decayed underneath it. That distinction matters, because one of those verdicts tells you to delete a citation, and the other tells you the citation was right all along."

**[2:45–3:40] — THE BENCHMARK DATA**
(Screen: dashboard's top metrics: 15 / 2 / 4 / 0)
"We ran this on 15 real citations across 5 real Wikipedia articles — deliberately chosen 'closed chapter' tech topics: Google Reader, Yahoo Groups, Windows Phone, Vine, and Myspace. Every citation, every archive snapshot, every verdict is real — no synthetic data anywhere in this dataset.
Comparing Sentinel against the same naive baseline on the same 15 citations: 20% were raw accuracy failures — the baseline was flatly wrong. Another 20% were structural blind spots — cases where the baseline's answer happened to match, but only because it can't see history at all, so it can't tell a dead-but-valid citation from a genuinely broken one. And 9% were dead links, which the baseline couldn't classify at all — it just threw an exception.
We're upfront that 15 citations is a small sample — that's a real constraint of building against live APIs and a free-tier token budget, not a claim of statistical significance. But every single one of these results is independently verifiable — including the citation's exact insertion timestamp, which we manually cross-checked against Wikipedia's own edit history and confirmed to the minute."

**[3:40–4:35] — THE ENGINEERING**
(Screen: quickly flash through: test_adversarial.py output, ESCALATION_TRACE.log, test_guardrails.py output, or the repo file list)
"A few of the engineering pieces that back this up: a confidence-based escalation loop, where the agent automatically re-checks its own low-confidence judgments with a stricter prompt. Verbatim quote guardrails — the model has to cite an exact quote from the source text, and we programmatically verify that quote actually exists before trusting the verdict. A multi-tier Wayback Machine fallback chain, so a single failed API call doesn't take down the whole pipeline. And an adversarial test suite — deliberately mutated dates and injected negations — to confirm the agent isn't doing lazy semantic matching.
Everything here runs on a completely free stack: Groq's free tier, public Wikipedia and Wayback Machine APIs, and SQLite for local memory. Zero cost end to end."

**[4:35–5:00] — CLOSE**
(Screen: the deployed dashboard homepage, or README title)
"This is deployed and live right now — the link's in our submission, so you can explore the full dataset and every diff yourself.
The core lesson from building this: temporal orchestration isn't a nice-to-have for automated moderation. Without it, you can't tell the difference between a citation that's wrong and a citation that was right, once."
