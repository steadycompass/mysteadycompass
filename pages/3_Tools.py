"""
TOOLS page - The Steady Compass.
Portfolio Simulator, Real vs Nominal, DRIP / Dividend Reinvestment, Magic of Compounding, Cost of Frictions.
"""

import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from components.nav import inject_nav_css, render_nav, render_footer, maybe_redirect_from_query

try:
    import plotly.graph_objects as go
    import plotly.express as px
    _plotly_ok = True
except ImportError:
    _plotly_ok = False

import pandas as pd
import numpy as np
try:
    import yfinance as yf
    _yf_ok = True
except ImportError:
    _yf_ok = False

st.set_page_config(page_title="The Steady Compass", page_icon="🧭", layout="wide", initial_sidebar_state="auto")
inject_nav_css()
maybe_redirect_from_query("TOOLS")
render_nav("TOOLS")

# Sidebar: 3 tools
with st.sidebar:
    st.markdown(
        "<style>"
        ".tools-sidenav { margin-top: 8rem; padding: 0.5rem 0; border-left: 3px solid #5a6378; padding-left: 0.75rem; margin-bottom: 1rem; } "
        ".tools-sidenav-title { font-size: 0.75rem; font-weight: 600; color: #64748b; letter-spacing: 0.05em; margin-bottom: 0.5rem; border-bottom: 1px solid #94a3b8; padding-bottom: 0.5rem; } "
        ".tools-sidenav a { display: block; padding: 0.35rem 0; font-size: 0.85rem; color: #475569; text-decoration: none; border-radius: 4px; } "
        ".tools-sidenav a:hover { color: #0ea5e9; background: #f1f5f9; padding-left: 0.25rem; } "
        "@media (max-width: 640px) { .tools-sidenav { margin-top: 5rem; } .tools-sidenav a { min-height: 44px; display: flex; align-items: center; } } "
        "</style>"
        '<div class="tools-sidenav">'
        '<div class="tools-sidenav-title">TOOLS</div>'
        '<a href="#portfolio-simulator">Portfolio Simulator</a>'
        '<a href="#real-nominal">Real vs Nominal Return</a>'
        '<a href="#drip">DRIP / Dividend Reinvestment</a>'
        '<a href="#compounding">Magic of Compounding</a>'
        '<a href="#cost-of-frictions">Cost of Frictions</a>'
        "</div>",
        unsafe_allow_html=True,
    )

st.markdown(
    '<div class="content-breadcrumb" aria-label="You are here">'
    '<a href="?page=HOME">Home</a> &nbsp;&gt;&nbsp; Tools</div>',
    unsafe_allow_html=True,
)
st.markdown(
    "<style>"
    "#portfolio-simulator, #real-nominal, #drip, #compounding, #cost-of-frictions { scroll-margin-top: 8rem; } "
    "</style>",
    unsafe_allow_html=True,
)

# When opened via Market link (?page=TOOLS&anchor=real-nominal), scroll to Real vs Nominal
if st.query_params.get("anchor") == "real-nominal":
    try:
        import streamlit.components.v1 as components
        components.html(
            """
            <script>
            (function() {
              var doc = window.parent.document;
              var el = doc.getElementById('real-nominal');
              if (el) {
                setTimeout(function() {
                  el.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }, 350);
              }
            })();
            </script>
            """,
            height=0,
        )
    except Exception:
        pass

# -----------------------------------------------------------------------------
# 1. Portfolio Simulator (Asset allocation backtest)
# -----------------------------------------------------------------------------
st.markdown(
    '<div id="portfolio-simulator"><div class="section-heading">Portfolio Simulator</div></div>',
    unsafe_allow_html=True,
)
st.markdown("Find the **stock vs bond** mix that fits you. See how adding bonds shrinks the worst drawdown.")
st.caption("Uses S&P 500 (^GSPC) for stocks and AGG (aggregate bonds) for 20-year history. Rebalanced monthly.")

