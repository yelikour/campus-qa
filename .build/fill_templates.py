# -*- coding: utf-8 -*-
"""按课程模板(03/)批量生成智问校园 CampusMind 的课程交付物,输出至 docs/课程交付物/。
填充策略:模板跟随(Template-Following)——保留模板结构与样式,替换占位段/标题/表格。
"""
import copy
import shutil
from pathlib import Path

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import RGBColor
from docx.text.paragraph import Paragraph

SRC = Path(r"G:/SHU/2601/软件体系结构/03")
DST = Path(__file__).resolve().parent.parent / "docs" / "课程交付物"
DST.mkdir(parents=True, exist_ok=True)

PROJECT = "智问校园CampusMind"
TEAM = "王若璋 / 何俐 / 郭祚梁"


def is_heading(p):
    return p.style.name.startswith(("Heading", "标题")) or p.style.name == "Title"


def is_placeholder(p):
    t = p.text.strip()
    if not t:
        return False
    if p.style.name == "InfoBlue":
        return True
    return p.style.name.startswith("Normal") and t.startswith("[")


def set_text(p, text, normalize=True):
    runs = p.runs
    if not runs:
        p.add_run(text)
        return
    runs[0].text = text
    for r in runs[1:]:
        r._r.getparent().remove(r._r)
    if normalize:
        runs[0].font.italic = False
        try:
            runs[0].font.color.rgb = RGBColor(0, 0, 0)
        except Exception:
            pass


def find_heading(doc, text, style_pref=("Heading",)):
    for p in doc.paragraphs:
        if is_heading(p) and p.style.name.startswith(style_pref) and text in p.text:
            return p
    return None


def find_any(doc, text):
    for p in doc.paragraphs:
        if text in p.text:
            return p
    return None


def remove_notes(doc):
    """删除模板说明性 [注:...] 段。"""
    for p in list(doc.paragraphs):
        if p.text.strip().startswith("[注：") or p.text.strip().startswith("[注:"):
            p._p.getparent().remove(p._p)


def strip_instructions(doc):
    """收尾清扫:删除所有仍以 [ 开头的 InfoBlue 模板说明段(未填充的指令)。"""
    n = 0
    for p in list(doc.paragraphs):
        if p.style.name == "InfoBlue" and p.text.strip().startswith("["):
            p._p.getparent().remove(p._p)
            n += 1
    if n:
        print(f"    stripped {n} instruction paragraphs")


def fill_section(doc, heading_text, lines, insert_if_missing=True):
    """在标题下填充内容:吃掉模板占位段,写入 lines(首段复用占位样式位置)。"""
    h = find_heading(doc, heading_text)
    if h is None:
        print(f"  !! heading not found: {heading_text}")
        return
    # 收集占位段(到下一个标题为止)
    body = list(h._p.itersiblings(qn("w:p")))
    paras = [Paragraph(el, h._parent) for el in body]
    placeholders, stop = [], False
    for p in paras:
        if is_heading(p):
            break
        if is_placeholder(p):
            placeholders.append(p)
    anchor = h
    if placeholders:
        set_text(placeholders[0], lines[0])
        anchor = placeholders[0]
        for p in placeholders[1:]:
            p._p.getparent().remove(p._p)
        rest = lines[1:]
    else:
        rest = lines
    for line in reversed(rest):
        new_p = OxmlElement("w:p")
        anchor._p.addnext(new_p)
        para = Paragraph(new_p, h._parent)
        para.style = "Normal"
        para.add_run(line)
    return


def rename_heading(doc, old, new):
    """重命名正文中的 Heading(优先),并同步目录行(如有)。"""
    hit = None
    for p in doc.paragraphs:
        if old in p.text:
            if is_heading(p):
                hit = p
                break
            if hit is None and p.style.name.startswith("toc"):
                hit = p  # 暂存 toc 行,若找到正文标题则一并改
    if hit is None:
        print(f"  !! rename target not found: {old}")
        return
    set_text(hit, new, normalize=False)
    # 同步另一处(toc 或正文)
    for p in doc.paragraphs:
        if p is not hit and old in p.text:
            set_text(p, new.replace("规约", "规约") if False else new, normalize=False)
            break


def fill_title(doc, revision_desc="按课程模板填写项目实际内容"):
    for p in doc.paragraphs:
        if p.style.name == "Title":
            if "<项目名称>" in p.text or "<项目名>" in p.text:
                set_text(p, PROJECT, normalize=False)
            elif "版本" in p.text:
                set_text(p, "版本 1.0(2026-10-16)", normalize=False)
    # 修订历史表
    if doc.tables:
        t = doc.tables[0]
        hdr = [c.text.strip() for c in t.rows[0].cells]
        if "版本" in "".join(hdr):
            row = t.rows[1]
            vals = ["2026-10-16", "1.0", revision_desc, "全体成员"]
            for c, v in zip(row.cells, vals):
                if not c.text.strip():
                    pass
            for i, v in enumerate(vals):
                if i < len(row.cells):
                    set_text(Paragraph(row.cells[i].paragraphs[0]._p, row.cells[i].paragraphs[0]._parent) if False else row.cells[i].paragraphs[0], v)


def set_cell(table, r, c, text):
    cell = table.rows[r].cells[c]
    p = cell.paragraphs[0]
    set_text(p, text, normalize=False)
    for extra in cell.paragraphs[1:]:
        if not extra.text.strip():
            continue


