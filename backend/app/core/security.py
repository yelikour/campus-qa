"""安全与稳定性:单机令牌桶限流(生产替换为 Redis 滑动窗口 + 网关层限流)。"""
from __future__ import annotations

import time

from ..config import settings


class TokenBucket:
    def __init__(self, qps: float, burst: int):
        self.capacity = burst
        self.tokens = float(burst)
        self.rate = qps
        self.last = time.monotonic()

    def allow(self) -> bool:
        now = time.monotonic()
        self.tokens = min(self.capacity, self.tokens + (now - self.last) * self.rate)
        self.last = now
        if self.tokens >= 1:
            self.tokens -= 1
            return True
        return False


_buckets: dict[str, TokenBucket] = {}

# 桶字典上限:防止攻击者伪造海量 X-User-Token 造成无界内存增长。
# 超限时按最久未活跃淘汰一半(简单 LRU 近似;生产换 Redis 时由 TTL 承担)
_MAX_BUCKETS = 10_000


def check_rate_limit(user_token: str) -> bool:
    bucket = _buckets.get(user_token)
    if bucket is None:
        if len(_buckets) >= _MAX_BUCKETS:
            for k in sorted(_buckets, key=lambda k: _buckets[k].last)[: _MAX_BUCKETS // 2]:
                del _buckets[k]
        bucket = _buckets[user_token] = TokenBucket(settings.RATE_LIMIT_QPS, settings.RATE_LIMIT_BURST)
    return bucket.allow()


def require_admin(x_admin_token: str | None) -> None:
    """知识库写接口鉴权:设置 ADMIN_TOKEN 后强制校验 X-Admin-Token 请求头。

    未设置(默认,演示模式)保持开放 —— 课程演示与 acceptance.py 不需要 Key;
    生产部署设置该环境变量即启用鉴权,防止未授权增删知识库。
    """
    if settings.ADMIN_TOKEN and x_admin_token != settings.ADMIN_TOKEN:
        from fastapi import HTTPException
        raise HTTPException(401, "管理操作需要有效的 X-Admin-Token")
