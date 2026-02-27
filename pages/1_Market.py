"""
MARKET page - The Steady Compass.
S&P 500 historical chart, recovery history, danger of timing, rolling returns, MDD (planned).
"""

import streamlit as st
import sys
from pathlib import Path

# Allow importing from project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from components.nav import inject_nav_css, render_nav, render_footer, maybe_redirect_from_query

# If plotly is not installed, run: pip install plotly
try:
    import plotly.express as px
except ImportError:
    px = None  # UI will show install message: pip install plotly

import yfinance as yf
import pandas as pd
import numpy as np


@st.cache_data(ttl=86400)
def _fetch_sp500_daily_from_1950():
    """S&P 500 (^GSPC) daily data from 1950. For chart and drawdown table."""
    try:
        ticker = yf.Ticker("^GSPC")
        hist = ticker.history(period="max", auto_adjust=True)
        if hist is None or hist.empty or len(hist) < 2:
            return None
        df = hist[["Close"]].copy()
        df = df.reset_index()
        df.columns = ["Date", "Close"]
        df["Date"] = pd.to_datetime(df["Date"]).dt.tz_localize(None)
        df = df.dropna()
        df = df[df["Date"] >= "1950-01-01"].copy()
        if len(df) < 4:
            return None
        return df
    except Exception:
        return None


@st.cache_data(ttl=86400)
def _fetch_sp500_history():
    """Fetch S&P 500 (^GSPC) full history via yfinance. Returns DataFrame with Date, Close."""
    df = _fetch_sp500_daily_from_1950()
    if df is not None:
        return df  # 1950+ is enough for chart; for full history we could use period=max without filter
    try:
        ticker = yf.Ticker("^GSPC")
        hist = ticker.history(period="max", auto_adjust=True)
        if hist is None or hist.empty or len(hist) < 2:
            return None
        df = hist[["Close"]].copy()
        df = df.reset_index()
        df.columns = ["Date", "Close"]
        df["Date"] = pd.to_datetime(df["Date"]).dt.tz_localize(None)
        return df.dropna()
    except Exception:
        return None


@st.cache_data(ttl=86400)
def _build_drawdown_forward_table():
    """
    Worst 15 quarterly drawdowns and forward returns (1m, 3m, 1y, 3y, 5y).
    Returns DataFrame with columns: Date, S&P500 (Price), Quarterly Drop (%), 1-Month Forward (%), ...
    Plus an Average row at the bottom.
    """
    daily = _fetch_sp500_daily_from_1950()
    if daily is None or len(daily) < 20:
        return None
    daily = daily.set_index("Date").sort_index()
    close = daily["Close"]

    # Quarterly close and quarter-over-quarter return (%)
    q_close = close.resample("Q").last()
    q_ret = q_close.pct_change() * 100.0  # quarterly drop when negative

    # Worst 15 quarters (most negative)
    worst = q_ret.nsmallest(15).dropna()
    if worst.empty:
        return None

    idx = daily.index

    def first_close_on_or_after(d):
        later = idx[idx >= d]
        if len(later) == 0:
            return np.nan
        return close.loc[later[0]]

    rows = []
    for qdate in worst.index:
        qdate = pd.Timestamp(qdate)
        p0 = q_close.loc[qdate]  # quarter-end close
        if np.isnan(p0) or p0 <= 0:
            continue
        p_1m = first_close_on_or_after(qdate + pd.DateOffset(months=1))
        p_3m = first_close_on_or_after(qdate + pd.DateOffset(months=3))
        p_1y = first_close_on_or_after(qdate + pd.DateOffset(years=1))
        p_3y = first_close_on_or_after(qdate + pd.DateOffset(years=3))
        p_5y = first_close_on_or_after(qdate + pd.DateOffset(years=5))

        def ret(p):
            if np.isnan(p) or p0 <= 0:
                return np.nan
            return (p / p0 - 1.0) * 100.0

        rows.append({
            "Date": qdate.strftime("%Y-%m-%d"),
            "S&P500 (Price)": round(p0, 1),
            "Quarterly Drop (%)": round(float(worst.loc[qdate]), 1),
            "1-Month Forward (%)": round(ret(p_1m), 1) if not np.isnan(p_1m) else np.nan,
            "1-Quarter Forward (%)": round(ret(p_3m), 1) if not np.isnan(p_3m) else np.nan,
            "1-Year Forward (%)": round(ret(p_1y), 1) if not np.isnan(p_1y) else np.nan,
            "3-Year Forward (%)": round(ret(p_3y), 1) if not np.isnan(p_3y) else np.nan,
            "5-Year Forward (%)": round(ret(p_5y), 1) if not np.isnan(p_5y) else np.nan,
        })

    if not rows:
        return None
    df = pd.DataFrame(rows)

    # Average row (numeric columns only; Date = "Average"); all numbers 1 decimal
    pct_cols = [c for c in df.columns if "(%)" in c]
    avg_row = {"Date": "Average", "S&P500 (Price)": round(df["S&P500 (Price)"].mean(), 1)}
    for c in pct_cols:
        avg_row[c] = round(df[c].mean(), 1)
    df = pd.concat([df, pd.DataFrame([avg_row])], ignore_index=True)
    return df


