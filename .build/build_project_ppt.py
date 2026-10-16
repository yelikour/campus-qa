# -*- coding: utf-8 -*-
"""智问校园 CampusMind 项目讲解 PPT 构建脚本(python-pptx,13.33×7.5 画布)。

设计系统:继承产品自身品牌色(前端 style.css)——
  品牌靛蓝 #3B5BFD(主)/ 紫 #7C4DFF(辅)/ 绿 #12B76A(强调,仅 PASS/收益)
  深墨 #1C2333(封面/封底底色与正文色)· 面板白 + 品牌浅底 #EEF1FF
字体:微软雅黑(Windows/Office 标配,拉丁与东亚字形同名写入)。
母题:圆角卡片 + 超大数字;深-浅-深三明治结构。禁止装饰色条/标题下划线。
"""
from pathlib import Path

from PIL import Image, ImageDraw
from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION, XL_LEGEND_POSITION
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "ppt" / "assets"
OUT = ROOT / "ppt" / "智问校园CampusMind项目讲解PPT.pptx"

# ---------------------------------------------------------------- 设计常量
FONT = "微软雅黑"
INK = "1C2333"; INK2 = "5A6478"; MUTED = "8A93A8"
BRAND = "3B5BFD"; BRAND_L = "8FA6FF"; BRAND_T = "99A9FF"
PURPLE = "7C4DFF"; GREEN = "12B76A"; GREEN_D = "0E9A57"
TINT = "EEF1FF"; TINT2 = "E3E9FF"; LINE = "E5E9F2"
DARK = "1C2333"; DARK_CARD = "27304A"; DARK_MUTED = "A8B0C6"; WHITE = "FFFFFF"

W, H, M = 13.333, 7.5, 0.5
TOTAL = 17


def C(hexstr):
    return RGBColor.from_string(hexstr)


# ---------------------------------------------------------------- 基础工具
def set_ea(run, font=FONT):
    rPr = run._r.get_or_add_rPr()
    ea = rPr.find(qn("a:ea"))
    if ea is None:
        from lxml import etree
        ea = etree.SubElement(rPr, qn("a:ea"))
    ea.set("typeface", font)


def style_run(run, size, bold=False, color=INK, font=FONT, italic=False):
    f = run.font
    f.name = font; f.size = Pt(size); f.bold = bold; f.italic = italic
    f.color.rgb = C(color)
    set_ea(run, font)


def tb(slide, x, y, w, h, paras, anchor=MSO_ANCHOR.TOP, wrap=True):
    """paras: list of dict(text,size,bold,color,align,space_after,line,bullet)"""
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.word_wrap = wrap
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    for i, spec in enumerate(paras):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = spec.get("align", PP_ALIGN.LEFT)
        if spec.get("line"):
            p.line_spacing = spec["line"]
        if spec.get("space_after") is not None:
            p.space_after = Pt(spec["space_after"])
        r = p.add_run(); r.text = spec["text"]
        style_run(r, spec.get("size", 14), spec.get("bold", False), spec.get("color", INK))
    return box


def card(slide, x, y, w, h, fill=WHITE, line=LINE, radius=0.055):
    sh = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    try:
        sh.adjustments[0] = radius
    except Exception:
        pass
    sh.fill.solid(); sh.fill.fore_color.rgb = C(fill)
    if line:
        sh.line.color.rgb = C(line); sh.line.width = Pt(0.75)
    else:
        sh.line.fill.background()
    sh.shadow.inherit = False
    return sh


def chip(slide, x, y, w, h, text, fill, color, size=12, bold=True):
    sh = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    try:
        sh.adjustments[0] = 0.5
    except Exception:
        pass
    sh.fill.solid(); sh.fill.fore_color.rgb = C(fill); sh.line.fill.background()
    sh.shadow.inherit = False
    tf = sh.text_frame; tf.word_wrap = False
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    r = p.add_run(); r.text = text
    style_run(r, size, bold, color)
    return sh


def circle_num(slide, x, y, d, text, fill=BRAND, color=WHITE, size=15):
    sh = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(x), Inches(y), Inches(d), Inches(d))
    sh.fill.solid(); sh.fill.fore_color.rgb = C(fill); sh.line.fill.background()
    sh.shadow.inherit = False
    tf = sh.text_frame; tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    r = p.add_run(); r.text = text
    style_run(r, size, True, color)
    return sh


def footer(slide, idx, dark=False):
    c = DARK_MUTED if dark else MUTED
    tb(slide, M, 7.12, 6.0, 0.3, [dict(text="智问校园 CampusMind · AI + RAG 校园智能问答", size=12, color=c)])
    tb(slide, W - M - 2.0, 7.12, 2.0, 0.3,
       [dict(text=f"{idx:02d} · {TOTAL}", size=12, color=c, align=PP_ALIGN.RIGHT)])


def header(slide, kicker, title, idx):
    tb(slide, M, 0.44, 9.0, 0.32, [dict(text=kicker, size=13, bold=True, color=BRAND)])
    tb(slide, M, 0.78, 11.0, 0.62, [dict(text=title, size=29, bold=True, color=INK)])
    footer(slide, idx)


def notes(slide, text):
    slide.notes_slide.notes_text_frame.text = text


def blank(prs, bg=WHITE):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    r = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    r.fill.solid(); r.fill.fore_color.rgb = C(bg); r.line.fill.background()
    r.shadow.inherit = False
    return s


def pic(slide, path, x, y, w, h):
    return slide.shapes.add_picture(str(path), Inches(x), Inches(y), Inches(w), Inches(h))


def round_img(name, radius=26):
    src = ASSETS / name; dst = ASSETS / "rounded" / name
    dst.parent.mkdir(exist_ok=True)
    if dst.exists():
        return dst
    im = Image.open(src).convert("RGBA")
    mask = Image.new("L", im.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, im.width - 1, im.height - 1], radius=radius, fill=255)
    im.putalpha(mask); im.save(dst)
    return dst


