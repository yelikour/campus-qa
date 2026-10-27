"""知识库管理接口:列表 / 检索 / 新增 / 删除(触发热更新重建索引)。

写接口(新增/删除)受 ADMIN_TOKEN 鉴权保护:未设置该环境变量时为演示
开放模式;设置后须携带 X-Admin-Token 请求头(见 core/security.require_admin)。
"""
from __future__ import annotations

import time

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field

from ..config import settings
from ..core.security import require_admin
from ..repository import db
from ..services import ingestion
from ..services.retrieval import retriever

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


class KnowledgeItem(BaseModel):
    category: str = Field(max_length=30)
    question: str = Field(min_length=4, max_length=200)
    answer: str = Field(min_length=4, max_length=2000)
    tags: list[str] = []
    source: str = Field(default="管理员录入", max_length=100)


@router.get("")
def list_knowledge(page: int = Query(1, ge=1), size: int = Query(10, ge=1, le=50),
                   category: str | None = None, q: str | None = None):
    docs = ingestion.load_seed()
    categories = sorted({d["category"] for d in docs})
    if category:
        docs = [d for d in docs if d["category"] == category]
    if q:
        docs = [d for d in docs if q.lower() in d["question"].lower() or q in d["answer"]]
    total = len(docs)
    return {"total": total, "page": page, "categories": categories,
            "items": docs[(page - 1) * size: page * size]}


@router.post("")
def add_knowledge(items: list[KnowledgeItem],
                  x_admin_token: str | None = Header(default=None)):
    require_admin(x_admin_token)
    if not items:
        raise HTTPException(400, "条目不能为空")
    entries = [i.model_dump() for i in items]
    chunks, ids = ingestion.add_documents(entries)
    return {"added": len(entries), "ids": ids, "total_chunks": chunks, "index_version": retriever.version}


@router.delete("/{doc_id}")
def delete_knowledge(doc_id: str, x_admin_token: str | None = Header(default=None)):
    require_admin(x_admin_token)
    try:
        chunks = ingestion.remove_document(doc_id)
    except KeyError:
        raise HTTPException(404, f"条目 {doc_id} 不存在")
    return {"deleted": doc_id, "total_chunks": chunks, "index_version": retriever.version}


@router.get("/search")
def search_knowledge(q: str = Query(min_length=1), top_k: int = 5):
    t0 = time.perf_counter()
    results = retriever.retrieve(q, top_k=top_k, rerank=settings.RERANK_ENABLED)
    ms = (time.perf_counter() - t0) * 1000
    return {"query": q, "elapsed_ms": round(ms, 1), "results": [
        {"doc_id": r.chunk.doc_id, "text": r.chunk.text, "category": r.chunk.category,
         "score": r.score, "bm25_rank": r.bm25_rank, "vec_rank": r.vec_rank} for r in results]}
