#!/usr/bin/env python3
"""性能拆分基准:retrieval-only(进程内)与 local-extractive E2E(HTTP)。

输出:QPS、p50/p95/p99 延迟(ms)、失败数。
用法:
  python scripts/bench.py retrieval          # 进程内直调检索链路
  python scripts/bench.py e2e [BASE_URL]     # 全量问答(检索+本地抽取式生成+落库)
"""
import asyncio
import statistics
import sys
import time

QUERIES = [
    "图书馆开放时间", "校园卡挂失", "奖学金申请条件", "宿舍熄灯时间", "论文查重要求",
    "缓考怎么申请", "体测标准是什么", "快递驿站取件", "保研需要什么", "食堂哪个好吃",
    "WiFi 连不上", "勤工助学岗位", "三方协议流程", "心理咨询预约", "火车票优惠",
]

def percentiles(lat_ms):
    s = sorted(lat_ms)
    def pct(p):
        return s[min(len(s) - 1, int(len(s) * p / 100))]
    return pct(50), pct(95), pct(99)

def report(name, lat_ms, fails, wall_s):
    p50, p95, p99 = percentiles(lat_ms)
    n = len(lat_ms) + fails
    print(f"[{name}] 请求 {n} | 失败 {fails} | 总耗时 {wall_s:.2f}s | "
          f"吞吐 {n / wall_s:.1f} QPS | p50 {p50:.1f}ms | p95 {p95:.1f}ms | p99 {p99:.1f}ms")

def bench_retrieval(n=300):
    sys.path.insert(0, "backend")
    from app.services import ingestion
    from app.services.retrieval import retriever
    ingestion.startup()
    for i in range(10):  # 预热(jieba/字典/缓存)
        retriever.retrieve(QUERIES[i % len(QUERIES)])
    lat, fails = [], 0
    t0 = time.perf_counter()
    for i in range(n):
        q = QUERIES[i % len(QUERIES)]
        s = time.perf_counter()
        try:
            r = retriever.retrieve(q)
            if not r:
                fails += 1  # 视为空结果(链路完成,非崩溃)
        except Exception:
            fails += 1
        lat.append((time.perf_counter() - s) * 1000)
    wall = time.perf_counter() - t0
    report(f"retrieval-only x{n}", lat, fails, wall)

async def bench_e2e(base, n=200, concurrency=20):
    import httpx
    sem = asyncio.Semaphore(concurrency)
    lat, fails = [], 0
    lock = asyncio.Lock()

    async def one(client, i):
        nonlocal fails
        q = QUERIES[i % len(QUERIES)]
        token = f"bench-{i % 100:03d}"  # 分散令牌桶,压满 100 用户
        async with sem:
            s = time.perf_counter()
            try:
                r = await client.post(f"{base}/api/chat", json={"message": q},
                                      headers={"X-User-Token": token})
                body = await r.aread()
                ok = r.status_code == 200 and b"done" in body
            except Exception:
                ok = False
            dt = (time.perf_counter() - s) * 1000
            async with lock:
                lat.append(dt)
                if not ok:
                    fails += 1

    async with httpx.AsyncClient(timeout=60) as client:
        await client.get(f"{base}/api/health")
        t0 = time.perf_counter()
        await asyncio.gather(*[one(client, i) for i in range(n)])
        wall = time.perf_counter() - t0
    report(f"local-extractive E2E x{n}(并发{concurrency})", lat, fails, wall)

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "retrieval"
    if mode == "retrieval":
        bench_retrieval()
    else:
        base = sys.argv[2] if len(sys.argv) > 2 else "http://127.0.0.1:8000"
        asyncio.run(bench_e2e(base))
