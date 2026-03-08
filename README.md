# 📈 Stock OHLCV Dashboard

A zero-backend stock data dashboard — CSV files live on GitHub, the HTML frontend reads them directly via raw URLs. No server, no database, no cost.

---

## Project Structure

```
your-repo/
├── data/
│   ├── manifest.json         ← auto-generated list of tickers
│   ├── RELIANCE_NS.csv       ← OHLCV data per ticker
│   ├── TCS_NS.csv
│   └── ...
├── index.html                ← dashboard (host via GitHub Pages)
├── update_data.py            ← data fetch + push script
└── README.md
```

---

## Setup (one-time)

### 1. Create the GitHub Repository

1. Go to [github.com/new](https://github.com/new)
2. Create a **public** repository (required for GitHub Pages + raw file access)
3. Note your `username` and `repo-name`

### 2. Get a GitHub Personal Access Token (PAT)

1. Go to **Settings → Developer Settings → Personal Access Tokens → Tokens (classic)**
2. Click **Generate new token**
3. Select scope: `repo` (full repo access)
4. Copy the token — you only see it once

### 3. Configure `update_data.py`

Open `update_data.py` and fill in the CONFIG block at the top:

```python
GITHUB_TOKEN  = "ghp_xxxxxxxxxxxx"     # your PAT
GITHUB_OWNER  = "your-github-username"
GITHUB_REPO   = "your-repo-name"
TICKERS       = ["RELIANCE.NS", "TCS.NS", "INFY.NS"]
PERIOD        = "2y"
INTERVAL      = "1d"
```

**Ticker format for NSE stocks:** append `.NS`  → e.g. `"RELIANCE.NS"`, `"HDFCBANK.NS"`  
**Ticker format for US stocks:** plain symbol   → e.g. `"AAPL"`, `"TSLA"`

### 4. Configure `index.html`

At the top of `index.html`, fill in the CONFIG block:

```js
const CONFIG = {
  owner:  "your-github-username",
  repo:   "your-repo-name",
  branch: "main",
};
```

### 5. Install Python Dependencies

```bash
pip install yfinance pandas requests
```

### 6. Run the Script

```bash
python update_data.py
```

This will:
- Download OHLCV history for all configured tickers
- Create/update `data/TICKER.csv` files in your repo
- Create/update `data/manifest.json` (used by the HTML to discover tickers)

### 7. Enable GitHub Pages

1. Go to your repo → **Settings → Pages**
2. Source: **Deploy from a branch** → `main` → `/ (root)`
3. Save — your dashboard will be live at:
   `https://your-username.github.io/your-repo-name/`

---

## Scheduling with Cron (Linux/macOS)

Run `crontab -e` and add a line. Examples:

```cron
# Every weekday at 6:30 PM IST (1:00 PM UTC)
0 13 * * 1-5 /usr/bin/python3 /path/to/update_data.py >> /var/log/stock_update.log 2>&1

# Every day at 9:00 AM
0 9 * * * /usr/bin/python3 /path/to/update_data.py
```

### On Windows — Task Scheduler

1. Open **Task Scheduler** → Create Basic Task
2. Trigger: Daily (set your time)
3. Action: Start a program → `python.exe` → Arguments: `C:\path\to\update_data.py`

---

## Adding More Tickers Later

1. Add the ticker string to `TICKERS` in `update_data.py`
2. Run `python update_data.py`
3. The new CSV + updated manifest are pushed automatically
4. Reload the dashboard — new ticker appears in the dropdown

---

## Dashboard Features

| Feature | Detail |
|---|---|
| Ticker selector | Populated from `manifest.json`, auto-updates |
| Range buttons | 1M / 3M / 6M / 1Y / 2Y / All |
| Custom date range | From / To date pickers |
| KPI cards | Latest close, day change, period return, period high/low, avg volume |
| Candlestick chart | Interactive, zoomable Plotly chart |
| Volume chart | Color-coded bar chart (green = up day, red = down day) |
| OHLCV table | Sortable by any column, searchable by date |
| Numbers | Formatted in `en-IN` locale (Indian numbering system) |

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `manifest.json` 404 | Run `update_data.py` at least once first |
| Ticker returns no data | Check Yahoo Finance ticker format (add `.NS` for NSE) |
| GitHub API 401 | Token expired or wrong scope — regenerate PAT with `repo` scope |
| GitHub API 422 | Branch name mismatch — check `GITHUB_BRANCH` in the script |
| CORS error in browser | Make sure repo is **public** |
| Dashboard blank | Check browser console — look for CONFIG mismatch |

---

## Tech Stack

- **Data source:** [yfinance](https://github.com/ranaroussi/yfinance)
- **Storage:** GitHub (flat file, CSV)
- **Charts:** [Plotly.js](https://plotly.com/javascript/)
- **CSV parsing:** [PapaParse](https://www.papaparse.com/)
- **Hosting:** GitHub Pages (free)
- **Backend:** None
