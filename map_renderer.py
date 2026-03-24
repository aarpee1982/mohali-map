"""
map_renderer.py
Generates the interactive HTML map from sector data.
Colours auto-update based on live prices.
"""

TIER_STYLES = {
    "Premium":       {"fill": "#E24B4A", "fill_op": "0.15", "stroke": "#A32D2D", "label": "#A32D2D", "sub": "#993556", "badge_bg": "#FCEBEB", "badge_fg": "#A32D2D"},
    "Upper-mid":     {"fill": "#EF9F27", "fill_op": "0.15", "stroke": "#BA7517", "label": "#BA7517", "sub": "#854F0B", "badge_bg": "#FAEEDA", "badge_fg": "#854F0B"},
    "Mid":           {"fill": "#1D9E75", "fill_op": "0.13", "stroke": "#0F6E56", "label": "#0F6E56", "sub": "#085041", "badge_bg": "#E1F5EE", "badge_fg": "#0F6E56"},
    "Affordable":    {"fill": "#378ADD", "fill_op": "0.11", "stroke": "#185FA5", "label": "#185FA5", "sub": "#0C447C", "badge_bg": "#E6F1FB", "badge_fg": "#185FA5"},
    "Emerging pick": {"fill": "#534AB7", "fill_op": "0.12", "stroke": "#534AB7", "label": "#534AB7", "sub": "#3C3489", "badge_bg": "#EEEDFE", "badge_fg": "#534AB7"},
}

def _sector_rect(s: dict) -> str:
    t = TIER_STYLES.get(s.get("tier", "Mid"), TIER_STYLES["Mid"])
    x, y = s.get("map_x", 40), s.get("map_y", 75)
    w, h = 95, 52
    star = "★ " if s.get("star") else ""
    sw = "2" if s.get("star") else "1.5"
    price_label = f'₹{s["price_avg"]:,}' if s.get("price_avg") else s.get("price_label", "—")
    yoy = s.get("yoy_pct")
    yoy_str = f'{yoy:+.1f}%' if yoy is not None else ""
    live_dot = ' 🟢' if s.get("live") else ""

    name_display = s["name"].replace(" ★", "")

    # Encode tooltip data safely
    import html as html_lib
    tip_name = html_lib.escape(s["name"])
    tip_price = html_lib.escape(price_label)
    tip_tier = html_lib.escape(s.get("tier", ""))
    tip_yoy = html_lib.escape(f'YOY: {yoy_str}' if yoy_str else "YOY: n/a")
    tip_note = html_lib.escape(s.get("note", ""))
    tip_live = "Live data" if s.get("live") else "Baseline data"

    sub_line = price_label
    if yoy_str:
        sub_line += f" · {yoy_str}"

    return f"""
<g class="sector"
   data-name="{tip_name}"
   data-price="{tip_price}"
   data-tier="{tip_tier}"
   data-yoy="{tip_yoy}"
   data-note="{tip_note}"
   data-live="{tip_live}">
  <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="5"
        fill="{t['fill']}" fill-opacity="{t['fill_op']}"
        stroke="{t['stroke']}" stroke-width="{sw}"/>
  <text x="{x+w//2}" y="{y+21}" text-anchor="middle" font-size="11" font-weight="500" fill="{t['label']}">{star}{name_display}</text>
  <text x="{x+w//2}" y="{y+37}" text-anchor="middle" font-size="9" fill="{t['sub']}">{sub_line}</text>
</g>"""


