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

**证据脚本(全部可复现)**:

```bash
.venv/bin/python scripts/eval_matrix.py      # 四路:BM25 / Vector(TF-IDF) / Hybrid+RRF / Hybrid+Rerank
.venv/bin/python scripts/bench.py retrieval  # 251.4 QPS, p95 7.0ms
.venv/bin/python scripts/bench.py e2e        # 44.1 QPS(含生成), p99 611ms, 0 失败
.venv/bin/python scripts/acceptance.py       # 四项验收 4/4 PASS
```

## 实测指标(2026-09-18)

### 检索评测矩阵(n=62 口语化同义改写,四路统一文档级去重口径)

| 链路 | Hit@1 | Hit@3 | MRR |
|---|---|---|---|
| BM25-only | 80.6% | 98.4% | 0.884 |
| Vector-only(TF-IDF,非语义嵌入) | 75.8% | 93.5% | 0.844 |
| **Hybrid+RRF(生产默认)** | **80.6%** | **98.4%** | **0.884** |
| Hybrid+Rerank(可选实验开关,默认关) | 74.2% | 90.3% | 0.815 |

结论(如实):在当前 62 条校园事务评测集上,BM25 对关键词密集型规章问题表现最好;TF-IDF 向量补充了另一种检索视角,但并未稳定超过 BM25;轻量词面 Reranker 实测无收益,保持 Provider 化设计并默认关闭(`RERANK_ENABLED=1` 可开启),计划替换为 Cross-Encoder 后再次评估。评测驱动修复三个真实缺陷(停用词表构造 bug / RRF 候选池截断 / 缺文档级去重);早期 RRF 口径存在同文档重复占位失真(旧值 95.2),统一口径后为 98.4。

### 性能基准(拆分,默认 Hybrid+RRF 链路)

| 基准 | 样本 | QPS | p50 | p95 | p99 | 失败 |
|---|---|---|---|---|---|---|
| retrieval-only | 300 | 251.4 | 3.4ms | 7.0ms | 7.2ms | 0 |
| local-extractive E2E(并发 20) | 200 | 44.1 | 415.7ms | 601.0ms | 611.1ms | 0 |

历史对照:Rerank 默认时期 217.8 QPS / p95 8.7ms(E2E 42.0 QPS / p99 683ms);初版链路 E2E 67.8 QPS。复现方法见 [docs/REPRODUCIBILITY.md](docs/REPRODUCIBILITY.md)。

### 架构验收(4/4 PASS)

A1 生成降级(无效 Key 流内回退)· A2 入口限流(并发 15 → 200×10+429×5)· A3 知识热更新(录入即命中,版本递增,验后清理)· A4 无知识兜底(sources=0,不编造)。完整追踪见 [docs/traceability.md](docs/traceability.md)。

## 架构要点

- **五层分层**:接入 → 网关边界 → 应用服务 → RAG 引擎 → 数据;模块化单体起步,预留服务化边界(ADR-1)。
- **双端可插拔 Provider**:Generator(本地抽取式/云端 GLM)与 Embedding(TF-IDF/云端 embedding-3)同类插件化,无 Key 自动回退并如实显示(ADR-4/ADR-7)。
- **可观察检索**:引用卡片与调试接口暴露双通道排名与融合分数;前端显示引擎信息与索引版本。
- **默认链路 Hybrid+RRF**:轻量 Reranker 实测无收益,降级为可配置实验开关(RERANK_ENABLED,默认 0),RRF 路径内置无知识硬零兜底与文档级去重。
- **安全三防线**:令牌桶限流 · 生成端熔断降级 · 强制引用溯源 + 全有或全无兜底门槛。

## 经济适用型与运营(2026-10 增补)

围绕「怎么卖、成本多少、怎么扛并发」三个问题给出可查证的答案(完整测算见《经济适用型与运营方案》):

- **售卖三档**:SaaS 订阅(¥4,999/校/年,定价假设示例)· 私有化买断(数据不出校,复用校内虚机)· 免费社区版(本项目形态,零 API 成本获客)。
- **月账单(全按真实收费价,不依赖免费活动)**:云端托管 ≈¥210–230/月(2C4G 轻量 + 按量 API:保守档 ¥1/百万 token × 日均 5,000 问 ≈¥195/月;Flash 历史挂牌价 ¥0.06–0.1/百万 档仅 ≈¥12–20/月);私有化复用校内虚机边际 ≈¥0;全离线 GPU ≈¥1,000–1,500/月(仅数据最敏感场景)。每问 ≈1.3k token(代码估算),本地抽取式兜底内置 ¥0,成本有硬上限。
- **高并发**:单实例 E2E 44.1 QPS(0 失败)对万人在校场景余量 10×+;扩展三级(uvicorn workers → Nginx 反代多实例 → 限流外置 Redis),扩容单位 ≈¥30/月/台,容量-成本线性挂钩。
- **反向代理要点**:Nginx `proxy_buffering off` 保 SSE 直通、`proxy_read_timeout ≥ 60s`、静态资源直出、TLS 终止、limit_req + 应用令牌桶双层限流。

口径如实:大模型调用成本一律按真实收费价核算,不依赖任何限时免费活动(现行免费活动未计入);外部价格为 2026-10 查询的公开活动价(标注波动与续费风险,以官方页面为准);商业定价为假设示例,非承诺。

详见《架构设计文档》第 4–11 章。
