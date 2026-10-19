"""Dashboard 1: Account Performance.  Specification: knowledge/dashboards/account_performance.md"""
import plotly.express as px
import streamlit as st

from copilot import config
from copilot.dashboards import common, queries as q

con, scope = common.get_con(), common.get_scope()

st.title("Account Performance")
st.caption("How corporate accounts perform: revenue, growth, cancellations and discounts.")
common.scope_banner(scope)

# ---------------------------------------------------------------- filters
with st.sidebar:
    st.subheader("Filters")
date_from, date_to = common.date_range_filter("ap")
regions = common.multiselect("Sales region", q.options(con, scope, "sales_region"), "ap_region")
managers = common.multiselect("Account manager", q.options(con, scope, "account_manager", regions),
                              "ap_manager|" + "-".join(regions))   # reset when the region choice changes
tiers = common.multiselect("Size tier", q.options(con, scope, "size_tier"), "ap_tier")
industries = common.multiselect("Industry", q.options(con, scope, "industry"), "ap_industry")

f = q.Filters(date_from, date_to, sales_regions=regions, managers=managers, tiers=tiers, industries=industries)

# ---------------------------------------------------------------- KPI row
k = q.kpis(con, f, scope)
common.stop_if_empty(k)
growth = q.yoy_growth(con, f, scope)

cols = st.columns(5)
common.kpi(cols[0], "Booked net revenue", common.eur_m(k["revenue"]))
common.kpi(cols[1], "Tickets sold", common.num(k["tickets"]))
common.kpi(cols[2], "Average net fare", common.eur(k["avg_fare"]))
common.kpi(cols[3], "Cancellation rate", common.pct(k["cancel_rate"]))
common.kpi(cols[4], "Year-over-year growth", "n/a" if growth is None else f"{growth:+.1f}%")
if growth is None:
    st.caption("Year-over-year growth needs data from one year earlier: choose a period that "
               "starts on or after 2026-01-01.")

# ---------------------------------------------------------------- monthly trend
trend = q.by_month(con, f, scope)
fig = px.line(trend, x="month", y="revenue", markers=True,
              title="Booked net revenue by booking month", labels={"month": "", "revenue": "EUR"})
st.plotly_chart(common.style_figure(fig), width="stretch")

# ---------------------------------------------------------------- top accounts
accounts = q.account_table(con, f, scope)
top = accounts.head(10).iloc[::-1]
fig = px.bar(top, x="revenue", y="account_name", orientation="h", color="size_tier",
             category_orders={"size_tier": config.TIERS},
             title="Top 10 accounts by booked net revenue", labels={"revenue": "EUR", "account_name": ""})
st.plotly_chart(common.style_figure(fig, 420), width="stretch")

# ---------------------------------------------------------------- split by tier and industry
left, right = st.columns(2)
tier_df = q.by_dimension(con, f, scope, "size_tier")
fig = px.bar(tier_df, x="size_tier", y="revenue", category_orders={"size_tier": config.TIERS},
             title="Booked net revenue by size tier", labels={"size_tier": "", "revenue": "EUR"})
left.plotly_chart(common.style_figure(fig), width="stretch")
industry_df = q.by_dimension(con, f, scope, "industry")
fig = px.bar(industry_df, x="revenue", y="industry", orientation="h",
             title="Booked net revenue by industry", labels={"industry": "", "revenue": "EUR"})
fig.update_yaxes(autorange="reversed")
right.plotly_chart(common.style_figure(fig), width="stretch")

# ---------------------------------------------------------------- account table
st.subheader("Accounts")
HIGH_CANCELLATION = 15.0
table = accounts.rename(columns={
    "account_name": "Account", "size_tier": "Size tier", "account_manager": "Account manager",
    "revenue": "Booked net revenue (EUR)", "tickets": "Tickets sold", "avg_fare": "Average net fare (EUR)",
    "cancel_rate": "Cancellation rate (%)", "discount_rate": "Effective discount rate (%)",
    "yoy_growth_pct": "Year-over-year growth (%)"}).drop(columns="account_id")


def highlight_cancellations(row):
    bad = row["Cancellation rate (%)"] > HIGH_CANCELLATION
    return ["background-color: #fde2e2" if bad else "" for _ in row]


styled = table.style.format({
    "Booked net revenue (EUR)": "{:,.0f}", "Tickets sold": "{:,.0f}", "Average net fare (EUR)": "{:,.0f}",
    "Cancellation rate (%)": "{:.1f}", "Effective discount rate (%)": "{:.1f}",
    "Year-over-year growth (%)": "{:+.1f}"}, na_rep="n/a").apply(highlight_cancellations, axis=1)
st.dataframe(styled, hide_index=True, width="stretch")
st.caption(f"Rows with a cancellation rate above {HIGH_CANCELLATION:.0f}% are highlighted.")
