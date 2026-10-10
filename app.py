#!/usr/bin/env python3
"""
Market & Tech Portfolio Monitor
Tracks:
- Invesco QQQ Trust (NASDAQ: QQQ)
- Micron Technology (NASDAQ: MU)
- SK Hynix Inc. (US ADR: SKHY / KRX: 000660.KS)
- Compact Honolulu, Hawaii status with Clement Weather / Severe Weather analysis
- Real-time stock movement catalysts & news summaries

Zero external dependencies required (uses standard library: urllib, json, http.server).
"""

import sys
import os
import json
import urllib.request
import urllib.error
from datetime import datetime
import http.server
import socketserver
import webbrowser
import threading
import time

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

PORT = 8080
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# WMO Weather interpretation codes
WMO_CODES = {
    0: ("Clear / Sunny", "☀️"),
    1: ("Mainly Clear", "🌤️"),
    2: ("Partly Cloudy", "⛅"),
    3: ("Overcast", "☁️"),
    45: ("Foggy", "🌫️"),
    48: ("Rime Fog", "🌫️"),
    51: ("Light Drizzle", "🌦️"),
    53: ("Moderate Drizzle", "🌧️"),
    55: ("Dense Drizzle", "🌧️"),
    61: ("Slight Rain", "🌦️"),
    63: ("Moderate Rain", "🌧️"),
    65: ("Heavy Rain", "🌧️"),
    80: ("Passing Showers", "🌦️"),
    81: ("Moderate Showers", "🌧️"),
    82: ("Violent Showers", "⛈️"),
    95: ("Thunderstorm", "⚡"),
    96: ("Thunderstorm with Hail", "⛈️"),
}


def fetch_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=12) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as e:
        print(f"[Warning] Failed to fetch {url}: {e}", file=sys.stderr)
        return None


def get_stock_data(symbol):
    """Fetch recent price data and 5-day history from Yahoo Finance."""
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=5d"
    data = fetch_json(url)
    if not data or "chart" not in data or not data["chart"].get("result"):
        return None

    result = data["chart"]["result"][0]
    meta = result.get("meta", {})
    price = meta.get("regularMarketPrice")
    prev_close = meta.get("chartPreviousClose") or meta.get("previousClose")

    if price is None or prev_close is None:
        return None

    change = price - prev_close
    change_pct = (change / prev_close) * 100 if prev_close else 0.0

    return {
        "symbol": symbol,
        "currency": meta.get("currency", "USD"),
        "exchange": meta.get("exchangeName", "US"),
        "price": round(price, 2),
        "prev_close": round(prev_close, 2),
        "change": round(change, 2),
        "change_pct": round(change_pct, 2),
        "high": round(meta.get("regularMarketDayHigh", price), 2),
        "low": round(meta.get("regularMarketDayLow", price), 2),
        "volume": meta.get("regularMarketVolume", 0)
    }


def get_stock_news(symbol):
    """Fetch recent news headlines from Yahoo Finance search."""
    url = f"https://query1.finance.yahoo.com/v1/finance/search?q={symbol}&newsCount=6"
    data = fetch_json(url)
    if not data or "news" not in data:
        return []

    news_items = []
    for item in data.get("news", [])[:4]:
        title = item.get("title", "")
        publisher = item.get("publisher", "")
        link = item.get("link", "#")
        provider_time = item.get("providerPublishTime")
        time_str = datetime.fromtimestamp(provider_time).strftime("%b %d, %H:%M") if provider_time else ""
        if title:
            news_items.append({
                "title": title,
                "publisher": publisher,
                "link": link,
                "time": time_str
            })
    return news_items


