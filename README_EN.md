# Business District Finder

[中文](README.md)

A business district finder powered by Amap (Gaode Maps) API — discovers areas where stores of multiple brands are co-located within a specified distance threshold.

## Features

- 🔍 Search brand stores via Amap POI REST API with automatic pagination and deduplication
- 📏 Precise distance calculation using the Haversine formula
- 🎯 Optimized clustering with spatial grid index and candidate pruning, dramatically reducing combinations
- ⭐ "Required brands" feature — ensures specified brands are always included in partial-match results
- 🗺️ Interactive map visualization with Amap JS API 2.0 (markers, polylines, info windows)
- 🌐 Web UI with SSE real-time progress streaming, mobile-responsive design
- 💻 CLI tool supporting JSON / HTML / log output formats
- 🖥️ uTools desktop plugin — pure frontend JavaScript implementation

## Quick Start

### 1. Install Dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env, at minimum set AMAP_API_KEY
```

You need API keys from [Amap Open Platform](https://console.amap.com/):

| Variable | Key Type | Purpose |
|----------|----------|---------|
| `AMAP_API_KEY` | Web Service | POI search (required) |
| `AMAP_JS_KEY` | Web (JS API) | Map display |
| `AMAP_SECURITY_CODE` | Security Code | Required for JS API 2.0 |

### 3. Run

**CLI mode:**

```bash
python main.py --city "深圳" --brands "优衣库,海底捞,星巴克" --threshold 200 --output json,html

# With required brands
python main.py --city "深圳" --brands "优衣库,海底捞,喜茶" --required-brands "海底捞"
```

**Web server mode:**

```bash
# Development
python app.py

# Production
pip install gunicorn
./start_production.sh
```

Visit http://localhost:5002 (default credentials: admin / admin123)

## CLI Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `--city` | City name (required) | - |
| `--brands` | Brand list, comma-separated (required) | - |
| `--threshold` | Distance threshold in meters (float) | 200 |
| `--required-brands` | Required brands, comma-separated | - |
| `--output` | Output formats: json, html, log | json,log |
| `--json-file` | JSON output filename | auto-generated |
| `--html-file` | HTML output filename | map.html |

## Environment Variables

```env
# Amap API Keys
AMAP_API_KEY=your_web_service_key       # Web Service Key (required)
AMAP_JS_KEY=your_js_api_key             # JS API Key
AMAP_SECURITY_CODE=your_security_code   # JS API Security Code

# Web Server
WEB_USERNAME=admin                       # Login username
WEB_PASSWORD=admin123                    # Login password
SECRET_KEY=your-secret-key               # Flask session secret
PORT=5002                                # Server port

# Algorithm Parameters
DEFAULT_DISTANCE_THRESHOLD=200           # Default distance threshold (meters)
DEDUPLICATION_DISTANCE=200               # Store deduplication distance (meters)

# Runtime
FLASK_DEBUG=False                        # Flask debug mode
WORKERS=4                               # gunicorn worker count
```

## Project Structure

```
where_will_we_go/
├── main.py                        # CLI entry point
├── app.py                         # Flask web application
├── config.py                      # Configuration loader
├── amap_api.py                    # Amap API wrapper (search, dedup, rate-limit retry)
├── cluster_finder.py              # Clustering entry (delegates to optimized/brute-force)
├── cluster_finder_optimized.py    # Optimized algorithm (spatial index + candidate pruning)
├── distance.py                    # Haversine distance calculation
├── output.py                      # Output module (JSON / log / HTML map)
├── log_capture.py                 # Log capture (stdout → SSE callback)
├── templates/                     # Web templates
│   ├── login.html                 # Login page
│   ├── search.html                # Search page (brand tags, progress bar)
│   ├── result.html                # Result page
│   └── map_view.html              # Map page
├── utools_plugin/                 # uTools desktop plugin (pure JS)
├── gunicorn.conf.py               # gunicorn production config
├── start_production.sh            # Production startup script
├── cluster-finder.service.example # systemd service template
├── requirements.txt               # Python dependencies
└── SDD-docs/                      # SDD specification documents
```

## Core Architecture

```
main.py (CLI)  ──┐
                  ├──▶ amap_api.py ──▶ cluster_finder.py ──▶ output.py
app.py  (Flask) ──┘        │                │
                       config.py        distance.py
```

1. **amap_api.py** — Amap REST API wrapper with auto-pagination, rate-limit retry, store deduplication
2. **cluster_finder.py** — Delegates to optimized algorithm (SpatialGrid spatial index), falls back to brute-force
3. **output.py** — Generates JSON / log / self-contained HTML map

## How the Algorithm Works

1. **POI Search** — For each brand, search all stores in the target city via Amap API
2. **Spatial Index** — Build a grid-based spatial index (cell size = 2× threshold)
3. **Candidate Pruning** — For each store, find nearby stores of other brands within the threshold
4. **Combination Check** — Only test feasible store combinations using Haversine distance
5. **Partial Fallback** — If no full-brand match exists, enumerate subsets from largest to smallest (≥2 brands)
6. **Required Brand Filter** — In partial fallback, skip subsets that don't include all required brands
7. **Deduplication** — Each store appears in at most one cluster (greedy by brand count, then distance)

## Production Deployment

```bash
# gunicorn + systemd
sudo cp cluster-finder.service.example /etc/systemd/system/cluster-finder.service
# Edit paths and user in the config file
sudo systemctl enable cluster-finder
sudo systemctl start cluster-finder
```

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| Map shows no tiles | Missing JS API security code | Set `AMAP_JS_KEY` + `AMAP_SECURITY_CODE` |
| USERKEY_PLAT_NOMATCH | Wrong key type | Use Web (JS API) type key for `AMAP_JS_KEY` |
| No stores found | Inaccurate brand name / quota exceeded | Use official brand names |
| API rate limiting | Too many requests | Auto-retry built in; reduce brand count if persistent |

## Tech Stack

Python 3.7+ · Flask · Amap JS API 2.0 · gunicorn · Vanilla JavaScript

## License

MIT License
