"""会话接口与运维接口(统计/健康检查)。"""
from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException

from ..repository import db
from ..services.retrieval import retriever

router = APIRouter(prefix="/api", tags=["conversation"])


@router.get("/conversations")
def list_conversations(x_user_token: str | None = Header(default=None)):
    return db.list_conversations((x_user_token or "anonymous")[:64])


@router.get("/conversations/{cid}/messages")
def get_messages(cid: str):
    msgs = db.get_messages(cid)
    if not msgs:
        raise HTTPException(404, "会话不存在")
    return msgs


@router.delete("/conversations/{cid}")
def delete_conversation(cid: str):
    conn = db.get_conn()
    conn.execute("DELETE FROM message WHERE conversation_id=?", (cid,))
    conn.execute("DELETE FROM conversation WHERE id=?", (cid,))
    conn.commit()
    return {"deleted": cid}