# ---------------------------------------------------------------- 图表工具
def chart_cjk(chart, size=12, color=INK2):
    """chartSpace 级默认字体(拉丁+东亚),图表内文本统一继承。"""
    from lxml import etree
    cs = chart._chartSpace
    for old in cs.findall(qn("c:txPr")):
        cs.remove(old)
    xml = (
        '<c:txPr xmlns:c="http://schemas.openxmlformats.org/drawingml/2006/chart" '
        'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
        '<a:bodyPr/><a:lstStyle/><a:p><a:pPr><a:defRPr sz="%d">'
        '<a:solidFill><a:srgbClr val="%s"/></a:solidFill>'
        '<a:latin typeface="%s"/><a:ea typeface="%s"/></a:defRPr></a:pPr>'
        "<a:endParaRPr lang=\"zh-CN\"/></a:p></c:txPr>" % (size * 100, color, FONT, FONT)
    )
    txPr = etree.fromstring(xml)
    anchor = cs.find(qn("c:spPr"))
    if anchor is None:
        anchor = cs.find(qn("c:chart"))
    anchor.addnext(txPr)


# ================================================================ 构建
prs = Presentation()
prs.slide_width = Inches(W); prs.slide_height = Inches(H)
prs.author = "智问校园 CampusMind"
prs.title = "智问校园 CampusMind 项目讲解"

# ---------------------------------------------------------------- 1 封面
s = blank(prs, DARK)
tb(s, 0.9, 1.42, 5.75, 0.35,
   [dict(text="《软件体系结构》课程项目 · 2026 春季学期", size=13, bold=True, color=BRAND_L)])
tb(s, 0.9, 1.86, 5.75, 1.9, [
    dict(text="智问校园", size=48, bold=True, color=WHITE, space_after=2),
    dict(text="CampusMind", size=30, bold=True, color=BRAND_L, space_after=8),
    dict(text="面向在校学生的校园事务智能问答系统 · AI + RAG", size=16, color=DARK_MUTED),
])
tb(s, 0.9, 4.15, 5.75, 0.4,
   [dict(text="混合检索 · RRF 融合 · 流式生成 · 引用溯源", size=15, bold=True, color=WHITE)])
tb(s, 0.9, 4.62, 5.75, 0.75, [
    dict(text="王若璋 · 何俐 · 郭祚梁 · 8 周交付", size=13, color=DARK_MUTED, space_after=3),
    dict(text="2026-10 完善轮:9 项缺陷修复,证据可复现", size=13, color=DARK_MUTED),
])
tb(s, 0.9, 6.55, 8.0, 0.35,
   [dict(text="github.com/yelikour/campus-qa(公开仓库)", size=13, bold=True, color=BRAND_L)])
img = pic(s, round_img("ui_welcome.png"), 6.85, 1.35, 5.95, 3.72)
img.line.color.rgb = C(DARK_CARD); img.line.width = Pt(1)
stats = [("62 条", "检索评测集"), ("4 / 4", "架构验收 PASS"), ("13 / 13", "单元测试通过")]
for i, (v, k) in enumerate(stats):
    x = 6.85 + i * 2.05
    card(s, x, 5.32, 1.9, 0.95, DARK_CARD, None)
    tb(s, x + 0.14, 5.44, 1.65, 0.75, [
        dict(text=v, size=19, bold=True, color=BRAND_L, space_after=1),
        dict(text=k, size=11.5, color=DARK_MUTED),
    ])
notes(s, "开场:一句话定位——面向在校学生的校园事务智能问答,自然语言提问,回答必带校内知识来源。右侧是真实产品界面。三个数字先立信任:评测集、验收、测试全绿。仓库已公开,所有指标可复现。")

# ---------------------------------------------------------------- 2 问题与方案
s = blank(prs)
header(s, "问题与方案", "校园事务信息的三堵墙,一套 RAG 系统拆掉它", 2)
pains = [
    ("信息分散", "规章散落在官网、公众号、群里,新生无从找起"),
    ("口径不一", "同学间口口相传,答案互相矛盾、时常过期"),
    ("不敢相信", "通用 AI 缺校内语料,一本正经地编造"),
]
y = 1.62
for i, (t, d) in enumerate(pains):
    card(s, M, y, 5.15, 1.42)
    circle_num(s, M + 0.22, y + 0.42, 0.56, str(i + 1), TINT2, BRAND, 17)
    tb(s, M + 1.0, y + 0.24, 4.0, 1.0, [
        dict(text=t, size=16, bold=True, color=INK, space_after=3),
        dict(text=d, size=12.5, color=INK2, line=1.15),
    ])
    y += 1.62
card(s, 6.35, 1.62, 6.48, 4.82, TINT, None)
tb(s, 6.62, 1.86, 6.0, 0.4, [dict(text="CampusMind 的答案", size=17, bold=True, color=BRAND)])
flow = [
    ("自然语言提问", "口语化问法直接问,如「饭卡找不到了」"),
    ("混合检索", "BM25 与向量双通道并行召回校内知识"),
    ("RRF 融合 + 质量门槛", "对排名融合,免分数归一化;零交集即判无知识"),
    ("流式生成 + 引用溯源", "SSE 打字机输出,每条回答标注来源与双通道排名"),
]
fy = 2.36
for i, (t, d) in enumerate(flow):
    card(s, 6.62, fy, 5.95, 0.8, WHITE, LINE)
    circle_num(s, 6.80, fy + 0.15, 0.5, str(i + 1), BRAND, WHITE, 14)
    tb(s, 7.45, fy + 0.12, 5.0, 0.6, [
        dict(text=t, size=14.5, bold=True, color=INK, space_after=1),
        dict(text=d, size=11.5, color=INK2),
    ])
    fy += 0.94
chip(s, 6.62, 6.06, 5.95, 0.34, "无命中 → 诚实回退引导话术,不编造(sources = 0)", GREEN_D, WHITE, 12.5)
notes(s, "左侧三堵墙是访谈得出的真实痛点;右侧是技术方案的主线:双通道检索→RRF 融合→流式生成→引用溯源。特别强调最后一行:知识库没有的问题,系统宁可说不知道,这是可信性的底线。")

# ---------------------------------------------------------------- 3 系统架构
s = blank(prs)
header(s, "系统架构", "五层分层 · 模块化单体起步,预留服务化边界(ADR-1)", 3)
layers = [
    ("接入层", "原生 SPA · 聊天 / 知识库管理 / 运行看板 · SSE 流式渲染", TINT),
    ("网关边界", "令牌桶限流 · ADMIN_TOKEN 鉴权 · CORS · 静态资源托管", TINT),
    ("应用服务", "chat · knowledge · conversations · admin 四组 API 服务", TINT2),
    ("RAG 引擎", "BM25 倒排 · 向量通道 · RRF 融合 · 重排开关 · 生成 Provider", "CBD9FF"),
    ("数据层", "知识语料 JSON · SQLite 会话与查询日志 · 内存索引(热重建)", "B8C9FF"),
]
ly = 1.66
for name, desc, fill in layers:
    card(s, M, ly, 7.9, 0.86, fill, None)
    tb(s, M + 0.28, ly + 0.14, 1.75, 0.6, [dict(text=name, size=15.5, bold=True, color=INK)])
    tb(s, M + 2.05, ly + 0.20, 5.7, 0.55, [dict(text=desc, size=12.5, color=INK)], anchor=MSO_ANCHOR.MIDDLE)
    ly += 1.00
