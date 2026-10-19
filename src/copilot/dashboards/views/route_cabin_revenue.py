"""Dashboard 2: Route & Cabin Revenue.  Specification: knowledge/dashboards/route_cabin_revenue.md"""
import plotly.express as px
import streamlit as st

from copilot import config
from copilot.dashboards import common, queries as q

con, scope = common.get_con(), common.get_scope()

st.title("Route & Cabin Revenue")
st.caption("Where corporate revenue comes from on the network: routes, distance bands and cabins.")
common.scope_banner(scope)

# ---------------------------------------------------------------- filters
with st.sidebar:
    st.subheader("Filters")
date_from, date_to = common.date_range_filter("rc")
market_regions = common.multiselect("Market region (region of the route)", config.REGIONS, "rc_market")
hauls = common.multiselect("Haul", config.HAULS, "rc_haul")
cabins = common.multiselect("Cabin", config.CABINS, "rc_cabin")

f = q.Filters(date_from, date_to, market_regions=market_regions, hauls=hauls, cabins=cabins)

# ---------------------------------------------------------------- KPI row
k = q.kpis(con, f, scope)
common.stop_if_empty(k)

cols = st.columns(5)
common.kpi(cols[0], "Booked net revenue", common.eur_m(k["revenue"]))
common.kpi(cols[1], "Net yield", "n/a" if k["net_yield"] is None else f"{k['net_yield']:.1f} c€/pkm")
common.kpi(cols[2], "Average net fare", common.eur(k["avg_fare"]))
common.kpi(cols[3], "Premium cabin share", common.pct(k["premium_share"]))
common.kpi(cols[4], "Average lead time", "n/a" if k["lead_time"] is None else f"{k['lead_time']:.1f} days")

# ---------------------------------------------------------------- top routes
routes = q.route_table(con, f, scope)
top = routes.head(15).iloc[::-1]
fig = px.bar(top, x="revenue", y="route_id", orientation="h", color="haul",
             category_orders={"haul": config.HAULS},
             title="Top 15 routes by booked net revenue", labels={"revenue": "EUR", "route_id": ""})
st.plotly_chart(common.style_figure(fig, 520), width="stretch")

# ---------------------------------------------------------------- haul x cabin, seasonality
left, right = st.columns(2)
hc = q.haul_cabin(con, f, scope)
fig = px.bar(hc, x="haul", y="revenue", color="cabin", barmode="stack",
             category_orders={"haul": config.HAULS, "cabin": config.CABINS},
             title="Booked net revenue by haul and cabin", labels={"haul": "", "revenue": "EUR"})
left.plotly_chart(common.style_figure(fig), width="stretch")

months = q.by_month(con, f, scope)
fig = px.bar(months, x="month", y="tickets", title="Tickets sold by booking month (seasonality)",
             labels={"month": "", "tickets": "Tickets"})
right.plotly_chart(common.style_figure(fig), width="stretch")

# ---------------------------------------------------------------- yield by haul
yield_df = q.by_dimension(con, f, scope, "haul", metrics=("net_yield",))
fig = px.bar(yield_df, x="haul", y="net_yield", category_orders={"haul": config.HAULS},
             title="Net yield by haul (euro cents per passenger-km)",
             labels={"haul": "", "net_yield": "c€ per pkm"})
st.plotly_chart(common.style_figure(fig, 320), width="stretch")
st.caption("Yield is only comparable within one haul: this chart shows the gap between hauls, "
           "it is not meant to rank routes of different lengths.")

# ---------------------------------------------------------------- route table
st.subheader("Routes")
table = routes.rename(columns={
    "route_id": "Route", "distance_km": "Distance (km)", "haul": "Haul", "tickets": "Tickets sold",
    "revenue": "Booked net revenue (EUR)", "avg_fare": "Average net fare (EUR)",
    "net_yield": "Net yield (c€/pkm)", "premium_share": "Premium cabin share (%)"})
styled = table.style.format({
    "Distance (km)": "{:,.0f}", "Tickets sold": "{:,.0f}", "Booked net revenue (EUR)": "{:,.0f}",
    "Average net fare (EUR)": "{:,.0f}", "Net yield (c€/pkm)": "{:.1f}",
    "Premium cabin share (%)": "{:.1f}"}, na_rep="n/a")
st.dataframe(styled, hide_index=True, width="stretch")
