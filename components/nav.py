"""
Shared top navigation bar for The Steady Compass.
Title + nav as one bar; compass watermark on main.
Tested with Streamlit 1.54.0.
"""

import base64
import streamlit as st

PAGES = ["HOME", "MARKET", "MIND", "TOOLS", "GUIDE", "ABOUT"]
NAV_HEIGHT = 36

# Script path for each page (for st.switch_page)
PAGE_SCRIPT = {
    "HOME": "app.py",
    "MARKET": "pages/1_Market.py",
    "MIND": "pages/2_Mind.py",
    "TOOLS": "pages/3_Tools.py",
    "GUIDE": "pages/4_Guide.py",
    "ABOUT": "pages/5_About.py",
}


def inject_nav_css():
    """Title + nav as one bar; compass watermark on main (Streamlit 1.54+)."""
    # Line-art compass SVG for background watermark (opacity via fill/stroke in SVG)
    compass_svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
        '<circle cx="50" cy="50" r="44" fill="none" stroke="currentColor" stroke-width="1.2"/>'
        '<line x1="50" y1="6" x2="50" y2="94" stroke="currentColor" stroke-width="1"/>'
        '<line x1="6" y1="50" x2="94" y2="50" stroke="currentColor" stroke-width="1"/>'
        '<line x1="50" y1="50" x2="50" y2="22" stroke="currentColor" stroke-width="1.5"/>'
        '<line x1="50" y1="50" x2="32" y2="68" stroke="currentColor" stroke-width="0.9"/>'
        '<line x1="50" y1="50" x2="68" y2="68" stroke="currentColor" stroke-width="0.9"/>'
        '</svg>'
    )
    compass_b64 = base64.b64encode(compass_svg.encode("utf-8")).decode("ascii")
    compass_data_uri = f"data:image/svg+xml;base64,{compass_b64}"

    st.markdown(
        f"""
    <style>
    /* ----- Row 1: Title "The Steady Compass" — darker gray text, lighter gray background ----- */
    .nav-title-block {{
        position: sticky !important;
        top: 3.25rem !important;
        z-index: 10000 !important;
        overflow: hidden !important;
        margin-left: calc(-50vw + 50%) !important;
        margin-right: calc(-50vw + 50%) !important;
        margin-bottom: 10px !important;
        width: 100vw !important;
        max-width: 100vw !important;
        box-sizing: border-box !important;
        padding: 12px 16px !important;
        background: linear-gradient(135deg, #e2e6ea 0%, #eef0f4 100%) !important;
        border-bottom: 1px solid #dde0e5 !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.04) !important;
        text-align: center !important;
    }}
    .nav-title-block::before {{
        content: "";
        position: absolute !important;
        inset: 0 !important;
        background: url("{compass_data_uri}") center/140px no-repeat !important;
        opacity: 0.12 !important;
        pointer-events: none !important;
        z-index: 0 !important;
    }}
    .nav-title-text {{
        font-size: 1.4rem !important;
        font-weight: 700 !important;
        color: #6b7280 !important;
        letter-spacing: 0.04em !important;
        margin: 0 !important;
        position: relative !important;
        z-index: 1 !important;
    }}
    .nav-title-block a.nav-title-text {{
        text-decoration: none !important;
        color: #6b7280 !important;
    }}
    .nav-title-block a.nav-title-text:hover {{
        color: #4b5563 !important;
    }}
    /* ----- Site-wide section titles (use class="section-heading" for consistent size) ----- */
    .section-heading {{
        font-size: 1.35rem !important;
        font-weight: 600 !important;
        margin: 0 0 8px 0 !important;
        display: block !important;
    }}
    /* ----- Row 2: Menu buttons — target columns row via marker's parent (Streamlit wraps in div) ----- */
    div:has(> #steady-compass-nav-marker) + * + * {{
        position: sticky !important;
        top: 5.5rem !important;
        z-index: 9999 !important;
        background: linear-gradient(135deg, #5a6378 0%, #4d5568 100%) !important;
        padding: 6px 12px !important;
        margin-left: calc(-50vw + 50%) !important;
        margin-right: calc(-50vw + 50%) !important;
        margin-top: 0 !important;
        margin-bottom: 8px !important;
        width: 100vw !important;
        max-width: 100vw !important;
        box-sizing: border-box !important;
        border-radius: 0 !important;
        border-bottom: 1px solid #6b7589 !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06) !important;
        display: flex !important;
        flex-wrap: nowrap !important;
        align-items: center !important;
    }}
    div:has(> #steady-compass-nav-marker) + * + * > div {{
        min-width: 56px !important;
        flex-shrink: 0 !important;
    }}
    div:has(> #steady-compass-nav-marker) + * + * button {{
        background: transparent !important;
        color: #e2e6ed !important;
        border: none !important;
        font-weight: 500 !important;
        font-size: 13px !important;
        padding: 6px 10px !important;
        min-height: 30px !important;
        min-width: 52px !important;
        width: 100% !important;
        white-space: nowrap !important;
        flex-shrink: 0 !important;
    }}
    div:has(> #steady-compass-nav-marker) + * + * button:hover {{
        background: #5a6378 !important;
        color: #fff !important;
    }}
    /* Active menu: applied by JS (class sc-nav-active) so it works regardless of DOM structure */
    button.sc-nav-active {{
        background: #5a6378 !important;
        color: #fff !important;
    }}
    /* ----- Breadcrumb: you are here (below menu) ----- */
    .sc-breadcrumb {{
        margin-left: calc(-50vw + 50%) !important;
        margin-right: calc(-50vw + 50%) !important;
        width: 100vw !important;
        max-width: 100vw !important;
        box-sizing: border-box !important;
        padding: 4px 16px 10px !important;
        font-size: 0.8rem !important;
        color: #64748b !important;
        letter-spacing: 0.02em !important;
    }}
    .sc-breadcrumb a {{ color: #475569 !important; text-decoration: none !important; }}
    .sc-breadcrumb a:hover {{ color: #334155 !important; text-decoration: underline !important; }}
    /* ----- In-content breadcrumb (same position on every page: start of main column) ----- */
    .content-breadcrumb {{ font-size: 0.8rem !important; color: #64748b !important; padding: 4px 0 10px 0 !important; letter-spacing: 0.02em !important; }}
    .content-breadcrumb a {{ color: #475569 !important; text-decoration: none !important; }}
    .content-breadcrumb a:hover {{ color: #334155 !important; text-decoration: underline !important; }}
    /* ----- Compass watermark: subtle background on main ----- */
    .main::before {{
        content: "";
        position: fixed !important;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background-image: url("{compass_data_uri}");
        background-size: min(420px, 60vmin) !important;
        background-position: center !important;
        background-repeat: no-repeat !important;
        opacity: 0.07 !important;
        pointer-events: none !important;
        z-index: 0 !important;
    }}
    .main > * {{ position: relative; z-index: 1; }}
    /* ----- Main & chart: wide enough for table, no cutoff ----- */
    .block-container,
    .main .block-container {{
        padding-top: 6rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        max-width: 640px !important;
        margin-left: auto !important;
        margin-right: auto !important;
    }}
    .main h1, .block-container h1 {{ font-size: 1.15rem !important; font-weight: 600 !important; margin-bottom: 6px !important; }}
    .main h2, .block-container h2 {{ font-size: 1rem !important; margin-bottom: 8px !important; }}
    .main p, .main .stCaption, .block-container p, .block-container .stCaption {{ font-size: 0.8125rem !important; }}
    .main .stCaption, .block-container .stCaption {{ line-height: 1.0 !important; margin-top: 0.08rem !important; margin-bottom: 0.08rem !important; }}
    /* DataFrame: readable, full width in container ----- */
    [data-testid="stDataFrame"],
    .stDataFrame,
    .main [data-testid="stDataFrame"],
    .main .stDataFrame {{
        font-size: 0.8125rem !important;
        border-radius: 6px !important;
        overflow-x: auto !important;
        width: 100% !important;
        max-width: 100% !important;
    }}
    [data-testid="stDataFrame"] table,
    .stDataFrame table {{ font-size: 0.8125rem !important; }}
    [data-testid="stDataFrame"] th,
    [data-testid="stDataFrame"] td,
    .stDataFrame th,
    .stDataFrame td {{
        padding: 6px 8px !important;
        font-size: 0.8125rem !important;
    }}
    [data-testid="stTabs"] {{ margin-bottom: 6px !important; }}
    [data-testid="stTabs"] [role="tab"] {{ font-size: 0.8125rem !important; padding: 6px 10px !important; min-height: 32px !important; }}
    /* ----- Responsive table wrapper (1DAY / PERFORMANCES custom HTML tables) ----- */
    .responsive-table-wrap {{
        overflow-x: auto !important;
        -webkit-overflow-scrolling: touch !important;
        width: 100% !important;
        margin-bottom: 0.5rem !important;
    }}
    .responsive-table-wrap table {{ min-width: 280px !important; }}
    /* ----- Mobile: responsive ----- */
    @media (max-width: 640px) {{
        .block-container, .main .block-container {{ max-width: 100% !important; padding-left: 0.75rem !important; padding-right: 0.75rem !important; padding-top: 5.5rem !important; }}
        .nav-title-block {{ padding: 10px 12px !important; margin-bottom: 8px !important; }}
        .nav-title-text {{ font-size: 1.15rem !important; }}
        .section-heading {{ font-size: 1.15rem !important; }}
        div:has(> #steady-compass-nav-marker) + * + * {{ padding: 8px 8px !important; margin-bottom: 6px !important; flex-wrap: wrap !important; justify-content: center !important; }}
        div:has(> #steady-compass-nav-marker) + * + * button {{ font-size: 11px !important; padding: 8px 6px !important; min-height: 44px !important; min-width: 44px !important; }}
        div:has(> #steady-compass-nav-marker) + * + * > div {{ min-width: 44px !important; }}
        .sc-breadcrumb {{ padding: 6px 12px 10px !important; font-size: 0.75rem !important; text-align: center !important; }}
        .content-breadcrumb {{ padding: 6px 0 12px 0 !important; font-size: 0.85rem !important; }}
        [data-testid="stDataFrame"], .stDataFrame {{ overflow-x: auto !important; -webkit-overflow-scrolling: touch !important; }}
        [data-testid="stDataFrame"] th, [data-testid="stDataFrame"] td, .stDataFrame th, .stDataFrame td {{ padding: 6px 8px !important; font-size: 0.75rem !important; }}
        .main h1 {{ font-size: 1.05rem !important; }}
        [data-testid="stTabs"] [role="tab"] {{ font-size: 0.75rem !important; padding: 8px 8px !important; min-height: 44px !important; }}
        .responsive-table-wrap {{ margin-left: -0.5rem !important; margin-right: -0.5rem !important; padding-left: 0.5rem !important; padding-right: 0.5rem !important; overflow-x: auto !important; -webkit-overflow-scrolling: touch !important; }}
        .responsive-table-wrap table {{ font-size: 0.8rem !important; min-width: 280px !important; }}
        .responsive-table-wrap th, .responsive-table-wrap td {{ padding: 6px 6px !important; }}
        .dd-html-table-wrap, .mdd-html-table-wrap {{ overflow-x: auto !important; -webkit-overflow-scrolling: touch !important; margin: 0 -0.5rem 1rem !important; padding: 0 0.5rem !important; }}
        .dd-html-table-wrap table, .mdd-html-table-wrap table {{ font-size: 0.75rem !important; min-width: 320px !important; }}
        .weekly-signal-table-wrap {{ overflow-x: auto !important; -webkit-overflow-scrolling: touch !important; }}
        .weekly-signal-table-wrap table {{ font-size: 0.8rem !important; }}
        .weekly-signal-box {{ padding: 0.5rem 0.75rem !important; overflow-x: auto !important; word-wrap: break-word !important; overflow-wrap: break-word !important; -webkit-overflow-scrolling: touch !important; }}
        .tip-of-the-day-box {{ word-wrap: break-word !important; overflow-wrap: break-word !important; padding: 0.5rem 0.75rem !important; font-size: 0.85rem !important; }}
        .gauge-header-block {{ word-wrap: break-word !important; overflow-wrap: break-word !important; font-size: 0.72rem !important; }}
        [data-testid="column"] {{ flex: 0 0 100% !important; max-width: 100% !important; }}
        .stExpander {{ font-size: 0.9rem !important; }}
        [data-testid="stExpander"] summary {{ min-height: 44px !important; display: flex !important; align-items: center !important; padding: 0.5rem 0 !important; }}
        .main .block-container {{ overflow-x: hidden !important; }}
        .main p, .main .stCaption, .main [data-testid="stMarkdown"] {{ word-wrap: break-word !important; overflow-wrap: break-word !important; }}
        .js-plotly-plot .svg-container {{ max-width: 100% !important; }}
        [data-testid="stPlotlyChart"] {{ overflow-x: auto !important; -webkit-overflow-scrolling: touch !important; }}
    }}
    @media (max-width: 380px) {{
        .nav-title-text {{ font-size: 1rem !important; }}
        div:has(> #steady-compass-nav-marker) + * + * button {{ font-size: 10px !important; padding: 6px 4px !important; min-width: 40px !important; }}
        div:has(> #steady-compass-nav-marker) + * + * > div {{ min-width: 40px !important; }}
    }}
    </style>
    """,
        unsafe_allow_html=True,
    )


