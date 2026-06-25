"""摘抄 CRUD + 全文检索"""

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import PlainTextResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text, func, delete
from sqlalchemy.orm import selectinload
import json
import os
import uuid
from datetime import datetime

from database import get_db
from models import Excerpt, Tag, ExcerptTag
from schemas import ExcerptCreate, ExcerptUpdate, ExcerptOut, SearchResult
from pydantic import BaseModel, Field
from typing import List

router = APIRouter(prefix="/api/excerpts", tags=["excerpts"])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload", summary="上传图片")
async def upload_image(file: UploadFile = File(...)):
    ext = file.filename.rsplit(".", 1)[-1] if "." in (file.filename or "") else "png"
    filename = f"{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)
    return {"url": f"/static/{filename}", "filename": filename}


@router.post("", response_model=ExcerptOut, summary="创建摘抄")
async def create_excerpt(data: ExcerptCreate, db: AsyncSession = Depends(get_db)):
    excerpt = Excerpt(
        book_id=data.book_id,
        content=data.content or "",
        insights=data.insights or "",
        links=data.links,
        images=data.images,
    )
    db.add(excerpt)
    await db.flush()

    if data.tag_ids:
        tags = (await db.execute(select(Tag).where(Tag.id.in_(data.tag_ids)))).scalars().all()
        for tag in tags:
            db.add(ExcerptTag(excerpt_id=excerpt.id, tag_id=tag.id))

    await db.commit()
    await db.refresh(excerpt)
    # re-fetch with relations
    result = await db.execute(
        select(Excerpt).options(selectinload(Excerpt.book), selectinload(Excerpt.tags))
        .where(Excerpt.id == excerpt.id)
    )
    return result.scalar().to_dict()


