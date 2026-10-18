"""Generate the synthetic Corporate Sales dataset into a DuckDB file.

Usage (from the repo root):
    python src/copilot/data/generate_synthetic.py
    python src/copilot/data/generate_synthetic.py --bookings 50000 --csv

Everything is driven by a fixed random seed, so the same command always
produces the same dataset (important for reproducible evaluation later).
"""
from __future__ import annotations

import argparse
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
from faker import Faker

# --------------------------------------------------------------------------
# 1. Global settings
# --------------------------------------------------------------------------
SEED = 42
START = pd.Timestamp("2025-01-01")   # first booking date
END = pd.Timestamp("2026-09-30")     # last booking date = "data as of" date
AS_OF = END                          # trips after this date are 'upcoming'
N_ACCOUNTS = 150
HUBS = ("CDG", "AMS")                # the airline's two hubs

REGIONS = ["Europe", "Americas", "Africa & Middle East", "Asia-Pacific"]
REGION_P = [0.45, 0.25, 0.12, 0.18]  # share of accounts headquartered in each region

TIERS = ["Small", "Mid", "Large", "Strategic"]
TIER_P = [0.45, 0.30, 0.18, 0.07]
TIER_MONTHLY_TICKETS = {"Small": 12, "Mid": 60, "Large": 250, "Strategic": 900}
TIER_DISCOUNT = {"Small": (2, 5), "Mid": (5, 9), "Large": (9, 14), "Strategic": (14, 20)}
TIER_CONTRACT = {"Small": "Standard", "Mid": "Preferred", "Large": "Preferred", "Strategic": "Strategic"}
TIER_BUSINESS_BASE = {"Small": 0.15, "Mid": 0.22, "Large": 0.30, "Strategic": 0.38}

INDUSTRIES = ["Consulting", "Banking & Finance", "Pharma & Health", "Technology", "Energy",
              "Automotive", "Luxury & Retail", "Public Sector", "Logistics", "Aerospace & Defense"]
INDUSTRY_P = [0.14, 0.14, 0.11, 0.15, 0.09, 0.08, 0.08, 0.06, 0.07, 0.08]

# Seasonality of business travel (1.0 = normal). August and late December are slow.
MONTH_FACTOR = {1: 0.90, 2: 1.00, 3: 1.10, 4: 1.00, 5: 1.10, 6: 1.10,
                7: 0.85, 8: 0.60, 9: 1.20, 10: 1.20, 11: 1.10, 12: 0.75}
# Business travellers book on weekdays, not weekends.
DOW_FACTOR = {0: 1.2, 1: 1.2, 2: 1.2, 3: 1.2, 4: 1.0, 5: 0.35, 6: 0.5}