# ================================================================ 1 软件项目计划
def build_plan():
    doc = Document(SRC / "软件项目计划.docx")
    remove_notes(doc)
    fill_title(doc)
    fill_section(doc, "目的", [
        "本计划确定「智问校园 CampusMind」校园智能问答系统的项目目标、组织分工、迭代安排、风险对策与质量保证活动,作为团队 8 周开发过程的基线文件。",
    ])
    fill_section(doc, "范围", [
        "本计划覆盖项目立项至交付的全过程:需求(Vision/SRS)、架构与设计(SDD+SAD)、编码实现(后端 FastAPI + 原生前端 SPA)、测试(单元/评测/验收/基准)与课程交付物制作;不涉及教务等业务系统对接。",
    ])
    fill_section(doc, "定义、首字母缩写词和缩略语", [
        "RAG:检索增强生成;BM25:稀疏关键词排序;RRF:倒数排名融合;SSE:服务端事件流;MVP:最小可行产品;ADR:架构决策记录。",
    ])
    fill_section(doc, "参考资料", [
        "《软件体系结构》课程任务说明;GB/T 9385 软件需求规格说明规范;项目仓库 docs/ 下 SRS、设计与架构文档、追踪矩阵与复现指南。",
    ])
    fill_section(doc, "项目的目的、规模和目标", [
        "目标:8 周交付一套面向在校学生的校园事务智能问答系统——口语化提问、流式回答、强制引用溯源、无知识不编造;演示环境零外部依赖离线可运行。",
        "规模:3 人团队;后端约 1,000 行、前端约 530 行(不含注释与空行);知识语料 59 篇文档 / 136 检索块。",
        "质量目标:检索 Hit@3 ≥ 95%、架构验收 4/4 通过、端到端 40 QPS 以上且零失败。",
    ])
    fill_section(doc, "假设与约束", [
        "约束:课程周期 8 周(2026 春季学期);演示必须零 API Key 离线可跑;云端大模型与语义向量按真实收费价核算成本;数据不出校(可选私有化)。",
        "假设:知识语料由人工维护且规模在数百篇以内;校园演示规模单机部署即可满足,高并发按三级扩展方案演进。",
    ])
    fill_section(doc, "项目的可交付成果", [
        "代码:github.com/yelikour/campus-qa(FastAPI 后端、原生 SPA、评测/验收/基准脚本、14 项单元测试)。",
        "文档:Vision 文档、软件项目计划、迭代计划、软件需求规约、软件架构文档、UI 原型、SRS 需求规格说明书、设计与架构文档(SDD+SAD)、系统测试用例与测试报告、项目总结报告、架构设计文档(22 页)、经济适用型与运营方案。",
        "演示材料:项目讲解 PPT(22 页)、答辩 PPT(21 页)、演示录屏与讲解视频;证据:评测/基准/验收实测产物 artifacts/。",
    ])
    fill_section(doc, "项目组织", [
        "王若璋(组长):总体架构、RAG 检索引擎(双通道/RRF/热更新)、项目管理与迭代推进。",
        "何俐:前端三视图与 SSE 流式渲染、界面原型、系统测试(用例/报告)。",
        "郭祚梁:需求与 Vision、评测矩阵与基准、文档交付物、运营方案测算。",
        "协作:GitHub 仓库统一版本管理;每周例会同步进展与风险。",
    ])
    # 风险表
    t = doc.tables[1]
    risks = [
        ("1", "云端大模型服务不可用/超时", "依赖外部 API,网络或配额异常将中断回答", "Provider 插件化 + 本地抽取式兜底;流内熔断降级并落日志(验收 A1)"),
        ("2", "口语化提问检索不准", "词面差异导致召回失败,回答质量下降", "双通道混合检索 + 同义词标签;62 条口语化评测集驱动修复与标定"),
        ("3", "课程周期内范围失控", "8 周内功能贪多导致核心链路质量不足", "MVP 分级:先问答主链路后管理/看板;每迭代可运行可演示"),
        ("4", "知识数据口径错误", "错误答案带引用比不回答更伤可信性", "来源字段强制;全有或全无阈值;答案仅从校内语料抽取"),
        ("5", "多人协作接口冲突", "前后端并行开发时接口不一致", "API 契约先行(端点/错误码固化);分包边界清晰,互不阻塞"),
    ]
    for i, row in enumerate(risks):
        for j, v in enumerate(row):
            set_cell(t, i + 1, j, v)
    fill_section(doc, "风险分析", ["按优先级排序的前五项风险及缓解措施如下表(风险表)。"])
    fill_section(doc, "方法和工具", [
        "过程:迭代式(RUP 裁剪),四轮迭代,每轮产出可运行版本;评测驱动开发(指标异常 → 定位修复 → 回归)。",
        "工具:Python 3.12 + FastAPI + uvicorn;jieba、httpx;pytest;jieba 分词;Git/GitHub;VS Code;matplotlib(图表)。",
    ])
    fill_section(doc, "开发计划", [
        "迭代一(第 1-2 周)探索与愿景:需求访谈、Vision、技术验证(jieba/BM25/SSE 原型)。",
        "迭代二(第 3-4 周)核心链路:双通道检索 + RRF 融合 + 流式生成 + 引用溯源;评测集建立。",
        "迭代三(第 5-6 周)管理与看板:知识库管理热更新、会话历史、运行看板;限流与降级。",
        "迭代四(第 7-8 周)加固与交付:性能基准、四项架构验收、安全加固(2026-10 完善轮 9 项缺陷修复)、文档与演示材料。",
        "详细任务分配见《迭代计划》。",
    ])
    fill_section(doc, "质量保证计划", [
        "单元测试:pytest 14 项(冒烟 4 + 回归 10,含会话隔离);检索评测:62 条口语化改写四路对比(Hit@1/Hit@3/MRR);性能基准:retrieval-only 与 E2E 拆分(p50/p95/p99/QPS/失败数);架构验收:降级/限流/热更新/无知识兜底四项脚本化验收;全部指标一条命令可复现(docs/REPRODUCIBILITY.md)。",
    ])
    fill_section(doc, "项目沟通计划", [
        "每周固定例会(进展/风险/下周计划);GitHub Issue 与提交记录留痕;课程节点(开题/中期/答辩)前增加评审会。",
    ])
    fill_section(doc, "培训计划", [
        "第 1 周内完成:RAG 与 SSE 基础概念对齐、FastAPI/jieba 快速上手;不需要外部付费培训。",
    ])
    fill_section(doc, "附录", [
        "课程模板:软件项目计划/Vision/需求规约/架构文档/迭代计划/测试用例/测试报告/项目总结;参考资料:11_软件工程标准与文档。",
    ])
    strip_instructions(doc)
    doc.save(DST / "软件项目计划.docx")
    print("软件项目计划.docx OK")


