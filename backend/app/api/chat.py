"""问答接口:POST /api/chat —— 混合检索 + SSE 流式生成。"""
from __future__ import annotations

import json
import time

from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from ..config import settings
from ..core.security import check_rate_limit
from ..repository import db
from ..services.generation import get_generator
from ..services.retrieval import retriever

router = APIRouter(prefix="/api", tags=["chat"])


class ChatRequest(BaseModel):
    conversation_id: str | None = None
    message: str = Field(min_length=1, max_length=500)


def _user(header_token: str | None) -> str:
    return (header_token or "anonymous")[:64]


@router.post("/chat")
async def chat(req: ChatRequest, x_user_token: str | None = Header(default=None)):
    user = _user(x_user_token)
    if not check_rate_limit(user):
        raise HTTPException(429, "请求过于频繁,请稍后再试(限流保护)")

    # 1. 混合检索
    t0 = time.perf_counter()
    results = retriever.retrieve(req.message, rerank=settings.RERANK_ENABLED)
    retrieval_ms = (time.perf_counter() - t0) * 1000

    sources = [
        {
            "doc_id": r.chunk.doc_id, "title": r.chunk.source, "category": r.chunk.category,
            "score": r.score, "bm25_rank": r.bm25_rank, "vec_rank": r.vec_rank,
        }
        for r in results
    ]

    # 2. 会话管理
    cid = req.conversation_id or db.new_conversation(user)
    if req.conversation_id:
        db.touch_conversation(cid, req.message)
    db.save_message(cid, "user", req.message)

    generator = get_generator()

    async def event_stream():
        answer_parts: list[str] = []
        gen_t0 = time.perf_counter()
        try:
            # meta 事件:先推送引用来源,前端即时展示「正在参考哪些资料」
            yield f"event: meta\ndata: {json.dumps({'conversation_id': cid, 'retrieval_ms': round(retrieval_ms, 1), 'sources': sources, 'provider': generator.name}, ensure_ascii=False)}\n\n"

            if not results:
                fallback = "抱歉,知识库中暂未收录与您问题直接相关的信息。建议您咨询对应职能部门,或换一种问法(例如:『图书馆开放时间』、『校园卡挂失』)。"
                for piece in fallback:
                    yield f"event: delta\ndata: {json.dumps({'text': piece}, ensure_ascii=False)}\n\n"
                    answer_parts.append(piece)
                yield "event: done\ndata: {}\n\n"
                return

            async for piece in generator.stream(req.message, results):
                answer_parts.append(piece)
                yield f"event: delta\ndata: {json.dumps({'text': piece}, ensure_ascii=False)}\n\n"

            elapsed = (time.perf_counter() - gen_t0) * 1000
            answer = "".join(answer_parts)
            mid = db.save_message(cid, "assistant", answer,
                                  sources=json.dumps(sources, ensure_ascii=False),
                                  latency_ms=int(elapsed))
            db.log_query(req.message, hit=True, top_score=results[0].score,
                         latency_ms=int(elapsed), category=results[0].chunk.category)
            yield f"event: done\ndata: {json.dumps({'message_id': mid, 'conversation_id': cid, 'total_ms': round(elapsed, 1)}, ensure_ascii=False)}\n\n"
        except Exception as e:  # 流中断兜底
            yield f"event: error\ndata: {json.dumps({'detail': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