def render_nav(current_page: str):
    """Render title above menu: Row 1 = The Steady Compass (with compass bg), Row 2 = menu buttons."""
    current = (current_page or "HOME").strip().upper()
    if current not in PAGES:
        current = "HOME"
    active_idx = PAGES.index(current)

    # Marker with active index for CSS (active menu = calm blue, no red)
    st.markdown(
        f'<div id="steady-compass-nav-marker" data-active-idx="{active_idx}" style="display:none; height:0; margin:0; padding:0;"></div>',
        unsafe_allow_html=True,
    )
    # Row 1: Title "The Steady Compass" above menu (click to go Home), with compass image behind text
    st.markdown(
        '<div class="nav-title-block"><a href="?page=HOME" class="nav-title-text" aria-label="Go to Home">🧭 The Steady Compass</a></div>',
        unsafe_allow_html=True,
    )
    # Row 2: Menu buttons only (all secondary)
    cols = st.columns(6)
    for i, page in enumerate(PAGES):
        with cols[i]:
            if st.button(
                page,
                key=f"nav_{page}",
                type="secondary",
                use_container_width=True,
            ):
                target = PAGE_SCRIPT.get(page)
                if target:
                    st.switch_page(target)

    # Breadcrumb is rendered in each page's main content for consistent position (below nav, start of content)
    st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)


