# 复现指南(REPRODUCIBILITY)

> 本文档覆盖 CampusMind 全部实验与验收的复现方法。所有数字为 2026-09-18 FINAL 实测,评测口径见 §6。

## 1. 环境

| 项 | 值 |
|---|---|
| OS | macOS(darwin 25.6.0, arm64);代码无平台专属依赖,Linux 可复现 |
| Python | 3.14.7(要求 ≥3.10) |
| 依赖 | `python3 -m venv .venv && .venv/bin/pip install -r backend/requirements.txt`(fastapi/uvicorn/jieba/httpx/pytest) |
| API Key | **不需要**。无 Key 时 LLM=local(本地抽取式生成)、向量=local-tfidf(TF-IDF 词袋) |

**TF-IDF 声明**:演示/复现环境的稠密向量通道为 TF-IDF 加权词袋,**不是深度语义 embedding**;云端语义向量 Provider(智谱 embedding-3)代码已实现,设置 `ZHIPUAI_API_KEY`(可选 `EMBEDDING_PROVIDER=zhipu`)后自动启用。重排默认关闭(`RERANK_ENABLED=0`,置 1 开启)。

## 2. 启动

```bash
cd backend && ../.venv/bin/python -m uvicorn app.main:app --port 8000
# http://127.0.0.1:8000 顶栏显示 LLM/向量 Provider 与索引版本
```

## 3. 检索评测(62 条口语化改写 × 四路)

```bash
.venv/bin/python scripts/eval_matrix.py
```

预期结果范围(文档级统一去重口径):

| 链路 | Hit@1 | Hit@3 | MRR |
|---|---|---|---|
| BM25-only | 80.6% | 98.4% | 0.884 |
| Vector-only(TF-IDF) | 75.8% | 93.5% | 0.844 |
| Hybrid+RRF(生产默认) | 80.6% | 98.4% | 0.884 |
| Hybrid+Rerank(可选开关) | 74.2% | 90.3% | 0.815 |

允许 ±1.6pp(Hit@1 一个名次)的运行间波动;评测数据集规模 = **62 条 evaluation queries**,语料 59 篇 / 136 chunks。

## 4. 性能基准

```bash
.venv/bin/python scripts/bench.py retrieval   # 进程内检索链路
.venv/bin/python scripts/bench.py e2e         # 需先启动服务(§2)
```

预期(默认 Hybrid+RRF 链路,单机):retrieval-only ≈ 250 QPS / p95 < 10ms;E2E(含本地抽取式生成+落库,并发 20)≈ 44 QPS / p99 < 700ms;两者失败数 = 0。机器性能不同会整体浮动,分位数比例应稳定。

## 5. 架构验收

```bash
.venv/bin/python scripts/acceptance.py   # 需先启动服务(§2)
```

预期:**4/4 PASS** —— A1 生成降级(无效 Key 流内回退本地抽取式)、A2 限流(单用户并发 15 → 200×10 + 429×5)、A3 热更新(索引版本递增、新增知识立即可检索、完成后自动清理)、A4 无知识兜底(sources=0、不编造)。

## 6. 评测口径备注

- 评估单位为文档级:chunk 命中按 doc_id 去重保序;四条链路口径一致。
- Hybrid+RRF 直接消费 `fuse_rrf` 原始融合输出(每通道 top-20 chunks 取前 10 再按文档去重);生产 `retrieve(rerank=False)` 内部的文档级去重与无知识硬零兜底不参与评测。
- 早期版本 RRF 口径存在同文档重复占位失真(旧值 Hit@3 95.2),FINAL 统一口径后为 98.4,以当前为准。