# --------------------------------------------------------------------------
# 2. Airports (hard-coded: no download needed, fully reproducible)
# --------------------------------------------------------------------------
# iata, city, country, region, latitude, longitude
AIRPORTS = [
    ("CDG", "Paris", "France", "Europe", 49.0097, 2.5479),
    ("AMS", "Amsterdam", "Netherlands", "Europe", 52.3105, 4.7683),
    ("NCE", "Nice", "France", "Europe", 43.6584, 7.2159),
    ("TLS", "Toulouse", "France", "Europe", 43.6291, 1.3638),
    ("LYS", "Lyon", "France", "Europe", 45.7256, 5.0811),
    ("MRS", "Marseille", "France", "Europe", 43.4393, 5.2214),
    ("BOD", "Bordeaux", "France", "Europe", 44.8283, -0.7156),
    ("LHR", "London", "United Kingdom", "Europe", 51.4700, -0.4543),
    ("FRA", "Frankfurt", "Germany", "Europe", 50.0379, 8.5622),
    ("MAD", "Madrid", "Spain", "Europe", 40.4983, -3.5676),
    ("BCN", "Barcelona", "Spain", "Europe", 41.2974, 2.0833),
    ("FCO", "Rome", "Italy", "Europe", 41.8003, 12.2389),
    ("MXP", "Milan", "Italy", "Europe", 45.6306, 8.7281),
    ("ZRH", "Zurich", "Switzerland", "Europe", 47.4647, 8.5492),
    ("BRU", "Brussels", "Belgium", "Europe", 50.9014, 4.4844),
    ("LIS", "Lisbon", "Portugal", "Europe", 38.7742, -9.1342),
    ("DUB", "Dublin", "Ireland", "Europe", 53.4264, -6.2499),
    ("CPH", "Copenhagen", "Denmark", "Europe", 55.6180, 12.6508),
    ("TUN", "Tunis", "Tunisia", "Africa & Middle East", 36.8510, 10.2272),
    ("CMN", "Casablanca", "Morocco", "Africa & Middle East", 33.3675, -7.5898),
    ("ALG", "Algiers", "Algeria", "Africa & Middle East", 36.6910, 3.2154),
    ("ABJ", "Abidjan", "Ivory Coast", "Africa & Middle East", 5.2614, -3.9263),
    ("DXB", "Dubai", "United Arab Emirates", "Africa & Middle East", 25.2532, 55.3657),
    ("JNB", "Johannesburg", "South Africa", "Africa & Middle East", -26.1392, 28.2460),
    ("LOS", "Lagos", "Nigeria", "Africa & Middle East", 6.5774, 3.3212),
    ("CAI", "Cairo", "Egypt", "Africa & Middle East", 30.1219, 31.4056),
    ("JFK", "New York", "United States", "Americas", 40.6413, -73.7781),
    ("LAX", "Los Angeles", "United States", "Americas", 33.9416, -118.4085),
    ("ORD", "Chicago", "United States", "Americas", 41.9742, -87.9073),
    ("ATL", "Atlanta", "United States", "Americas", 33.6407, -84.4277),
    ("MIA", "Miami", "United States", "Americas", 25.7959, -80.2870),
    ("SFO", "San Francisco", "United States", "Americas", 37.6213, -122.3790),
    ("IAH", "Houston", "United States", "Americas", 29.9902, -95.3368),
    ("BOS", "Boston", "United States", "Americas", 42.3656, -71.0096),
    ("YUL", "Montreal", "Canada", "Americas", 45.4706, -73.7408),
    ("MEX", "Mexico City", "Mexico", "Americas", 19.4363, -99.0721),
    ("GRU", "Sao Paulo", "Brazil", "Americas", -23.4356, -46.4731),
    ("HND", "Tokyo", "Japan", "Asia-Pacific", 35.5494, 139.7798),
    ("PEK", "Beijing", "China", "Asia-Pacific", 40.0799, 116.5849),
    ("PVG", "Shanghai", "China", "Asia-Pacific", 31.1443, 121.8083),
    ("SIN", "Singapore", "Singapore", "Asia-Pacific", 1.3644, 103.9915),
    ("BOM", "Mumbai", "India", "Asia-Pacific", 19.0896, 72.8656),
    ("DEL", "Delhi", "India", "Asia-Pacific", 28.5562, 77.1000),
    ("ICN", "Seoul", "South Korea", "Asia-Pacific", 37.4602, 126.4407),
    ("BKK", "Bangkok", "Thailand", "Asia-Pacific", 13.6900, 100.7501),
    ("HKG", "Hong Kong", "Hong Kong", "Asia-Pacific", 22.3080, 113.9185),
]
# How popular an airport is for corporate travel (default 1.0).
AIRPORT_WEIGHT = {"LHR": 4, "FRA": 4, "JFK": 4, "MAD": 2.5, "BCN": 2.5, "ZRH": 2.5,
                  "NCE": 2.5, "FCO": 2, "MXP": 2, "BRU": 2, "TLS": 2, "LYS": 2,
                  "DXB": 3, "SIN": 2.5, "HND": 2.5, "LAX": 2.5, "YUL": 2.5,
                  "SFO": 2, "PVG": 2, "ORD": 2, "CMN": 1.5}


def haversine_km(lat1, lon1, lat2, lon2):
    """Great-circle distance between two points, in kilometres."""
    r = 6371.0088
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dphi, dlmb = p2 - p1, np.radians(lon2 - lon1)
    a = np.sin(dphi / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dlmb / 2) ** 2
    return 2 * r * np.arcsin(np.sqrt(a))


def build_airports() -> pd.DataFrame:
    return pd.DataFrame(AIRPORTS, columns=["iata", "city", "country", "region", "latitude", "longitude"])


