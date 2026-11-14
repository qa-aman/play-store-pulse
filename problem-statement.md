# Problem Statement: Monthly Play Store Review Report

**Owner:** Aman Parmar, Product Manager, Zomato
**Date:** 14-11-2026
**Status:** Draft

## The problem

Every month I send the leadership team a summary of Zomato's Google Play Store reviews.

Today it is fully manual:

1. Export the month's reviews from the Play Store.
2. Put them in Excel, then clean, sort and read them by hand.
3. Pull out the ratings, themes and notable reviews.
4. Write the report myself.
5. Share it with the leadership team.

The same steps repeat every month. A month of reviews for an app Zomato's size is far more than one person can read properly, so the report depends on what I manage to sample. It takes hours I could spend on product work, and the report only goes out when I'm free to put it together.

## Who it is for

| User | What they need |
|---|---|
| Leadership team (reader) | A short report in the same format every month: how ratings moved, what users complain about or praise, what changed since last month, and what needs attention |
| Me, the PM (owner) | The report built without the export, Excel and writing work, so I only check it, add context and approve it |

## Goal

Automate the monthly flow from getting the reviews to sharing the report, so leadership gets a consistent review summary on a fixed day each month and my part is a short review.

## What the report should cover

- **Rating summary:** review count, average rating, star split, and change from last month
- **Top themes** (for example delivery delays, refunds, app bugs, customer support, pricing), each with its share of reviews and 2-3 example quotes
- **What changed:** new or fast-growing issues compared with last month, and issues that went down
- **Trend within the month:** week-by-week movement, so a spike after a release or an outage shows up
- **App version view:** whether a specific release drove a rise in complaints
- **Notable reviews** leadership should read
- **Recommended actions** with an owner team where it's clear

## In scope

- Getting the full month of Zomato Android reviews without manual export
- Grouping reviews into themes and scoring sentiment with AI, across every review, not a sample
- Comparing each month with the month before
- Building the report in a fixed format
- Sending it to leadership on a schedule, after my approval

## Out of scope (for now)

- iOS App Store reviews
- Replying to reviews
- Competitor apps
- Real-time alerts during the month

## Success criteria

- The report is ready on the agreed day each month with no manual export, Excel or writing step
- My time per report goes from today's manual effort (to fill in: ___ hours) to a 15-20 minute review
- Themes match what I would find reading the reviews myself, checked against 2 past months before it replaces the manual report
- The format and theme list stay the same each month, so leadership can compare month on month
- Nothing goes out to leadership without my approval

## Data source and constraints

- **Play Console monthly review export:** Play Console writes a monthly reviews CSV for each app to a Google Cloud Storage bucket (file name pattern `reviews_[package_name]_YYYYMM.csv`). This matches a monthly report and covers the full month. Needs access to Zomato's Play Console bucket. Source: https://support.google.com/googleplay/android-developer/answer/6135870
- **Google Play Developer API (Reply to Reviews API):** only returns reviews created or changed in the last 7 days, so on its own it cannot cover a month. Usable only if we pull it every week and store the results. Needs a service account with Play Console access. Source: https://developers.google.com/android-publisher/reply-to-reviews
- **Volume:** a month of reviews for Zomato is large, so theming has to run on batches, not a manual read.
- **Privacy:** review text can contain names, phone numbers or order details, so quotes in the report need masking.
- **Consistent themes:** if the theme list changes every month, the month-on-month comparison breaks. Theme changes should be proposed to me, not applied silently.

## Open questions

1. Can I get access to Zomato's Play Console review export bucket or a service account, or does another team have to set it up?
2. What format does leadership want: email, Slack post, Google Doc, slides or a dashboard link?
3. Does leadership already track a fixed list of themes, or should the first list come from the data?
4. Which day of the month should it go out, and how many days after month end is acceptable?
5. Should the report break down by app version, city or language?
6. Who else reviews it before it goes out, besides me?
