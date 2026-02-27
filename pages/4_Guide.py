"""
GUIDE page - The Steady Compass.
Sidebar: Guru Principles, Investment Principles.
"""

import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from components.nav import inject_nav_css, render_nav, render_footer, maybe_redirect_from_query

st.set_page_config(page_title="The Steady Compass", page_icon="🧭", layout="wide", initial_sidebar_state="auto")
inject_nav_css()
maybe_redirect_from_query("GUIDE")
render_nav("GUIDE")

# Sidebar: Guru Principles, Investment Principles
with st.sidebar:
    st.markdown(
        "<style>"
        ".guide-sidenav { margin-top: 8rem; padding: 0.5rem 0; border-left: 3px solid #5a6378; padding-left: 0.75rem; margin-bottom: 1rem; } "
        ".guide-sidenav-title { font-size: 0.75rem; font-weight: 600; color: #64748b; letter-spacing: 0.05em; margin-bottom: 0.5rem; border-bottom: 1px solid #94a3b8; padding-bottom: 0.5rem; } "
        ".guide-sidenav a { display: block; padding: 0.35rem 0; font-size: 0.85rem; color: #475569; text-decoration: none; border-radius: 4px; } "
        ".guide-sidenav a:hover { color: #0ea5e9; background: #f1f5f9; padding-left: 0.25rem; } "
        ".guide-sidenav-sub { padding-left: 1rem; font-size: 0.8rem; } "
        ".guide-sidenav-group { margin-left: 0.5rem; padding-left: 0.5rem; border-left: 2px solid #cbd5e1; margin-top: 0.15rem; margin-bottom: 0.5rem; } "
        "@media (max-width: 640px) { .guide-sidenav { margin-top: 5rem; } .guide-sidenav a { min-height: 44px; display: flex; align-items: center; } } "
        "</style>"
        '<div class="guide-sidenav">'
        '<div class="guide-sidenav-title">GUIDE</div>'
        '<a href="#guru-principles">Guru Principles</a>'
        '<a href="#investment-principles">Investment Principles</a>'
        '<div class="guide-sidenav-group" aria-label="Under Investment Principles">'
        '<a href="#foundation" class="guide-sidenav-sub">Foundation</a>'
        '<a href="#market-reality" class="guide-sidenav-sub">Market Reality</a>'
        '<a href="#cost-efficiency" class="guide-sidenav-sub">Cost & Efficiency</a>'
        '<a href="#behavioral-traps" class="guide-sidenav-sub">Behavioral Traps</a>'
        '</div>'
        "</div>",
        unsafe_allow_html=True,
    )

st.markdown(
    '<div class="content-breadcrumb" aria-label="You are here">'
    '<a href="?page=HOME">Home</a> &nbsp;&gt;&nbsp; Guide</div>',
    unsafe_allow_html=True,
)
# Scroll margin so anchored sections are not hidden under fixed nav
st.markdown(
    "<style>"
    "#guru-principles, #investment-principles, #foundation, #market-reality, #cost-efficiency, #behavioral-traps { scroll-margin-top: 8rem; } "
    "</style>",
    unsafe_allow_html=True,
)

st.markdown(
    '<div id="guru-principles" class="section-heading">Guru Principles (Philosophy of the Great Masters)</div>',
    unsafe_allow_html=True,
)
st.caption("Eight legendary investors and their timeless wisdom.")

_guru_names = [
    "John Bogle", "Warren Buffett", "Peter Lynch", "Charlie Munger",
    "Benjamin Graham", "André Kostolany", "Burton Malkiel", "Tony Robbins",
]
# Ensure all tab labels are visible: allow wrap and slightly smaller font
st.markdown(
    "<style>"
    "[data-testid='stTabs'] [data-baseweb='tab-list'] { flex-wrap: wrap; gap: 0.25rem; } "
    "[data-testid='stTabs'] [data-baseweb='tab'] { font-size: 0.85rem; padding: 0.35rem 0.6rem; white-space: normal; } "
    "</style>",
    unsafe_allow_html=True,
)
tabs = st.tabs(_guru_names)

