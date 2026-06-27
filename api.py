"""FastAPI 查询接口"""
from fastapi import FastAPI, Query, HTTPException
from storage import get_db, query_articles

app = FastAPI(title="News Fetcher", version="1.0.0")


@app.get("/api/articles")
async def list_articles(
    after_id: int | None = Query(None, description="增量拉取: 只返回 id > after_id 的文章"),
    source: str | None = Query(None, description="按来源过滤"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
):
    articles, total = await query_articles(
        after_id=after_id,
        source=source,
        page=page,
        page_size=page_size,
    )

    return {
        "data": articles,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": max(1, (total + page_size - 1) // page_size),
        },
    }


@app.get("/api/articles/{article_id}")
async def get_article(article_id: int):
    db = await get_db()
    cursor = await db.execute("SELECT * FROM articles WHERE id = ?", (article_id,))
    row = await cursor.fetchone()
    await db.close()

    if row is None:
        raise HTTPException(status_code=404, detail="Article not found")

    return {"data": dict(row)}
