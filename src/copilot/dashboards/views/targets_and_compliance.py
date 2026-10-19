"""Dashboard 3: Targets & Contract Compliance.
Specification: knowledge/dashboards/targets_and_compliance.md"""
from datetime import date

import pandas as pd
import plotly.express as px
import streamlit as st

from copilot import config
from copilot.dashboards import common, queries as q

con, scope = common.get_con(), common.get_scope()

PERIODS = {"2025 (full year)": (date(2025, 1, 1), date(2025, 12, 31)),
           "2026 year to date": (date(2026, 1, 1), config.AS_OF)}

st.title("Targets & Contract Compliance")
st.caption("Did each region reach its revenue target? Does each account respect its contract commitment?")
common.scope_banner(scope)

# ---------------------------------------------------------------- filters
with st.sidebar:
    st.subheader("Regional targets")
quarters = common.multiselect("Quarter", q.target_quarters(con), "tc_quarter")
target_regions = common.multiselect("Sales region (targets)", q.options(con, scope, "sales_region"), "tc_target_region")

with st.sidebar:
    st.subheader("Contract compliance")
    period_label = st.selectbox("Period (booking date)", list(PERIODS), key="tc_period")
regions = common.multiselect("Sales region (contracts)", q.options(con, scope, "sales_region"), "tc_region")
managers = common.multiselect("Account manager", q.options(con, scope, "account_manager", regions),
                              "tc_manager|" + "-".join(regions))
tiers = common.multiselect("Size tier", q.options(con, scope, "size_tier"), "tc_tier")
contract_types = common.multiselect("Contract type", q.contract_type_options(con, scope), "tc_type")

tab_targets, tab_contracts = st.tabs(["Regional targets", "Contract compliance"])

# ================================================================ Section A: regional targets
with tab_targets:
    if not scope.can_view_targets:
        st.info("Regional targets are not available to account managers: they combine the revenue "
                "of accounts you do not manage.")
    else:
        df = q.targets_vs_actual(con, scope, quarters, target_regions)
        if df.empty:
            st.warning("No targets match these filters.")
        else:
            long = df.melt(id_vars=["sales_region", "quarter"], value_vars=["target_eur", "actual_eur"],
                           var_name="series", value_name="eur")
            long["series"] = long["series"].map({"target_eur": "Target", "actual_eur": "Booked net revenue"})
            fig = px.bar(long, x="quarter", y="eur", color="series", barmode="group",
                         facet_col="sales_region", facet_col_wrap=2,
                         color_discrete_map={"Target": "#9aa5b1", "Booked net revenue": "#2f6fdb"},
                         category_orders={"sales_region": config.REGIONS},
                         title="Target vs booked net revenue", labels={"eur": "EUR", "quarter": ""})
            fig.update_yaxes(matches=None)
            fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
            st.plotly_chart(common.style_figure(fig, 280 * (1 + (df["sales_region"].nunique() > 2))),
                            width="stretch")

            def band(value):
                if pd.isna(value):
                    return ""
                if value >= 100:
                    return "background-color: #d6f0e0"
                return "background-color: #fdeccd" if value >= 90 else "background-color: #fbd9d9"

            attainment = df.pivot(index="sales_region", columns="quarter", values="attainment_pct")
            st.subheader("Target attainment")
            st.dataframe(attainment.style.format("{:.1f}%").map(band), width="stretch")
            st.caption("Colour bands: green 100% or more, amber 90% to under 100%, red under 90%.")

            gap = df.pivot(index="sales_region", columns="quarter", values="gap_eur")
            st.subheader("Gap to target (EUR)")
            st.dataframe(gap.style.format("€{:,.0f}").map(
                lambda v: "" if pd.isna(v) else ("color: #067647" if v >= 0 else "color: #b42318")),
                width="stretch")
            st.caption("Booked net revenue minus target. Negative means the target was missed.")

# ================================================================ Section B: contract compliance
with tab_contracts:
    start, end = PERIODS[period_label]
    days = (end - start).days + 1
    st.caption(f"Period: {start} to {end} ({days} days). The yearly commitment is prorated to "
               f"{days}/365 for this period.")
    comp = q.compliance_table(con, scope, start, end, regions, managers, tiers, contract_types)
    if comp.empty:
        st.warning("No accounts match these filters (or they are outside your access scope).")
    else:
        counts = (comp["compliance_status"].value_counts().reindex(config.STATUS_ORDER, fill_value=0)
                  .rename_axis("status").reset_index(name="accounts"))
        fig = px.bar(counts, x="status", y="accounts", color="status", text="accounts",
                     color_discrete_map=common.STATUS_COLORS, category_orders={"status": config.STATUS_ORDER},
                     title="Accounts by contract compliance status", labels={"status": "", "accounts": "Accounts"})
        fig.update_layout(showlegend=False)
        st.plotly_chart(common.style_figure(fig, 320), width="stretch")
        st.caption(common.metric_help("Contract compliance status"))

        st.subheader("Accounts")
        comp["gap_tickets"] = comp["tickets_sold"] - comp["prorated_commitment"]
        table = comp.rename(columns={
            "account_name": "Account", "account_manager": "Account manager", "contract_type": "Contract type",
            "annual_ticket_commitment": "Annual commitment (tickets)",
            "prorated_commitment": "Prorated commitment (tickets)", "tickets_sold": "Tickets sold",
            "attainment_pct": "Commitment attainment (%)", "gap_tickets": "Gap to commitment (tickets)",
            "compliance_status": "Status"})[[
                "Account", "Account manager", "Contract type", "Annual commitment (tickets)",
                "Prorated commitment (tickets)", "Tickets sold", "Commitment attainment (%)",
                "Gap to commitment (tickets)", "Status"]]
        colour = {"On track": "background-color: #d6f0e0", "At risk": "background-color: #fdeccd",
                  "Off track": "background-color: #fbd9d9"}
        styled = table.style.format({
            "Annual commitment (tickets)": "{:,.0f}", "Prorated commitment (tickets)": "{:,.0f}",
            "Tickets sold": "{:,.0f}", "Commitment attainment (%)": "{:.1f}",
            "Gap to commitment (tickets)": "{:+,.0f}"}).map(lambda s: colour.get(s, ""), subset=["Status"])
        st.dataframe(styled, hide_index=True, width="stretch")
        st.caption("Gap to commitment = tickets sold minus prorated commitment. Negative means a shortfall.")