@st.cache_data(ttl=86400)
def _build_top15_drawdowns_table():
    """
    Non-overlapping drawdown periods: From (peak) -> Trough -> To (recovery).
    Returns Top 15 by depth with: From, Trough, To, Depth (%), Length (Days), To Trough (Days), Recovery (Days).
    """
    daily = _fetch_sp500_daily_from_1950()
    if daily is None or len(daily) < 10:
        return None
    df = daily.set_index("Date").sort_index()
    close = df["Close"]
    df = df.assign(
        RunningMax=close.cummax(),
        DrawdownPct=(close - close.cummax()) / close.cummax() * 100.0,
    )

    periods = []
    i = 0
    while i < len(df):
        # Only consider rows that are at a new all-time high (peak)
        if df["Close"].iloc[i] < df["RunningMax"].iloc[i]:
            i += 1
            continue
        from_date = df.index[i]
        from_price = float(df["Close"].iloc[i])
        window = df.iloc[i + 1 :]
        if len(window) == 0:
            break
        # Find first recovery (close >= from_price) and trough (min in between)
        j = 0
        while j < len(window) and window["Close"].iloc[j] < from_price:
            j += 1
        if j == 0:
            i += 1
            continue
        sub = window.iloc[:j]
        trough_date = sub["Close"].idxmin()
        trough_price = float(sub["Close"].min())
        depth_pct = (trough_price - from_price) / from_price * 100.0
        to_trough_days = (trough_date - from_date).days
        if j < len(window):
            recovery_date = window.index[j]
            recovery_days = (recovery_date - trough_date).days
            length_days = (recovery_date - from_date).days
            to_str = recovery_date.strftime("%Y-%m-%d")
        else:
            recovery_date = None
            recovery_days = None
            length_days = None
            to_str = "Not Recovered"

        periods.append({
            "From": from_date.strftime("%Y-%m-%d"),
            "Trough": trough_date.strftime("%Y-%m-%d"),
            "To": to_str,
            "Depth (%)": round(depth_pct, 1),
            "Length (Days)": length_days,
            "To Trough (Days)": to_trough_days,
            "Recovery (Days)": recovery_days,
        })
        if j < len(window):
            i = df.index.get_loc(window.index[j])
            i = i.start if isinstance(i, slice) else i
        else:
            break

    if not periods:
        return None
    result = pd.DataFrame(periods)
    result = result.sort_values("Depth (%)").head(15).reset_index(drop=True)
    return result


