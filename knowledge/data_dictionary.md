---
doc_id: data_dictionary
doc_type: data_dictionary
title: Data Dictionary
languages: [en]
---

# Data Dictionary

The dataset has six tables. This page explains what each table contains, what one row means
(its "grain"), and what every column means. Amounts are in euros (EUR).

## How the tables are linked

- `bookings.account_id` → `accounts.account_id` (who bought the ticket)
- `bookings.route_id` → `routes.route_id` (which flight)
- `contracts.account_id` → `accounts.account_id` (the contract of the account)
- `routes.origin_iata` and `routes.destination_iata` → `airports.iata`
- `targets.sales_region` matches `accounts.sales_region` (same region names; this is a join on the name, not a foreign key)

Typical join for revenue by region and route type:
`bookings b JOIN accounts a USING (account_id) JOIN routes r USING (route_id)`.

## Table: airports

One row per airport (46 airports). Airports are real, with real coordinates.

| Column | Type | Description | Allowed values / notes |
|---|---|---|---|
| `iata` | VARCHAR | Three-letter airport code, primary key | e.g. CDG, AMS, JFK |
| `city` | VARCHAR | City served by the airport | e.g. Paris |
| `country` | VARCHAR | Country of the airport | e.g. France |
| `region` | VARCHAR | Geographic region of the airport | Europe, Americas, Africa & Middle East, Asia-Pacific |
| `latitude` | DOUBLE | Latitude in decimal degrees | used to compute route distances |
| `longitude` | DOUBLE | Longitude in decimal degrees | used to compute route distances |

## Table: routes

One row per **directed** route (178 routes). CDG-JFK and JFK-CDG are two different routes.
Every route starts or ends at one of the two hubs (CDG or AMS).

| Column | Type | Description | Allowed values / notes |
|---|---|---|---|
| `route_id` | VARCHAR | Route identifier, primary key | origin-destination, e.g. CDG-JFK |
| `origin_iata` | VARCHAR | Departure airport | foreign key to `airports.iata` |
| `destination_iata` | VARCHAR | Arrival airport | foreign key to `airports.iata` |
| `distance_km` | INTEGER | Great-circle distance in kilometres | computed from airport coordinates |
| `haul` | VARCHAR | Distance band | short (up to 1,500 km), medium (up to 5,000 km), long (over 5,000 km) |
| `market_region` | VARCHAR | Region of the end of the route that is not a hub | Europe, Americas, Africa & Middle East, Asia-Pacific |

## Table: accounts

One row per corporate account, i.e. per company customer (150 accounts).

| Column | Type | Description | Allowed values / notes |
|---|---|---|---|
| `account_id` | VARCHAR | Account identifier, primary key | format ACC-0001 |
| `account_name` | VARCHAR | Company name | fictional names |
| `industry` | VARCHAR | Industry of the company | Consulting, Banking & Finance, Pharma & Health, Technology, Energy, Automotive, Luxury & Retail, Public Sector, Logistics, Aerospace & Defense |
| `size_tier` | VARCHAR | Size class of the account | Small, Mid, Large, Strategic |
| `hq_city` | VARCHAR | City of the company headquarters | a city of the airports table |
| `hq_country` | VARCHAR | Country of the company headquarters | |
| `sales_region` | VARCHAR | Sales team that owns the account, based on the headquarters | Europe, Americas, Africa & Middle East, Asia-Pacific |
| `account_manager` | VARCHAR | Name of the airline employee who manages the account | several accounts per manager |

## Table: contracts

One row per contract. Each account has exactly one contract, covering the whole data period.

| Column | Type | Description | Allowed values / notes |
|---|---|---|---|
| `contract_id` | VARCHAR | Contract identifier, primary key | format CTR-0001 |
| `account_id` | VARCHAR | Account that signed the contract | foreign key to `accounts.account_id` |
| `contract_type` | VARCHAR | Type of agreement | Standard, Preferred, Strategic |
| `start_date` | DATE | First day of the contract | 2025-01-01 for all contracts |
| `end_date` | DATE | Last day of the contract | 2026-12-31 for all contracts |
| `discount_pct` | DOUBLE | Negotiated discount on the gross fare, in percent | between 2 and 20; higher for larger tiers |
| `annual_ticket_commitment` | INTEGER | Number of tickets the account commits to buy per year | at least 10 |

## Table: bookings

One row per **ticket**: one passenger on one one-way flight. This is the largest table
(about 250,000 rows by default). Booking dates run from 2025-01-01 to 2026-09-30.

| Column | Type | Description | Allowed values / notes |
|---|---|---|---|
| `booking_id` | VARCHAR | Ticket identifier, primary key | format BK-0000001 |
| `booking_date` | DATE | Day the ticket was bought | 2025-01-01 to 2026-09-30 |
| `travel_date` | DATE | Day of the flight | after the booking date; can be after the as-of date |
| `account_id` | VARCHAR | Account that bought the ticket | foreign key to `accounts.account_id` |
| `route_id` | VARCHAR | Route flown | foreign key to `routes.route_id` |
| `cabin` | VARCHAR | Travel class | Economy, Premium Economy, Business |
| `status` | VARCHAR | State of the ticket | flown, upcoming, cancelled |
| `gross_fare_eur` | DOUBLE | Public price of the ticket before discount | in EUR |
| `discount_pct` | DOUBLE | Contract discount applied to this ticket | same value as the account contract |
| `net_fare_eur` | DOUBLE | Price after discount: gross fare × (1 − discount_pct / 100) | in EUR; this is the revenue |

Notes on `status`: a `cancelled` ticket still has fares in the table but generates no revenue
and must be excluded from revenue and ticket counts. A ticket is `upcoming` when its travel date
is after 2026-09-30.

## Table: targets

One row per sales region and quarter (4 regions × 7 quarters = 28 rows).
The primary key is the pair `sales_region` + `quarter`.

| Column | Type | Description | Allowed values / notes |
|---|---|---|---|
| `sales_region` | VARCHAR | Sales region the target applies to | Europe, Americas, Africa & Middle East, Asia-Pacific |
| `quarter` | VARCHAR | Calendar quarter, by booking date | 2025-Q1 to 2026-Q3 |
| `target_revenue_eur` | DOUBLE | Booked net revenue the region had to reach in the quarter | in EUR |

## Known limitations of the data

- The data is simulated; companies, contracts and fares are fictional.
- No passenger identity, no taxes, no ancillary revenue, no public (non-corporate) sales.
- Every account has a single contract covering the whole period.
- Targets exist only at region and quarter level.
- 2026 is incomplete: the last booking date is 2026-09-30.
