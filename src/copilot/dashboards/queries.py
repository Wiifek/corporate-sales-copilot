"""Every SQL query used by the dashboards.

There is no Streamlit code in this file, so everything can be unit-tested.
Two rules make the dashboards trustworthy:
1. Each metric is defined ONCE here, exactly as in knowledge/metrics_glossary.md
   (a test compares the two).
2. The access scope is added to every query, so filters can never widen it.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date

import duckdb
import pandas as pd

from copilot import config
from copilot.security.access import Scope

# ---------------------------------------------------------------- metric definitions
NC = "b.status <> 'cancelled'"        # "non-cancelled ticket"
EXPR = {
    "revenue": f"sum(b.net_fare_eur) FILTER (WHERE {NC})",                         # Booked net revenue
    "tickets": f"count(*) FILTER (WHERE {NC})",                                    # Tickets sold
    "cancel_rate": "100.0 * avg((b.status = 'cancelled')::INT)",                   # Cancellation rate (%)
    "premium_share": ("100.0 * avg((b.cabin IN ('Premium Economy', 'Business'))::INT) "
                      f"FILTER (WHERE {NC})"),                                     # Premium cabin share (%)
    "lead_time": f"avg(date_diff('day', b.booking_date, b.travel_date)) FILTER (WHERE {NC})",
}
EXPR["avg_fare"] = f"{EXPR['revenue']} / nullif({EXPR['tickets']}, 0)"             # Average net fare
EXPR["discount_rate"] = (f"100.0 * (1 - {EXPR['revenue']} / "
                         f"nullif(sum(b.gross_fare_eur) FILTER (WHERE {NC}), 0))")  # Effective discount rate (%)
EXPR["net_yield"] = (f"100.0 * {EXPR['revenue']} / "
                     f"nullif(sum(r.distance_km) FILTER (WHERE {NC}), 0)")          # Net yield (cents per pkm)

FROM = "FROM bookings b JOIN accounts a USING (account_id) JOIN routes r USING (route_id)"

# Columns the dashboards are allowed to group by (a whitelist: nothing from the UI goes into SQL text).
DIMENSIONS = {"size_tier": "a.size_tier", "industry": "a.industry", "sales_region": "a.sales_region",
              "haul": "r.haul", "cabin": "b.cabin", "market_region": "r.market_region"}
OPTION_COLUMNS = {"sales_region": config.REGIONS, "size_tier": config.TIERS,
                  "account_manager": None, "industry": None}   # value = preferred display order


# ---------------------------------------------------------------- filters
@dataclass(frozen=True)
class Filters:
    """What the user chose in the sidebar. An empty tuple means 'all'."""
    date_from: date
    date_to: date
    sales_regions: tuple = ()
    managers: tuple = ()
    tiers: tuple = ()
    industries: tuple = ()
    market_regions: tuple = ()
    hauls: tuple = ()
    cabins: tuple = ()


FILTER_COLUMNS = {"sales_regions": "a.sales_region", "managers": "a.account_manager",
                  "tiers": "a.size_tier", "industries": "a.industry",
                  "market_regions": "r.market_region", "hauls": "r.haul", "cabins": "b.cabin"}


def _where(f: Filters, scope: Scope) -> tuple[str, list]:
    scope_sql, scope_params = scope.account_predicate("a")
    clauses = ["b.booking_date BETWEEN ? AND ?", scope_sql]
    params: list = [f.date_from, f.date_to, *scope_params]
    for attr, column in FILTER_COLUMNS.items():
        values = getattr(f, attr)
        if values:
            clauses.append(f"{column} IN ({','.join('?' * len(values))})")
            params.extend(values)
    return " AND ".join(clauses), params


def _run(con: duckdb.DuckDBPyConnection, sql: str, params: list | None = None) -> pd.DataFrame:
    # A cursor per query keeps one shared connection safe across Streamlit threads.
    return con.cursor().execute(sql, params or []).df()


def _select(names) -> str:
    return ", ".join(f"{EXPR[n]} AS {n}" for n in names)


# ---------------------------------------------------------------- period helpers
def _shift_year(d: date) -> date:
    return (pd.Timestamp(d) - pd.DateOffset(years=1)).date()


def previous_year(f: Filters) -> Filters:
    return replace(f, date_from=_shift_year(f.date_from), date_to=_shift_year(f.date_to))


def yoy_available(f: Filters) -> bool:
    """Growth needs data from one year earlier; the data starts on 2025-01-01."""
    return previous_year(f).date_from >= config.DATA_START


# ---------------------------------------------------------------- shared by dashboards 1 and 2
def kpis(con, f: Filters, scope: Scope) -> dict:
    where, params = _where(f, scope)
    row = _run(con, f"SELECT {_select(EXPR)} {FROM} WHERE {where}", params).iloc[0]
    out = {k: (None if pd.isna(v) else float(v)) for k, v in row.items()}
    out["revenue"] = out["revenue"] or 0.0
    out["tickets"] = int(out["tickets"] or 0)
    return out


def yoy_growth(con, f: Filters, scope: Scope) -> float | None:
    """Year-over-year growth of booked net revenue in %, or None when it cannot be computed."""
    if not yoy_available(f):
        return None
    previous = kpis(con, previous_year(f), scope)["revenue"]
    if not previous:
        return None
    return 100.0 * (kpis(con, f, scope)["revenue"] / previous - 1)


def by_month(con, f: Filters, scope: Scope) -> pd.DataFrame:
    where, params = _where(f, scope)
    sql = (f"SELECT date_trunc('month', b.booking_date)::DATE AS month, {_select(['revenue', 'tickets'])} "
           f"{FROM} WHERE {where} GROUP BY 1 ORDER BY 1")
    return _run(con, sql, params)


def by_dimension(con, f: Filters, scope: Scope, dimension: str,
                 metrics=("revenue", "tickets")) -> pd.DataFrame:
    column = DIMENSIONS[dimension]            # KeyError if not whitelisted
    where, params = _where(f, scope)
    sql = (f"SELECT {column} AS {dimension}, {_select(metrics)} "
           f"{FROM} WHERE {where} GROUP BY 1 ORDER BY 2 DESC")
    return _run(con, sql, params)


# ---------------------------------------------------------------- dashboard 1: accounts
def account_table(con, f: Filters, scope: Scope) -> pd.DataFrame:
    where, params = _where(f, scope)
    metrics = _select(["revenue", "tickets", "avg_fare", "cancel_rate", "discount_rate"])
    sql = (f"SELECT a.account_id, a.account_name, a.size_tier, a.account_manager, {metrics} "
           f"{FROM} WHERE {where} "
           f"GROUP BY a.account_id, a.account_name, a.size_tier, a.account_manager ORDER BY revenue DESC")
    table = _run(con, sql, params)
    table["yoy_growth_pct"] = float("nan")
    if yoy_available(f):
        pw, pp = _where(previous_year(f), scope)
        prev = _run(con, f"SELECT a.account_id, {_select(['revenue'])} {FROM} WHERE {pw} GROUP BY 1", pp)
        prev = prev.rename(columns={"revenue": "prev_revenue"})
        table = table.merge(prev, on="account_id", how="left")
        table["yoy_growth_pct"] = 100.0 * (table["revenue"] / table["prev_revenue"] - 1)
        table = table.drop(columns="prev_revenue")
    return table


# ---------------------------------------------------------------- dashboard 2: routes
def haul_cabin(con, f: Filters, scope: Scope) -> pd.DataFrame:
    where, params = _where(f, scope)
    sql = (f"SELECT r.haul, b.cabin, {_select(['revenue'])} {FROM} WHERE {where} GROUP BY 1, 2")
    return _run(con, sql, params)


def route_table(con, f: Filters, scope: Scope) -> pd.DataFrame:
    where, params = _where(f, scope)
    metrics = _select(["tickets", "revenue", "avg_fare", "net_yield", "premium_share"])
    sql = (f"SELECT b.route_id, r.distance_km, r.haul, {metrics} "
           f"{FROM} WHERE {where} GROUP BY b.route_id, r.distance_km, r.haul ORDER BY revenue DESC")
    return _run(con, sql, params)


# ---------------------------------------------------------------- dashboard 3: targets and contracts
def target_quarters(con) -> list[str]:
    return [r[0] for r in con.cursor().execute("SELECT DISTINCT quarter FROM targets ORDER BY 1").fetchall()]


def targets_vs_actual(con, scope: Scope, quarters=(), regions=()) -> pd.DataFrame:
    """Target, booked net revenue, attainment (%) and gap (EUR) per sales region and quarter."""
    account_sql, account_params = scope.account_predicate("a")
    target_sql, target_params = scope.target_predicate("t")   # PermissionError for account managers
    clauses, params = [target_sql], list(target_params)
    if quarters:
        clauses.append(f"t.quarter IN ({','.join('?' * len(quarters))})")
        params += list(quarters)
    if regions:
        clauses.append(f"t.sales_region IN ({','.join('?' * len(regions))})")
        params += list(regions)
    sql = f"""
        WITH actual AS (
            SELECT a.sales_region,
                   year(b.booking_date)::VARCHAR || '-Q' || quarter(b.booking_date)::VARCHAR AS quarter,
                   {EXPR['revenue']} AS actual_eur
            FROM bookings b JOIN accounts a USING (account_id)
            WHERE {account_sql}
            GROUP BY 1, 2)
        SELECT t.sales_region, t.quarter,
               t.target_revenue_eur AS target_eur,
               coalesce(x.actual_eur, 0) AS actual_eur,
               100.0 * coalesce(x.actual_eur, 0) / t.target_revenue_eur AS attainment_pct,
               coalesce(x.actual_eur, 0) - t.target_revenue_eur AS gap_eur
        FROM targets t
        LEFT JOIN actual x ON x.sales_region = t.sales_region AND x.quarter = t.quarter
        WHERE {' AND '.join(clauses)}
        ORDER BY t.quarter, t.sales_region"""
    return _run(con, sql, [*account_params, *params])


def compliance_table(con, scope: Scope, start: date, end: date,
                     regions=(), managers=(), tiers=(), contract_types=()) -> pd.DataFrame:
    """Commitment attainment (%) and compliance status per account for a period.

    The yearly commitment is prorated: commitment * days_in_period / 365.
    """
    if not (isinstance(start, date) and isinstance(end, date)):
        raise TypeError("start and end must be dates")
    factor = f"CAST({((end - start).days + 1) / 365.0!r} AS DOUBLE)"   # DOUBLE avoids DuckDB decimal overflow
    scope_sql, params = scope.account_predicate("a")
    clauses = [scope_sql]
    for column, values in (("a.sales_region", regions), ("a.account_manager", managers),
                           ("a.size_tier", tiers), ("c.contract_type", contract_types)):
        if values:
            clauses.append(f"{column} IN ({','.join('?' * len(values))})")
            params += list(values)
    sql = f"""
        WITH sold AS (
            SELECT b.account_id, count(*) AS tickets_sold
            FROM bookings b
            WHERE {NC} AND b.booking_date BETWEEN DATE '{start.isoformat()}' AND DATE '{end.isoformat()}'
            GROUP BY 1)
        SELECT *, CASE WHEN attainment_pct >= 100 THEN 'On track'
                       WHEN attainment_pct >= 85 THEN 'At risk'
                       ELSE 'Off track' END AS compliance_status
        FROM (
            SELECT a.account_id, a.account_name, a.account_manager, a.sales_region, a.size_tier,
                   c.contract_type, c.annual_ticket_commitment,
                   c.annual_ticket_commitment * {factor} AS prorated_commitment,
                   coalesce(s.tickets_sold, 0) AS tickets_sold,
                   100.0 * coalesce(s.tickets_sold, 0) / (c.annual_ticket_commitment * {factor}) AS attainment_pct
            FROM accounts a
            JOIN contracts c USING (account_id)
            LEFT JOIN sold s USING (account_id)
            WHERE {' AND '.join(clauses)})
        ORDER BY attainment_pct"""
    return _run(con, sql, params)


# ---------------------------------------------------------------- option lists for the sidebar
def options(con, scope: Scope, column: str, regions=()) -> list[str]:
    """Values the user may pick for a filter, limited to what their scope allows."""
    if column not in OPTION_COLUMNS:
        raise ValueError(f"Not a filterable column: {column}")
    scope_sql, params = scope.account_predicate("a")
    sql = f"SELECT DISTINCT a.{column} FROM accounts a WHERE {scope_sql}"
    if regions and column == "account_manager":
        sql += f" AND a.sales_region IN ({','.join('?' * len(regions))})"
        params += list(regions)
    values = [r[0] for r in con.cursor().execute(sql, params).fetchall()]
    order = OPTION_COLUMNS[column]
    return [v for v in order if v in values] if order else sorted(values)


def contract_type_options(con, scope: Scope) -> list[str]:
    scope_sql, params = scope.account_predicate("a")
    rows = con.cursor().execute(
        f"SELECT DISTINCT c.contract_type FROM contracts c JOIN accounts a USING (account_id) WHERE {scope_sql}",
        params).fetchall()
    values = {r[0] for r in rows}
    return [v for v in config.CONTRACT_TYPES if v in values]


def all_managers(con) -> list[tuple[str, str]]:
    """(manager, region) pairs, used only by the 'Viewing as' selector (not scoped)."""
    return con.cursor().execute(
        "SELECT DISTINCT account_manager, sales_region FROM accounts ORDER BY 2, 1").fetchall()