def analyze_driver(symbol, stock_data, news_items):
    """Generate synthesized summary of what drove stock movements."""
    change_pct = stock_data["change_pct"] if stock_data else 0
    headlines = [n["title"] for n in news_items]
    headline_text = " ".join(headlines).lower()

    if symbol == "QQQ":
        core_themes = []
        if "rate" in headline_text or "fed" in headline_text or "yield" in headline_text or "inflation" in headline_text:
            core_themes.append("Federal Reserve interest rate projections and benchmark Treasury yield shifts")
        if "ai" in headline_text or "nvidia" in headline_text or "apple" in headline_text or "microsoft" in headline_text:
            core_themes.append("Mega-cap tech 'Magnificent Seven' capital expenditure and AI hardware investment trends")
        if "rally" in headline_text or "market" in headline_text or "stocks" in headline_text or "earnings" in headline_text:
            core_themes.append("Broader tech equity sentiment and corporate earnings season expectations")

        if not core_themes:
            core_themes = [
                "Mega-cap tech valuations (NVIDIA, Apple, Microsoft, Amazon, Alphabet)",
                "Treasury yield fluctuations and macroeconomic interest rate expectations",
                "Enterprise spending trajectory on cloud computing and AI infrastructure"
            ]

        summary = (
            f"QQQ moved {change_pct:+.2f}%. Primary market drivers: "
            + "; ".join(core_themes) + ". "
            f"As the benchmark ETF tracking the top 100 non-financial companies on Nasdaq, "
            f"QQQ reflects overarching institutional appetite for technology growth stocks."
        )

    elif symbol == "MU":
        core_themes = []
        if "ai" in headline_text or "revenue" in headline_text:
            core_themes.append("AI hardware revenue sentiment and hyperscaler datacenter memory demand")
        if "hbm" in headline_text or "memory" in headline_text:
            core_themes.append("High-Bandwidth Memory (HBM3E/HBM4) production yields and customer allocation")
        if "cramer" in headline_text or "analyst" in headline_text or "wall street" in headline_text:
            core_themes.append("Wall Street analyst price target revisions and cyclical memory valuation expectations")

        if not core_themes:
            core_themes = [
                "Cyclical DRAM/NAND memory pricing contracts",
                "High-Bandwidth Memory (HBM3E) shipments to AI accelerator customers",
                "Broader semiconductor sector momentum (SOX / AI chip indexes)"
            ]

        summary = (
            f"Micron moved {change_pct:+.2f}%. Primary drivers: "
            + "; ".join(core_themes) + ". "
            f"As one of the world's top three memory producers alongside SK Hynix and Samsung, "
            f"Micron's valuation is driven by datacenter AI server memory demand against standard consumer PC/mobile cyclicality."
        )

    elif symbol == "SKHY":
        core_themes = []
        if "nvidia" in headline_text or "ai" in headline_text:
            core_themes.append("NVIDIA supply chain dynamics and dominant share in HBM3E packaging")
        if "china" in headline_text or "export" in headline_text:
            core_themes.append("Global trade & semiconductor export policy shifts")
        if "etf" in headline_text or "semiconductor" in headline_text:
            core_themes.append("Global tech fund flows and overseas ADR liquidity adjustments")

        if not core_themes:
            core_themes = [
                "Dominant market position supplying 8-layer and 12-layer HBM3E memory for NVIDIA AI GPUs",
                "Capacity expansion at Cheongju/Yongin fabs and capital expenditure adjustments",
                "Currency exchange dynamics (KRW/USD) and overseas ADR trading liquidity"
            ]

        summary = (
            f"SK Hynix moved {change_pct:+.2f}% in US trading. Primary catalysts: "
            + "; ".join(core_themes) + ". "
            f"SK Hynix remains the premier supplier of cutting-edge HBM to top-tier AI GPU manufacturers, "
            f"making its stock price closely correlated with datacenter accelerator roadmaps."
        )
    else:
        summary = f"Stock moved {change_pct:+.2f}% driven by macroeconomic trends and sector news."

    return {
        "summary": summary
    }


