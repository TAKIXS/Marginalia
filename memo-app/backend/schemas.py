"""Pydantic 请求/响应模型"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ── Tag ──────────────────────────────────────────────

class TagOut(BaseModel):
    id: int
    name: str
    color: str
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class TagCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    color: str = Field(default="#409EFF", max_length=7)


class TagUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    color: Optional[str] = Field(None, max_length=7)


# ── Book ─────────────────────────────────────────────

class BookCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    author: str = ""
    cover: str = ""


class BookOut(BaseModel):
    id: int
    title: str
    author: str
    cover: str
    created_at: Optional[datetime] = None
    excerpt_count: int = 0

    model_config = {"from_attributes": True}


class BookUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    author: Optional[str] = None
    cover: Optional[str] = None


# ── Excerpt ──────────────────────────────────────────

class ExcerptCreate(BaseModel):
    book_id: int
    content: Optional[str] = ""
    insights: Optional[str] = ""
    links: List[str] = []
    images: List[str] = []
    tag_ids: List[int] = []


class ExcerptUpdate(BaseModel):
    book_id: Optional[int] = None
    content: Optional[str] = None
    insights: Optional[str] = None
    links: Optional[List[str]] = None
    images: Optional[List[str]] = None
    tag_ids: Optional[List[int]] = None
    is_favorite: Optional[bool] = None


class ExcerptOut(BaseModel):
    id: int
    book_id: int
    content: Optional[str]
    insights: Optional[str]
    links: List[str]
    images: List[str]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    book: Optional[BookOut] = None
    tags: List[TagOut] = []
    is_favorite: bool = False

    model_config = {"from_attributes": True}


# ── Grouped by book ──────────────────────────────────

class BookGroup(BaseModel):
    book: BookOut
    excerpts: List[ExcerptOut]


# ── AI ────────────────────────────────────────────────

class GenerateInsightsRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000)
    book_id: Optional[int] = None


# ── Batch Operations ──────────────────────────────────

class BatchDeletePayload(BaseModel):
    ids: List[int] = Field(..., min_length=1)

class BatchTagPayload(BaseModel):
    ids: List[int] = Field(..., min_length=1)
    tag_ids: List[int] = Field(..., min_length=1)


# ── Search ───────────────────────────────────────────

class SearchResult(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[ExcerptOut]
