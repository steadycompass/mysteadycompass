"""
ABOUT page - The Steady Compass.
Sections: Our Story & Philosophy, Disclaimer, Transparency & Methodology, Contact, Version.
"""

import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from components.nav import inject_nav_css, render_nav, render_footer, maybe_redirect_from_query

st.set_page_config(page_title="The Steady Compass", page_icon="🧭", layout="wide", initial_sidebar_state="collapsed")
inject_nav_css()
maybe_redirect_from_query("ABOUT")
render_nav("ABOUT")

st.markdown(
    '<div class="content-breadcrumb" aria-label="You are here">'
    '<a href="?page=HOME">Home</a> &nbsp;&gt;&nbsp; About</div>',
    unsafe_allow_html=True,
)

st.title("About The Steady Compass")

# -----------------------------------------------------------------------------
# 1. Our Story & Philosophy
# -----------------------------------------------------------------------------
st.markdown('<div class="section-heading">Our Story & Philosophy</div>', unsafe_allow_html=True)
st.info(
    "The world of investing is like a rough sea: endless news, greed, and fear swirling every day. I, too, was an ordinary individual "
    "investor who once suffered painful losses in that sea and lost sleep over every short-term spike or crash.\n\n"
    "Then I met the philosophy of **John Bogle**. After embracing his truth—*give up the arrogance of predicting the market; "
    "own capitalism's long-term upward path as a whole*—my investing changed completely. Above all, my mind grew calm. "
    "I could sleep well at night even in a crash (Sleep Well At Night).\n\n"
    "**The Steady Compass** was built for those who, like my past self, feel lost in the storm. Choose simplicity over complexity, "
    "patience over prediction. I sincerely hope this small compass helps you sail successfully."
)

# -----------------------------------------------------------------------------
# 2. Disclaimer
# -----------------------------------------------------------------------------
st.markdown('<div class="section-heading">Disclaimer</div>', unsafe_allow_html=True)
st.warning(
    "All data, charts, simulation results, and investment philosophy provided on this website are for **educational and informational "
    "purposes only**. They do not constitute professional financial advice or a recommendation to buy or sell any specific asset. "
    "All investing involves risk of loss of principal. Final investment decisions and their consequences are solely the responsibility "
    "of the investor."
)

# -----------------------------------------------------------------------------
# 3. Transparency & Methodology
# -----------------------------------------------------------------------------
with st.expander("Transparency & Methodology (Data & How We Calculate)", expanded=True):
    st.markdown(
        "- **Data sources:** All market data (prices, MDD, etc.) in this app are fetched and computed **neutrally** via the Yahoo Finance (yfinance) API, using real-time and historical data.\n\n"
        "- **Simulator assumptions:** The Portfolio Simulator is based on nominal returns excluding taxes and assumes **annual mechanical rebalancing**.\n\n"
        "- **Zero conflicts of interest:** We are not affiliated with any financial institution and do not receive fees for recommending specific products.\n\n"
        "- **Strict privacy:** Information you enter in the simulator (e.g. age, investment amount) is **not stored** on any server and **disappears** when you close the browser."
    )

# -----------------------------------------------------------------------------
# 4. Contact & Feedback
# -----------------------------------------------------------------------------
st.markdown('<div class="section-heading">Contact & Feedback</div>', unsafe_allow_html=True)
st.markdown(
    "Suggestions for new features, reports of errors, or ideas for additional guru philosophy? We'd love to hear from you."
)
st.markdown("[Contact Us](mailto:feedback@steadycompass.com)")

render_footer()
