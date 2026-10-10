# Market & Tech Portfolio Monitor

A lightweight, zero-dependency market and weather monitor built with Python and modern HTML5.

## Features
- **Stock Tracking & Catalysts:**
  - **Micron Technology (`MU`)**: Memory leader, HBM3E yields, and AI datacenter demand.
  - **SK Hynix Inc. (`SKHY`)**: Primary NVIDIA HBM supplier and global tech fund movements.
  - **Invesco QQQ Trust (`QQQ`)**: Nasdaq-100 benchmark tracking mega-cap tech momentum and interest rates.
- **Honolulu, Hawaii Status & Clement Weather:**
  - Current temperature, trade winds, humidity, and condition.
  - **Clement Weather Check**: Automated 7-day severe weather evaluator (storms, tropical gusts, heavy rain).
- **Two Ways to Run:**
  1. **Standalone (`index.html`)**: Open directly in any web browser or deploy directly to **GitHub Pages**.
  2. **Live Auto-Refreshing Server (`app.py`)**: Local web server that fetches real-time quotes without CORS issues.

## Usage

### 1. Run Live Auto-Refreshing Dashboard
```bash
python app.py
```
Starts a local web server at `http://localhost:8080`, opens your browser, and auto-refreshes data every 5 minutes.

### 2. Quick Command Line Glance (CLI Mode)
```bash
python app.py --cli
```

### 3. Update the Offline Static HTML Dashboard
```bash
python app.py --export
```
Updates `index.html` with the latest quotes and catalysts.
