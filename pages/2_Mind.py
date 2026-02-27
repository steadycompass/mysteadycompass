"""
MIND page - The Steady Compass.
Why Investors Lose: short fact-based messages + interactive visuals.
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
try:
    import yfinance as yf
    _yf_ok = True
except ImportError:
    _yf_ok = False


@st.cache_data(ttl=86400)
def _cost_of_missing_best_days():
    """$10,000 over 20y S&P 500: Fully Invested vs Missed Top 10/20/30 best days. Returns DataFrame with scenario, final_value."""
    if not _yf_ok:
        return None
    try:
        ticker = yf.Ticker("^GSPC")
        hist = ticker.history(period="20y", auto_adjust=True)
        if hist is None or hist.empty or len(hist) < 100:
            return None
        close = hist["Close"].dropna()
        ret = close.pct_change().dropna()
        if len(ret) < 50:
            return None
        initial = 10_000.0
        def compound(returns_series):
            return initial * (1 + returns_series).prod()
        full = compound(ret)
        def missed_top_n(n):
            r = ret.copy()
            top_idx = r.nlargest(n).index
            r.loc[top_idx] = 0.0
            return compound(r)
        rows = [
            ("Fully Invested", full),
            ("Missed Top 10 Days", missed_top_n(10)),
            ("Missed Top 20 Days", missed_top_n(20)),
            ("Missed Top 30 Days", missed_top_n(30)),
        ]
        return pd.DataFrame(rows, columns=["scenario", "final_value"])
    except Exception:
        return None

st.set_page_config(page_title="The Steady Compass", page_icon="🧭", layout="wide", initial_sidebar_state="auto")
inject_nav_css()
maybe_redirect_from_query("MIND")
render_nav("MIND")

# Sidebar: ON THIS PAGE — Why Investors Lose, Emotional Reset
with st.sidebar:
    st.markdown(
        "<style>"
        ".mind-sidenav { margin-top: 8rem; padding: 0.5rem 0; border-left: 3px solid #5a6378; padding-left: 0.75rem; margin-bottom: 1rem; } "
        ".mind-sidenav-title { font-size: 0.75rem; font-weight: 600; color: #64748b; letter-spacing: 0.05em; margin-bottom: 0.5rem; border-bottom: 1px solid #94a3b8; padding-bottom: 0.5rem; } "
        ".mind-sidenav a { display: block; padding: 0.35rem 0; font-size: 0.85rem; color: #475569; text-decoration: none; border-radius: 4px; } "
        ".mind-sidenav a:hover { color: #0ea5e9; background: #f1f5f9; padding-left: 0.25rem; } "
        ".mind-sidenav-sub { padding-left: 1rem; font-size: 0.8rem; } "
        ".mind-sidenav-group { margin-left: 0.5rem; padding-left: 0.5rem; border-left: 2px solid #cbd5e1; margin-top: 0.15rem; margin-bottom: 0.5rem; } "
        "@media (max-width: 640px) { .mind-sidenav { margin-top: 5rem; } .mind-sidenav a { font-size: 0.9rem; padding: 0.6rem 0; min-height: 44px; display: flex; align-items: center; } } "
        "</style>"
        '<div class="mind-sidenav">'
        '<div class="mind-sidenav-title">MIND</div>'
        '<a href="#why-investors-lose">Why Investors Lose</a>'
        '<div class="mind-sidenav-group" aria-label="Under Why Investors Lose">'
        '<a href="#mind-market-timing" class="mind-sidenav-sub">The Curse of Market Timing</a>'
        '<a href="#mind-tyranny-costs" class="mind-sidenav-sub">The Tyranny of Costs</a>'
        '<a href="#mind-chasing-fomo" class="mind-sidenav-sub">Chasing Past Performance & FOMO</a>'
        '<a href="#mind-needle-haystack" class="mind-sidenav-sub">Hunting the Needle Instead of the Haystack</a>'
        '<a href="#mind-discipline" class="mind-sidenav-sub">Lack of Emotional Discipline</a>'
        '</div>'
        '<a href="#emotional-reset">Emotional Reset</a>'
        '<div class="mind-sidenav-group" aria-label="Under Emotional Reset">'
        '<a href="#er-24hr" class="mind-sidenav-sub">The 24-Hour Rule</a>'
        '<a href="#er-checklist" class="mind-sidenav-sub">Panic Checklist</a>'
        '<a href="#er-museum" class="mind-sidenav-sub">The Museum of Noise</a>'
        '<a href="#er-stay-course" class="mind-sidenav-sub">Stay the Course</a>'
        '</div>'
        "</div>",
        unsafe_allow_html=True,
    )

st.markdown(
    '<div class="content-breadcrumb" aria-label="You are here">'
    '<a href="?page=HOME">Home</a> &nbsp;&gt;&nbsp; Mind</div>',
    unsafe_allow_html=True,
)
# Scroll so section titles are visible when sidebar links are clicked
st.markdown(
    "<style>"
    "#why-investors-lose, #mind-market-timing, #mind-tyranny-costs, #mind-chasing-fomo, #mind-needle-haystack, #mind-discipline, #emotional-reset, #er-24hr, #er-checklist, #er-museum, #er-stay-course { scroll-margin-top: 8rem; } "
    "</style>",
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# Why Investors Lose — 5 blocks: short fact + interactive proof
# -----------------------------------------------------------------------------
st.markdown(
    "<style>"
    ".mind-block-title { font-size: 1.12rem !important; font-weight: 600 !important; color: #334155 !important; margin: 1.25rem 0 0.35rem 0 !important; } "
    ".mind-warning-box { border-left: 4px solid #dc2626 !important; background: #fef2f2 !important; padding: 0.75rem 1rem !important; margin: 0.5rem 0 !important; border-radius: 0 6px 6px 0 !important; font-size: 0.95rem !important; color: #991b1b !important; word-wrap: break-word !important; } "
    ".mind-metric-wrap { text-align: center !important; padding: 1rem !important; margin: 0.75rem 0 !important; border: 2px solid #5a6378 !important; border-radius: 8px !important; background: #f8fafc !important; } "
    ".mind-metric-big { font-size: 2.5rem !important; font-weight: 700 !important; color: #334155 !important; } "
    "@media (max-width: 640px) { "
    ".mind-block-title { font-size: 1rem !important; margin: 1rem 0 0.25rem 0 !important; } "
    ".mind-warning-box { padding: 0.6rem 0.75rem !important; font-size: 0.875rem !important; } "
    ".mind-metric-wrap { padding: 0.75rem !important; } "
    ".mind-metric-big { font-size: 2rem !important; } "
    ".main .block-container { padding-left: 0.5rem !important; padding-right: 0.5rem !important; } "
    "[data-testid='stVerticalBlock'] > div[data-testid='column'] { min-width: 100% !important; flex: 0 0 100% !important; } "
    ".js-plotly-plot .svg-container { max-width: 100% !important; } "
    ".main [data-testid='stCheckbox'] label { min-height: 44px !important; display: flex !important; align-items: center !important; padding: 0.35rem 0 !important; } "
    ".main [data-testid='stSlider'] label { font-size: 0.875rem !important; } "
    ".main p, .main .stMarkdown { font-size: 0.875rem !important; } "
    ".main .stExpander { font-size: 0.875rem !important; } "
    "} "
    "</style>",
    unsafe_allow_html=True,
)
st.markdown(
    '<div id="why-investors-lose"><div class="section-heading">Why Investors Lose</div></div>',
    unsafe_allow_html=True,
)
# ----- Block 1: Market Timing -----
st.markdown('<div id="mind-market-timing" class="mind-block-title">The Curse of Market Timing</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="mind-warning-box">You cannot time the market.</div>',
    unsafe_allow_html=True,
)
st.markdown(
    "Trying to dodge dips and buy the bottom usually means missing the best days—and that halves your long-term return. "
    "**Miss a handful of the best days and your outcome collapses.**"
)
# Mini chart: Cost of Missing the Best Days (same as Market "Time in the Market")
cost_df = _cost_of_missing_best_days()
if cost_df is not None and _plotly_ok and len(cost_df) > 0:
    cost_df = cost_df.copy()
    cost_df["final_str"] = cost_df["final_value"].apply(lambda x: f"${x:,.0f}")
    colors = ["#16a34a", "#dc2626", "#b91c1c", "#78716c"]
    fig = px.bar(
        cost_df, x="scenario", y="final_value", text="final_str",
        labels={"scenario": "", "final_value": "Final value ($)"}, title="",
    )
    fig.update_traces(textposition="outside", textfont_size=11, marker_color=colors, hovertemplate="%{x}<br>$%{y:,.0f}<extra></extra>")
    y_max = cost_df["final_value"].max()
    fig.update_layout(
        showlegend=False, xaxis_tickangle=-25, margin=dict(t=72, b=70), height=320,
        template="plotly_white", yaxis_tickformat="$,.0f",
        yaxis=dict(range=[0, y_max * 1.18]),
        dragmode=False,
    )
    fig.update_xaxes(fixedrange=True, tickfont=dict(size=10))
    fig.update_yaxes(fixedrange=True)
    st.plotly_chart(fig, use_container_width=True, config=dict(displayModeBar=False, scrollZoom=False))
    st.caption("$10,000 invested in S&P 500 over the past 20 years. Full chart on **Market** → Time in the Market.")
else:
    st.caption("Chart data unavailable here. See **Market** → Time in the Market for the full chart.")

st.divider()

# ----- Block 2: Tyranny of Costs -----
st.markdown('<div id="mind-tyranny-costs" class="mind-block-title">The Tyranny of Costs</div>', unsafe_allow_html=True)
st.markdown("Investing is what’s left after costs. Move the sliders and see what % of your 30-year wealth goes to fees.")
ANNUAL_RETURN = 0.07
YEARS = 30
col_a, col_b = st.columns(2)
with col_a:
    fee_index = st.slider("Index fund fee (% per year)", 0.01, 0.50, 0.03, 0.01, key="fee_index") / 100.0
with col_b:
    fee_active = st.slider("Active fund fee (% per year)", 0.30, 2.50, 1.50, 0.10, key="fee_active") / 100.0

def fee_impact(annual_return, years, fee_pct):
    growth_no_fee = (1 + annual_return) ** years
    growth_with_fee = (1 + annual_return - fee_pct) ** years
    keep_pct = (growth_with_fee / growth_no_fee) * 100.0
    cost_pct = 100.0 - keep_pct
    return keep_pct, cost_pct

keep_i, cost_i = fee_impact(ANNUAL_RETURN, YEARS, fee_index)
keep_a, cost_a = fee_impact(ANNUAL_RETURN, YEARS, fee_active)

if _plotly_ok:
    fig_col1, fig_col2 = st.columns(2)
    with fig_col1:
        fig1 = go.Figure(data=[go.Pie(labels=["You keep", "Lost to fees"], values=[keep_i, cost_i], hole=0.5, marker_colors=["#16a34a", "#dc2626"])])
        fig1.update_layout(title=f"Index-style ({fee_index*100:.2f}% fee) · {YEARS}y", margin=dict(t=40, b=20), height=280, showlegend=True, legend=dict(orientation="h"), dragmode=False)
        st.plotly_chart(fig1, use_container_width=True, config=dict(displayModeBar=False, scrollZoom=False))
    with fig_col2:
        fig2 = go.Figure(data=[go.Pie(labels=["You keep", "Lost to fees"], values=[keep_a, cost_a], hole=0.5, marker_colors=["#16a34a", "#dc2626"])])
        fig2.update_layout(title=f"Active-style ({fee_active*100:.2f}% fee) · {YEARS}y", margin=dict(t=40, b=20), height=280, showlegend=True, legend=dict(orientation="h"), dragmode=False)
        st.plotly_chart(fig2, use_container_width=True, config=dict(displayModeBar=False, scrollZoom=False))
else:
    st.info(f"Index ({fee_index*100:.2f}%): You keep {keep_i:.1f}% · Active ({fee_active*100:.2f}%): You keep {keep_a:.1f}%. Install plotly for pie charts.")
st.caption('Bogle: "The more the financial system takes, the less you keep."')

st.divider()

# ----- Block 3: Chasing performance & FOMO -----
st.markdown('<div id="mind-chasing-fomo" class="mind-block-title">Chasing Past Performance & FOMO</div>', unsafe_allow_html=True)
st.markdown("**Buy high, sell low** is human nature. The cycle repeats: optimism → euphoria → panic → capitulation. Where are you now?")
if _plotly_ok:
    stages = ["Optimism", "Thrill", "Euphoria", "Complacency", "Anxiety", "Denial", "Fear", "Panic", "Capitulation", "Despair"]
    y = [2, 4, 6, 5, 3, 1, -1, -3, -5, -4]
    fig3 = go.Figure(data=[go.Scatter(x=list(range(len(stages))), y=y, mode="lines+text", line=dict(color="#5a6378", width=2), text=stages, textposition="top center")])
    fig3.update_layout(xaxis=dict(showticklabels=False), yaxis_title="Emotion", margin=dict(t=50, b=40), height=320, template="plotly_white", showlegend=False, dragmode=False)
    fig3.update_xaxes(zeroline=True, zerolinewidth=1, zerolinecolor="#e2e8f0", fixedrange=True)
    fig3.update_yaxes(fixedrange=True)
    st.plotly_chart(fig3, use_container_width=True, config=dict(displayModeBar=False, scrollZoom=False))
st.caption("When everyone is euphoric, you’re often buying high. When everyone has capitulated, the best opportunities appear.")

st.divider()

# ----- Block 4: Failing to diversify -----
st.markdown('<div id="mind-needle-haystack" class="mind-block-title">Hunting the Needle Instead of the Haystack</div>', unsafe_allow_html=True)
st.markdown("**Looking for the next Apple or Tesla?**")
st.markdown(
    '<div class="mind-metric-wrap"><span class="mind-metric-big">40%</span></div>',
    unsafe_allow_html=True,
)
st.markdown(
    "Of all U.S.-listed companies in history, **40%** eventually suffered a catastrophic loss (down **−70% or more** from their peak and never recovered). "
    "— *J.P. Morgan*. Don’t hunt the needle; buy the haystack (e.g. S&P 500)."
)

st.divider()

# ----- Block 5: Emotional discipline -----
st.markdown('<div id="mind-discipline" class="mind-block-title">Lack of Emotional Discipline</div>', unsafe_allow_html=True)
st.markdown("Before you hit *Sell*, check these. If the answer is *no*, pause.")
c1 = st.checkbox("Has the crash actually damaged the real value of my portfolio (companies’ ability to earn)?", key="chk1")
c2 = st.checkbox("Am I scared mainly because of yesterday’s gloomy headlines?", key="chk2")
c3 = st.checkbox("Will I still remember this drop in 10 years?", key="chk3")
if c1 or c2 or c3:
    st.info("**Bogle’s advice:** Do nothing. Just stand there. Don’t turn a paper loss into a permanent one by selling in panic.")

# -----------------------------------------------------------------------------
# Emotional Reset — 4 steps
# -----------------------------------------------------------------------------
st.divider()
st.markdown(
    '<div id="emotional-reset"><div class="section-heading">Emotional Reset</div></div>',
    unsafe_allow_html=True,
)

# ----- Step 1: The 24-Hour Rule -----
st.markdown('<div id="er-24hr" class="mind-block-title">The 24-Hour Rule</div>', unsafe_allow_html=True)
st.warning(
    "**Do you want to sell your stocks right now?** John Bogle said: *\"When you feel the urge to do something, do nothing. Just stand there.\"* "
    "Before you press the sell button, read this page to the end and **delay your decision by 24 hours.** "
    "Emotions always cool with time—the simplest way to block impulsive selling."
)

# ----- Step 2: Panic Checklist -----
st.markdown('<div id="er-checklist" class="mind-block-title">Panic Checklist: Wake Up Your Rational Brain</div>', unsafe_allow_html=True)
st.markdown("Answer these with a click. They switch your brain from emotion to logic.")
er1 = st.checkbox("Has my long-term retirement plan or financial goal suddenly changed today?", key="er_chk1")
er2 = st.checkbox("Have the companies in the S&P 500 (Apple, Microsoft, Google, etc.) stopped making profits and gone bankrupt today?", key="er_chk2")
er3 = st.checkbox("Am I selling because the *intrinsic value* of the companies is damaged, or only because I am afraid of the *price* going down?", key="er_chk3")
if er1 and er2 and er3:
    st.success("**Your plan is unchanged. So are the companies. The only thing that changed is the market’s mood.**")

# ----- Step 3: The Museum of Noise -----
st.markdown('<div id="er-museum" class="mind-block-title">The Museum of Noise</div>', unsafe_allow_html=True)
st.markdown("\"This crash is different—the world is really ending.\" History says otherwise. Open the headlines below.")
with st.expander("1987 Black Monday: \"Stock market collapse—the end of capitalism?\""):
    st.markdown("**Fact:** The S&P 500 went on to rise **over 1,000%** from the lows.")
with st.expander("2008 Financial Crisis: \"The fall of the U.S. economy—recovery is impossible\""):
    st.markdown("**Fact:** The following decade saw the **longest bull market** in history.")
st.caption("*The media sells fear for a living. Investors make money by selling patience.*")

# ----- Step 4: Bogle’s Stay-the-Course -----
st.markdown('<div id="er-stay-course" class="mind-block-title">Stay the Course: Bogle’s Calm</div>', unsafe_allow_html=True)
st.info("*\"Ignore the daily noise of the market. Focus only on the growth of dividends and earnings that companies create.\"*")
st.info("*\"Time is your friend; impulse is your enemy.\"*")

render_footer()
