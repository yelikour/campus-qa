// 智问校园 CampusMind —— 设计与架构文档(SDD+SAD 合并)生成脚本
const { Document, Packer, Paragraph, TextRun, ImageRun, AlignmentType, SectionType, NumberFormat, TableOfContents } = require("docx");
const fs = require("fs");
const { PALETTE, buildCoverR2, h1, h2, h3, body, run, bullet, caption, tableTitle, hTable, pageFooter, pageHeader, F } = require("./docx_lib.js");

const pgSize = { width: 11906, height: 16838 };
const pgMargin = { top: 1440, bottom: 1440, left: 1701, right: 1417 };
const AVAIL_EMU = 9345; // 可用宽度(twips)
const IMG_W = 6600;     // 架构图统一约 70% 宽,避免整图+图注被分页推出留白

const children = [];

function img(path, wPx, hPx, widthTw) {
  const w = widthTw || IMG_W;
  const h = Math.round(w * hPx / wPx);
  return new Paragraph({
    alignment: AlignmentType.CENTER, spacing: { before: 120, after: 40 },
    keepNext: true, // 图与图注同页保持,避免分页拆开
    children: [new ImageRun({ type: "png", data: fs.readFileSync(path),
      transformation: { width: Math.round(w / 20), height: Math.round(h / 20) } })],
  });
}

// ================================================================ 1 引言
children.push(h1("1  引言"));
children.push(h2("1.1  编写目的与文档关系"));
children.push(body("本文档是《软件需求规格说明书(SRS)》的设计侧承接,合并软件设计文档(SDD,模块/数据/接口的详细设计)与软件架构文档(SAD,多视图架构描述与决策记录)为一册:第 2-3 章为架构描述(SAD),第 4-7 章为详细设计(SDD),第 8-10 章为部署、决策与质量证据。需求编号 FR-x / NFR-x 与 SRS 一致,追踪矩阵见第 10 章。"));
children.push(h2("1.2  范围与读者"));
children.push(body("覆盖后端(app/api、services、repository、core 四分包)、前端原生 SPA 与评测工具链的全部设计决策;预期读者为课程指导教师、项目组成员与后续维护者。文档中全部指标为 2026-10-16 复测实测值,复现方法见 docs/REPRODUCIBILITY.md。"));

// ================================================================ 2 架构总览
children.push(h1("2  架构总览"));
children.push(h2("2.1  架构风格与总体形态"));
children.push(body("系统采用分层风格的模块化单体:五层单向依赖、进程内调用,以分包边界预留服务化拆分点(ADR-1)。演示形态为单进程零外部依赖;生产形态通过反向代理与多实例水平扩展(第 8 章),无需修改应用代码。"));
children.push(img("docs/assets/arch_layers.png", 2280, 1620));
children.push(caption("图 2-1  五层分层架构(接入 \u2192 网关边界 \u2192 应用服务 \u2192 RAG 引擎 \u2192 数据)"));
children.push(h2("2.2  分层职责"));
children.push(tableTitle("表 2-1  分层职责与技术选型"));
children.push(hTable(["层次", "职责", "主要构件"], [
  ["接入层", "用户交互与流式渲染", "原生 SPA 三视图(问答/知识库/看板),SSE 解析,输出全量转义"],
  ["网关边界", "限流、鉴权、跨域", "令牌桶(5 QPS/突发 10,桶字典有界)、ADMIN_TOKEN 写鉴权、CORS"],
  ["应用服务", "用例编排", "chat(SSE 问答)、knowledge(增删查+热更新)、conversations、admin(统计)"],
  ["RAG 引擎", "检索与生成", "BM25Index(倒排)、VectorIndex(TF-IDF/embedding-3)、fuse_rrf、Reranker 开关、GeneratorProvider"],
  ["数据层", "持久化与语料", "SQLite(WAL,会话/消息/查询日志)、campus_qa.json 知识语料、内存索引(热重建)"],
], [1500, 2200, 5645]));
children.push(h2("2.3  技术选型与约束"));
children.push(bullet("后端 Python 3.10+ / FastAPI / uvicorn;分词 jieba;HTTP 客户端 httpx;测试 pytest"));
children.push(bullet("约束 C-1 零依赖演示:C-2 Provider 可插拔(ADR-4/ADR-7);C-4 如实原则(引擎信息可见)"));
children.push(bullet("选型理由:FastAPI 原生 async 承载 SSE 流;自实现 BM25/RRF 保证算法可解释、可评测、零模型依赖"));

