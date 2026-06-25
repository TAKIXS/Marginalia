"""书籍管理"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import List

from database import get_db
from models import Book, Excerpt
from schemas import BookCreate, BookOut, BookUpdate, BookGroup

router = APIRouter(prefix="/api/books", tags=["books"])


@router.get("", response_model=List[BookOut], summary="获取所有书籍")
async def list_books(db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(
        select(
            Book.id, Book.title, Book.author, Book.cover, Book.created_at,
            func.count(Excerpt.id).label("excerpt_count")
        )
        .outerjoin(Excerpt, Excerpt.book_id == Book.id)
        .group_by(Book.id)
        .order_by(Book.id.desc())
    )).all()

    return [
        {
            "id": r.id,
            "title": r.title,
            "author": r.author,
            "cover": r.cover,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "excerpt_count": r.excerpt_count,
        }
        for r in rows
    ]


@router.post("", response_model=BookOut, summary="创建书籍")
async def create_book(data: BookCreate, db: AsyncSession = Depends(get_db)):
    existing = (await db.execute(
        select(Book).where(Book.title == data.title, Book.author == data.author)
    )).scalar()
    if existing:
        raise HTTPException(status_code=400, detail="该书籍已存在")
    book = Book(title=data.title, author=data.author, cover=data.cover)
    db.add(book)
    await db.commit()
    await db.refresh(book)
    return {**book.to_dict(), "excerpt_count": 0}


@router.get("/groups", response_model=List[BookGroup], summary="按书籍分组获取所有摘抄")
async def get_book_groups(
    book_id: int = Query(None, description="筛选特定书籍"),
    db: AsyncSession = Depends(get_db),
):
    """主页接口：返回按书籍分组的摘抄列表，支持折叠展示"""
    book_query = select(Book)
    if book_id:
        book_query = book_query.where(Book.id == book_id)
    book_query = book_query.order_by(Book.id.desc())

    books = (await db.execute(
        book_query.options(selectinload(Book.excerpts).selectinload(Excerpt.tags))
    )).scalars().all()

    result = []
    for book in books:
        excerpts = sorted(book.excerpts, key=lambda e: e.updated_at or e.created_at, reverse=True)
        result.append(BookGroup(
            book=BookOut(
                id=book.id,
                title=book.title,
                author=book.author,
                cover=book.cover,
                created_at=book.created_at.isoformat() if book.created_at else None,
                excerpt_count=len(excerpts),
            ),
            excerpts=[e.to_dict() for e in excerpts],
        ))
    return result


@router.get("/{book_id}", response_model=BookOut, summary="获取单本书籍详情")
async def get_book(book_id: int, db: AsyncSession = Depends(get_db)):
    row = (await db.execute(
        select(
            Book.id, Book.title, Book.author, Book.cover, Book.created_at,
            func.count(Excerpt.id).label("excerpt_count")
        )
        .outerjoin(Excerpt, Excerpt.book_id == Book.id)
        .where(Book.id == book_id)
        .group_by(Book.id)
    )).first()
    if not row:
        raise HTTPException(status_code=404, detail="书籍不存在")
    return {
        "id": row.id,
        "title": row.title,
        "author": row.author,
        "cover": row.cover,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "excerpt_count": row.excerpt_count,
    }


@router.put("/{book_id}", response_model=BookOut, summary="更新书籍信息")
async def update_book(book_id: int, data: BookUpdate, db: AsyncSession = Depends(get_db)):
    book = (await db.execute(select(Book).where(Book.id == book_id))).scalar()
    if not book:
        raise HTTPException(status_code=404, detail="书籍不存在")
    if data.title is not None:
        book.title = data.title
    if data.author is not None:
        book.author = data.author
    if data.cover is not None:
        book.cover = data.cover
    await db.commit()
    await db.refresh(book)
    # get excerpt count
    count = (await db.execute(
        select(func.count(Excerpt.id)).where(Excerpt.book_id == book.id)
    )).scalar() or 0
    return {**book.to_dict(), "excerpt_count": count}


@router.delete("/{book_id}", summary="删除书籍及其所有摘抄")
async def delete_book(book_id: int, db: AsyncSession = Depends(get_db)):
    book = (await db.execute(select(Book).where(Book.id == book_id))).scalar()
    if not book:
        raise HTTPException(status_code=404, detail="书籍不存在")
    await db.delete(book)
    await db.commit()
    return {"ok": True}