# ================================================================ 2 Vision
def build_vision():
    doc = Document(SRC / "Vision文档(1).docx")
    remove_notes(doc)
    fill_title(doc)
    fill_section(doc, "目的", ["本文档定义 CampusMind 的产品前景:目标用户、核心问题、产品定位与关键特性,为需求与迭代优先级提供决策依据。"])
    fill_section(doc, "范围", ["覆盖产品定位、涉众与用户分析、产品概述与特性、约束与质量范围;不包含具体技术实现(见架构文档)。"])
    fill_section(doc, "定义、首字母缩写词和缩略语", ["RAG:检索增强生成;MVP:最小可行产品;SSE:服务端事件流;Hit@K:检索前 K 命中率。"])
    fill_section(doc, "参考资料", ["需求访谈记录(同学 12 人);《经济适用型与运营方案》;课程材料:基于产品的软件开发(SCAMPER 与 MVP)。"])
    fill_section(doc, "商机", [
        "校园事务咨询是高频刚需:规章散落在官网、公众号与口头传播中,口径不一且难以溯源;通用大模型缺少校内语料,极易编造。一个「回答必带校内出处、没有就说没有」的智能问答入口,能同时服务学生(答疑)、管理员(知识治理)与学校(数字化形象)。",
    ])
    fill_section(doc, "问题说明", [
        "学生视角:找不到(信息分散)、不敢信(口径矛盾/无出处)、问不了(通用 AI 编造)。管理员视角:知识更新难触达、错漏难发现。解决思路:以校内知识语料为唯一答案来源,检索增强生成 + 强制引用溯源。",
    ])
    fill_section(doc, "产品定位说明", [
        "面向在校学生的校园事务智能问答系统:自然语言提问,流式回答并标注校内信息来源与双通道检索排名;面向管理员的轻量知识治理入口(录入即生效)。对学校:零成本起步(免费社区版形态)、可按 SaaS/私有化扩展。",
    ])
    fill_section(doc, "市场统计", [
        "以万人规模在校高校为例:假设日均 5,000 次提问、每问约 1.3k token,云端托管月成本约 ¥210-230(真实收费价核算);单实例实测 42-44 QPS,余量 10 倍以上。定价假设:SaaS ¥4,999/校/年,私有化买断与免费社区版并行(详见运营方案)。",
    ])
    fill_section(doc, "涉众概要", [
        "学生(最终用户,价值:快速可信答疑);知识库管理员(内容维护者,价值:录入即生效);课程教师(评审者,价值:架构与质量证据);学校信息化部门(潜在客户,价值:低成本数字化服务)。",
    ])
    fill_section(doc, "用户概要", [
        "在校学生:移动/桌面浏览器,口语化提问,不关心实现,核心诉求「快、准、有出处」。管理员:维护分类与来源,要求操作可逆、生效即时。运维:看板观察命中率与时延,要求指标可复现。",
    ])
    fill_section(doc, "关键的涉众/用户需要", [
        "N1 回答可信:每条回答标注校内来源(学生/教师);N2 无知识诚实回退,不编造(全体);N3 响应快:首字即时、检索毫秒级(学生);N4 知识录入免重启生效(管理员);N5 运行状态可见:引擎/命中率/时延(运维);N6 成本可控:免费起步、按量透明(学校)。",
    ])
    rename_heading(doc, "<一个竞争对手>", "竞争对手一:通用大模型对话产品(ChatGPT 类)")
    fill_section(doc, "竞争对手一", [
        "优势:语言能力强、知识面广;劣势:无校内语料,校园事务答案不可信、无出处,且数据出校。差异化:CampusMind 以校内知识库为唯一答案来源,强制引用溯源,无命中即回退。",
    ])
    rename_heading(doc, "<另一个竞争对手>", "竞争对手二:校内官网/公众号站内检索")
    fill_section(doc, "竞争对手二", [
        "优势:内容权威;劣势:关键词检索、层级深、无问答能力、多入口分散。差异化:自然语言口语化提问,一站式覆盖教务/图书馆/宿舍/卡务/奖助等分类。",
    ])
    fill_section(doc, "产品总体效果", [
        "Web 应用三视图:智能问答(默认,流式回答+引用卡片)、知识库管理(分页/筛选/录入/删除,热更新)、运行看板(命中率/时延/热点分类)。后端 FastAPI + RAG 引擎,演示零依赖,可配置云端大模型与语义向量。",
    ])
    fill_section(doc, "功能摘要", [
        "口语化问答与引用溯源;SSE 流式输出;多轮会话与历史;知识库管理与热更新(版本递增);运行看板;无知识诚实回退;入口限流与生成降级。",
    ])
    fill_section(doc, "假设与依赖关系", [
        "假设知识语料人工维护、规模数百篇以内;依赖(可选)智谱 GLM 与 embedding-3 API;演示形态不依赖任何外部服务。",
    ])
    rename_heading(doc, "<一个特性>", "特性一:可信问答(引用溯源 + 无知识兜底)")
    fill_section(doc, "特性一", [
        "双通道混合检索(BM25 ∥ 向量)+ RRF 融合;回答附来源、分类、双通道排名;检索与查询零交集时返回引导话术且不带引用(sources=0)。收益:回答可验证,杜绝编造。",
    ])
    rename_heading(doc, "<另一个特性>", "特性二:知识热更新与运行可观察")
    fill_section(doc, "特性二", [
        "管理员录入/删除条目后索引免重启即时重建,版本号递增并在前端可见;看板聚合命中率/时延/热点分类;引擎信息如实展示(含「TF-IDF 非语义嵌入」标注)。收益:内容治理闭环、状态透明。",
    ])
    fill_section(doc, "约束", [
        "课程 8 周周期与 3 人人力;演示零 API Key 离线可跑;输出全量转义与可选写接口鉴权;云端成本按真实收费价核算。",
    ])
    fill_section(doc, "质量范围", [
        "性能:检索 p95 < 50ms(实测 1.8-3.2ms);可用性:云端故障自动降级;安全性:单用户限流、写接口可鉴权;可修改性:Provider 插件化;可测试性:指标全脚本复现。",
    ])
    fill_section(doc, "优先级", [
        "P0 问答主链路与引用溯源;P1 无知识兜底、限流降级;P2 知识管理与看板;P3 重排实验、云端语义向量接入。",
    ])
    fill_section(doc, "适用的标准", ["HTTP/SSE 通信;JSON 数据交换;UTF-8 编码;RESTful API 风格。"])
    fill_section(doc, "系统需求", ["服务端 Python 3.10+;客户端现代浏览器;可选智谱开放平台 API。"])
    fill_section(doc, "环境需求", ["开发/演示:单机;生产:Nginx 反代 + uvicorn 多实例,SQLite 起步可换 PostgreSQL。"])
    fill_section(doc, "用户手册", ["README 快速开始与复现指南(docs/REPRODUCIBILITY.md)即用户手册。"])
    fill_section(doc, "联机帮助", ["界面内置快捷问题与引导话术;管理操作即时提示(新增条数/索引版本)。"])
    fill_section(doc, "安装指南、配置文件、自述文件", [
        "README 含安装(venv + pip)、启动(uvicorn)与全部环境变量说明(ZHIPUAI_API_KEY / RERANK_ENABLED / ADMIN_TOKEN 等)。",
    ])
    strip_instructions(doc)
    doc.save(DST / "Vision文档.docx")
    print("Vision文档.docx OK")