// ================================================================ 3 4+1 视图
children.push(h1("3  架构描述:4+1 视图"));
children.push(h2("3.1  逻辑视图(功能分解)"));
children.push(body("最终用户视角的功能结构。检索引擎 HybridRetriever 聚合稀疏通道 BM25Index(倒排索引 + k1=1.5/b=0.75)、稠密通道 VectorIndex(EmbeddingProvider 抽象:TF-IDF 词袋或智谱 embedding-3)与 fuse_rrf 融合;生成端 GeneratorProvider 具有本地抽取式与智谱 GLM 两个实现;ingestion 负责语料摄取、QA 双通道分块与热重建。"));
children.push(tableTitle("表 3-1  逻辑构件与职责"));
children.push(hTable(["构件", "位置", "职责"], [
  ["HybridRetriever", "services/retrieval.py", "双通道检索编排、RRF 融合、文档级去重、无知识兜底"],
  ["GeneratorProvider", "services/generation.py", "流式生成抽象;本地抽取式/云端 GLM;异常熔断降级"],
  ["ingestion", "services/ingestion.py", "语料装载、q/a 分块(答案按 3 句滑窗)、统一文件锁热更新"],
  ["api 路由组", "app/api/*", "chat / knowledge / conversations / admin 四组 HTTP 用例"],
  ["repository.db", "repository/db.py", "SQLite 仓储:会话、消息、查询日志(接口隔离 SQL)"],
  ["security", "core/security.py", "令牌桶限流(有界淘汰)与 ADMIN_TOKEN 写鉴权"],
], [1900, 2600, 4845]));
children.push(h2("3.2  进程视图(并发与同步)"));
children.push(bullet("运行时为单进程 asyncio 事件循环:chat 以流式生成器逐事件推送 SSE,不阻塞其它请求"));
children.push(bullet("并发控制:入口令牌桶按用户隔离;桶字典上限 1 万、最久未活跃淘汰,防伪造令牌内存耗尽"));
children.push(bullet("热更新同步:ingestion 持文件锁串行化「读语料-写文件-重建索引」,新增与删除共用一把锁(F8 修复)"));
children.push(bullet("SQLite 连接为线程局部并开启 WAL,读多写少场景并发安全"));
children.push(h2("3.3  开发视图(代码组织)"));
children.push(bullet("backend/app 四分包 api / services / repository / core,依赖方向单向:api \u2192 services \u2192 repository/core"));
children.push(bullet("frontend 原生三文件 SPA(index.html / app.js / style.css),无构建链;scripts 为评测工具链(eval_matrix / bench / acceptance);tests 含冒烟与完善轮回归共 13 项"));
children.push(bullet("构建与文档脚本位于 .build/(deck 与 docx 生成均可在本机一键复现)"));
children.push(h2("3.4  物理视图(部署拓扑)"));
children.push(img("docs/assets/arch_deploy.png", 2280, 1340));
children.push(caption("图 3-1  部署拓扑与演进(演示单机 \u2192 Nginx 反代多实例 \u2192 限流外置)"));
children.push(body("演示形态:浏览器直接访问 uvicorn(127.0.0.1:8000,同源托管前端静态资源)。生产形态:Nginx 终止 TLS 并反代 /api(proxy_buffering off 保 SSE 直通,proxy_read_timeout \u2265 60s),静态资源直出;多实例共享外置数据;云端 GLM/embedding 为可选外部服务,异常自动降级本地。"));
children.push(h2("3.5  场景视图(端到端用例走查)"));
children.push(img("docs/assets/arch_sequence.png", 2469, 1500));
children.push(caption("图 3-2  一次问答的时序:检索、融合、流式生成与引用溯源"));
children.push(body("以「图书馆开放时间是几点」走查:浏览器 POST /api/chat \u2192 网关限流校验(进程视图)\u2192 HybridRetriever 双通道检索与 RRF 融合(逻辑视图)\u2192 meta 事件先推引用来源 \u2192 GeneratorProvider 流式生成 \u2192 消息与查询日志落库(数据层)\u2192 引用卡片渲染。该场景贯穿四视图,是验收 A1-A4 的载体。"));

