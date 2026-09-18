"""运维接口:健康检查、运行统计。"""
from fastapi import APIRouter

from ..config import settings
from ..repository import db
from ..services.retrieval import retriever

router = APIRouter(prefix="/api", tags=["ops"])


@router.get("/health")
def health():
    return {"status": "ok", "app": settings.APP_NAME, "version": settings.APP_VERSION}


@router.get("/admin/stats")
def admin_stats():
    s = db.stats()
    s["index_version"] = retriever.version
    s["chunk_count"] = len(retriever.chunks)
    s["llm_provider"] = settings.LLM_PROVIDER
    s["embedding_provider"] = retriever.embedder_name
    s["rerank_enabled"] = settings.RERANK_ENABLED
    return s
