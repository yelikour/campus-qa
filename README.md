# 智问校园 CampusMind —— 校园智能问答系统(AI + RAG)

《软件体系结构》课程项目 · 2026 春季学期 · 3 人团队（王若璋 · 何俐 · 郭祚梁） · 8 周交付

面向在校学生的校园事务智能问答系统:自然语言提问 → **混合检索**(BM25 ∥ 向量)→ **RRF 融合** → **重排序** → **流式生成**(SSE)→ **引用溯源**。所有回答均标注校内知识来源,无命中时诚实回退、不编造。

> **向量通道如实说明**:演示环境稠密通道为 **TF-IDF 加权词袋(非语义嵌入)**;云端语义向量 Provider(智谱 embedding-3)已实现,配置 `ZHIPUAI_API_KEY` 即启用,接口不变;前端与统计接口实时显示当前 Provider 与索引版本。

## 目录结构

```
campus-qa/
├── backend/            # FastAPI 后端(app/api · services · repository · core 分层)
│   ├── app/data/campus_qa.json   # 校园知识语料(含验收演示条目)
│   └── requirements.txt
├── frontend/           # 原生 SPA(聊天 / 知识库管理 / 运行看板;顶栏与侧栏显示引擎信息)
├── scripts/
│   ├── ask.py            # 命令行 SSE 问答验证
│   ├── eval_matrix.py    # 检索评测:62 条口语化改写 × 四路链路对比
│   ├── bench.py          # 性能拆分:retrieval-only / E2E(p50/p95/p99/QPS/失败数)
│   ├── acceptance.py     # 四项架构验收(降级/限流/热更新/无知识兜底)
│   └── gen_diagrams.py   # 架构图生成
├── docs/
│   ├── 智问校园CampusMind架构设计文档.docx/.pdf   # 交付物一(22 页,含追踪矩阵章)
│   ├── 智问校园CampusMind经济适用型与运营方案.docx/.pdf  # 售卖模式/成本核算/高并发/反向代理(2026-10 增补)
│   ├── traceability.md    # 需求→质量属性→ADR→模块→测试→证据 追踪矩阵
│   ├── IMPROVEMENTS.md    # 2026-10-16 完善轮调研报告:缺陷清单、修复与验证证据
│   └── assets/            # 分层架构 / RAG 时序 / 部署演进图
├── ppt/智问校园CampusMind答辩PPT.pptx              # 交付物二(21 页,含经济适用型三页与讲者备注;字体微软雅黑,Windows/Office 跨平台标配)
├── video/
│   ├── demo_frontend_v2.webm                 # 前端演示录屏(60s,含引擎信息与热更新闭环)
│   ├── 智问校园CampusMind答辩讲解视频.mp4      # 完整讲解视频(16:18,21 页+演示+TTS)
│   └── narration.py / build_video.sh          # 旁白文案与合成脚本(TTS: macOS Tingting)
└── .build/             # 文档/幻灯片构建脚本(generate_doc.js / build_ppt.js)
```

## 快速开始

```bash
cd campus-qa
python3 -m venv .venv && .venv/bin/pip install -r backend/requirements.txt
cd backend && ../.venv/bin/python -m uvicorn app.main:app --port 8000
# 打开 http://127.0.0.1:8000(顶栏显示 LLM/向量 Provider 与索引版本)
```

**云端 LLM / 语义向量(可选)**:默认零依赖离线运行;设置 `ZHIPUAI_API_KEY`(可选 `LLM_PROVIDER=zhipu`、`EMBEDDING_PROVIDER=zhipu`)后重启,生成切智谱 GLM 流式、向量切 embedding-3;云端异常自动熔断降级到本地。

**知识库写接口鉴权(可选)**:默认演示开放模式;设置 `ADMIN_TOKEN` 后,`POST/DELETE /api/knowledge` 强制校验 `X-Admin-Token` 请求头(前端管理页会提示输入),防止未授权增删知识库。

**证据脚本(全部可复现)**:

```bash
.venv/bin/python scripts/eval_matrix.py      # 四路:BM25 / Vector(TF-IDF) / Hybrid+RRF / Hybrid+Rerank
.venv/bin/python scripts/bench.py retrieval  # 251.4 QPS, p95 7.0ms
.venv/bin/python scripts/bench.py e2e        # 44.1 QPS(含生成), p99 611ms, 0 失败
.venv/bin/python scripts/acceptance.py       # 四项验收 4/4 PASS
```

