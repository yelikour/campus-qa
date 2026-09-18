"""知识库管理接口:列表 / 检索 / 新增(触发热更新重建索引)。"""
from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ..config import settings
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
    docs = json.load(open(settings.SEED_QA_PATH, encoding="utf-8"))
    if category:
        docs = [d for d in docs if d["category"] == category]
    if q:
        docs = [d for d in docs if q.lower() in d["question"].lower() or q in d["answer"]]
    categories = sorted({d["category"] for d in json.load(open(settings.SEED_QA_PATH, encoding="utf-8"))})
    total = len(docs)
    return {"total": total, "page": page, "categories": categories,
            "items": docs[(page - 1) * size: page * size]}


@router.post("")
def add_knowledge(items: list[KnowledgeItem]):
    if not items:
        raise HTTPException(400, "条目不能为空")
    entries = [i.model_dump() for i in items]
    chunks, ids = ingestion.add_documents(entries)
    return {"added": len(entries), "ids": ids, "total_chunks": chunks, "index_version": retriever.version}


@router.delete("/{doc_id}")
def delete_knowledge(doc_id: str):
    docs = json.load(open(settings.SEED_QA_PATH, encoding="utf-8"))
    rest = [d for d in docs if d["id"] != doc_id]
    if len(rest) == len(docs):
        raise HTTPException(404, f"条目 {doc_id} 不存在")
    json.dump(rest, open(settings.SEED_QA_PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    chunks = ingestion.rebuild_index(rest)
    return {"deleted": doc_id, "total_chunks": chunks, "index_version": retriever.version}


@router.get("/search")
def search_knowledge(q: str = Query(min_length=1), top_k: int = 5):
    t0 = __import__("time").perf_counter()
    results = retriever.retrieve(q, top_k=top_k, rerank=settings.RERANK_ENABLED)
    ms = (__import__("time").perf_counter() - t0) * 1000
    return {"query": q, "elapsed_ms": round(ms, 1), "results": [
        {"doc_id": r.chunk.doc_id, "text": r.chunk.text, "category": r.chunk.category,
         "score": r.score, "bm25_rank": r.bm25_rank, "vec_rank": r.vec_rank} for r in results]}
