"""
The Steady Compass - Market Dashboard

SITE LANGUAGE: English only. All UI text, labels, AI-generated content (e.g. Weekly Signal),
and prompts sent to APIs must be in English. Do not introduce Korean or other languages.

Streamlit app with fixed top navigation and HOME/MARKET/MIND/TOOLS/GUIDE/ABOUT pages.
Data layer prepared for future Yahoo Finance (or other API) integration.
"""

import html
import json
import os
import random
import re
import time
import traceback
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from components.nav import inject_nav_css, render_nav, render_footer, maybe_redirect_from_query, PAGES

try:
    from streamlit_autorefresh import st_autorefresh
except ImportError:
    st_autorefresh = None

try:
    import plotly.graph_objects as go
except ImportError:
    go = None

try:
    from streamlit.errors import StreamlitSecretNotFoundError
except ImportError:
    StreamlitSecretNotFoundError = Exception  # fallback for older Streamlit


def _get_gemini_api_key():
    """Safely read GEMINI_API_KEY. Returns '' if .streamlit/secrets.toml is missing or key not set."""
    try:
        return (st.secrets.get("GEMINI_API_KEY") or "").strip()
    except (StreamlitSecretNotFoundError, KeyError, FileNotFoundError, Exception):
        return ""


def _get_news_api_key():
    """Safely read NEWS_API_KEY for Weekly Signal. Optional; placeholder used if missing."""
    try:
        return (st.secrets.get("NEWS_API_KEY") or "").strip()
    except (StreamlitSecretNotFoundError, KeyError, FileNotFoundError, Exception):
        return ""


# -----------------------------------------------------------------------------
# Page config (must be first Streamlit command). Main nav is top bar; sidebar empty.
# -----------------------------------------------------------------------------
# Left sidebar left empty for now; reserved for future submenus or detailed content.
st.set_page_config(
    page_title="The Steady Compass",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
# SITE LANGUAGE: English only. UI, copy, and AI prompts must stay in English.
# -----------------------------------------------------------------------------
TICKERS_1DAY = ["VOO", "QQQ", "VWO", "VXUS", "BND", "SGOV", "GLD", "PDBC"]
TICKERS_PERF = ["VOO", "QQQ", "VWO", "VXUS", "BND", "SGOV", "GLD", "PDBC"]

# -----------------------------------------------------------------------------
# 1DAY data: live via yfinance when available, else placeholder
# -----------------------------------------------------------------------------
def _this_last_month_labels(now_et_dt):
    """Return (this_month_label, last_month_label) e.g. ('Feb 2026', 'Jan 2026'). Uses ET date."""
    this_start = now_et_dt.replace(day=1).date()
    last_end = this_start - timedelta(days=1)
    last_start = last_end.replace(day=1)
    this_label = now_et_dt.strftime("%b %Y")
    last_label = last_start.strftime("%b %Y")
    return this_label, last_label


def get_1day_data():
    """Fetch 1-day change and returns from yfinance on every call (no cache = live when app reruns). Fallback to placeholder if unavailable."""
    et = ZoneInfo("America/New_York")
    now_et_dt = datetime.now(et)
    now_et = now_et_dt.strftime("%Y-%m-%d %H:%M ET")
    # First month column = this month's return %; second = last month's. Labels auto-update when the month changes.
    this_label, last_label = _this_last_month_labels(now_et_dt)
    col_this = f"{this_label} (%)"   # e.g. Feb 2026 (%) = this month
    col_last = f"{last_label} (%)"   # e.g. Jan 2026 (%) = last month

    try:
        import yfinance as yf
    except ImportError:
        return _placeholder_1day_data(now_et, col_this, col_last)

    # Date bounds for this month (MTD) and last month (full month)
    this_start = now_et_dt.replace(day=1).date()
    last_end = this_start - timedelta(days=1)
    last_start = last_end.replace(day=1)

    chg_pct = []
    this_month_pct = []
    last_month_pct = []
    tickers_ok = []
    for t in TICKERS_1DAY:
        try:
            hist = yf.Ticker(t).history(period="3mo", interval="1d", auto_adjust=True)
            if hist is None or len(hist) < 2:
                chg_pct.append(None)
                this_month_pct.append(None)
                last_month_pct.append(None)
                tickers_ok.append(t)
                continue
            hist = hist.copy()
            if hist.index.tz is not None:
                hist = hist.tz_convert(et)
            hist = hist.sort_index(ascending=True)
            hist["_date"] = hist.index.date if hasattr(hist.index, "date") else [d.date() for d in hist.index]
            close = hist["Close"]

            # 1-day Chg (%) and Return (%) (same as day-over-day)
            latest = float(close.iloc[-1])
            prev = float(close.iloc[-2])
            pct = (latest - prev) / prev * 100.0
            chg_pct.append(round(pct, 2))
            tickers_ok.append(t)

            # This month MTD: (latest - close at start of this month) / start * 100
            mask_this = hist["_date"] >= this_start
            if not mask_this.any():
                this_month_pct.append(None)
            else:
                start_close = float(close.loc[mask_this].iloc[0])
                this_month_pct.append(round((latest - start_close) / start_close * 100.0, 2))

            # Last month: (close at end of last month - close at start of last month) / start * 100
            mask_last = (hist["_date"] >= last_start) & (hist["_date"] <= last_end)
            if not mask_last.any() or mask_last.sum() < 2:
                last_month_pct.append(None)
            else:
                sub = hist.loc[mask_last]
                first_close = float(sub["Close"].iloc[0])
                end_close = float(sub["Close"].iloc[-1])
                last_month_pct.append(round((end_close - first_close) / first_close * 100.0, 2))
        except Exception:
            chg_pct.append(None)
            this_month_pct.append(None)
            last_month_pct.append(None)
            tickers_ok.append(t)

    if all(x is None for x in chg_pct):
        return _placeholder_1day_data(now_et, col_this, col_last)

    n = len(tickers_ok)
    return pd.DataFrame({
        "Ticker": tickers_ok,
        "Chg (%)": chg_pct,
        col_this: (this_month_pct + [None] * n)[:n],
        col_last: (last_month_pct + [None] * n)[:n],
        "Time ET": [now_et] * n,
    })


def _placeholder_1day_data(now_et, col_this_month, col_last_month):
    """Fallback when yfinance is missing or all tickers fail. col_this_month / col_last_month e.g. 'Feb 2026 (%)', 'Jan 2026 (%)'."""
    data = {
        "Ticker": TICKERS_1DAY,
        "Chg (%)": [0.12, -0.05, 0.31, 0.18, 0.02, 0.01, -0.15, 0.42],
        col_this_month: [2.1, 3.2, 1.8, 2.0, 0.3, 0.2, -0.5, 5.1],
        col_last_month: [1.5, 2.8, 1.2, 1.4, 0.4, 0.3, 0.2, 3.2],
        "Time ET": [now_et] * len(TICKERS_1DAY),
    }
    return pd.DataFrame(data)


# Trading days (approx) for performance periods
_PERF_DAYS = {"1M": 21, "3M": 63, "6M": 126, "1Y": 252, "3Y": 756, "5Y": 1260, "10Y": 2520}


@st.cache_data(ttl=3600)
def get_performances_data():
    """Fetch 1M, 3M, 6M, 1Y, 3Y, 5Y, 10Y performance from yfinance (real price history)."""
    et = ZoneInfo("America/New_York")
    now_et = datetime.now(et).strftime("%Y-%m-%d %H:%M ET")
    try:
        import yfinance as yf
    except ImportError:
        return _performances_placeholder(now_et)
    rows = []
    for ticker in TICKERS_PERF:
        try:
            t = yf.Ticker(ticker)
            hist = t.history(period="10y", interval="1d", auto_adjust=True)
            if hist is None or hist.empty or "Close" not in hist.columns:
                rows.append(_perf_row_none(ticker, now_et))
                continue
            close = hist["Close"].dropna()
            if len(close) < 22:
                rows.append(_perf_row_none(ticker, now_et))
                continue
            row = {"Ticker": ticker}
            for period, days in _PERF_DAYS.items():
                if len(close) <= days:
                    row[period] = None
                    continue
                p_old = float(close.iloc[-days - 1])
                p_new = float(close.iloc[-1])
                if p_old and p_old > 0:
                    row[period] = round((p_new / p_old - 1) * 100, 1)
                else:
                    row[period] = None
            row["Time ET"] = now_et
            rows.append(row)
        except Exception:
            rows.append(_perf_row_none(ticker, now_et))
    if not rows:
        return _performances_placeholder(now_et)
    return pd.DataFrame(rows)


def _perf_row_none(ticker: str, now_et: str):
    """One row of None for each period when data is missing."""
    return {
        "Ticker": ticker,
        "1M": None, "3M": None, "6M": None, "1Y": None,
        "3Y": None, "5Y": None, "10Y": None,
        "Time ET": now_et,
    }


def _performances_placeholder(now_et: str):
    """Fallback when yfinance is unavailable."""
    return pd.DataFrame([
        {"Ticker": t, "1M": None, "3M": None, "6M": None, "1Y": None, "3Y": None, "5Y": None, "10Y": None, "Time ET": now_et}
        for t in TICKERS_PERF
    ])


# -----------------------------------------------------------------------------
# Market Temperature: ^VIX, VOO (disparity), Market Breadth (S5TH or S&P 100 large-cap)
# Breadth: Try S5TH first; if unavailable, use S&P 100 (top 100 by market cap) % above 200-day MA. Show source in UI.
# -----------------------------------------------------------------------------
# S&P 100 style: Top 100 large-cap tickers (fixed list). Lower API load; used as large-cap market temperature.
SP100_TICKERS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "BRK-B", "UNH", "JNJ", "JPM",
    "V", "PG", "XOM", "HD", "CVX", "MA", "ABBV", "MRK", "PEP", "KO", "COST", "LLY",
    "WMT", "MCD", "CSCO", "ABT", "DHR", "VZ", "TMO", "NEE", "WFC", "PM", "NKE", "BMY",
    "HON", "INTC", "AMGN", "TXN", "AMD", "QCOM", "UPS", "IBM", "LOW", "CAT", "GE",
    "AXP", "GS", "BA", "SPGI", "PLD", "DE", "SBUX", "GILD", "ADI", "REGN", "LMT",
    "BLK", "BKNG", "MDT", "AMAT", "CVS", "SYK", "TJX", "CI", "C", "SO", "DUK",
    "CMCSA", "BDX", "BSX", "PGR", "ISRG", "SLB", "CB", "CL", "ZTS", "MMC", "APD",
    "MO", "EOG", "ITW", "WM", "AON", "EQIX", "SHW", "KLAC", "HCA", "ETN", "ECL",
    "MU", "NOC", "RTX", "FIS", "VRSK", "ICE", "APTV", "PSA", "FCX", "EMR", "MET",
    "PH", "NXPI", "SNPS", "CDNS", "ORLY", "CME", "PANW", "MAR", "USB", "PGR",
]