age = st.slider("Age", 20, 100, 50, 1, key="ps_age")
bogle_stock = 100 - age
bogle_bond = age

# Visual bar: Bogle-recommended allocation (stocks = teal, bonds = blue); right below Age slider
st.markdown(
    f'<div style="margin:0.25rem 0 0.5rem 0; font-size:0.8rem; color:#64748b;">Recommended by age (Bogle)</div>'
    f'<div style="display:flex; height:28px; border-radius:6px; overflow:hidden; border:1px solid #e2e8f0;">'
    f'<div style="width:{bogle_stock}%; background:#0d9488; display:flex; align-items:center; justify-content:center; color:white; font-weight:600; font-size:0.8rem;">Stocks {bogle_stock}%</div>'
    f'<div style="width:{bogle_bond}%; background:#2563eb; display:flex; align-items:center; justify-content:center; color:white; font-weight:600; font-size:0.8rem;">Bonds {bogle_bond}%</div>'
    f'</div>',
    unsafe_allow_html=True,
)

st.success(
    "💡 **Bogle's Rule of Thumb**\n\n"
    "John Bogle advised: **'Hold bonds equal to your age.'**\n\n"
    f"For your age, the suggested portfolio is **{bogle_stock}% stocks / {bogle_bond}% bonds**. "
    "Use the slider below to match this or adjust to your preference."
)
st.caption("Some use a higher stock share as lifespans lengthen: **110 − age** or **120 − age** for the stock portion.")
st.markdown('<div style="margin-bottom: 1.25rem;"></div>', unsafe_allow_html=True)

@st.cache_data(ttl=86400)
def _fetch_stock_bond_20y():
    """S&P 500 (^GSPC) and bonds (AGG) daily for ~20y. Returns (dates, stock_ret, bond_ret) or None."""
    if not _yf_ok:
        return None
    try:
        gspc = yf.Ticker("^GSPC").history(period="20y", interval="1d", auto_adjust=True)
        agg = yf.Ticker("AGG").history(period="20y", interval="1d", auto_adjust=True)
        if gspc is None or gspc.empty or agg is None or agg.empty:
            return None
        gspc = gspc["Close"].dropna()
        agg = agg["Close"].dropna()
        common = gspc.index.intersection(agg.index).sort_values()
        if len(common) < 252:
            return None
        gspc = gspc.reindex(common).ffill().bfill()
        agg = agg.reindex(common).ffill().bfill()
        stock_ret = gspc.pct_change().dropna()
        bond_ret = agg.pct_change().dropna()
        common = stock_ret.index.intersection(bond_ret.index).sort_values()
        return common, stock_ret.reindex(common).fillna(0), bond_ret.reindex(common).fillna(0)
    except Exception:
        return None

stock_pct = st.slider("Stocks (S&P 500) %", 0, 100, bogle_stock, 5, key="ps_stock")
bond_pct = 100 - stock_pct
st.caption(f"**{stock_pct}% stocks / {bond_pct}% bonds** (rebalanced monthly)")
# Visual bar: stock (teal) + bond (blue); bond updates automatically when stock moves
st.markdown(
    f'<div style="margin:0.25rem 0 0.5rem 0; font-size:0.8rem; color:#64748b;">Allocation</div>'
    f'<div style="display:flex; height:28px; border-radius:6px; overflow:hidden; border:1px solid #e2e8f0;">'
    f'<div style="width:{stock_pct}%; background:#0d9488; display:flex; align-items:center; justify-content:center; color:white; font-weight:600; font-size:0.8rem;">Stocks {stock_pct}%</div>'
    f'<div style="width:{bond_pct}%; background:#2563eb; display:flex; align-items:center; justify-content:center; color:white; font-weight:600; font-size:0.8rem;">Bonds {bond_pct}%</div>'
    f'</div>',
    unsafe_allow_html=True,
)

