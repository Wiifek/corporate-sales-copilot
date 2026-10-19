"""Entry point of the dashboards.   Run from the repo root:

    streamlit run src/copilot/dashboards/app.py
"""
from pathlib import Path

import streamlit as st

from copilot.dashboards import common

st.set_page_config(page_title="Corporate Sales Dashboards", page_icon="✈️", layout="wide")

VIEWS = Path(common.__file__).parent / "views"   # from the package, so it also works under test runners
navigation = st.navigation([
    st.Page(VIEWS / "account_performance.py", title="Account Performance", icon="👥", default=True),
    st.Page(VIEWS / "route_cabin_revenue.py", title="Route & Cabin Revenue", icon="🛫"),
    st.Page(VIEWS / "targets_and_compliance.py", title="Targets & Contract Compliance", icon="🎯"),
    #st.Page(VIEWS / "assistant.py", title="Assistant", icon="💬"),
])
common.scope_selector()
navigation.run()