card(s, 8.75, 1.66, 4.08, 4.86, WHITE, LINE)
tb(s, 9.0, 1.9, 3.6, 0.4, [dict(text="关键架构决策(ADR)", size=15, bold=True, color=BRAND)])
adrs = [
    ("ADR-1", "模块化单体起步,按 api/services/repository/core 分包,预留服务化拆分边界"),
    ("ADR-2", "混合检索 + RRF 融合,对排名而非分数融合,免归一化"),
    ("ADR-4", "生成/向量双端 Provider 插件化,云端异常自动熔断降级"),
    ("ADR-5", "内存索引热重建,知识增删免重启即生效(版本递增)"),
]
ay = 2.38
for tag, d in adrs:
    chip(s, 9.0, ay, 0.85, 0.34, tag, TINT, BRAND, 11.5)
    tb(s, 9.98, ay - 0.04, 2.72, 0.92, [dict(text=d, size=11.5, color=INK2, line=1.12)])
    ay += 1.02
notes(s, "架构叙事:五层从上到下一次请求穿过全栈。分层的目的不是分层本身,而是可替换:数据层可外置 PG/向量库,应用层无状态可水平扩展,引擎层 Provider 可插拔。右侧四个 ADR 是文档第 11 章追踪矩阵的入口。")

# ---------------------------------------------------------------- 4 RAG 核心链路
s = blank(prs)
header(s, "核心链路", "一条提问的完整旅程:检索、融合、生成、溯源", 4)
steps = [("提问", "≤500 字\n口语化问法"), ("双通道检索", "BM25 top20\n∥ 向量 top20"),
         ("RRF 融合", "Σ1/(k+rank)\nk=60 对排名融合"), ("重排(实验)", "RERANK_ENABLED\n默认关·实测无收益"),
         ("SSE 生成", "meta 先推引用\n打字机式输出"), ("引用溯源", "来源+BM25/VEC\n双通道排名")]
cx, cw, ch = M, 2.08, 1.02
for i, (t, d) in enumerate(steps):
    x = cx + i * 2.045
    sh = s.shapes.add_shape(MSO_SHAPE.CHEVRON, Inches(x), Inches(1.72), Inches(cw), Inches(ch))
    sh.adjustments[0] = 0.28
    fill = BRAND if i in (1, 2) else (PURPLE if i == 4 else TINT2)
    txt = WHITE if i in (1, 2, 4) else INK
    sh.fill.solid(); sh.fill.fore_color.rgb = C(fill); sh.line.fill.background()
    sh.shadow.inherit = False
    tf = sh.text_frame; tf.word_wrap = False
    tf.margin_left = tf.margin_right = Inches(0.16); tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    r = p.add_run(); r.text = t; style_run(r, 14.5, True, txt)
    tb(s, x + 0.16, 2.88, 1.85, 0.75, [dict(text=d, size=10.5, color=INK2, line=1.15, align=PP_ALIGN.CENTER)])
highlights = [
    ("检索快", "p50 1.1–1.9ms(修正口径实测)", "位于双通道检索下方"),
    ("首字快", "meta 事件先推引用来源,边生成边展示", "SSE 生成特性"),
    ("可开关", "重排与生成 Provider 均为运行时配置", "实验与生产一键切换"),
]
hx = M
for t, d, _ in highlights:
    card(s, hx, 3.95, 4.04, 1.0, WHITE, LINE)
    tb(s, hx + 0.22, 4.10, 3.6, 0.75, [
        dict(text=t, size=14, bold=True, color=BRAND, space_after=2),
        dict(text=d, size=11.5, color=INK2, line=1.12),
    ])
    hx += 4.15
card(s, M, 5.22, 12.33, 1.52, TINT, None)
tb(s, M + 0.28, 5.42, 11.8, 1.15, [
    dict(text="兜底路径(可信性底线):全部候选与查询实质词零交集 → 判定无相关知识 → 返回引导话术,不带任何引用来源", size=14, bold=True, color=INK, space_after=4),
    dict(text="口径:文档级去重(q/a 双通道 chunk 不重复占位)· 全有或全无门槛 MIN_RELEVANCE=0.08(62 条评测标定:0.15 误杀口语化正解,0.06 放入无关命中)", size=11.5, color=INK2, line=1.15),
])
notes(s, "沿着链路讲一遍:双通道并行召回、RRF 只看排名不比分数、重排是实验开关、SSE 先推 meta 让用户立刻看到在参考哪些资料。底部兜底是这套系统与「普通 ChatGPT 套壳」的本质区别:没有知识就说没有。")