data_20y = _fetch_stock_bond_20y()
if data_20y is not None and _plotly_ok:
    dates, sr, br = data_20y
    w_s, w_b = stock_pct / 100.0, bond_pct / 100.0
    # Monthly rebalance: compound within month, then apply weights at month end
    stock_m = (1 + sr).resample("ME").prod() - 1
    bond_m = (1 + br).resample("ME").prod() - 1
    common_m = stock_m.index.intersection(bond_m.index).sort_values()
    stock_m = stock_m.reindex(common_m).fillna(0)
    bond_m = bond_m.reindex(common_m).fillna(0)
    port_ret_m = w_s * stock_m + w_b * bond_m
    port_ret_m = port_ret_m.dropna()
    if len(port_ret_m) < 2:
        st.warning("Not enough data for chart.")
    else:
        wealth = 100 * (1 + port_ret_m).cumprod()
        wealth = wealth / wealth.iloc[0] * 100
        running_max = wealth.cummax()
        drawdown_pct = (wealth - running_max) / running_max * 100
        mdd = float(drawdown_pct.min())
        total_return_pct = (float(wealth.iloc[-1]) / 100 - 1) * 100

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Final wealth (start=100)", f"{wealth.iloc[-1]:.1f}", f"{total_return_pct:.1f}% total return")
        with col2:
            st.metric("Max drawdown (MDD)", f"{mdd:.1f}%", "Peak to trough")
        with col3:
            st.caption("Lower stock % → smaller MDD, slightly lower return.")

        # S&P 500 (100% stocks) monthly for comparison — same index as wealth
        sp500_wealth = 100 * (1 + stock_m.reindex(wealth.index).ffill().bfill()).cumprod()
        sp500_wealth = sp500_wealth.dropna()
        if len(sp500_wealth) > 0 and sp500_wealth.iloc[0] > 0:
            sp500_wealth = sp500_wealth / float(sp500_wealth.iloc[0]) * 100
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=wealth.index, y=wealth.values, mode="lines", name=f"Portfolio ({stock_pct}% stocks)", line=dict(color="#0ea5e9", width=2)))
        fig.add_trace(go.Scatter(x=sp500_wealth.index, y=sp500_wealth.values, mode="lines", name="S&P 500 (100% stocks)", line=dict(color="#ea580c", width=2)))
        fig.update_layout(
            title="Growth of $100 (rebalanced monthly)",
            xaxis_title="", yaxis_title="Value",
            margin=dict(t=50, b=70), height=380, template="plotly_white",
            showlegend=True, legend=dict(orientation="h", yanchor="top", y=-0.12, xanchor="center", x=0.5),
            dragmode=False,
        )
        fig.update_xaxes(fixedrange=True)
        fig.update_yaxes(fixedrange=True)
        st.plotly_chart(fig, use_container_width=True, config=dict(displayModeBar=False, scrollZoom=False))

        # Drawdown chart: current portfolio vs S&P 500 (100% stocks) — bonds soften the fall
        # Plot drawdown as negative (0 at top, down into negative %); classic upside-down drawdown
        sp500_dd = (sp500_wealth - sp500_wealth.cummax()) / sp500_wealth.cummax() * 100
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=sp500_dd.index, y=sp500_dd.values, fill="tozeroy", line=dict(color="#ea580c", width=1.5), fillcolor="rgba(234,88,12,0.25)", name="S&P 500 (100% stocks)"))
        fig2.add_trace(go.Scatter(x=drawdown_pct.index, y=drawdown_pct.values, fill="tozeroy", line=dict(color="#0369a1", width=2.5), fillcolor="rgba(3,105,161,0.35)", name=f"Portfolio ({stock_pct}% stocks)"))
        fig2.update_layout(
            title="Drawdown from peak — adding bonds softens the fall",
            xaxis_title="", yaxis_title="Drawdown %",
            margin=dict(t=50, b=70), height=300, template="plotly_white",
            yaxis=dict(range=[-55, 0], tickvals=[0, -10, -20, -30, -40, -50], tickformat=".0f"), showlegend=True, legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5),
            dragmode=False,
        )
        fig2.update_xaxes(fixedrange=True)
        fig2.update_yaxes(fixedrange=True)
        st.plotly_chart(fig2, use_container_width=True, config=dict(displayModeBar=False, scrollZoom=False))

        # MDD by allocation: show how bonds improve (reduce) MDD
        mdd_by_stock = []
        for pct in range(0, 101, 10):
            ws, wb = pct / 100.0, (100 - pct) / 100.0
            pr = ws * stock_m + wb * bond_m
            pr = pr.dropna()
            if len(pr) < 2:
                mdd_by_stock.append((pct, 0))
                continue
            w = 100 * (1 + pr).cumprod()
            w = w / w.iloc[0]
            dd = (w - w.cummax()) / w.cummax() * 100
            mdd_by_stock.append((pct, float(dd.min())))
        mdd_df = pd.DataFrame(mdd_by_stock, columns=["Stocks %", "MDD %"])
        # Plot MDD as negative %; y-axis 0 at top, -50 at bottom, with minus on labels
        fig3 = go.Figure()
        fig3.add_trace(go.Scatter(x=mdd_df["Stocks %"], y=mdd_df["MDD %"], mode="lines+markers", name="MDD", line=dict(color="#5a6378", width=2), marker=dict(size=8)))
        fig3.add_trace(go.Scatter(x=[stock_pct], y=[mdd], mode="markers", name=f"Your mix ({stock_pct}%)", marker=dict(size=14, color="#dc2626", symbol="diamond", line=dict(width=2, color="white"))))
        fig3.update_layout(
            title="Max drawdown by stock allocation — more bonds, gentler drawdowns",
            xaxis_title="Stocks %", yaxis_title="MDD %",
            margin=dict(t=50, b=95), height=320, template="plotly_white",
            xaxis=dict(dtick=10), yaxis=dict(range=[-55, 0], tickvals=[0, -10, -20, -30, -40, -50], tickformat=".0f"),
            showlegend=True, legend=dict(orientation="h", yanchor="top", y=-0.28, xanchor="center", x=0.5),
            dragmode=False,
        )
        fig3.update_xaxes(fixedrange=True)
        fig3.update_yaxes(fixedrange=True)
        st.plotly_chart(fig3, use_container_width=True, config=dict(displayModeBar=False, scrollZoom=False))

        st.markdown("---")
        st.markdown("**Bogle's Wisdom: Why add bonds even if it lowers return?**")
        st.markdown(
            "*If stocks are the powerful 'engine' that drives the boat forward, bonds are the 'ballast' "
            "that keeps the boat from capsizing in a storm.*"
        )
        st.markdown("**It's psychology, not math.**")
        st.markdown(
            "Backtesting shows that the highest return has always come from 100% stocks. But the human brain—not a computer—"
            "cannot calmly endure the pain of watching half your wealth vanish (−50%) as in 2008. Bonds are the strongest "
            "psychological safeguard that keeps you from the fatal mistake of pressing the *sell* button in panic during a crash."
        )
        st.markdown("**Insurance premium for sleeping well at night.**")
        st.markdown(
            "Mixing in bonds may mean slightly lower returns than 100% stocks in a bull market. But this is the small, "
            "reasonable premium you pay to *sleep well at night*—without the fear of a market crash every evening."
        )
        st.markdown("**The magic bullet that turns crisis into opportunity.**")
        st.markdown(
            "When the stock market collapses, investors tremble with fear. But the investor who holds bonds can smile. "
            "Those bonds become your *rebalancing bullet*—you can sell some of the bonds that held their value and buy "
            "quality stocks that the market has thrown away at fire-sale prices."
        )
        st.markdown(
            "Look at the **Max Drawdown (MDD)** number in the simulator above. First know how much pain you can tolerate, "
            "then hold only as much in stocks as you can endure with a smile. Investment success depends not on maximizing return, "
            "but on **staying the course** through any crisis."
        )
