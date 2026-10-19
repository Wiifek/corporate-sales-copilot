---
doc_id: dashboard_targets_and_compliance
doc_type: dashboard
title: Targets & Contract Compliance
languages: [en]
---

# Dashboard: Targets & Contract Compliance

## Purpose
Check two commitments in one place: whether each sales region reached its quarterly revenue
target, and whether each account buys enough tickets to respect its contract commitment.

## Who uses it
Regional directors and commercial control (targets); account managers and regional directors (contracts).

## Questions it answers
- Did a region reach its revenue target in a given quarter, and by how much did it miss or beat it?
- Which regions are furthest from their target?
- Which accounts respect their contract commitment, which are at risk and which are off track?
- How far is an account from its (prorated) commitment, in tickets?

## Filters
- Sales region
- Quarter (targets section)
- Period: calendar year 2025 or 2026 year to date, up to 2026-09-30 (contracts section)
- Account manager, size tier and contract type (contracts section)

## Content

### Section A: Regional targets

#### Target vs actual by region
Clustered bar chart comparing the target and the booked net revenue of each sales region, per quarter.

#### Target attainment table
One row per sales region and one column per quarter, showing target attainment in percent
with colour bands: green at 100% or more, amber from 90% to under 100%, red under 90%.
A second table shows the gap in euros (booked net revenue minus target).

### Section B: Contract compliance

#### Compliance status summary
Number of accounts in each Contract compliance status (On track, At risk, Off track) for the chosen period.

#### Account compliance table
One row per account, sortable, with: account name, account manager, contract type, annual commitment,
prorated commitment for the period, tickets sold, commitment attainment, gap to commitment and compliance status.
The gap is tickets sold minus prorated commitment; a negative gap is a shortfall.

## Metrics used
- Booked net revenue
- Tickets sold
- Target attainment
- Commitment attainment
- Contract compliance status

## Access
Section A (regional targets) is not shown to account managers, because targets combine the revenue of accounts they do not manage. Regional directors see only their own region.

## Data sources
Tables `targets`, `bookings`, `accounts` and `contracts`.

## What this dashboard does not show
- Targets per account, route or month: targets only exist per sales region and quarter.
- Route, distance or cabin details: see the Route & Cabin Revenue dashboard.
- Revenue trends and cancellations per account: see the Account Performance dashboard.
- The colour bands of the target table (100% and 90%) differ from the compliance thresholds of contracts (100% and 85%).
