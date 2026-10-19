---
doc_id: dashboard_route_cabin_revenue
doc_type: dashboard
title: Route & Cabin Revenue
languages: [en]
---

# Dashboard: Route & Cabin Revenue

## Purpose
Understand where corporate revenue comes from on the network: which routes, which distance
bands (haul) and which cabins sell best, at what price, and how sales vary over the year.

## Who uses it
Network and revenue analysts, and regional directors.

## Questions it answers
- Which are the best-selling routes?
- How is revenue split between short, medium and long haul, and between cabins?
- What is the average fare and the net yield of a route or haul?
- What share of tickets is sold in Premium Economy or Business?
- How early do companies book their tickets?
- Which months are strong or weak (seasonality)?

## Filters
- Market region (region of the route, not of the customer)
- Haul (short, medium, long)
- Cabin
- Period (by booking date): presets *Year to date 2026* (default), *Last 12 months*, *Full year 2025*, or a custom range

## Content

### KPI row
Five headline numbers for the current filters: Booked net revenue, Net yield,
Average net fare, Premium cabin share and Average lead time.

### Top 15 routes
Horizontal bar chart of the fifteen routes with the highest booked net revenue.

### Revenue by haul and cabin
Stacked bar chart of booked net revenue by haul, split by cabin.

### Seasonality
Column chart of tickets sold by booking month.

### Net yield by haul
Bar chart comparing the net yield of short, medium and long haul. Yield is only comparable within one haul, so this chart is meant to show the gap between hauls, not to rank routes.

### Route table
One row per route, sortable, with: route, distance, haul, tickets sold, booked net revenue,
average net fare, net yield and premium cabin share.

## Metrics used
- Booked net revenue
- Tickets sold
- Average net fare
- Net yield
- Premium cabin share
- Average lead time

## Data sources
Tables `bookings` and `routes`.

## What this dashboard does not show
- Customer information (account, industry, size tier, account manager): see the Account Performance dashboard.
- Targets and contract commitments: see the Targets & Contract Compliance dashboard.
- The market region filter describes the route, not the customer's sales region, so it cannot be used to see "revenue of the Europe sales team".