# --------------------------------------------------------------------------
# 3. Routes: hub-and-spoke network around CDG and AMS
# --------------------------------------------------------------------------
def build_routes(airports: pd.DataFrame) -> pd.DataFrame:
    ap = airports.set_index("iata")
    rows, seen = [], set()
    for hub in HUBS:
        for other in ap.index:
            if other == hub:
                continue
            for o, d in ((hub, other), (other, hub)):
                if (o, d) in seen:
                    continue
                seen.add((o, d))
                partner = d if d not in HUBS else (o if o not in HUBS else d)
                km = float(haversine_km(ap.at[o, "latitude"], ap.at[o, "longitude"],
                                        ap.at[d, "latitude"], ap.at[d, "longitude"]))
                weight = AIRPORT_WEIGHT.get(partner, 1.0) * (1.3 if "CDG" in (o, d) else 1.0)
                rows.append({"route_id": f"{o}-{d}", "origin_iata": o, "destination_iata": d,
                             "distance_km": int(round(km)), "market_region": ap.at[partner, "region"],
                             "gen_weight": weight})
    routes = pd.DataFrame(rows)
    routes["haul"] = pd.cut(routes["distance_km"], bins=[0, 1500, 5000, 1e9],
                            labels=["short", "medium", "long"]).astype(str)
    return routes


# --------------------------------------------------------------------------
# 4. Accounts (the companies that buy flights)
# --------------------------------------------------------------------------
def build_accounts(rng: np.random.Generator, fake: Faker, airports: pd.DataFrame) -> pd.DataFrame:
    n = N_ACCOUNTS
    regions = rng.choice(REGIONS, size=n, p=REGION_P)
    tiers = rng.choice(TIERS, size=n, p=TIER_P)
    industries = rng.choice(INDUSTRIES, size=n, p=INDUSTRY_P)

    # A small pool of account managers per region (they own several accounts each).
    managers = {r: [fake.name() for _ in range(5)] for r in REGIONS}

    names, seen = [], set()
    while len(names) < n:
        nm = fake.company()
        if nm not in seen:
            seen.add(nm)
            names.append(nm)

    rows = []
    for i in range(n):
        pool = airports[airports["region"] == regions[i]]
        hq = pool.iloc[rng.integers(len(pool))]
        rows.append({
            "account_id": f"ACC-{i + 1:04d}",
            "account_name": names[i],
            "industry": industries[i],
            "size_tier": tiers[i],
            "hq_city": hq["city"],
            "hq_country": hq["country"],
            "sales_region": regions[i],
            "account_manager": managers[regions[i]][rng.integers(5)],
            # --- internal generation parameters (not stored in the database) ---
            "gen_volume": TIER_MONTHLY_TICKETS[tiers[i]] * rng.lognormal(0, 0.35),
            "gen_growth": rng.normal(0.05, 0.20),        # yearly trend: some accounts grow, some shrink
            "gen_cancel_rate": rng.beta(2, 26),          # mean ~7%, a few accounts cancel a lot
        })
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------
# 5. Bookings (the big table) and contracts
# --------------------------------------------------------------------------
def base_fare(km: np.ndarray, haul: np.ndarray) -> np.ndarray:
    """Economy flexible fare in EUR by distance band."""
    return np.select([haul == "short", haul == "medium"],
                     [90 + 0.11 * km, 150 + 0.09 * km], default=250 + 0.075 * km)


def sample_cabin(rng: np.random.Generator, haul: np.ndarray, tier: str) -> np.ndarray:
    """Short flights: Economy/Business. Medium and long: also Premium Economy."""
    p_bus = TIER_BUSINESS_BASE[tier] * np.select([haul == "short", haul == "medium"], [0.6, 1.0], default=1.3)
    p_pe = np.where(haul == "short", 0.0, 0.15)
    u = rng.random(len(haul))
    return np.where(u < p_bus, "Business", np.where(u < p_bus + p_pe, "Premium Economy", "Economy"))