def _get_all_drawdown_periods():
    """All non-overlapping drawdown periods (peak->trough->recovery) with Depth (%) and Recovery (Days)."""
    daily = _fetch_sp500_daily_from_1950()
    if daily is None or len(daily) < 10:
        return None, None
    df = daily.set_index("Date").sort_index()
    close = df["Close"]
    df = df.assign(
        RunningMax=close.cummax(),
        DrawdownPct=(close - close.cummax()) / close.cummax() * 100.0,
    )
    periods = []
    i = 0
    while i < len(df):
        if df["Close"].iloc[i] < df["RunningMax"].iloc[i]:
            i += 1
            continue
        from_date = df.index[i]
        from_price = float(df["Close"].iloc[i])
        window = df.iloc[i + 1 :]
        if len(window) == 0:
            break
        j = 0
        while j < len(window) and window["Close"].iloc[j] < from_price:
            j += 1
        if j == 0:
            i += 1
            continue
        sub = window.iloc[:j]
        trough_date = sub["Close"].idxmin()
        trough_price = float(sub["Close"].min())
        depth_pct = (trough_price - from_price) / from_price * 100.0
        if j < len(window):
            recovery_date = window.index[j]
            recovery_days = (recovery_date - trough_date).days
        else:
            recovery_days = None
        periods.append({"Depth (%)": depth_pct, "Recovery (Days)": recovery_days})
        if j < len(window):
            i = df.index.get_loc(window.index[j])
            i = i.start if isinstance(i, slice) else i
        else:
            break
    if not periods:
        return None, None
    total_years = (df.index[-1] - df.index[0]).days / 365.25
    return pd.DataFrame(periods), total_years


@st.cache_data(ttl=86400)
def _frequency_of_drops_table(_cache_version=2):
    """
    By depth bucket: Total Events, Frequency (e.g. once every N years), Avg Recovery Days.
    First two buckets are exclusive: Pullback (-5~-10%), Correction (-10~-20%).
    Bear = -20% or more (cumulative), Crash = -30% or more (cumulative), so Bear count >= Crash.
    """
    all_periods, total_years = _get_all_drawdown_periods()
    if all_periods is None or total_years is None or total_years < 1:
        return None
    df = all_periods.copy()
    # Only rows with depth <= -5% (we show Pullback, Correction, Bear, Crash)
    df = df[df["Depth (%)"] <= -5].copy()
    if df.empty:
        return None

    def bucket_exclusive(row):
        d = row["Depth (%)"]
        if -10 < d <= -5:
            return "−5% to −10% (Pullback)"
        if -20 < d <= -10:
            return "−10% to −20% (Correction)"
        return None

    df["_b"] = df.apply(bucket_exclusive, axis=1)
    rows = []
    # 1) Pullback, 2) Correction (exclusive)
    for label in ["−5% to −10% (Pullback)", "−10% to −20% (Correction)"]:
        sub = df[df["_b"] == label]
        n = len(sub)
        if n == 0:
            freq_str = "—"
            avg_rec = "—"
        else:
            yrs_per_one = total_years / n
            freq_str = f"Once every {yrs_per_one:.1f} years" if yrs_per_one >= 1 else f"{1/yrs_per_one:.1f} times per year"
            recovered = sub["Recovery (Days)"].dropna()
            avg_rec = int(round(recovered.mean())) if len(recovered) > 0 else "—"
        rows.append({"Depth Range": label, "Total Events": n, "Frequency": freq_str, "Avg Recovery (Days)": avg_rec})

    # 3) Bear Market: -20% or more (cumulative). 4) Crash: -30% or more (cumulative) → Bear >= Crash
    for label, threshold in [("−20% or more (Bear Market)", -20), ("−30% or more (Crash)", -30)]:
        sub = df[df["Depth (%)"] <= threshold]
        n = len(sub)
        if n == 0:
            freq_str = "—"
            avg_rec = "—"
        else:
            yrs_per_one = total_years / n
            freq_str = f"Once every {yrs_per_one:.1f} years" if yrs_per_one >= 1 else f"{1/yrs_per_one:.1f} times per year"
            recovered = sub["Recovery (Days)"].dropna()
            avg_rec = int(round(recovered.mean())) if len(recovered) > 0 else "—"
        rows.append({"Depth Range": label, "Total Events": n, "Frequency": freq_str, "Avg Recovery (Days)": avg_rec})

    return pd.DataFrame(rows)