# ---------------------------------------------------------------- 5 混合检索双通道
s = blank(prs)
header(s, "检索引擎 · 双通道", "稀疏管精确,稠密管语义,RRF 只融合排名", 5)
card(s, M, 1.62, 6.0, 3.3, WHITE, LINE)
tb(s, M + 0.3, 1.84, 5.4, 0.4, [dict(text="BM25 · 稀疏通道", size=16, bold=True, color=INK)])
tb(s, M + 0.3, 2.32, 5.45, 2.4, [
    dict(text="jieba 分词 + 自实现 BM25(k1=1.5 / b=0.75)", size=12.5, color=INK2, space_after=5, line=1.2),
    dict(text="倒排索引:查询只访问命中词的倒排链,不做全量扫描", size=12.5, color=INK2, space_after=5, line=1.2),
    dict(text="关键词密集的规章问题表现最好:Hit@1 80.6%", size=12.5, color=INK2, space_after=8, line=1.2),
])
chip(s, M + 0.3, 4.32, 2.6, 0.4, "Hit@1  80.6%", BRAND, WHITE, 12.5)
card(s, 6.83, 1.62, 6.0, 3.3, WHITE, LINE)
tb(s, 7.13, 1.84, 5.4, 0.4, [dict(text="向量 · 稠密通道", size=16, bold=True, color=INK)])
tb(s, 7.13, 2.32, 5.45, 2.4, [
    dict(text="演示环境:TF-IDF 加权词袋(离线零依赖,如实标注「非语义嵌入」)", size=12.5, color=INK2, space_after=5, line=1.2),
    dict(text="生产切换:智谱 embedding-3,配置 ZHIPUAI_API_KEY 即启用,接口不变", size=12.5, color=INK2, space_after=5, line=1.2),
    dict(text="提供与词面不同的第二视角,补充口语改写召回", size=12.5, color=INK2, space_after=8, line=1.2),
])
chip(s, 7.13, 4.32, 2.6, 0.4, "Hit@1  75.8%", PURPLE, WHITE, 12.5)
card(s, M, 5.14, 12.33, 1.6, TINT, None)
tb(s, M + 0.3, 5.34, 11.8, 1.25, [
    dict(text="融合与质量控制:为什么用 RRF", size=14.5, bold=True, color=BRAND, space_after=4),
    dict(text="对「排名」而非原始分数融合,天然免两通道分数归一化;同文档双通道 chunk 只保留最高分一条(文档级去重),避免挤占其它文档名额——该缺陷正是 62 条评测暴露并修复的真实问题。", size=12, color=INK2, line=1.25),
])
notes(s, "双通道定位要说清:BM25 管关键词精确匹配,向量管语义视角。演示环境向量是 TF-IDF 词袋,不是真语义嵌入——这是材料里如实标注的,不是藏着掖着。RRF 融合排名而非分数,省掉归一化这个老大难。")

# ---------------------------------------------------------------- 6 可插拔 Provider
s = blank(prs)
header(s, "生成与向量 · Provider 插件化", "同类可替换:无 Key 离线可跑,有 Key 一键上云", 6)
cols = [
    ("生成 Generator", [
        ("本地抽取式(默认)", "离线零依赖 · 抽取式合成 · 降级兜底", BRAND),
        ("智谱 GLM(云端)", "流式生成 · 带引用上下文提示词 · 温度 0.3", PURPLE),
    ], "云端超时/故障 → 流内自动回退本地,降级原因落日志"),
    ("向量 Embedding", [
        ("TF-IDF 词袋(默认)", "离线 fallback · 前端如实显示 provider 名", BRAND),
        ("智谱 embedding-3(云端)", "真语义向量 · 内存缓存避免重复嵌入", PURPLE),
    ], "构建失败(网络/配额)→ 回退 TF-IDF,检索始终可用"),
]
for ci, (title, items, fallback) in enumerate(cols):
    x = M + ci * 6.33
    card(s, x, 1.62, 6.0, 3.42, WHITE, LINE)
    tb(s, x + 0.3, 1.84, 5.4, 0.4, [dict(text=title, size=16, bold=True, color=INK)])
    iy = 2.34
    for name, desc, accent in items:
        card(s, x + 0.3, iy, 5.4, 0.98, TINT, None)
        tb(s, x + 0.52, iy + 0.13, 5.0, 0.75, [
            dict(text=name, size=14, bold=True, color=accent, space_after=2),
            dict(text=desc, size=11.5, color=INK2),
        ])
        iy += 1.12
    tb(s, x + 0.3, 4.62, 5.5, 0.35, [dict(text="自动回退:" + fallback.split("→")[0].strip() + " → " + fallback.split("→")[1].strip(), size=11, color=INK2)])
card(s, M, 5.28, 12.33, 1.45, TINT, None)
tb(s, M + 0.3, 5.48, 11.8, 1.1, [
    dict(text="可观察性:引擎信息不藏着", size=14.5, bold=True, color=BRAND, space_after=4),
    dict(text="前端顶栏与运行看板实时显示当前 LLM Provider / 向量 Provider / 索引版本——用户永远知道回答由哪个引擎生成、向量是不是语义嵌入。", size=12, color=INK2, line=1.25),
])
notes(s, "这一页讲架构决策 ADR-4/ADR-7 的落地:两端 Provider 同一套抽象,演示环境零依赖离线可跑,配置 Key 即切云端,异常自动降级。重点是降级不是静默的——前端如实显示当前引擎,这是产品诚实的一部分。")

# ---------------------------------------------------------------- 7 产品一览
s = blank(prs)
header(s, "产品一览", "三个视图:问答、知识库治理、运行看板", 7)
img = pic(s, round_img("ui_chat_citations.png"), M, 1.62, 8.0, 5.0)
img.line.color.rgb = C(LINE); img.line.width = Pt(1)
tb(s, M, 6.68, 8.0, 0.3,
   [dict(text="智能问答:回答下方即引用卡片——来源、BM25/VEC 双通道排名、融合分数、检索耗时", size=12, color=INK2)])
for i, (name, file) in enumerate([("知识库管理 · 录入即热更新", "ui_knowledge.png"),
                                   ("运行看板 · 命中率/时延实时刷新", "ui_dashboard.png")]):
    y = 1.62 + i * 2.62
    im = pic(s, round_img(file), 8.72, y, 4.13, 2.58)
    im.line.color.rgb = C(LINE); im.line.width = Pt(1)
    # 图内标签:深色小条压在截图左下角,避免与相邻截图争空间
    card(s, 8.72, y + 2.58 - 0.42, 2.72, 0.34, DARK, None, radius=0.5)
    tb(s, 8.84, y + 2.58 - 0.39, 2.55, 0.3,
       [dict(text=name, size=10.5, bold=True, color=WHITE)], anchor=MSO_ANCHOR.MIDDLE)
notes(s, "产品三视图走一遍:左边是核心体验——回答带引用卡片,双通道排名和分数直接可见;右上知识库管理,录入即热更新;右下运行看板,给运维和课程演示用。截图全部来自当前版本真实运行,非设计稿。")

