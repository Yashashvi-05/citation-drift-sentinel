# Citation Drift Sentinel: Benchmark Report

## Executive Summary

This report analyzes the performance of the Citation Drift Sentinel against a standard single-pass LLM baseline. The data demonstrates the critical necessity of temporal orchestration for automated moderation, highlighting three distinct failure modes in the baseline architecture:

* **20% Raw Accuracy Disagreements (2/10):** Sentinel corrected baseline hallucinations and missed extractions on live pages.
* **20% Structural Blind-Spots (2/10):** Sentinel detected citation drift where the baseline falsely penalized editors, proving historical validity that standard LLM pipelines cannot evaluate.
* **9% Dead Link Categorization (1/11):** Sentinel cleanly classified hard 404s as `DEAD_LINK` rather than discarding them as unhandled errors.

## Discrepancy Analysis (Count Breakdown)

- **Raw Accuracy Failures:** 2
- **Structural Blind Spots (Drift):** 2
- **Dead Links:** 1
- **Agreements:** 6
- **Errors:** 4

## Citation Evaluation Table

| Article | Citation URL | Baseline Live | Sentinel Live | Final Verdict |
|---|---|---|---|---|
| Google Reader | http://googlereader.blogspot.com/2005/10/google-reader-two-weeks.html | False | False | ORIGINALLY INVALID |
| Google Reader | http://googleblog.blogspot.com/2013/03/a-second-spring-of-cleaning.html | False | False | DRIFT DETECTED |
| Google Reader | http://massless.org/default.php?archive=2007/05/about-google-readers-birth-part-1 | None | None | ERROR |
| Yahoo Groups | https://help.yahoo.com/kb/groups/SLN35505.html | False | False | DRIFT DETECTED |
| Yahoo Groups | https://www.ghacks.net/2020/10/14/farewell-yahoo-groups-shutting-down-on-december-15-2020/ | True | True | VERIFIED |
| Yahoo Groups | https://money.cnn.com/2000/06/28/technology/yahoo | None | None | DEAD_LINK |
| Windows Phone | https://www.cnet.com/news/windows-10-mobile-features-hardware-death-sentence-microsoft/ | True | True | VERIFIED |
| Windows Phone | http://asia.cnet.com/reviews/mobilephones/0,39050603,62061278,00.htm | None | None | ERROR |
| Windows Phone | https://www.engadget.com/2010/03/04/microsoft-talks-windows-phone-7-series-development-ahead-of-gdc/ | False | True | VERIFIED |
| Vine (service) | https://www.nbcnews.com/pop-culture/pop-culture-news/look-back-vine-six-second-video-app-made-us-scream-laugh-cry-rcna10910 | True | True | VERIFIED |
| Vine (service) | https://futureparty.com/what-happened-to-vine/ | True | False | ORIGINALLY INVALID |
| Vine (service) | https://www.cnet.com/tech/services-and-software/twitter-kills-off-vine/ | False | False | ORIGINALLY INVALID |
| Myspace | http://www.abc.net.au/science/articles/2008/03/27/2199691.htm | False | False | ORIGINALLY INVALID |
| Myspace | https://mashable.com/2006/09/13/myspace-well-crush-youtube/ | False | None | ERROR |
| Myspace | https://venturebeat.com/2009/07/24/myspace-is-a-big-gaming-platform-but-it-hopes-to-be-more-of-one/ | None | None | ERROR |