# Data: (quote, [principle1, principle2, principle3], (book_title, book_reason))
_guru_data = [
    (
        "Don't look for the needle in the haystack. Just buy the haystack.",
        [
            "Invest in index funds that own the entire market.",
            "Minimize costs—fees and taxes—that eat away at compound returns.",
            "Ignore the noise and stay the course.",
        ],
        ("*The Little Book of Common Sense Investing*", "The bible of index investing, praised by Warren Buffett as the alpha and omega for Bogleheads."),
    ),
    (
        "My will says that 10% of the cash left to my wife should go into short-term governments and 90% into a very low-cost S&P 500 index fund.",
        [
            "Never hold a stock for 10 minutes if you wouldn't hold it for 10 years.",
            "Bet on capitalism and America's long-term upward path.",
            "Only when the tide goes out do you discover who's been swimming naked. (Secure a margin of safety.)",
        ],
        ("*The Essays of Warren Buffett*", "Letters from the greatest investor in history to his shareholders, full of his investment philosophy and wisdom."),
    ),
    (
        "The key organ in the stock market is not the brain; it's the stomach. Your ability to withstand the fear of a crash determines your returns.",
        [
            "Trying to predict macroeconomics (rates, inflation) is a complete waste of time.",
            "Bear markets are as natural as a blizzard in winter.",
            "Don't chase fads; invest only in businesses you can understand with common sense.",
        ],
        ("*One Up On Wall Street*", "Wall Street's best practical guide: trust common sense and patience, not the experts."),
    ),
    (
        "The first principle of compounding is to never unnecessarily interrupt it.",
        [
            "You don't need to be a genius to be a great investor; you need to be less foolish than others.",
            "Frequent trading only makes the broker rich.",
            "It's the sitting patience—sitting on your rear—that makes the money.",
        ],
        ("*Poor Charlie's Almanack*", "Munger's multidisciplinary thinking and investment philosophy—Buffett's lifelong partner and sage."),
    ),
    (
        "The investor's chief problem—and even his worst enemy—is likely to be himself.",
        [
            "Don't be swayed by Mr. Market's mood swings.",
            "Investment is the thorough analysis that promises safety of principal and an adequate return.",
            "Always insist on a margin of safety.",
        ],
        ("*The Intelligent Investor*", "The eternal classic on investment psychology and philosophy by the father of value investing."),
    ),
    (
        "Buy a few international blue chips, take a sleeping pill, and sleep for a few years. When you wake up, you'll be rich.",
        [
            "Short-term market moves are 90% psychology.",
            "Think and act contrary to the crowd (contrarian investing).",
            "Never invest on borrowed money; pressure paralyzes reason.",
        ],
        ("*The Art of Speculation* (Kostolany)", "Insights on mastering greed and fear from Europe's legendary investor."),
    ),
    (
        "A blindfolded monkey throwing darts at the stock pages could select a portfolio that would do just as well as one carefully selected by the experts.",
        [
            "Markets are efficient; trying to time the market is pointless.",
            "Expensive active funds cannot beat the market (index) over the long run.",
            "Wide diversification is the only free lunch for reducing risk.",
        ],
        ("*A Random Walk Down Wall Street*", "The definitive academic and empirical case for index investing."),
    ),
    (
        "The financial industry's high fees are invisible predators eating your compound returns. Own the whole market at the lowest cost.",
        [
            "The world's best investors agree: don't lose money, and seek asymmetric risk/reward.",
            "Trust the power of compounding and build an automated investment system.",
            "Understand the rules of the game; don't be the sucker for the financial industry.",
        ],
        ("*MONEY: Master the Game*", "Interviews with top masters distilled into a simple index-investing path for everyone."),
    ),
]

for tab, name, (quote, principles, (book_title, book_reason)) in zip(tabs, _guru_names, _guru_data):
    with tab:
        st.subheader(name)
        st.success(quote)
        st.markdown("**Core principles**")
        for p in principles:
            st.markdown(f"- {p}")
        st.divider()
        col1, col2 = st.columns([1, 4])
        with col1:
            st.markdown(f"📖 **{book_title}**")
        with col2:
            st.markdown(book_reason)

st.divider()
st.markdown(
    '<div id="investment-principles" class="section-heading">Investment Principles</div>',
    unsafe_allow_html=True,
)

st.markdown('<div id="foundation" class="section-heading" style="font-size:1rem; margin-top:1rem;">🏛️ Foundation (The Four Pillars of Investing)</div>', unsafe_allow_html=True)
st.markdown("Before you pick a single stock, build your base: keep it simple, set your stock/bond mix, invest for the long run, and rebalance on a schedule. The four blocks below are the pillars every Bogle-style portfolio rests on.")
st.markdown("")

