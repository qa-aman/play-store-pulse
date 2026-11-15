# Writing email.json

The email is the 30-second version of the dashboard for Zomato leadership. Its shape is fixed by the render script; you write only the parts below, in `data/report/<label>/email.json`. The three asks come from the dashboard's `narrative.json`, so they always match.

## The frameworks it follows

| Part | Framework | Rule |
|---|---|---|
| Subject | Smart Brevity (Axios) + BLUF | The finding and the ask, under 70 characters. A reader who sees only the subject knows what happened. |
| Bottom line | Pyramid Principle (Minto) + BLUF | One sentence: the answer first. What changed and what needs action. |
| Why it matters | Smart Brevity | One or two sentences on the consequence for the business, not a restatement of the numbers. |
| The numbers | Pyramid Principle | 2 to 4 bullets that support the bottom line, each a number with its comparison. No number that doesn't support it. |
| Three asks | Writing for Busy Readers: "make responding easy" | From `narrative.json`, each with an owner and one reply-by date. |
| In their words | Made to Stick: concrete | One real, masked user quote that makes the top issue felt. |
| Go deeper | Smart Brevity | The dashboard link carries the detail; the email does not repeat it. |
| Whole email | Writing for Busy Readers + On Writing Well (Zinsser) | Under 200 words, short sentences, no filler, plain words. |

## Shape

```json
{
  "subject": "Play Store Pulse 01-11 to 07-11: support still top complaint, check 20.0.0",
  "bottom_line": "Ratings held at [[kpis.avg_rating#0|dec2]], but customer support is still the top complaint.",
  "why_it_matters": "The issues users write about are operational, so the fixes sit with CX, Pricing and the App team.",
  "numbers": [
    "[[kpis.reviews#0|int]] reviews, average [[kpis.avg_rating#0|dec2]] (October: [[10-2026:kpis.avg_rating#0|dec2]])",
    "Support in [[complaints.share@code=support|pct]] of written complaints, prices and fees in [[complaints.share@code=price|pct]]"
  ],
  "quote": "complaints:offers"
}
```

## Tokens

Same syntax as the dashboard narrative, filled with the formatted value:

| Token | Meaning |
|---|---|
| `[[kpis.reviews#0\|int]]` | row 0 of this period's file |
| `[[complaints.share@code=support\|pct]]` | the row where `code` is `support` |
| `[[versions.one_star_share@version=20.0.0\|pct]]` | a version's row |
| `[[windows.avg_rating@window=night\|dec2]]` | part of the day: `early`, `morning`, `afternoon`, `night` |
| `[[10-2026:kpis.avg_rating#0\|dec2]]` | another period's value, by its label, for comparisons |

Formats: `int`, `pct`, `dec2`, `min`, `text`. Files: `kpis, stars, complaints, praise, hours, daily, versions, loudest`. The script fails on a token that doesn't match the data, and lists any number you typed by hand so you can check it.

`quote` is `complaints:<code>` (that theme's quote) or `loudest:<rank>` (1 to 5). Pick the one that best supports the bottom line.

## Rules

- Lead with what changed or what needs a decision, not with "This week we received...".
- Compare every headline number with something: the previous period, the period average, a target.
- One idea per bullet. No adjectives in place of numbers ("sharp drop" becomes "down from 22.1% to 18.6%").
- No em dashes, no emojis, dates DD-MM-YYYY, no exclamation marks.
- Match each number to the group it was measured on. `top_template_share` covers all replies, most of them thank-yous to 4 and 5-star reviews; next to a 1-star point use `one_star_top_template_share`.
- Compare parts of the day per hour, not in total: night and morning are 4 hours, early and afternoon are 8. Say "busiest" or "most" only if it holds per hour, and say "per hour".
- Check every superlative (most, busiest, worst, top, again) against this period's data before writing it. A claim like "again" or "second period" needs the earlier period's file.
- `median_reply_minutes` is empty when no reply time is valid (an edited review can carry a date after its reply). Then say reply times are not available, never that replies are fast.
- Never name a reviewer or paste an unmasked review.
