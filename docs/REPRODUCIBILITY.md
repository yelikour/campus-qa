# 复现指南(REPRODUCIBILITY)

> 本文档覆盖 CampusMind 全部实验与验收的复现方法。2026-09-18 FINAL 为原始交付实测;2026-10-16 完善轮(见 IMPROVEMENTS.md)修正 RRF 公式后复测,评测口径见 §6。

## 1. 环境

| 项 | 值 |
|---|---|
| OS | macOS(darwin 25.6.0, arm64,2026-09-18 FINAL);Windows 11 x64(2026-10-16 完善轮复测);代码无平台专属依赖,Linux 可复现 |
| Python | 3.14.7 / 3.12.10(要求 ≥3.10) |
| 依赖 | `python -m venv .venv && .venv/Scripts/pip install -r backend/requirements.txt`(fastapi/uvicorn/jieba/httpx/pytest;Windows 用 `.venv/Scripts/`,macOS/Linux 用 `.venv/bin/`) |
| API Key | **不需要**。无 Key 时 LLM=local(本地抽取式生成)、向量=local-tfidf(TF-IDF 词袋) |
| ADMIN_TOKEN | 可选。设置后知识库写接口(POST/DELETE /api/knowledge)强制校验 `X-Admin-Token`;不设置 = 演示开放模式(启动日志有提示) |

**TF-IDF 声明**:演示/复现环境的稠密向量通道为 TF-IDF 加权词袋,**不是深度语义 embedding**;云端语义向量 Provider(智谱 embedding-3)代码已实现,设置 `ZHIPUAI_API_KEY`(可选 `EMBEDDING_PROVIDER=zhipu`)后自动启用。重排默认关闭(`RERANK_ENABLED=0`,置 1 开启)。

## 2. 启动

```bash
cd backend && ../.venv/bin/python -m uvicorn app.main:app --port 8000
# http://127.0.0.1:8000 顶栏显示 LLM/向量 Provider 与索引版本
```

## 3. 检索评测(62 条口语化改写 × 四路)

```bash
.venv/Scripts/python scripts/eval_matrix.py    # Windows
.venv/bin/python scripts/eval_matrix.py        # macOS / Linux
```

预期结果范围(文档级统一去重口径,2026-10-16 完善轮复测):

| 链路 | Hit@1 | Hit@3 | MRR |
|---|---|---|---|
| BM25-only | 80.6% | 98.4% | 0.884 |
| Vector-only(TF-IDF) | 75.8% | 93.5% | 0.844 |
| Hybrid+RRF(生产默认) | 80.6% | 98.4% | 0.882 |
| Hybrid+Rerank(可选开关) | 77.4% | 96.8% | 0.860 |

允许 ±1.6pp(Hit@1 一个名次)的运行间波动;评测数据集规模 = **62 条 evaluation queries**,语料 59 篇 / 136 chunks。2026-09-18 FINAL 历史值:Hybrid+RRF MRR 0.884、Hybrid+Rerank 74.2/90.3/0.815(RRF 公式修正前的常数权重融合,见 IMPROVEMENTS.md §1)。

## 4. 性能基准

```bash
.venv/bin/python scripts/bench.py retrieval   # 进程内检索链路
.venv/bin/python scripts/bench.py e2e         # 需先启动服务(§2)
```

预期(单机):retrieval-only 按 `RERANK_ENABLED` 决定的链路测量(输出标签含 `(RRF)`/`(rerank)`,2026-10-16 修正口径):RRF 生产路径 515.8–880.4 QPS / p50 1.1–1.9ms(Win/x64 两次实测,负载波动);2026-09-18 的 251.4 QPS(p95 7.0ms)为修正前口径(误测重排路径,macOS/arm64)。E2E(含本地抽取式生成+落库,并发 20)≈ 42–44 QPS / p99 < 800ms;失败数 = 0。机器性能不同会整体浮动,分位数比例应稳定。

BM25 通道 A/B 对照(完善轮,Windows/x64,同进程三轮取最好):倒排索引化后当前语料 2,145 → 21,505 QPS(10.0×),20× 语料(2,720 chunks)68 → 2,587 QPS(35×);全链路 `retrieve()` 持平(瓶颈在分词与编排)。倒排结果与原暴力扫描逐查询、逐位等价(`backend/tests/test_improvements.py` 校验)。

## 5. 架构验收

```bash
.venv/bin/python scripts/acceptance.py   # 需先启动服务(§2)
```

预期:**4/4 PASS** —— A1 生成降级(无效 Key 流内回退本地抽取式)、A2 限流(单用户并发 15 → 200×10 + 429×5)、A3 热更新(索引版本递增、新增知识立即可检索、完成后自动清理)、A4 无知识兜底(sources=0、不编造)。

## 6. 评测口径备注

- 评估单位为文档级:chunk 命中按 doc_id 去重保序;四条链路口径一致。
- Hybrid+RRF 直接消费 `fuse_rrf` 原始融合输出(每通道 top-20 chunks 取前 10 再按文档去重);生产 `retrieve(rerank=False)` 内部的文档级去重与无知识硬零兜底不参与评测。
- 早期版本 RRF 口径存在同文档重复占位失真(旧值 Hit@3 95.2),FINAL 统一口径后为 98.4,以当前为准。
- 2026-10-16 完善轮:`fuse_rrf` 由常数权重 `1/(RRF_K+1)` 修正为标准 RRF `Σ 1/(k+rank)`;融合分语义变化,Hit@1/Hit@3 不变、MRR 0.884→0.882、Rerank 路径 74.2/90.3→77.4/96.8。

## 7. 单元测试

```bash
.venv/Scripts/python -m pytest backend/tests/ -q    # Windows
.venv/bin/python -m pytest backend/tests/ -q        # macOS / Linux
```

预期:**13 passed**(test_smoke.py 4 项发布冒烟 + test_improvements.py 9 项完善轮:RRF 公式正确性、vec_rank 不伪造、BM25 倒排等价性、ADMIN_TOKEN 鉴权门禁、演示开放模式兼容、令牌桶淘汰、知识删除语义、降级日志可归因)。