def build_bookings_and_contracts(rng, accounts, routes, n_bookings):
    days = pd.date_range(START, END, freq="D")
    t_years = (days - START).days.to_numpy() / 365.25
    day_w = np.array([MONTH_FACTOR[d.month] * DOW_FACTOR[d.dayofweek] for d in days])

    # Route popularity, boosted when the route serves the account's home region.
    r_w = routes["gen_weight"].to_numpy()
    route_p = {}
    for region in REGIONS:
        w = r_w * np.where(routes["market_region"].to_numpy() == region, 2.5, 1.0)
        route_p[region] = w / w.sum()
    r_km = routes["distance_km"].to_numpy()
    r_haul = routes["haul"].to_numpy()
    r_id = routes["route_id"].to_numpy()

    # How many bookings does each account get? (heavy-tailed: a few big accounts dominate)
    share = accounts["gen_volume"] / accounts["gen_volume"].sum()
    counts = rng.multinomial(n_bookings, share.to_numpy())

    contracts, frames = [], []
    for acc, n in zip(accounts.itertuples(index=False), counts):
        # --- contract: one per account, covering the whole period ---
        lo, hi = TIER_DISCOUNT[acc.size_tier]
        discount = round(float(rng.uniform(lo, hi)), 1)
        yearly_expected = n / ((END - START).days / 365.25)
        commitment = max(10, int(5 * round(yearly_expected * rng.uniform(0.7, 1.2) / 5)))
        contracts.append({
            "contract_id": f"CTR-{acc.account_id[4:]}", "account_id": acc.account_id,
            "contract_type": TIER_CONTRACT[acc.size_tier], "start_date": START,
            "end_date": pd.Timestamp("2026-12-31"), "discount_pct": discount,
            "annual_ticket_commitment": commitment,
        })
        if n == 0:
            continue

        # --- bookings ---
        p = np.clip(day_w * (1 + acc.gen_growth * (t_years - t_years.mean())), 0.05, None)
        booking_date = days[rng.choice(len(days), size=n, p=p / p.sum())]
        ridx = rng.choice(len(routes), size=n, p=route_p[acc.sales_region])
        haul = r_haul[ridx]
        cabin = sample_cabin(rng, haul, acc.size_tier)

        cabin_mult = np.select(
            [cabin == "Economy", cabin == "Premium Economy"],
            [1.0, 1.7],
            default=np.select([haul == "short", haul == "medium"], [2.0, 2.6], default=3.4))
        gross = base_fare(r_km[ridx], haul) * cabin_mult * rng.lognormal(-0.016, 0.18, n)

        lead = np.minimum(1 + rng.gamma(2.0, 9.0, n), 90).astype(int)
        travel_date = booking_date + pd.to_timedelta(lead, unit="D")
        cancelled = rng.random(n) < acc.gen_cancel_rate
        status = np.where(cancelled, "cancelled", np.where(travel_date <= AS_OF, "flown", "upcoming"))

        frames.append(pd.DataFrame({
            "booking_date": booking_date, "travel_date": travel_date,
            "account_id": acc.account_id, "route_id": r_id[ridx], "cabin": cabin,
            "status": status, "gross_fare_eur": gross.round(2), "discount_pct": discount,
        }))

    bookings = pd.concat(frames, ignore_index=True).sort_values("booking_date", kind="stable")
    bookings = bookings.reset_index(drop=True)
    bookings.insert(0, "booking_id", [f"BK-{i + 1:07d}" for i in range(len(bookings))])
    bookings["net_fare_eur"] = (bookings["gross_fare_eur"] * (1 - bookings["discount_pct"] / 100)).round(2)
    return bookings, pd.DataFrame(contracts)


# --------------------------------------------------------------------------
# 6. Targets (what each sales region was expected to sell per quarter)
# --------------------------------------------------------------------------
def build_targets(rng, bookings, accounts) -> pd.DataFrame:
    df = bookings.merge(accounts[["account_id", "sales_region"]], on="account_id")
    df = df[df["status"] != "cancelled"]
    df["quarter"] = df["booking_date"].dt.year.astype(str) + "-Q" + df["booking_date"].dt.quarter.astype(str)
    actual = df.groupby(["sales_region", "quarter"], as_index=False)["net_fare_eur"].sum()
    # Targets are set around actuals so some regions beat them and some miss them.
    actual["target_revenue_eur"] = (actual["net_fare_eur"] * rng.uniform(0.88, 1.12, len(actual)) / 1e4).round() * 1e4
    return actual[["sales_region", "quarter", "target_revenue_eur"]]


# --------------------------------------------------------------------------
# 7. Load into DuckDB + sanity checks
# --------------------------------------------------------------------------
def load_duckdb(out: Path, tables: dict[str, pd.DataFrame]) -> duckdb.DuckDBPyConnection:
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        out.unlink()                       # start clean: the script is re-runnable
    con = duckdb.connect(str(out))
    con.execute((Path(__file__).parent / "schema.sql").read_text())
    for name in ["airports", "routes", "accounts", "contracts", "bookings", "targets"]:
        df = tables[name]
        con.register("df_in", df)
        cols = ", ".join(df.columns)
        con.execute(f"INSERT INTO {name} ({cols}) SELECT {cols} FROM df_in")
        con.unregister("df_in")
    return con


