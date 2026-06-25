"""读书摘抄检索系统 - FastAPI 入口"""

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import traceback

from routers.excerpts import router as excerpts_router
from routers.books import router as books_router
from routers.tags import router as tags_router

app = FastAPI(title="读书摘抄检索系统", version="2.0.0")

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