def get_honolulu_weather():
    """Fetch current conditions and evaluate if weather is clement or has severe conditions ahead."""
    url = (
        "https://api.open-meteo.com/v1/forecast?"
        "latitude=21.3069&longitude=-157.8583"
        "&current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m,wind_direction_10m"
        "&daily=weather_code,precipitation_sum,wind_gusts_10m_max"
        "&temperature_unit=fahrenheit&wind_speed_unit=mph&precipitation_unit=inch"
        "&timezone=Pacific%2FHonolulu"
    )
    data = fetch_json(url)
    if not data or "current" not in data:
        return None

    curr = data["current"]
    code = curr.get("weather_code", 0)
    cond_text, cond_icon = WMO_CODES.get(code, ("Fair", "🌤️"))

    wind_dir_deg = curr.get("wind_direction_10m", 0)
    wind_dir = "NE" if 22.5 <= wind_dir_deg < 67.5 else \
               "E" if 67.5 <= wind_dir_deg < 112.5 else \
               "SE" if 112.5 <= wind_dir_deg < 157.5 else \
               "S" if 157.5 <= wind_dir_deg < 202.5 else \
               "SW" if 202.5 <= wind_dir_deg < 247.5 else \
               "W" if 247.5 <= wind_dir_deg < 292.5 else \
               "NW" if 292.5 <= wind_dir_deg < 337.5 else "N"

    # Analyze if upcoming weather is Clement or has Severe weather ahead
    daily = data.get("daily", {})
    codes = daily.get("weather_code", [])
    precip = daily.get("precipitation_sum", [])
    gusts = daily.get("wind_gusts_10m_max", [])

    severe_alerts = []
    for c in codes[:5]:
        if c in [95, 96, 99]:
            severe_alerts.append("Thunderstorms or lightning expected")
            break
        elif c in [65, 82]:
            severe_alerts.append("Heavy torrential downpours forecasted")
            break

    for g in gusts[:5]:
        if g and g >= 45:
            severe_alerts.append(f"Gale-force gusts ({g:.0f} mph)")
            break

    for p in precip[:5]:
        if p and p >= 2.0:
            severe_alerts.append("High rainfall / localized flooding potential")
            break

    if not severe_alerts:
        clement_status = "Clement Weather: Calm"
        clement_is_severe = False
        clement_desc = "No severe weather ahead. Pleasant trade winds & clear island conditions expected for the next 7 days."
    else:
        clement_status = "Weather Notice Ahead"
        clement_is_severe = True
        clement_desc = "Notice: " + "; ".join(severe_alerts) + " ahead in Oahu forecast."

    return {
        "city": "Honolulu, HI",
        "temperature": round(curr.get("temperature_2m", 80), 1),
        "feels_like": round(curr.get("apparent_temperature", 80), 1),
        "humidity": curr.get("relative_humidity_2m", 60),
        "precipitation": curr.get("precipitation", 0.0),
        "wind_speed": round(curr.get("wind_speed_10m", 10), 1),
        "wind_direction": wind_dir,
        "condition": cond_text,
        "icon": cond_icon,
        "updated": curr.get("time", ""),
        "clement": {
            "status": clement_status,
            "is_severe": clement_is_severe,
            "description": clement_desc
        }
    }