## 实测指标

### 检索评测矩阵(n=62 口语化同义改写,四路统一文档级去重口径)

2026-09-18 FINAL 实测;2026-10-16 完善轮(RRF 公式修正后)复测,指标如下:

| 链路 | Hit@1 | Hit@3 | MRR |
|---|---|---|---|
| BM25-only | 80.6% | 98.4% | 0.884 |
| Vector-only(TF-IDF,非语义嵌入) | 75.8% | 93.5% | 0.844 |
| **Hybrid+RRF(生产默认)** | **80.6%** | **98.4%** | **0.882** |
| Hybrid+Rerank(可选实验开关,默认关) | 77.4% | 96.8% | 0.860 |

结论(如实):在当前 62 条校园事务评测集上,BM25 对关键词密集型规章问题表现最好;TF-IDF 向量补充了另一种检索视角,但并未稳定超过 BM25;轻量词面 Reranker 实测无收益,保持 Provider 化设计并默认关闭(`RERANK_ENABLED=1` 可开启),计划替换为 Cross-Encoder 后再次评估。评测驱动修复三个真实缺陷(停用词表构造 bug / RRF 候选池截断 / 缺文档级去重);早期 RRF 口径存在同文档重复占位失真(旧值 95.2),统一口径后为 98.4。

2026-10-16 完善轮修正:原 `fuse_rrf` 误用常数 `1/(RRF_K+1)`(与排名无关,等价于通道计数),已改为标准 RRF 公式 `Σ 1/(k+rank)`。TF-IDF 演示语料上双通道高度相关,Hit@1/Hit@3 不变,MRR 0.884→0.882(一名次内波动);附带收益是 Rerank 路径的 RRF 先验更有效(74.2/90.3 → 77.4/96.8)。接入真实语义向量后双通道分歧增大,标准公式才是正确行为(详见 [docs/IMPROVEMENTS.md](docs/IMPROVEMENTS.md))。

### 性能基准(拆分,默认 Hybrid+RRF 链路)

| 基准 | 样本 | QPS | p50 | p95 | p99 | 失败 |
|---|---|---|---|---|---|---|
| retrieval-only·RRF 链路(2026-10-16 修正口径,Win/x64,两次实测) | 300 | 515.8–880.4 | 1.1–1.9ms | 1.8–3.2ms | 2.1–3.7ms | 0 |
| retrieval-only·重排路径(2026-09-18,macOS/arm64,修正前口径) | 300 | 251.4 | 3.4ms | 7.0ms | 7.2ms | 0 |
| local-extractive E2E 并发 20(2026-09-18,macOS/arm64) | 200 | 44.1 | 415.7ms | 601.0ms | 611.1ms | 0 |
| local-extractive E2E 并发 20(2026-10-16 复测,Win/x64) | 200 | 42.1–43.3 | 413.3ms | 627.6ms | 727.1–761.2ms | 0 |

口径说明:2026-09-18 的 retrieval-only 251.4 QPS 实测的是重排实验路径(bench.py 当时误用 `retrieve` 默认 rerank=True,与"默认链路"宣称不符);2026-10-16 修正后按生产 `RERANK_ENABLED=0` 的 RRF 路径测量,吞吐显著更高。历史对照:Rerank 默认时期 217.8 QPS / p95 8.7ms(E2E 42.0 QPS / p99 683ms);初版链路 E2E 67.8 QPS。复现方法见 [docs/REPRODUCIBILITY.md](docs/REPRODUCIBILITY.md)。

2026-10-16 完善轮 BM25 通道优化:查询从逐文档全量扫描(O(词数×N×文档长))改为倒排索引 + 预计算词频。同进程 A/B 对照(Windows/x64,三轮取最好):当前语料 BM25-only 2,145 → 21,505 QPS(10.0×);20 倍语料(2,720 chunks)68 → 2,587 QPS(35×,复杂度随语料的扩展性显著改善);全链路 `retrieve()` 27 QPS 持平(瓶颈在分词与融合编排,无回归)。倒排实现与原暴力算法逐查询、逐位等价(单元测试校验)。

### 架构验收(4/4 PASS)

A1 生成降级(无效 Key 流内回退)· A2 入口限流(并发 15 → 200×10+429×5)· A3 知识热更新(录入即命中,版本递增,验后清理)· A4 无知识兜底(sources=0,不编造)。完整追踪见 [docs/traceability.md](docs/traceability.md)。