// ================================================================ 4 检索引擎详细设计
children.push(h1("4  详细设计:RAG 检索引擎"));
children.push(h2("4.1  双通道检索"));
children.push(bullet("稀疏通道 BM25:jieba lcut_for_search 分词(停用词过滤),倒排索引(词\u2192{文档:词频}),查询仅访问命中词倒排链;与暴力扫描逐位等价(单元测试校验),当前语料 10 倍、20 倍语料 35 倍吞吐(F6)"));
children.push(bullet("稠密通道:演示环境 TF-IDF 加权词袋(与 BM25 共享 idf);生产切智谱 embedding-3(批量嵌入 + 内存缓存),接口不变"));
children.push(h2("4.2  RRF 融合与质量控制"));
children.push(body("融合公式为标准 RRF:score(d) = \u03a3_channel 1/(RRF_K + rank),RRF_K=60,对排名融合、免分数归一化(完善轮 F1 将常数权重修正为排名权重,为语义通道预留正确行为)。质量控制包含文档级去重(同文档 q/a 双通道 chunk 仅保留最高分,避免挤占名额)与无知识硬零兜底(候选与查询实质词零交集即判无知识,触发 FR-6)。"));
children.push(h2("4.3  重排序(实验开关)"));
children.push(body("LightweightReranker 为特征化词面重排(实质词覆盖/二元词重叠/句子级重叠/标签信号);62 条评测显示其无稳定收益(Hit@1 77.4% vs RRF 80.6%),故 RERANK_ENABLED 默认关闭,保留 Provider 化接口,计划替换 Cross-Encoder(bge-reranker)后重评。"));
children.push(h2("4.4  参数标定(评测驱动)"));
children.push(tableTitle("表 4-1  关键参数与标定依据"));
children.push(hTable(["参数", "取值", "标定依据"], [
  ["CHUNK_TOP_K / FINAL_TOP_K", "5 / 3", "融合候选与最终上下文条数,Top-3 已覆盖 98.4% 正解"],
  ["RRF_K", "60", "标准取值;对排名融合,语料规模不敏感"],
  ["MIN_RELEVANCE", "0.08", "62 条标定:0.15 误杀口语化正解,0.06 放入无关命中"],
], [2600, 1500, 5245]));

// ================================================================ 5 数据库设计
children.push(h1("5  数据库设计"));
children.push(h2("5.1  存储划分与 ER 关系"));
children.push(bullet("关系数据(SQLite):conversation 会话 1\u2192N message 消息;query_log 查询日志独立追加,不关联个人"));
children.push(bullet("文档数据(JSON):知识语料 campus_qa.json,摄取为 136 个双通道 chunk(question 通道管问法匹配,answer 通道按 3 句滑窗管内容覆盖,同 doc_id 关联引用溯源)"));
children.push(bullet("内存数据:BM25 倒排与向量矩阵构成检索索引,版本号递增,热更新免重启重建"));
children.push(h2("5.2  表结构"));
children.push(tableTitle("表 5-1  关系表结构(SQLite DDL 摘要)"));
children.push(hTable(["表", "字段", "说明"], [
  ["conversation", "id PK / user_token / title / created_at / updated_at", "用户令牌隔离;标题取首问前 24 字"],
  ["message", "id PK / conversation_id FK / role / content / sources(JSON) / latency_ms / created_at", "sources 保存引用来源快照,支撑历史回放"],
  ["query_log", "id PK 自增 / ts / query / hit / top_score / latency_ms / category", "看板聚合源;仅追加"],
], [1900, 4200, 3245]));
children.push(h2("5.3  演进设计"));
children.push(bullet("仓储模式隔离 SQL:repository/db.py 对上仅暴露函数接口,替换 PostgreSQL 只改实现不改调用方(NFR-6)"));
children.push(bullet("知识文件与索引共用一把文件锁双写一致(F8);SQLite 开 WAL 支持并发读"));