# ---------------------------------------------------------------- 8 安全与稳定性
s = blank(prs)
header(s, "安全与稳定性", "四道防线:从入口到内容逐层设防", 8)
rows = [
    ("入口限流", "令牌桶 5 QPS / 突发 10,按用户隔离;桶字典有界(≤1 万,最久未活跃淘汰),伪造 token 无法耗尽内存", "200×10+429×5"),
    ("熔断降级", "云端 GLM 异常 → 流内回退本地抽取式生成;降级原因落日志,频率/超时/网络/鉴权可归因", "139字·不中断"),
    ("溯源兜底", "回答强制携带引用来源;全有或全无门槛——最佳分低于阈值即判无知识,返回引导话术", "sources=0"),
    ("写接口安全", "知识库写接口可选 ADMIN_TOKEN 鉴权;前端三处输出全量转义,封死存储型 XSS 注入链", "401 拦截写入"),
]
y = 1.62
for i, (t, d, metric) in enumerate(rows):
    card(s, M, y, 12.33, 1.22, WHITE, LINE)
    circle_num(s, M + 0.24, y + 0.33, 0.56, str(i + 1), BRAND if i < 2 else GREEN_D, WHITE, 16)
    tb(s, M + 1.02, y + 0.18, 2.2, 0.9, [dict(text=t, size=16, bold=True, color=INK)], anchor=MSO_ANCHOR.MIDDLE)
    tb(s, M + 3.15, y + 0.16, 6.6, 0.95, [dict(text=d, size=12, color=INK2, line=1.2)], anchor=MSO_ANCHOR.MIDDLE)
    chip(s, M + 10.05, y + 0.36, 2.0, 0.52, metric, GREEN_D, WHITE, 12)
    y += 1.34
notes(s, "四道防线从外到内:入口限流保可用性;生成熔断保服务不挂;溯源兜底保可信性;写接口鉴权+XSS 转义保内容安全。后两道是 2026-10 完善轮新增/加固的,后面会展开讲怎么发现的。")

# ---------------------------------------------------------------- 9 检索评测
s = blank(prs)
header(s, "质量证据 · 检索评测", "62 条口语化改写 × 四条链路,统一文档级去重口径", 9)
chart_data = CategoryChartData()
chart_data.categories = ["BM25-only", "向量 TF-IDF", "混合+RRF(生产)", "混合+重排(实验)"]
chart_data.add_series("Hit@1", (80.6, 75.8, 80.6, 77.4))
chart_data.add_series("Hit@3", (98.4, 93.5, 98.4, 96.8))
gf = s.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(M), Inches(1.66), Inches(7.55), Inches(4.7), chart_data)
ch = gf.chart
chart_cjk(ch, 12)
ch.has_legend = True
ch.legend.position = XL_LEGEND_POSITION.TOP
ch.legend.include_in_layout = False
va = ch.value_axis
va.minimum_scale = 60; va.maximum_scale = 100
va.tick_labels.number_format = '0"%"'; va.tick_labels.number_format_is_linked = False
va.has_major_gridlines = True
va.major_gridlines.format.line.color.rgb = C(LINE); va.major_gridlines.format.line.width = Pt(0.5)
ch.category_axis.has_major_gridlines = False
plot = ch.plots[0]; plot.gap_width = 120; plot.overlap = -10
for si, col in enumerate([BRAND, BRAND_T]):
    ser = plot.series[si]
    ser.format.fill.solid(); ser.format.fill.fore_color.rgb = C(col)
plot.has_data_labels = True
dl = plot.data_labels
dl.number_format = '0.0"%"'; dl.number_format_is_linked = False
dl.position = XL_LABEL_POSITION.OUTSIDE_END
dl.font.size = Pt(11); dl.font.color.rgb = C(INK)
card(s, 8.35, 1.66, 4.48, 4.7, WHITE, LINE)
tb(s, 8.6, 1.88, 4.0, 0.4, [dict(text="结论(如实)", size=15.5, bold=True, color=BRAND)])
concl = [
    ("BM25 最稳", "关键词密集的规章问题上表现最好"),
    ("向量是补充视角", "TF-IDF 词袋未稳定超过 BM25,材料如实标注"),
    ("RRF 为生产默认", "融合收益在口语改写场景体现,链路最简"),
    ("轻量重排无收益", "词面特征重排默认关闭,留待 Cross-Encoder"),
]
cy = 2.36
for t, d in concl:
    tb(s, 8.6, cy, 4.0, 0.9, [
        dict(text=t, size=13.5, bold=True, color=INK, space_after=2),
        dict(text=d, size=11.5, color=INK2, line=1.15),
    ])
    cy += 1.0
tb(s, M, 6.55, 12.3, 0.3,
   [dict(text="来源:scripts/eval_matrix.py · n=62 口语化同义改写 · 2026-10-16 实测 · 语料 59 篇 / 136 chunks · 允许 ±1.6pp 运行间波动", size=12, color=MUTED)])
notes(s, "评测方法先讲口径:62 条口语化改写、文档级去重、四条链路同口径,这是多次口径事故后统一的结果。数字如实:BM25 最好 80.6,重排实验路径 77.4——我们不挑好看的数字,默认链路选 RRF 是综合质量与成本的决定。")

# ---------------------------------------------------------------- 10 性能基准
s = blank(prs)
header(s, "质量证据 · 性能基准", "检索快到不是瓶颈,生成端吞吐 44 QPS 零失败", 10)
stat_cards = [
    ("880", "QPS", "retrieval-only · RRF 生产链路(修正口径实测,515.8–880.4)", BRAND),
    ("44", "QPS", "local-extractive E2E(并发 20,含生成+落库)", PURPLE),
    ("0", "失败", "retrieval 300 样本 + E2E 200 样本,全部成功", GREEN_D),
]
x = M
for v, unit, d, accent in stat_cards:
    card(s, x, 1.62, 4.0, 1.72, WHITE, LINE)
    tb(s, x + 0.28, 1.78, 3.5, 0.8, [
        dict(text=v + "  " + unit, size=30, bold=True, color=accent),
    ])
    tb(s, x + 0.28, 2.62, 3.5, 0.62, [dict(text=d, size=11.5, color=INK2, line=1.15)])
    x += 4.15
lat = [
    ("retrieval-only(RRF)", [("p50", 1.1), ("p95", 1.8), ("p99", 2.1)], "ms", 2.1, BRAND),
    ("E2E 并发 20", [("p50", 425), ("p95", 627), ("p99", 761)], "ms", 761, PURPLE),
]
ly = 3.66
for name, items, unit, vmax, accent in lat:
    tb(s, M, ly, 3.0, 0.35, [dict(text=name, size=13.5, bold=True, color=INK)])
    for k, (label, v) in enumerate(items):
        slot_x = 3.6 + k * 3.1
        w_bar = max(0.15, 1.9 * v / vmax)
        bar = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(slot_x), Inches(ly + 0.02), Inches(w_bar), Inches(0.34))
        bar.adjustments[0] = 0.5
        bar.fill.solid(); bar.fill.fore_color.rgb = C(accent); bar.line.fill.background(); bar.shadow.inherit = False
        tb(s, slot_x + w_bar + 0.1, ly + 0.02, 0.95, 0.34,
           [dict(text=f"{label} {v}{unit}", size=12, bold=True, color=INK)], anchor=MSO_ANCHOR.MIDDLE)
    ly += 0.62
