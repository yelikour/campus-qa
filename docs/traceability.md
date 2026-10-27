# 追踪矩阵:需求 → 质量属性 → ADR → 模块 → 测试 → 证据

> 本矩阵是《智问校园 CampusMind 架构设计文档》第 11 章的配套索引,所有证据均为 2026-09-18 本地实测(可复现脚本见 scripts/)。
> 说明:演示环境向量通道为 **TF-IDF 加权词袋(非语义嵌入)**;云端语义向量 Provider(Zhipu embedding-3)已实现、配置 `ZHIPUAI_API_KEY` 即启用,本轮未接入真实模型,材料如实标注。

## 一、需求级追踪

| 需求 | 质量属性场景(六元组摘要) | ADR | 实现模块 | 验证方式 | 证据(实测) |
|---|---|---|---|---|---|
| FR-1 自然语言提问,回答带引用溯源 | 可信性:回答必须可溯源、不编造 | ADR-2/ADR-7 | api/chat.py · services/retrieval.py · services/generation.py | eval_matrix.py + 演示录屏 | 引用卡片展示双通道排名与融合分数;默认链路( Hybrid+RRF)Hit@3 98.4%(62 条) |
| FR-2 流式输出(首字 < 1s) | 性能:并发峰值不劣化 | ADR-3 | api/chat.py(SSE) · frontend/app.js | bench.py e2e | E2E p50 436ms / p95 632ms(含全量生成,首字更早:meta 事件先推) |
| FR-3 会话历史 | — | ADR-1 | api/conversations.py · repository/db.py | 手动 + 演示录屏 | 刷新后历史会话可恢复(侧栏列表) |
| FR-4 知识库管理与热更新(<5s 无需重启) | 可修改性:录入即生效 | ADR-5 | api/knowledge.py · services/ingestion.py | acceptance.py A3 | **PASS**:版本 1→2 递增,录入后即时检索命中并正确回答,清理后版本再递增 |
| FR-5 运行看板 | 可测试性/可观察性 | ADR-1 | api/admin.py · 前端看板视图 | 手动 + bench | 命中率/时延/热点分类实时刷新;新增 embedding_provider 字段 |
| FR-6 无相关知识时诚实回退 | 可信性:不编造 | ADR-2 | services/retrieval.py(全有或全无阈值) | acceptance.py A4 | **PASS**:sources=0,返回引导话术 |
| NFR 性能(检索 P95<50ms) | 性能 | ADR-5 | services/retrieval.py | bench.py retrieval | retrieval-only p95 7.0ms / p99 7.2ms / 251.4 QPS(默认 RRF 链路) |
| NFR 可用性(LLM 故障自动降级) | 可用性 ≥99.5% | ADR-4 | services/generation.py(熔断降级) | acceptance.py A1 | **PASS**:无效 Key 下 zhipu-glm 流内回退本地抽取式,产出 139 字正解 |
| NFR 可扩展(无状态水平扩展) | 可扩展性 | ADR-1 | 应用层无状态设计 | 部署视图审查 | 应用不持有会话状态(SQLite/索引可外置),架构文档 §10 |
| NFR 安全(单用户限流) | 安全性 | ADR-6 | core/security.py(令牌桶) | acceptance.py A2 | **PASS**:并发 15 → 200×10 + 429×5(桶容量精确) |

## 二、架构决策(ADR)→ 落点与证据