@router.get("", response_model=SearchResult, summary="搜索/列表摘抄")
async def list_excerpts(
    keyword: str = Query("", description="全文检索关键词(搜索原文+见解)"),
    tag_ids: str = Query("", description="标签ID，逗号分隔"),
    book_id: int = Query(None, description="筛选特定书籍"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    favorites: bool = Query(False, description="仅显示收藏"),
    db: AsyncSession = Depends(get_db),
):
    tag_id_list = [int(x) for x in tag_ids.split(",") if x.strip().isdigit()] if tag_ids else []
    conditions = []
    params = {}

    if favorites:
        conditions.append("e.is_favorite = 1")

    if book_id is not None:
        conditions.append("e.book_id = :book_id")
        params["book_id"] = book_id

    if tag_id_list:
        placeholders = ",".join([f":tid_{i}" for i in range(len(tag_id_list))])
        for i, tid in enumerate(tag_id_list):
            params[f"tid_{i}"] = tid
        conditions.append(
            f"e.id IN (SELECT et.excerpt_id FROM excerpt_tags et "
            f"WHERE et.tag_id IN ({placeholders}) "
            f"GROUP BY et.excerpt_id HAVING COUNT(DISTINCT et.tag_id) = :tag_count)"
        )
        params["tag_count"] = len(tag_id_list)

    if keyword.strip():
        kw = keyword.strip()
        # MySQL InnoDB FULLTEXT doesn't tokenize Chinese well without ngram parser.
        # Use LIKE fallback for CJK text; FULLTEXT for Latin text.
        has_cjk = any('一' <= c <= '鿿' for c in kw)
        if has_cjk:
            conditions.append("(e.content LIKE :kw_like OR e.insights LIKE :kw_like)")
            params["kw_like"] = f"%{kw}%"
        else:
            conditions.append("MATCH(e.content, e.insights) AGAINST(:kw IN BOOLEAN MODE)")
            params["kw"] = f"+{kw}"

    where_clause = " AND ".join(conditions) if conditions else "1=1"

    # Count
    count_sql = text(f"SELECT COUNT(*) FROM excerpts e WHERE {where_clause}")
    total = (await db.execute(count_sql, params)).scalar() or 0

    # Paginated IDs
    offset = (page - 1) * page_size
    query_sql = text(
        f"SELECT e.id FROM excerpts e WHERE {where_clause} "
        f"ORDER BY e.updated_at DESC LIMIT :limit OFFSET :offset"
    )
    all_params = {**params, "limit": page_size, "offset": offset}
    rows = (await db.execute(query_sql, all_params)).fetchall()
    excerpt_ids = [row[0] for row in rows]

    # Fetch full objects with relations
    excerpts = []
    if excerpt_ids:
        excerpt_objs = (
            (await db.execute(
                select(Excerpt)
                .options(selectinload(Excerpt.book), selectinload(Excerpt.tags))
                .where(Excerpt.id.in_(excerpt_ids))
                .order_by(Excerpt.updated_at.desc())
            ))
            .scalars().all()
        )
        # maintain ID order
        id_to_excerpt = {e.id: e for e in excerpt_objs}
        excerpts = [id_to_excerpt[eid] for eid in excerpt_ids if eid in id_to_excerpt]

    return SearchResult(
        total=total,
        page=page,
        page_size=page_size,
        items=[e.to_dict() for e in excerpts],
    )


@router.get("/export", summary="导出摘抄")
async def export_excerpts(
    fmt: str = Query("md", description="导出格式：md 或 json"),
    book_id: int = Query(None, description="筛选特定书籍"),
    tag_ids: str = Query("", description="标签ID，逗号分隔"),
    db: AsyncSession = Depends(get_db),
):
    tag_id_list = [int(x) for x in tag_ids.split(",") if x.strip().isdigit()] if tag_ids else []

    base = select(Excerpt).options(selectinload(Excerpt.book), selectinload(Excerpt.tags))

    if book_id is not None:
        base = base.where(Excerpt.book_id == book_id)

    if tag_id_list:
        sub = (
            select(ExcerptTag.excerpt_id)
            .where(ExcerptTag.tag_id.in_(tag_id_list))
            .group_by(ExcerptTag.excerpt_id)
            .having(func.count(func.distinct(ExcerptTag.tag_id)) == len(tag_id_list))
        ).subquery()
        base = base.where(Excerpt.id.in_(select(sub.c.excerpt_id)))

    result = await db.execute(base.order_by(Excerpt.updated_at.desc()))
    excerpts = result.scalars().all()

    if fmt == "json":
        return JSONResponse(content=[e.to_dict() for e in excerpts])

    # Markdown format: grouped by book
    groups = {}
    for e in excerpts:
        book_title = e.book.title if e.book else "未归类"
        groups.setdefault(book_title, []).append(e)

    lines = ["# 读书摘抄导出\n"]
    for book_title, exs in groups.items():
        lines.append(f"## {book_title}\n")
        for e in exs:
            if e.content:
                lines.append(f"> {e.content}\n")
            if e.insights:
                lines.append(f"**我的想法：** {e.insights}\n")
            tags_str = " ".join([f"`{t.name}`" for t in e.tags]) if e.tags else ""
            if tags_str:
                lines.append(f"标签：{tags_str}\n")
            if e.links:
                for link in e.links:
                    lines.append(f"- {link}")
                lines.append("")
            lines.append("---\n")

    return PlainTextResponse("\n".join(lines), media_type="text/markdown; charset=utf-8")


@router.get("/random", response_model=ExcerptOut, summary="随机获取一条摘抄")
async def random_excerpt(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Excerpt)
        .options(selectinload(Excerpt.book), selectinload(Excerpt.tags))
        .order_by(func.rand())
        .limit(1)
    )
    excerpt = result.scalar()
    if not excerpt:
        raise HTTPException(status_code=404, detail="暂无摘抄")
    return excerpt.to_dict()


@router.put("/{excerpt_id}/favorite", response_model=ExcerptOut, summary="切换收藏状态")
async def toggle_favorite(excerpt_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Excerpt)
        .options(selectinload(Excerpt.book), selectinload(Excerpt.tags))
        .where(Excerpt.id == excerpt_id)
    )
    excerpt = result.scalar()
    if not excerpt:
        raise HTTPException(status_code=404, detail="摘抄不存在")
    excerpt.is_favorite = not excerpt.is_favorite
    await db.commit()
    await db.refresh(excerpt)
    return excerpt.to_dict()