@st.cache_data(ttl=86400)
def _cost_of_missing_best_days():
    """
    $10,000 over 20y in S&P 500: Fully Invested vs Missed Top 10/20/30 best days.
    Returns DataFrame with columns: scenario, final_value (float), label (str for display).
    """
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

        # Fully invested
        full = compound(ret)

        # Missed top N days: set those returns to 0
        def missed_top_n(n):
            r = ret.copy()
            top_idx = r.nlargest(n).index
            r.loc[top_idx] = 0.0
            return compound(r)

        missed_10 = missed_top_n(10)
        missed_20 = missed_top_n(20)
        missed_30 = missed_top_n(30)

        rows = [
            ("Fully Invested", full),
            ("Missed Top 10 Days", missed_10),
            ("Missed Top 20 Days", missed_20),
            ("Missed Top 30 Days", missed_30),
        ]
        return pd.DataFrame(rows, columns=["scenario", "final_value"])
    except Exception:
        return None


@st.cache_data(ttl=86400)
def _rolling_win_rate_table():
    """
    S&P 500 from 1950: win rate (%) for holding 1y, 3y, 5y, 10y, 20y (252, 756, 1260, 2520, 5040 days).
    Returns DataFrame with columns: period_label, win_rate.
    """
    daily = _fetch_sp500_daily_from_1950()
    if daily is None or len(daily) < 252:
        return None
    close = daily.set_index("Date").sort_index()["Close"]
    periods = [
        (252, "1Y"),
        (756, "3Y"),
        (1260, "5Y"),
        (2520, "10Y"),
        (5040, "20Y"),
    ]
    rows = []
    for days, label in periods:
        if len(close) < days + 1:
            continue
        ret = close.pct_change(periods=days).dropna()
        win_rate = (ret > 0).mean() * 100.0
        rows.append({"period_label": label, "win_rate": round(win_rate, 1)})
    if not rows:
        return None
    return pd.DataFrame(rows)


# Auto: sidebar hidden on mobile (hamburger to open), shown on desktop — best for small screens
st.set_page_config(page_title="The Steady Compass", page_icon="🧭", layout="wide", initial_sidebar_state="auto")
inject_nav_css()
maybe_redirect_from_query("MARKET")
render_nav("MARKET")

# Sidebar: short labels + styled block (mobile-friendly when opened)
with st.sidebar:
    st.markdown(
        "<style>"
        ".market-sidenav { margin-top: 8rem; padding: 0.5rem 0; border-left: 3px solid #5a6378; padding-left: 0.75rem; margin-bottom: 1rem; } "
        ".market-sidenav-title { font-size: 0.75rem; font-weight: 600; color: #64748b; letter-spacing: 0.05em; margin-bottom: 0.5rem; border-bottom: 1px solid #94a3b8; padding-bottom: 0.5rem; } "
        ".market-sidenav a { display: block; padding: 0.35rem 0; font-size: 0.85rem; color: #475569; text-decoration: none; border-radius: 4px; } "
        ".market-sidenav a:hover { color: #0ea5e9; background: #f1f5f9; padding-left: 0.25rem; } "
        "@media (max-width: 640px) { .market-sidenav { margin-top: 5rem; } .market-sidenav a { font-size: 0.9rem; padding: 0.6rem 0; min-height: 44px; display: flex; align-items: center; } } "
        "</style>"
        '<div class="market-sidenav">'
        '<div class="market-sidenav-title">MARKET</div>'
        '<a href="#big-picture">The Big Picture</a>'
        '<a href="#crashes-opportunities">Crashes Are Opportunities</a>'
        '<a href="#pain-and-patience">Pain and Patience</a>'
        '<a href="#frequency-drops">Frequency of Drops</a>'
        '<a href="#cost-of-timing">Cost of Timing</a>'
        '<a href="#power-of-time">Power of Time</a>'
        "</div>",
        unsafe_allow_html=True,
    )

