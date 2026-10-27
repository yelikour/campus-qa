# 2026-10-16 完善轮:独立调研报告与加固记录

> 背景:对 2026-09-18 FINAL 交付版做第二轮独立代码调研(后端五层 / 前端 SPA / 脚本 / 文档全量通读 +
> 全部证据脚本本地复跑),确认现状可复现(pytest 4/4、评测矩阵四路指标与 README 一致、四项架构验收 4/4 PASS)
> 后,识别出 9 项缺陷并全部修复验证。本报告按「发现 → 影响 → 修复 → 证据」组织,与 traceability.md §六互为索引。

## 0. 调研方法

1. **现状复现**:干净环境安装依赖 → 冒烟测试 → 评测矩阵 → 启动服务 → 四项验收 → SSE 手工验证;
   全部与 2026-09-18 FINAL 产物(artifacts/final_validation.txt)一致,排除"修的是坏基线"。
2. **静态审查**:后端(api/services/repository/core)逐文件通读;前端 app.js 重点审查所有 innerHTML 注入点;
   脚本与文档交叉核对(evaluate 口径、指标、配置项)。
3. **实验驱动**:对每个候选修复先做对照实验(同进程 A/B),采纳与否以数据为准,不做无依据的"顺手改"。

## 1. F1 — `fuse_rrf` 并非标准 RRF(检索正确性)

- **发现**:`services/retrieval.py` 原实现对每个通道命中累加常数 `1.0/(RRF_K+1)`,与该文档在通道内的排名无关
  ——数学上等价于"通道计数投票",而非文档注释与架构文档宣称的 Reciprocal Rank Fusion。
- **影响**:TF-IDF 演示语料上双通道高度相关(都是词面匹配),两版本指标恰好持平(见下),问题被掩盖;
  但接入真实语义向量(智谱 embedding-3)后双通道分歧显著增大,常数版会系统性偏好"双通道都命中但排名靠后"
  的文档而非"单通道排名靠前"的强匹配,行为错误。
- **对照实验**(修复前,62 条评测):常数版 80.6/98.4/0.884 vs 标准 RRF 80.6/98.4/0.882 —— 结论:
  演示指标持平,修复是面向正确性与未来语义通道的必要修正,如实记录 MRR 一名次内波动。
- **附带收益**:Rerank 实验路径(RRF 先验 0.7 + 词面重排 0.3)从 74.2/90.3/0.815 提升到 77.4/96.8/0.860
  ——常数融合下 rrf_norm 只有 {1.0, 0.5} 两档,先验噪声大;标准 RRF 的连续排名信号让先验真正起效。
- **修复**:`rrf[i] += 1.0/(RRF_K + rank + 1)`,rank 为通道内零基排名。
- **证据**:`tests/test_improvements.py::test_rrf_uses_rank_based_formula`(分数逐项等于公式)、
  `test_rrf_prefers_higher_rank_within_same_channel_hits`;`scripts/eval_matrix.py` 复测。

## 2. F2 — 引用卡片 vec_rank 伪造(可观察性失真)

- **发现**:原 `ranks` 字典构造为 `{i: {"bm25": r+1, "vec": r+1}}`(bm25 命中即同时写入 vec 键),
  仅 BM25 命中的 chunk 显示的 vec_rank 实为 BM25 排名。
- **影响**:与「可观察检索:引用卡片暴露双通道排名」的架构承诺矛盾——调试接口与前端展示的观测数据失真,
  会误导调参与归因。