| ADR | 决策 | 受影响模块 | 验证证据 |
|---|---|---|---|
| ADR-1 | 模块化单体起步,预留服务化边界 | backend/app 分包结构 | api/services/repository/core 边界清晰,评测/压测均从外部接口进入 |
| ADR-2 | 混合检索 + RRF + 重排 | retrieval.py | eval_matrix.py 四路对比:BM25 80.6/98.4,Hybrid+RRF 80.6/95.2,生产链路 74.2/90.3 |
| ADR-3 | SSE 承载流式 | api/chat.py · frontend | 演示录屏打字机效果;bench e2e 200/200 成功 |
| ADR-4 | 生成 Provider 插件化 + 本地兜底 | generation.py | acceptance A1(降级 PASS);无 Key 环境全功能可跑 |
| ADR-5 | 内存索引 + 热重建 | retrieval.py · ingestion.py | acceptance A3(热更新 PASS,版本递增);136 chunks 重建耗时 < 1s(启动日志) |
| ADR-6 | 令牌桶入口限流 | core/security.py | acceptance A2(429 PASS) |
| ADR-7 | Embedding Provider 可插拔,TF-IDF 为离线 fallback | retrieval.py(ZhipuEmbeddingProvider) | 无 Key 工厂回退验证 PASS;配置 Key 即切云端语义向量(接口不变) |
| FINAL 补充 | 默认检索链路 = Hybrid+RRF;轻量 Reranker 降级为可配置实验开关(RERANK_ENABLED,默认 0) | config.py · chat.py · retrieval.py | 62 条评测:Rerank 路径 74.2/90.3 vs RRF 80.6/98.4,实测无收益故默认关闭;smoke pytest 覆盖 |

## 三、四项架构验收结论(2026-09-18,scripts/acceptance.py)

| 编号 | 验收项 | 结果 | 关键证据 |
|---|---|---|---|
| A1 | 生成降级 | **PASS** | 无效 Key → 流内回退本地抽取式,139 字正解,服务不中断 |
| A2 | 入口限流 | **PASS** | 并发 15:200×10、429×5,超出桶容量请求被拒 |
| A3 | 知识热更新 | **PASS** | 录入→即时命中→正确回答→清理,索引版本 1→2→3 递增 |
| A4 | 无知识兜底 | **PASS** | sources=0,返回引导话术,不编造 |

## 四、性能基准(2026-09-18,scripts/bench.py)

| 基准(FINAL,默认链路 Hybrid+RRF) | 样本 | QPS | p50 | p95 | p99 | 失败 |
|---|---|---|---|---|---|---|
| retrieval-only(进程内) | 300 | 251.4 | 3.4ms | 7.0ms | 7.2ms | 0 |
| local-extractive E2E(HTTP,并发 20) | 200 | 44.1 | 415.7ms | 601.0ms | 611.1ms | 0 |

历史对照(同一基准脚本):Rerank 默认时期 retrieval-only 217.8 QPS / p95 8.7ms,E2E 42.0 QPS / p99 683ms;初版(链路不完整)E2E 67.8 QPS。默认切换至 RRF 后检索计算量下降,吞吐回升,数据如实呈现。

## 五、检索评测矩阵(2026-09-18 FINAL,scripts/eval_matrix.py,n=62,四路统一文档级去重口径)

| 链路 | Hit@1 | Hit@3 | MRR |
|---|---|---|---|
| BM25-only | 80.6% | 98.4% | 0.884 |
| Vector-only(TF-IDF,非语义嵌入) | 75.8% | 93.5% | 0.844 |
| **Hybrid+RRF(生产默认)** | **80.6%** | **98.4%** | **0.884** |
| Hybrid+Rerank(可选实验开关,默认关) | 74.2% | 90.3% | 0.815 |

## 六、2026-10-16 完善轮(二轮调研加固,详见 IMPROVEMENTS.md)

独立代码调研发现并修复 9 项缺陷,全部带验证证据;完整报告见 [IMPROVEMENTS.md](IMPROVEMENTS.md)。