else:
    if not _yf_ok:
        st.info("Install yfinance and plotly to use the Portfolio Simulator.")
    else:
        st.info("Could not load 20-year data. Try again later.")

st.divider()

# -----------------------------------------------------------------------------
# 2. Real vs Nominal Return (anchor for Market page link)
# -----------------------------------------------------------------------------
st.markdown(
    '<div id="real-nominal"><div class="section-heading">Real vs Nominal Return</div></div>',
    unsafe_allow_html=True,
)
st.markdown("Compare **nominal** returns (e.g. from the Market or Performance tables) with **inflation-adjusted (real)** returns. Over the long run, real returns matter more for purchasing power.")
st.caption("Use the Portfolio Simulator and compounding tools above and below with an inflation assumption to approximate real returns.")
st.divider()

# -----------------------------------------------------------------------------
# 3. DRIP / Dividend Reinvestment
# -----------------------------------------------------------------------------
st.markdown(
    '<div id="drip"><div class="section-heading">DRIP / Dividend Reinvestment</div></div>',
    unsafe_allow_html=True,
)
st.markdown(
    "**DRIP** (Dividend Reinvestment Plan) means automatically reinvesting dividends to buy more shares. Over time, that *snowball* can add a lot to your wealth. See how much difference reinvesting makes compared to taking dividends as cash."
)
st.caption("Typical broad-market index funds yield around 1–2% per year. Reinvesting grows share count and compounds returns.")