// ================================================================ 6 接口设计
children.push(h1("6  接口设计"));
children.push(h2("6.1  问答接口(SSE)"));
children.push(body("POST /api/chat,请求体 {message, conversation_id?},响应为 text/event-stream 事件序列:meta(会话 id、检索耗时、引用来源数组、引擎名)\u2192 delta(增量文本)多次 \u2192 done(消息 id、总耗时);流内异常推送 error 事件。429 表示触发限流。"));
children.push(h2("6.2  知识与运维接口"));
children.push(tableTitle("表 6-1  API 摘要(与 SRS 表 6-1 对应)"));
children.push(hTable(["端点", "方法", "语义", "关键行为"], [
  ["/api/knowledge", "GET", "分页列表", "category / q 过滤;分类集合基于全量计算"],
  ["/api/knowledge", "POST", "批量新增", "锁内追加+热重建,版本递增;ADMIN_TOKEN 启用时需 X-Admin-Token"],
  ["/api/knowledge/{id}", "DELETE", "删除", "remove_document 统一锁;404 不存在"],
  ["/api/knowledge/search", "GET", "调试检索", "返回双通道排名与融合分数(观测数据不伪造,F2)"],
  ["/api/admin/stats", "GET", "运行统计", "含 llm/embedding provider 与索引版本(如实展示)"],
], [2500, 900, 1700, 4245]));

// ================================================================ 7 前端设计
children.push(h1("7  前端设计(SPA)"));
children.push(bullet("三视图单页应用:智能问答(流式渲染+引用卡片)、知识库管理(分页/筛选/录入)、运行看板(统计+分类热点)"));
children.push(bullet("SSE 解析:fetch 流式读取,按事件分派;meta 先行渲染引用区,打字机增量渲染回答"));
children.push(bullet("安全实现:全部 innerHTML 插值经 escapeHtml(来源标题/看板分类/历史回放三处修复,F3);管理令牌按需提示输入并记忆"));
children.push(bullet("交互细节与状态设计(空态/限流/无知识兜底/降级提示)见《UI 原型》交付物"));

// ================================================================ 8 部署与运维
children.push(h1("8  部署与运维"));
children.push(h2("8.1  配置项(环境变量)"));
children.push(tableTitle("表 8-1  配置项"));
children.push(hTable(["变量", "默认", "说明"], [
  ["ZHIPUAI_API_KEY", "空", "配置后生成切 GLM、向量切 embedding-3;异常自动降级"],
  ["LLM_PROVIDER / EMBEDDING_PROVIDER", "local / auto", "Provider 显式指定;auto=有 Key 用云端"],
  ["RERANK_ENABLED", "0", "重排实验开关(实测无收益,默认关)"],
  ["RATE_LIMIT_QPS / BURST", "5 / 10", "单用户令牌桶"],
  ["ADMIN_TOKEN", "空", "设置后知识写接口强制 X-Admin-Token(演示开放模式启动时打印提示)"],
], [3200, 1300, 4845]));
children.push(h2("8.2  扩展三级与反向代理要点"));
children.push(bullet("第一级 uvicorn workers 竖扩;第二级 Nginx 反代多实例(应用无状态,SQLite/索引外置或每实例只读);第三级限流外置 Redis 滑动窗口"));
children.push(bullet("Nginx 要点:proxy_buffering off 保 SSE 直通;proxy_read_timeout \u2265 60s;静态直出与 TLS 终止;limit_req 与应用令牌桶双层限流"));
children.push(bullet("容量基线:单实例 E2E 42-44 QPS(0 失败),万人在校场景余量 10 倍以上;成本测算见《经济适用型与运营方案》"));

