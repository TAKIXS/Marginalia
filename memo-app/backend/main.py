"""读书摘抄检索系统 - FastAPI 入口"""

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import os
import traceback

from database import engine, DATABASE_URL
from models import Base
from routers.excerpts import router as excerpts_router
from routers.books import router as books_router
from routers.tags import router as tags_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: auto-create tables and FULLTEXT index
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # Ensure FULLTEXT index exists on excerpts (MySQL doesn't support IF NOT EXISTS on indexes)
    try:
        from sqlalchemy import text
        async with engine.connect() as conn:
            await conn.execute(text(
                "CREATE FULLTEXT INDEX ft_excerpt "
                "ON excerpts(content, insights) WITH PARSER ngram"
            ))
    except Exception:
        pass  # index already exists or isn't supported — app still works with LIKE fallback
    yield
    await engine.dispose()


app = FastAPI(title="读书摘抄检索系统", version="3.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=UPLOAD_DIR), name="static")

app.include_router(books_router)
app.include_router(excerpts_router)
app.include_router(tags_router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch-all handler — prevents stack trace leaks."""
    return JSONResponse(
        status_code=500,
        content={"detail": "服务器内部错误"},
    )


@app.get("/api/health")
async def health():
    return {"status": "ok"}