drip_initial = st.number_input("Initial investment ($)", min_value=1000, value=10000, step=1000, key="drip_initial")
drip_yield_pct = st.slider("Dividend yield (% per year)", 0.5, 5.0, 1.5, 0.1, key="drip_yield") / 100.0
drip_appreciation_pct = st.slider("Annual price appreciation (% per year)", -2.0, 15.0, 6.0, 0.5, key="drip_appr") / 100.0
drip_years = st.slider("Years", 1, 50, 20, 1, key="drip_years")

# With DRIP: each year end we have shares; dividend paid on those shares buys more at current price; price grows
# Simplified: start with value V0; each year V grows by (1 + appreciation), then we add dividend = V * yield, which is reinvested so next year we have V*(1+appr) + V*(1+appr)*yield = V*(1+appr)*(1+yield). So total return per year = (1+appr)*(1+yield) - 1.
# Without DRIP: V grows only by (1+appreciation) each year; we "take out" dividend as cash so it doesn't compound.
def drip_simulate(initial, yield_pct, appreciation_pct, years, reinvest):
    value = float(initial)
    for _ in range(years):
        value = value * (1.0 + appreciation_pct)
        if reinvest:
            value = value * (1.0 + yield_pct)  # dividend reinvested at same yield
        # else: dividend taken as cash, not added to value
    return value

val_with_drip = drip_simulate(drip_initial, drip_yield_pct, drip_appreciation_pct, drip_years, reinvest=True)
val_without_drip = drip_simulate(drip_initial, drip_yield_pct, drip_appreciation_pct, drip_years, reinvest=False)
diff = val_with_drip - val_without_drip
diff_pct = (diff / val_without_drip * 100.0) if val_without_drip else 0

col_d1, col_d2 = st.columns(2)
with col_d1:
    st.metric("With DRIP (reinvest dividends)", f"${val_with_drip:,.0f}", f"After {drip_years} years")
with col_d2:
    st.metric("Without DRIP (take cash)", f"${val_without_drip:,.0f}", f"After {drip_years} years")

st.info(f"**Reinvesting dividends** adds **${diff:,.0f}** ({diff_pct:.1f}% more) over {drip_years} years in this scenario. Small yield, big effect over time.")

