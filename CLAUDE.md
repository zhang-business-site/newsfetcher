# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

News Fetcher — periodically scrapes BBC Business articles, stores them in SQLite, and serves them via a FastAPI query API.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Start API server + scheduled scraping
python3 main.py

# Scrape once (no API server)
python3 main.py --fetch-only
```

## Architecture

```
main.py        Entry point: CLI args → init DB → fetch once → [API server + scheduler loop]
config.py      Configuration via env vars: FETCH_INTERVAL_MINUTES, API_HOST, API_PORT, DB_PATH
scraper.py     BBC Business scraper (sync, runs in executor thread) using scrapling, trafilatura, readability-lxml
storage.py     SQLite storage layer: aiosqlite (async, for API) with init_db, query_articles, insert_article
api.py         FastAPI app: GET /api/articles (paginated, filterable), GET /api/articles/{id}
```

## Key Design Points

- **Dual DB access**: `storage.py` uses `aiosqlite` for async API queries. `scraper.py` uses standard `sqlite3` directly because it runs in a thread via `loop.run_in_executor()`. Both share the same `articles.db` file.
- **Content extraction**: `trafilatura` is the primary extractor (outputs clean HTML). `readability-lxml` is the fallback when trafilatura produces <200 chars.
- **Deduplication**: Articles are skipped by URL before fetching detail pages — no re-scraping of known URLs.
- **Incremental API**: `GET /api/articles?after_id=N` returns articles with `id > N` in ascending order, designed for client-side sync.
- **Source config**: News sources are defined as dicts in `config.py`'s `SOURCES` list, though only BBC Business is currently implemented. Each source has a `listing_url`, regex `article_path_pattern`, and `base_url`.

## Docker

```bash
# 构建并启动（API on :8000, DB 持久化到宿主机）
docker compose up -d

# 直接拉取 GitHub 镜像（跳过本地构建）
docker compose pull && docker compose up -d

# 指定仓库
GH_REPO=your-org/newsfetcher docker compose pull && docker compose up -d

# 查看日志
docker compose logs -f

# 停止
docker compose down
```

推送 main 分支后，[`.github/workflows/docker-build.yml`](.github/workflows/docker-build.yml) 自动构建镜像并推送到 `ghcr.io`，生成 `latest`、`main` 和 `sha-xxxx` 三个 tag。

## Dependencies

`scrapling` drives the headless browser fetch; `curl_cffi`, `patchright`, `browserforge`, `pyOpenSSL` are its transitive dependencies for stealth/TLS fingerprinting.
