"""Checks that the knowledge documents tell the truth about the database.

Why: the assistants answer from these documents. If a document says one thing
and the data says another, every later evaluation score would be wrong for the
wrong reason. Run with:  pytest tests/unit/test_knowledge_docs.py -v
"""
from __future__ import annotations

import re
from pathlib import Path

import duckdb
import pytest

ROOT = Path(__file__).resolve().parents[2]
KNOWLEDGE = ROOT / "knowledge"
DB_PATH = ROOT / "data" / "synthetic" / "copilot.duckdb"

REQUIRED_LABELS = ["**French name:**", "**Definition:**", "**Définition (FR):**", "**Formula:**",
                   "**Unit:**", "**Shown in:**", "**Pitfalls:**"]


@pytest.fixture(scope="module")
def con():
    if not DB_PATH.exists():
        pytest.skip("Database not found: run  python src/copilot/data/generate_synthetic.py  first")
    connection = duckdb.connect(str(DB_PATH), read_only=True)
    yield connection
    connection.close()


# ---------------------------------------------------------------- parsing helpers
def parse_glossary_metrics() -> dict[str, str]:
    """Return {metric name: full text of its section} for the '## Metrics' part."""
    section, current, metrics = None, None, {}
    for line in (KNOWLEDGE / "metrics_glossary.md").read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            section, current = line[3:].strip(), None
        elif line.startswith("### "):
            current = line[4:].strip()
            if section == "Metrics":
                metrics[current] = ""
        elif section == "Metrics" and current:
            metrics[current] += line + "\n"
    return metrics


def sql_blocks(text: str) -> list[str]:
    return re.findall(r"```sql\n(.*?)```", text, flags=re.S)


def parse_dashboards() -> dict[str, list[str]]:
    """Return {dashboard title: list of metric names under '## Metrics used'}."""
    result = {}
    for path in sorted((KNOWLEDGE / "dashboards").glob("*.md")):
        text = path.read_text(encoding="utf-8")
        title = re.search(r"^title: (.+)$", text, flags=re.M).group(1).strip()
        block = re.search(r"## Metrics used\n(.*?)(?=\n## |\Z)", text, flags=re.S).group(1)
        result[title] = [ln[2:].strip() for ln in block.splitlines() if ln.startswith("- ")]
    return result


