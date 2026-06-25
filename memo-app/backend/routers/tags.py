"""标签管理"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from database import get_db
from models import Tag
from schemas import TagCreate, TagUpdate, TagOut

router = APIRouter(prefix="/api/tags", tags=["tags"])


@router.get("", response_model=List[TagOut], summary="获取所有标签")
async def list_tags(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Tag).order_by(Tag.id))
    tags = result.scalars().all()
    return [t.to_dict() for t in tags]


@router.post("", response_model=TagOut, summary="创建标签")
async def create_tag(data: TagCreate, db: AsyncSession = Depends(get_db)):
    existing = (await db.execute(select(Tag).where(Tag.name == data.name))).scalar()
    if existing:
        raise HTTPException(status_code=400, detail="标签名已存在")
    tag = Tag(name=data.name, color=data.color)
    db.add(tag)
    await db.commit()
    await db.refresh(tag)
    return tag.to_dict()


@router.put("/{tag_id}", response_model=TagOut, summary="更新标签")
async def update_tag(tag_id: int, data: TagUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Tag).where(Tag.id == tag_id))
    tag = result.scalar()
    if not tag:
        raise HTTPException(status_code=404, detail="标签不存在")
    if data.name is not None:
        existing = (await db.execute(
            select(Tag).where(Tag.name == data.name, Tag.id != tag_id)
        )).scalar()
        if existing:
            raise HTTPException(status_code=400, detail="标签名已存在")
        tag.name = data.name
    if data.color is not None:
        tag.color = data.color
    await db.commit()
    await db.refresh(tag)
    return tag.to_dict()


@router.delete("/{tag_id}", summary="删除标签")
async def delete_tag(tag_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Tag).where(Tag.id == tag_id))
    tag = result.scalar()
    if not tag:
        raise HTTPException(status_code=404, detail="标签不存在")
    await db.delete(tag)
    await db.commit()
    return {"ok": True}