@st.cache_data(ttl=3600)
def _pct_sp100_above_200ma(_v=3):
    """S&P 100 large-cap: % of tickers above 200-day MA. Computed from 1y yfinance data for the 100 tickers."""
    try:
        import yfinance as yf
        data = yf.download(
            tickers=SP100_TICKERS[:100],
            period="1y",
            interval="1d",
            group_by="ticker",
            auto_adjust=True,
            threads=True,
            progress=False,
            timeout=45,
        )
        if data is None or data.empty:
            return None
        above, total = 0, 0
        multi = getattr(data.columns, "nlevels", 1) > 1
        for sym in SP100_TICKERS[:100]:
            close = None
            if multi:
                if (sym, "Close") in data.columns:
                    close = data[(sym, "Close")]
                elif sym in data.columns.get_level_values(0):
                    try:
                        close = data[sym]["Close"]
                    except (KeyError, TypeError):
                        pass
            if close is None or len(close) < 200:
                continue
            close = close.dropna()
            if len(close) < 200:
                continue
            ma200 = close.rolling(200).mean()
            last_c, last_ma = float(close.iloc[-1]), float(ma200.iloc[-1])
            if last_ma and last_ma > 0:
                total += 1
                if last_c > last_ma:
                    above += 1
        if total < 20:
            return None
        return round(above / total * 100, 1)
    except Exception:
        return None


@st.cache_data(ttl=3600)
def _pct_s5th_from_yahoo(_v=2):
    """Use official S5TH (^S5TH) from Yahoo if available; otherwise None."""
    try:
        import yfinance as yf
        for sym in ("^S5TH", "S5TH"):
            try:
                t = yf.Ticker(sym)
                h = t.history(period="5d", interval="1d", auto_adjust=True)
                if h is not None and len(h) > 0 and "Close" in h.columns:
                    val = float(h["Close"].iloc[-1])
                    if 0 <= val <= 100:
                        return round(val, 1)
                    if 0 <= val <= 1:
                        return round(val * 100, 1)
            except Exception:
                continue
    except Exception:
        pass
    return None


def _vix_state_and_fear_greed(vix_val):
    """VIX value → (state_label, fear_greed 0-100 for get_market_condition)."""
    if vix_val < 15:
        return "Calm", 80.0
    if vix_val < 20:
        return "Normal", 55.0
    if vix_val < 30:
        return "Anxious", 35.0
    return "Extreme Fear", 15.0


@st.cache_data(ttl=3600)
def get_market_temperature_metrics(_cache_version=2):
    """
    vix_value, vix_state, fear_greed, disparity_pct, breadth_pct. All from yfinance.
    """
    out = {
        "vix_value": 20.0,
        "vix_state": "Normal",
        "fear_greed": 50.0,
        "disparity_pct": 0.0,
        "breadth_pct": 50.0,
        "breadth_available": False,
        "breadth_label": "",
    }
    try:
        import yfinance as yf

        # 1) Market Volatility (VIX): ^VIX latest close, 4-tier state
        vix = yf.Ticker("^VIX")
        vix_hist = vix.history(period="5d", interval="1d", auto_adjust=True)
        if vix_hist is not None and len(vix_hist) > 0:
            vix_val = float(vix_hist["Close"].iloc[-1])
            out["vix_value"] = round(vix_val, 2)
            out["vix_state"], out["fear_greed"] = _vix_state_and_fear_greed(vix_val)

        # 2) 200-Day Disparity: VOO current vs 200-day SMA (%)
        voo = yf.Ticker("VOO")
        hist = voo.history(period="1y", interval="1d", auto_adjust=True)
        if hist is not None and len(hist) >= 200:
            close = hist["Close"]
            ma200 = close.rolling(200).mean()
            last_close = float(close.iloc[-1])
            last_ma = float(ma200.iloc[-1])
            if last_ma and last_ma > 0:
                out["disparity_pct"] = round((last_close - last_ma) / last_ma * 100, 1)

        # 3) Market Breadth: Try S5TH; if unavailable, compute from S&P 100 large-cap. Show source in UI.
        pct_above = _pct_s5th_from_yahoo(_v=2)
        if pct_above is not None:
            out["breadth_pct"] = pct_above
            out["breadth_available"] = True
            out["breadth_label"] = "S&P 500 (S5TH)"
        else:
            pct_above = _pct_sp100_above_200ma(_v=3)
            if pct_above is not None:
                out["breadth_pct"] = pct_above
                out["breadth_available"] = True
                out["breadth_label"] = "S&P 100 large-cap"

    except Exception:
        pass
    return out


# Metric zones: bad, neutral, good
def _zone_fear_greed(v):
    if v < 30:
        return "bad"
    if v <= 70:
        return "neutral"
    return "good"


def _zone_disparity(v):
    if v <= -5:
        return "bad"
    if v <= 8:
        return "neutral"
    return "good"


def _zone_breadth(v):
    if v < 30:
        return "bad"
    if v <= 70:
        return "neutral"
    return "good"


def get_market_condition(fear_greed, disparity_pct, breadth_pct):
    """
    Returns state ('COLD'|'NEUTRAL'|'HOT'), zones dict, and is_divergence.
    COLD: 2+ metrics in bad.  HOT: 2+ metrics in good.  Else NEUTRAL. (3 metrics: VIX, disparity, breadth)
    """
    z_fg = _zone_fear_greed(fear_greed)
    z_d = _zone_disparity(disparity_pct)
    z_b = _zone_breadth(breadth_pct)
    zones = {"fear_greed": z_fg, "disparity": z_d, "breadth": z_b}

    bad_count = sum(1 for z in (z_fg, z_d, z_b) if z == "bad")
    good_count = sum(1 for z in (z_fg, z_d, z_b) if z == "good")

    if bad_count >= 2:
        state = "COLD"
    elif good_count >= 2:
        state = "HOT"
    else:
        state = "NEUTRAL"

    is_divergence = (z_d in ("good", "neutral") and z_b == "bad") or (
        z_d == "good" and z_b == "neutral"
    )

    return state, zones, is_divergence


# Shared very-light colors for both Gurus' Beacon and Current Sea boxes (by market state).
STATE_BOX_STYLE = {
    "COLD": (
        "linear-gradient(135deg, #f8fafc 0%, #f0f9ff 50%, #e0f2fe 100%)",
        "#93c5fd",
    ),
    "NEUTRAL": (
        "linear-gradient(135deg, #f8fafc 0%, #f0fdf4 50%, #dcfce7 100%)",
        "#86efac",
    ),
    "HOT": (
        "linear-gradient(135deg, #fffbeb 0%, #fff7ed 50%, #ffedd5 100%)",
        "#fdba74",
    ),
}

# Current Sea: 5 (title, desc) per state — 15 total. Picked at random per load.
CURRENT_SEA_BY_STATE = {
    "COLD": [
        ("Current Sea: Stormy (Cold)", "The beacon when fear rules and the index is low. The market is full of pessimism; prices are well below average and most stocks are declining."),
        ("Current Sea: Choppy Waters (Cold)", "When the index is low and fear dominates, the lighthouse appears. Sentiment is deeply negative and breadth is weak."),
        ("Current Sea: Storm Warning (Cold)", "A beacon for the fearful. The market is in a downturn; many stocks are below their averages and investors are anxious."),
        ("Current Sea: Rough Seas (Cold)", "The beacon when the market is cold. Pessimism prevails; prices are well below the long-term average and few stocks are advancing."),
        ("Current Sea: Fog and Swell (Cold)", "When fear rules and the index is low, the steady light appears. The market is full of pessimism and declining breadth."),
    ],
    "NEUTRAL": [
        ("Current Sea: Steady Sailing (Neutral)", "A whisper that tests the sailor's patience when the waves are calm. The market is range-bound or rising gently with no clear direction; sentiment is stable."),
        ("Current Sea: Calm Waters (Neutral)", "When the waves are calm, the sailor's patience is tested. The market is neither euphoric nor fearful; it is drifting or edging along."),
        ("Current Sea: Fair Winds (Neutral)", "Neither storm nor scorching sun. The market is in a holding pattern; breadth and sentiment are mixed and direction is unclear."),
        ("Current Sea: Gentle Swell (Neutral)", "The sea is calm and the compass is steady. The market is range-bound; no strong trend in fear, breadth, or disparity."),
        ("Current Sea: Quiet Seas (Neutral)", "A whisper when the waves are flat. Sentiment is stable, the market is neither overheated nor cold; it is the time for patience."),
    ],
    "HOT": [
        ("Current Sea: Scorching Sun (Overheated)", "A warning when the sun is too hot and eyes are dazzled. The market is euphoric; prices have risen far above average and almost all stocks are up—FOMO is extreme."),
        ("Current Sea: High Noon (Overheated)", "When the sun is highest, the shadow is shortest. Euphoria is in the air; the index and breadth are extended and everyone is bullish."),
        ("Current Sea: Overheated (HOT)", "A warning for the party. Prices are well above average, breadth is strong, and sentiment is greedy. Time to check your life jacket."),
        ("Current Sea: Blazing Trail (Overheated)", "The market has run hot; fear is low and greed is high. Many stocks are well above their averages. Stay alert, not reckless."),
        ("Current Sea: Summer High (Overheated)", "When everyone is celebrating, the compass warns. The market is euphoric and extended; FOMO is high. Rebalance, do not chase."),
    ],
}