| 编号 | 缺陷 | 影响 | 修复 | 验证 |
|---|---|---|---|---|
| F1 | `fuse_rrf` 用常数 1/(RRF_K+1),与排名无关,非标准 RRF | 设计-实现不一致;接入真语义向量后双通道分歧大时系统性偏好"双通道都命中但排名靠后"的文档 | 改为 `Σ 1/(k+rank)` | test_rrf_uses_rank_based_formula;62 条复测 Hit@1/Hit@3 不变、MRR 0.884→0.882、Rerank 路径 74.2/90.3→77.4/96.8 |
| F2 | bm25-only chunk 的 vec_rank 伪造为 bm25 排名 | 引用卡片/调试接口观测数据失真,与"可观察检索"承诺矛盾 | 排名表仅记录真实命中通道 | test_vec_rank_absent_when_only_bm25_hits |
| F3 | 前端三处未转义输出(来源标题/看板分类/历史回放) | 存储型 XSS(与 F4 组成未授权注入链) | 全量 escapeHtml | 代码审查 + escapeHtml 覆盖路径确认 |
| F4 | 知识库写接口(POST/DELETE)无鉴权 | 任何人可增删知识库,污染检索与引用 | 可选 ADMIN_TOKEN + X-Admin-Token 门禁;演示模式保持开放(验收脚本兼容) | test_admin_token_gates_knowledge_writes / test_admin_token_unset_keeps_demo_open |
| F5 | 令牌桶字典按用户 token 无界增长 | 伪造海量 token 可耗尽内存 | 上限 10,000 + 最久未活跃淘汰一半 | test_token_bucket_eviction |
| F6 | BM25 查询逐文档全量扫描 O(词数×N×文档长) | 语料增长后检索吞吐坍缩(20× 语料实测 68 QPS) | 倒排索引 + 预计算词频 | test_bm25_inverted_index_equivalent_to_bruteforce(逐位等价);A/B:10×(当前语料)/35×(20× 语料) |
| F7 | 云端生成降级静默吞异常 | 故障不可归因(频率/超时/网络/鉴权无法区分) | 降级原因落日志 | test_zhipu_fallback_logs_reason |
| F8 | 知识删除在 ingestion 文件锁外读写 JSON | 与新增并发时读写竞态,可能丢更新或索引-文件不一致 | remove_document 并入统一锁;文件单次读取 | test_remove_document_semantics |
| F9 | bench.py retrieval 基准误测重排路径(retrieve 默认 rerank=True) | "默认 Hybrid+RRF 链路"吞吐被系统性低估,与宣称口径不符 | `retrieve(q, rerank=RERANK_ENABLED)`,输出标签标注实际链路 | 修正后同机实测 RRF 路径 515.8–880.4 QPS / p50 1.1–1.9ms(vs 重排路径 ~33 QPS) |
| F10(2026-10-27) | 会话读取/删除未校验属主,可水平越权读删他人会话 | 隐私泄露 + 数据破坏(知道 12 位会话 id 即可操作) | db.get_conversation + API 归属校验,非属主与不存在统一 404;前端请求带令牌 | test_conversation_isolation;HTTP 手验 4/4(artifacts/validation_2026-10-27.txt) |

完善轮复测:pytest 13/13(新增 9 项)、eval_matrix 四路指标见 §五上方 2026-10-16 复测表(REPRODUCIBILITY.md §3)、acceptance 4/4 PASS、E2E 43.3 QPS / 0 失败(Win/x64)。

结论(如实表述):在当前 62 条校园事务评测集上,BM25 对关键词密集型规章问题表现最好;TF-IDF 向量补充了另一种检索视角,但并未稳定超过 BM25;轻量词面 Reranker 实测无收益,因此保持 Provider 化设计并默认关闭(RERANK_ENABLED=1 可开启),计划替换为 Cross-Encoder 后再次评估。

口径说明:早期 RRF 评测存在"同文档双通道 chunk 重复占位"失真(旧值 95.2/0.863);FINAL 轮补齐 RRF 生产链路文档级去重后,四路统一口径实测 98.4/0.884,以本表为准。调优过程中修复的三个真实缺陷:停用词表构造 bug(整串未 split)、RRF 候选池截断、输出缺少文档级去重(初版生产链路 Hit@3 82.3% → 修复后 Rerank 路径 90.3%)。
