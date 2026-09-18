#!/usr/bin/env python3
"""四项架构验收(全部走 HTTP / 进程内真实执行,输出 PASS/FAIL):

  A1 生成降级   —— 云端 GLM 配置了无效 Key 时,流内自动回退本地抽取式,服务不中断
  A2 入口限流   —— 单用户突发超过令牌桶容量,返回 429
  A3 知识热更新 —— 新增条目后无需重启,检索立即命中,索引版本递增(验收后清理)
  A4 无知识兜底 —— 知识库无相关问题时不编造,返回引导性回退话术且无引用来源
"""
import asyncio
import json
import sys

import httpx

BASE = "http://127.0.0.1:8000"
RESULTS = []


def record(name, ok, detail):
    RESULTS.append((name, ok, detail))
    print(f"{'PASS' if ok else 'FAIL'}  {name}  {detail}")


async def read_sse(resp):
    """拼合 SSE delta,返回 (answer_text, meta_dict, done_dict)。"""
    buf, answer, meta, done = "", "", {}, {}
    async for chunk in resp.aiter_text():
        buf += chunk
        events = buf.split("\n\n")
        buf = events.pop()
        for ev in events:
            lines = ev.split("\n")
            etype = next((l[6:].strip() for l in lines if l.startswith("event: ")), "")
            data = next((l for l in lines if l.startswith("data: ")), None)
            if not data:
                continue
            payload = json.loads(data[6:])
            if etype == "delta":
                answer += payload.get("text", "")
            elif etype == "meta":
                meta = payload
            elif etype == "done":
                done = payload
    return answer, meta, done


async def a1_degradation():
    """进程内注入无效 Key 构造 ZhipuGenerator,验证 stream 回退本地抽取式。"""
    sys.path.insert(0, "backend")
    from app.config import settings as cfg
    from app.services import ingestion
    from app.services.generation import ZhipuGenerator
    from app.services.retrieval import retriever
    ingestion.startup()
    old = cfg.ZHIPU_API_KEY
    cfg.ZHIPU_API_KEY = "invalid-key-for-acceptance-test"
    try:
        results = retriever.retrieve("图书馆开放时间是几点")
        gen = ZhipuGenerator()
        out = []
        async for piece in gen.stream("图书馆开放时间是几点", results):
            out.append(piece)
        answer = "".join(out)
        ok = len(answer) > 20 and "图书馆" in answer
        record("A1 生成降级(云端无效 Key → 本地抽取式)", ok,
               f"provider=zhipu-glm 降级产出 {len(answer)} 字,内容含正解关键信息" if ok else f"异常输出:{answer[:50]}")
    finally:
        cfg.ZHIPU_API_KEY = old


async def a2_rate_limit(client):
    token = "acceptance-ratelimit-user"

    async def fire(i):
        r = await client.post(f"{BASE}/api/chat", json={"message": "图书馆开放时间"},
                              headers={"X-User-Token": token})
        return r.status_code
    # 并发突发 15(桶容量 10,补充 5/s;串行慢请求只以 ~2QPS 消耗,不会触发)
    codes = await asyncio.gather(*[fire(i) for i in range(15)])
    n429 = codes.count(429)
    n200 = codes.count(200)
    record("A2 入口限流(令牌桶 5QPS/突发10)", n429 >= 1 and n200 >= 1,
           f"并发 15:200x{n200} / 429x{n429}(超出桶容量的请求被拒)")


async def a3_hot_update(client):
    probe_q = "校史馆开放时间怎么预约"
    doc = {"category": "验收测试", "question": "校史馆开放时间怎么预约?",
           "answer": "校史馆每周二、四、六 10:00-16:00 开放,凭校园卡在一层服务台登记后可自由参观;团体讲解需提前两个工作日电话预约。",
           "source": "验收测试临时条目", "tags": ["校史馆", "预约"]}
    before = (await client.get(f"{BASE}/api/admin/stats")).json()["index_version"]
    r = await client.post(f"{BASE}/api/knowledge", json=[doc])
    added = r.json()
    # 立即检索验证(无重启)
    s = (await client.get(f"{BASE}/api/knowledge/search", params={"q": probe_q})).json()
    hit = any(x["doc_id"] == added.get("doc_id", "") or x["category"] == "验收测试" for x in s["results"])
    # 走问答链路验证
    chat = await client.post(f"{BASE}/api/chat", json={"message": probe_q},
                             headers={"X-User-Token": "acceptance-hotupdate"})
    answer, meta, _ = await read_sse(chat)
    answered = "校史馆" in answer
    after = (await client.get(f"{BASE}/api/admin/stats")).json()["index_version"]
    # 清理:删除验收条目并确认版本再次递增
    doc_id = added["ids"][0]
    d = await client.delete(f"{BASE}/api/knowledge/{doc_id}")
    cleaned = d.status_code == 200
    s2 = (await client.get(f"{BASE}/api/knowledge/search", params={"q": probe_q})).json()
    gone = all(x["category"] != "验收测试" for x in s2["results"])
    record("A3 知识热更新(录入即检索,验收后清理)",
           hit and answered and after > before and cleaned and gone,
           f"版本 {before}→{after}→{d.json().get('index_version')},即时命中={hit},即时回答={answered},清理={cleaned and gone}")


async def a4_no_knowledge_fallback(client):
    chat = await client.post(f"{BASE}/api/chat", json={"message": "今天股票行情怎么样"},
                             headers={"X-User-Token": "acceptance-fallback"})
    answer, meta, done = await read_sse(chat)
    ok = (not meta.get("sources")) and ("暂未收录" in answer or "暂未" in answer)
    record("A4 无知识兜底(不编造,回退引导话术)", ok,
           f"sources={len(meta.get('sources', []))} 条,回答含回退话术={ok}")


async def main():
    async with httpx.AsyncClient(timeout=60) as client:
        await a1_degradation()
        await a4_no_knowledge_fallback(client)
        await a3_hot_update(client)
        await a2_rate_limit(client)
    passed = sum(1 for _, ok, _ in RESULTS if ok)
    print(f"\n验收结果:{passed}/{len(RESULTS)} PASS")
    sys.exit(0 if passed == len(RESULTS) else 1)

if __name__ == "__main__":
    asyncio.run(main())