with st.expander("🥇 Simple is Best (The Beauty of Simplicity)", expanded=True):
    st.markdown("Wall Street sells complex products to earn fees, but the answer to investing has always been simple.")
    st.info(
        "**Guru's wisdom:**\n\n"
        "* **John Bogle & Warren Buffett:** \"Don't look for the needle in the haystack. Own the entire U.S. capitalism with one S&P 500 index fund.\"\n\n"
        "* **Charlie Munger:** \"Great investing is inherently boring. If you want excitement, go to the casino.\""
    )

with st.expander("⚖️ Asset Allocation"):
    st.markdown("Over 90% of your returns and volatility are determined not by which stocks you pick, but by how you split the ratio between stocks and safe assets (bonds/cash).")
    st.info(
        "**Guru's wisdom:**\n\n"
        "* **Benjamin Graham:** \"Always insist on a margin of safety. Bonds are your lifeline that preserves your sanity when Mr. Market has a fit in the worst crash.\"\n\n"
        "* **John Bogle:** \"Use your age in bonds as a starting point, and find the ratio that lets you sleep well at night.\""
    )

with st.expander("⏳ Long Term Investment"):
    st.markdown("In the short run the stock market is a voting machine for popularity; in the long run it is a weighing machine for real business value. The magic of compounding is completed only through time.")
    st.info(
        "**Guru's wisdom:**\n\n"
        "* **Peter Lynch:** \"Predicting interest rates or the next recession is impossible and a waste of time. Accept that bear markets are as natural as a blizzard in winter.\"\n\n"
        "* **André Kostolany:** \"If you bought a quality index fund, take a sleeping pill and sleep soundly. Time in the market solves everything.\""
    )

with st.expander("🔄 Rebalancing (Mechanical Rebalancing)"):
    st.markdown("Rebalancing is the only legal system that fully removes emotion and lets you 'buy low and sell high' mechanically.")
    st.info(
        "**Guru's wisdom:**\n\n"
        "* **Burton Malkiel & Tony Robbins:** \"Human nature wants to sell in a crash and buy in a rally. Set a rule: once a year, mechanically restore your target allocation (e.g. 60% stocks / 40% bonds). This automated habit makes you buy stocks cheap when you're scared and take profits when you're greedy.\""
    )

st.markdown('<div id="market-reality" class="section-heading" style="font-size:1rem; margin-top:1rem;">🌍 Market Reality (The Reality of the Market)</div>', unsafe_allow_html=True)
st.markdown("Markets are driven by emotion in the short run and by fundamentals in the long run. Understanding sentiment and volatility helps you stay calm when headlines scream—so you can keep your plan instead of reacting.")
st.markdown("")

with st.expander("🎭 Market Sentiment (Market Psychology & Mr. Market)"):
    st.markdown(
        "Short-term stock markets move on **greed** and **fear**, not fundamentals. The moment you are swept up by the crowd, investing becomes gambling. "
        "Get into the habit of checking market mood with objective indicators, not headlines. Try recording a number like the CNN Fear & Greed Index each Friday and calmly observe Mr. Market's mood swings."
    )
    st.info(
        "**Guru's wisdom:**\n\n"
        "* **Benjamin Graham:** \"Think of the market as a business partner called 'Mr. Market.' He shows up every day offering to buy or sell at a price. When he's cheerful (greed), he quotes silly high prices; when he's gloomy (fear), he quotes silly low prices. Don't be swayed by his mood—use him when he's gloomy.\"\n\n"
        "* **Warren Buffett:** \"Be fearful when others are greedy, and greedy when others are fearful.\""
    )

with st.expander("📉 Volatility (Not a Penalty—It's the Price of Admission)"):
    st.markdown(
        "Stock price swings are not a **penalty** for bad choices. They are the **price of admission** you pay for long-term returns above bank interest. "
        "If you paid for the theme park ticket, you don't jump off the roller coaster when it shakes."
    )
    st.info(
        "**Guru's wisdom:**\n\n"
        "* **Peter Lynch:** \"Historically, a 10%+ pullback has come every year. It's like the blizzard that hits Colorado every winter. Nobody abandons their car and runs—they put on a warm coat and wait for spring.\"\n\n"
        "* **Charlie Munger:** \"If you can't stomach watching your holdings fall 50% once or twice without losing your composure, you don't deserve the higher returns the stock market can offer.\""
    )

st.markdown('<div id="cost-efficiency" class="section-heading" style="font-size:1rem; margin-top:1rem;">💸 Cost & Efficiency (Costs and Efficiency)</div>', unsafe_allow_html=True)
st.markdown("Fees, taxes, and inflation shrink what you keep. The less you pay and the less you trade, the more compounding works for you. Real wealth is built by earning a solid *real* return and keeping it.")
st.markdown("")

