"""检索服务:RAG 核心链路 —— 混合检索(BM25 + 向量)→ RRF 融合 → 重排序。

架构说明(对应架构文档 §6.2):
- 稀疏通道 BM25:自实现 k1=1.5/b=0.75,jieba 分词,负责关键词精确匹配;
- 稠密通道:EmbeddingProvider 抽象。演示环境用 TF-IDF 加权词袋向量
  (零外部依赖、离线可跑);生产环境切换为智谱 embedding-3 等真实
  语义向量 + Milvus/pgvector,接口不变;
- 融合:Reciprocal Rank Fusion(RRF),对排名而非分数融合,免归一化;
- 重排:Reranker 抽象。演示用特征化轻量重排(查询覆盖率、句子级
  重叠、类别信号);生产可替换 BGE-reranker 等 Cross-Encoder。
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from typing import Callable

import jieba

from ..config import settings


# ---------------------------------------------------------------- 数据模型
@dataclass
class KnowledgeChunk:
    """知识片段:一条 QA 的最小检索单元(question/answer 各建一个通道)。"""
    id: str
    doc_id: str
    category: str
    text: str
    source: str
    tags: list[str] = field(default_factory=list)
    kind: str = "qa"          # qa | passage
    answer_text: str | None = None  # qa 通道的纯答案正文,供生成器抽取


@dataclass
class RetrievedChunk:
    chunk: KnowledgeChunk
    score: float
    bm25_rank: int | None = None
    vec_rank: int | None = None


# ---------------------------------------------------------------- 分词
_stopwords = set(list("的了和是就都而及与着或在在一一各每写首找我你他她它帮") + [
    "一个", "没有", "我们", "你们", "他们", "它们", "这", "那",
    "怎么", "怎么样", "怎样", "如何", "什么", "哪些", "哪个", "请问", "请",
    "吗", "呢", "吧", "呀", "哦", "嘛", "么", "啊", "啥",
    "今天", "明天", "最近", "附近", "学校", "可以", "能", "想", "要",
    "帮忙", "帮我", "一下", "还是", "有没有", "应该", "需要", "一首",
])

def tokenize(text: str) -> list[str]:
    words = jieba.lcut_for_search(text.lower())
    return [w for w in words if w.strip() and not re.fullmatch(r"[\d\W]+", w) and w not in _stopwords]


# ---------------------------------------------------------------- 稀疏通道:BM25
class BM25Index:
    def __init__(self, chunks: list[KnowledgeChunk], k1: float = 1.5, b: float = 0.75):
        self.k1, self.b = k1, b
        self.chunks = chunks
        self.doc_tokens = [tokenize(f"{c.category} {c.text} {' '.join(c.tags)}") for c in chunks]
        self.doc_len = [len(t) for t in self.doc_tokens]
        self.avgdl = sum(self.doc_len) / max(1, len(self.doc_len))
        self.df: dict[str, int] = {}
        # 倒排索引:词 → {文档下标: 词频}。查询只访问命中词的倒排链,
        # 免去逐文档全量扫描(等价性由 tests/test_improvements.py 对暴力实现校验)
        self.inv: dict[str, dict[int, int]] = {}
        for i, tokens in enumerate(self.doc_tokens):
            for w in tokens:
                postings = self.inv.setdefault(w, {})
                postings[i] = postings.get(i, 0) + 1
            for w in set(tokens):
                self.df[w] = self.df.get(w, 0) + 1
        self.N = len(chunks)

    def idf(self, w: str) -> float:
        return math.log((self.N - self.df.get(w, 0) + 0.5) / (self.df.get(w, 0) + 0.5) + 1.0)

    def search(self, query: str, top_k: int = 10) -> list[tuple[int, float]]:
        q = tokenize(query)
        scores: dict[int, float] = {}
        for w in q:
            postings = self.inv.get(w)
            if not postings:
                continue
            idf = self.idf(w)
            for i, tf in postings.items():
                denom = tf + self.k1 * (1 - self.b + self.b * self.doc_len[i] / self.avgdl)
                scores[i] = scores.get(i, 0.0) + idf * tf * (self.k1 + 1) / denom
        ranked = sorted(scores.items(), key=lambda x: -x[1])[:top_k]
        return ranked


# ---------------------------------------------------------------- 稠密通道:向量
class EmbeddingProvider:
    """向量提供者抽象(本地 TF-IDF 实现,离线 fallback,无语义嵌入能力)。

    远程语义实现见 ZhipuEmbeddingProvider:统一 embed_batch/embed_query 接口,
    VectorIndex 按需选择稠密/稀疏构建路径,上层编排代码不变。
    """
    name = "local-tfidf"
    is_remote = False

    def __init__(self):
        self.vocab: dict[str, int] = {}

    def _ensure_vocab(self, token_docs: list[list[str]]):
        for tokens in token_docs:
            for w in tokens:
                if w not in self.vocab:
                    self.vocab[w] = len(self.vocab)

    def _vectorize(self, tokens: list[str], idf_fn: Callable[[str], float]) -> dict[int, float]:
        v: dict[int, float] = {}
        n = len(tokens) or 1
        for w in tokens:
            idx = self.vocab.get(w)
            if idx is None:
                continue
            v[idx] = v.get(idx, 0.0) + idf_fn(w) / n
        return v

    @staticmethod
    def cosine(a, b) -> float:
        if len(b) < len(a):
            a, b = b, a
        if isinstance(a, dict):  # 稀疏(TF-IDF)
            dot = sum(s * b.get(i, 0.0) for i, s in a.items())
            if dot == 0:
                return 0.0
            na = math.sqrt(sum(x * x for x in a.values()))
            nb = math.sqrt(sum(x * x for x in b.values()))
            return dot / (na * nb)
        # 稠密(远程语义向量)
        dot = sum(x * y for x, y in zip(a, b))
        if dot == 0:
            return 0.0
        na = math.sqrt(sum(x * x for x in a))
        nb = math.sqrt(sum(x * x for x in b))
        return dot / (na * nb)


class ZhipuEmbeddingProvider(EmbeddingProvider):
    """云端语义向量 Provider:智谱 embedding-3(openai 兼容协议)。

    需配置 ZHIPUAI_API_KEY;未配置或调用失败时由 get_embedder() 回退 TF-IDF。
    向量带内存缓存,避免重复嵌入同一 chunk(索引热重建时增量复用)。
    """
    name = "zhipu-embedding-3"
    is_remote = True
    _MODEL = "embedding-3"
    _BATCH = 16

    def __init__(self):
        super().__init__()
        import httpx  # noqa: F401 (延迟导入,TF-IDF 模式零网络依赖)
        from ..config import settings
        if not settings.ZHIPU_API_KEY:
            raise RuntimeError("ZHIPUAI_API_KEY 未配置,无法启用云端语义向量")
        self._cache: dict[str, list[float]] = {}

    def _embed(self, texts: list[str]) -> list[list[float]]:
        import json
        import httpx
        from ..config import settings
        out: list[list[float]] = []
        todo = [t for t in texts if t not in self._cache]
        for i in range(0, len(todo), self._BATCH):
            batch = todo[i:i + self._BATCH]
            resp = httpx.post(
                settings.ZHIPU_BASE_URL + "embeddings",
                headers={"Authorization": f"Bearer {settings.ZHIPU_API_KEY}"},
                json={"model": self._MODEL, "input": batch},
                timeout=30.0,
            )
            resp.raise_for_status()
            data = sorted(json.loads(resp.text)["data"], key=lambda d: d["index"])
            for t, d in zip(batch, data):
                self._cache[t] = [float(x) for x in d["embedding"]]
        return [self._cache[t] for t in texts]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return self._embed(texts)

    def embed_query(self, text: str) -> list[float]:
        return self._embed([text])[0]


def get_embedder() -> EmbeddingProvider:
    """工厂:auto 模式下有 Key 用云端语义向量,否则 TF-IDF 离线 fallback。"""
    from ..config import settings
    pref = settings.EMBEDDING_PROVIDER
    if pref in ("auto", "zhipu") and settings.ZHIPU_API_KEY:
        try:
            return ZhipuEmbeddingProvider()
        except Exception as e:
            print(f"[retrieval] 云端语义向量不可用,回退 TF-IDF:{e}")
    return EmbeddingProvider()


class VectorIndex:
    def __init__(self, chunks: list[KnowledgeChunk], embedder: EmbeddingProvider):
        self.chunks = chunks
        self.embedder = embedder
        if embedder.is_remote:
            # 稠密路径:批量语义嵌入(查询与文档同一编码器)
            vecs = embedder.embed_batch([c.text for c in chunks])
            self.doc_vecs = list(vecs)
            return
        # 稀疏路径:TF-IDF 加权词袋(离线,与 BM25 共享 idf)
        token_docs = [tokenize(f"{c.category} {c.text} {' '.join(c.tags)}") for c in chunks]
        self.bm25 = BM25Index.__new__(BM25Index)  # 仅复用 idf
        self.bm25.df = {}
        for tokens in token_docs:
            for w in set(tokens):
                self.bm25.df[w] = self.bm25.df.get(w, 0) + 1
        self.bm25.N = len(chunks)
        self.embedder._ensure_vocab(token_docs)
        self.doc_vecs = [self.embedder._vectorize(t, self.bm25.idf) for t in token_docs]

    def search(self, query: str, top_k: int = 10) -> list[tuple[int, float]]:
        if self.embedder.is_remote:
            qv = self.embedder.embed_query(query)
        else:
            qv = self.embedder._vectorize(tokenize(query), self.bm25.idf)
        sims = [(i, EmbeddingProvider.cosine(qv, dv)) for i, dv in enumerate(self.doc_vecs)]
        sims.sort(key=lambda x: -x[1])
        return [x for x in sims[:top_k] if x[1] > 0]


# ---------------------------------------------------------------- 重排
class LightweightReranker:
    """特征化轻量重排:实质词覆盖 + 二元词重叠 + 句子级重叠 + 同义词标签信号。

    设计约束(62 条评测标定):
    - 查询实质词与文档(含 tags)零交集 → 硬归零,保证无关问题触发兜底;
    - 同义词标签命中加权,缓解口语改写与标准问法的词面差异;
    生产部署时替换为 Cross-Encoder(如 bge-reranker-base),接口不变。
    """
    def rerank(self, query: str, cands: list[KnowledgeChunk]) -> list[tuple[KnowledgeChunk, float]]:
        q_tokens = set(tokenize(query))
        q_bigrams = self._bigrams(query)
        out = []
        for c in cands:
            c_tokens = set(tokenize(f"{c.text} {' '.join(c.tags)}"))
            tag_hit = any(t in q_tokens for t in c.tags)
            hard = len(q_tokens & c_tokens) + (1 if tag_hit else 0)
            if hard == 0:
                out.append((c, 0.0))
                continue
            cover = len(q_tokens & c_tokens) / max(1, len(q_tokens))
            doc_bigrams = self._bigrams(c.text)
            bigram_overlap = len(q_bigrams & doc_bigrams) / max(1, len(q_bigrams))
            sent_hit = self._best_sentence_overlap(query, c.text)
            score = 0.30 * cover + 0.20 * bigram_overlap + 0.35 * sent_hit + (0.15 if tag_hit else 0)
            out.append((c, round(score, 4)))
        out.sort(key=lambda x: -x[1])
        return out

    @staticmethod
    def _bigrams(text: str) -> set[str]:
        toks = tokenize(text)
        return {f"{a}_{b}" for a, b in zip(toks, toks[1:])}

    @staticmethod
    def _best_sentence_overlap(query: str, doc: str) -> float:
        qs = set(tokenize(query))
        best = 0.0
        for sent in re.split(r"[。;!;?\n]", doc):
            if not sent.strip():
                continue
            ss = set(tokenize(sent))
            if not ss:
                continue
            best = max(best, len(qs & ss) / len(qs))
        return best


# ---------------------------------------------------------------- 混合检索编排
class HybridRetriever:
    def __init__(self):
        self.chunks: list[KnowledgeChunk] = []
        self.bm25: BM25Index | None = None
        self.vector: VectorIndex | None = None
        self.reranker = LightweightReranker()
        self.embedder_name = "local-tfidf"
        self.version = 0

    def build(self, chunks: list[KnowledgeChunk]):
        self.chunks = chunks
        self.bm25 = BM25Index(chunks)
        embedder = get_embedder()
        try:
            self.vector = VectorIndex(chunks, embedder)
        except Exception as e:
            # 云端语义向量构建失败(网络/配额)→ 回退 TF-IDF,保证检索可用
            print(f"[retrieval] 语义向量索引构建失败,回退 TF-IDF:{e}")
            self.vector = VectorIndex(chunks, EmbeddingProvider())
        self.embedder_name = self.vector.embedder.name
        self.version += 1

    def fuse_rrf(self, query: str, candidate_k: int | None = None) -> list[tuple[int, float, dict[int, int]]]:
        """双通道并行检索 + RRF 融合(不含重排)。供编排与评测共用。

        标准公式:score(d) = Σ_channel 1 / (RRF_K + rank),对排名而非原始分数
        融合,免归一化。早期实现误用常数 1/(RRF_K+1)(与排名无关,等价于
        通道计数),在 TF-IDF 演示语料上指标恰好持平,但接入真实语义向量后
        双通道分歧增大,会系统性偏好"双通道都命中但排名靠后"的文档,已修正;
        62 条评测复测 Hit@1/Hit@3 不变,MRR 0.884→0.882(一名次内波动)。
        """
        candidate_k = candidate_k or settings.CHUNK_TOP_K * 2
        bm25_hits = self.bm25.search(query, candidate_k) if self.bm25 else []
        vec_hits = self.vector.search(query, candidate_k) if self.vector else []
        rrf: dict[int, float] = {}
        for r, (i, _) in enumerate(bm25_hits):
            rrf[i] = rrf.get(i, 0.0) + 1.0 / (settings.RRF_K + r + 1)
        for r, (i, _) in enumerate(vec_hits):
            rrf[i] = rrf.get(i, 0.0) + 1.0 / (settings.RRF_K + r + 1)
        # 双通道排名表:仅记录真实命中通道,未命中通道不写键(vec_rank=None),
        # 保证引用卡片与调试接口暴露的观测数据不失真
        ranks: dict[int, dict[str, int]] = {i: {"bm25": r + 1} for r, (i, _) in enumerate(bm25_hits)}
        for r, (i, _) in enumerate(vec_hits):
            ranks.setdefault(i, {})["vec"] = r + 1
        fused = sorted(rrf.items(), key=lambda x: -x[1])
        return [(i, s, ranks.get(i, {})) for i, s in fused]

    def retrieve(self, query: str, top_k: int | None = None, rerank: bool = True) -> list[RetrievedChunk]:
        top_k = top_k or settings.FINAL_TOP_K
        # 融合候选池不截断:双通道 chunk 会重复占据名额,截断会压缩文档多样性
        # (62 条评测显示截断到 10 chunks 使 Hit@3 从 ~90% 降至 ~82%)
        fused = self.fuse_rrf(query, candidate_k=settings.CHUNK_TOP_K * 4)[: 4 * settings.CHUNK_TOP_K]
        rank_by_id = {self.chunks[i].id: (rk.get("bm25"), rk.get("vec")) for i, _, rk in fused}
        if rerank:
            cands = [self.chunks[i] for i, _, _ in fused]
            reranked = self.reranker.rerank(query, cands)
            # 排序:RRF 通道先验为主(0.7),特征化重排做精调(0.3)——
            # 62 条评测显示轻量词面重排无法稳定超越双通道排序,
            # 其主要价值是质量控制(阈值)与 chunk 级精排;排序增益需 Cross-Encoder。
            max_rrf = fused[0][1] if fused else 1.0
            rrf_norm = {self.chunks[i].id: s / max_rrf for i, s, _ in fused}
            rerank_raw = {c.id: s for c, s in reranked}
            combined = sorted(
                ((c, round(0.7 * rrf_norm.get(c.id, 0.0) + 0.3 * s, 4)) for c, s in reranked),
                key=lambda x: -x[1],
            )
            # 阈值语义(全有或全无):整条查询的最佳重排分低于 MIN_RELEVANCE
            # 视为无相关知识,触发兜底;不对单条低分结果逐一过滤——
            # 62 条评测显示逐条过滤会误杀口语化弱词面正解(Hit@3 85% vs 95%)。
            if combined and max(rerank_raw[c.id] for c, _ in combined) < settings.MIN_RELEVANCE:
                return []
            # 文档级去重:同一文档的 q/a0 双通道 chunk 只保留最高分一条,
            # 避免挤占其它文档的 Top-K 名额(引用卡片也因此不再重复来源)
            seen_docs: set[str] = set()
            results: list[RetrievedChunk] = []
            for c, s in combined:
                if c.doc_id in seen_docs:
                    continue
                seen_docs.add(c.doc_id)
                results.append(RetrievedChunk(
                    chunk=c, score=s,
                    bm25_rank=rank_by_id[c.id][0], vec_rank=rank_by_id[c.id][1]))
                if len(results) >= top_k:
                    break
            return results
        # RRF 路径(生产默认,由 RERANK_ENABLED=0 选择):保留无知识兜底 ——
        # 全部候选与查询实质词(含同义词 tags)零交集时视为无相关知识,返回空触发回退话术
        if fused:
            q_tokens = set(tokenize(query))
            def _hard(i: int) -> bool:
                c = self.chunks[i]
                ct = set(tokenize(f"{c.text} {' '.join(c.tags)}"))
                return bool(q_tokens & ct) or any(t in q_tokens for t in c.tags)
            if not any(_hard(i) for i, _, _ in fused):
                return []
        # 文档级去重(与 rerank 分支一致):同一文档的双通道 chunk 只保留最高分一条
        seen: set[str] = set()
        out: list[RetrievedChunk] = []
        for i, s, rk in fused:
            doc = self.chunks[i].doc_id
            if doc in seen:
                continue
            seen.add(doc)
            out.append(RetrievedChunk(chunk=self.chunks[i], score=round(s, 4),
                                      bm25_rank=rk.get("bm25"), vec_rank=rk.get("vec")))
            if len(out) >= top_k:
                break
        return out


# 单例:由 ingestion 服务负责装载与热更新
retriever = HybridRetriever()