# Compass Wisdom: 5 msg per state — 15 total. Picked at random per load.
COMPASS_WISDOM_BY_STATE = {
    "COLD": [
        "The wind is strong and the waves are high, but the compass still points north. Do not change harbor. Those who abandon ship in a storm never reach their destination.",
        "In a storm, the best move is often no move. Stay the course. History rewards those who kept their allocation through the crash.",
        "Do not sell in a panic. The market will recover; those who stayed invested after past crashes were glad they did. Hold your course.",
        "When everyone is fearful, the compass says stay. Rebalance if you must, but do not flee to cash. Your plan was made for days like this.",
        "The sea is rough; your job is to keep the ship. Do not change your long-term allocation because of short-term weather. Stay the course.",
    ],
    "NEUTRAL": [
        "When the sea is calm, seamanship is tested. Now is the time for patience and holding course, not flashy moves. Enjoy daily life and forget the market.",
        "No storm, no euphoria—just the long game. Stick to your allocation, rebalance if your plan says so, and do not chase or flee. Patience wins.",
        "The market is giving you nothing to do. That is exactly when doing nothing is the right move. Stay invested and stay calm.",
        "In calm waters, the best sailors do not stir the pot. Keep your asset allocation, keep costs low, and let time work. Enjoy the boredom.",
        "When there is no clear trend, the compass says hold. Do not increase risk out of boredom or cut exposure out of worry. Stay the course.",
    ],
    "HOT": [
        "When the sun is highest, the shadow is shortest. When everyone is celebrating, check your life jacket. Do not get drunk on excess returns; it is time to rebalance your asset allocation.",
        "Euphoria is the enemy of the long-term investor. Now is the time to rebalance toward your target allocation, not to add more risk. Stay disciplined.",
        "When everyone is greedy, be cautious. Put new money in gradually; do not chase. The best time to have sold was yesterday; the second best is to rebalance today.",
        "The party is loud; the compass says prepare. Rebalance if you are overweight stocks. Do not assume the rally never ends. Discipline wins.",
        "High prices mean future returns are likely lower. Do not pour new money in at the top. Rebalance, stay diversified, and keep your plan. Cool heads win.",
    ],
}


def get_state_display(state, is_divergence):
    """
    Current Sea & Compass Wisdom box: one (title, desc) and one msg at random per state.
    Uses CURRENT_SEA_BY_STATE and COMPASS_WISDOM_BY_STATE (5 options each per state).
    """
    pool_sea = CURRENT_SEA_BY_STATE.get(state, CURRENT_SEA_BY_STATE["NEUTRAL"])
    pool_wisdom = COMPASS_WISDOM_BY_STATE.get(state, COMPASS_WISDOM_BY_STATE["NEUTRAL"])
    title, desc = random.choice(pool_sea)
    msg = random.choice(pool_wisdom)
    theme, border = STATE_BOX_STYLE.get(state, STATE_BOX_STYLE["NEUTRAL"])

    if is_divergence:
        msg += (
            " <strong>Divergence alert:</strong> The market looks strong on the surface but is weak underneath. "
            "The index is high while the number of advancing stocks is low. Proceed with caution."
        )

    return title, desc, msg, theme, border


def zone_label(z, metric="generic"):
    """Metric: generic | disparity | breadth. Disparity uses Weak/Normal/Overextended."""
    if metric == "disparity":
        return {"bad": "Weak", "neutral": "Normal", "good": "Overextended"}.get(z, "")
    if metric == "breadth":
        return {"bad": "Few advancing", "neutral": "Normal", "good": "Broad advance"}.get(z, "")
    return {"bad": "Bad", "neutral": "Neutral", "good": "Good"}.get(z, "")


def make_gauge_figure(value, axis_range, steps, title, number_suffix=""):
    """Unified half-circle gauge. steps = [(end_val, "#color"), ...] for contiguous segments."""
    if not go:
        return None
    step_ranges = []
    lo = axis_range[0]
    for end_val, color in steps:
        step_ranges.append({"range": [lo, end_val], "color": color})
        lo = end_val
    gauge = {
        "axis": {"range": axis_range, "tickwidth": 1, "tickcolor": "#64748b", "tickfont": {"size": 11}},
        "bar": {"color": "#1e293b", "thickness": 0.2},
        "bgcolor": "rgba(0,0,0,0)",
        "borderwidth": 0,
        "steps": step_ranges,
        "threshold": {"line": {"color": "#1e293b", "width": 2}, "thickness": 0.85, "value": value},
    }
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        number={"suffix": number_suffix, "font": {"size": 22}, "valueformat": ".1f"},
        domain={"x": [0.08, 0.92], "y": [0.1, 0.9]},
        title={"text": title, "font": {"size": 13}},
        gauge=gauge,
    ))
    fig.update_layout(
        height=200,
        margin=dict(l=24, r=24, t=44, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        font={"family": "Segoe UI, sans-serif", "color": "#334155"},
        showlegend=False,
        dragmode=False,
    )
    return fig


# -----------------------------------------------------------------------------
# NYC market hours & Guru's Wisdom (rule-based, zero API cost)
# -----------------------------------------------------------------------------
ET = ZoneInfo("America/New_York")


def is_weekend_or_holiday(now_et=None):
    """True if today is weekend or US market holiday (NYSE). Simple list of common holidays."""
    now_et = now_et or datetime.now(ET)
    if now_et.weekday() >= 5:  # Sat=5, Sun=6
        return True
    month_day = (now_et.month, now_et.day)
    us_holidays = {
        (1, 1), (7, 4), (12, 25),
        (11, 28), (11, 29),  # Thanksgiving (approx)
    }
    return month_day in us_holidays


def is_ny_market_open(now_et=None):
    """True if current time is within 09:30–16:00 ET, Mon–Fri (excluding holidays)."""
    now_et = now_et or datetime.now(ET)
    if is_weekend_or_holiday(now_et):
        return False
    t = now_et.time()
    from datetime import time
    open_t, close_t = time(9, 30), time(16, 0)
    return open_t <= t < close_t


# -----------------------------------------------------------------------------
# Current Sea (Compass Wisdom) + Guru's Wisdom via Gemini 1.5 Flash
# Gemini 1.5 Flash free tier limits:
#   RPD (daily requests): 1,500/day  |  RPM (per minute): 15/min  |  TPM: 1M tokens/min
# We use 2h time-bucket cache (one call per 2h per feature) → ~24 calls/day max, well under 1,500.
# -----------------------------------------------------------------------------
def _call_gemini_current_sea(state, is_divergence, f_g, disparity, breadth):
    """Call Gemini 1.5 Flash for Current Sea title, desc, msg. Returns (title, desc, msg) or None. Concise prompt to minimize tokens."""
    try:
        import google.generativeai as genai
    except ImportError:
        return None
    api_key = _get_gemini_api_key()
    if not api_key:
        return None
    genai.configure(api_key=api_key)
    prompt = (
        f"State={state}, divergence={is_divergence}, FearGreed={f_g}, 200MAgap={disparity}%, Breadth={breadth}%. "
        "Reply with JSON only, no other text: {\"title\": \"Current Sea: ...\", \"desc\": \"one short sentence\", \"msg\": \"2 short sentences for long-term investors\"}. "
        "title: sea metaphor (Stormy/Steady/Overheated). desc: current market in plain language. msg: calm Bogle-style guidance."
    )
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        if not response or not response.text:
            return None
        text = response.text.strip()
        json_match = re.search(r"\{[\s\S]*\}", text)
        if json_match:
            out = json.loads(json_match.group())
            return (
                out.get("title") or "",
                out.get("desc") or "",
                out.get("msg") or "",
            )
    except Exception as e:
        print("[Gemini Current Sea] API call failed:", str(e), flush=True)
        traceback.print_exc()
    return None


@st.cache_data(ttl=7200)
def _get_current_sea_open(time_bucket_2h):
    """Current Sea during market hours: 1 call per 2h (time bucket only to avoid RPM 429)."""
    m = get_market_temperature_metrics()
    state, _, is_divergence = get_market_condition(m["fear_greed"], m["disparity_pct"], m["breadth_pct"])
    f_g_int = int(round(m["fear_greed"]))
    d, b = round(m["disparity_pct"], 1), round(m["breadth_pct"], 1)
    return _call_gemini_current_sea(state, is_divergence, f_g_int, d, b)


@st.cache_data(ttl=86400)
def _get_current_sea_closed(time_bucket_2h):
    """Current Sea when market closed: 1 call per 2h bucket until next open."""
    m = get_market_temperature_metrics()
    state, _, is_divergence = get_market_condition(m["fear_greed"], m["disparity_pct"], m["breadth_pct"])
    f_g_int = int(round(m["fear_greed"]))
    d, b = round(m["disparity_pct"], 1), round(m["breadth_pct"], 1)
    return _call_gemini_current_sea(state, is_divergence, f_g_int, d, b)


def get_current_sea_display(state, is_divergence, f_g, disparity, breadth):
    """
    Returns (title, desc, msg, theme, border_color) for the Compass Wisdom box.
    Curated content only (no AI). Uses get_state_display; adds divergence note when needed.
    """
    fallback = get_state_display(state, is_divergence)
    theme, border = fallback[3], fallback[4]
    title, desc, msg = fallback[0], fallback[1], fallback[2]
    if is_divergence:
        msg += (
            " <strong>Divergence alert:</strong> The market looks strong on the surface but is weak underneath. "
            "The index is high while the number of advancing stocks is low. Proceed with caution."
        )
    return (title, desc, msg, theme, border)


# -----------------------------------------------------------------------------
# The Weekly Signal: Macro news (Fed, inflation, recession) from yfinance Search
# → score by importance → pick 3 diverse → Gemini (gemini-2.5-flash) → Markdown table.
# Successful results cached 24h; last result (table + headlines) persisted for when Gemini is unavailable.
# -----------------------------------------------------------------------------
_weekly_signal_gemini_cache = {}  # bucket_date_str -> (markdown_table_str, timestamp)
_WEEKLY_SIGNAL_CACHE_TTL = 86400  # 24h for success
_WEEKLY_SIGNAL_LAST_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".streamlit", "weekly_signal_last.json")
_WEEKLY_SIGNAL_DEFAULT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".streamlit", "weekly_signal_default.json")

