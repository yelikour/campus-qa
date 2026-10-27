"""会话接口与运维接口(统计/健康检查)。

会话归属校验(F10,2026-10-27):读取/删除会话须校验 X-User-Token 与会话属主一致,
防止知道会话 ID 即可越权读取或删除他人对话;不一致与不存在统一返回 404,不泄露会话存在性。
"""
from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException

from ..repository import db
from ..services.retrieval import retriever

router = APIRouter(prefix="/api", tags=["conversation"])


def _own_conversation(cid: str, user_token: str | None):
    row = db.get_conversation(cid)
    if row is None or row["user_token"] != (user_token or "anonymous"):
        raise HTTPException(404, "会话不存在或无权访问")
    return row


@router.get("/conversations")
def list_conversations(x_user_token: str | None = Header(default=None)):
    return db.list_conversations((x_user_token or "anonymous")[:64])


@router.get("/conversations/{cid}/messages")
def get_messages(cid: str, x_user_token: str | None = Header(default=None)):
    _own_conversation(cid, (x_user_token or "anonymous")[:64])
    msgs = db.get_messages(cid)
    if not msgs:
        raise HTTPException(404, "会话不存在")
    return msgs


@router.delete("/conversations/{cid}")
def delete_conversation(cid: str, x_user_token: str | None = Header(default=None)):
    _own_conversation(cid, (x_user_token or "anonymous")[:64])
    conn = db.get_conn()
    conn.execute("DELETE FROM message WHERE conversation_id=?", (cid,))
    conn.execute("DELETE FROM conversation WHERE id=?", (cid,))
    conn.commit()
    return {"deleted": cid}