- **修复**:排名表只写真实命中通道;未命中通道保持 `None`,前端显示 `-`。
- **证据**:`test_vec_rank_absent_when_only_bm25_hits`;手工 SSE 验证 meta 事件
  (kb-008 bm25#1/vec#1、kb-009 bm25#5/vec#3,均为真实双通道命中)。

## 3. F3 — 前端三处未转义输出(存储型 XSS)

- **发现**:`frontend/app.js` 中三处模板字符串直接注入 innerHTML:
  ① `finishAnswer` 的来源标题 `s.title`(知识条目 source 字段);② `loadDash` 的热点分类 `c`;
  ③ `openConversation` 历史回放的 bot 消息正文(走 `appendMsg` 的 bot 分支不转义)。
- **影响**:知识库 answer/source/category 均为知识文本,若被注入(结合 F4 无鉴权写入)即形成
  存储型 XSS——恶意条目被检索命中后,脚本在所有提问学生的浏览器执行。
- **修复**:三处全部 `escapeHtml`;用户输入路径本已转义,未改动。
- **证据**:代码路径审查(escapeHtml 覆盖所有 innerHTML 插值点);与 F4 的 401 门禁组成双防线。

## 4. F4 — 知识库写接口无鉴权(未授权增删)

- **发现**:`POST/DELETE /api/knowledge` 无任何身份校验。
- **影响**:任何人可增删知识库——轻则污染检索结果与引用溯源(可信性崩塌),重则配合 F3 打存储型 XSS。
- **修复设计**:新增 `ADMIN_TOKEN` 环境变量 + `core/security.require_admin` 门禁。
  **默认不设置 = 演示开放模式**(启动日志提示),课程演示与 acceptance.py 免 Key 不受影响;
  设置后强制 `X-Admin-Token` 请求头,前端管理页 401 时提示输入并记住(localStorage)。
  读接口(列表/检索/统计)保持开放——运行看板是面向所有用户的演示特性,且不含个人数据。
- **证据**:`test_admin_token_gates_knowledge_writes`(无/错令牌 401、正确令牌 200)、
  `test_admin_token_unset_keeps_demo_open`(演示模式兼容验收)。

## 5. F5 — 令牌桶字典无界增长(内存泄漏面)

- **发现**:`core/security.py` 的 `_buckets` 按用户 token 只增不减。
- **影响**:攻击者伪造海量随机 `X-User-Token` 即可无界消耗内存(限流本身挡不住字典膨胀)。
- **修复**:上限 10,000 只桶,超限按最久未活跃淘汰一半(近似 LRU;生产换 Redis 时由 TTL 承担同样职责)。
- **证据**:`test_token_bucket_eviction`。

## 6. F6 — BM25 查询全量扫描(性能/扩展性)

- **发现**:原 `search` 对每个查询词遍历全部文档并 `tokens.count(w)` 重扫文档词表,复杂度 O(词数×N×文档长)。
- **影响**:当前 136 chunks 无感;语料增长后检索吞吐坍缩——实测 20× 语料(2,720 chunks)仅 68 QPS,
  与"高并发、容量-成本线性挂钩"的运营方案叙事矛盾。
- **修复**:构建期生成倒排索引(词 → {文档下标: 词频}),查询只访问命中词的倒排链。
- **等价性**:与原暴力算法逐查询、逐位一致(浮点运算路径相同),由
  `test_bm25_inverted_index_equivalent_to_bruteforce` 在真实语料上校验。
- **A/B 证据**(Windows/x64,同进程三轮取最好):

  | 语料 | 旧(全量扫描) | 新(倒排) | 加速比 |
  |---|---|---|---|
  | 136 chunks(当前) | 2,145 QPS | 21,505 QPS | 10.0× |
  | 2,720 chunks(20×) | 68 QPS | 2,587 QPS | 35× |

  全链路 `retrieve()` 27 QPS 持平(瓶颈在 jieba 分词与融合编排,BM25 非热点,无回归);
  语义:通道内优化不改全链路指标,但把"语料增长 → 检索坍缩"的扩展性风险消除了。

## 7. F7 — 云端生成降级静默吞异常(不可归因)

- **发现**:`ZhipuGenerator.stream` 的 `except Exception` 直接回退本地,无任何日志。
- **影响**:ADR-4 的熔断降级是核心可用性机制,但触发原因(限流/超时/网络/鉴权)完全不可观测,
  生产排障只能盲猜。
- **修复**:降级时打印异常类型与信息(`[generation] 云端 GLM 不可用,降级本地抽取式:ConnectError: ...`)。
- **证据**:`test_zhipu_fallback_logs_reason`(不可达地址触发降级,断言日志与降级产出)。

## 8. F8 — 知识删除在文件锁外读写(竞态)

- **发现**:`api/knowledge.py` 的 `delete_knowledge` 直接读写 JSON 语料文件,未持有 ingestion 的 `_lock`;
  同文件此前还被读取两次(列表接口)。
- **影响**:删除与新增并发时存在读写竞态(丢更新/索引与文件不一致);列表接口无谓双倍 IO。
- **修复**:删除逻辑并入 `ingestion.remove_document`(与新增共用同一把锁,KeyError → API 404);
  `rebuild_index/add/remove` 统一"锁内重建"结构;列表接口单次读取。
- **证据**:`test_remove_document_semantics`(增删后文件与索引同步、语料恢复原状、重复删除 KeyError)。

## 8b. F9 — bench.py 检索基准口径失真(评测方法论)

- **发现**:`scripts/bench.py` 的 `bench_retrieval` 调用 `retriever.retrieve(q)` 未传 `rerank`,
  走默认 `rerank=True` —— 测的是**重排实验路径**,而基准与 README 均宣称测"默认 Hybrid+RRF 链路"
  (生产 `RERANK_ENABLED=0`)。
- **影响**:retrieval-only 基准系统性偏重(重排路径含逐候选分词/二元组/句子级重叠计算)。
  2026-09-18 FINAL 的 251.4 QPS 实为重排路径吞吐;RRF 生产路径真实吞吐被低估。
- **修复**:`retrieve(q, rerank=settings.RERANK_ENABLED)`,输出标签标注实际链路。
- **证据**:修正后同机实测 RRF 路径 515.8–880.4 QPS / p50 1.1–1.9ms(两次实测,负载波动;vs 重排路径同机 ~33 QPS,
  与 §6 A/B 中 BM25 通道 10× 加速的结论互相印证)。

## 9. 未采纳的候选(如实记录)

- **调优 Rerank 权重/特征**:62 条评测集上调参有过拟合风险,且项目已明确"轻量重排无收益、
  计划换 Cross-Encoder"的技术路线;本轮仅因 F1 修正自然获得 +3.2/+6.5pp,未额外调参。
- **给 `GET /api/admin/stats` 加鉴权**:看板是全员演示特性、仅含聚合统计;加门禁破坏演示叙事,
  收益低,未采纳(写接口已保护)。
- **CORS 收紧**:同源部署(前端由本服务/Nginx 托管)下 `allow_origins=["*"]` 风险有限;
  生产化部署清单已在《经济适用型与运营方案》反向代理章节覆盖,不在本轮代码改动。

## 10. 2026-10-27 三轮增补:F10 会话越权

- **发现**:`GET/DELETE /api/conversations/{cid}` 未校验会话属主——知道(或枚举到)12 位会话 id
  即可读取他人完整对话(含引用快照)或删除他人会话(水平越权)。首轮调研曾记录为次要项,本轮修复。
- **修复**:仓储层新增 `get_conversation(cid)`;API 层 `_own_conversation` 校验 `X-User-Token`
  与属主一致;**不一致与不存在统一返回 404**,不泄露会话存在性;前端历史回放请求补带用户令牌。
- **证据**:`tests/test_improvements.py::test_conversation_isolation`(B 越权读/删 404,A 正常 200/200);
  HTTP 手验同结论(artifacts/validation_2026-10-27.txt §6)。
- **卫生优化(同轮)**:`ingestion._load_seed` 公有化为 `load_seed`,API 层不再触私有函数。
- **三轮回归**:pytest **14/14**(新增 1 项)、评测矩阵四路不变、验收 4/4 PASS、
  retrieval 665-679 QPS / E2E 42-43 QPS 0 失败(Win/x64,2026-10-27 实测)。

## 11. 回归验证汇总(2026-10-16,Windows 11 x64 / Python 3.12.10)

| 验证项 | 命令 | 结果 |
|---|---|---|
| 单元测试 | `python -m pytest backend/tests/ -q` | **13 passed**(4 冒烟 + 9 新增) |
| 检索评测矩阵 | `python scripts/eval_matrix.py` | BM25 80.6/98.4/0.884 · Vector 75.8/93.5/0.844 · **RRF 80.6/98.4/0.882** · Rerank 77.4/96.8/0.860 |
| retrieval-only 基准(修正口径) | `python scripts/bench.py retrieval` | RRF 生产路径 515.8–880.4 QPS / p50 1.1–1.9ms / 0 失败(同机两次实测,负载波动) |
| 架构验收 | `python scripts/acceptance.py` | **4/4 PASS**(A1 降级/A2 限流 200×10+429×5/A3 热更新/A4 兜底) |
| E2E 基准 | `python scripts/bench.py e2e` | 43.3 QPS / 0 失败 / p99 761ms(并发 20) |
| BM25 A/B | 同进程对照 | 10.0×(136 chunks)/ 35×(20× 语料),逐位等价 |
| SSE 手工验证 | curl /api/chat | meta 事件双通道真实排名;融合分 2/61=0.0328 与标准 RRF 公式一致 |

> 指标口径与历史值的关系见 REPRODUCIBILITY.md §3/§6;追踪矩阵增补见 traceability.md §六。
