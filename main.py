#!/usr/bin/env python3
"""News Fetcher — 定时抓取 BBC Business 新闻，存入 SQLite，提供查询 API

用法:
    python3 main.py              # 启动 API 服务 + 定时抓取
    python3 main.py --fetch-only # 只抓取一次
"""

import asyncio
import argparse
from datetime import datetime

import config
from storage import init_db
from scraper import fetch_bbc_articles


async def fetch_all_sources():
    print(f"\n{'='*50}")
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 开始抓取...")
    loop = asyncio.get_running_loop()
    new_count = await loop.run_in_executor(None, fetch_bbc_articles)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 本次新增 {new_count} 篇")
    print(f"{'='*50}\n")
    return new_count


async def run_scheduler():
    """异步定时调度"""
    while True:
        await asyncio.sleep(config.FETCH_INTERVAL_MINUTES * 60)
        await fetch_all_sources()


async def main():
    parser = argparse.ArgumentParser(description="News Fetcher")
    parser.add_argument("--fetch-only", action="store_true", help="只抓取一次，不启动 API")
    args = parser.parse_args()

    await init_db()
    print("📦 SQLite 数据库已就绪")

    if args.fetch_only:
        await fetch_all_sources()
        print("Fetch-only 模式，退出")
        return

    # 启动 API + 定时调度
    import uvicorn
    from api import app

    # 首次抓取放入后台，不阻塞 API 启动
    asyncio.create_task(fetch_all_sources())

    # 在后台启动定时抓取
    asyncio.create_task(run_scheduler())
    print(f"⏱ 定时任务已启动（每 {config.FETCH_INTERVAL_MINUTES} 分钟）\n")

    # 阻塞运行 API
    uvicorn_config = uvicorn.Config(
        app,
        host=config.API_HOST,
        port=config.API_PORT,
        log_level="info",
    )
    server = uvicorn.Server(uvicorn_config)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())
