# Writing narrative.json

The dashboard's numbers come from the data files. The few words that depend on judgment come from `data/report/<label>/narrative.json`, which you write each run after reading the data. Readers are Zomato leadership: short, specific, no hype.

## Shape

```json
{
  "headline": "One sentence after the ratings sentence: the single biggest finding.",
  "comparison_note": "One line under the scorecard about comparison with the previous period.",
  "release_note": "One to three sentences on the release check table.",
  "asks_heading": "Three asks for <next month or 'the next period'>",
  "actions": [
    {"owner": "Team", "title": "Short imperative", "text": "Why, with numbers, and what to do.", "measure": "what to track next period"},
    {"...": "exactly 3 actions"}
  ]
}
```

## Numbers in the words

Never type a number from the data by hand. Write a token and the render script turns it into a live, checkable number:

| Token | Meaning |
|---|---|
| `[[kpis.one_star_unreplied#0\|int]]` | row 0 of a file |
| `[[complaints.share@code=support\|pct]]` | the row where `code` is `support` |
| `[[windows.avg_rating@window=night\|dec2]]` | page calc: `window` is `early`, `morning`, `afternoon` or `night` |
| `[[worst_days.one_star_share#0\|pct]]` | page calc: the worst day's 1-star share (fields `rank, one_star_share, reviews`; dates can't be tokens, type them) |

Formats: `int` (19,593), `pct` (26.9%), `dec2` (3.98), `min` (6 min). Complaint codes: `support, price, late, refund, missing, cancel, quality, rider, offers, payment`. Praise codes: `fast, offers, food, easy, variety`. The script fails on any token that does not match the data.

Fixed words like "8 pm to midnight" are fine as text.

## What to write

- **headline:** the finding that changes what leadership does. Usually the top complaint theme and how it compares with the next one. Name it plainly ("Their top complaint is customer support, not the app.").
- **comparison_note:** if this is the first period of its length, say there is no comparison yet. If an earlier period's `data/report/<label>/kpis.json` exists, state the change in rating and 1-star share in words (those numbers are typed, so say they come from the earlier report).
- **release_note:** read `versions.json`. Name any version whose 1-star share is 5+ points above the period's, or say none stands out. "Not given" versions are usually reviews from old or uninstalled apps.
- **actions:** one per owner, drawn from the top complaint themes, the hours pattern and reply coverage. Each `text` holds at least one token. Owners are suggestions; use the `owner` names in `complaints.json`.

## Rules

- No em dashes, no emojis, dates as DD-MM-YYYY. The script fails on em dashes and ISO dates.
- Say what the data shows, not more. Keyword themes are estimates, so no claims finer than one decimal.
- Never quote a review in the narrative; quotes live in `complaints.json` and `loudest.json`, already masked.