# ================================================================ 3 软件需求规约
def build_srs():
    doc = Document(SRC / "软件需求规约(1).docx")
    remove_notes(doc)
    fill_title(doc)
    fill_section(doc, "目的", ["本规约定义 CampusMind 的外部行为:功能需求以用例规约表述,非功能需求覆盖易用性/可靠性/性能/可支持性/约束/接口,作为开发与测试验收依据。"])
    fill_section(doc, "定义、首字母缩写词和缩略语", ["RAG:检索增强生成;BM25/RRF/SSE:见术语表;Hit@K:前 K 命中率;FR/NFR:功能/非功能需求编号。"])
    fill_section(doc, "参考资料", ["《SRS 需求规格说明书(详细版)》docs/;Vision 文档;追踪矩阵 docs/traceability.md。"])
    fill_section(doc, "整体说明", [
        "系统面向在校学生提供校园事务智能问答:知识语料为唯一答案来源,回答强制引用溯源;含知识库管理与运行看板。用户类别、运行环境与总体约束见《软件项目计划》第 2 章与 Vision 文档。",
    ])
    rename_heading(doc, "<Use case 图>", "用例总览")
    fill_section(doc, "用例总览", [
        "UC1 智能问答(含引用溯源与流式输出)——学生;UC2 知识库管理与热更新——管理员;UC3 会话与历史管理——学生;UC4 运行看板——运维。",
        "关系:UC1 与 UC3 包含关系(回答归档至会话);UC2 的「录入/删除」扩展 UC1 的知识来源;无知识兜底是 UC1 的替代流。",
    ])
    rename_heading(doc, "<Use case1 规约>", "UC1 智能问答规约")
    fill_section(doc, "UC1 智能问答规约", [
        "参与者:学生(主)、计时计费系统(辅,云端模式)。",
        "前置:服务在线;知识索引就绪。",
        "主流程:学生提交问题(≤500 字)→ 系统双通道检索并 RRF 融合 → meta 事件先推引用来源 → 流式生成回答(delta)→ 完成事件携带总耗时 → 回答与引用卡片渲染。",
        "替代流:无相关知识(候选与查询零交集)→ 引导话术,不带引用;触发限流 → 429 提示;云端生成异常 → 流内降级本地抽取式并如实标注引擎。",
        "后置:消息与引用快照落库;查询日志记录命中/时延/分类。",
        "验收:Hit@3 98.4%(62 条评测);E2E 42-44 QPS、p99<800ms、0 失败;验收 A1/A4 PASS。",
    ])
    rename_heading(doc, "<Use case2 规约>", "UC2 知识库管理与热更新规约")
    fill_section(doc, "UC2 知识库管理与热更新规约", [
        "参与者:管理员(主)。",
        "前置:进入知识库管理视图;启用鉴权时持有管理令牌。",
        "主流程:检索/筛选条目 → 录入(问法/答案/分类/来源/标签)→ 服务端统一文件锁内追加语料并重建索引 → 版本号递增 → 新知识即时可检索命中。",
        "替代流:删除条目(同样触发热重建);删除不存在条目 → 404;未授权写入 → 401。",
        "后置:语料文件与内存索引一致;前端提示新增条数与索引版本。",
        "验收:A3 热更新 PASS(录入即命中、版本 1→2、验后清理)。",
    ])
    # 追加 UC3/UC4
    h = find_heading(doc, "UC2 知识库管理与热更新规约")
    if h is not None:
        anchor = h
        for title, lines in [
            ("UC3 会话与历史管理规约", [
                "参与者:学生。主流程:首次提问自动创建会话;侧栏按最近活跃列出历史;点击恢复完整对话(含引用)。替代流:删除会话级联删除消息;他人令牌访问会话 → 404(属主校验,F10)。验收:刷新后历史完整恢复;越权读删被拒(单元+HTTP 手验)。",
            ]),
            ("UC4 运行看板规约", [
                "参与者:运维/教师。主流程:进入看板 → 展示累计提问/命中率/平均时延/会话与索引块数/热点分类 → 手动刷新。验收:统计与数据库口径一致;引擎信息如实显示当前 Provider。",
            ]),
        ]:
            np = OxmlElement("w:p"); anchor._p.addnext(np)
            para = Paragraph(np, anchor._parent); para.style = h.style
            para.add_run(title)
            anchor2 = para
            for line in lines:
                np2 = OxmlElement("w:p"); anchor2._p.addnext(np2)
                p2 = Paragraph(np2, anchor._parent); p2.style = "Normal"; p2.add_run(line)
                anchor2 = p2
            anchor = anchor2
    rename_heading(doc, "<易用性需求一>", "易用性需求:口语化提问与即时反馈")
    fill_section(doc, "易用性需求:口语化提问与即时反馈", [
        "支持口语化问法(快捷问题一键代填);回答流式打字机输出且引用来源先于正文出现;界面三视图一键切换。验收:课程演示与录屏验证。",
    ])
    rename_heading(doc, "<可靠性需求一>", "可靠性需求:降级与诚实回退")
    fill_section(doc, "可靠性需求:降级与诚实回退", [
        "云端生成异常自动流内回退本地抽取式,服务不中断(A1 PASS,139 字正解);无知识时诚实回退不编造(A4 PASS,sources=0);限流精确放行/拒绝(A2 PASS,200×10+429×5)。",
    ])
    rename_heading(doc, "<性能需求一>", "性能需求:检索与端到端时延")
    fill_section(doc, "性能需求:检索与端到端时延", [
        "检索 p95 < 50ms(实测 RRF 链路 1.8-3.2ms,515.8-880.4 QPS);E2E 并发 20 下 42-44 QPS、p99 727-761ms、0 失败(bench.py)。",
    ])
    rename_heading(doc, "<可支持性需求一>", "可支持性需求:Provider 插件化与配置化")
    fill_section(doc, "可支持性需求:Provider 插件化与配置化", [
        "生成端与向量端同类可替换,环境变量切换(无 Key 离线/有 Key 云端);重排为实验开关;全部指标脚本可复现(pytest 14 项 + 评测/基准/验收)。",
    ])
    rename_heading(doc, "<设计约束一>", "设计约束:零依赖离线与如实展示")
    fill_section(doc, "设计约束:零依赖离线与如实展示", [
        "演示环境不得依赖外部 API;向量通道为 TF-IDF 时必须在前端与统计接口明示;输出全量转义,写接口支持 ADMIN_TOKEN 鉴权。",
    ])
    fill_section(doc, "联机用户文档和帮助系统需求", ["界面内置引导话术与快捷问题;README 与复现指南充当联机文档。"])
    fill_section(doc, "用户界面", ["见《UI 原型》交付物:三视图、引用卡片、状态设计(限流/兜底/鉴权/降级)与设计规范。"])
    fill_section(doc, "硬件接口", ["无专用硬件接口;标准 x86/ARM 服务器或个人电脑即可运行。"])
    fill_section(doc, "软件接口", ["HTTP REST API(/api/chat、/api/knowledge、/api/conversations、/api/admin);可选智谱 GLM 与 embedding-3(openai 兼容协议)。"])
    fill_section(doc, "通信接口", ["HTTP/1.1 + SSE(流式回答);生产经 Nginx 反代(proxy_buffering off 保 SSE 直通)。"])
    fill_section(doc, "适用的标准", ["UTF-8;JSON;REST 风格;GB/T 9385 需求规约编写规范。"])
    strip_instructions(doc)
    doc.save(DST / "软件需求规约.docx")
    print("软件需求规约.docx OK")