# Macro keyword weights: Fed +5, Inflation +4, Recession +4, etc. Used to score and rank news.
MACRO_KEYWORDS_WEIGHTED = [
    ("fed", 5), ("federal reserve", 5), ("rate hike", 5), ("rate cut", 5),
    ("monetary policy", 5), ("central bank", 5),
    ("inflation", 4), ("cpi", 4), ("pce", 4),
    ("recession", 4), ("gdp", 4), ("unemployment", 4),
    ("treasury", 3), ("bond yield", 3), ("10-year yield", 3),
    ("banking crisis", 3), ("debt ceiling", 3), ("credit rating", 3), ("default", 3),
    ("stock market", 2), ("s&p 500", 2), ("nasdaq", 2), ("dow", 2),
    ("earnings", 1), ("profit warning", 1),
    ("oil price", 1), ("crude oil", 1), ("geopolitical", 1), ("china economy", 1),
    ("trade war", 1), ("tariffs", 1), ("housing market", 1), ("consumer spending", 1),
]
EXCLUDE_KEYWORDS = [
    "iphone", "tesla delivery", "product launch", "quarterly sales", "stock split",
    "ceo interview", "merger talks",
]

THEME_FED = ["fed", "federal reserve", "rate hike", "rate cut", "interest rate", "monetary policy", "central bank"]
THEME_INFLATION = ["inflation", "cpi", "pce"]
THEME_RECESSION = ["recession", "gdp", "unemployment", "growth", "jobs", "employment"]


def _score_news_item(title, description=""):
    """Score by macro importance. Fed +5, Inflation +4, Recession +4, etc. Exclude keywords subtract 3."""
    text = ((title or "") + " " + (description or "")).lower()
    score = 0
    for kw, points in MACRO_KEYWORDS_WEIGHTED:
        if kw in text:
            score += points
    for kw in EXCLUDE_KEYWORDS:
        if kw in text:
            score -= 3
    return score


def _theme_of(title, description=""):
    """Return 'fed', 'inflation', 'recession', or 'other' for the item's main theme."""
    text = ((title or "") + " " + (description or "")).lower()
    if any(k in text for k in THEME_FED):
        return "fed"
    if any(k in text for k in THEME_INFLATION):
        return "inflation"
    if any(k in text for k in THEME_RECESSION):
        return "recession"
    return "other"


def _headline_significant_words(title):
    """Lowercase word set for similarity check; skip very short and numbers."""
    if not title or not isinstance(title, str):
        return set()
    words = set(re.findall(r"[a-z0-9]{3,}", (title or "").lower()))
    return words - {"the", "and", "for", "are", "but", "not", "you", "all", "can", "had", "her", "his", "was", "one", "our", "out", "day", "get", "has", "how", "its", "may", "new", "now", "old", "see", "way", "who", "did", "say", "any"}


def _headlines_too_similar(title1, title2, min_shared_ratio=0.4):
    """True if the two headlines share too many significant words (same story)."""
    w1 = _headline_significant_words(title1)
    w2 = _headline_significant_words(title2)
    if not w1 or not w2:
        return False
    shared = len(w1 & w2) / min(len(w1), len(w2))
    return shared >= min_shared_ratio


def _news_item_timestamp(item):
    """Return Unix timestamp if available (providerPublishTime, created, etc.), else None."""
    if isinstance(item, dict):
        for key in ("providerPublishTime", "provider_publish_time", "created", "published_at", "pub_date"):
            val = item.get(key)
            if val is not None:
                try:
                    return int(val) if isinstance(val, (int, float)) else None
                except (TypeError, ValueError):
                    pass
    if hasattr(item, "providerPublishTime") and item.providerPublishTime is not None:
        try:
            return int(item.providerPublishTime)
        except (TypeError, ValueError):
            pass
    return None


def _fetch_macro_news_candidates():
    """
    Fetch macro/economy news (Fed, inflation, recession, etc.) via yfinance Search.
    Prefer items from the past 7 days when date is available. Returns list of dicts with title, description, optional ts.
    If Search returns nothing, fallback: fetch from SPY/QQQ.
    """
    try:
        import yfinance as yf
    except ImportError:
        return []
    cutoff_ts = (datetime.now() - timedelta(days=7)).timestamp()
    seen = set()
    out = []
    search_queries = [
        "Fed interest rate",
        "Federal Reserve economy",
        "inflation economy",
        "CPI inflation",
        "recession GDP",
        "stock market economy",
    ]
    for query in search_queries:
        try:
            if hasattr(yf, "Search"):
                search = yf.Search(query, news_count=12)
                news_list = getattr(search, "news", None) or []
                if callable(news_list):
                    news_list = news_list() or []
            else:
                news_list = []
            for item in (news_list or [])[:12]:
                if isinstance(item, dict):
                    title = (item.get("title") or item.get("headline") or "").strip()
                    desc = (item.get("summary") or item.get("description") or "").strip()
                    ts = _news_item_timestamp(item)
                else:
                    title = (getattr(item, "title", None) or getattr(item, "headline", None) or "").strip() if item else ""
                    desc = (getattr(item, "summary", None) or getattr(item, "description", None) or "").strip() if item else ""
                    ts = _news_item_timestamp(item) if item else None
                if not title or title in seen:
                    continue
                if ts is not None and ts < cutoff_ts:
                    continue
                seen.add(title)
                out.append({"title": title, "description": desc, "ts": ts})
                if len(out) >= 25:
                    break
        except Exception:
            pass
        if len(out) >= 25:
            break
    if not out:
        for ticker_symbol in ("SPY", "QQQ"):
            try:
                t = yf.Ticker(ticker_symbol)
                news = getattr(t, "news", None) or []
                for n in (news or [])[:10]:
                    if isinstance(n, dict):
                        title = (n.get("title") or n.get("headline") or "").strip()
                        desc = (n.get("summary") or n.get("description") or "").strip()
                        ts = _news_item_timestamp(n)
                    else:
                        title = (getattr(n, "title", None) or getattr(n, "headline", None) or "").strip() if n else ""
                        desc = (getattr(n, "summary", None) or getattr(n, "description", None) or "").strip() if n else ""
                        ts = _news_item_timestamp(n) if n else None
                    if not title or title in seen:
                        continue
                    if ts is not None and ts < cutoff_ts:
                        continue
                    seen.add(title)
                    out.append({"title": title, "description": desc, "ts": ts})
            except Exception:
                pass
    return out[:25]


def _filter_news_macro_scored(news_items, max_items=12, min_score=0):
    """Keep only macro-relevant news; sort by score descending; return top max_items."""
    if not news_items:
        return []
    scored = []
    for it in news_items:
        s = _score_news_item(it.get("title") or "", it.get("description") or "")
        if s >= min_score:
            scored.append((s, it))
    scored.sort(reverse=True, key=lambda x: x[0])
    return [entry for _, entry in scored[:max_items]]


def _pick_diverse_three(news_items):
    """
    Pick 3 items so the reader sees different topics: 1 Fed-related, 1 inflation-related, 1 recession/growth-related.
    Avoid picking two headlines that are the same story (similar wording). Ensures 3 distinct subjects.
    """
    if not news_items:
        return []
    if len(news_items) <= 3:
        return list(news_items[:3])
    scored = [(_score_news_item(it.get("title") or "", it.get("description") or ""), it) for it in news_items]
    by_theme = {"fed": [], "inflation": [], "recession": [], "other": []}
    for score, it in scored:
        theme = _theme_of(it.get("title") or "", it.get("description") or "")
        by_theme[theme].append((score, it))
    for t in ("fed", "inflation", "recession", "other"):
        by_theme[t].sort(reverse=True, key=lambda x: x[0])
    out = []
    for theme in ("fed", "inflation", "recession"):
        if by_theme[theme]:
            out.append(by_theme[theme][0][1])
    while len(out) < 3 and by_theme["other"]:
        out.append(by_theme["other"].pop(0)[1])
    for theme in ("fed", "inflation", "recession"):
        while len(out) < 3 and len(by_theme[theme]) > 1:
            out.append(by_theme[theme].pop(1)[1])
    out = out[:3]
    pool = [it for _, theme_list in by_theme.items() for _, it in theme_list if it not in out]
    while True:
        changed = False
        for i, j in ((0, 1), (0, 2), (1, 2)):
            t1 = (out[i].get("title") or "").strip()
            t2 = (out[j].get("title") or "").strip()
            if _headlines_too_similar(t1, t2):
                other_idx = 3 - i - j
                for repl in pool:
                    rt = (repl.get("title") or "").strip()
                    if _headlines_too_similar(rt, t1) or _headlines_too_similar(rt, (out[other_idx].get("title") or "").strip()):
                        continue
                    out[j] = repl
                    pool = [x for x in pool if x != repl]
                    changed = True
                    break
            if changed:
                break
        if not changed:
            break
    return out[:3]


