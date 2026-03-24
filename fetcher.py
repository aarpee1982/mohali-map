"""
fetcher.py
Tries to pull live data from 99acres internal locality API.
Falls back to hardcoded baseline if blocked/rate-limited.
DeepSeek is used only as an optional parser when raw HTML is returned instead of JSON.
"""

import requests
import json
import re
import os

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")

# Master sector list with baseline data (updated Jan 2026)
SECTORS = [
    {
        "id": "sector-69-mohali",
        "name": "Sector 69",
        "tier": "Premium",
        "price_avg": 20000,
        "price_label": "~₹20,000",
        "yoy_pct": 28.6,
        "note": "Highest price in Mohali. New premium launches.",
        "map_x": 155, "map_y": 75,
    },
    {
        "id": "sector-71-mohali",
        "name": "Sector 71",
        "tier": "Premium",
        "price_avg": 17500,
        "price_label": "~₹17,500",
        "yoy_pct": None,
        "note": "Mature, close to Chandigarh. Limited fresh supply.",
        "map_x": 40, "map_y": 145,
    },
    {
        "id": "phase-10-mohali",
        "name": "Phase 10",
        "tier": "Premium",
        "price_avg": 14700,
        "price_label": "₹9,750–14,700",
        "yoy_pct": None,
        "note": "Villas & large plots. Established premium address.",
        "map_x": 40, "map_y": 75,
    },
    {
        "id": "sector-66a-mohali",
        "name": "Sector 66A",
        "tier": "Premium",
        "price_avg": 11150,
        "price_label": "~₹11,150",
        "yoy_pct": 20.5,
        "note": "JLPL Falcon View, Galaxy Heights. Airport Road spine.",
        "map_x": 260, "map_y": 75,
    },
    {
        "id": "sector-70-mohali",
        "name": "Sector 70",
        "tier": "Premium",
        "price_avg": 10800,
        "price_label": "~₹10,800",
        "yoy_pct": 20.7,
        "note": "Mature sector, Airport Road belt.",
        "map_x": 280, "map_y": 145,
    },
    {
        "id": "sector-82-mohali",
        "name": "Sector 82",
        "tier": "Upper-mid",
        "price_avg": 9950,
        "price_label": "~₹9,950",
        "yoy_pct": 19.2,
        "note": "JLPL township. Amity University nearby.",
        "map_x": 370, "map_y": 145,
    },
    {
        "id": "sector-66-mohali",
        "name": "Sector 66",
        "tier": "Upper-mid",
        "price_avg": 8900,
        "price_label": "~₹8,900",
        "yoy_pct": None,
        "note": "ISB, IT City, Airport proximity. Strong rental demand.",
        "map_x": 370, "map_y": 75,
    },
    {
        "id": "sector-92-mohali",
        "name": "Sector 92",
        "tier": "Mid",
        "price_avg": 8650,
        "price_label": "~₹8,650",
        "yoy_pct": 40.7,
        "note": "Fastest appreciating mid-sector. MC expansion confirmed.",
        "map_x": 280, "map_y": 215,
    },
    {
        "id": "sector-88-mohali",
        "name": "Sector 88",
        "tier": "Mid",
        "price_avg": 9136,
        "price_label": "~₹9,136",
        "yoy_pct": 8.0,
        "note": "Govt offices anchor. Hero Realty active. MC expansion incoming.",
        "map_x": 40, "map_y": 215,
    },
    {
        "id": "aerocity-mohali",
        "name": "Aerocity",
        "tier": "Mid",
        "price_avg": 8100,
        "price_label": "₹7,400–10,350",
        "yoy_pct": 15.7,
        "note": "Next to airport. GMADA Aerotropolis. Strong long-term play.",
        "map_x": 460, "map_y": 145,
    },
    {
        "id": "sector-99-mohali",
        "name": "Sector 99",
        "tier": "Mid",
        "price_avg": 8050,
        "price_label": "~₹8,050",
        "yoy_pct": 16.7,
        "note": "Hero Realty paid ₹260Cr for land here. Aerotropolis adjacency.",
        "map_x": 460, "map_y": 215,
    },
    {
        "id": "it-city-mohali",
        "name": "IT City",
        "tier": "Mid",
        "price_avg": 7750,
        "price_label": "₹7,000–8,500",
        "yoy_pct": 12.0,
        "note": "1,700 acres active GMADA IT park. Workforce housing anchor.",
        "map_x": 155, "map_y": 215,
    },
    {
        "id": "tdi-city-mohali",
        "name": "TDI City / Sec 117",
        "tier": "Upper-mid",
        "price_avg": 9250,
        "price_label": "₹6,300–9,250",
        "yoy_pct": 37.0,
        "note": "TDI gated township at ₹9.2k. Adjacent Sec 117 at ₹6.3k — gap closing.",
        "map_x": 155, "map_y": 145,
    },
    {
        "id": "sector-91-mohali",
        "name": "Sector 91 ★",
        "tier": "Emerging pick",
        "price_avg": 6900,
        "price_label": "~₹6,900",
        "yoy_pct": 6.2,
        "note": "JLPL 143-acre township. Green, low crime. 91.7% in 5 yrs. Top stealth pick.",
        "map_x": 370, "map_y": 285,
        "star": True,
    },
    {
        "id": "sector-94-mohali",
        "name": "Sector 94",
        "tier": "Emerging pick",
        "price_avg": 7500,
        "price_label": "~₹7,500",
        "yoy_pct": None,
        "note": "JLPL Mixed-Use project. Part of same 400-acre mega-township. MC expansion confirmed.",
        "map_x": 460, "map_y": 285,
    },
    {
        "id": "sunny-enclave-kharar",
        "name": "Sunny Enclave",
        "tier": "Affordable",
        "price_avg": 6100,
        "price_label": "~₹6,100",
        "yoy_pct": None,
        "note": "Popular gated family area. Technically Kharar — outside pure Mohali.",
        "map_x": 40, "map_y": 355,
    },
    {
        "id": "kharar-mohali",
        "name": "Kharar",
        "tier": "Affordable",
        "price_avg": 4750,
        "price_label": "~₹4,750",
        "yoy_pct": 14.5,
        "note": "Most affordable. High volume, good rental yield. Outside Mohali proper.",
        "map_x": 310, "map_y": 355,
    },
    {
        "id": "sector-124-mohali",
        "name": "Sectors 124/126",
        "tier": "Affordable",
        "price_avg": 4625,
        "price_label": "₹4,300–4,950",
        "yoy_pct": None,
        "note": "Budget entry point. Longer appreciation horizon.",
        "map_x": 180, "map_y": 355,
    },
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.99acres.com/",
    "Accept-Language": "en-IN,en;q=0.9",
}