card(s, M, 5.05, 12.33, 1.62, TINT, None)
tb(s, M + 0.3, 5.25, 11.8, 1.3, [
    dict(text="口径如实的代价与修正(F9,完善轮)", size=14.5, bold=True, color=BRAND, space_after=4),
    dict(text="bench.py 此前误测重排实验路径却标注「默认链路」——2026-09-18 的 251.4 QPS 实为重排路径数值。完善轮修正口径后按生产 RRF 链路实测 515.8–880.4 QPS / p50 1.1–1.9ms;历史值保留并标注口径演变,不删改。", size=12, color=INK2, line=1.25),
])
tb(s, M, 6.72, 12.3, 0.3,
   [dict(text="来源:scripts/bench.py · Win/x64 · 2026-10-16 · 历史值 macOS/arm64 2026-09-18(重排口径)", size=12, color=MUTED)])
notes(s, "三个大数字先说结论:检索 880 QPS、端到端 44 QPS、零失败。延迟条展示两组分位数。底部坦白一个口径修正:旧基准测错了路径,新数字更高但更重要的是口径干净——历史值保留不删,这是项目的如实原则。")

# ---------------------------------------------------------------- 11 四项架构验收
s = blank(prs)
header(s, "质量证据 · 架构验收", "四个最像「翻车现场」的场景,4/4 PASS", 11)
acc = [
    ("A1 生成降级", "云端 GLM 配置无效 Key", "流内自动回退本地抽取式,产出 139 字含正解关键信息,服务不中断"),
    ("A2 入口限流", "单用户并发突发 15 请求", "令牌桶精确放行 10、拒绝 5:200×10 + 429×5"),
    ("A3 知识热更新", "验收中新增知识条目", "免重启即时检索命中并正确回答,索引版本 1→2 递增,验后自动清理"),
    ("A4 无知识兜底", "提问知识库完全无关的问题", "sources=0,返回引导话术,不编造任何事实"),
]
for i, (t, cond, ev) in enumerate(acc):
    x = M + (i % 2) * 6.33; y = 1.62 + (i // 2) * 2.62
    card(s, x, y, 6.0, 2.42, WHITE, LINE)
    tb(s, x + 0.3, y + 0.2, 3.6, 0.4, [dict(text=t, size=16.5, bold=True, color=INK)])
    chip(s, x + 4.65, y + 0.22, 1.05, 0.38, "PASS", GREEN, WHITE, 12.5)
    tb(s, x + 0.3, y + 0.72, 5.4, 0.35, [dict(text="场景:" + cond, size=12, bold=True, color=BRAND)])
    tb(s, x + 0.3, y + 1.14, 5.45, 1.1, [dict(text="证据:" + ev, size=12, color=INK2, line=1.25)])
notes(s, "验收脚本 acceptance.py 全走真实 HTTP/进程内执行,不是 mock。四个场景都是生产最容易翻车的:云挂了、流量突刺、知识要更新、用户问库里没有的东西。结果 4/4 PASS,证据可复现。")

# ---------------------------------------------------------------- 12 完善轮总览
s = blank(prs)
header(s, "2026-10 完善轮", "独立二轮调研:9 项真实缺陷,全部修复并验证", 12)
tb(s, M, 1.42, 7.6, 0.35,
   [dict(text="方法:基线复现(pytest/评测/验收全绿)→ 全量代码审查 → 对照实验驱动修复", size=12.5, color=INK2)])
groups = [
    ("检索正确性", "F1 RRF 误用常数权重(非标准公式)· F2 引用卡片 vec_rank 伪造失真", BRAND),
    ("安全", "F3 前端三处未转义(存储型 XSS)· F4 写接口无鉴权 · F5 令牌桶无界增长", "D94F3D"),
    ("性能", "F6 BM25 全量扫描 → 倒排索引(10×/35×,与原算法逐位等价)", PURPLE),
    ("健壮性", "F7 云端降级静默吞异常 · F8 知识删除在文件锁外读写(竞态)", "946200"),
    ("评测口径", "F9 bench 误测重排路径却宣称默认链路,吞吐被低估", "0E7490"),
]
gy = 1.92
for name, d, accent in groups:
    card(s, M, gy, 7.85, 0.9, WHITE, LINE)
    chip(s, M + 0.22, gy + 0.26, 1.35, 0.38, name, accent, WHITE, 12)
    tb(s, M + 1.75, gy + 0.12, 5.95, 0.68, [dict(text=d, size=11.5, color=INK2, line=1.18)], anchor=MSO_ANCHOR.MIDDLE)
    gy += 1.0
card(s, 8.62, 1.92, 4.21, 4.9, DARK, None)
tb(s, 8.9, 2.16, 3.7, 0.4, [dict(text="修复后的全量回归", size=15, bold=True, color=WHITE)])
metrics = [("9", "项缺陷修复(报告 F1–F9,证据链完整)"),
           ("13/13", "单元测试通过(新增 9 项回归测试)"),
           ("4/4", "架构验收复测 PASS"),
           ("0", "指标回退(评测矩阵 Hit@1/Hit@3 持平)")]
my = 2.72
for v, d in metrics:
    tb(s, 8.9, my, 3.7, 0.95, [
        dict(text=v, size=25, bold=True, color=BRAND_L, space_after=1),
        dict(text=d, size=11, color=DARK_MUTED, line=1.15),
    ])
    my += 1.02
notes(s, "完善轮的定位:不是重写,是独立视角的二轮调研。左侧按影响面分五组,每项都有编号和证据;右侧是修复后的回归结果——9 项修复、13/13 测试、4/4 验收、指标零回退。完整报告在 docs/IMPROVEMENTS.md。")

# ---------------------------------------------------------------- 13 深挖 F1
s = blank(prs)
header(s, "完善轮深挖 · F1", "名为 RRF,实为通道计数:一个被语料掩盖的公式错误", 13)
card(s, M, 1.62, 6.0, 1.72, WHITE, LINE)
tb(s, M + 0.28, 1.78, 5.5, 1.45, [
    dict(text="修复前(错误)", size=13, bold=True, color="D94F3D", space_after=4),
    dict(text="score(d) = Σ_channel  1/(K+1)", size=15, bold=True, color=INK, space_after=3),
    dict(text="常数权重,与排名无关 → 等价于「通道计数投票」,排名 1 与排名 20 贡献相同", size=11.5, color=INK2, line=1.2),
])
card(s, 6.83, 1.62, 6.0, 1.72, WHITE, LINE)
tb(s, 7.11, 1.78, 5.5, 1.45, [
    dict(text="修复后(标准 RRF)", size=13, bold=True, color=GREEN_D, space_after=4),
    dict(text="score(d) = Σ_channel  1/(K + rank)", size=15, bold=True, color=INK, space_after=3),
    dict(text="对每通道真实排名累加 —— 文档注释与架构文档宣称的行为,至此实现与设计一致", size=11.5, color=INK2, line=1.2),
])
rows = [("混合+RRF(生产)", "80.6 / 98.4 持平", "0.884 → 0.882(一名次内波动)", INK),
        ("混合+重排(实验)", "74.2 / 90.3 → 77.4 / 96.8", "+3.2pp / +6.5pp(先验变连续信号)", GREEN_D)]
tb(s, M, 3.5, 12.0, 0.3, [dict(text="62 条评测复测(Hit@1 / Hit@3):", size=13.5, bold=True, color=INK)])
ty = 3.86
for name, main, mrr, accent in rows:
    card(s, M, ty, 12.33, 0.72, TINT if accent == INK else "E7F8F0", None)
    tb(s, M + 0.28, ty + 0.07, 3.4, 0.58, [dict(text=name, size=13.5, bold=True, color=INK)], anchor=MSO_ANCHOR.MIDDLE)
    tb(s, M + 3.8, ty + 0.07, 3.9, 0.58, [dict(text=main, size=13, bold=True, color=accent)], anchor=MSO_ANCHOR.MIDDLE)
    tb(s, M + 7.9, ty + 0.07, 4.2, 0.58, [dict(text=mrr, size=12, color=INK2)], anchor=MSO_ANCHOR.MIDDLE)
    ty += 0.84
card(s, M, 5.52, 12.33, 1.28, WHITE, LINE)
tb(s, M + 0.28, 5.68, 11.8, 1.0, [
    dict(text="为什么在演示环境「测不出来」,仍然必须修?", size=13.5, bold=True, color=BRAND, space_after=3),
    dict(text="TF-IDF 演示语料双通道高度相关(都是词面匹配),两版指标恰好持平,错误被掩盖;接入真语义向量后双通道分歧显著增大,常数版会系统性偏好「双通道都命中但排名靠后」的文档——标准公式才是正确行为,这是面向未来语义通道的修正。", size=11.5, color=INK2, line=1.22),
])
notes(s, "这是完善轮最有代表性的一页:实现与设计文档不一致,但恰好被语料特性掩盖。修复后生产链路指标持平、实验链路反而提升 3-6pp。教训:指标没退不等于实现没错,公式要对齐设计。")

# ---------------------------------------------------------------- 14 深挖 F6+F9
s = blank(prs)
header(s, "完善轮深挖 · F6 / F9", "倒排索引 10–35 倍加速,与一次基准口径纠偏", 14)
chart_data = CategoryChartData()
chart_data.categories = ["当前语料 136 chunks", "20× 语料 2,720 chunks"]
chart_data.add_series("旧 · 全量扫描", (2145, 68))
chart_data.add_series("新 · 倒排索引", (21505, 2587))
gf = s.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(M), Inches(1.66), Inches(6.6), Inches(4.35), chart_data)
ch = gf.chart
chart_cjk(ch, 12)
ch.has_legend = True
ch.legend.position = XL_LEGEND_POSITION.TOP
ch.legend.include_in_layout = False
va = ch.value_axis
va.has_major_gridlines = True
va.major_gridlines.format.line.color.rgb = C(LINE); va.major_gridlines.format.line.width = Pt(0.5)
va.tick_labels.number_format = "#,##0"; va.tick_labels.number_format_is_linked = False
plot = ch.plots[0]; plot.gap_width = 110; plot.overlap = -10
for si, col in enumerate(["C9D2E8", BRAND]):
    ser = plot.series[si]
    ser.format.fill.solid(); ser.format.fill.fore_color.rgb = C(col)