def render_map_html(sectors: list[dict]) -> str:
    sector_rects = "\n".join(_sector_rect(s) for s in sectors)
    live_count = sum(1 for s in sectors if s.get("live"))
    live_note = f"{live_count}/{len(sectors)} sectors with live data" if live_count else "Showing baseline data"

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
* {{ box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }}
body {{ background: transparent; }}
.wrap {{ position: relative; width: 100%; max-width: 680px; margin: 0 auto; }}
svg {{ width: 100%; height: auto; display: block; }}
.legend {{ display: flex; gap: 12px; flex-wrap: wrap; margin: 0.5rem 0 0.75rem; justify-content: center; }}
.li {{ display: flex; align-items: center; gap: 5px; font-size: 12px; color: #555; }}
.ld {{ width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }}
.tooltip {{
  position: absolute;
  background: #fff;
  border: 1px solid #e0e0e0;
  border-radius: 10px;
  padding: 10px 14px;
  font-size: 13px;
  pointer-events: none;
  opacity: 0;
  transition: opacity 0.12s;
  max-width: 210px;
  z-index: 10;
  box-shadow: 0 2px 12px rgba(0,0,0,0.10);
}}
.tooltip.show {{ opacity: 1; }}
.tt-name {{ font-size: 13px; font-weight: 600; color: #222; margin-bottom: 3px; }}
.tt-price {{ font-size: 12px; color: #444; }}
.tt-yoy {{ font-size: 12px; color: #444; }}
.tt-tier {{ font-size: 11px; font-weight: 500; padding: 2px 8px; border-radius: 4px; display: inline-block; margin: 4px 0; }}
.tt-note {{ font-size: 11px; color: #777; margin-top: 4px; line-height: 1.4; }}
.tt-live {{ font-size: 10px; color: #27ae60; margin-top: 4px; }}
.note {{ font-size: 11px; color: #aaa; text-align: center; margin-top: 0.5rem; }}
.sector {{ cursor: pointer; }}
</style>
</head>
<body>
<div class="wrap">

  <div class="legend">
    <div class="li"><div class="ld" style="background:#A32D2D"></div> Premium (₹10k+)</div>
    <div class="li"><div class="ld" style="background:#BA7517"></div> Upper-mid (₹8–10k)</div>
    <div class="li"><div class="ld" style="background:#0F6E56"></div> Mid (₹6–8k)</div>
    <div class="li"><div class="ld" style="background:#185FA5"></div> Affordable (&lt;₹6k)</div>
    <div class="li"><div class="ld" style="background:#534AB7"></div> Emerging ★</div>
  </div>

  <svg viewBox="0 0 560 520" xmlns="http://www.w3.org/2000/svg" id="map-svg">

    <!-- Chandigarh reference -->
    <rect x="10" y="10" width="110" height="44" rx="4" fill="#F1EFE8" stroke="#B4B2A9" stroke-width="1"/>
    <text x="65" y="28" text-anchor="middle" font-size="11" font-weight="500" fill="#5F5E5A">Chandigarh</text>
    <text x="65" y="43" text-anchor="middle" font-size="9" fill="#888780">(reference point)</text>

    <!-- Airport -->
    <rect x="390" y="10" width="120" height="44" rx="4" fill="#E6F1FB" stroke="#B5D4F4" stroke-width="1"/>
    <text x="450" y="27" text-anchor="middle" font-size="11" font-weight="500" fill="#185FA5">✈ Airport</text>
    <text x="450" y="42" text-anchor="middle" font-size="9" fill="#378ADD">~10km from Sec 66</text>

    <!-- Airport Road line -->
    <line x1="120" y1="32" x2="390" y2="28" stroke="#D3D1C7" stroke-width="1.5" stroke-dasharray="4,3"/>
    <text x="255" y="20" text-anchor="middle" font-size="9" fill="#999">Airport Road (NH-5)</text>

    {sector_rects}

    <!-- Compass -->
    <g transform="translate(520, 460)">
      <circle cx="0" cy="0" r="16" fill="none" stroke="#D3D1C7" stroke-width="1"/>
      <text x="0" y="-4" text-anchor="middle" font-size="9" fill="#888">N</text>
      <line x1="0" y1="0" x2="0" y2="-12" stroke="#888" stroke-width="1.5"/>
      <line x1="0" y1="0" x2="0" y2="12" stroke="#ccc" stroke-width="1"/>
      <line x1="-12" y1="0" x2="12" y2="0" stroke="#ccc" stroke-width="1"/>
    </g>

    <text x="280" y="510" text-anchor="middle" font-size="9" fill="#bbb">Schematic layout · not to exact geographic scale · Chandigarh is NW · Airport is NE</text>

  </svg>

  <div class="tooltip" id="tt">
    <div class="tt-name" id="tt-name"></div>
    <div class="tt-price" id="tt-price"></div>
    <div class="tt-yoy" id="tt-yoy"></div>
    <div class="tt-tier" id="tt-tier"></div>
    <div class="tt-note" id="tt-note"></div>
    <div class="tt-live" id="tt-live"></div>
  </div>

  <p class="note">{live_note} · hover any sector for details</p>
</div>

<script>
const tt = document.getElementById('tt');
const tierColors = {{
  'Premium':       ['#FCEBEB','#A32D2D'],
  'Upper-mid':     ['#FAEEDA','#854F0B'],
  'Mid':           ['#E1F5EE','#0F6E56'],
  'Affordable':    ['#E6F1FB','#185FA5'],
  'Emerging pick': ['#EEEDFE','#534AB7'],
}};

document.querySelectorAll('.sector').forEach(s => {{
  const show = (ex, ey) => {{
    const d = s.dataset;
    document.getElementById('tt-name').textContent = d.name;
    document.getElementById('tt-price').textContent = 'Price: ' + d.price;
    document.getElementById('tt-yoy').textContent = d.yoy;
    document.getElementById('tt-note').textContent = d.note;
    document.getElementById('tt-live').textContent = d.live;
    const tc = tierColors[d.tier] || ['#eee','#333'];
    const tierEl = document.getElementById('tt-tier');
    tierEl.textContent = d.tier;
    tierEl.style.background = tc[0];
    tierEl.style.color = tc[1];
    const cont = tt.closest ? tt.parentElement : tt.offsetParent || document.body;
    const cr = cont.getBoundingClientRect ? cont.getBoundingClientRect() : {{left:0,top:0,width:680,height:600}};
    let x = ex - cr.left + 14;
    let y = ey - cr.top + 14;
    if (x + 220 > cr.width) x -= 240;
    if (y + 170 > cr.height) y -= 185;
    tt.style.left = x + 'px';
    tt.style.top = y + 'px';
    tt.classList.add('show');
  }};
  s.addEventListener('mouseenter', e => show(e.clientX, e.clientY));
  s.addEventListener('mousemove', e => show(e.clientX, e.clientY));
  s.addEventListener('mouseleave', () => tt.classList.remove('show'));
  s.addEventListener('touchstart', e => {{ e.preventDefault(); const t = e.touches[0]; show(t.clientX, t.clientY); }}, {{passive:false}});
  s.addEventListener('touchend', () => setTimeout(() => tt.classList.remove('show'), 2000));
}});
</script>
</body>
</html>"""
