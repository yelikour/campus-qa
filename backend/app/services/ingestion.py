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


def _save_seed(docs: list[dict]) -> None:
    with open(settings.SEED_QA_PATH, "w", encoding="utf-8") as f:
        json.dump(docs, f, ensure_ascii=False, indent=1)


def _rebuild(docs: list[dict]) -> int:
    """重建索引(调用方须已持有 _lock,rebuild_index/add/remove 统一串行化)。"""
    chunks = _to_chunks(docs)
    retriever.build(chunks)
    return len(chunks)


def rebuild_index(docs: list[dict] | None = None) -> int:
    docs = docs if docs is not None else _load_seed()
    with _lock:
        return _rebuild(docs)


def add_documents(entries: list[dict]) -> tuple[int, list[str]]:
    with _lock:
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
        _save_seed(docs)
        n = _rebuild(docs)
    return n, new_ids


def remove_document(doc_id: str) -> int:
    """删除知识条目并热重建索引(与新增共用同一把文件锁,消除读写竞态)。

    不存在时抛 KeyError,由 API 层转 404。
    """
    with _lock:
        docs = _load_seed()
        rest = [d for d in docs if d["id"] != doc_id]
        if len(rest) == len(docs):
            raise KeyError(doc_id)
        _save_seed(rest)
        return _rebuild(rest)


def startup() -> int:
    n = rebuild_index()
    print(f"[ingestion] 索引就绪:{len(_load_seed())} 篇文档 / {n} 个 chunk")
    return n
