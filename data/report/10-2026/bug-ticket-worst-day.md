# Bug ticket: 1-star spike on 04-10-2026, check checkout payment failures (cause not confirmed)

## Summary

04-10-2026 had the most 1-star Play Store reviews of October 2026: 169 of 746 reviews (22.7%), against 18.7% for the month. No app version explains it. The complaint with the biggest rise that day is payment failure at checkout, but it rests on only 4 clear reports. This ticket asks for the payment gateway and checkout logs for 04-10-2026 to be checked. It does not claim a root cause.

## Environment

- Platform: Android, Google Play Store reviews from India, in English only
- Date: 04-10-2026
- App version: not version-specific. The 1-star reviews that day are mostly on 19.9.1 (57) and 19.9.3 (53), but those were the builds most users had in early October. The 19.9.1 1-star rate was 21.8% on 04-10-2026, against 21.3% to 22.3% on 05-10-2026 to 07-10-2026. The 4 payment reports come from 3 builds (19.9.0, 19.9.1, 19.9.3).
- IST hours: peaks at 14:00 to 14:59 (17 one-star reviews) and 21:00 to 21:59 (16), then 23:00 (12) and 13:00, 18:00, 19:00 and 22:00 (11 each). Lunch, 12:00 to 14:59, is the only window above its usual share: 21.9% of the day's 1-star reviews, against 15.3% on a normal October day.

## Impact

- 04-10-2026: 169 one-star reviews out of 746 (22.7%). October as a whole: 3,656 out of 19,593 (18.7%), an average of 117.9 a day.
- The next days are close: 20-10-2026 had 147, 02-10-2026 had 143, 10-10-2026 had 142 and 24-10-2026 had 140. By share, 24-10-2026 (22.6%) nearly ties 04-10-2026.
- Complaint themes in the 123 written 1-star reviews that day, against the other 2,614 written 1-star reviews in October:
  - Payment failures: 7.3% against 5.0% (1.46x). The keyword match finds 9 reviews, and 4 of them describe a real payment failure.
  - Food quality: 1.21x
  - Late delivery: 20.3% against 17.1% (1.19x, 25 reviews). It is the largest theme in raw numbers but only slightly above its October level.
  - Every other theme: 0.55x to 0.96x
- No review that day mentions a crash, login or OTP problem, so there is no sign of an app outage.

## Steps to reproduce

As reported by users, not yet reproduced in QA. The reviews do not say which payment method was used.

1. Open the Zomato Android app (reports come from 19.9.0, 19.9.1 and 19.9.3) and add items to the cart.
2. Go to checkout and pay.
3. Reported: the payment fails several times in a row.
4. Reported: or the payment goes through but no order is placed.
5. Contact support about the money taken. Reported: support says the payment failed and gives no refund.

## Expected vs actual

- Expected: the payment either completes and places the order, or fails without taking money. Any money taken for an order that was not placed is refunded.
- Actual (as reported): repeated payment failures, money taken with no order placed, and support calling it a failed payment instead of refunding.

## User quotes

All three are 1-star reviews from 04-10-2026, checked against the raw reviews file and passed through `mask()` from `scripts/build_report_data.py` (they held no personal details).

1. reviewId `927e822a-0778-468a-b858-3b69ba5d50cf`, 13:57 IST, app 19.9.3: "payment is getting failed mutltple times"
2. reviewId `76d12bd1-b631-45cf-9dcc-732704af4959`, 19:08 IST, app 19.9.0: "payment in first order is done but order not placed"
3. reviewId `88f04579-05f1-44a0-86b7-8f953d37f801`, 22:15 IST, app 19.9.1: "3rd clss.. rather thn refund they say my payment if failed"

These are short reviews. They are the only same-day reviews that clearly describe a payment failure.

## Suggested owner

Payments, to check the gateway, checkout and refund logs for 04-10-2026. This is a check, not an assignment of blame. Delivery Operations should look at the lunch window as well, for the slight rise in late delivery. For example, `8e70ce9a-9a11-4048-8063-2c4bdb3f3eed` (22:03 IST, 19.9.3): "it shows time around 15 to 30 minutes. But always get late by minimum 15 minutes to 30 minutes."

## Confidence and open questions

Confidence: medium that 04-10-2026 was a worse day than usual, with extra 1-star reviews at lunch. Low that payment failures caused it.

- Do gateway or checkout logs show a higher failure rate on 04-10-2026, especially from 12:00 to 14:59 IST?
- Did refund requests or support tickets for "money taken, no order" rise that day?
- Was there a restaurant or rider supply problem at lunch that day?
- 24-10-2026 has almost the same 1-star share (22.6%). Does the same pattern show up there?
- Only English reviews are included, so Hindi reviews from that day are not counted.
