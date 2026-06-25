"""SQLAlchemy ORM 模型 — 读书摘抄系统"""

from sqlalchemy import (
    Column, BigInteger, Integer, String, Text, DateTime, ForeignKey,
    JSON, UniqueConstraint, Boolean
)
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    author = Column(String(255), default="")
    cover = Column(String(500), default="")
    created_at = Column(DateTime, server_default=func.now())

    excerpts = relationship("Excerpt", back_populates="book", lazy="selectin",
                            cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("title", "author", name="uk_title_author"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "author": self.author,
            "cover": self.cover,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Excerpt(Base):
    __tablename__ = "excerpts"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    book_id = Column(Integer, ForeignKey("books.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text)
    insights = Column(Text)
    links = Column(JSON, default=list)
    images = Column(JSON, default=list)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    is_favorite = Column(Boolean, default=False, server_default="0")

    book = relationship("Book", back_populates="excerpts", lazy="selectin")
    tags = relationship("Tag", secondary="excerpt_tags", back_populates="excerpts", lazy="selectin")

    def to_dict(self):
        return {
            "id": self.id,
            "book_id": self.book_id,
            "content": self.content,
            "insights": self.insights,
            "links": self.links or [],
            "images": self.images or [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "book": self.book.to_dict() if self.book else None,
            "tags": [t.to_dict() for t in self.tags] if self.tags else [],
            "is_favorite": bool(self.is_favorite),
        }


class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False)
    color = Column(String(7), default="#409EFF")
    created_at = Column(DateTime, server_default=func.now())

    excerpts = relationship("Excerpt", secondary="excerpt_tags", back_populates="tags", lazy="selectin")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "color": self.color,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ExcerptTag(Base):
    __tablename__ = "excerpt_tags"

    excerpt_id = Column(BigInteger, ForeignKey("excerpts.id", ondelete="CASCADE"), primary_key=True)
    tag_id = Column(Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)