# 99acres locality slug → price trend endpoint pattern
def _99acres_url(locality_slug: str) -> str:
    return f"https://www.99acres.com/api/v2/localities/price-trend?localitySlug={locality_slug}&propType=1"

def _try_fetch_99acres(sector: dict) -> dict:
    """Attempt to get live price from 99acres API. Returns updated sector dict."""
    try:
        url = _99acres_url(sector["id"])
        resp = requests.get(url, headers=HEADERS, timeout=8)
        if resp.status_code == 200:
            data = resp.json()
            # Navigate the response tree
            trend = data.get("data", {}).get("priceTrend", {})
            current = trend.get("currentAvgRate") or trend.get("avgRate")
            yoy = trend.get("yoyChange")
            if current:
                updated = sector.copy()
                updated["price_avg"] = int(current)
                updated["price_label"] = f"₹{int(current):,}"
                if yoy is not None:
                    updated["yoy_pct"] = round(float(yoy), 1)
                updated["live"] = True
                return updated
    except Exception:
        pass
    return sector  # return baseline if anything fails

def _try_parse_with_deepseek(html_text: str, sector_name: str) -> dict | None:
    """Use DeepSeek to extract price from raw HTML if JSON fails."""
    if not DEEPSEEK_API_KEY:
        return None
    try:
        import openai
        client = openai.OpenAI(
            api_key=DEEPSEEK_API_KEY,
            base_url="https://api.deepseek.com"
        )
        prompt = f"""Extract the current average property price per sq ft for "{sector_name}" from this 99acres page snippet.
Return ONLY valid JSON: {{"price_avg": <integer>, "yoy_pct": <float or null>}}
No explanation. If you cannot find the price, return {{"price_avg": null, "yoy_pct": null}}

Page content (first 3000 chars):
{html_text[:3000]}"""
        resp = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100,
            temperature=0
        )
        raw = resp.choices[0].message.content.strip()
        return json.loads(raw)
    except Exception:
        return None

def fetch_all_sectors() -> list[dict]:
    """
    Fetch live data for all sectors.
    Strategy:
    1. Try 99acres JSON API
    2. If blocked, try 99acres HTML + DeepSeek parser
    3. Fall back to baseline
    """
    results = []
    for sector in SECTORS:
        updated = _try_fetch_99acres(sector)
        # If still using baseline, try HTML + DeepSeek
        if not updated.get("live") and DEEPSEEK_API_KEY:
            try:
                html_url = f"https://www.99acres.com/{sector['id']}-overview-piffid"
                resp = requests.get(html_url, headers=HEADERS, timeout=10)
                if resp.status_code == 200:
                    parsed = _try_parse_with_deepseek(resp.text, sector["name"])
                    if parsed and parsed.get("price_avg"):
                        updated = sector.copy()
                        updated["price_avg"] = parsed["price_avg"]
                        updated["price_label"] = f"₹{parsed['price_avg']:,}"
                        if parsed.get("yoy_pct") is not None:
                            updated["yoy_pct"] = parsed["yoy_pct"]
                        updated["live"] = True
            except Exception:
                pass
        results.append(updated)
        # Be polite to the server
        import time
        time.sleep(0.3)
    return results