# ================================================================ 4 软件架构文档
def build_arch():
    doc = Document(SRC / "软件架构文档.docx")
    remove_notes(doc)
    fill_title(doc)
    fill_section(doc, "目的", ["本文档以多视图方式描述 CampusMind 的软件架构:用例/逻辑/进程/部署/实现/技术/数据视图、核心算法与质量属性设计;与《设计与架构文档(SDD+SAD)》互为详略版本。"])
    fill_section(doc, "参考资料", ["《设计与架构文档(SDD+SAD)》;《SRS 需求规格说明书》;追踪矩阵;架构图 docs/assets/。"])
    fill_section(doc, "用例视图", [
        "核心用例:UC1 智能问答(引用溯源/流式/无知识兜底)、UC2 知识库管理与热更新、UC3 会话历史、UC4 运行看板。一次问答贯穿全部视图:提问 → 限流校验 → 双通道检索 → RRF 融合 → SSE 流式生成 → 引用渲染与落库(时序图见 docs/assets/arch_sequence.png)。",
    ])
    fill_section(doc, "概述", [
        "分层风格的模块化单体:接入(前端 SPA)→ 网关边界(限流/鉴权)→ 应用服务(四组 API)→ RAG 引擎(检索/融合/生成)→ 数据(SQLite/JSON 语料/内存索引);依赖单向,以分包边界预留服务化拆分点(ADR-1)。",
    ])
    fill_section(doc, "在构架方面具有重要意义的设计包", [
        "services/retrieval.py:HybridRetriever 聚合 BM25Index(倒排)、VectorIndex(TF-IDF/embedding-3)、fuse_rrf(标准 RRF)、LightweightReranker(实验开关)——检索质量的核心。",
        "services/generation.py:GeneratorProvider 抽象,本地抽取式与智谱 GLM 双实现,异常流内熔断降级(可用性核心)。",
        "services/ingestion.py:统一文件锁的语料摄取、q/a 双通道分块与热重建(可修改性核心)。",
        "core/security.py:有界令牌桶限流 + ADMIN_TOKEN 写鉴权;repository/db.py:仓储模式隔离 SQL(可扩展性核心)。",
    ])
    fill_section(doc, "进程视图", [
        "单进程 asyncio 事件循环:chat 以异步生成器推送 SSE,不阻塞其它请求;并发控制为按用户令牌桶(5 QPS/突发 10,桶字典 ≤1 万、最久未活跃淘汰);热更新持文件锁串行化「读语料-写文件-重建索引」;SQLite 线程局部连接 + WAL。",
    ])
    fill_section(doc, "部署视图", [
        "演示:浏览器 → uvicorn(127.0.0.1:8000,同源托管前端)。生产:浏览器 → Nginx(TLS 终止/静态直出/反代 /api,SSE 直通)→ uvicorn 多实例 → SQLite/JSON(可外置 PG/向量库);外部服务:智谱 GLM 与 embedding-3(可选,异常降级)。扩展三级:workers → 多实例 → Redis 限流(图见 docs/assets/arch_deploy.png)。",
    ])
    fill_section(doc, "实现视图", [
        "backend/app 四分包(api/services/repository/core,依赖单向);frontend 三文件原生 SPA;scripts 评测工具链(eval_matrix/bench/acceptance);tests 13 项;.build 承载文档与 PPT 构建脚本,全部可一键复现。",
    ])
    fill_section(doc, "技术视图", [
        "Python 3.10+/FastAPI/uvicorn;jieba 分词;httpx;pytest;原生 JS。技术选型动机:FastAPI 原生 async 承载 SSE;自实现 BM25/RRF 保证算法可解释、可评测、零模型依赖。",
    ])
    fill_section(doc, "数据视图（可选）", [
        "关系数据:conversation(会话)1→N message(消息,含引用快照);query_log 独立追加支撑看板。文档数据:campus_qa.json(59 篇)摄取为 136 个双通道 chunk(question 通道管问法、answer 通道按 3 句滑窗管覆盖,doc_id 关联溯源)。内存索引:BM25 倒排 + 向量矩阵,版本递增热重建。演进:仓储模式接口不变,SQLite → PostgreSQL。",
    ])
    fill_section(doc, "核心算法设计（可选）", [
        "BM25:自实现 k1=1.5/b=0.75,jieba 分词 + 停用词过滤,倒排索引(与暴力扫描逐位等价,10-35 倍吞吐)。",
        "RRF 融合:score(d)=Σ 1/(RRF_K+rank),K=60,对排名融合免归一化(完善轮 F1 修正为标准公式);文档级去重与无知识硬零兜底。",
        "重排(实验):特征化词面重排,实测无收益默认关闭(RERANK_ENABLED);兜底阈值 MIN_RELEVANCE=0.08 由 62 条评测标定。",
    ])
    fill_section(doc, "质量属性的设计", [
        "性能:双通道倒排 + 融合编排,检索 p50 1.1-1.9ms;可用性:Provider 熔断降级 + 本地兜底;安全:限流/写鉴权/全量转义/会话属主校验(F10);可修改性:双端 Provider 插件化(ADR-4/7);可测试性:评测/基准/验收/单测(14 项)四层脚本化;可扩展性:应用无状态,三级水平扩展。",
    ])
    strip_instructions(doc)
    doc.save(DST / "软件架构文档.docx")
    print("软件架构文档.docx OK")