def _weekly_signal_bucket_date_et():
    """Return the date (ET) for which we show the weekly signal: today if >= 7 PM ET, else yesterday. Fetches once per day at 7 PM ET."""
    et = ZoneInfo("America/New_York")
    now = datetime.now(et)
    if now.hour >= 19:
        return now.date()
    return (now - timedelta(days=1)).date()


def get_weekly_signal_headlines():
    """
    Fetch and return the 3 headline strings used for Weekly Signal (no Gemini).
    Used when building the prompt and for saving to file (headlines shown only in the table Headline column).
    """
    candidates = _fetch_macro_news_candidates()
    news = _filter_news_macro_scored(candidates, max_items=12, min_score=0)
    if not news:
        news = candidates[:12]
    picked = _pick_diverse_three(news)
    if not picked:
        return ["Market update (no headlines fetched)", "Economic data (no headlines fetched)", "Fed policy (no headlines fetched)"]
    headlines = [(p.get("title") or "").strip() or "—" for p in picked[:3]]
    while len(headlines) < 3:
        headlines.append("—")
    return headlines[:3]


def get_weekly_signal_gemini_table(bucket_date_str):
    """
    Fetch macro news → pick 3 diverse → send to Gemini. Returns (markdown_table_str, error_msg, headlines, success_ts).
    success_ts = Unix timestamp when table was last generated (from cache or API); None if failed. headlines = list of 3 strings.
    """
    now_ts = time.time()
    cached = _weekly_signal_gemini_cache.get(bucket_date_str)
    if cached and (now_ts - cached[1]) < _WEEKLY_SIGNAL_CACHE_TTL:
        return (cached[0], None, cached[2] if len(cached) > 2 else [], cached[1])
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
    except Exception:
        api_key = (st.secrets.get("GEMINI_API_KEY") or "").strip()
    if not api_key or not str(api_key).strip():
        return (None, "No GEMINI_API_KEY in .streamlit/secrets.toml", [], None)
    candidates = _fetch_macro_news_candidates()
    news = _filter_news_macro_scored(candidates, max_items=12, min_score=0)
    if not news:
        news = candidates[:12]
    picked = _pick_diverse_three(news)
    if not picked:
        # No news from yfinance: still ask Gemini for a short generic table so the section isn't blank
        headlines = ["Market update (no headlines fetched)", "Economic data (no headlines fetched)", "Fed policy (no headlines fetched)"]
    else:
        headlines = [(p.get("title") or "").strip() or "—" for p in picked[:3]]
    while len(headlines) < 3:
        headlines.append("—")
    headlines = headlines[:3]

    # Save headlines immediately so they stay visible even if Gemini fails (e.g. 7 PM run, Gemini down).
    try:
        with open(_WEEKLY_SIGNAL_LAST_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "bucket_str": bucket_date_str,
                "headlines": headlines,
                "saved_at": datetime.now(ZoneInfo("America/New_York")).isoformat(),
            }, f, ensure_ascii=False)
    except Exception:
        pass

    system_prompt = (
        "You are a Boglehead advisor. Categorize the following 3 news headlines as [Signal] or [Noise]. "
        "Provide advice suitable for long-term investors with a diversified stock and bond allocation (do not assume or mention any specific ratio like 60/40). Follow John Bogle's principles. Keep it extremely brief. "
        "Output ONLY a Markdown table with no other text."
    )
    user_prompt = (
        "The table must be in English and have exactly 3 columns:\n"
        "| Category (Signal/Noise) | Headline | Compass View |\n\n"
        "Headlines:\n1. " + headlines[0] + "\n2. " + headlines[1] + "\n3. " + headlines[2]
    )
    def _extract_text(resp):
        if not resp:
            return None
        t = getattr(resp, "text", None)
        if t and str(t).strip():
            return str(t).strip()
        # Fallback: candidates[0].content.parts[0].text (e.g. blocked or different SDK version)
        try:
            cands = getattr(resp, "candidates", None) or []
            if cands and len(cands) > 0:
                c = cands[0]
                content = getattr(c, "content", None)
                if content:
                    parts = getattr(content, "parts", None) or []
                    if parts and len(parts) > 0:
                        p = parts[0]
                        pt = getattr(p, "text", None)
                        if pt and str(pt).strip():
                            return str(pt).strip()
        except Exception:
            pass
        return None

    last_error = None
    # Use only 2.x Flash models (2.5 first, then 2.0). Do not use 1.5 — they often 404.
    for model_name in ("gemini-2.5-flash", "gemini-2.0-flash"):
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key.strip())
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(system_prompt + "\n\n" + user_prompt)
            text = _extract_text(response)
            if text and "|" in text:
                _weekly_signal_gemini_cache[bucket_date_str] = (text, now_ts, headlines)
                try:
                    with open(_WEEKLY_SIGNAL_LAST_FILE, "w", encoding="utf-8") as f:
                        json.dump({
                            "bucket_str": bucket_date_str,
                            "table_md": text,
                            "headlines": headlines,
                            "saved_at": datetime.now(ZoneInfo("America/New_York")).isoformat(),
                        }, f, ensure_ascii=False)
                except Exception:
                    pass
                return (text, None, headlines, now_ts)
        except Exception as e:
            last_error = str(e) or type(e).__name__
            continue
    return (None, last_error or "Gemini returned no table", headlines, None)


def _load_last_weekly_signal():
    """
    Load the last Weekly Signal from disk (table + headlines). If no saved run exists, load default
    so the deployed app always shows something (e.g. first deploy or after restart).
    Returns (table_md or None, saved_at_iso, headlines). headlines = list of up to 3 strings.
    """
    def _read_file(path):
        try:
            if not path or not os.path.isfile(path):
                return (None, None, [])
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            table_md = (data.get("table_md") or "").strip()
            if table_md and "|" not in table_md:
                table_md = None
            saved_at = data.get("saved_at") or ""
            headlines = data.get("headlines")
            if not isinstance(headlines, list) or len(headlines) < 3:
                headlines = []
            else:
                headlines = [str(h) for h in headlines[:3]]
            return (table_md if table_md else None, saved_at, headlines)
        except Exception:
            return (None, None, [])

    last_md, saved_at, headlines = _read_file(_WEEKLY_SIGNAL_LAST_FILE)
    if last_md or (saved_at and headlines):
        return (last_md, saved_at, headlines)
    # No saved run (e.g. first deploy, or ephemeral server): use default so something is always shown
    return _read_file(_WEEKLY_SIGNAL_DEFAULT_FILE)


def _test_gemini_connection_sdk():
    """Test 2: Use Google's Python SDK (google-generativeai). Same key, different path."""
    api_key = _get_gemini_api_key()
    if not api_key or not str(api_key).strip():
        return "Failed: No GEMINI_API_KEY in .streamlit/secrets.toml"
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key.strip())
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content("Who is John Bogle? Reply in one sentence only. English.")
        if not response or not getattr(response, "text", None):
            return "Failed: SDK returned no text"
        text = (response.text or "").strip()[:300]
        if not text:
            return "Failed: SDK returned empty text"
        return f"OK (SDK): {text}"
    except Exception as e:
        return f"Failed (SDK): {e}"


# Guru's Wisdom: use gemini-2.5-flash. Try new SDK (google-genai) first, then fallback to google-generativeai.
def _call_gemini_guru(state, is_divergence, f_g, disparity, breadth):
    """Calls Gemini API. Returns (msg, author) or None. Raises on API errors (401, 403, 429) so caller can st.error(e)."""
    api_key = _get_gemini_api_key()
    if not api_key:
        return None
    prompt = (
        f"You are a wise investment guru like John Bogle. Based on these 3 metrics (Fear&Greed: {f_g}, 200MA Gap: {disparity}%, Breadth: {breadth}%), "
        "provide 2 lines of psychological guidance for a long-term investor. Speak in a calm and encouraging tone. "
        "Reply with JSON only: {\"msg\": \"your 2 lines here\"}."
    )

    # 1) Try new official SDK (google-genai). Free tier: gemini-2.5-flash only.
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        text = None
        if response:
            text = getattr(response, "text", None)
            if not text and getattr(response, "candidates", None):
                c = response.candidates[0]
                if getattr(c, "content", None) and getattr(c.content, "parts", None) and c.content.parts:
                    text = getattr(c.content.parts[0], "text", None)
        if text and text.strip():
            return _parse_guru_json(text.strip())
        _raise_or_log_empty(response, "google-genai")
    except ImportError:
        pass
    except Exception:
        raise

    # 2) Fallback to legacy SDK (google-generativeai)
    try:
        import google.generativeai as genai_legacy
    except ImportError:
        return None
    genai_legacy.configure(api_key=api_key)
    model = genai_legacy.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content(prompt)
    if not response:
        print("[Gemini Guru] Legacy API returned None.", flush=True)
        return None
    text = getattr(response, "text", None)
    if text and text.strip():
        return _parse_guru_json(text.strip())
    _raise_or_log_empty(response, "google-generativeai")
    return None