## 架构要点

- **五层分层**:接入 → 网关边界 → 应用服务 → RAG 引擎 → 数据;模块化单体起步,预留服务化边界(ADR-1)。
- **双端可插拔 Provider**:Generator(本地抽取式/云端 GLM)与 Embedding(TF-IDF/云端 embedding-3)同类插件化,无 Key 自动回退并如实显示(ADR-4/ADR-7)。
- **可观察检索**:引用卡片与调试接口暴露双通道排名与融合分数(仅记录真实命中通道,不伪造排名);前端显示引擎信息与索引版本。
- **默认链路 Hybrid+RRF**:标准 RRF 公式 `Σ 1/(k+rank)` 对排名融合;轻量 Reranker 实测无收益,降级为可配置实验开关(RERANK_ENABLED,默认 0),RRF 路径内置无知识硬零兜底与文档级去重。
- **安全防线**:令牌桶限流(桶字典有界,防伪造 token 内存泄漏)· 生成端熔断降级(带归因日志)· 强制引用溯源 + 全有或全无兜底门槛 · 知识库写接口可选 ADMIN_TOKEN 鉴权 + 前端输出全量转义(防存储型 XSS)。

## 2026-10-16 完善轮(二轮调研加固)

对交付版做独立代码调研,修复 9 项缺陷并全部验证(完整报告与证据见 [docs/IMPROVEMENTS.md](docs/IMPROVEMENTS.md)):

- **检索正确性**:`fuse_rrf` 常数权重 → 标准 RRF(指标持平,Rerank 路径 +3.2pp/+6.5pp);引用卡片 vec_rank 不再伪造 bm25 排名。
- **性能**:BM25 倒排索引化,当前语料 10×、20× 语料 35×,与原算法逐位等价。
- **安全**:前端三处未转义输出(存储型 XSS 链)修复;知识库写接口可选 `ADMIN_TOKEN` 鉴权;令牌桶字典有界化。
- **健壮性**:知识删除与新增共用文件锁(消除读写竞态);云端生成降级输出归因日志。
- **测试**:新增 9 项单元测试(RRF 公式/等价性/鉴权/桶淘汰/删除语义/降级日志),全量 13/13 通过;四项架构验收复测 4/4 PASS。
- **评测口径**:bench.py retrieval 基准误测重排实验路径(`retrieve` 默认 rerank=True),已修正为跟随 `RERANK_ENABLED` 并标注实际链路——修正后 RRF 生产路径实测 515.8–880.4 QPS / p50 1.1–1.9ms(Win/x64 两次实测),原 251.4 QPS 实为重排路径数值。

## 经济适用型与运营(2026-10 增补)

围绕「怎么卖、成本多少、怎么扛并发」三个问题给出可查证的答案(完整测算见《经济适用型与运营方案》):

- **售卖三档**:SaaS 订阅(¥4,999/校/年,定价假设示例)· 私有化买断(数据不出校,复用校内虚机)· 免费社区版(本项目形态,零 API 成本获客)。
- **月账单(全按真实收费价,不依赖免费活动)**:云端托管 ≈¥210–230/月(2C4G 轻量 + 按量 API:保守档 ¥1/百万 token × 日均 5,000 问 ≈¥195/月;Flash 历史挂牌价 ¥0.06–0.1/百万 档仅 ≈¥12–20/月);私有化复用校内虚机边际 ≈¥0;全离线 GPU ≈¥1,000–1,500/月(仅数据最敏感场景)。每问 ≈1.3k token(代码估算),本地抽取式兜底内置 ¥0,成本有硬上限。
- **高并发**:单实例 E2E 44.1 QPS(0 失败)对万人在校场景余量 10×+;扩展三级(uvicorn workers → Nginx 反代多实例 → 限流外置 Redis),扩容单位 ≈¥30/月/台,容量-成本线性挂钩。
- **反向代理要点**:Nginx `proxy_buffering off` 保 SSE 直通、`proxy_read_timeout ≥ 60s`、静态资源直出、TLS 终止、limit_req + 应用令牌桶双层限流。

口径如实:大模型调用成本一律按真实收费价核算,不依赖任何限时免费活动(现行免费活动未计入);外部价格为 2026-10 查询的公开活动价(标注波动与续费风险,以官方页面为准);商业定价为假设示例,非承诺。

详见《架构设计文档》第 4–11 章。