# ================================================================ 5 迭代计划
def build_iterations():
    doc = Document(SRC / "迭代计划.docx")
    t = doc.tables[0]
    iters = [
        ("迭代一 探索与愿景", "第 1-2 周",
         "任务与人员分配:\n"
         "· 需求访谈与痛点梳理(全员;郭祚梁牵头)→ Vision 文档\n"
         "· 技术验证:jieba 分词/BM25 原型、SSE 流式打通(王若璋)\n"
         "· 界面草图与交互设计(何俐)\n"
         "里程碑:技术选型确定,问答最小原型可演示\n风险:口语化检索不准 → 建立评测集基线"),
        ("迭代二 核心链路", "第 3-4 周",
         "· 双通道检索 + RRF 融合 + 文档级去重(王若璋)\n"
         "· 流式生成与引用卡片渲染(何俐)\n"
         "· 62 条口语化评测集建立与首轮评测(郭祚梁)\n"
         "里程碑:问答主链路可用,评测指标进入基线\n风险:重排无收益 → 降级为实验开关"),
        ("迭代三 管理与看板", "第 5-6 周",
         "· 知识库管理与热更新(王若璋/何俐)\n"
         "· 会话历史与运行看板(何俐)\n"
         "· 限流与生成降级;测试用例编写(郭祚梁)\n"
         "里程碑:三视图完整,验收 A1-A4 全通\n风险:接口冲突 → 契约先行冻结"),
        ("迭代四 加固与交付", "第 7-8 周",
         "· 性能基准与容量测算(郭祚梁)\n"
         "· 安全加固与二轮调研修复 9 项缺陷(王若璋)\n"
         "· 文档/PPT/录屏等交付物制作(全员)\n"
         "里程碑:13 项测试全绿,交付物齐备\n风险:工期挤压 → 按 MVP 优先级裁剪"),
    ]
    # 首表填迭代一,其余克隆
    tables_parent = t._tbl.getparent()
    anchor_el = t._tbl
    cloned = []
    for i in range(1, 4):
        new_tbl = copy.deepcopy(t._tbl)
        anchor_el.addnext(new_tbl)
        cloned.append(new_tbl)
        anchor_el = new_tbl
    all_tables = [t] + [DocumentPartTable(nt) for nt in cloned] if False else None
    # 用 doc 重新读取克隆表(简单方式:直接操作 XML 后重开)
    doc.save(DST / "迭代计划.docx")
    # 重新打开填写(克隆表已在文档中)
    doc2 = Document(DST / "迭代计划.docx")
    for idx, tbl in enumerate(doc2.tables):
        if idx >= len(iters):
            break
        name, dates, tasks = iters[idx]
        # 行结构: 0 组号/项目名 1 迭代名/起止 2 任务(合并)
        cells = tbl.rows[0].cells
        set_cell(tbl, 0, 1, "3"); set_cell(tbl, 0, 3, PROJECT)
        set_cell(tbl, 1, 1, name); set_cell(tbl, 1, 3, dates)
        task_cell = tbl.rows[2].cells[0]
        set_text(task_cell.paragraphs[0], tasks, normalize=False)
    # 顶部制定日期
    for p in doc2.paragraphs:
        if "制定日期" in p.text:
            set_text(p, "制定日期:2026 年春季学期(迭代一启动前)", normalize=False)
            break
    doc2.save(DST / "迭代计划.docx")
    print("迭代计划.docx OK")


class DocumentPartTable:
    pass