def _parse_guru_json(text):
    """Parse JSON from guru response. Returns (msg, author) or raises."""
    json_match = re.search(r"\{[\s\S]*\}", text)
    if not json_match:
        raise ValueError(f"API response had no JSON. First 200 chars: {text[:200]!r}")
    out = json.loads(json_match.group())
    msg = (out.get("msg") or "").strip()
    author = (out.get("author") or "").strip()
    if not msg:
        raise ValueError(f"API JSON had empty 'msg'. Response: {text[:200]!r}")
    return (msg, author)


def _raise_or_log_empty(response, sdk_name):
    """Raise with details when response has no text, so user sees 403/block reason etc."""
    err_parts = [f"[{sdk_name}] API returned no text"]
    try:
        if response and hasattr(response, "prompt_feedback") and response.prompt_feedback:
            err_parts.append(f"prompt_feedback={response.prompt_feedback}")
        if response and getattr(response, "candidates", None) and len(response.candidates) > 0:
            c = response.candidates[0]
            if getattr(c, "finish_reason", None):
                err_parts.append(f"finish_reason={c.finish_reason}")
            if getattr(c, "safety_ratings", None):
                err_parts.append(f"safety_ratings={c.safety_ratings}")
    except Exception:
        pass
    msg = " ".join(str(x) for x in err_parts)
    print("[Gemini Guru]", msg, flush=True)
    raise RuntimeError(msg)


@st.cache_data(ttl=7200)
def _get_guru_wisdom_open(time_bucket_2h, retry=0):
    """Guru wisdom during market hours: 1 call per 2h (cache key = time bucket only to avoid RPM 429)."""
    m = get_market_temperature_metrics()
    state, _, is_divergence = get_market_condition(m["fear_greed"], m["disparity_pct"], m["breadth_pct"])
    f_g_int = int(round(m["fear_greed"]))
    d, b = round(m["disparity_pct"], 1), round(m["breadth_pct"], 1)
    return _call_gemini_guru(state, is_divergence, f_g_int, d, b)


@st.cache_data(ttl=86400)
def _get_guru_wisdom_closed(time_bucket_2h, retry=0):
    """Guru wisdom when market closed: 1 call per 2h bucket until next open."""
    m = get_market_temperature_metrics()
    state, _, is_divergence = get_market_condition(m["fear_greed"], m["disparity_pct"], m["breadth_pct"])
    f_g_int = int(round(m["fear_greed"]))
    d, b = round(m["disparity_pct"], 1), round(m["breadth_pct"], 1)
    return _call_gemini_guru(state, is_divergence, f_g_int, d, b)


# -----------------------------------------------------------------------------
# Gurus' Beacon: 15 curated quotes (Current Sea & Compass Wisdom).
# COLD = fear/downturn, NEUTRAL = calm/steady, HOT = euphoria/overheated.
# random.choice() so a different quote appears on each refresh.
# -----------------------------------------------------------------------------
QUOTES_BY_STATE = {
    "COLD": [
        ("In the storm of the market, the safest action you can take is to do nothing. Stay the course.", "John Bogle"),
        ("Predicting rain doesn't matter. Building the ark does.", "Warren Buffett"),
        ("Those who have no stocks in a downturn will have no stocks in an upturn. Conviction investors act contrary to the crowd.", "André Kostolany"),
        ("A downturn is an opportunity to stop pulling flowers and watering weeds, and to hold more of the best companies.", "Peter Lynch"),
        ("Panicking over falling stock prices is proof that you lack principles. Composure is skill.", "Charlie Munger"),
    ],
    "NEUTRAL": [
        ("Investing should be like watching paint dry or grass grow. Enjoy the boredom.", "Paul Samuelson"),
        ("Don't try to beat the market's randomness. Cut costs, diversify widely, and wait for time.", "Burton Malkiel"),
        ("Don't get carried away by small events. In 100 years of capitalism, today is just a tiny dot.", "Ray Dalio"),
        ("Don't bother looking for the needle in the haystack. Just buy the haystack (the whole market).", "John Bogle"),
        ("The four pillars of successful investing are discipline, diversification, rebalancing, and cost control. Stick to the basics.", "William Bernstein"),
    ],
    "HOT": [
        ("The most dangerous asset is one everyone believes in so much that the price is too high. Check your life jacket now.", "Howard Marks"),
        ("Be fearful when others are greedy, and greedy when others are fearful.", "Warren Buffett"),
        ("Stand near the exit when the party is hot. The crowd's euphoria is when it's most dangerous.", "André Kostolany"),
        ("Following the crowd is just reversion to the mean. When everyone is excited, you must keep the coolest head.", "Charlie Munger"),
        ("When debt grows faster than income and asset values soar, the compass points to danger. Time to return to principles.", "Ray Dalio"),
    ],
}


# Flat list of all guru quotes for "Tip of the day" (one per day, rotated by date).
TIP_QUOTES_DAILY = [
    (q, a) for quotes_list in QUOTES_BY_STATE.values() for (q, a) in quotes_list
]


def get_tip_of_the_day():
    """Return one (text, author) quote for Tip of the day. Same quote for the whole day (ET)."""
    if not TIP_QUOTES_DAILY:
        return ("Stay the course.", "The Steady Compass")
    et = ZoneInfo("America/New_York")
    day_str = datetime.now(et).strftime("%Y-%m-%d")
    idx = hash(day_str) % len(TIP_QUOTES_DAILY)
    return TIP_QUOTES_DAILY[idx]


def _get_curated_guru_quotes(f_g, disparity, breadth, count=1):
    """
    Use random.choice() so a different quote is displayed each time the page is refreshed.
    Categorized by market state (COLD / NEUTRAL / HOT). Returns (list of (text, author), state).
    """
    state, _, _ = get_market_condition(f_g, disparity, breadth)
    pool = QUOTES_BY_STATE.get(state, QUOTES_BY_STATE["NEUTRAL"])
    n = min(count, len(pool))
    if n == 1:
        chosen = [random.choice(pool)]
    else:
        chosen = random.sample(pool, n)
    return (list(chosen), state)


def get_guru_wisdom(f_g, disparity, breadth):
    """
    Gurus' Beacon: curated quotes only (no AI). Returns (quotes_list, is_weekend_style, state).
    state = "COLD" | "NEUTRAL" | "HOT" for styling; None when weekend.
    """
    return get_guru_wisdom_message(f_g, disparity, breadth)


def generate_guru_wisdom(f_g, disparity, breadth):
    """Alias for get_guru_wisdom."""
    return get_guru_wisdom(f_g, disparity, breadth)


def get_guru_wisdom_message(f_g, disparity, breadth):
    """
    Curated quotes from QUOTES_BY_STATE. Returns (quotes_list, is_weekend_style, state).
    One quote per load (random.choice) for COLD/NEUTRAL/HOT; state used for background color.
    """
    now_et = datetime.now(ET)
    if is_weekend_or_holiday(now_et):
        return (
            [
                (
                    "The market is resting today. Step away from the numbers and spend time with what matters—"
                    "your mental muscles will thank you.",
                    "",
                )
            ],
            True,
            None,
        )
    quotes, state = _get_curated_guru_quotes(f_g, disparity, breadth, count=1)
    return (quotes, False, state)


# -----------------------------------------------------------------------------
# Top nav (fixed on all pages) + redirect from query params
# -----------------------------------------------------------------------------
inject_nav_css()
maybe_redirect_from_query("HOME")
render_nav("HOME")