def maybe_redirect_from_query(current_page: str):
    """
    If query param 'page' is set and different from current_page, switch to that page.
    Call this at the top of each script after set_page_config / before rendering nav.
    """
    q = st.query_params.get("page")
    query_page = (q[0] if isinstance(q, list) else q) or ""
    query_page = str(query_page).upper().strip()
    if query_page and query_page in PAGES and query_page != current_page:
        target = PAGE_SCRIPT.get(query_page)
        if target:
            st.switch_page(target)


# Footer: same background as nav title block for consistency; minimal, professional.
# Match nav: linear-gradient(135deg, #e2e6ea 0%, #eef0f4 100%), border #dde0e5
FOOTER_BG = "linear-gradient(135deg, #e2e6ea 0%, #eef0f4 100%)"
FOOTER_BORDER = "#dde0e5"
FOOTER_TEXT = "#64748b"
FOOTER_LINK = "#475569"
FOOTER_LINK_HOVER = "#334155"


def render_footer():
    """Render site footer: service name, slogan, main menu links, contact placeholder, disclaimer, copyright."""
    links_html = " &nbsp;·&nbsp; ".join(
        f'<a href="?page={p}" target="_self" class="sc-footer-link" aria-label="Go to {p} page">{p}</a>' for p in PAGES
    )
    st.markdown(
        f"""
    <style>
    .sc-footer {{
        background: {FOOTER_BG} !important;
        border-top: 1px solid {FOOTER_BORDER} !important;
        color: {FOOTER_TEXT} !important;
        padding: 2.5rem 1.5rem 2rem !important;
        margin-top: 3rem !important;
        margin-left: calc(-50vw + 50%) !important;
        margin-right: calc(-50vw + 50%) !important;
        width: 100vw !important;
        max-width: 100vw !important;
        box-sizing: border-box !important;
        text-align: center !important;
        font-size: 0.875rem !important;
        line-height: 1.6 !important;
    }}
    .sc-footer-brand {{ font-size: 1.1rem !important; font-weight: 600 !important; color: {FOOTER_LINK} !important; margin-bottom: 0.25rem !important; }}
    .sc-footer-brand a {{ color: inherit !important; text-decoration: none !important; }}
    .sc-footer-brand a:hover {{ color: {FOOTER_LINK_HOVER} !important; }}
    .sc-footer-slogan {{ font-size: 0.8rem !important; color: {FOOTER_TEXT} !important; margin-bottom: 1.25rem !important; letter-spacing: 0.02em !important; }}
    .sc-footer-nav {{ padding-top: 1rem !important; margin-bottom: 1rem !important; border-top: 1px solid {FOOTER_BORDER} !important; }}
    .sc-footer-nav .sc-footer-link {{ color: {FOOTER_LINK} !important; text-decoration: none !important; }}
    .sc-footer-nav .sc-footer-link:hover {{ color: {FOOTER_LINK_HOVER} !important; }}
    @media (max-width: 640px) {{
        .sc-footer {{ padding: 1.5rem 1rem !important; }}
        .sc-footer-nav {{ display: flex !important; flex-wrap: wrap !important; justify-content: center !important; gap: 0.35rem 0.75rem !important; }}
        .sc-footer-disclaimer {{ font-size: 0.7rem !important; padding-left: 0.5rem !important; padding-right: 0.5rem !important; }}
    }}
    .sc-footer-contact {{ padding-top: 1rem !important; margin-bottom: 1rem !important; border-top: 1px solid {FOOTER_BORDER} !important; font-size: 0.8rem !important; color: {FOOTER_TEXT} !important; }}
    .sc-footer-contact a {{ color: {FOOTER_LINK} !important; text-decoration: none !important; }}
    .sc-footer-contact a:hover {{ color: {FOOTER_LINK_HOVER} !important; }}
    .sc-footer-disclaimer {{ padding-top: 1rem !important; max-width: 640px !important; margin: 0 auto 0.75rem !important; font-size: 0.75rem !important; color: {FOOTER_TEXT} !important; border-top: 1px solid {FOOTER_BORDER} !important; }}
    .sc-footer-copy {{ font-size: 0.7rem !important; color: {FOOTER_TEXT} !important; opacity: 0.9 !important; }}
    </style>
    <footer class="sc-footer" role="contentinfo">
        <div class="sc-footer-brand"><a href="?page=HOME" target="_self" aria-label="Go to Home">🧭 The Steady Compass</a></div>
        <div class="sc-footer-slogan">Stay the Course</div>
        <nav class="sc-footer-nav" aria-label="Footer navigation">{links_html}</nav>
        <div class="sc-footer-contact">Contact: <a href="mailto:contact@thesteadycompass.com" aria-label="Email The Steady Compass">contact@thesteadycompass.com</a></div>
        <div class="sc-footer-disclaimer">The information contained herein does not constitute the provision of investment advice. The Steady Compass is not a registered investment advisor. Data: Yahoo Finance · Not financial advice.</div>
        <div class="sc-footer-copy">© 2026 The Steady Compass. All rights reserved.</div>
    </footer>
    """,
        unsafe_allow_html=True,
    )
