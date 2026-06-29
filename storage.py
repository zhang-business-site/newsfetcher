"""SQLite 存储层"""
import aiosqlite
import config


async def get_db() -> aiosqlite.Connection:
    db = await aiosqlite.connect(config.DB_PATH)
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA journal_mode=WAL")
    await db.execute("PRAGMA foreign_keys=ON")
    return db


async def init_db():
    db = await get_db()
    await db.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            url        TEXT UNIQUE NOT NULL,
            title      TEXT NOT NULL,
            source     TEXT NOT NULL DEFAULT 'BBC Business',
            summary    TEXT NOT NULL DEFAULT '',
            body_html  TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)
    # 兼容旧表：缺失列自动添加
    for col, col_def in [
        ("summary", "TEXT NOT NULL DEFAULT ''"),
        ("published_at", "TEXT NOT NULL DEFAULT ''"),
        ("author", "TEXT NOT NULL DEFAULT ''"),
        ("section", "TEXT NOT NULL DEFAULT ''"),
        ("image_url", "TEXT NOT NULL DEFAULT ''"),
    ]:
        try:
            await db.execute(f"ALTER TABLE articles ADD COLUMN {col} {col_def}")
        except Exception:
            pass  # 列已存在
    await db.execute("""
        CREATE INDEX IF NOT EXISTS idx_articles_created_at
        ON articles(created_at DESC)
    """)
    await db.execute("""
        CREATE INDEX IF NOT EXISTS idx_articles_source
        ON articles(source)
    """)
    await db.commit()
    await db.close()


async def insert_article(
    url: str, title: str, source: str, summary: str, body_html: str,
    published_at: str = "", author: str = "", section: str = "", image_url: str = "",
) -> bool:
    """插入文章，如果 URL 已存在则忽略。返回 True 表示新插入。"""
    db = await get_db()
    try:
        await db.execute(
            "INSERT INTO articles (url, title, source, summary, body_html, published_at, author, section, image_url) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (url, title, source, summary, body_html, published_at, author, section, image_url),
        )
        await db.commit()
        return True
    except aiosqlite.IntegrityError:
        return False
    finally:
        await db.close()


async def url_exists(url: str) -> bool:
    db = await get_db()
    cursor = await db.execute("SELECT 1 FROM articles WHERE url = ?", (url,))
    row = await cursor.fetchone()
    await db.close()
    return row is not None


async def query_articles(
    after_id: int | None = None,
    source: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[dict], int]:
    """
    查询文章列表。
    after_id 有值 → 增量模式，按 id ASC
    after_id 无值 → 常规模式，按 created_at DESC
    返回 (articles, total_count)
    """
    db = await get_db()

    conditions = []
    params: list = []
    order_by = "created_at DESC"

    if after_id is not None:
        conditions.append("id > ?")
        params.append(after_id)
        order_by = "id ASC"

    if source:
        conditions.append("source = ?")
        params.append(source)

    where = ""
    if conditions:
        where = "WHERE " + " AND ".join(conditions)

    # 总数
    count_sql = f"SELECT COUNT(*) FROM articles {where}"
    cursor = await db.execute(count_sql, params)
    total = (await cursor.fetchone())[0]

    # 分页
    offset = (page - 1) * page_size
    query_sql = f"SELECT * FROM articles {where} ORDER BY {order_by} LIMIT ? OFFSET ?"
    cursor = await db.execute(query_sql, params + [page_size, offset])
    rows = await cursor.fetchall()

    await db.close()

    articles = [dict(row) for row in rows]
    return articles, total
