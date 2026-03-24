import streamlit as st
import json
import time
import os
from datetime import datetime, timedelta
from fetcher import fetch_all_sectors, SECTORS
from map_renderer import render_map_html

st.set_page_config(
    page_title="Mohali Property Map",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; padding-bottom: 1rem; }
    .stAlert { border-radius: 8px; }
    h1 { font-size: 1.5rem !important; font-weight: 600 !important; }
    h3 { font-size: 1rem !important; font-weight: 500 !important; color: #555 !important; }
    .metric-box {
        background: #f8f8f8;
        border-radius: 10px;
        padding: 0.75rem 1rem;
        border: 1px solid #eee;
        text-align: center;
    }
    .metric-box .val { font-size: 1.3rem; font-weight: 600; }
    .metric-box .lbl { font-size: 0.75rem; color: #888; margin-top: 2px; }
    .tier-badge {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 20px;
        font-size: 0.72rem;
        font-weight: 500;
    }
    footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

CACHE_FILE = "data_cache.json"
CACHE_TTL_HOURS = 168  # 1 week

def load_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE) as f:
                return json.load(f)
        except Exception:
            return None
    return None

def save_cache(data):
    with open(CACHE_FILE, "w") as f:
        json.dump(data, f)

def cache_is_fresh(cache):
    if not cache or "fetched_at" not in cache:
        return False
    fetched = datetime.fromisoformat(cache["fetched_at"])
    return datetime.now() - fetched < timedelta(hours=CACHE_TTL_HOURS)

def get_data(force_refresh=False):
    cache = load_cache()
    if not force_refresh and cache_is_fresh(cache):
        return cache["sectors"], cache["fetched_at"], "cache"
    with st.spinner("Fetching latest rates from 99acres…"):
        sectors = fetch_all_sectors()
    fetched_at = datetime.now().isoformat()
    save_cache({"sectors": sectors, "fetched_at": fetched_at})
    return sectors, fetched_at, "live"

# ── Header ──────────────────────────────────────────────────────────────────
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.markdown("## 🏙️ Mohali Property Price Map")
    st.markdown("##### Live rates · hover sectors · updated weekly")
with col_h2:
    refresh = st.button("🔄 Refresh now", use_container_width=True)

sectors_data, fetched_at, source = get_data(force_refresh=refresh)

# ── Status bar ───────────────────────────────────────────────────────────────
fetched_dt = datetime.fromisoformat(fetched_at)
age_str = fetched_dt.strftime("%d %b %Y, %I:%M %p")
src_color = "#27ae60" if source == "live" else "#888"
src_label = "live fetch" if source == "live" else "cached"
st.markdown(
    f'<p style="font-size:0.78rem; color:{src_color}; margin-bottom:1rem;">Last updated: {age_str} &nbsp;·&nbsp; {src_label}</p>',
    unsafe_allow_html=True
)

# ── Summary metrics ──────────────────────────────────────────────────────────
prices = [s["price_avg"] for s in sectors_data if s.get("price_avg")]
if prices:
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f'<div class="metric-box"><div class="val">₹{max(prices):,}</div><div class="lbl">Highest (sqft)</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="metric-box"><div class="val">₹{min(prices):,}</div><div class="lbl">Lowest (sqft)</div></div>', unsafe_allow_html=True)
    with c3:
        avg = int(sum(prices) / len(prices))
        st.markdown(f'<div class="metric-box"><div class="val">₹{avg:,}</div><div class="lbl">Average (sqft)</div></div>', unsafe_allow_html=True)
    with c4:
        st.markdown(f'<div class="metric-box"><div class="val">{len(sectors_data)}</div><div class="lbl">Sectors tracked</div></div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

# ── Map ───────────────────────────────────────────────────────────────────────
map_html = render_map_html(sectors_data)
st.components.v1.html(map_html, height=660, scrolling=False)

# ── Data table ────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("#### Sector-wise breakdown")

tier_colors = {
    "Premium":      ("#fde8e8", "#a32d2d"),
    "Upper-mid":    ("#fef3e0", "#854f0b"),
    "Mid":          ("#e4f5ec", "#0f6e56"),
    "Affordable":   ("#e8f2fc", "#185fa5"),
    "Emerging pick":("#eeedfe", "#534ab7"),
}

rows = []
for s in sorted(sectors_data, key=lambda x: x.get("price_avg", 0), reverse=True):
    tier = s.get("tier", "")
    bg, fg = tier_colors.get(tier, ("#f0f0f0", "#333"))
    badge = f'<span class="tier-badge" style="background:{bg};color:{fg}">{tier}</span>'
    yoy = s.get("yoy_pct")
    yoy_str = f'<span style="color:{"#27ae60" if yoy and yoy > 0 else "#e74c3c"}">{yoy:+.1f}%</span>' if yoy else "—"
    price = f'₹{s["price_avg"]:,}' if s.get("price_avg") else s.get("price_label", "—")
    rows.append(f"""
    <tr style="border-bottom:1px solid #f0f0f0;">
        <td style="padding:8px 12px;font-weight:500">{s['name']}</td>
        <td style="padding:8px 12px">{badge}</td>
        <td style="padding:8px 12px;font-weight:500">{price}</td>
        <td style="padding:8px 12px">{yoy_str}</td>
        <td style="padding:8px 12px;font-size:0.8rem;color:#666;max-width:260px">{s.get("note","")}</td>
    </tr>
    """)

table_html = f"""
<table style="width:100%;border-collapse:collapse;font-size:0.88rem;font-family:sans-serif">
  <thead>
    <tr style="background:#f8f8f8;border-bottom:2px solid #eee">
      <th style="padding:8px 12px;text-align:left">Sector</th>
      <th style="padding:8px 12px;text-align:left">Tier</th>
      <th style="padding:8px 12px;text-align:left">Avg price/sqft</th>
      <th style="padding:8px 12px;text-align:left">YOY</th>
      <th style="padding:8px 12px;text-align:left">Notes</th>
    </tr>
  </thead>
  <tbody>{"".join(rows)}</tbody>
</table>
"""
st.components.v1.html(table_html, height=len(rows) * 50 + 60, scrolling=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    '<p style="font-size:0.75rem;color:#aaa;text-align:center">Data sourced from 99acres.com · For reference only · Not financial advice · Built with Streamlit</p>',
    unsafe_allow_html=True
)
