---
name: definitions
description: How each Play Store Pulse number is defined and which denominator it uses
type: reference
---

Taken from `scripts/build_report_data.py` and the page calcs in `.claude/skills/play-store-pulse/assets/dashboard.html`. Re-read the code if these look out of date.

- **Text review:** stripped `content` longer than `MIN_TEXT` (20) characters. Everything else is star-only.
- **Shares** are percentages rounded to 1 decimal. Average ratings round to 2 decimals.
- **Complaint share:** reviews matching the theme regex (lower-cased text) / negative text reviews (1-2 stars with text). One review can match several themes, so shares sum to more than 100%.
- **Praise share:** matches / positive text reviews (4-5 stars with text).
- **Reply rate:** reviews with `replyContent` / all reviews. **1-star reply rate:** replied 1-star / all 1-star. **1-star unreplied:** 1-star without a reply.
- **Top template share:** the most common reply opening / ALL replies, not 1-star replies.
- **1-star top template share** (`one_star_top_template_share`, added 15-11-2026): the most common opening among replies to 1-star reviews / those replies. Reports built before 15-11-2026 lack it.
- **Median reply minutes:** only replies dated at or after the review count. An edited review carries its edit time, so its reply can predate it. The value is empty when no reply time is valid (all of 09-2026). Reports built before 15-11-2026 included the negative lags.
- **Versions:** top 8 by review count, so they do not sum to the total. An empty `appVersion` is "Not given".
- **windows** (page calc): average rating per part of the day, weighted by reviews in each hour. early 0-8, morning 8-12, afternoon 12-20, night 20-24.
- **worst_days** (page calc): the top 3 daily rows by `one_star_share`, in descending order. Ties keep the daily file's date order.
- **Loudest:** the top 5 text reviews by thumbs-up. The text is masked, then cut at a word boundary near 320 characters with "..." (before 15-11-2026 it was cut mid-word).
- **Quotes** (since 15-11-2026): complaint quotes skip praise-toned text, praise quotes skip complaint or request cues (`NOT_PRAISE`), and the order is fewest other themes, then most mentions of the theme, then thumbs-up. A praise quote can be empty when every match fails the tone check.
- **Times** in the CSV are IST, as the scraper gives them.