def validate(con: duckdb.DuckDBPyConnection) -> None:
    print("\n=== Sanity checks ===")
    for t in ["airports", "routes", "accounts", "contracts", "bookings", "targets"]:
        print(f"{t:<10} {con.execute(f'SELECT count(*) FROM {t}').fetchone()[0]:>9,} rows")

    cancel = con.execute("SELECT avg((status='cancelled')::INT) FROM bookings").fetchone()[0]
    print(f"\ncancellation rate: {cancel:.1%}")
    assert 0.04 < cancel < 0.12, "cancellation rate looks wrong"

    print("\nNet revenue by sales region (non-cancelled, EUR M):")
    print(con.execute("""
        SELECT a.sales_region, round(sum(b.net_fare_eur)/1e6, 1) AS revenue_m, count(*) AS tickets
        FROM bookings b JOIN accounts a USING (account_id)
        WHERE b.status <> 'cancelled' GROUP BY 1 ORDER BY 2 DESC""").df().to_string(index=False))

    top = con.execute("""
        WITH r AS (SELECT account_id, sum(net_fare_eur) rev FROM bookings WHERE status<>'cancelled' GROUP BY 1),
             ranked AS (SELECT rev, row_number() OVER (ORDER BY rev DESC) rk, count(*) OVER () n FROM r)
        SELECT sum(CASE WHEN rk <= n*0.1 THEN rev END) / sum(rev) FROM ranked""").fetchone()[0]
    print(f"\ntop 10% of accounts = {top:.0%} of revenue")

    print("\nBookings per month (shows seasonality):")
    print(con.execute("""SELECT strftime(booking_date, '%Y-%m') AS month, count(*) AS bookings
                         FROM bookings GROUP BY 1 ORDER BY 1""").df().to_string(index=False))

    print("\nAverage net fare by cabin and haul (EUR):")
    print(con.execute("""
        SELECT r.haul, b.cabin, round(avg(b.net_fare_eur)) AS avg_net_fare
        FROM bookings b JOIN routes r USING (route_id)
        GROUP BY 1, 2 ORDER BY 1, 2""").df().to_string(index=False))

    print("\nContract compliance preview (2025 tickets vs yearly commitment):")
    print(con.execute("""
        WITH t AS (SELECT account_id, count(*) AS tickets FROM bookings
                   WHERE status <> 'cancelled' AND year(booking_date) = 2025 GROUP BY 1)
        SELECT round(avg(t.tickets / c.annual_ticket_commitment), 2) AS avg_ratio,
               sum((t.tickets >= c.annual_ticket_commitment)::INT) AS accounts_meeting_commitment,
               count(*) AS accounts
        FROM t JOIN contracts c USING (account_id)""").df().to_string(index=False))
    print("\nAll checks passed.")


# --------------------------------------------------------------------------
# 8. Main
# --------------------------------------------------------------------------
def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bookings", type=int, default=250_000, help="number of bookings to generate")
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--out", type=Path, default=Path("data/synthetic/copilot.duckdb"))
    ap.add_argument("--csv", action="store_true", help="also export each table as CSV next to the database")
    args = ap.parse_args()

    rng = np.random.default_rng(args.seed)
    Faker.seed(args.seed)
    fake = Faker(["fr_FR", "en_GB", "de_DE", "es_ES", "it_IT"])
    fake.seed_instance(args.seed)

    airports = build_airports()
    routes = build_routes(airports)
    accounts = build_accounts(rng, fake, airports)
    bookings, contracts = build_bookings_and_contracts(rng, accounts, routes, args.bookings)
    targets = build_targets(rng, bookings, accounts)

    tables = {
        "airports": airports,
        "routes": routes.drop(columns=["gen_weight"]),
        "accounts": accounts.drop(columns=[c for c in accounts.columns if c.startswith("gen_")]),
        "contracts": contracts,
        "bookings": bookings,
        "targets": targets,
    }
    con = load_duckdb(args.out, tables)
    validate(con)

    if args.csv:
        for name, df in tables.items():
            df.to_csv(args.out.parent / f"{name}.csv", index=False)
        print(f"\nCSV files written to {args.out.parent}/")
    print(f"\nDatabase ready: {args.out}")


if __name__ == "__main__":
    main()
