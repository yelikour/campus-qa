"""智问校园 CampusMind —— 校园智能问答系统(AI+RAG)后端入口。"""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import settings
from .repository import db
from .services import ingestion
from .api import chat, knowledge, conversations, admin


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_schema()
    ingestion.startup()
    yield


app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)

app.include_router(chat.router)
app.include_router(knowledge.router)
app.include_router(conversations.router)
app.include_router(admin.router)

# 前端静态资源(开发期同源部署;生产由 Nginx 托管并反代 /api)
frontend_dir = Path(__file__).resolve().parent.parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")
