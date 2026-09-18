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


def check_rate_limit(user_token: str) -> bool:
    bucket = _buckets.get(user_token)
    if bucket is None:
        bucket = _buckets[user_token] = TokenBucket(settings.RATE_LIMIT_QPS, settings.RATE_LIMIT_BURST)
    return bucket.allow()
