# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

商圈查找工具 — finds business districts ("商圈") where multiple brand stores are co-located within a distance threshold. Uses Amap (高德地图) REST API for POI search and JS API 2.0 for map visualization.

## Commands

```bash
# Install dependencies (Python 3.7+, venv at .venv)
pip install -r requirements.txt

# Run CLI
python main.py --city "深圳" --brands "优衣库,海底捞" --threshold 200 --output json,html

# Run web server (dev)
python app.py                # Flask dev server on port 5002

# Run web server (production)
./start_production.sh        # gunicorn, requires: pip install gunicorn
```

No test suite exists in this project.

## Architecture

Two entry points share the same core pipeline:

```
main.py (CLI)  ──┐
                  ├──> amap_api.py ──> cluster_finder.py ──> output.py
app.py  (Flask) ──┘         │                  │
                        config.py          distance.py
```

**Core pipeline:**
1. `amap_api.py` — Amap REST API wrapper. `search_poi()` paginates POI results with rate-limit retry and deduplication (stores within `DEDUPLICATION_DISTANCE` meters are merged). `search_brands_with_progress()` adds progress callbacks for the web SSE stream.
2. `cluster_finder.py` — Delegates to `cluster_finder_optimized.py` (spatial grid index + candidate pruning) when available, falls back to brute-force Cartesian product. Finds store combinations where every pair is within the threshold, then deduplicates clusters so each store appears in at most one (greedy by brand count).
3. `output.py` — Generates JSON, log, or standalone HTML map (inline Amap JS API 2.0 with markers, polylines, and an info panel).

**Web-specific:**
- `app.py` — Flask app with session-based auth (`login_required` decorator). Key endpoint is `POST /api/search/stream` which uses SSE (`text/event-stream`) to push progress/log/result messages. Search and clustering run in background threads; `LogCapture` (in `log_capture.py`) redirects `print()` output from those threads into the SSE queue.
- Templates: `templates/{login,search,result,map_view}.html`

**Optimized algorithm** (`cluster_finder_optimized.py`):
- `SpatialGrid` — grid-based spatial index (cell size = 2× threshold). Converts lat/lon to grid cells, checks 3×3 neighborhood for nearby stores.
- Builds per-store candidate sets grouped by brand, then only iterates over feasible combinations instead of full Cartesian product.
- Falls back to partial brand combinations (≥2 brands) if no full match exists.

## Configuration

All config via `.env` (loaded by `config.py` using `python-dotenv`):
- `AMAP_API_KEY` (Web服务 key, required for POI search)
- `AMAP_JS_KEY` + `AMAP_SECURITY_CODE` (JS API 2.0 key + security code, required for map display)
- `WEB_USERNAME`/`WEB_PASSWORD` — web login credentials (default: admin/admin123)
- `DEFAULT_DISTANCE_THRESHOLD`, `DEDUPLICATION_DISTANCE` — algorithm parameters in meters

## Key Conventions

- All coordinates use `lat`/`lon` keys (Amap returns `location` as "lon,lat" string — note the order swap in `amap_api.py`).
- Cluster data structure: `{"brands": {brand_name: store_dict}, "stores": [store_dict], "max_distance": float, "brand_count": int}`
- Store data structure: `{"name", "address", "lat", "lon", "poi_id", "type"}`
- The HTML map output is a self-contained HTML string (no external templates) built via string concatenation in `output.py`.
- `utools_plugin/` is a standalone uTools desktop plugin (JS-based), separate from the Python codebase.
