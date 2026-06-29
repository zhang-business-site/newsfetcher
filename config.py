"""
News Fetcher 配置
"""
import os

# 抓取间隔（分钟）
FETCH_INTERVAL_MINUTES = int(os.getenv("FETCH_INTERVAL_MINUTES", "30"))

# SQLite 数据库路径
DB_PATH = os.getenv("DB_PATH", os.path.join(os.path.dirname(__file__), "data", "articles.db"))

# API 配置
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))

# 新闻源配置
SOURCES = [
    {
        "name": "BBC Business",
        "enabled": True,
        "listing_url": "https://www.bbc.com/business",
        "article_path_pattern": r"(/news/articles/[a-z0-9]+)",
        "base_url": "https://www.bbc.com",
    },
]