# -----------------------------------------------------------------------------
# HOME page: no sidebar, dashboard with 1DAY / PERFORMANCES tabs
# -----------------------------------------------------------------------------
def home_page():
    # Breadcrumb in main content (same position as on Market for consistent feel)
    st.markdown(
        '<div class="content-breadcrumb" aria-label="You are here">Home</div>',
        unsafe_allow_html=True,
    )
    # Tip of the day: one Gurus' Beacon quote, rotated by day (ET)
    tip_text, tip_author = get_tip_of_the_day()
    tip_author_line = f" — {tip_author}" if tip_author else ""
    st.markdown(
        '<div class="tip-of-the-day-box" style="background:#f0f9ff; border:1px solid #bae6fd; border-radius:8px; padding:0.6rem 1rem; margin-bottom:1rem; font-size:0.9rem;">'
        '<strong>Tip of the day</strong>: '
        f'"{tip_text}"{tip_author_line}'
        "</div>",
        unsafe_allow_html=True,
    )
    # Section titles use .section-heading (defined in components/nav.py) for consistent size across the site
    st.markdown('<div class="section-heading">Today\'s Market Dashboard</div>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["1DAY", "PERFORMANCES"])

    with tab1:
        # Auto-update 1DAY data every 10 min
        if st_autorefresh is not None:
            st_autorefresh(interval=600_000, key="1day_autorefresh")
        with st.spinner("Loading market data…"):
            df_1d = get_1day_data()
        # Column order: Ticker, Chg (%), this month (%), last month (%), Time ET
        display_cols = list(df_1d.columns)
        df_display = df_1d[display_cols].copy()
        col_ticker, col_chg = display_cols[0], display_cols[1]
        col_this_month = display_cols[2]
        col_last_month = display_cols[3]
        col_time = display_cols[4]

        # Tooltip: short column guide (English only)
        with st.expander("What do these columns mean?", expanded=False):
            st.markdown(
                "- **Ticker:** ETF symbol.  "
                "- **Chg (%):** Day-over-day price change (vs. previous close).  "
                f"- **{col_this_month}:** Month-to-date return (from first trading day of the month).  "
                f"- **{col_last_month}:** Full previous month return.  "
                "- **Time ET:** Data timestamp (Eastern Time)."
            )
        # Data-as-of + "Return (%)" label above table
        time_et_str = str(df_display[col_time].iloc[0]) if len(df_display) > 0 else "—"
        _c_left, _c_right = st.columns([3, 1])
        with _c_left:
            st.caption(f"**Data as of:** {time_et_str}")
        with _c_right:
            st.markdown(
                '<div style="text-align:right; font-weight:600; font-size:0.95rem; color:#475569; margin-top:0; margin-bottom:4px;">Return (%)</div>',
                unsafe_allow_html=True,
            )

        def _pct_style(val):
            if val is None or (isinstance(val, float) and pd.isna(val)):
                return ""
            try:
                v = float(val)
                if v > 0:
                    return "color:#0d7a4a;font-weight:500;"
                if v < 0:
                    return "color:#c0392b;font-weight:500;"
            except (TypeError, ValueError):
                pass
            return ""

        def _pct_fmt(val):
            if val is None or (isinstance(val, float) and pd.isna(val)):
                return "—"
            try:
                return f"{float(val):.2f}%"
            except (TypeError, ValueError):
                return str(val)

        # Build HTML table; single header row (Return % is outside table, above)
        table_css = (
            "width:100%; border-collapse:collapse; font-size:0.9rem; "
            "margin-bottom:0.5rem;"
        )
        head_css = "text-align:left; padding:6px 8px; border-bottom:1px solid #e2e8f0; background:#f8fafc; font-weight:600;"
        cell_css = "padding:6px 8px; border-bottom:1px solid #e2e8f0;"
        html_rows = [
            '<div class="responsive-table-wrap">',
            f"<table style='{table_css}'><thead><tr>",
            f"<th style='{head_css}'>{col_ticker}</th>",
            f"<th style='{head_css}'>{col_chg}</th>",
            f"<th style='{head_css}'>{col_this_month}</th>",
            f"<th style='{head_css}'>{col_last_month}</th>",
            f"<th style='{head_css}'>{col_time}</th>",
            "</tr></thead><tbody>",
        ]
        for _, row in df_display.iterrows():
            s_chg = _pct_style(row[col_chg])
            s_this = _pct_style(row[col_this_month])
            s_last = _pct_style(row[col_last_month])
            html_rows.append("<tr>")
            html_rows.append(f"<td style='{cell_css}'>{row[col_ticker]}</td>")
            html_rows.append(f"<td style='{cell_css};{s_chg}'>{_pct_fmt(row[col_chg])}</td>")
            html_rows.append(f"<td style='{cell_css};{s_this}'>{_pct_fmt(row[col_this_month])}</td>")
            html_rows.append(f"<td style='{cell_css};{s_last}'>{_pct_fmt(row[col_last_month])}</td>")
            html_rows.append(f"<td style='{cell_css}'>{row[col_time]}</td>")
            html_rows.append("</tr>")
        html_rows.append("</tbody></table></div>")
        st.markdown("".join(html_rows), unsafe_allow_html=True)
        st.caption(
            "1DAY: Live from Yahoo Finance (auto-updates every 10 minutes). "
            "Eastern Time (ET). Some ETCs can be affected by contango/backwardation."
        )
        st.caption("**—** = data temporarily unavailable for that ticker.")

    with tab2:
        with st.spinner("Loading performance data…"):
            df_perf = get_performances_data()
        perf_cols = ["1M", "3M", "6M", "1Y", "3Y", "5Y", "10Y"]
        display_perf = ["Ticker"] + perf_cols + ["Time ET"]
        df_perf_display = df_perf[display_perf].copy()

        # Tooltip: column guide for PERFORMANCES
        with st.expander("What do these columns mean?", expanded=False):
            st.markdown(
                "- **Ticker:** ETF symbol.  "
                "- **1M, 3M, 6M, 1Y, 3Y, 5Y, 10Y:** Total return over that period (e.g. 1M = last 1 month, 1Y = last 1 year).  "
                "- **Time ET:** Data timestamp (Eastern Time)."
            )
        # Data as of
        perf_time_str = str(df_perf_display["Time ET"].iloc[0]) if len(df_perf_display) > 0 else "—"
        st.caption(f"**Data as of:** {perf_time_str}")
        # "Return (%)" at top right above table (same as 1DAY)
        _p_left, _p_right = st.columns([3, 1])
        with _p_right:
            st.markdown(
                '<div style="text-align:right; font-weight:600; font-size:0.95rem; color:#475569; margin-top:0; margin-bottom:4px;">Return (%)</div>',
                unsafe_allow_html=True,
            )

        def color_perf(val):
            if val is None or pd.isna(val):
                return ""
            if val > 0:
                return "color: #0d7a4a; font-weight: 500;"
            if val < 0:
                return "color: #c0392b; font-weight: 500;"
            return ""

        def perf_fmt(val):
            if val is None or (isinstance(val, float) and pd.isna(val)):
                return "—"
            try:
                return f"{float(val):.1f}%"
            except (TypeError, ValueError):
                return str(val)

        # Same HTML table styling as 1DAY for consistent header/cell look
        table_css = (
            "width:100%; border-collapse:collapse; font-size:0.9rem; "
            "margin-bottom:0.5rem;"
        )
        head_css = "text-align:left; padding:6px 8px; border-bottom:1px solid #e2e8f0; background:#f8fafc; font-weight:600;"
        cell_css = "padding:6px 8px; border-bottom:1px solid #e2e8f0;"
        perf_html = [
            '<div class="responsive-table-wrap">',
            f"<table style='{table_css}'><thead><tr>",
            f"<th style='{head_css}'>Ticker</th>",
        ]
        for c in perf_cols:
            perf_html.append(f"<th style='{head_css}'>{c}</th>")
        perf_html.append(f"<th style='{head_css}'>Time ET</th>")
        perf_html.append("</tr></thead><tbody>")
        for _, row in df_perf_display.iterrows():
            perf_html.append("<tr>")
            perf_html.append(f"<td style='{cell_css}'>{row['Ticker']}</td>")
            for c in perf_cols:
                s = color_perf(row[c])
                perf_html.append(f"<td style='{cell_css};{s}'>{perf_fmt(row[c])}</td>")
            perf_html.append(f"<td style='{cell_css}'>{row['Time ET']}</td>")
            perf_html.append("</tr>")
        perf_html.append("</tbody></table></div>")
        st.markdown("".join(perf_html), unsafe_allow_html=True)
        st.caption("Period return (%). 1M=last 1 month, 3M=last 3 months, etc. USD. Some ETCs can suffer by contango/backwardation.")
        st.caption("**—** = data temporarily unavailable for that ticker.")

    # ----- Shared below both tabs: Market Temperature, Gurus' Beacon, Current Sea -----
    st.divider()
    m = get_market_temperature_metrics()
    state, zones, is_divergence = get_market_condition(
        m["fear_greed"], m["disparity_pct"], m["breadth_pct"]
    )
    title, desc, msg, theme, border_color = get_current_sea_display(
        state, is_divergence, m["fear_greed"], m["disparity_pct"], m["breadth_pct"]
    )
    zone_colors = {"bad": "#3b82f6", "neutral": "#059669", "good": "#ea580c"}
    st.markdown(
        "<style>"
        ".gauge-header-block { font-size: 0.78rem !important; line-height: 1.35 !important; "
        "height: 3.6em !important; min-height: 3.6em !important; margin-bottom: 0 !important; "
        "box-sizing: border-box; display: block !important; text-align: center !important; } "
        "[data-testid='column'] { align-self: flex-start !important; } "
        "</style>",
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="section-heading">Market Temperature</div>',
        unsafe_allow_html=True,
    )
    state_short = {"COLD": "Bad (Stormy)", "NEUTRAL": "Neutral (Steady)", "HOT": "Good/Overheated"}
    st.markdown(
        f'<p style="margin-bottom: 0.5rem;">'
        f'<strong>Current market:</strong> <span style="color:{border_color}; font-weight:600;">{state_short.get(state, state)}</span>'
        f'{" · <span style=\"color:#b45309;\">Divergence warning</span>" if is_divergence else ""}'
        f'</p>',
        unsafe_allow_html=True,
    )
    gauge_header_css = "gauge-header-block"
    gauge_config = {"displayModeBar": False, "scrollZoom": False}
    c1, c2, c3 = st.columns(3)

    with c1:
        vix_val = m["vix_value"]
        vix_state = m["vix_state"]
        vix_emoji = {"Calm": "🟢", "Normal": "🟡", "Anxious": "🟠", "Extreme Fear": "🔴"}.get(vix_state, "🟡")
        vix_colors = {"Calm": "#22c55e", "Normal": "#eab308", "Anxious": "#f97316", "Extreme Fear": "#ef4444"}
        vix_color = vix_colors.get(vix_state, "#64748b")
        st.markdown(
            f'<div class="{gauge_header_css}">'
            f'<span style="font-weight:600;">Market Volatility (VIX)</span> · <span style="font-weight:600;">{vix_state}</span><br>'
            f'<span style="color:{vix_color}; font-size:0.95em;">(&lt;15=Calm, 15–20=Normal, 20–30=Anxious, &gt;30=Extreme Fear)</span></div>',
            unsafe_allow_html=True,
        )
        vix_gauge_val = max(0, min(50, vix_val))
        fig1 = make_gauge_figure(
            vix_gauge_val,
            [0, 50],
            [(15, "#86efac"), (20, "#fde047"), (30, "#fdba74"), (50, "#fca5a5")],
            "VIX (CBOE Volatility Index)",
        )
        if fig1:
            st.plotly_chart(fig1, use_container_width=True, config=gauge_config)
        else:
            st.metric("VIX", f"{vix_val:.2f}")
            st.caption(f"{vix_emoji} {vix_state}")

    with c2:
        z = zones["disparity"]
        st.markdown(
            f'<div class="{gauge_header_css}">'
            f'<span style="font-weight:600;">200-Day Disparity (S&P 500)</span> · <span style="font-weight:600;">{zone_label(z, "disparity")}</span><br>'
            f'<span style="color:{zone_colors[z]}; font-size:0.95em;">(≤-5%=Weak, -5% to +8%=Normal, &gt;+8%=Overextended)</span></div>',
            unsafe_allow_html=True,
        )
        disp_val = max(-10, min(15, m["disparity_pct"]))
        fig2 = make_gauge_figure(
            disp_val,
            [-10, 15],
            [(-5, "#bfdbfe"), (8, "#d1fae5"), (15, "#fed7aa")],
            "S&P 500 % vs 200-day MA",
            number_suffix="%",
        )
        if fig2:
            st.plotly_chart(fig2, use_container_width=True, config=gauge_config)
        else:
            st.metric("S&P 500 vs 200MA", f"{m['disparity_pct']:+.1f}%")
            st.progress((m["disparity_pct"] + 10) / 25.0)

    with c3:
        z = zones["breadth"]
        breadth_ok = m.get("breadth_available", False)
        breadth_label = m.get("breadth_label", "") or "S&P 100 large-cap"
        if breadth_ok:
            title_line = f'<span style="font-weight:600;">Market Breadth ({breadth_label})</span> · <span style="font-weight:600;">{zone_label(z, "breadth")}</span><br>'
            sub_line = f'<span style="color:{zone_colors[z]}; font-size:0.95em;">(&lt;30%=Few advancing, 30–70%=Normal, &gt;70%=Broad advance)</span>'
        else:
            title_line = f'<span style="font-weight:600;">Market Breadth</span> · <span style="font-weight:600;">N/A</span><br>'
            sub_line = '<span style="color:#94a3b8; font-size:0.9em;">(Data unavailable)</span>'
        st.markdown(
            f'<div class="{gauge_header_css}">'
            f'{title_line}'
            f'{sub_line}</div>',
            unsafe_allow_html=True,
        )
        fig3 = make_gauge_figure(
            m["breadth_pct"],
            [0, 100],
            [(30, "#bfdbfe"), (70, "#d1fae5"), (100, "#fed7aa")],
            f"% above 200MA ({breadth_label})" if breadth_ok else "N/A",
            number_suffix="%",
        )
        if fig3:
            st.plotly_chart(fig3, use_container_width=True, config=gauge_config)
        else:
            st.metric("% above 200MA", f"{m['breadth_pct']:.1f}%" if breadth_ok else "N/A")
            if breadth_ok:
                st.progress(m["breadth_pct"] / 100.0)
            else:
                st.caption("Breadth data unavailable.")

    st.markdown(
        '<div style="margin-top: -2rem;"><hr style="margin: 0; padding: 0; border: none; border-top: 1px solid #e2e8f0;"></div>',
        unsafe_allow_html=True,
    )

    box_bg, box_border = "#ffffff", "#e2e8f0"
    guru_quotes, _, _ = get_guru_wisdom(m["fear_greed"], m["disparity_pct"], m["breadth_pct"])
    parts = []
    for text, author in guru_quotes:
        initial = (author[0].upper() if author else "?")
        author_badge = (
            f'<span style="display:inline-block; width:26px; height:26px; border-radius:50%; background:#e2e8f0; '
            'color:#475569; font-size:0.7rem; font-weight:700; line-height:26px; text-align:center; '
            'vertical-align:middle; margin-right:8px;">{}</span>'
            '<span style="font-size:0.9em; font-weight:700; color:#334155; letter-spacing:0.03em; font-family:Georgia,\'Times New Roman\',serif;">{}</span>'
        ).format(initial, author or "")
        block = (
            f'<div style="margin-bottom:0.5rem; text-align:left;">'
            f'<div style="margin-bottom:0.15rem;">{author_badge}</div>'
            f'<div style="color:#334155; padding-left:34px; font-style:italic;">"{text}"</div>'
            f'</div>'
        )
        parts.append(block)
    content = "".join(parts)
    support_line = (
        '<p style="font-size:0.8rem; color:#94a3b8; margin-top:0.6rem; margin-bottom:0;">'
        "The Steady Compass is rooting for your peace of mind.</p>"
    )
    st.markdown(
        f'<div style="background: {box_bg}; border: 1px solid {box_border}; border-radius: 12px; '
        'padding: 0.75rem 1rem; margin-top: 1rem; font-size: 0.95rem; line-height: 1.4; '
        'box-shadow: 0 1px 3px rgba(0,0,0,0.06);">'
        f'<div style="text-align: center; margin-bottom:0.35rem;"><strong>🧭 Gurus\' Beacon</strong></div>'
        f"{content}"
        f"{support_line}</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        f'<div style="background: {box_bg}; border: 2px solid {box_border}; border-radius: 10px; '
        'padding: 0.75rem 1rem; margin-top: 1rem; color: #1f2937; font-size: 0.95rem; line-height: 1.4;">'
        f'<div style="text-align: center; margin-bottom:0.35rem;"><strong>🧭 {title}</strong></div>'
        f'<em>{desc}</em><br>'
        f'<div style="margin-top:0.4rem;"><strong>Compass Wisdom:</strong> {msg}</div></div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div style="margin-top: 1rem;"><hr style="margin: 0; padding: 0; border: none; border-top: 1px solid #e2e8f0;"></div>',
        unsafe_allow_html=True,
    )

    # ----- The Weekly Signal: one box (header + table), VOO headlines + Gemini, cached 24h -----
    bucket_date = _weekly_signal_bucket_date_et()
    bucket_str = bucket_date.isoformat() + "_gemini_v1"
    start_str = (bucket_date - timedelta(days=6)).strftime("%b %d")
    end_str = bucket_date.strftime("%b %d, %Y")
    ws_title = "The Weekly Signal"
    ws_date_range = f"{start_str} – {end_str}"
    edition_str = bucket_date.strftime("%b %d, %Y") + " · 7 PM ET"
    ws_table_css = (
        "<style>"
        ".weekly-signal-table-wrap table { table-layout: fixed !important; width: 100% !important; } "
        ".weekly-signal-table-wrap table th:first-child, .weekly-signal-table-wrap table td:first-child { width: 18% !important; max-width: 165px !important; } "
        ".weekly-signal-table-wrap table th:nth-child(2), .weekly-signal-table-wrap table td:nth-child(2) { width: 44% !important; max-width: none !important; } "
        ".weekly-signal-table-wrap table th:last-child, .weekly-signal-table-wrap table td:last-child { width: 38% !important; max-width: 320px !important; } "
        "</style>"
    )
    table_md, err_msg, headlines, success_ts = get_weekly_signal_gemini_table(bucket_str)

    caption_parts = []
    if table_md:
        if success_ts is not None:
            try:
                dt = datetime.fromtimestamp(success_ts, tz=ZoneInfo("America/New_York"))
                caption_parts.append(f"**Last successful:** {dt.strftime('%b %d, %Y · %I:%M %p ET')}")
            except Exception:
                caption_parts.append("**Last successful:** recent")
        table_content = table_md
    else:
        last_md, last_saved_at, last_headlines = _load_last_weekly_signal()
        if last_md:
            if last_saved_at:
                caption_parts.append("**AI temporarily unavailable** — showing last saved edition. Previous content is kept so the signal is never lost.")
            else:
                caption_parts.append("**Sample edition.** The first run (around 7 PM ET) will replace this with live headlines and analysis.")
            if last_saved_at:
                try:
                    dt = datetime.fromisoformat(last_saved_at.replace("Z", "+00:00"))
                    caption_parts.append(f"**Last successful:** {dt.strftime('%b %d, %Y · %I:%M %p')} ET")
                except Exception:
                    pass
            table_content = last_md
        else:
            caption_parts.append(
                "**AI temporarily unavailable.** Check GEMINI_API_KEY in .streamlit/secrets.toml and that google-generativeai is installed: pip install google-generativeai"
            )
            if err_msg:
                caption_parts.append(f"Error: {err_msg}")
            table_content = (
                "| Category (Signal/Noise) | Headline | Compass View |\n"
                "|--------------------------|----------|--------------------------------|\n"
                "| Signal | — | Stay the course. |\n"
                "| Signal | — | Stay diversified. |\n"
                "| Noise | — | Turn off the screen. |"
            )

    if table_content:
        caption_html = "".join(
            f'<p style="font-size:0.8rem; color:#64748b; margin:0.25rem 0 0.5rem 0;">{p}</p>' for p in caption_parts
        )
        ws_inner = (
            f'<div style="text-align:center; margin-bottom:0.5rem;"><strong>🧭 {ws_title}</strong></div>'
            f'<div style="text-align:center; font-size:0.85rem; color:#64748b;">{ws_date_range}</div>'
            f'<div style="text-align:center; font-size:0.8rem; color:#94a3b8; margin-bottom:0.75rem;">Edition: {edition_str} · Updated once daily · 3 distinct topics (past week) · Analysis: Gemini</div>'
            f'{caption_html}'
            '<div class="weekly-signal-table-wrap">\n\n' + table_content + '\n\n</div>'
        )
        st.markdown(
            ws_table_css
            + '<div class="weekly-signal-box" style="background:#fff; border:1px solid #e2e8f0; border-radius:10px; padding:0.75rem 1rem; margin-top:1rem; box-shadow:0 1px 3px rgba(0,0,0,0.06);">'
            + ws_inner
            + "</div>",
            unsafe_allow_html=True,
        )

# -----------------------------------------------------------------------------
# HOME page content (1DAY / PERFORMANCES ETF charts)
# -----------------------------------------------------------------------------
home_page()
render_footer()
