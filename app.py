import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="DFR Cost-Benefit Dashboard V 2.1", layout="wide")
st.title("Drone-as-First-Responder (DFR) — Cost / Benefit Dashboard V 2.1")

st.markdown(
    """
    <style>
    /* Applies only when printing to PDF */
    @media print {

        /* Shrink ALL images (Streamlit renders plots as <img>) */
        img {
            max-width: 60% !important;
            height: auto !important;
        }

        /* Reduce margins so PDF fits more content */
        body {
            margin: 0;
            padding: 0;
            zoom: 0.85; /* shrink everything slightly */
        }

        /* Force header text to be smaller on PDF */
        h1, h2, h3, h4 {
            font-size: 80% !important;
        }

        /* Fix overflow issues */
        .element-container, .stPlotlyChart, .stImage {
            page-break-inside: avoid;
        }
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ------------------------------------------------------------
# CAPITAL COSTS (One-Time)
# ------------------------------------------------------------
st.sidebar.header("Capital Costs (One-Time)")

# kept (as requested)
equipment_cost = st.sidebar.number_input("Equipment (Radar) (one-time $)", value=15000.0, step=1000.0)
infra_cost = st.sidebar.number_input("Infrastructure (one-time $)", value=20000.0, step=1000.0)

# keep number of drones input (doesn't affect capital anymore)
num_drones = st.sidebar.number_input("Number of drones", value=2, min_value=0, step=1)

# updated capital calculation (as requested)
capital_costs = equipment_cost + infra_cost

# ------------------------------------------------------------
# ANNUAL TRAINING
# ------------------------------------------------------------
st.sidebar.header("Annual Training")

# toggle: either annual budget OR detailed breakdown (as requested)
use_training_budget = st.sidebar.checkbox("Use Annual Training Budget (instead of breakdown)", value=True)

if use_training_budget:
    annual_training_cost = st.sidebar.number_input("Training budget ($/year)", value=2560.0, step=100.0)
else:
    train_hours = st.sidebar.number_input("Training hours per session", value=4.0, step=0.5)
    train_interval = st.sidebar.slider("Training intervals per year", 1, 12, 4)
    train_people = st.sidebar.number_input("Number of personnel trained", value=4, step=1, min_value=0)
    train_hourly_rate = st.sidebar.number_input("Training hourly labor rate ($)", value=40.0, step=1.0)
    annual_training_cost = train_hours * train_interval * train_people * train_hourly_rate

# ------------------------------------------------------------
# ANNUAL OPERATING COSTS
# ------------------------------------------------------------
st.sidebar.header("Operating Costs (Annual)")

# --- Contract / Subscriptions (always on; no option box) ---
st.sidebar.subheader("Contract / Subscriptions")

contract_fee_annual = st.sidebar.number_input("Contract Fee ($/year)", value=60000.0, step=1000.0)
software_subscriptions_annual = st.sidebar.number_input("Software Subscriptions ($/year)", value=8000.0, step=500.0)

# Labor per hour
st.sidebar.subheader("Labor")
labor_rate = st.sidebar.number_input("Labor cost ($/hour/person)", value=25.0, step=1.0)
labor_hours_per_day = st.sidebar.number_input("Hours per day per person", value=2.0, step=0.5)
labor_people = st.sidebar.number_input("People per shift", value=2, step=1, min_value=0)
num_shifts = st.sidebar.slider("Number of shifts per day", 1, 3, 1)
labor_days = st.sidebar.number_input("Operational days per year", value=365, min_value=1)
annual_labor = labor_rate * labor_hours_per_day * labor_people * num_shifts * labor_days

# Maintenance
st.sidebar.subheader("Maintenance")
# Removed Regular Maintenance ($/year) as requested
irregular_cost = st.sidebar.number_input("Unexpected failure cost ($)", value=2000.0, step=200.0)
irregular_events = st.sidebar.slider("Expected failures per year", 0, 10, 1)
irregular_annual = irregular_cost * irregular_events

# Communications & permits
st.sidebar.subheader("Communications & Permits")

# Communication ($/month) -> per year + dropdown (as requested)
comm_type = st.sidebar.selectbox("Communication Type", ["Cellular", "Other (user input)"])
annual_comm = st.sidebar.number_input("Communication cost ($/year)", value=2400.0, step=100.0)

permits_cost_annual = st.sidebar.number_input("Waivers & Permits (annual $)", value=3000.0, step=200.0)

annual_op_cost = (
    annual_labor +
    contract_fee_annual +
    software_subscriptions_annual +
    irregular_annual +
    annual_training_cost +
    annual_comm +
    permits_cost_annual
)

# ------------------------------------------------------------
# ANNUAL BENEFITS
# ------------------------------------------------------------
st.sidebar.header("Benefits (Annual)")

minutes_saved = st.sidebar.number_input("Response time improvement ", value=3.0, step=0.5)
value_per_min = st.sidebar.number_input("Value of time ($/min)", value=20.0)
calls_per_year = st.sidebar.number_input("Calls handled by drones per year", value=2000)
avoided_cost_per_call = st.sidebar.number_input("Avoided officer response cost ($/call)", value=50.0)

# kept
ben_labor = st.sidebar.number_input("Labor Savings ($/yr)", value=0.0)

# Safety Improvements: numbers only (no $/event)
safety_events_per_year = st.sidebar.number_input("Safety Improvements (count/yr)", value=0, step=1, min_value=0)
ben_safety = float(safety_events_per_year)  # numbers only

ben_revenue = st.sidebar.number_input("Revenue Increases ($/yr)", value=0.0)

# Reduced Dispatch Units: numbers only
dispatch_units_reduced_per_year = st.sidebar.number_input("Reduced Dispatch Units (count/yr)", value=0, step=1, min_value=0)
ben_dispatch = float(dispatch_units_reduced_per_year)  # numbers only

response_time_savings = minutes_saved * value_per_min * calls_per_year
cost_avoidance = avoided_cost_per_call * calls_per_year

# updated annual benefits (includes numeric-only safety + dispatch as requested)
annual_benefits = response_time_savings + cost_avoidance + ben_labor + ben_safety + ben_revenue + ben_dispatch

# ------------------------------------------------------------
# ANALYSIS SETTINGS
# ------------------------------------------------------------
st.sidebar.header("Analysis Settings")
years = st.sidebar.slider("Analysis Horizon (Years)", 1, 10, 5)
discount_rate = st.sidebar.slider("Discount Rate (%)", 0.0, 20.0, 5.0)
st.sidebar.header("Graph Settings")

# ------------------------------------------------------------
# FINANCIAL CALCULATIONS
# ------------------------------------------------------------
annual_net_benefit = annual_benefits - annual_op_cost
roi = (annual_net_benefit / annual_op_cost * 100) if annual_op_cost > 0 else np.nan
bcr = (annual_benefits / annual_op_cost) if annual_op_cost > 0 else np.nan
payback_period = (capital_costs / annual_net_benefit) if annual_net_benefit > 0 else np.inf

years_idx = np.arange(1, years + 1)
discount_factors = 1 / ((1 + discount_rate / 100) ** (years_idx - 1))

cashflows = []
cum = -capital_costs
for y, d in zip(years_idx, discount_factors):
    net = annual_net_benefit
    discounted = net * d
    cum += net
    cashflows.append(
        {
            "Year": y,
            "Benefits": annual_benefits,
            "Costs": annual_op_cost,
            "Net Benefit": net,
            "Discount Factor": d,
            "Discounted Net": discounted,
            "Cumulative Net (nominal)": cum,
        }
    )
df = pd.DataFrame(cashflows)

# ------------------------------------------------------------
# TOP DASHBOARD — HIGH LEVEL NUMBERS
# ------------------------------------------------------------
st.header("Summary")
col1, col2, col3 = st.columns(3)
col1.metric("Fixed / Capital Costs", f"${capital_costs:,.0f}")
col2.metric("Annual Operating Cost", f"${annual_op_cost:,.0f}")
col3.metric("Annual Benefits", f"${annual_benefits:,.0f}")

# ------------------------------------------------------------
# KEY METRICS — ROI / BCR / Payback
# ------------------------------------------------------------
st.header("Key Metrics")
col1, col2, col3 = st.columns(3)
col1.metric("ROI (annual)", f"{roi:.1f}%")
col2.metric("Benefit-Cost Ratio", f"{bcr:.2f}")
col3.metric("Payback Period (years)", f"{payback_period:.2f}" if np.isfinite(payback_period) else "No payback")

# ------------------------------------------------------------
# THIN BAR PLOTS FOR METRICS
# ------------------------------------------------------------
st.subheader("Metrics Visualization")
fig, axs = plt.subplots(1, 3, figsize=(8, 2))

bar_width = 0.2

axs[0].bar([0], [roi], width=bar_width, color="#1f77b4")
axs[0].set_title("ROI (%)")
axs[0].set_xticks([])
axs[0].grid(True, axis="y")

axs[1].bar([0], [bcr], width=bar_width, color="#2ca02c")
axs[1].set_title("BCR")
axs[1].set_xticks([])
axs[1].grid(True, axis="y")

pb_val = payback_period if np.isfinite(payback_period) else 0
axs[2].bar([0], [pb_val], width=bar_width, color="#ff7f0e")
axs[2].set_title("Payback Period (yrs)")
axs[2].set_xticks([])
axs[2].grid(True, axis="y")

plt.tight_layout()
st.pyplot(fig)

# ------------------------------------------------------------
# CASHFLOW TABLE
# ------------------------------------------------------------
st.header("Year-by-Year Cash Flow")
st.dataframe(df)

# ------------------------------------------------------------
# ORIGINAL PLOTS
# ------------------------------------------------------------
st.header("Financial Charts")
chart_width = st.sidebar.slider("Chart Width", 4, 12, 6)
chart_height = st.sidebar.slider("Chart Height", 2, 8, 3)

# 1) Annual Benefits vs Costs
fig1, ax1 = plt.subplots(figsize=(chart_width, chart_height))
ax1.plot(df["Year"], df["Benefits"], marker="o", label="Benefits")
ax1.plot(df["Year"], df["Costs"], marker="o", label="Costs")
ax1.set_title("Annual Benefits vs Costs")
ax1.set_xlabel("Year")
ax1.set_ylabel("$")
ax1.legend()
ax1.grid(True)
st.pyplot(fig1)

# 2) Cumulative Nominal Net Benefit
fig2, ax2 = plt.subplots(figsize=(chart_width, chart_height))
ax2.plot([0] + df["Year"].tolist(), [-capital_costs] + df["Cumulative Net (nominal)"].tolist(), marker="o")
ax2.axhline(0, linestyle="--", color="gray")
ax2.set_title("Cumulative Nominal Net Benefit")
ax2.set_xlabel("Year")
ax2.set_ylabel("$")
ax2.grid(True)
st.pyplot(fig2)

# 3) Discounted Cumulative Net Benefit
fig3, ax3 = plt.subplots(figsize=(chart_width, chart_height))
ax3.plot(df["Year"], df["Discounted Net"].cumsum(), marker="o")
ax3.set_title("Discounted Cumulative Net Benefit")
ax3.set_xlabel("Year")
ax3.set_ylabel("$")
ax3.grid(True)
st.pyplot(fig3)

# ------------------------------------------------------------
# BREAK-EVEN SLIDER
# ------------------------------------------------------------
st.header("Break-Even Visualization")
break_year = st.slider("Highlight Year", 0, years, 0)
fig_be, ax_be = plt.subplots(figsize=(chart_width, chart_height))
ax_be.plot([0] + df["Year"].tolist(), [-capital_costs] + df["Cumulative Net (nominal)"].tolist(), marker="o")
ax_be.axhline(0, linestyle="--", color="gray")
ax_be.axvline(break_year, linestyle="--", color="red", label=f"Selected Year {break_year}")
ax_be.set_xlabel("Year")
ax_be.set_ylabel("Cumulative Net ($)")
ax_be.set_title("Break-Even Analysis")
ax_be.grid(True)
ax_be.legend()
st.pyplot(fig_be)

# ------------------------------------------------------------
# EXPORT CSV
# ------------------------------------------------------------
csv = df.to_csv(index=False)

# ------------------------------------------------------------
# EXPORT OPTIONS (PNG + CSV + PDF)
# ------------------------------------------------------------
st.header("Export Options")

st.download_button(
    "Download Cashflow CSV",
    data=csv,
    file_name="cashflow.csv",
    mime="text/csv",
)

st.subheader("Download Charts (PNG)")

from io import BytesIO

buf1 = BytesIO()
fig1.savefig(buf1, format="png", dpi=300, bbox_inches="tight")
buf1.seek(0)
st.download_button(
    "Download Annual Benefits vs Costs (PNG)",
    data=buf1,
    file_name="annual_benefits_vs_costs.png",
    mime="image/png",
)

buf2 = BytesIO()
fig2.savefig(buf2, format="png", dpi=300, bbox_inches="tight")
buf2.seek(0)
st.download_button(
    "Download Cumulative Net Benefit (PNG)",
    data=buf2,
    file_name="cumulative_net_benefit.png",
    mime="image/png",
)

buf3 = BytesIO()
fig3.savefig(buf3, format="png", dpi=300, bbox_inches="tight")
buf3.seek(0)
st.download_button(
    "Download Discounted Net Benefit (PNG)",
    data=buf3,
    file_name="discounted_net_benefit.png",
    mime="image/png",
)

st.subheader("Save Full Dashboard as PDF")

import streamlit.components.v1 as components

components.html(
    """
    <button onclick="window.top.print()"
            style="font-size:16px;padding:8px 14px;border-radius:6px;cursor:pointer;">
        Print / Save as PDF
    </button>
    """,
    height=80,
)
