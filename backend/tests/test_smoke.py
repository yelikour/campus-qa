"""发布冒烟测试:导入、索引构建、四路检索可用性与兜底行为。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import settings          # noqa: E402
from app.services import ingestion       # noqa: E402
from app.services.retrieval import retriever, get_embedder  # noqa: E402


def test_index_build():
    n = ingestion.startup()
    assert n > 100, "索引 chunk 数异常"
    assert retriever.version >= 1


def test_default_route_is_rrf_without_key():
    assert settings.RERANK_ENABLED is False, "默认应关闭重排(实测无收益)"
    assert get_embedder().name == "local-tfidf", "无 Key 环境向量通道应为 TF-IDF"


def test_rrf_route_hit_and_dedup():
    results = retriever.retrieve("图书馆开放时间", rerank=False)
    assert results, "正常查询应有命中"
    docs = [r.chunk.doc_id for r in results]
    assert len(docs) == len(set(docs)), "RRF 路径输出应文档级去重"


def test_no_knowledge_fallback():
    for q in ["今天股票行情怎么样", "帮我写一首诗"]:
        assert retriever.retrieve(q, rerank=False) == [], f"{q} 应回退兜底"
        assert retriever.retrieve(q, rerank=True) == [], f"{q}(重排开启)也应回退兜底"