# ================================================================ 6 系统测试用例 xlsx
def build_testcases():
    from openpyxl import load_workbook
    wb = load_workbook(SRC / "系统测试用例.xlsx")
    info = wb["Information"]
    for row in info.iter_rows():
        for cell in row:
            v = str(cell.value or "")
            if "Project Nam" in v or v.strip() == "XXXXXX":
                pass
    # 简单替换:项目名称行下方的 XXXXXX 与文档编号
    for row in info.iter_rows():
        for cell in row:
            if cell.value == "XXXXXX":
                cell.value = PROJECT
    ws = wb["Test Cases"]
    cases = [
        ("CM-testcase-001", "智能问答", "功能测试", "提问命中知识库并返回带引用的流式回答", "高",
         "服务在线,索引就绪", "问题:图书馆开放时间是几点?",
         "1.POST /api/chat 提交问题 2.解析 SSE 事件流",
         "meta 先推引用来源;回答含开放时间;引用卡片含双通道排名", "同预期", "Y", "Null(无缺陷)", "验收与评测联动"),
        ("CM-testcase-002", "智能问答", "功能测试", "无知识问题触发诚实回退且不带引用", "高",
         "服务在线", "问题:今天股票行情怎么样",
         "1.提交与知识库无关的问题 2.检查 meta 与回答",
         "sources=0;回答为引导话术,不编造", "同预期", "Y", "Null(无缺陷)", "验收 A4"),
        ("CM-testcase-003", "智能问答", "功能测试", "SSE 流式输出与打字机渲染", "中",
         "前端页面已打开", "任意命中问题",
         "1.发送问题 2.观察回答逐字渲染与引用先现",
         "delta 增量推送;引用先于正文;done 携带耗时", "同预期", "Y", "Null(无缺陷)", ""),
        ("CM-testcase-004", "入口限流", "可靠性测试", "单用户突发 15 请求被令牌桶精确限流", "高",
         "服务在线", "同一用户并发 15 次提问",
         "1.并发提交 15 次 2.统计状态码",
         "200×10 + 429×5", "同预期", "Y", "Null(无缺陷)", "验收 A2"),
        ("CM-testcase-005", "知识库管理", "功能测试", "新增条目热更新即时命中且版本递增", "高",
         "管理员视图可用", "录入校史馆预约条目",
         "1.POST /api/knowledge 2.立即检索该问题 3.验后删除",
         "索引版本+1;新条目即时可检索与回答;清理后不再命中", "同预期", "Y", "Null(无缺陷)", "验收 A3"),
        ("CM-testcase-006", "知识库管理", "功能测试", "删除不存在的条目返回 404", "低",
         "服务在线", "不存在的 doc_id",
         "1.DELETE /api/knowledge/{id}",
         "404 与错误说明", "同预期", "Y", "Null(无缺陷)", ""),
        ("CM-testcase-007", "知识库管理", "安全测试", "未授权写知识库被 401 拒绝", "高",
         "已设置 ADMIN_TOKEN", "无令牌/错令牌提交新增",
         "1.不带 X-Admin-Token 提交 2.带错误令牌提交 3.带正确令牌提交",
         "前两者 401;正确令牌 200", "同预期", "Y", "Null(无缺陷)", "完善轮 F4"),
        ("CM-testcase-008", "会话历史", "功能测试", "会话列表与历史恢复完整", "中",
         "存在历史会话", "刷新页面后操作",
         "1.查看侧栏会话列表 2.点击恢复",
         "列表按活跃排序;对话与引用快照完整恢复", "同预期", "Y", "Null(无缺陷)", ""),
        ("CM-testcase-009", "运行看板", "功能测试", "调试检索接口返回双通道真实排名", "中",
         "服务在线", "q=图书馆开放时间",
         "1.GET /api/knowledge/search 2.核对排名字段",
         "bm25_rank/vec_rank 与命中通道一致,未命中通道为空", "同预期", "Y", "Null(无缺陷)", "完善轮 F2"),
        ("CM-testcase-010", "性能基准", "性能测试", "retrieval-only 吞吐与时延达标", "高",
         "服务在线", "300 次检索请求",
         "1.python scripts/bench.py retrieval",
         "515.8-880.4 QPS;p50 1.1-1.9ms;0 失败", "同预期", "Y", "Null(无缺陷)", "修正口径 F9"),
        ("CM-testcase-011", "性能基准", "性能测试", "E2E 并发 20 吞吐与时延达标", "高",
         "服务在线", "200 次并发 20 请求",
         "1.python scripts/bench.py e2e",
         "42.1-43.3 QPS;p99 727-761ms;0 失败", "同预期", "Y", "Null(无缺陷)", ""),
        ("CM-testcase-013", "会话安全", "安全测试", "会话读取/删除校验属主,越权返回 404", "高",
         "用户 A 已创建会话", "用户 B 携带他人会话 id 访问",
         "1.A 提问建立会话 2.B 读取/删除该会话 3.A 读取/删除",
         "B 的读/删均 404(与不存在一致);A 操作 200", "同预期", "Y", "Null(无缺陷)", "三轮 F10"),
        ("CM-testcase-012", "回归测试", "功能测试", "单元测试套件全绿", "高",
         "开发环境就绪", "pytest 全量",
         "1.python -m pytest backend/tests -q",
         "13 passed(冒烟 4 + 完善轮 9)", "同预期", "Y", "Null(无缺陷)", ""),
    ]
    header_row = 4
    for i, case in enumerate(cases):
        r = header_row + 1 + i
        for j, v in enumerate(case):
            ws.cell(row=r, column=j + 1, value=v)
    # 清除示例行(原第5-6行为示例,已被覆盖);确保后续无残留
    for r in range(header_row + 1 + len(cases), header_row + 9):
        for c in range(1, 14):
            if ws.cell(row=r, column=c).value:
                ws.cell(row=r, column=c, value=None)
    wb.save(DST / "系统测试用例.xlsx")
    print("系统测试用例.xlsx OK")


# ================================================================ 7 系统测试报告
def build_test_report():
    doc = Document(SRC / "系统测试报告.docx")
    remove_notes(doc)
    fill_title(doc)
    fill_section(doc, "目的", ["本报告汇总 CampusMind 的系统测试过程与结果,给出需求覆盖率、缺陷分布与测试结论,作为交付质量证据。"])
    fill_section(doc, "范围", ["覆盖功能测试(问答/知识库/会话/看板)、可靠性测试(限流/降级/兜底)、性能测试(检索/E2E 基准)、安全测试(会话属主)与回归测试;对应 13 条测试用例(见《系统测试用例》)。"])
    fill_section(doc, "定义、首字母缩写词和缩略语", ["QPS:每秒请求数;p50/p95/p99:分位时延;SSE:服务端事件流;Hit@K:检索前 K 命中率。"])
    fill_section(doc, "参考资料", ["《系统测试用例》;scripts/eval_matrix.py、bench.py、acceptance.py;artifacts/validation_2026-10-16.txt。"])
    fill_section(doc, "概述", ["第 2 章测试概要,第 3 章环境,第 4 章结果与两张汇总表,第 5 章结论与建议。"])
    fill_section(doc, "测试概要", [
        "时间:2026-10-16;地点:开发机(Windows 11 x64);人员:全体成员(何俐执行、王若璋复核)。",
        "方法:黑盒功能测试(HTTP/SSE 实测)+ 脚本化性能基准 + 自动化验收(四项)+ 单元回归(pytest)。",
        "内容:13 条用例覆盖 6 项功能需求与性能/可靠性/安全/回归,全部执行完毕。",
    ])
    fill_section(doc, "测试环境", [
        "硬件:x86_64 个人电脑;OS:Windows 11;Python 3.12.10;依赖 fastapi/uvicorn/jieba/httpx/pytest;被测服务 uvicorn 单实例(127.0.0.1:8000);浏览器 Chrome/Edge。",
    ])
    fill_section(doc, "测试结果及分析", [
        "功能/性能/安全用例 13/13 通过,需求覆盖率 100%,本轮未发现未修复缺陷。历史缺陷:2026-10-16 完善轮修复 9 项(RRF 公式、基准口径、XSS/鉴权等),2026-10-27 三轮修复 F10 会话越权——累计 10 项,全部附回归测试与证据(docs/IMPROVEMENTS.md),本轮测试予以验证通过。",
    ])
    t1 = doc.tables[1]
    rows = [
        ("功能项", "问答与引用溯源(FR-1/2/3)", "3", "100%", "0", "0%", ""),
        ("功能项", "知识库管理与热更新(FR-4)", "3", "100%", "0", "0%", "含安全用例 TC-007"),
        ("功能项", "看板/兜底/会话(FR-3/5/6)", "3", "100%", "0", "0%", "含 TC-013 会话属主"),
        ("功能项", "功能项小计", "9", "100%", "0", "0%", ""),
        ("非功能项", "性能", "2", "100%", "0", "0%", "检索与 E2E 基准"),
        ("非功能项", "可靠性", "1", "100%", "0", "0%", "限流 A2"),
        ("非功能项", "回归", "1", "100%", "0", "0%", "pytest 13/13"),
        ("", "非功能项小计", "4", "100%", "0", "0%", ""),
        ("", "总计", "13", "100%", "0", "0%", ""),
    ]
    for i, row in enumerate(rows, start=1):
        for j, v in enumerate(row):
            if v:
                set_cell(t1, i, j, v)
    t2 = doc.tables[2]
    for j, v in enumerate(["0", "0", "0", "0", "0"]):
        set_cell(t2, 1, j + 1, v)
        set_cell(t2, 2, j + 1, "0%")
    fill_section(doc, "需求覆盖率及缺陷分布", [
        "6 项功能需求全部覆盖(100%);性能/可靠性/安全/回归非功能项全覆盖。缺陷分布见上表:本轮 0 缺陷;完善轮 9 项 + 三轮 F10 共 10 项历史缺陷均已闭环并纳入回归(不计入本轮新增)。",
    ])
    fill_section(doc, "缺陷严重程度", [
        "本轮致命/严重/一般/细微缺陷均为 0。历史累计 10 项按严重程度:严重 2(RRF 非标准公式、基准口径失真)、一般 6(XSS、写接口鉴权、桶无界、锁竞态、降级无日志、会话越权 F10)、细微 2(vec_rank 伪造、分类列表计算)——全部修复并通过 14 项回归测试。",
    ])
    fill_section(doc, "测试结论与建议", [
        "结论:13/13 用例通过、需求覆盖率 100%、四项架构验收 PASS、单元测试 14/14——系统达到交付标准。",
        "建议:后续引入 Cross-Encoder 重排并重评测;配置真实语义向量(embedding-3)后补测四路指标;生产部署启用 ADMIN_TOKEN 与 Redis 分布式限流。",
    ])
    strip_instructions(doc)
    doc.save(DST / "系统测试报告.docx")
    print("系统测试报告.docx OK")


