"""
update_data.py
==============
Fetches OHLCV data from Yahoo Finance (yfinance) and pushes
individual CSVs + a manifest.json to your GitHub repository.

Run manually:
    python update_data.py

Schedule via cron (example: every weekday at 6:30 PM IST):
    30 13 * * 1-5 /usr/bin/python3 /path/to/update_data.py >> /var/log/stock_update.log 2>&1

Requirements:
    pip install yfinance pandas requests
"""

import yfinance as yf
import pandas as pd
import requests
import base64
import json
import sys
from datetime import datetime, timezone

# ─────────────────────────────────────────────
#  CONFIG — edit these before first run
# ─────────────────────────────────────────────

GITHUB_TOKEN      = "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"   # github.com → Settings → Developer Settings → PAT (repo scope)
GITHUB_OWNER      = "anon-murgi"
GITHUB_REPO       = "stock-test"
GITHUB_BRANCH     = "main"

# Tickers to track — use Yahoo Finance format
# Indian NSE stocks: append .NS  (e.g. "RELIANCE.NS")
# Indian BSE stocks: append .BO  (e.g. "RELIANCE.BO")
# US stocks:         plain symbol (e.g. "AAPL")
TICKERS = [
    "RELIANCE.NS",
    "TCS.NS",
    "INFY.NS",
    "HDFCBANK.NS",
    "ICICIBANK.NS",
]

PERIOD   = "2y"   # How much history: 1d 5d 1mo 3mo 6mo 1y 2y 5y 10y ytd max
INTERVAL = "1d"   # Bar size: 1m 2m 5m 15m 30m 60m 90m 1h 1d 5d 1wk 1mo 3mo

# ─────────────────────────────────────────────
#  GITHUB HELPERS
# ─────────────────────────────────────────────

BASE_URL = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/contents"
HEADERS  = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept":        "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}


def get_file_sha(path: str) -> str | None:
    """Return the SHA of an existing file, or None if it doesn't exist."""
    r = requests.get(f"{BASE_URL}/{path}", headers=HEADERS)
    if r.status_code == 200:
        return r.json().get("sha")
    return None


def push_file(path: str, content: str, commit_message: str) -> bool:
    """Create or update a file in the repo. content must be a UTF-8 string."""
    encoded = base64.b64encode(content.encode("utf-8")).decode("utf-8")
    sha     = get_file_sha(path)

    payload = {
        "message": commit_message,
        "content": encoded,
        "branch":  GITHUB_BRANCH,
    }
    if sha:
        payload["sha"] = sha  # required for updates

    r = requests.put(f"{BASE_URL}/{path}", headers=HEADERS, json=payload)
    if r.status_code in (200, 201):
        action = "Updated" if sha else "Created"
        print(f"  ✓ {action}: {path}")
        return True
    else:
        print(f"  ✗ Failed to push {path}: {r.status_code} — {r.text[:200]}")
        return False


# ─────────────────────────────────────────────
#  DATA FETCHING
# ─────────────────────────────────────────────

def fetch_ohlcv(ticker: str) -> pd.DataFrame | None:
    """Download OHLCV data for a single ticker via yfinance."""
    try:
        tk   = yf.Ticker(ticker)
        df   = tk.history(period=PERIOD, interval=INTERVAL, auto_adjust=True)
        info = tk.fast_info

        if df.empty:
            print(f"  ✗ No data returned for {ticker}")
            return None, None

        # Standardise columns
        df = df[["Open", "High", "Low", "Close", "Volume"]].copy()
        df.index.name = "Date"
        df.index = df.index.tz_localize(None)          # strip timezone
        df.index = df.index.strftime("%Y-%m-%d")       # ISO date string
        df = df.round(4)
        df["Volume"] = df["Volume"].astype(int)

        # Basic metadata dict
        meta = {
            "ticker":       ticker,
            "name":         getattr(info, "company_name", ticker),
            "currency":     getattr(info, "currency",     "INR"),
            "exchange":     getattr(info, "exchange",     ""),
            "last_updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "rows":         len(df),
            "latest_close": float(df["Close"].iloc[-1]),
            "latest_date":  df.index[-1],
        }

        return df, meta

    except Exception as e:
        print(f"  ✗ Error fetching {ticker}: {e}")
        return None, None


# ─────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────

def main():
    now_str   = datetime.now().strftime("%Y-%m-%d %H:%M")
    manifest  = []                 # list of metadata dicts for all tickers
    success   = 0
    failed    = []

    print(f"\n{'═'*50}")
    print(f"  Stock DB Update — {now_str}")
    print(f"{'═'*50}\n")

    for ticker in TICKERS:
        print(f"→ {ticker}")
        df, meta = fetch_ohlcv(ticker)

        if df is None:
            failed.append(ticker)
            continue

        # Push CSV
        csv_content = df.to_csv()
        safe_ticker = ticker.replace(".", "_")           # avoid dots in filenames
        csv_path    = f"data/{safe_ticker}.csv"
        msg         = f"data: update {ticker} ({now_str})"

        if push_file(csv_path, csv_content, msg):
            meta["csv_path"] = csv_path                  # store path in manifest
            manifest.append(meta)
            success += 1
        else:
            failed.append(ticker)

    # Push manifest.json (used by the HTML to discover available tickers)
    manifest_json = json.dumps(manifest, indent=2, ensure_ascii=False)
    push_file(
        "data/manifest.json",
        manifest_json,
        f"data: update manifest ({now_str})",
    )

    # Summary
    print(f"\n{'─'*50}")
    print(f"  Done. {success}/{len(TICKERS)} tickers updated.")
    if failed:
        print(f"  Failed: {', '.join(failed)}")
    print(f"{'─'*50}\n")

    sys.exit(0 if not failed else 1)


if __name__ == "__main__":
    main()
