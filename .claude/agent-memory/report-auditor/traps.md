---
name: traps
description: Report errors and false alarms seen in earlier audits, to check first
type: feedback
---

- **The reply template share is placed next to a 1-star claim.** `top_template_share` is measured over all replies. Its top line is usually a thank-you sent to 4-5 star reviews. Wording like "most replies reuse one line" beside a 1-star ask is misleading. Report the 1-star-only figure as the better number. (Found in the 10-2026 audit, 15-11-2026: 62.8% for all replies vs 54.6% for 1-star replies.)
  **Why:** a correct number in the wrong context misleads leadership as much as a wrong one.
  **How to apply:** for every number, check that the population it was computed on matches the sentence around it.
- **"Busiest" window claims:** the night window (4 hours) has fewer total reviews than afternoon (8 hours) but more per hour. Check the wording ("most reviews" vs "busiest per hour"). The narrative ask says "brings the most reviews", which is wrong on totals.
- **Typed comparison numbers** in `comparison_note` come from an earlier period's report. Recompute them from that period's raw CSV when it exists.
- **Not mismatches:**
  - Version rows not summing to the total (only the top 8 are listed).
  - Theme shares summing above 100%.
  - `—` characters in the page HTML (loading placeholders).
  - A bare "2" in "2-day read" (the period length).
- **Short periods (2-day):** the praise `easy`/`variety` themes can have 0-1 hits and empty quotes; not an error. Loudest ranks 4-5 can tie on thumbs-up (stable sort keeps raw file order); the cut at 320 chars can end mid-word on rank 1-3. Cosmetic only.
- **Quote fit seen again:** a praise quote under "offers" was a 4-5 star review complaining that discounts are not given; a "missing items" quote was really a customer-service complaint. The `NEGATIVE` filter on praise quotes misses these. Always read each quote.
- **Contradictory-rating quotes:** complaint quotes come from 1-2 star reviews, so a glowing text under a 1-star rating can be picked (seen under `quality`). Flag it. Also `offers`/`payment` quotes often drift (delivery-person demand, GST invoice).
- **Short-range reports** (partial months): the page calcs `windows`/`worst_days` are not in the JSON; recompute from raw and say rendered page was not viewed. Check "top for a second period" claims against the other period's complaints.json.
- **`repliedAt` can carry the wrong year (seen 09-2026, 15-11-2026):** raw `repliedAt` was dated 2022-2023 for September reviews, so every reply lag is negative and `kpis.median_reply_minutes` is a huge negative number. The "Median time to reply" tile and the h2 "Replies are fast but canned" then rest on garbage. Check the sign of the median first. Reply rate was also under 1%, so reply data looks truncated.
- **Page template prose is hand-typed:** the `pp-text` under "When it goes wrong" calls 8 pm to midnight "the busiest stretch". It has the fewest reviews, in total and per hour. Read the `dashboard.html` prose, not only the tokens.
- **Snapshot drift (raw re-fetched after the report was built):** a re-fetch loses reviews (09-2026: 66, almost all 4-5 star), so counts shift by about 0.3%, text positives by more, and a quote may vanish from raw. Not a mismatch. Check internal consistency (stars/daily/hours sums, shares vs counts, windows, worst_days) against the report's own JSON first.
- **Multi-month labels (08-2026_to_10-2026):** the narrative/email pull September and October comparison numbers as `[[09-2026:...]]` tokens. The 09-2026 raw CSV has since shed reviews (19,743 vs 19,809 in its JSON), so raw gives 3.91 / 20.4% against the report's 3.92 / 20.3%. Treat as snapshot drift, say so, and check the number against the other period's JSON.
- **Guard hook quirks:** `_` anywhere as a name (even `for _,c in`) is blocked; `sed` is blocked (use `tail -n +N | head`). Matching quotes to raw: search `core in normalised content` where core is the quote minus a trailing "...".
- **Praise quotes drift:** the `variety` praise quote can be a 4-star review that complains (pushy tips screen), and `offers` one can be a profane Hinglish comparison with a competitor. `NOT_PRAISE` misses both.
- **Quotes:** themes are keyword matches, so a quote can match its regex and still be off-topic (a weight complaint under support, a "be faster" request under fast-delivery praise). List off-topic quotes under "Misleading but correct".
