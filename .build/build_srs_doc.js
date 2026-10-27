// 智问校园 CampusMind —— 软件需求规格说明书(SRS)生成脚本
const { Document, Packer, Paragraph, TextRun, AlignmentType, SectionType, NumberFormat, TableOfContents } = require("docx");
const fs = require("fs");
const { PALETTE, buildCoverR2, h1, h2, body, run, bullet, tableTitle, hTable, pageFooter, pageHeader, F } = require("./docx_lib.js");

const pgSize = { width: 11906, height: 16838 };
const pgMargin = { top: 1440, bottom: 1440, left: 1701, right: 1417 };
const W3 = [3200, 4000, 2688]; // 常用三列宽(twips,合计≈可用宽度 9345)

const children = [];

// ================================================================ 1 引言
children.push(h1("1  引言"));
children.push(h2("1.1  编写目的"));
children.push(body("本说明书定义「智问校园 CampusMind」校园智能问答系统的功能需求与非功能需求,作为课程项目设计、实现、测试与验收的基线依据。预期读者为课程指导教师、项目组成员以及后续维护者。需求条目编号为 FR-x(功能需求)与 NFR-x(非功能需求),全部条目在《设计与架构文档》第 10 章追踪矩阵中映射到实现模块与验证证据。"));
children.push(h2("1.2  项目范围"));
children.push(body("系统面向在校学生的校园事务咨询场景,提供基于校内知识语料的自然语言问答:口语化提问,回答流式输出并强制标注校内信息来源;知识库无相关内容时诚实回退,不编造事实。范围包含智能问答、知识库管理与热更新、运行看板三类能力;不包含教务/财务等业务系统的数据对接,知识语料以人工维护的校园规章 QA 库为准(演示语料 59 篇文档)。"));
children.push(h2("1.3  术语与缩略语"));
children.push(tableTitle("表 1-1  术语与缩略语"));
children.push(hTable(["术语", "定义"], [
  ["RAG", "检索增强生成(Retrieval-Augmented Generation):先检索知识片段,再基于片段生成回答"],
  ["BM25", "稀疏通道关键词排序算法,本系统 jieba 分词后自实现(k1=1.5, b=0.75)"],
  ["RRF", "倒数排名融合(Reciprocal Rank Fusion),公式 score = \u03a3 1/(k+rank),对排名而非原始分数融合"],
  ["SSE", "Server-Sent Events,服务端向浏览器单向推送事件流,承载打字机式输出"],
  ["TF-IDF", "词频-逆文档频率加权词袋,演示环境的向量通道实现(非语义嵌入,如实标注)"],
  ["Hit@K / MRR", "检索评测指标:前 K 命中率 / 平均倒数排名"],
], W3.map(() => 0).length ? [2400, 6945] : [2400, 6945]));
children.push(h2("1.4  参考文献"));
children.push(bullet("《软件体系结构》课程任务说明与学生组队要求"));
children.push(bullet("GB/T 9385-2008 计算机软件需求规格说明规范"));
children.push(bullet("项目仓库 docs/traceability.md(需求追踪矩阵)与 docs/REPRODUCIBILITY.md(复现指南)"));

