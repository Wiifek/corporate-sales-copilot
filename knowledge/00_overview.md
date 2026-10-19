---
doc_id: overview
doc_type: overview
title: Corporate Sales Knowledge Base – Overview
languages: [en, fr]
---

# Corporate Sales Knowledge Base – Overview

## What this knowledge base is about

The airline sells flights to companies ("corporate accounts") under negotiated contracts.
Each contract gives the company a **discount** on the public fare in exchange for a **commitment**
to buy a minimum number of tickets per year. The Corporate Sales team follows this business
through three dashboards. The airline operates two hubs: Paris-Charles de Gaulle (CDG) and
Amsterdam-Schiphol (AMS).

Français : la compagnie vend des billets à des entreprises (« comptes corporate ») dans le cadre
de contrats négociés. Chaque contrat accorde une remise sur le tarif public en échange d'un
engagement de volume annuel. L'équipe Corporate Sales suit cette activité via trois tableaux de bord.

## What the data covers

- **Period:** bookings made from 2025-01-01 to 2026-09-30. The **data as-of date is 2026-09-30**.
  There is no data after this date.
- **Currency:** euros (EUR). All amounts exclude taxes and ancillary services (baggage, seats, lounge).
- **Grain:** one row in the bookings table is one ticket: one passenger on one one-way flight.
- **Scope:** corporate bookings only. Public (non-corporate) sales, competitors and market
  share are not in the data.
- The data is **simulated**: it is realistic but does not describe real companies or real sales.

## The three dashboards at a glance

| Dashboard | Main question it answers | Main audience |
|---|---|---|
| Account Performance | How is each corporate account (or group of accounts) performing? | Account managers, regional directors |
| Route & Cabin Revenue | Which routes, distances and cabins generate revenue, and at what price? | Network and revenue analysts, regional directors |
| Targets & Contract Compliance | Did each region reach its revenue target? Does each account respect its contract commitment? | Regional directors, commercial control |

## Which dashboard should I use?

| If you want to know… | Use this dashboard |
|---|---|
| Revenue, tickets or cancellations of one account, a tier, an industry or an account manager | Account Performance |
| Growth of an account or region compared with the previous year | Account Performance |
| Which accounts cancel a lot or receive the largest discounts | Account Performance |
| Best-selling routes, revenue by distance (short, medium, long haul) or by cabin | Route & Cabin Revenue |
| Average fare, yield, share of premium cabins, how early tickets are booked | Route & Cabin Revenue |
| Seasonality (which months are strong or weak) | Route & Cabin Revenue |
| Whether a region met its quarterly revenue target | Targets & Contract Compliance |
| Whether an account buys enough tickets to respect its contract | Targets & Contract Compliance |

Some questions have no dashboard (for example flown revenue, gross revenue, or a custom
combination of filters). Those can still be answered by querying the data directly; each
metric page says whether a dashboard shows it.

## Who can see what

Access rules apply to every answer, whatever the question:

- **Global analyst:** all sales regions and all accounts.
- **Regional director:** only the accounts of their own sales region, and only their region's targets.
- **Account manager:** only the accounts they manage. Regional targets are not shown to them, because a target combines the revenue of accounts they do not manage.

A question about data outside the user's scope must be refused, and the refusal should say
that it is an access restriction, not that the data does not exist.

## What this assistant cannot answer

- Traveller identities or any personal data (not in the data).
- Forecasts or any figure after the as-of date (2026-09-30).
- Public fares, competitors, market share or non-corporate sales.
- Taxes, baggage, seat fees or other ancillary revenue.
- Anything outside the user's access scope (see above).

## How this knowledge base is organized

| File | Content |
|---|---|
| `metrics_glossary.md` | Definition, formula and pitfalls of every metric, plus business terms |
| `data_dictionary.md` | Every table and column, with meaning and allowed values |
| `dashboards/*.md` | One page per dashboard: purpose, filters, tiles, metrics, limits |