# ================================================================ 8 项目总结报告
def build_summary():
    doc = Document(SRC / "项目总结报告.docx")
    for p in doc.paragraphs:
        if p.text.strip().startswith("日期"):
            set_text(p, "日期:2026-10-16", normalize=False)
        elif "签字" in p.text:
            set_text(p, "项目组各成员签字:王若璋、何俐、郭祚梁", normalize=False)
    t0 = doc.tables[0]
    set_cell(t0, 0, 1, "3"); set_cell(t0, 0, 3, PROJECT)
    set_cell(t0, 1, 1, "Python(后端)/ JavaScript(前端)")
    set_cell(t0, 1, 3, "FastAPI · uvicorn · jieba · httpx / 原生 SPA · SSE")
    t1 = doc.tables[1]
    summary_text = (
        "1. 采用哪种架构风格?哪些设计模式?\n"
        "分层风格的模块化单体(接入/网关边界/应用服务/RAG 引擎/数据五层,ADR-1),预留服务化边界。"
        "设计模式:策略+工厂(生成/向量双端 Provider 插件化)、单例(检索器/配置)、仓储(隔离 SQL)、"
        "令牌桶限流、熔断降级。\n\n"
        "2. 技术方案有哪些亮点?\n"
        "① 混合检索 BM25∥向量 + 标准 RRF 排名融合,62 条口语化评测 Hit@3 98.4%;"
        "② 回答强制引用溯源(来源+双通道排名),无知识硬零兜底不编造;"
        "③ SSE 流式输出,meta 事件先推引用;④ 知识热更新免重启(索引版本递增);"
        "⑤ 评测驱动质量闭环:评测/基准/验收/单测四层全脚本可复现;"
        "⑥ 多轮独立调研累计修复 10 项真实缺陷(含安全与口径),全部带证据。\n\n"
        "3. 是否做了单元测试及各类系统测试?\n"
        "单元测试:pytest 14 项全绿;功能测试:13 条系统用例(含引用溯源/热更新/限流/鉴权/会话属主);"
        "性能测试:retrieval-only 515.8-880.4 QPS(p50 1.1-1.9ms)、E2E 并发 20 下 42-44 QPS、p99<800ms、0 失败;"
        "易用性:课程演示与录屏验证;兼容性:Windows/macOS + Chrome/Edge 实测通过。\n\n"
        "4. 是否采用大模型辅助开发?生产率提升估计?\n"
        "是。用于架构调研、代码审查与完善(多轮累计修复 10 项缺陷)、文档/PPT 初稿生成与测试用例整理;"
        "估算整体生产率提升约 30-40%(文档与调研环节提升最显著),关键决策与数据仍由团队复核。"
    )
    set_text(t1.rows[1].cells[0].paragraphs[0], summary_text, normalize=False)
    # 贡献度行
    contrib = t1.rows[2].cells[0]
    set_text(contrib.paragraphs[0], "王若璋 34%(架构与检索引擎、项目管理);何俐 33%(前端、界面与系统测试);郭祚梁 33%(需求与 Vision、评测基准、文档交付物)。注:项目管理包括项目计划、报告、沟通与协调。", normalize=False)
    t2 = doc.tables[1] if len(doc.tables) < 3 else doc.tables[2]
    set_cell(t2, 1, 1, "533 行(2026-10-16 统计)")
    set_cell(t2, 2, 1, "1005 行(2026-10-16 统计)")
    t3 = doc.tables[-1]
    lessons = (
        "1) 评测驱动优于感觉驱动:停用词、截断、去重三个真实缺陷均由指标异常暴露,先建评测集再优化;"
        "2) 如实是最好的工程策略:主动标注 TF-IDF 非语义嵌入、保留历史口径演变,反而让结论更可信;"
        "3) 演示与生产同构(Provider 插件化 + 降级兜底)让课程项目具备了真实部署的可能;"
        "4) 二轮独立视角的代码调研价值巨大:9 项缺陷多数在自测中不可见;"
        "5) 8 周节奏下按 MVP 裁剪范围、契约先行,是三人团队不加班交付的关键。"
    )
    set_text(t3.rows[1].cells[0].paragraphs[0], lessons, normalize=False)
    doc.save(DST / "项目总结报告.docx")
    print("项目总结报告.docx OK")


if __name__ == "__main__":
    build_plan()
    build_vision()
    build_srs()
    build_arch()
    build_iterations()
    build_testcases()
    build_test_report()
    build_summary()
    print("ALL DONE ->", DST)
