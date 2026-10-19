---
doc_id: dashboard_account_performance
doc_type: dashboard
title: Account Performance
languages: [en]
---

# Dashboard: Account Performance

## Purpose
Follow the commercial performance of corporate accounts: how much revenue each account
generates, how it evolves over time, and which accounts cancel a lot or receive large discounts.

## Who uses it
Account managers (their own accounts) and regional directors (all accounts of their region).

## Questions it answers
- How much revenue did an account, a size tier, an industry or an account manager generate?
- Which are the top accounts of a region?
- Is revenue growing or shrinking compared with last year?
- Which accounts have a high cancellation rate?
- What discount does an account really receive?

## Filters
- Sales region
- Account manager
- Size tier
- Industry
- Period (by booking date): presets *Year to date 2026* (default), *Last 12 months*, *Full year 2025*, or a custom range

## Content

### KPI row
Five headline numbers for the current filters: Booked net revenue, Tickets sold,
Average net fare, Cancellation rate and Year-over-year growth.

### Monthly revenue trend
Line chart of booked net revenue by booking month, for the current filters.

### Top 10 accounts
Horizontal bar chart of the ten accounts with the highest booked net revenue.

### Revenue by size tier and industry
Two bar charts showing booked net revenue split by size tier and by industry.

### Account table
One row per account, sortable, with: account name, size tier, account manager, booked net revenue,
tickets sold, average net fare, cancellation rate, effective discount rate and year-over-year growth.
Rows with a cancellation rate above 15% are highlighted in red.

## Metrics used
- Booked net revenue
- Tickets sold
- Average net fare
- Effective discount rate
- Cancellation rate
- Year-over-year growth

## Data sources
Tables `bookings` and `accounts`. The discount shown comes from the tickets, so it matches the contract discount of each account.

## What this dashboard does not show
- Route, distance or cabin details: see the Route & Cabin Revenue dashboard.
- Regional targets and contract commitments: see the Targets & Contract Compliance dashboard.
- Flown revenue and gross revenue are not displayed (they can be computed from the data).
- Year-over-year growth is only available for periods starting in 2026, because the data starts on 2025-01-01; for other periods the tile shows n/a.