# Breadcrumb in main content (same position as Home for consistent feel)
st.markdown(
    '<div class="content-breadcrumb" aria-label="You are here">'
    '<a href="?page=HOME">Home</a> &nbsp;&gt;&nbsp; Market'
    "</div>",
    unsafe_allow_html=True,
)
# When sidebar link is clicked, scroll so the section title is visible (not hidden above viewport)
st.markdown(
    "<style>"
    "#big-picture, #crashes-opportunities, #pain-and-patience, #frequency-drops, #cost-of-timing, #power-of-time { "
    "scroll-margin-top: 8rem; } "
    "</style>",
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# 1. The Big Picture: S&P 500 Historical Trend
# -----------------------------------------------------------------------------
st.markdown(
    '<div id="big-picture"><div class="section-heading">The Big Picture: S&P 500 Historical Trend</div></div>',
    unsafe_allow_html=True,
)

df = _fetch_sp500_history()
if df is not None and len(df) > 0:
    use_log_scale = st.checkbox("Apply log scale", value=True, key="sp500_log_scale")
    if px is not None:
        fig = px.line(
            df,
            x="Date",
            y="Close",
            title="S&P 500 Index (^GSPC) — Historical Price",
            labels={"Close": "Price", "Date": "Date"},
        )
        fig.update_layout(
            yaxis_type="log" if use_log_scale else "linear",
            hovermode="x unified",
            template="plotly_white",
            height=500,
            margin=dict(t=50, b=50),
            dragmode=False,
        )
        fig.update_xaxes(fixedrange=True)
        fig.update_yaxes(fixedrange=True)
        fig.update_traces(line=dict(color="#2563eb", width=1.5))
        st.plotly_chart(fig, use_container_width=True, config=dict(displayModeBar=True, displaylogo=False, scrollZoom=False))
    else:
        st.warning("Plotly is not installed. Install with: `pip install plotly`")
    st.markdown(
        "*Short-term crashes are but small waves in decades of history. Stay the course.*"
    )
else:
    st.info("S&P 500 historical data could not be loaded. Please try again later.")

# -----------------------------------------------------------------------------
# 2. Historical Drawdowns & Forward Returns
# -----------------------------------------------------------------------------
st.divider()
st.markdown(
    '<div id="crashes-opportunities"><div class="section-heading">Crashes Are Opportunities: Returns After the Worst Quarterly Drops</div></div>',
    unsafe_allow_html=True,
)

dd_table = _build_drawdown_forward_table()
if dd_table is not None and len(dd_table) > 0:
    # Format for HTML: 1 decimal, "—" for NaN; no scroll (same pattern as MDD table)
    def _esc(s):
        return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    pct_cols_orig = [c for c in dd_table.columns if "(%)" in c]
    cols = ["Date", "S&P500 (Price)"] + pct_cols_orig
    headers = ["Date", "S&P500", "Qtr Drop (%)", "1-Mo (%)", "1-Qtr (%)", "1-Yr (%)", "3-Yr (%)", "5-Yr (%)"]
    thead = "".join("<th>" + _esc(h) + "</th>" for h in headers)

    rows_html = []
    for ri, (_, row) in enumerate(dd_table.iterrows()):
        is_avg = row["Date"] == "Average"
        cells = []
        for ci, c in enumerate(cols):
            val = row[c]
            if pd.isna(val) or (isinstance(val, float) and np.isnan(val)):
                cell_val = "—"
            elif isinstance(val, float):
                cell_val = f"{val:.1f}"
            else:
                cell_val = str(val)
            cls = []
            if c in pct_cols_orig and cell_val != "—":
                try:
                    v = float(cell_val)
                    cls.append("pct-pos" if v > 0 else "pct-neg")
                except ValueError:
                    pass
            if ci >= 2:
                cls.append("num")
            cls_str = ' class="' + " ".join(cls) + '"' if cls else ""
            cells.append("<td" + cls_str + ">" + _esc(cell_val) + "</td>")
        tr_cls = ' class="avg-row"' if is_avg else ""
        rows_html.append("<tr" + tr_cls + ">" + "".join(cells) + "</tr>")
    tbody = "".join(rows_html)

    dd_style = (
        ".dd-html-table { width: 100%; table-layout: fixed; border-collapse: collapse; font-size: 0.8125rem; "
        "border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.06); } "
        ".dd-html-table th, .dd-html-table td { padding: 8px 10px; border: 1px solid #e2e8f0; } "
        ".dd-html-table th { background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%); font-weight: 600; "
        "text-align: left; color: #475569; letter-spacing: 0.02em; } "
        ".dd-html-table td { text-align: left; color: #334155; } "
        ".dd-html-table td.num { text-align: right; font-variant-numeric: tabular-nums; } "
        ".dd-html-table tbody tr:nth-child(even) { background: #fafbfc; } "
        ".dd-html-table tbody tr:hover { background: #f1f5f9; } "
        ".dd-html-table td.pct-pos { background: #dcfce7; color: #166534; } "
        ".dd-html-table td.pct-neg { background: #fef2f2; color: #b91c1c; } "
        ".dd-html-table tr.avg-row td { font-weight: 600; background: #f1f5f9; } "
    )
    dd_colgroup = (
        "<col style='width:14%'><col style='width:12%'>"
        "<col style='width:11%'><col style='width:11%'><col style='width:11%'><col style='width:11%'><col style='width:11%'><col style='width:11%'>"
    )
    dd_html = (
        "<style>" + dd_style + "</style>"
        "<div class='dd-html-table-wrap'>"
        "<table class='dd-html-table'>"
        "<colgroup>" + dd_colgroup + "</colgroup>"
        "<thead><tr>" + thead + "</tr></thead><tbody>" + tbody + "</tbody></table>"
        "</div>"
    )
    try:
        st.html(dd_html)
    except Exception:
        st.markdown(dd_html, unsafe_allow_html=True)
    st.caption(
        "**In John Bogle’s words:** “Time is the investor’s best friend.” As the bright green numbers in the table above (3-year and 5-year forward returns) show, only those who stayed invested through terrible crashes could enjoy the magic of compounding. Believe in capitalism’s long-term upward path and, even in fear, stay the course without wavering."
    )
else:
    st.info("Drawdown table could not be built. Please try again later.")

# -----------------------------------------------------------------------------
# 3. Top-15 S&P 500 Drawdowns (non-overlapping: peak -> trough -> recovery)
# -----------------------------------------------------------------------------
st.divider()
st.markdown(
    '<div id="pain-and-patience"><div class="section-heading">Pain and Patience: Top-15 Max Drawdowns (MDD) and Recovery</div></div>',
    unsafe_allow_html=True,
)

mdd_table = _build_top15_drawdowns_table()
if mdd_table is not None and len(mdd_table) > 0:
    # Format: 1 decimal for %, integers for days, "—" for missing
    mdd_display = mdd_table.copy()
    mdd_display["Depth (%)"] = mdd_display["Depth (%)"].apply(lambda x: f"{x:.1f}" if pd.notna(x) else "—")
    for col in ["Length (Days)", "To Trough (Days)", "Recovery (Days)"]:
        mdd_display[col] = mdd_display[col].apply(
            lambda x: "—" if pd.isna(x) else str(int(x))
        )

    # Render as HTML table (column widths: 1–4 wide, 5–7 narrow); build string without f-string to avoid brace issues
    def _esc(s):
        return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    cols = ["From", "Trough", "To", "Depth (%)", "Length (Days)", "To Trough (Days)", "Recovery (Days)"]
    thead = "".join("<th>" + _esc(c) + "</th>" for c in cols)
    rows_html = []
    for _, row in mdd_display.iterrows():
        cells = []
        for i, c in enumerate(cols):
            cls = []
            if i >= 3:  # Depth (%) and the three day columns: same narrow width, right-aligned
                cls.append("narrow")
            if c == "Depth (%)" and isinstance(row[c], str) and row[c].startswith("-"):
                cls.append("depth-neg")
            cls_str = ' class="' + " ".join(cls) + '"' if cls else ""
            cells.append("<td" + cls_str + ">" + _esc(row[c]) + "</td>")
        rows_html.append("<tr>" + "".join(cells) + "</tr>")
    tbody = "".join(rows_html)

    # From/Trough/To wider; Depth, Length, To Trough, Recovery same narrow width; clean, readable style
    style_block = (
        ".mdd-html-table { width: 100%; table-layout: fixed; border-collapse: collapse; font-size: 0.8125rem; "
        "border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.06); } "
        ".mdd-html-table th, .mdd-html-table td { padding: 8px 10px; border: 1px solid #e2e8f0; } "
        ".mdd-html-table th { background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%); font-weight: 600; "
        "text-align: left; color: #475569; letter-spacing: 0.02em; } "
        ".mdd-html-table td { text-align: left; color: #334155; } "
        ".mdd-html-table tbody tr:nth-child(even) { background: #fafbfc; } "
        ".mdd-html-table tbody tr:hover { background: #f1f5f9; } "
        ".mdd-html-table td.narrow { text-align: right; font-variant-numeric: tabular-nums; } "
        ".mdd-html-table td.depth-neg { background: #fef2f2; color: #b91c1c; font-weight: 600; }"
    )
    colgroup = (
        "<col style='width:22%'><col style='width:22%'><col style='width:22%'>"
        "<col style='width:11%'><col style='width:11%'><col style='width:11%'><col style='width:11%'>"
    )
    html_table = (
        "<style>" + style_block + "</style>"
        "<div class='mdd-html-table-wrap'>"
        "<table class='mdd-html-table'>"
        "<colgroup>" + colgroup + "</colgroup>"
        "<thead><tr>" + thead + "</tr></thead><tbody>" + tbody + "</tbody></table>"
        "</div>"
    )
    try:
        st.html(html_table)
    except Exception:
        st.markdown(html_table, unsafe_allow_html=True)
    st.caption(
        "Time is your friend; impulse is your enemy. Don't check your account balance too often. "
        "History shows that every past crash has ultimately been a stepping stone to greater gains."
    )
else:
    st.info("Top-15 drawdown table could not be built. Please try again later.")

# -----------------------------------------------------------------------------
# 4. Frequency of Market Drops: How Often Do They Happen?
# -----------------------------------------------------------------------------
st.divider()
st.markdown(
    '<div id="frequency-drops"><div class="section-heading">Frequency of Market Drops: How Often Do They Happen?</div></div>',
    unsafe_allow_html=True,
)
freq_drops_df = _frequency_of_drops_table(_cache_version=2)
if freq_drops_df is not None and len(freq_drops_df) > 0:
    st.table(freq_drops_df)
    st.info(
        "**Bogle's Wisdom:** Volatility is not an anomaly—it is the 'season' that comes every year. "
        "A 10% drop is like winter: it arrives about once a year. You don't sell your house when winter comes; "
        "you put on a warm coat and wait for spring. Volatility is the 'fee' you pay for long-term returns. "
        "Don't be surprised. It has always been this way, and markets have always recovered."
    )
else:
    st.info("Frequency-of-drops table could not be built. Please try again later.")

# -----------------------------------------------------------------------------
# 5. The Cost of Missing the Best Days (bar chart)
# -----------------------------------------------------------------------------
st.divider()
st.markdown(
    '<div id="cost-of-timing"><div class="section-heading">Time in the Market: The Cost of Trying to Time It</div></div>',
    unsafe_allow_html=True,
)

cost_df = _cost_of_missing_best_days()
if cost_df is not None and len(cost_df) > 0 and px is not None:
    st.info(
        "**Simulation:** $10,000 invested in S&P 500 over the past 20 years. "
        "This chart shows the final value if you stayed **fully invested** (never sold) over ~5,000 trading days "
        "versus the impact of missing just a few of the **best days**. "
        "The best rallies often arrive in the middle of the worst selloffs."
    )
    cost_df = cost_df.copy()
    cost_df["final_str"] = cost_df["final_value"].apply(lambda x: f"${x:,.0f}")
    colors = ["#16a34a", "#dc2626", "#b91c1c", "#78716c"]
    fig = px.bar(
        cost_df,
        x="scenario",
        y="final_value",
        text="final_str",
        labels={"scenario": "", "final_value": "Final value (unit: $)"},
        title="",
    )
    fig.update_traces(
        textposition="outside",
        textfont_size=12,
        marker_color=colors,
        hovertemplate="%{x}<br>Final value: $%{y:,.0f}<extra></extra>",
    )
    fig.update_layout(
        showlegend=False,
        xaxis_tickangle=-25,
        yaxis_title="Final value (unit: $)",
        margin=dict(t=40, b=80),
        height=420,
        template="plotly_white",
        yaxis_tickformat="$,.0f",
        dragmode=False,
    )
    fig.update_xaxes(fixedrange=True, tickfont=dict(size=11))
    fig.update_yaxes(fixedrange=True)
    st.plotly_chart(fig, use_container_width=True, config=dict(displayModeBar=True, displaylogo=False, scrollZoom=False))
    st.markdown(
        "*The best rallies often come right after the worst selloffs. "
        "Jumping in and out of the market is like trying to dodge lightning and getting struck instead.*"
    )
elif cost_df is None or len(cost_df) == 0:
    st.info("Cost-of-missing-days data could not be loaded. Please try again later.")
else:
    st.warning("Plotly is required for this chart. Install with: `pip install plotly`")

# -----------------------------------------------------------------------------
# 6. The Power of Time: Rolling Returns Win Rate
# -----------------------------------------------------------------------------
st.divider()
st.markdown(
    '<div id="power-of-time"><div class="section-heading">The Power of Time: Rolling Returns Win Rate</div></div>',
    unsafe_allow_html=True,
)

win_df = _rolling_win_rate_table()
if win_df is not None and len(win_df) > 0 and px is not None:
    st.info(
        "**Bogle's Wisdom:** Time dilutes risk. In the short run the stock market is like a casino; "
        "in the long run it's a sure win. In S&P 500 history, 1-year holdings had about a 25% chance of loss, "
        "but no one who stayed invested 20 years or more lost money. Stay the course and you win."
    )
    win_df = win_df.copy()
    win_df["win_str"] = win_df["win_rate"].apply(lambda x: f"{x:.1f}%")
    colors = ["#7dd3fc", "#38bdf8", "#0ea5e9", "#0284c7", "#0369a1"]
    fig = px.bar(
        win_df,
        x="period_label",
        y="win_rate",
        text="win_str",
        labels={"period_label": "Holding period", "win_rate": "Win rate (%)"},
        title="",
    )
    fig.update_traces(
        textposition="outside",
        textfont_size=12,
        marker_color=colors,
        hovertemplate="%{x}<br>Win rate: %{y:.1f}%<extra></extra>",
    )
    fig.update_layout(
        showlegend=False,
        yaxis_title="Win rate (%)",
        yaxis_range=[0, 105],
        margin=dict(t=50, b=60),
        height=420,
        template="plotly_white",
        dragmode=False,
    )
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    st.plotly_chart(fig, use_container_width=True, config=dict(displayModeBar=True, displaylogo=False, scrollZoom=False))
elif win_df is None or len(win_df) == 0:
    st.info("Rolling win-rate data could not be loaded. Please try again later.")
else:
    st.warning("Plotly is required for this chart. Install with: `pip install plotly`")

# When opened via Mind link (?page=MARKET&anchor=cost-of-timing), scroll to that section
if st.query_params.get("anchor") == "cost-of-timing":
    try:
        import streamlit.components.v1 as components
        components.html(
            """
            <script>
            (function() {
              var doc = window.parent.document;
              var el = doc.getElementById('cost-of-timing');
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

# Link to Tools: Compare with inflation (Real vs Nominal)
st.markdown(
    '<p style="margin-top:1.5rem; font-size:0.9rem; color:#64748b;">'
    '<strong>Compare with inflation:</strong> '
    '<a href="?page=TOOLS&anchor=real-nominal" target="_self" style="color:#0ea5e9;">Real vs Nominal Return</a> '
    '— see how nominal returns compare to inflation in Tools.</p>',
    unsafe_allow_html=True,
)

render_footer()