// ================================================================ 2 总体描述
children.push(h1("2  总体描述"));
children.push(h2("2.1  产品定位与前景"));
children.push(body("校园事务信息散落在官网、公众号与口头传播中,口径不一且难以溯源;通用大模型缺少校内语料,容易编造。CampusMind 以「检索增强 + 强制引用」为核心,回答每条均标注校内知识来源与双通道检索排名,无命中时明确说明并引导咨询职能部门。产品形态为 Web 应用(原生 SPA + FastAPI 后端),默认零外部依赖离线运行,可配置云端大模型与语义向量服务提升生成与检索质量。"));
children.push(h2("2.2  用户类别与特征"));
children.push(tableTitle("表 2-1  用户类别"));
children.push(hTable(["用户", "特征与使用方式", "主要诉求"], [
  ["在校学生(主要)", "移动/桌面浏览器提问,口语化问法,不关心内部实现", "快、准、有出处;不知道就说不知道"],
  ["知识库管理员", "知识库管理视图录入/删除条目,维护分类与来源", "录入即生效,免重启;误操作可控"],
  ["运维/开发(课程演示)", "运行看板观察命中率与时延,运行评测与验收脚本", "指标可复现,引擎状态可见"],
], [1900, 4700, 2745]));
children.push(h2("2.3  运行环境"));
children.push(bullet("服务端:Python 3.10+(实测 3.12/3.14),FastAPI + uvicorn;Windows / macOS / Linux 均可"));
children.push(bullet("数据:SQLite(内建文件库)+ JSON 知识语料,无 mandatory 外部服务"));
children.push(bullet("客户端:现代浏览器(原生 JS,无构建链);开发期同源部署,生产由 Nginx 托管静态资源并反代 /api"));
children.push(bullet("可选外部服务:智谱 GLM(生成)与 embedding-3(语义向量),配置 API Key 后启用,异常自动降级本地"));
children.push(h2("2.4  设计与实现约束"));
children.push(bullet("C-1 演示零依赖:无 API Key 时全功能离线可运行(本地抽取式生成 + TF-IDF 向量)"));
children.push(bullet("C-2 Provider 可插拔:生成端与向量端同类可替换,接口不变(架构决策 ADR-4/ADR-7)"));
children.push(bullet("C-3 课程周期:3 人团队 8 周交付,模块化单体起步,预留服务化边界"));
children.push(bullet("C-4 如实原则:向量通道为非语义嵌入时必须在前端与统计接口明示;指标口径演变留痕"));
children.push(h2("2.5  假设与依赖"));
children.push(bullet("知识语料由人工整理且规模有限(数十至数百篇),检索采用内存索引即可满足性能与成本"));
children.push(bullet("单机部署满足校园演示规模;高并发场景按三级扩展方案(uvicorn workers / Nginx 多实例 / Redis 限流)演进"));
children.push(bullet("云端 API 按真实收费价计费,成本模型见《经济适用型与运营方案》,不依赖任何限时免费活动"));

// ================================================================ 3 功能需求
children.push(h1("3  功能需求"));
children.push(body("功能需求按用户可见能力划分为六项;每项给出描述、主流程、替代流程与可执行的验收标准。", { after: 120 }));

function frBlock(no, name, desc, main, alt, ac) {
  children.push(h2("3." + no.slice(3) + "  " + no + " " + name));
  children.push(body(desc));
  children.push(tableTitle("主流程"));
  main.forEach(t => children.push(bullet(t)));
  if (alt && alt.length) {
    children.push(tableTitle("替代流程与异常"));
    alt.forEach(t => children.push(bullet(t)));
  }
  children.push(tableTitle("验收标准"));
  ac.forEach(t => children.push(bullet(t)));
}

frBlock("FR-1", "自然语言问答与引用溯源",
  "学生以口语化问法提问(限 500 字),系统经混合检索定位校内知识,生成回答并在回答下方展示引用卡片:来源名称、分类、BM25/向量双通道排名与融合分数、检索耗时。",
  ["学生输入问题(或点击快捷问题)提交 POST /api/chat", "系统执行 BM25 与向量双通道检索并按 RRF 融合,取前 3 篇文档", "回答流式输出;首个 meta 事件先行推送引用来源列表", "前端渲染引用卡片,双通道排名与分数即时可见"],
  ["触发限流(429):提示请求过于频繁", "检索会话关联:conversation_id 首次由服务端生成,后续复用"],
  ["62 条口语化评测集上生产链路 Hit@3 = 98.4%(scripts/eval_matrix.py)", "引用卡片展示的来源与检索命中一一对应,无编造来源"]) ;

frBlock("FR-2", "流式输出",
  "回答以 SSE 事件流推送,meta(引用)→ delta(增量文本)→ done(统计),前端打字机式渲染,用户无需等待全文生成完成。",
  ["客户端 fetch 建立流式连接,逐事件解析渲染", "meta 事件先到,引用区与「正在参考哪些资料」即时展示", "done 事件携带总耗时与会话标识"],
  ["网络中断:前端提示网络异常;服务端事件流异常时推送 error 事件"],
  ["首字延迟由 meta 先行保障;E2E(含生成与落库)并发 20 实测 42-44 QPS、p99 < 800ms、0 失败(scripts/bench.py e2e)"]);

frBlock("FR-3", "会话与历史(属主隔离)",
  "按浏览器令牌(X-User-Token)隔离会话;侧栏列出历史会话,点击可恢复完整对话记录。",
  ["首次提问自动创建会话;后续消息携带 conversation_id 归档", "侧栏列表按最近活跃排序;点击恢复该会话全部消息"],
  ["删除会话:级联删除消息记录", "越权访问他人会话:统一返回 404,不泄露存在性(F10)"],
  ["刷新页面后历史会话与对话内容完整恢复(演示录屏验证)"]);