def get_dashboard_payload():
    """Aggregate all live data into a single payload."""
    # Stocks: MU, SKHY, QQQ (in requested order)
    tickers_info = [
        ("MU", "Micron Technology", "NASDAQ", "Semiconductor / Memory"),
        ("SKHY", "SK Hynix Inc.", "US (ADR / OTC)", "HBM Leader / AI Memory"),
        ("QQQ", "Invesco QQQ Trust", "NASDAQ (Benchmark ETF)", "Tech Benchmark / Nasdaq 100")
    ]

    stocks = {}
    for sym, name, exch, badge_name in tickers_info:
        s_data = get_stock_data(sym)
        news = get_stock_news(sym)
        driver = analyze_driver(sym, s_data, news)
        stocks[sym] = {
            "name": name,
            "ticker": sym,
            "exchange": exch,
            "badge": badge_name,
            "data": s_data,
            "news": news,
            "driver": driver
        }

    # Reference for SK Hynix Korean primary listing
    sk_krx_data = get_stock_data("000660.KS")
    stocks["SKHY"]["korea_ref"] = sk_krx_data

    # Weather (compact)
    weather = get_honolulu_weather()

    return {
        "timestamp": datetime.now().strftime("%Y-%m-%d %I:%M:%S %p HST"),
        "stocks": stocks,
        "weather": weather
    }


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Market & Tech Portfolio Monitor</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #0b0f19;
            --card-bg: rgba(22, 29, 47, 0.78);
            --card-border: rgba(255, 255, 255, 0.08);
            --text-main: #f1f5f9;
            --text-muted: #94a3b8;
            --accent: #38bdf8;
            --accent-glow: rgba(56, 189, 248, 0.25);
            --green: #10b981;
            --green-glow: rgba(16, 185, 129, 0.15);
            --red: #f43f5e;
            --red-glow: rgba(244, 63, 94, 0.15);
            --font: 'Inter', -apple-system, sans-serif;
            --mono: 'JetBrains Mono', monospace;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }

        body {
            background-color: var(--bg);
            background-image: 
                radial-gradient(circle at 10% 15%, rgba(56, 189, 248, 0.06) 0%, transparent 40%),
                radial-gradient(circle at 90% 85%, rgba(139, 92, 246, 0.05) 0%, transparent 40%);
            color: var(--text-main);
            font-family: var(--font);
            min-height: 100vh;
            padding: 1.5rem 1.25rem;
            line-height: 1.5;
        }

        .container {
            max-width: 1360px;
            margin: 0 auto;
        }

        /* Compact Header */
        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
            padding-bottom: 0.85rem;
            border-bottom: 1px solid var(--card-border);
            flex-wrap: wrap;
            gap: 1rem;
        }

        .header-title h1 {
            font-size: 1.6rem;
            font-weight: 800;
            letter-spacing: -0.02em;
            background: linear-gradient(135deg, #ffffff 40%, var(--accent) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .header-title p {
            color: var(--text-muted);
            font-size: 0.825rem;
            margin-top: 0.2rem;
        }

        .header-actions {
            display: flex;
            align-items: center;
            gap: 0.85rem;
        }

        .refresh-btn {
            background: linear-gradient(135deg, #0284c7, #0369a1);
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 8px;
            font-weight: 600;
            font-size: 0.825rem;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 0.45rem;
            transition: all 0.2s ease;
            box-shadow: 0 4px 12px var(--accent-glow);
        }

        .refresh-btn:hover {
            transform: translateY(-1px);
            filter: brightness(1.1);
        }

        /* Very Small Compact Weather Ribbon with Clement Weather status */
        .weather-ribbon {
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: rgba(15, 23, 42, 0.7);
            border: 1px solid var(--card-border);
            border-radius: 10px;
            padding: 0.5rem 1rem;
            margin-bottom: 1.5rem;
            font-size: 0.825rem;
            flex-wrap: wrap;
            gap: 0.75rem;
            backdrop-filter: blur(8px);
        }

        .weather-left {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            flex-wrap: wrap;
        }

        .weather-loc {
            font-weight: 600;
            color: #e2e8f0;
            display: flex;
            align-items: center;
            gap: 0.35rem;
        }

        .weather-temp {
            font-family: var(--mono);
            font-weight: 700;
            color: #38bdf8;
            font-size: 0.95rem;
        }

        .weather-meta {
            color: var(--text-muted);
            font-size: 0.8rem;
        }

        .clement-section {
            display: flex;
            align-items: center;
            gap: 0.65rem;
            flex-wrap: wrap;
        }

        .clement-pill {
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            padding: 0.2rem 0.65rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
            letter-spacing: 0.02em;
        }

        .clement-calm {
            background: rgba(16, 185, 129, 0.15);
            color: #34d399;
            border: 1px solid rgba(16, 185, 129, 0.3);
        }

        .clement-alert {
            background: rgba(245, 158, 11, 0.15);
            color: #fbbf24;
            border: 1px solid rgba(245, 158, 11, 0.3);
        }

        .clement-dot {
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background-color: currentColor;
            display: inline-block;
        }

        .clement-desc {
            color: #cbd5e1;
            font-size: 0.785rem;
        }

        /* 3-Column Stock Grid */
        .stocks-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 1.25rem;
        }

        @media (max-width: 1080px) {
            .stocks-grid { grid-template-columns: 1fr; }
        }

        .card {
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 14px;
            padding: 1.25rem;
            backdrop-filter: blur(12px);
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }

        .card:hover {
            border-color: rgba(255, 255, 255, 0.15);
        }

        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 1rem;
        }

        .company-name {
            font-size: 1.15rem;
            font-weight: 700;
            color: #fff;
        }

        .ticker-sub {
            color: var(--text-muted);
            font-size: 0.8rem;
            font-family: var(--mono);
        }

        .badge {
            display: inline-flex;
            align-items: center;
            padding: 0.2rem 0.55rem;
            border-radius: 9999px;
            font-size: 0.7rem;
            font-weight: 600;
            letter-spacing: 0.04em;
            text-transform: uppercase;
        }

        .badge-qqq { background: rgba(14, 165, 233, 0.15); color: #38bdf8; border: 1px solid rgba(14, 165, 233, 0.3); }
        .badge-mu { background: rgba(99, 102, 241, 0.15); color: #818cf8; border: 1px solid rgba(99, 102, 241, 0.3); }
        .badge-skhy { background: rgba(168, 85, 247, 0.15); color: #c084fc; border: 1px solid rgba(168, 85, 247, 0.3); }

        .price-section {
            display: flex;
            align-items: baseline;
            gap: 0.85rem;
            margin-bottom: 0.85rem;
        }

        .price-main {
            font-size: 2rem;
            font-weight: 800;
            font-family: var(--mono);
            letter-spacing: -0.03em;
        }

        .price-change {
            font-size: 0.95rem;
            font-weight: 700;
            font-family: var(--mono);
            padding: 0.2rem 0.55rem;
            border-radius: 6px;
            display: inline-flex;
            align-items: center;
        }

        .change-up { color: var(--green); background: var(--green-glow); }
        .change-down { color: var(--red); background: var(--red-glow); }

        .stats-row {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 0.5rem;
            padding: 0.65rem 0;
            border-top: 1px solid var(--card-border);
            border-bottom: 1px solid var(--card-border);
            margin-bottom: 1rem;
            font-size: 0.8rem;
        }

        .stat-item {
            display: flex;
            flex-direction: column;
        }

        .stat-label {
            color: var(--text-muted);
            font-size: 0.7rem;
            text-transform: uppercase;
            letter-spacing: 0.03em;
        }

        .stat-val {
            font-weight: 600;
            font-family: var(--mono);
            font-size: 0.825rem;
        }

        .driver-box {
            background: rgba(15, 23, 42, 0.65);
            border-left: 3px solid var(--accent);
            border-radius: 8px;
            padding: 0.85rem;
            margin-bottom: 1rem;
        }

        .driver-title {
            font-size: 0.75rem;
            text-transform: uppercase;
            font-weight: 700;
            letter-spacing: 0.05em;
            color: var(--accent);
            margin-bottom: 0.35rem;
            display: flex;
            align-items: center;
            gap: 0.35rem;
        }

        .driver-text {
            font-size: 0.825rem;
            color: #cbd5e1;
            line-height: 1.4;
        }

        .news-section h4 {
            font-size: 0.725rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--text-muted);
            margin-bottom: 0.6rem;
        }

        .news-list {
            list-style: none;
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }

        .news-item a {
            color: #e2e8f0;
            text-decoration: none;
            font-size: 0.8rem;
            display: block;
            line-height: 1.35;
            transition: color 0.15s ease;
        }

        .news-item a:hover {
            color: var(--accent);
            text-decoration: underline;
        }

        .news-meta {
            font-size: 0.7rem;
            color: var(--text-muted);
            margin-top: 0.1rem;
        }

        footer {
            margin-top: 2rem;
            text-align: center;
            color: var(--text-muted);
            font-size: 0.75rem;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="header-title">
                <h1>Market & Tech Portfolio Monitor</h1>
                <p id="last-updated">Synchronizing market data...</p>
            </div>
            <div class="header-actions">
                <button class="refresh-btn" onclick="fetchData()">
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"/></svg>
                    Refresh
                </button>
            </div>
        </header>

        <!-- Compact Hawaiian Weather & Clement Weather Status Ribbon -->
        <div class="weather-ribbon" id="weather-ribbon">
            <div class="weather-left">
                <span class="weather-loc">🌴 Honolulu, HI</span>
                <span class="weather-temp" id="w-temp">--°F</span>
                <span class="weather-meta" id="w-cond">Loading conditions...</span>
                <span class="weather-meta" id="w-meta">Winds: -- mph • Humidity: --%</span>
            </div>
            <div class="clement-section">
                <span class="clement-pill clement-calm" id="clement-pill">
                    <span class="clement-dot"></span>
                    <span id="clement-status">Clement Weather: Calm</span>
                </span>
                <span class="clement-desc" id="clement-desc">Checking upcoming conditions...</span>
            </div>
        </div>

        <!-- 3-Column Stock Cards (Order: Micron, SK Hynix, QQQ) -->
        <div class="stocks-grid">
            <!-- 1. Micron Card -->
            <div class="card" id="card-mu">
                <div>
                    <div class="card-header">
                        <div>
                            <div class="company-name">Micron Technology</div>
                            <div class="ticker-sub">NASDAQ: MU</div>
                        </div>
                        <span class="badge badge-mu">Memory Leader</span>
                    </div>

                    <div class="price-section">
                        <span class="price-main" id="mu-price">--</span>
                        <span class="price-change" id="mu-change">--</span>
                    </div>

                    <div class="stats-row">
                        <div class="stat-item">
                            <span class="stat-label">Prev Close</span>
                            <span class="stat-val" id="mu-prev">--</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">Day Range</span>
                            <span class="stat-val" id="mu-range">--</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">Volume</span>
                            <span class="stat-val" id="mu-vol">--</span>
                        </div>
                    </div>

                    <div class="driver-box">
                        <div class="driver-title">
                            <span>⚡</span> Movement Catalyst & Driver
                        </div>
                        <div class="driver-text" id="mu-driver">Analyzing market catalyst...</div>
                    </div>
                </div>

                <div class="news-section">
                    <h4>Recent Headlines</h4>
                    <ul class="news-list" id="mu-news">
                        <li>Loading news...</li>
                    </ul>
                </div>
            </div>

            <!-- 2. SK Hynix Card -->
            <div class="card" id="card-skhy">
                <div>
                    <div class="card-header">
                        <div>
                            <div class="company-name">SK Hynix Inc.</div>
                            <div class="ticker-sub">US: SKHY / KRX: 000660</div>
                        </div>
                        <span class="badge badge-skhy">AI HBM Supplier</span>
                    </div>

                    <div class="price-section">
                        <span class="price-main" id="skhy-price">--</span>
                        <span class="price-change" id="skhy-change">--</span>
                    </div>

                    <div class="stats-row">
                        <div class="stat-item">
                            <span class="stat-label">Prev Close (USD)</span>
                            <span class="stat-val" id="skhy-prev">--</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">Day Range (USD)</span>
                            <span class="stat-val" id="skhy-range">--</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">Korea KRX</span>
                            <span class="stat-val" id="skhy-krx">--</span>
                        </div>
                    </div>

                    <div class="driver-box">
                        <div class="driver-title">
                            <span>⚡</span> Movement Catalyst & Driver
                        </div>
                        <div class="driver-text" id="skhy-driver">Analyzing market catalyst...</div>
                    </div>
                </div>

                <div class="news-section">
                    <h4>Recent Headlines</h4>
                    <ul class="news-list" id="skhy-news">
                        <li>Loading news...</li>
                    </ul>
                </div>
            </div>

            <!-- 3. QQQ Card -->
            <div class="card" id="card-qqq">
                <div>
                    <div class="card-header">
                        <div>
                            <div class="company-name">Invesco QQQ Trust</div>
                            <div class="ticker-sub">NASDAQ: QQQ</div>
                        </div>
                        <span class="badge badge-qqq">Tech Benchmark</span>
                    </div>

                    <div class="price-section">
                        <span class="price-main" id="qqq-price">--</span>
                        <span class="price-change" id="qqq-change">--</span>
                    </div>

                    <div class="stats-row">
                        <div class="stat-item">
                            <span class="stat-label">Prev Close</span>
                            <span class="stat-val" id="qqq-prev">--</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">Day Range</span>
                            <span class="stat-val" id="qqq-range">--</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">Volume</span>
                            <span class="stat-val" id="qqq-vol">--</span>
                        </div>
                    </div>

                    <div class="driver-box">
                        <div class="driver-title">
                            <span>⚡</span> Movement Catalyst & Driver
                        </div>
                        <div class="driver-text" id="qqq-driver">Analyzing market catalyst...</div>
                    </div>
                </div>

                <div class="news-section">
                    <h4>Recent Headlines</h4>
                    <ul class="news-list" id="qqq-news">
                        <li>Loading news...</li>
                    </ul>
                </div>
            </div>
        </div>

        <footer>
            Market data via Yahoo Finance • Weather provided by Open-Meteo • Zero external dependencies
        </footer>
    </div>

    <script>
        function formatNumber(num) {
            return num ? num.toLocaleString() : '--';
        }

        function populateStock(ticker, symData) {
            const lower = ticker.toLowerCase();
            if (!symData || !symData.data) return;
            const d = symData.data;

            document.getElementById(`${lower}-price`).textContent = '$' + d.price.toFixed(2);
            const chgElem = document.getElementById(`${lower}-change`);
            const sign = d.change >= 0 ? '+' : '';
            chgElem.textContent = `${sign}$${d.change.toFixed(2)} (${sign}${d.change_pct.toFixed(2)}%)`;
            chgElem.className = 'price-change ' + (d.change >= 0 ? 'change-up' : 'change-down');

            document.getElementById(`${lower}-prev`).textContent = '$' + d.prev_close.toFixed(2);
            document.getElementById(`${lower}-range`).textContent = `$${d.low.toFixed(2)} - $${d.high.toFixed(2)}`;

            const volElem = document.getElementById(`${lower}-vol`);
            if (volElem) volElem.textContent = formatNumber(d.volume);

            const driverElem = document.getElementById(`${lower}-driver`);
            if (driverElem && symData.driver) {
                driverElem.textContent = symData.driver.summary;
            }

            const newsList = document.getElementById(`${lower}-news`);
            if (newsList) {
                newsList.innerHTML = '';
                if (symData.news && symData.news.length > 0) {
                    symData.news.forEach(n => {
                        const li = document.createElement('li');
                        li.className = 'news-item';
                        li.innerHTML = `<a href="${n.link}" target="_blank" rel="noopener noreferrer">${n.title}</a>
                                        <div class="news-meta">${n.publisher} • ${n.time}</div>`;
                        newsList.appendChild(li);
                    });
                } else {
                    newsList.innerHTML = '<li class="news-item">No recent articles found.</li>';
                }
            }
        }

        function updateUI(payload) {
            if (!payload) return;
            document.getElementById('last-updated').textContent = 'Last sync: ' + payload.timestamp;

            // Update Stocks (Order: MU, SKHY, QQQ)
            populateStock('MU', payload.stocks.MU);
            populateStock('SKHY', payload.stocks.SKHY);
            populateStock('QQQ', payload.stocks.QQQ);

            // SK Hynix Korea underlying
            const skhy = payload.stocks.SKHY;
            if (skhy && skhy.korea_ref && skhy.korea_ref.price) {
                const kr = skhy.korea_ref;
                const krSign = kr.change >= 0 ? '+' : '';
                document.getElementById('skhy-krx').textContent = `₩${formatNumber(kr.price)} (${krSign}${kr.change_pct.toFixed(1)}%)`;
            }

            // Compact Weather & Clement status
            const w = payload.weather;
            if (w) {
                document.getElementById('w-temp').textContent = `${Math.round(w.temperature)}°F`;
                document.getElementById('w-cond').textContent = `${w.icon} ${w.condition}`;
                document.getElementById('w-meta').textContent = `Winds: ${w.wind_speed} mph ${w.wind_direction} • Humidity: ${w.humidity}%`;

                if (w.clement) {
                    const pill = document.getElementById('clement-pill');
                    pill.className = 'clement-pill ' + (w.clement.is_severe ? 'clement-alert' : 'clement-calm');
                    document.getElementById('clement-status').textContent = w.clement.status;
                    document.getElementById('clement-desc').textContent = w.clement.description;
                }
            }
        }

        async function fetchClientWeather() {
            try {
                const url = 'https://api.open-meteo.com/v1/forecast?latitude=21.3069&longitude=-157.8583&current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m,wind_direction_10m&daily=weather_code,precipitation_sum,wind_gusts_10m_max&temperature_unit=fahrenheit&wind_speed_unit=mph&precipitation_unit=inch&timezone=Pacific%2FHonolulu';
                const r = await fetch(url);
                if (!r.ok) return;
                const d = await r.json();
                const curr = d.current;
                if (!curr) return;
                
                const wmoMap = {
                    0: ["Clear / Sunny", "☀️"], 1: ["Mainly Clear", "🌤️"], 2: ["Partly Cloudy", "⛅"],
                    3: ["Overcast", "☁️"], 45: ["Foggy", "🌫️"], 51: ["Light Drizzle", "🌦️"],
                    61: ["Slight Rain", "🌦️"], 63: ["Rain", "🌧️"], 80: ["Passing Showers", "🌦️"],
                    95: ["Thunderstorm", "⚡"]
                };
                const cond = wmoMap[curr.weather_code] || ["Fair", "🌤️"];
                const deg = curr.wind_direction_10m || 0;
                const dir = (deg>=22.5 && deg<67.5)?"NE":(deg>=67.5 && deg<112.5)?"E":(deg>=112.5 && deg<157.5)?"SE":(deg>=157.5 && deg<202.5)?"S":(deg>=202.5 && deg<247.5)?"SW":(deg>=247.5 && deg<292.5)?"W":(deg>=292.5 && deg<337.5)?"NW":"N";

                document.getElementById('w-temp').textContent = `${Math.round(curr.temperature_2m)}°F`;
                document.getElementById('w-cond').textContent = `${cond[1]} ${cond[0]}`;
                document.getElementById('w-meta').textContent = `Winds: ${Math.round(curr.wind_speed_10m)} mph ${dir} • Humidity: ${curr.relative_humidity_2m}%`;

                const daily = d.daily || {};
                const codes = daily.weather_code || [];
                const gusts = daily.wind_gusts_10m_max || [];
                let isSev = false;
                for (let c of codes) { if ([95,96,99,65,82].includes(c)) isSev = true; }
                for (let g of gusts) { if (g >= 45) isSev = true; }

                const pill = document.getElementById('clement-pill');
                if (pill) {
                    pill.className = 'clement-pill ' + (isSev ? 'clement-alert' : 'clement-calm');
                    document.getElementById('clement-status').textContent = isSev ? 'Weather Notice Ahead' : 'Clement Weather: Calm';
                    document.getElementById('clement-desc').textContent = isSev ? 'Notice: Storm systems or gale winds in forecast.' : 'No severe weather ahead. Pleasant trade winds & clear skies across Oahu for the week.';
                }
            } catch(e) { console.warn('Weather fallback error:', e); }
        }

        async function fetchData() {
            const btn = document.querySelector('.refresh-btn');
            btn.style.opacity = '0.7';
            btn.textContent = 'Updating...';
            try {
                const res = await fetch('/api/data');
                if (res.ok) {
                    const data = await res.json();
                    updateUI(data);
                    return;
                }
                await fetchClientWeather();
            } catch (err) {
                await fetchClientWeather();
            } finally {
                btn.style.opacity = '1';
                btn.innerHTML = `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"/></svg> Refresh`;
            }
        }

        // Initial fetch
        fetchData();
        // Auto-refresh every 5 minutes
        setInterval(fetchData, 300000);
    </script>
</body>
</html>
"""


class DashboardHandler(http.server.BaseHTTPRequestHandler):
    cached_payload = None
    last_fetched_time = 0

    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode("utf-8"))

        elif self.path == "/api/data":
            now = time.time()
            if not DashboardHandler.cached_payload or (now - DashboardHandler.last_fetched_time > 60):
                DashboardHandler.cached_payload = get_dashboard_payload()
                DashboardHandler.last_fetched_time = now

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(DashboardHandler.cached_payload).encode("utf-8"))

        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not Found")

    def log_message(self, format, *args):
        return


def run_cli_mode():
    """Print clean CLI summary."""
    print("\nFetching latest market data...\n" + "="*65)
    data = get_dashboard_payload()

    # Weather
    w = data.get("weather", {})
    c = w.get("clement", {})
    print(f"\n🌴 HONOLULU STATUS ({data.get('timestamp')})")
    print(f"Current: {w.get('temperature')}°F {w.get('icon')} {w.get('condition')} | Winds: {w.get('wind_speed')} mph {w.get('wind_direction')} | Humidity: {w.get('humidity')}%")
    print(f"Forecast Status: [{c.get('status')}] - {c.get('description')}")

    # Stocks
    stocks = data.get("stocks", {})
    print("\n" + "="*65)
    print("📈 MARKET & TECH TICKERS (MU, SKHY, QQQ)")
    print("="*65)

    for ticker in ["MU", "SKHY", "QQQ"]:
        info = stocks.get(ticker, {})
        s = info.get("data")
        driver = info.get("driver", {})
        if s:
            sign = "+" if s["change"] >= 0 else ""
            print(f"\n▶ {info['name']} ({ticker}) - {info['exchange']}")
            print(f"  Price: ${s['price']:.2f} USD  |  Change: {sign}${s['change']:.2f} ({sign}{s['change_pct']:.2f}%)")
            print(f"  Day Range: ${s['low']:.2f} - ${s['high']:.2f}  |  Prev Close: ${s['prev_close']:.2f}")
            if "korea_ref" in info and info["korea_ref"]:
                kr = info["korea_ref"]
                kr_sign = "+" if kr["change"] >= 0 else ""
                print(f"  Korean Primary (000660.KS): ₩{kr['price']:,.0f} ({kr_sign}{kr['change_pct']:.2f}%)")
            print(f"  Movement Driver:")
            print(f"  {driver.get('summary', 'N/A')}")
            print(f"  Recent Headlines:")
            for n in info.get("news", [])[:3]:
                print(f"   • {n['title']} ({n['publisher']})")
        else:
            print(f"\n▶ {info['name']} ({ticker}): Failed to retrieve quote.")
    print("\n" + "="*65 + "\n")


def generate_static_html():
    """Build a standalone static HTML file populated with initial data."""
    print("Generating updated standalone static index.html...")
    payload = get_dashboard_payload()
    injected_html = HTML_TEMPLATE.replace(
        "// Initial fetch\n        fetchData();",
        f"// Initial baked-in data\n        const initialData = {json.dumps(payload)};\n        updateUI(initialData);\n        // Background refresh if server is up\n        fetchData();"
    )
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(injected_html)
    print(f"Saved updated dashboard to: {output_path}")
    return output_path


def main():
    if "--cli" in sys.argv:
        run_cli_mode()
        return

    if "--export" in sys.argv:
        path = generate_static_html()
        webbrowser.open(f"file://{path}")
        return

    static_file = generate_static_html()
    
    server_address = ("", PORT)
    try:
        httpd = socketserver.TCPServer(server_address, DashboardHandler)
    except OSError:
        httpd = socketserver.TCPServer(("", 8081), DashboardHandler)
    
    actual_port = httpd.server_address[1]
    url = f"http://localhost:{actual_port}"
    print(f"\n[+] Local Server running at {url}")
    print("[+] Press Ctrl+C in terminal to stop.")
    
    threading.Thread(target=lambda: (time.sleep(0.8), webbrowser.open(url)), daemon=True).start()
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[!] Shutting down server...")
        httpd.server_close()


if __name__ == "__main__":
    main()