class BatchDeletePayload(BaseModel):
    ids: List[int] = Field(..., min_length=1)

class BatchTagPayload(BaseModel):
    ids: List[int] = Field(..., min_length=1)
    tag_ids: List[int] = Field(..., min_length=1)


@router.post("/batch-delete", summary="批量删除摘抄")
async def batch_delete_excerpts(payload: BatchDeletePayload, db: AsyncSession = Depends(get_db)):
    await db.execute(delete(Excerpt).where(Excerpt.id.in_(payload.ids)))
    await db.commit()
    return {"ok": True, "deleted": len(payload.ids)}


@router.post("/batch-tag", summary="批量为摘抄添加标签")
async def batch_tag_excerpts(payload: BatchTagPayload, db: AsyncSession = Depends(get_db)):
    existing_tags = (await db.execute(
        select(Tag.id).where(Tag.id.in_(payload.tag_ids))
    )).scalars().all()
    valid_tag_ids = list(existing_tags)
    if not valid_tag_ids:
        raise HTTPException(status_code=400, detail="无效的标签ID")

    added = 0
    for excerpt_id in payload.ids:
        for tag_id in valid_tag_ids:
            exists = (await db.execute(
                select(ExcerptTag).where(ExcerptTag.excerpt_id == excerpt_id, ExcerptTag.tag_id == tag_id)
            )).scalar()
            if not exists:
                db.add(ExcerptTag(excerpt_id=excerpt_id, tag_id=tag_id))
                added += 1

    await db.commit()
    return {"ok": True, "added": added}


@router.get("/{excerpt_id}", response_model=ExcerptOut, summary="获取摘抄详情")
async def get_excerpt(excerpt_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Excerpt)
        .options(selectinload(Excerpt.book), selectinload(Excerpt.tags))
        .where(Excerpt.id == excerpt_id)
    )
    excerpt = result.scalar()
    if not excerpt:
        raise HTTPException(status_code=404, detail="摘抄不存在")
    return excerpt.to_dict()


@router.put("/{excerpt_id}", response_model=ExcerptOut, summary="更新摘抄")
async def update_excerpt(excerpt_id: int, data: ExcerptUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Excerpt)
        .options(selectinload(Excerpt.book), selectinload(Excerpt.tags))
        .where(Excerpt.id == excerpt_id)
    )
    excerpt = result.scalar()
    if not excerpt:
        raise HTTPException(status_code=404, detail="摘抄不存在")

    if data.book_id is not None:
        excerpt.book_id = data.book_id
    if data.content is not None:
        excerpt.content = data.content
    if data.insights is not None:
        excerpt.insights = data.insights
    if data.links is not None:
        excerpt.links = data.links
    if data.images is not None:
        excerpt.images = data.images
    if data.is_favorite is not None:
        excerpt.is_favorite = data.is_favorite

    if data.tag_ids is not None:
        await db.execute(delete(ExcerptTag).where(ExcerptTag.excerpt_id == excerpt_id))
        if data.tag_ids:
            tags = (await db.execute(select(Tag).where(Tag.id.in_(data.tag_ids)))).scalars().all()
            for tag in tags:
                db.add(ExcerptTag(excerpt_id=excerpt.id, tag_id=tag.id))

    excerpt.updated_at = datetime.now()
    await db.commit()
    await db.refresh(excerpt)
    return excerpt.to_dict()


@router.delete("/{excerpt_id}", summary="删除摘抄")
async def delete_excerpt(excerpt_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Excerpt).where(Excerpt.id == excerpt_id))
    excerpt = result.scalar()
    if not excerpt:
        raise HTTPException(status_code=404, detail="摘抄不存在")
    await db.delete(excerpt)
    await db.commit()
    return {"ok": True}
