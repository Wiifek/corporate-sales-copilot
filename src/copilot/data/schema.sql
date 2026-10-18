-- Schema of the synthetic Corporate Sales dataset (DuckDB).
-- Created in dependency order: parents first, children after.

CREATE TABLE airports (
    iata        VARCHAR PRIMARY KEY,
    city        VARCHAR NOT NULL,
    country     VARCHAR NOT NULL,
    region      VARCHAR NOT NULL,      -- Europe | Americas | Africa & Middle East | Asia-Pacific
    latitude    DOUBLE  NOT NULL,
    longitude   DOUBLE  NOT NULL
);

CREATE TABLE routes (
    route_id            VARCHAR PRIMARY KEY,           -- e.g. 'CDG-JFK'
    origin_iata         VARCHAR NOT NULL REFERENCES airports(iata),
    destination_iata    VARCHAR NOT NULL REFERENCES airports(iata),
    distance_km         INTEGER NOT NULL,
    haul                VARCHAR NOT NULL,              -- short (<1500 km) | medium | long (>5000 km)
    market_region       VARCHAR NOT NULL               -- region of the non-hub end of the route
);

CREATE TABLE accounts (
    account_id       VARCHAR PRIMARY KEY,              -- e.g. 'ACC-0001'
    account_name     VARCHAR NOT NULL,
    industry         VARCHAR NOT NULL,
    size_tier        VARCHAR NOT NULL,                 -- Small | Mid | Large | Strategic
    hq_city          VARCHAR NOT NULL,
    hq_country       VARCHAR NOT NULL,
    sales_region     VARCHAR NOT NULL,                 -- the sales team that owns the account
    account_manager  VARCHAR NOT NULL
);

CREATE TABLE contracts (
    contract_id                 VARCHAR PRIMARY KEY,
    account_id                  VARCHAR NOT NULL REFERENCES accounts(account_id),
    contract_type               VARCHAR NOT NULL,      -- Standard | Preferred | Strategic
    start_date                  DATE    NOT NULL,
    end_date                    DATE    NOT NULL,
    discount_pct                DOUBLE  NOT NULL,      -- negotiated discount on the gross fare
    annual_ticket_commitment    INTEGER NOT NULL       -- tickets the company promised to buy per year
);

CREATE TABLE bookings (
    booking_id      VARCHAR PRIMARY KEY,               -- e.g. 'BK-0000001'
    booking_date    DATE    NOT NULL,
    travel_date     DATE    NOT NULL,
    account_id      VARCHAR NOT NULL REFERENCES accounts(account_id),
    route_id        VARCHAR NOT NULL REFERENCES routes(route_id),
    cabin           VARCHAR NOT NULL,                  -- Economy | Premium Economy | Business
    status          VARCHAR NOT NULL,                  -- flown | upcoming | cancelled
    gross_fare_eur  DOUBLE  NOT NULL,                  -- public price of the ticket
    discount_pct    DOUBLE  NOT NULL,                  -- contract discount applied
    net_fare_eur    DOUBLE  NOT NULL                   -- gross_fare_eur * (1 - discount_pct / 100)
);

CREATE TABLE targets (
    sales_region          VARCHAR NOT NULL,
    quarter               VARCHAR NOT NULL,            -- e.g. '2025-Q1' (by booking date)
    target_revenue_eur    DOUBLE  NOT NULL,
    PRIMARY KEY (sales_region, quarter)
);
