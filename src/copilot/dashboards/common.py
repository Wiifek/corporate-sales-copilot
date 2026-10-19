"""Streamlit helpers shared by the three dashboards."""
from __future__ import annotations

from datetime import date

import duckdb
import pandas as pd
import streamlit as st

from copilot import config, knowledge
from copilot.dashboards import queries as q
from copilot.security.access import (GLOBAL, ROLE_GLOBAL, ROLE_LABELS, ROLE_MANAGER, ROLE_REGIONAL,
                                     ROLES, Scope)

REGION_COLORS = {"Europe": "#2f6fdb", "Americas": "#e07b39", "Africa & Middle East": "#2e9e5b",
                 "Asia-Pacific": "#8b5cf6"}
STATUS_COLORS = {"On track": "#2e9e5b", "At risk": "#f0a202", "Off track": "#d64545"}


# ---------------------------------------------------------------- connection and scope
@st.cache_resource
def get_con() -> duckdb.DuckDBPyConnection:
    if not config.DB_PATH.exists():
        st.error(f"Database not found at {config.DB_PATH}. "
                 "Run: python src/copilot/data/generate_synthetic.py")
        st.stop()
    return duckdb.connect(str(config.DB_PATH), read_only=True)


def get_scope() -> Scope:
    return st.session_state.get("scope", GLOBAL)


def scope_selector() -> None:
    """Sidebar 'Viewing as' box. It simulates a login: real authentication is out of scope."""
    con = get_con()
    with st.sidebar:
        st.subheader("Viewing as")
        role = st.selectbox("Role", ROLES, format_func=ROLE_LABELS.get, key="role_choice")
        if role == ROLE_REGIONAL:
            region = st.selectbox("Sales region", config.REGIONS, key="role_region")
            scope = Scope(ROLE_REGIONAL, region=region)
        elif role == ROLE_MANAGER:
            managers = q.all_managers(con)
            name = st.selectbox("Account manager", [m for m, _ in managers], key="role_manager",
                                format_func=lambda m: f"{m} ({dict(managers)[m]})")
            scope = Scope(ROLE_MANAGER, manager=name)
        else:
            scope = Scope(ROLE_GLOBAL)
        st.session_state["scope"] = scope
        st.divider()


def scope_banner(scope: Scope) -> None:
    st.caption(f"Viewing as: {scope.describe()}")


# ---------------------------------------------------------------- sidebar filters
def multiselect(label: str, options: list[str], key: str) -> tuple:
    """Multi-select in the sidebar; nothing selected means 'All'.

    The widget key includes the access scope, so filter choices are reset when the
    user switches role (otherwise an old value could be missing from the new options).
    """
    chosen = st.sidebar.multiselect(label, options, key=f"{key}|{get_scope().key}", placeholder="All")
    return tuple(chosen)


def presets() -> dict[str, tuple[date, date] | None]:
    last_12_start = (pd.Timestamp(config.AS_OF) - pd.DateOffset(years=1) + pd.Timedelta(days=1)).date()
    return {
        "Year to date 2026": (date(2026, 1, 1), config.AS_OF),
        "Last 12 months": (last_12_start, config.AS_OF),
        "Full year 2025": (date(2025, 1, 1), date(2025, 12, 31)),
        "Custom range": None,
    }


def date_range_filter(key: str) -> tuple[date, date]:
    options = presets()
    choice = st.sidebar.selectbox("Period (booking date)", list(options), key=f"{key}_preset")
    if options[choice] is not None:
        return options[choice]
    picked = st.sidebar.date_input("Dates", value=(date(2026, 1, 1), config.AS_OF), key=f"{key}_dates",
                                   min_value=config.DATA_START, max_value=config.AS_OF)
    if isinstance(picked, tuple) and len(picked) == 2:
        return picked
    st.sidebar.info("Select an end date to continue.")
    st.stop()


# ---------------------------------------------------------------- display helpers
def metric_help(name: str) -> str:
    """Tooltip text = the glossary definition, so dashboards and documents cannot drift apart."""
    return knowledge.metric_definitions()[name]


def kpi(column, name: str, value: str) -> None:
    column.metric(name, value, help=metric_help(name))


def eur_m(x: float | None) -> str:
    return "n/a" if x is None else f"€{x / 1e6:,.1f}M"


def eur(x: float | None) -> str:
    return "n/a" if x is None else f"€{x:,.0f}"


def num(x: float | None) -> str:
    return "n/a" if x is None else f"{x:,.0f}"


def pct(x: float | None) -> str:
    return "n/a" if x is None else f"{x:.1f}%"


def style_figure(fig, height: int = 360):
    fig.update_layout(template="plotly_white", height=height, margin=dict(l=10, r=10, t=50, b=10),
                      legend_title_text="")
    return fig


def stop_if_empty(kpi_values: dict) -> None:
    if not kpi_values["tickets"]:
        st.warning("No bookings match these filters (or they are outside your access scope). "
                   "Try a wider period or fewer filters.")
        st.stop()