with st.expander("🧛‍♂️ Fees (The Invisible Predator)"):
    st.markdown(
        "A typical active fund's 1.5% fee seems small, but over 30 years of compounding it can take nearly half of the returns that should have been yours. "
        "The great truth of investing is: **what you don't pay is what you keep.** Choose index ETFs (e.g. VOO, VTI) with fees around 0.03%."
    )
    st.info(
        "**Guru's wisdom:**\n\n"
        "* **John Bogle:** \"In the real world we live in, 'you get what you pay for' is the rule—but in investing it's the opposite. In investing, what you *don't* pay is what stays in your pocket.\"\n\n"
        "* **Tony Robbins:** \"The financial industry's hidden fees are invisible predators quietly eating away at your compound returns.\""
    )

with st.expander("🛑 Tax (The Brake on Your Compound Engine)"):
    st.markdown(
        "Every time you realize short-term gains by trading often, you pay taxes and trading costs. It's like constantly shaving snow off a snowball that's trying to grow. "
        "The best tax strategy is simple: **don't sell—hold for the long term.**"
    )
    st.info(
        "**Guru's wisdom:**\n\n"
        "* **Charlie Munger:** \"If you buy shares of a great business and leave them alone, you don't pay taxes every year—that money keeps compounding. Don't trade needlessly, pay taxes, and stop the magic of compounding.\""
    )

with st.expander("❄️ Compound Interest (The Eighth Wonder of the World)"):
    st.markdown(
        "Compound interest grows exponentially: not just on principal, but **interest on interest**. The first 10 years can feel slow, but once you cross the threshold, wealth can explode. "
        "What you need to enjoy compounding isn't high intelligence—it's starting early and not giving up along the way."
    )
    st.info(
        "**Guru's wisdom:**\n\n"
        "* **Warren Buffett:** \"My wealth comes from the luck of being born in America, a bit of genetics, and the magic of compounding. Start rolling a tiny snowball from the top of a mountain and let it roll a long time without breaking—eventually you get an avalanche.\""
    )

with st.expander("📊 Nominal vs Real Return (Inflation)", expanded=False):
    st.markdown(
        "**Nominal** return is the number you see (e.g. 7% a year). **Real** return is what’s left after inflation (e.g. 3%). So 7% nominal − 3% inflation ≈ **4% real**—that’s the purchasing power you actually gain. "
        "Long-term plans should focus on real returns; use the calculator in **Tools** to try different inflation assumptions."
    )

st.markdown('<div id="behavioral-traps" class="section-heading" style="font-size:1rem; margin-top:1rem;">🧠 Behavioral Traps (Behavioral Pitfalls)</div>', unsafe_allow_html=True)
st.markdown("The biggest risk is often ourselves: trading too much or trying to time the market. These two traps explain why many investors underperform—and how to avoid them.")
st.markdown("")

with st.expander("🕹️ Overtrading (The Curse of Action Addiction)"):
    st.markdown(
        "When we feel threatened or bored, we often feel we *must do something*. But in the stock market, frequent buying and selling only enriches the broker and is one of the worst enemies of your returns. "
        "Investing is done with your **seat**, not your head or your fingers. The greatest investments are inherently boring."
    )
    st.info(
        "**Guru's wisdom:**\n\n"
        "* **John Bogle:** \"When the market swings, do you feel you must do something? Don't—just stand there!\"\n\n"
        "* **Charlie Munger:** \"The big money in investing is not in the buying and selling. It's in the waiting.\"\n\n"
        "* **Warren Buffett:** \"Wall Street makes money when you move; you make money when you sit still.\""
    )

with st.expander("⏱️ Timing the Market (The Price of Arrogance)"):
    st.markdown(
        "Thinking you'll 'sell at the top and buy back at the bottom' is arrogance that trespasses on the divine. While you wait for the perfect timing, you're often out of the market during the handful of **magic days** that delivered the best returns in capitalist history—and missing those few days can devastate your long-term results. "
        "Don't try to **time the market**; focus on **time in the market**."
    )
    st.info(
        "**Guru's wisdom:**\n\n"
        "* **Peter Lynch:** \"More money has been lost by investors waiting for or trying to predict corrections than has been lost in the corrections themselves.\"\n\n"
        "* **Burton Malkiel:** \"Nobody can time the market. I've never met anyone who did it successfully, or who knew anyone who did.\""
    )

render_footer()