# Optional: yearly breakdown for chart (with DRIP vs without)
if _plotly_ok:
    years_arr = np.arange(drip_years + 1)
    with_drip_curve = [drip_initial]
    without_curve = [drip_initial]
    v_w, v_wo = float(drip_initial), float(drip_initial)
    for _ in range(drip_years):
        v_w = v_w * (1.0 + drip_appreciation_pct) * (1.0 + drip_yield_pct)
        v_wo = v_wo * (1.0 + drip_appreciation_pct)
        with_drip_curve.append(v_w)
        without_curve.append(v_wo)
    fig_drip = go.Figure()
    fig_drip.add_trace(go.Scatter(x=years_arr, y=with_drip_curve, mode="lines+markers", name="With DRIP", line=dict(color="#0d9488", width=2), marker=dict(size=4)))
    fig_drip.add_trace(go.Scatter(x=years_arr, y=without_curve, mode="lines+markers", name="Without DRIP (cash)", line=dict(color="#64748b", width=2), marker=dict(size=4)))
    fig_drip.update_layout(
        title="Value over time: reinvesting vs taking dividends as cash",
        xaxis_title="Years",
        yaxis_title="Portfolio value ($)",
        margin=dict(t=50, b=60),
        height=320,
        template="plotly_white",
        legend=dict(orientation="h", yanchor="top", y=1.02, xanchor="center", x=0.5),
        yaxis_tickformat="$,.0f",
        dragmode=False,
    )
    fig_drip.update_xaxes(fixedrange=True)
    fig_drip.update_yaxes(fixedrange=True)
    st.plotly_chart(fig_drip, use_container_width=True, config=dict(displayModeBar=False, scrollZoom=False))

st.markdown("**Compass tip:** Many index ETFs (e.g. VOO, VTI) let you turn on automatic dividend reinvestment in your broker account. Set it once and stay the course.")
st.divider()

# -----------------------------------------------------------------------------
# 4. Magic of Compounding
# -----------------------------------------------------------------------------
st.markdown(
    '<div id="compounding"><div class="section-heading">Magic of Compounding</div></div>',
    unsafe_allow_html=True,
)
st.markdown("See how **time** and the market grow your money. Blue = what you put in; green = what compounding adds.")

initial = st.number_input("Initial investment ($)", min_value=0, value=10000, step=1000, key="comp_initial")
monthly = st.number_input("Monthly contribution ($)", min_value=0, value=500, step=50, key="comp_monthly")
rate = st.slider("Expected annual return (%)", 1.0, 15.0, 8.0, 0.5, key="comp_rate") / 100.0
years = st.slider("Years", 1, 50, 30, 1, key="comp_years")

months = years * 12
r_month = rate / 12
principal_series = []
value_series = []
v = float(initial)
p_cum = float(initial)
for m in range(months + 1):
    principal_series.append(p_cum)
    value_series.append(v)
    if m < months:
        p_cum += monthly
        v = v * (1 + r_month) + monthly

principal_series = np.array(principal_series)
value_series = np.array(value_series)

if _plotly_ok:
    x = np.arange(months + 1) / 12  # years on x-axis
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=principal_series, fill="tozeroy", name="Principal (what you put in)", line=dict(color="#3b82f6"), fillcolor="rgba(59,130,246,0.5)"))
    fig.add_trace(go.Scatter(x=x, y=value_series, fill="tonexty", name="Compound growth (time + market)", line=dict(color="#22c55e"), fillcolor="rgba(34,197,94,0.5)"))
    fig.update_layout(
        title=f"Future value after {years} years",
        xaxis_title="Years", yaxis_title="Amount ($)",
        margin=dict(t=56, b=88),
        height=400,
        template="plotly_white",
        legend=dict(orientation="h", yanchor="top", y=-0.22, x=0.5, xanchor="center"),
        yaxis_tickformat="$,.0f",
        dragmode=False,
    )
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    st.plotly_chart(fig, use_container_width=True, config=dict(displayModeBar=False, scrollZoom=False))

st.metric("Final value", f"${value_series[-1]:,.0f}", f"Principal ${principal_series[-1]:,.0f} + growth ${value_series[-1] - principal_series[-1]:,.0f}")
st.caption("Try 40+ years to see retirement or early-start impact.")