// ================================================================ 9 架构决策记录
children.push(h1("9  架构决策记录(ADR)"));
const adrs = [
  ["ADR-1 模块化单体起步,预留服务化边界", "课程周期 8 周、3 人团队,微服务全栈成本不可承受,但需为演进留路。", "五层分包、进程内调用、应用无状态(SQLite/索引可外置)。", "正:交付快、调试链路短;负:规模增长后需按边界拆分(已预留在分包与接口设计)。"],
  ["ADR-2 混合检索 + RRF 融合", "规章问答词面匹配强,但口语改写易漏召回,单通道无冗余。", "BM25 \u2225 向量双通道,RRF 对排名融合免归一化;文档级去重 + 硬零兜底。", "正:Hit@3 98.4%,通道独立演进;负:双索引成本,参数需评测标定。"],
  ["ADR-3 SSE 承载流式输出", "回答生成耗时数百毫秒,同步等待体验差。", "meta 先推引用,delta 增量推文,done 收尾;前端打字机渲染。", "正:首字即时、可感知进度;负:反向代理需关缓冲(部署清单已列)。"],
  ["ADR-4 生成 Provider 插件化 + 熔断降级", "演示零依赖与生产质量二选一矛盾。", "GeneratorProvider 统一流式接口;默认本地抽取式,配 Key 切 GLM;异常流内回退并落日志。", "正:演示/生产同构,可用性有硬底(A1 PASS);负:双实现双份测试。"],
  ["ADR-5 内存索引热重建", "知识录入要求免重启生效(<5s)。", "摄取服务持锁重建全量索引,版本号递增,前端可见。", "正:59 篇/136 chunks 重建 <1s;负:语料巨大时需增量或外置向量库。"],
  ["ADR-6 令牌桶入口限流", "突发流量会拖垮生成与外部 API 配额。", "单机令牌桶(5 QPS/突发 10,桶字典有界淘汰);生产外置 Redis。", "正:A2 精确放行/拒绝;负:多实例需外置共享限流。"],
  ["ADR-7 Embedding Provider 可插拔,TF-IDF 为离线 fallback", "语义向量依赖外部服务,课程环境不可假设可用。", "auto 工厂:有 Key 用 embedding-3(带缓存),否则 TF-IDF;构建失败回退并如实显示。", "正:零依赖与语义升级同构;负:TF-IDF 非语义嵌入,须明示(如实原则)。"],
];
for (const [title, bg, dec, cons] of adrs) {
  children.push(h2(title));
  children.push(body([run("背景:", { bold: true }), run(bg)]));
  children.push(body([run("决策:", { bold: true }), run(dec)]));
  children.push(body([run("后果:", { bold: true }), run(cons)]));
}

// ================================================================ 10 质量证据与追踪
children.push(h1("10  质量证据与需求追踪"));
children.push(h2("10.1  检索评测(n=62 口语化改写,统一文档级去重口径)"));
children.push(tableTitle("表 10-1  四路链路评测(2026-10-16 实测)"));
children.push(hTable(["链路", "Hit@1", "Hit@3", "MRR"], [
  ["BM25-only", "80.6%", "98.4%", "0.884"],
  ["Vector-only(TF-IDF)", "75.8%", "93.5%", "0.844"],
  ["Hybrid+RRF(生产默认)", "80.6%", "98.4%", "0.882"],
  ["Hybrid+Rerank(实验开关)", "77.4%", "96.8%", "0.860"],
], [3600, 1900, 1900, 1945]));
children.push(h2("10.2  性能基准与架构验收"));
children.push(tableTitle("表 10-2  性能基准(拆分口径)"));
children.push(hTable(["基准", "QPS", "p50", "p95", "p99", "失败"], [
  ["retrieval-only(RRF,Win/x64 两次实测)", "515.8-880.4", "1.1-1.9ms", "1.8-3.2ms", "2.1-3.7ms", "0"],
  ["E2E 并发 20(含生成+落库)", "42.1-43.3", "413-425ms", "628-647ms", "727-761ms", "0"],
], [3300, 1500, 1200, 1200, 1200, 945]));
children.push(bullet("架构验收 4/4 PASS:A1 生成降级(139 字正解)/ A2 入口限流(200x10+429x5)/ A3 热更新(版本递增)/ A4 无知识兜底(sources=0)"));
children.push(bullet("单元测试 13/13(冒烟 4 + 完善轮 9:RRF 公式、倒排等价、鉴权、桶淘汰、删除语义、降级日志等)"));
children.push(h2("10.3  追踪矩阵"));
children.push(body("需求 \u2192 质量属性 \u2192 ADR \u2192 模块 \u2192 测试 \u2192 证据的完整映射维护于仓库 docs/traceability.md(含 2026-10-16 完善轮 F1-F9 修复行,见 docs/IMPROVEMENTS.md)。本文档与《SRS》《UI 原型》共同构成课程交付物;仓库 github.com/yelikour/campus-qa(公开)。"));

