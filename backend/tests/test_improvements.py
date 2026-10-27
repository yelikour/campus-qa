"""2026-10-16 完善轮新增测试:RRF 公式正确性、观测数据不失真、鉴权、
令牌桶淘汰、BM25 倒排索引等价性、知识删除与降级日志。

背景见 docs/IMPROVEMENTS.md;既有冒烟测试(test_smoke.py)不受影响。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import settings                                  # noqa: E402
from app.core import security                                    # noqa: E402
from app.services import ingestion                               # noqa: E402
from app.services.retrieval import BM25Index, KnowledgeChunk, retriever  # noqa: E402


# ---------------------------------------------------------------- RRF 公式正确性
def _mini_chunks():
    """构造可控小语料:a 与查询强词面重叠,b 中度,c 无关。"""
    return [
        KnowledgeChunk(id="a-q", doc_id="a", category="学业", text="选课 时间 安排 选课",
                       source="教务处", tags=["选课"]),
        KnowledgeChunk(id="b-q", doc_id="b", category="学业", text="退课 时间 规定 退课",
                       source="教务处", tags=["退课"]),
        KnowledgeChunk(id="c-q", doc_id="c", category="生活", text="食堂 菜品 推荐",
                       source="后勤", tags=["食堂"]),
    ]


def test_rrf_uses_rank_based_formula():
    """融合分应符合标准 RRF:score = Σ 1/(RRF_K + rank),而非常数 1/(RRF_K+1)。"""
    retriever.build(_mini_chunks())
    fused = retriever.fuse_rrf("选课 时间", candidate_k=10)
    assert fused, "应有融合候选"
    k = settings.RRF_K
    for i, s, ranks in fused:
        expect = 0.0
        if "bm25" in ranks:
            expect += 1.0 / (k + ranks["bm25"])
        if "vec" in ranks:
            expect += 1.0 / (k + ranks["vec"])
        assert abs(s - expect) < 1e-9, f"chunk {i}: 实得 {s} 期望 {expect}(标准 RRF)"


def test_rrf_prefers_higher_rank_within_same_channel_hits():
    """同为双通道命中时,平均排名更靠前者应排前(常数版无法区分)。"""
    retriever.build(_mini_chunks())
    fused = retriever.fuse_rrf("选课 时间", candidate_k=10)
    assert fused[0][0] == 0, "词面强重叠的 a 应排第一"


def test_vec_rank_absent_when_only_bm25_hits():
    """仅 BM25 命中的 chunk 不应伪造 vec 排名(引用卡片观测数据不失真)。"""
    ingestion.rebuild_index()
    fused = retriever.fuse_rrf("图书馆开放时间", candidate_k=20)
    only_bm25 = [(i, rk) for i, _, rk in fused if "bm25" in rk and "vec" not in rk]
    assert only_bm25, "候选池中应存在仅 BM25 命中的 chunk"
    # 生产 retrieve() 输出:每条结果至少有一个真实通道排名,未命中通道保持 None
    for r in retriever.retrieve("图书馆开放时间", rerank=False):
        assert (r.bm25_rank is None) != (r.vec_rank is None) or \
               (r.bm25_rank is not None and r.vec_rank is not None), \
               "排名字段应来自真实命中的通道"


# ---------------------------------------------------------------- BM25 倒排索引等价性
def test_bm25_inverted_index_equivalent_to_bruteforce():
    """倒排索引实现与逐文档暴力扫描(旧实现算法)在真实语料上逐查询一致。"""
    docs = ingestion.load_seed()
    chunks = ingestion._to_chunks(docs)
    idx = BM25Index(chunks)
    k1, b = idx.k1, idx.b

    def bruteforce(query, top_k=10):
        import math
        from app.services.retrieval import tokenize
        scores = {}
        for w in tokenize(query):
            if w not in idx.df:
                continue
            idf = math.log((idx.N - idx.df.get(w, 0) + 0.5) / (idx.df.get(w, 0) + 0.5) + 1.0)
            for i, tokens in enumerate(idx.doc_tokens):
                tf = tokens.count(w)
                if tf == 0:
                    continue
                denom = tf + k1 * (1 - b + b * idx.doc_len[i] / idx.avgdl)
                scores[i] = scores.get(i, 0.0) + idf * tf * (k1 + 1) / denom
        return sorted(scores.items(), key=lambda x: -x[1])[:top_k]

    queries = ["图书馆开放时间", "校园卡挂失", "奖学金申请条件", "宿舍熄灯时间",
               "论文查重要求", "缓考怎么申请", "体测标准", "保研需要什么"]
    for q in queries:
        got, want = idx.search(q, 10), bruteforce(q, 10)
        assert [i for i, _ in got] == [i for i, _ in want], f"{q}: 倒排结果与暴力扫描不一致"
        for (i, s), (j, t) in zip(got, want):
            assert i == j and abs(s - t) < 1e-9, f"{q}: 分数不一致 {s} vs {t}"


# ---------------------------------------------------------------- 鉴权与限流
def test_admin_token_gates_knowledge_writes():
    """设置 ADMIN_TOKEN 后,无/错令牌写知识库返回 401,正确令牌放行。"""
    from fastapi.testclient import TestClient
    from app.main import app

    old = settings.ADMIN_TOKEN
    settings.ADMIN_TOKEN = "test-secret"
    doc = [{"category": "测试", "question": "鉴权测试问法?", "answer": "鉴权测试答案。",
            "source": "单元测试"}]
    try:
        with TestClient(app) as client:
            assert client.post("/api/knowledge", json=doc).status_code == 401, "无令牌应 401"
            assert client.post("/api/knowledge", json=doc,
                               headers={"X-Admin-Token": "wrong"}).status_code == 401, "错令牌应 401"
            r = client.post("/api/knowledge", json=doc,
                            headers={"X-Admin-Token": "test-secret"})
            assert r.status_code == 200, f"正确令牌应放行:{r.text}"
            # 清理测试条目(带令牌删除)
            d = client.delete(f"/api/knowledge/{r.json()['ids'][0]}",
                              headers={"X-Admin-Token": "test-secret"})
            assert d.status_code == 200
    finally:
        settings.ADMIN_TOKEN = old


def test_admin_token_unset_keeps_demo_open():
    """未设置 ADMIN_TOKEN(默认演示模式)时写接口保持开放,验收脚本兼容。"""
    from fastapi.testclient import TestClient
    from app.main import app

    old = settings.ADMIN_TOKEN
    settings.ADMIN_TOKEN = ""
    doc = [{"category": "测试", "question": "开放模式测试?", "answer": "开放模式答案。",
            "source": "单元测试"}]
    try:
        with TestClient(app) as client:
            r = client.post("/api/knowledge", json=doc)
            assert r.status_code == 200, "演示模式应免令牌放行"
            client.delete(f"/api/knowledge/{r.json()['ids'][0]}")
    finally:
        settings.ADMIN_TOKEN = old


def test_token_bucket_eviction():
    """桶字典超过上限时按最久未活跃淘汰,内存有界。"""
    security._buckets.clear()
    old_max = security._MAX_BUCKETS
    security._MAX_BUCKETS = 6
    try:
        for i in range(10):
            assert security.check_rate_limit(f"user-{i}")
        assert len(security._buckets) <= 6, f"应淘汰至不超过上限,实得 {len(security._buckets)}"
        assert security.check_rate_limit("user-9"), "最近创建的桶应仍可用"
    finally:
        security._MAX_BUCKETS = old_max
        security._buckets.clear()


# ---------------------------------------------------------------- 知识删除一致性
def test_remove_document_semantics():
    """删除存在条目 → 文件与索引同步;删除不存在条目 → KeyError。"""
    docs_before = ingestion.load_seed()
    entry = [{"category": "临时", "question": "删除语义测试问法?", "answer": "删除语义测试答案。",
              "source": "单元测试", "tags": []}]
    _, ids = ingestion.add_documents(entry)
    did = ids[0]
    assert any(d["id"] == did for d in ingestion.load_seed()), "新增后应存在"
    assert any(c.doc_id == did for c in retriever.chunks), "索引应含新 chunk"
    ingestion.remove_document(did)
    assert all(d["id"] != did for d in ingestion.load_seed()), "删除后应不存在"
    assert all(c.doc_id != did for c in retriever.chunks), "索引应同步移除"
    try:
        ingestion.remove_document(did)
        raise AssertionError("重复删除应抛 KeyError")
    except KeyError:
        pass
    assert len(ingestion.load_seed()) == len(docs_before), "增删后语料应恢复原状"


# ---------------------------------------------------------------- 会话归属隔离(F10)
def test_conversation_isolation():
    """会话读取/删除须校验属主:他人令牌访问返回 404,属主正常访问。"""
    import json
    from fastapi.testclient import TestClient
    from app.main import app

    with TestClient(app) as client:
        # 用户 A 建立会话并提问(SSE meta 事件携带 conversation_id)
        with client.stream("POST", "/api/chat", json={"message": "图书馆开放时间"},
                           headers={"X-User-Token": "iso-user-a"}) as resp:
            meta_cid = None
            for line in resp.iter_lines():
                if line.startswith("data:") and "conversation_id" in line:
                    meta_cid = json.loads(line[5:].strip())["conversation_id"]
                    break
        assert meta_cid, "应从 meta 事件取到会话 id"

        # 用户 B 越权读取/删除 → 404(与不存在一致,不泄露存在性)
        assert client.get(f"/api/conversations/{meta_cid}/messages",
                          headers={"X-User-Token": "iso-user-b"}).status_code == 404
        assert client.delete(f"/api/conversations/{meta_cid}",
                             headers={"X-User-Token": "iso-user-b"}).status_code == 404
        # 属主 A 正常读取与删除
        assert client.get(f"/api/conversations/{meta_cid}/messages",
                          headers={"X-User-Token": "iso-user-a"}).status_code == 200
        assert client.delete(f"/api/conversations/{meta_cid}",
                             headers={"X-User-Token": "iso-user-a"}).status_code == 200


# ---------------------------------------------------------------- 降级可归因
def test_zhipu_fallback_logs_reason(capsys, monkeypatch):
    """云端不可用时降级到本地抽取式,且降级原因输出日志(可归因)。"""
    import asyncio
    from app.services.generation import ZhipuGenerator

    monkeypatch.setattr(settings, "ZHIPU_BASE_URL", "http://127.0.0.1:1/")  # 立即连接失败
    retriever_results = retriever.retrieve("图书馆开放时间")
    out = []
    async def run():
        async for piece in ZhipuGenerator().stream("图书馆开放时间", retriever_results):
            out.append(piece)
    asyncio.run(run())
    captured = capsys.readouterr().out
    assert "降级本地抽取式" in captured, f"应输出降级日志,实得:{captured!r}"
    assert "ConnectError" in captured or "Error" in captured, f"日志应含异常类型,实得:{captured!r}"
    assert "".join(out), "降级后仍应有本地生成产出"