plot.has_data_labels = True
dl = plot.data_labels
dl.number_format = "#,##0"; dl.number_format_is_linked = False
dl.position = XL_LABEL_POSITION.OUTSIDE_END
dl.font.size = Pt(11); dl.font.color.rgb = C(INK)
tb(s, M, 6.1, 6.6, 0.3, [dict(text="BM25 通道 QPS(同进程 A/B,三轮取最好)· 结果与原暴力算法逐查询逐位等价(单元测试校验)", size=12, color=MUTED, line=1.1)])
chip(s, 7.4, 1.66, 1.7, 0.62, "10.0 ×", GREEN, WHITE, 16)
tb(s, 7.4, 2.34, 1.7, 0.3, [dict(text="当前语料", size=11.5, color=INK2, align=PP_ALIGN.CENTER)])
chip(s, 9.25, 1.66, 1.7, 0.62, "35 ×", GREEN, WHITE, 16)
tb(s, 9.25, 2.34, 1.7, 0.3, [dict(text="20× 语料扩展性", size=11.5, color=INK2, align=PP_ALIGN.CENTER)])
card(s, 7.4, 2.86, 5.44, 3.5, WHITE, LINE)
tb(s, 7.66, 3.06, 5.0, 0.4, [dict(text="F9 · 基准口径纠偏(如实)", size=15, bold=True, color=BRAND)])
tb(s, 7.66, 3.52, 4.95, 2.7, [
    dict(text="发现:bench.py 调用 retrieve() 未传 rerank,默认走了重排实验路径——测的与宣称的「默认链路」不是同一条。", size=12, color=INK2, space_after=6, line=1.25),
    dict(text="影响:2026-09-18 的 251.4 QPS 实为重排路径数值,生产 RRF 链路吞吐被低估。", size=12, color=INK2, space_after=6, line=1.25),
    dict(text="修正:跟随 RERANK_ENABLED 并在输出标注实际链路;修正后实测 515.8–880.4 QPS / p50 1.1–1.9ms,历史值保留并注明口径。", size=12, color=INK2, line=1.25),
])
notes(s, "F6 讲扩展性:倒排索引让 BM25 通道在 20 倍语料下从 68 QPS 提到 2,587 QPS,且与原算法逐位等价——性能优化不改行为。F9 讲诚实:基准脚本自己测错了路径,修正后数字更好看,但更重要的是口径终于干净。")