frBlock("FR-4", "知识库管理与热更新",
  "管理员在知识库视图检索、筛选、录入、删除知识条目;写入后索引免重启即时重建生效,索引版本号递增并在前端展示。",
  ["录入条目(问法/答案/分类/来源/标签)提交 POST /api/knowledge", "服务端统一文件锁内追加语料并重建双通道索引,版本号 +1", "前端提示新增条数与当前 chunk 数、索引版本"],
  ["设置 ADMIN_TOKEN 环境变量后,写接口强制校验 X-Admin-Token,未授权返回 401", "删除不存在的条目返回 404"],
  ["验收 A3:录入后无需重启即时检索命中并正确回答,索引版本 1\u21922 递增,验收后自动清理(scripts/acceptance.py)"]);

frBlock("FR-5", "运行看板",
  "运维视图实时展示累计提问、知识命中率、平均生成时延、会话数/索引块数,以及命中查询的分类热点条形图;顶栏常驻显示当前 LLM/向量 Provider 与索引版本。",
  ["GET /api/admin/stats 聚合 query_log 与索引状态", "看板视图与顶栏定期刷新"],
  [],
  ["统计口径与数据库记录一致;引擎信息如实反映当前 Provider(本地/云端)"]);

frBlock("FR-6", "无知识诚实回退",
  "知识库无相关问题时不编造:返回引导性回退话术,不携带任何引用来源(sources=0)。",
  ["双通道候选与查询实质词(含同义词标签)零交集时,检索返回空", "生成端输出固定引导话术,建议换问法或咨询对应职能部门"],
  ["用户继续追问:进入下一轮正常检索流程"],
  ["验收 A4:提问与知识库完全无关的问题,sources=0 且回答含回退话术(scripts/acceptance.py)"]);

// ================================================================ 4 非功能需求
children.push(h1("4  非功能需求(质量属性)"));
children.push(body("非功能需求以质量属性场景(六元组:刺激源/刺激/制品/环境/响应/响应度量)表述,每项附实测证据。示例场景给出完整六元组,其余以表 4-1 汇总。", { after: 120 }));
children.push(h2("4.1  示例场景:NFR-2 可用性(完整六元组)"));
children.push(tableTitle("表 4-1  可用性场景六元组"));
children.push(hTable(["要素", "内容"], [
  ["刺激源", "云端 LLM 服务(智谱 GLM)"],
  ["刺激", "API Key 失效 / 请求超时 / 网络中断"],
  ["制品", "生成服务 generation.py(ZhipuGenerator 流内降级)"],
  ["环境", "正常运行,并发问答进行中"],
  ["响应", "流内自动回退本地抽取式生成,降级原因写入日志"],
  ["响应度量", "服务不中断,回答仍含正解关键信息(139 字);验收 A1 PASS"],
], [1800, 7545]));
children.push(h2("4.2  质量属性需求汇总"));
children.push(tableTitle("表 4-2  非功能需求一览(NFR)"));
children.push(hTable(["编号", "质量属性", "需求目标", "实测证据(2026-10-16)"], [
  ["NFR-1", "性能", "检索 p95 < 50ms;E2E p99 < 800ms", "RRF 链路 p95 1.8-3.2ms;E2E p99 727-761ms"],
  ["NFR-2", "可用性", "云端故障自动降级,服务不中断", "验收 A1 PASS(139 字正解,流内回退)"],
  ["NFR-3", "安全性", "单用户限流 5 QPS/突发 10;写接口可鉴权;输出全量转义;会话属主校验", "验收 A2 PASS(200x10+429x5);XSS 转义;ADMIN_TOKEN 门禁;F10 越权返回 404"],
  ["NFR-4", "可修改性", "生成/向量 Provider 同类可替换,接口不变", "zhipu/tfidf 双实现共存,配置即切换"],
  ["NFR-5", "可测试性", "全部指标脚本可复现", "pytest 14/14;评测/基准/验收四套脚本一条命令复现"],
  ["NFR-6", "可扩展性", "应用无状态,支持水平扩展", "SQLite/索引可外置;uvicorn workers \u2192 Nginx 多实例三级扩展"],
], [900, 1300, 3400, 3745]));

// ================================================================ 5 数据需求
children.push(h1("5  数据需求"));
children.push(bullet("知识语料 campus_qa.json:id、category、question、answer、tags、source、updated_at;59 篇演示文档,摄取为 136 个双通道 chunk"));
children.push(bullet("会话数据:conversation(会话)与 message(消息,含引用来源 JSON 与时延)1:N 关联,SQLite 持久化"));
children.push(bullet("查询日志 query_log:每次回答记录命中、最高分、时延、分类,支撑看板聚合;仅追加,不关联个人"));
children.push(bullet("详细表结构与演进设计(SQLite \u2192 PostgreSQL)见《设计与架构文档》第 5 章"));

