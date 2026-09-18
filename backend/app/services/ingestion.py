"""知识摄取服务:加载种子语料 → 清洗/分块 → 构建双通道索引,支持热更新。"""
from __future__ import annotations

import json
import threading
import time

from ..config import settings
from .retrieval import KnowledgeChunk, retriever

_lock = threading.Lock()


def _load_seed() -> list[dict]:
    with open(settings.SEED_QA_PATH, encoding="utf-8") as f:
        return json.load(f)


def _to_chunks(docs: list[dict]) -> list[KnowledgeChunk]:
    """QA 拆分策略:question 通道负责『问法匹配』,answer 通道负责『内容覆盖』。

    每个 chunk 携带 doc_id,引用溯源时聚合回同一文档。
    """
    chunks: list[KnowledgeChunk] = []
    for d in docs:
        cid = d["id"]
        chunks.append(KnowledgeChunk(
            id=f"{cid}-q", doc_id=cid, category=d["category"],
            text=f"{d['question']} {d['answer']}", source=d["source"], tags=d.get("tags", []),
            answer_text=d["answer"],
        ))
        # 长答案按句号滑窗二次分块(每块 ≤3 句),保证长文档召回粒度
        answer = d["answer"]
        sentences = [s.strip() for s in answer.replace("。", "。\n").split("\n") if s.strip()]
        for i in range(0, len(sentences), 3):
            piece = "".join(sentences[i:i + 3])
            if len(piece) < 8:
                continue
            chunks.append(KnowledgeChunk(
                id=f"{cid}-a{i//3}", doc_id=cid, category=d["category"],
                text=piece, source=d["source"], tags=d.get("tags", []),
            ))
    return chunks


def rebuild_index(docs: list[dict] | None = None) -> int:
    docs = docs if docs is not None else _load_seed()
    chunks = _to_chunks(docs)
    with _lock:
        retriever.build(chunks)
    return len(chunks)


def add_documents(entries: list[dict]) -> tuple[int, list[str]]:
    docs = _load_seed()
    base = max((int(d["id"].split("-")[-1]) for d in docs), default=0) if docs else 0
    new_ids = []
    for i, e in enumerate(entries, start=base + 1):
        e.setdefault("id", f"kb-{i:03d}")
        e.setdefault("category", "其他")
        e.setdefault("tags", [])
        e.setdefault("source", "管理员录入")
        e.setdefault("updated_at", time.strftime("%Y-%m-%d"))
        new_ids.append(e["id"])
        docs.append(e)
    with open(settings.SEED_QA_PATH, "w", encoding="utf-8") as f:
        json.dump(docs, f, ensure_ascii=False, indent=1)
    return rebuild_index(docs), new_ids


def startup() -> int:
    n = rebuild_index()
    print(f"[ingestion] 索引就绪:{len(_load_seed())} 篇文档 / {n} 个 chunk")
    return n