# ---------------------------------------------------------------- 15 工程方法
s = blank(prs)
header(s, "工程方法", "评测驱动 · 如实原则:数字怎么来,就怎么写", 15)
items = [
    ("评测驱动", "62 条口语化改写评测集是第一工具:停用词 bug、候选池截断、文档级去重缺失……三个真实缺陷均由评测指标异常暴露,再定位修复", BRAND),
    ("如实原则", "TF-IDF 非语义嵌入主动声明;指标口径演变全程留痕(旧值 95.2 → 98.4 并存);商业定价标注「假设示例」", PURPLE),
    ("追踪矩阵", "需求 → 质量属性 → ADR → 模块 → 测试 → 证据 六级串联,完善轮 9 项修复同样入矩阵(traceability.md §六)", "0E9A57"),
    ("全量可复现", "一条命令复现全部指标:pytest 13 项 / eval_matrix 四路 / bench 拆分 / acceptance 四项,环境与口径写入复现指南", "946200"),
]
for i, (t, d, accent) in enumerate(items):
    x = M + (i % 2) * 6.33; y = 1.66 + (i // 2) * 2.52
    card(s, x, y, 6.0, 2.32, WHITE, LINE)
    circle_num(s, x + 0.28, y + 0.26, 0.56, str(i + 1), accent, WHITE, 16)
    tb(s, x + 1.05, y + 0.28, 4.7, 0.4, [dict(text=t, size=16.5, bold=True, color=INK)])
    tb(s, x + 0.3, y + 0.88, 5.45, 1.3, [dict(text=d, size=12, color=INK2, line=1.3)])
notes(s, "这页讲方法论,也是这门课想展示的软实力:评测集是第一工具;数字如实——包括不利的历史值和口径事故;追踪矩阵让每个需求都能落到证据;任何人 clone 仓库一条命令复现全部数字。")

# ---------------------------------------------------------------- 16 总结与展望
s = blank(prs)
header(s, "总结与展望", "交付了什么,下一步去哪", 16)
card(s, M, 1.62, 6.0, 4.92, WHITE, LINE)
tb(s, M + 0.3, 1.86, 5.4, 0.4, [dict(text="已交付", size=16.5, bold=True, color=BRAND)])
dones = [
    "可运行的 AI+RAG 系统:双通道检索 / 流式生成 / 引用溯源 / 知识热更新",
    "质量闭环:62 条评测 + 四项架构验收 + 性能基准,全绿且可复现",
    "文档交付物:22 页架构设计文档(含追踪矩阵)+ 经济适用型与运营方案 + 答辩 PPT 与讲解视频",
    "完善轮加固:9 项缺陷修复,安全、性能、口径三面收口(github.com/yelikour/campus-qa)",
]
dy = 2.4
for d in dones:
    card(s, M + 0.3, dy, 5.4, 0.92, TINT, None)
    tb(s, M + 0.52, dy + 0.10, 4.98, 0.74, [dict(text=d, size=12, color=INK, line=1.2)], anchor=MSO_ANCHOR.MIDDLE)
    dy += 1.02
card(s, 6.83, 1.62, 6.0, 4.92, WHITE, LINE)
tb(s, 7.13, 1.86, 5.4, 0.4, [dict(text="下一步", size=16.5, bold=True, color=PURPLE)])
nexts = [
    ("Cross-Encoder 重排", "轻量词面重排实测无收益已默认关闭;替换 bge-reranker 后重开评测,验证排序增益"),
    ("真语义向量评测", "配置 ZHIPUAI_API_KEY 后补测 embedding-3 四路指标——F1 的标准 RRF 正是为该场景修正"),
    ("生产化部署", "Nginx 反代(SSE 直通)· Redis 滑动窗口限流 · ADMIN_TOKEN 启用写接口鉴权"),
    ("容量与成本", "按运营方案扩展三级:uvicorn workers → 多实例 → 限流外置,扩容单位约 ¥30/月/台"),
]
ny = 2.4
for t, d in nexts:
    chip(s, 7.13, ny + 0.08, 1.9, 0.4, t, "F0EBFF", PURPLE, 11.5)
    tb(s, 9.2, ny, 3.5, 0.92, [dict(text=d, size=11, color=INK2, line=1.18)])
    ny += 1.02
notes(s, "收尾:左边是可验证的交付物清单,右边是诚实的技术债与计划。重点讲前两条:重排和语义向量评测是检索质量的上限空间,F1/F9 的修正正是为这两步铺路。")

# ---------------------------------------------------------------- 17 封底
s = blank(prs, DARK)
tb(s, 0.9, 2.3, 11.5, 1.2, [dict(text="谢谢观看 · 欢迎提问", size=44, bold=True, color=WHITE, align=PP_ALIGN.CENTER)])
tb(s, 0.9, 3.55, 11.5, 0.4,
   [dict(text="所有数字可复现 · 所有缺陷有编号 · 所有结论留证据", size=16, color=BRAND_L, align=PP_ALIGN.CENTER)])
stats = [("62 条", "口语化评测"), ("80.6%", "Hit@1 · BM25"), ("880 QPS", "检索吞吐峰值"),
         ("4 / 4", "架构验收"), ("9 项", "完善轮修复")]
for i, (v, k) in enumerate(stats):
    x = 1.35 + i * 2.2
    card(s, x, 4.5, 2.0, 1.1, DARK_CARD, None)
    tb(s, x + 0.1, 4.66, 1.8, 0.85, [
        dict(text=v, size=20, bold=True, color=BRAND_L, space_after=2, align=PP_ALIGN.CENTER),
        dict(text=k, size=11.5, color=DARK_MUTED, align=PP_ALIGN.CENTER),
    ])
tb(s, 0.9, 6.15, 11.5, 0.35,
   [dict(text="github.com/yelikour/campus-qa · 智问校园 CampusMind · 《软件体系结构》课程项目", size=13, color=DARK_MUTED, align=PP_ALIGN.CENTER)])
notes(s, "结束页停留:回顾五个关键数字。提问引导:检索质量上限(Cross-Encoder/语义向量)、完善轮的发现方法、运营成本模型,都是可以展开的话题。")

prs.save(str(OUT))
print("saved:", OUT, "slides:", len(prs.slides.__iter__.__self__._sldIdLst))
