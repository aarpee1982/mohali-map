# Mohali Property Map — Streamlit App

Interactive, self-updating Mohali property price map.
Fetches live data from 99acres weekly. Falls back to baseline if blocked.
DeepSeek used as HTML parser fallback.

---

## Deploy to Streamlit Cloud (10 minutes)

### Step 1 — Push to GitHub
1. Create a new GitHub repo (can be private)
2. Upload all files in this folder to the repo root

### Step 2 — Deploy on Streamlit Cloud
1. Go to https://share.streamlit.io
2. Sign in with GitHub
3. Click "New app"
4. Select your repo → Branch: main → Main file: app.py
5. Click Deploy

### Step 3 — Add DeepSeek key (optional but recommended)
1. In Streamlit Cloud, go to your app → Settings → Secrets
2. Add:
   ```
   DEEPSEEK_API_KEY = "your_key_here"
   ```

### Step 4 — Share
You get a permanent URL like:
`https://your-name-mohali-map-app-xyz123.streamlit.app`

Send this on WhatsApp. Opens on mobile. No login needed.

---

## Files
- `app.py` — main Streamlit UI
- `fetcher.py` — data fetching (99acres API + DeepSeek fallback)
- `map_renderer.py` — generates interactive SVG map
- `requirements.txt` — Python dependencies
- `.streamlit/config.toml` — theme config
- `.streamlit/secrets.toml` — local secrets (DO NOT commit this to GitHub)

## How data refresh works
- On first load: fetches live data from 99acres
- Caches result for 7 days in `data_cache.json`
- "Refresh now" button forces a fresh fetch
- If 99acres blocks the request: shows last cached data
- If DeepSeek key is set: uses AI to parse HTML as a second attempt

## Local development
```bash
pip install -r requirements.txt
streamlit run app.py
```