// ================================================================ 组装
const doc = new Document({
  styles: { default: { document: {
    run: { font: F, size: 24, color: PALETTE.body },
    paragraph: { spacing: { line: 312 } },
  } } },
  sections: [
    { properties: { page: { size: pgSize, margin: { top: 0, bottom: 0, left: 0, right: 0 } } },
      children: buildCoverR2({
        palette: { ...PALETTE.cover, accent: PALETTE.accent },
        englishLabel: "SOFTWARE DESIGN AND ARCHITECTURE",
        title: "\u667a\u95ee\u6821\u56ed CampusMind \u8bbe\u8ba1\u4e0e\u67b6\u6784\u6587\u6863",
        subtitle: "\u8f6f\u4ef6\u8bbe\u8ba1\u8bf4\u660e\u4e66(SDD)+ \u8f6f\u4ef6\u67b6\u6784\u6587\u6863(SAD)\u5408\u5e76 \u00b7 v1.0",
        metaLines: ["\u300a\u8f6f\u4ef6\u4f53\u7cfb\u7ed3\u6784\u300b\u8bfe\u7a0b\u9879\u76ee \u00b7 2026 \u6625\u5b63\u5b66\u671f",
                    "\u56e2\u961f\uff1a\u738b\u82e5\u748b \u00b7 \u4f55\u4fea \u00b7 \u90ed\u7956\u6881",
                    "2026 \u5e74 10 \u6708"],
        footerRight: "CampusMind \u00b7 github.com/yelikour/campus-qa",
      }) },
    { properties: { type: SectionType.NEXT_PAGE,
        page: { size: pgSize, margin: pgMargin, pageNumbers: { start: 1, formatType: NumberFormat.UPPER_ROMAN } } },
      footers: { default: pageFooter() },
      children: [
        new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 480, after: 360 },
          children: [new TextRun({ text: "\u76ee  \u5f55", bold: true, size: 32, color: PALETTE.primary, font: { eastAsia: "SimHei", ascii: "Calibri" } })] }),
        new TableOfContents("Table of Contents", { hyperlink: true, headingStyleRange: "1-2" }),
        new Paragraph({ spacing: { before: 200 },
          children: [new TextRun({ text: "\u6ce8\uff1a\u672c\u76ee\u5f55\u7531\u57df\u4ee3\u7801\u751f\u6210\uff0c\u5982\u7f16\u8f91\u540e\u9875\u7801\u53d8\u52a8\uff0c\u8bf7\u53f3\u952e\u76ee\u5f55\u9009\u62e9\u300c\u66f4\u65b0\u57df\u300d\u5237\u65b0\u3002", italics: true, size: 18, color: "888888", font: F })] }),
      ] },
    { properties: { type: SectionType.NEXT_PAGE,
        page: { size: pgSize, margin: pgMargin, pageNumbers: { start: 1, formatType: NumberFormat.DECIMAL } } },
      headers: { default: pageHeader("\u667a\u95ee\u6821\u56ed CampusMind \u00b7 \u8bbe\u8ba1\u4e0e\u67b6\u6784\u6587\u6863(SDD+SAD)") },
      footers: { default: pageFooter() },
      children },
  ],
});

Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync("docs/\u667a\u95ee\u6821\u56edCampusMind-\u8bbe\u8ba1\u4e0e\u67b6\u6784\u6587\u6863SDD-SAD.docx", buf);
  console.log("SDD+SAD docx written");
});