st.divider()

# -----------------------------------------------------------------------------
# 5. Cost of Frictions (Buy & hold vs trader)
# -----------------------------------------------------------------------------
st.markdown(
    '<div id="cost-of-frictions"><div class="section-heading">Cost of Frictions</div></div>',
    unsafe_allow_html=True,
)
st.markdown("Same 10% annual return. **Investor A** holds 20 years and pays long-term capital gains once. **Investor B** realizes gains every year and pays short-term tax + fees.")

initial_p = st.number_input("Starting amount ($)", min_value=1000, value=100000, step=10000, key="frict_initial")
lt_rate = st.slider("Long-term capital gains rate (%)", 0.0, 30.0, 15.0, 0.5, key="lt_rate") / 100.0
st_rate = st.slider("Short-term (ordinary) tax rate (%)", 0.0, 30.0, 24.0, 0.5, key="st_rate") / 100.0
lt_rate_pct = lt_rate * 100
st_rate_pct = st_rate * 100
fee_pct = st.slider("Trading cost per round-trip (%)", 0.0, 2.0, 0.2, 0.1, key="fee_pct") / 100.0
years_f = 20
ann_return = 0.10

# A: buy & hold — grow 20y, then pay LTCG once
v_a = initial_p * (1 + ann_return) ** years_f
gain_a = v_a - initial_p
tax_a = gain_a * lt_rate
final_a = v_a - tax_a

# B: each year grow 10%, realize gain (pay short-term tax), then pay round-trip fee
v_b = initial_p
for _ in range(years_f):
    prev = v_b
    v_b = v_b * (1 + ann_return)
    gain_yr = v_b - prev
    v_b = v_b - gain_yr * st_rate
    v_b = v_b * (1 - fee_pct)
final_b = v_b

if _plotly_ok:
    # Tax rate comparison: fixed 0–30% scale so LTCG (lower) looks clearly smaller than ST
    fig_rates = go.Figure(data=[
        go.Bar(x=["Long-term capital gains", "Short-term (ordinary)"], y=[lt_rate_pct, st_rate_pct], marker_color=["#16a34a", "#dc2626"], text=[f"{lt_rate_pct:.1f}%", f"{st_rate_pct:.1f}%"], textposition="outside"),
    ])
    fig_rates.update_layout(
        title="Tax rates (same scale 0–30%)",
        yaxis_title="Rate (%)", margin=dict(t=40, b=60), height=280, template="plotly_white",
        showlegend=False, yaxis=dict(range=[0, 30], dtick=5),
        dragmode=False,
    )
    fig_rates.update_xaxes(fixedrange=True)
    fig_rates.update_yaxes(fixedrange=True)
    st.plotly_chart(fig_rates, use_container_width=True, config=dict(displayModeBar=False, scrollZoom=False))

    y_max = max(final_a, final_b)
    fig = go.Figure(data=[
        go.Bar(x=["Investor A (Buy & hold)", "Investor B (Annual realize)"], y=[final_a, final_b], marker_color=["#16a34a", "#dc2626"], text=[f"${final_a:,.0f}", f"${final_b:,.0f}"], textposition="outside"),
    ])
    fig.update_layout(
        title="Final wealth after 20 years (10% annual return)",
        yaxis_title="Final amount ($)", margin=dict(t=80, b=60), height=380, template="plotly_white",
        showlegend=False, yaxis_tickformat="$,.0f",
        yaxis=dict(range=[0, y_max * 1.18]),
        dragmode=False,
    )
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    st.plotly_chart(fig, use_container_width=True, config=dict(displayModeBar=False, scrollZoom=False))

st.caption(f"**A:** ${final_a:,.0f} (after LTCG). **B:** ${final_b:,.0f}. Friction (tax + fees) costs B **${final_a - final_b:,.0f}**.")

render_footer()