def parse_dictionary() -> dict[str, dict[str, str]]:
    """Return {table: {column: type}} from the data dictionary."""
    tables, current = {}, None
    for line in (KNOWLEDGE / "data_dictionary.md").read_text(encoding="utf-8").splitlines():
        m = re.match(r"## Table: (\w+)", line)
        if m:
            current = m.group(1)
            tables[current] = {}
        elif current and line.startswith("| `"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            tables[current][cells[0].strip("`")] = cells[1]
    return tables


METRICS = parse_glossary_metrics()


# ---------------------------------------------------------------- glossary tests
@pytest.mark.parametrize("name", list(METRICS))
def test_metric_section_is_complete(name):
    body = METRICS[name]
    for label in REQUIRED_LABELS:
        assert label in body, f"'{name}' is missing {label}"
    assert sql_blocks(body), f"'{name}' has no SQL example"


@pytest.mark.parametrize("name", list(METRICS))
def test_metric_sql_runs_and_returns_rows(con, name):
    for sql in sql_blocks(METRICS[name]):
        rows = con.execute(sql).fetchall()
        assert rows, f"SQL of '{name}' returned no rows"


# ---------------------------------------------------------------- dictionary tests
def test_dictionary_matches_database_columns(con):
    documented = parse_dictionary()
    actual = {}
    for table, column, dtype in con.execute(
            "SELECT table_name, column_name, data_type FROM information_schema.columns "
            "WHERE table_schema = 'main'").fetchall():
        actual.setdefault(table, {})[column] = dtype
    assert set(documented) == set(actual), "tables differ between dictionary and database"
    for table in actual:
        assert documented[table] == actual[table], f"columns/types differ for table '{table}'"


def test_row_counts_stated_in_dictionary(con):
    text = (KNOWLEDGE / "data_dictionary.md").read_text(encoding="utf-8")
    stated = {"airports": r"\((\d+) airports\)", "routes": r"\((\d+) routes\)",
              "accounts": r"\((\d+) accounts\)", "targets": r"= (\d+) rows"}
    for table, pattern in stated.items():
        n = int(re.search(pattern, text).group(1))
        actual = con.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
        assert n == actual, f"{table}: dictionary says {n}, database has {actual}"


# ---------------------------------------------------------------- dashboards <-> glossary
def test_dashboard_metrics_are_defined_and_consistent():
    dashboards = parse_dashboards()
    shown_in = {}
    for name, body in METRICS.items():
        line = re.search(r"\*\*Shown in:\*\* (.+)", body).group(1).strip()
        shown_in[name] = set() if line.startswith("None") else {d.strip() for d in line.split(",")}

    for title, metrics in dashboards.items():
        for m in metrics:
            assert m in METRICS, f"dashboard '{title}' uses undefined metric '{m}'"
    for name, expected in shown_in.items():
        actual = {title for title, metrics in dashboards.items() if name in metrics}
        assert actual == expected, f"'{name}': glossary says {expected}, dashboards say {actual}"


# ---------------------------------------------------------------- facts written in prose
def test_facts_stated_in_the_documents(con):
    q = lambda sql: con.execute(sql).fetchall()

    # Data period and as-of date
    assert q("SELECT min(booking_date), max(booking_date) FROM bookings")[0] == (
        __import__("datetime").date(2025, 1, 1), __import__("datetime").date(2026, 9, 30))
    # 2026 year to date is 273 days
    assert q("SELECT date_diff('day', DATE '2026-01-01', DATE '2026-09-30') + 1")[0][0] == 273
    # 'upcoming' means a travel date after the as-of date; 'flown' means on or before it
    assert q("SELECT count(*) FROM bookings WHERE status='upcoming' AND travel_date <= DATE '2026-09-30'")[0][0] == 0
    assert q("SELECT count(*) FROM bookings WHERE status='flown' AND travel_date > DATE '2026-09-30'")[0][0] == 0
    # Haul bands
    bands = {h: (lo, hi) for h, lo, hi in q("SELECT haul, min(distance_km), max(distance_km) FROM routes GROUP BY 1")}
    assert bands["short"][1] <= 1500 and bands["medium"][0] > 1500 and bands["medium"][1] <= 5000 and bands["long"][0] > 5000
    # Short-haul routes have no Premium Economy
    assert q("""SELECT count(*) FROM bookings b JOIN routes r USING (route_id)
                WHERE r.haul='short' AND b.cabin='Premium Economy'""")[0][0] == 0
    # Every route starts or ends at a hub
    assert q("SELECT count(*) FROM routes WHERE origin_iata NOT IN ('CDG','AMS') AND destination_iata NOT IN ('CDG','AMS')")[0][0] == 0
    # Contracts: one per account, same dates, discount range, minimum commitment
    assert q("SELECT count(*) = count(DISTINCT account_id) FROM contracts")[0][0]
    assert q("SELECT min(start_date), max(start_date), min(end_date), max(end_date) FROM contracts")[0] == (
        __import__("datetime").date(2025, 1, 1),) * 2 + (__import__("datetime").date(2026, 12, 31),) * 2
    low, high = q("SELECT min(discount_pct), max(discount_pct) FROM contracts")[0]
    assert 2 <= low and high <= 20
    assert q("SELECT min(annual_ticket_commitment) FROM contracts")[0][0] >= 10
    # A ticket's discount equals its account's contract discount
    assert q("SELECT count(*) FROM bookings b JOIN contracts c USING (account_id) WHERE b.discount_pct <> c.discount_pct")[0][0] == 0
    # Targets: 4 regions x 7 quarters
    assert q("SELECT count(DISTINCT sales_region), count(DISTINCT quarter) FROM targets")[0] == (4, 7)
