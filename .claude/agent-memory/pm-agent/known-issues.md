---
name: known-issues
description: Problems found in earlier Play Store Pulse runs and audits, and how to handle each
type: feedback
---

- **Wording, not numbers, is the usual audit finding.** The audits of 15-11-2026 found no wrong numbers in 10-2026 or the November periods. They did find misleading wording: a reply figure for all replies placed next to a 1-star ask, "busiest" for a window that was busiest only per hour, and off-topic quotes.
  **Why:** the narrative is written by hand each run, while the numbers come from tokens.
  **How to apply:** before step 4, re-read the narrative against the rules in `.claude/skills/play-store-pulse/references/narrative.md`. Use `one_star_top_template_share` for 1-star points, and say "per hour" when comparing parts of the day.
- **Raw data must stay on this machine.** 09-2026 was built in a cloud run, and its raw CSV never came back. It could not be audited exactly, because a fresh fetch had 66 fewer reviews. Edited and deleted reviews make every later fetch differ.
  **How to apply:** run the audit in the same session as the fetch. Never refetch between building and auditing.
- **Reply times can be invalid.** An edited review carries its edit time, so its reply can appear to predate it. The builder now drops those lags. If `median_reply_minutes` is empty, the hand-over says reply times are not available, never that replies are fast.
- **Quotes are keyword matches.** Even with the tone filters, a quote can be off-topic, or in Hindi or Hinglish. For the email, prefer an on-topic English complaint quote. A `loudest:<rank>` review about the top theme is a good fallback.
- **Praise quotes and the "offers" complaint quote are the weak spots.** The audit of a 3-month range found no wrong numbers, but 3 of 5 praise quotes (variety, offers, easy) and the complaint `offers` quote_1 were off-topic or unfit (a complaint inside a 4-star review, profanity, a competitor rant). Step 4 of the skill only asks to check complaint quotes, so praise quotes slip through.
  **How to apply:** in step 4 also read `praise.json` quotes, and fix them before the audit so the PM is not asked.
- **Older periods drift in raw data.** A later audit may recompute a past month (September) slightly differently because the old raw CSV lost reviews. When the comparison note or email quotes an earlier period, treat the earlier report JSON as the source and expect the auditor to flag it as drift, not an error.
- **Long ranges and the page check.** A 3-month range fetches in the background in a few minutes. In step 8 no tab is open during an agent run, so `data/users/me` is empty: say the page has not run yet and do not loop.
- **The dashboard is private.** The email links to it, so the PM must share it before sending.
