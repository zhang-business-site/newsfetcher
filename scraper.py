"""新闻抓取器 - BBC Business + 可扩展源"""
import re
import time
from scrapling import Fetcher, StealthyFetcher
import trafilatura
from readability import Document
import sqlite3

import config
import config as _cfg


def _db_path() -> str:
    return _cfg.DB_PATH


def _extract_summary(html_content: str, body_html: str | None = None) -> str:
    """
    从页面 HTML 提取新闻简介。
    优先级：meta[description] > og:description > 正文第一段。
    """
    from lxml import html as lxhtml  # noqa: F811

    # 1) meta description / og:description
    try:
        doc = lxhtml.fromstring(html_content)
        for xp in [
            '//meta[@name="description"]/@content',
            '//meta[@property="og:description"]/@content',
        ]:
            val = doc.xpath(xp)
            if val and val[0].strip():
                return val[0].strip()
    except Exception:
        pass

    # 2) 从提取后的正文取第一段纯文本
    if body_html:
        try:
            doc = lxhtml.fromstring(body_html)
            for tag in doc.xpath("//p"):
                text = tag.text_content().strip()
                if len(text) > 30:
                    return text[:500]
        except Exception:
            pass

    return ""


def fetch_bbc_articles() -> int:
    """
    抓取 BBC Business 最新文章（同步，运行在线程中）。
    返回新插入的文章数量。
    """
    cfg = config.SOURCES[0]
    print(f"📡 [BBC] 获取列表页 {cfg['listing_url']} ...")

    listing = StealthyFetcher.fetch(
        cfg["listing_url"],
        headless=True,
        timeout=60000,
        wait=8000,
    )

    # 从原始 HTML 提取文章路径
    paths = list(set(re.findall(cfg["article_path_pattern"], listing.html_content)))
    urls = [cfg["base_url"] + p for p in paths]
    print(f"   发现 {len(urls)} 个文章链接")

    # 线程中不能用 aiosqlite，用标准 sqlite3
    db = sqlite3.connect(_db_path())
    new_count = 0

    for i, url in enumerate(urls):
        # 跳过已存在的文章
        cursor = db.execute("SELECT 1 FROM articles WHERE url = ?", (url,))
        if cursor.fetchone():
            print(f"   [{i+1}/{len(urls)}] ⏭ 已存在")
            continue

        try:
            detail = Fetcher.get(url, impersonate="chrome131", stealthy_headers=True, timeout=20)
            if detail.status != 200 or len(detail.html_content) < 2000:
                print(f"   [{i+1}/{len(urls)}] ✗ HTTP {detail.status}")
                continue

            html_body = trafilatura.extract(
                detail.html_content,
                output_format="html",
                include_links=True,
                include_images=True,
                include_tables=True,
                url=url,
                favor_precision=True,
            )

            if not html_body or len(html_body) < 200:
                doc = Document(detail.html_content)
                html_body = doc.summary(html_partial=True)

            if html_body and len(html_body) > 200:
                title_match = re.search(r"<h1[^>]*>(.+?)</h1>", html_body)
                title = title_match.group(1) if title_match else url.split("/")[-1]

                summary = _extract_summary(detail.html_content, html_body)

                db.execute(
                    "INSERT INTO articles (url, title, source, summary, body_html) VALUES (?, ?, ?, ?, ?)",
                    (url, title, cfg["name"], summary, html_body),
                )
                db.commit()
                new_count += 1
                print(f"   [{i+1}/{len(urls)}] ✓ {title[:60]} | HTML:{len(html_body)}字")
            else:
                print(f"   [{i+1}/{len(urls)}] ✗ 无内容提取")

            time.sleep(0.5)
        except Exception as e:
            print(f"   [{i+1}/{len(urls)}] ✗ {str(e)[:80]}")

    db.close()
    return new_count