// ================================================================ 6 外部接口需求
children.push(h1("6  外部接口需求"));
children.push(h2("6.1  用户界面"));
children.push(body("界面为单页应用三视图(智能问答 / 知识库管理 / 运行看板),交互与状态设计详见《UI 原型》交付物;关键状态包含流式回答中、触发限流提示、无知识回退话术与管理鉴权提示。"));
children.push(h2("6.2  软件接口(HTTP API)"));
children.push(tableTitle("表 6-1  API 一览"));
children.push(hTable(["端点", "方法", "说明", "错误码"], [
  ["/api/chat", "POST", "问答(SSE 流式响应)", "429 限流"],
  ["/api/knowledge", "GET/POST", "知识列表分页检索 / 新增(热更新)", "401 鉴权"],
  ["/api/knowledge/{id}", "DELETE", "删除条目并重建索引", "401/404"],
  ["/api/knowledge/search", "GET", "调试检索:双通道排名与分数", "\u2014"],
  ["/api/conversations", "GET", "当前用户会话列表", "\u2014"],
  ["/api/conversations/{cid}", "GET/DELETE", "会话消息 / 删除会话(属主校验)", "404(含越权)"],
  ["/api/admin/stats", "GET", "运行统计与引擎信息", "\u2014"],
  ["/api/health", "GET", "健康检查", "\u2014"],
], [2600, 1400, 3700, 1645]));
children.push(h2("6.3  第三方接口(可选)"));
children.push(bullet("智谱 GLM chat/completions(openai 兼容协议,流式),用于云端生成"));
children.push(bullet("智谱 embedding-3 /embeddings,用于语义向量;两者异常时自动降级本地实现"));

// ================================================================ 7 验收与追踪
children.push(h1("7  验收准则与需求追踪"));
children.push(body("全部功能与质量属性需求均绑定可执行验收:功能面由四项架构验收脚本覆盖,质量面由评测矩阵与性能基准覆盖。需求 \u2192 模块 \u2192 测试 \u2192 证据的完整追踪见仓库 docs/traceability.md(其中完善轮 F1-F9 修复同样入矩阵)。"));
children.push(tableTitle("表 7-1  需求-验收映射"));
children.push(hTable(["需求", "验收方式", "结果"], [
  ["FR-1 / FR-2 / FR-3", "评测矩阵 + E2E 基准 + 演示录屏", "Hit@3 98.4%;44 QPS 0 失败"],
  ["FR-4", "验收 A3 知识热更新", "PASS:版本递增、录入即命中、验后清理"],
  ["FR-5", "看板与统计接口核对", "口径一致"],
  ["FR-6", "验收 A4 无知识兜底", "PASS:sources=0 不编造"],
  ["NFR-1/2/3", "bench + 验收 A1/A2", "全部达标(详见表 4-2)"],
], [2400, 4000, 2945]));
children.push(body("本说明书与《设计与架构文档(SDD+SAD)》《UI 原型》共同构成课程交付物;仓库地址 github.com/yelikour/campus-qa(公开),复现命令见 docs/REPRODUCIBILITY.md。"));

// ================================================================ 组装
const doc = new Document({
  styles: { default: { document: {
    run: { font: F, size: 24, color: PALETTE.body },
    paragraph: { spacing: { line: 312 } },
  } } },
  sections: [
    { properties: { page: { size: pgSize, margin: { top: 0, bottom: 0, left: 0, right: 0 } } },
      children: buildCoverR2({
        palette: PALETTE.cover ? { ...PALETTE.cover, accent: PALETTE.accent } : PALETTE,
        englishLabel: "SOFTWARE REQUIREMENTS SPECIFICATION",
        title: "\u667a\u95ee\u6821\u56ed CampusMind \u8f6f\u4ef6\u9700\u6c42\u89c4\u683c\u8bf4\u660e\u4e66",
        subtitle: "\u6821\u56ed\u667a\u80fd\u95ee\u7b54\u7cfb\u7edf(AI + RAG) \u00b7 SRS v1.0",
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
      headers: { default: pageHeader("\u667a\u95ee\u6821\u56ed CampusMind \u00b7 \u8f6f\u4ef6\u9700\u6c42\u89c4\u683c\u8bf4\u660e\u4e66(SRS)") },
      footers: { default: pageFooter() },
      children },
  ],
});

Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync("docs/\u667a\u95ee\u6821\u56edCampusMind-SRS\u9700\u6c42\u89c4\u683c\u8bf4\u660e\u4e66.docx", buf);
  console.log("SRS docx written");
});
