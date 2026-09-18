#!/usr/bin/env python3
"""生成架构设计文档与答辩 PPT 所需的三张架构图(matplotlib 绘制)。"""
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

plt.rcParams["font.sans-serif"] = ["PingFang SC", "Hiragino Sans GB", "Arial Unicode MS"]
plt.rcParams["axes.unicode_minus"] = False

C_LAYER = ["#e8edff", "#e3f0ff", "#dcf5ec", "#fdf0dd", "#f6e3ff"]
C_BOX = "#ffffff"
C_EDGE = "#5b79ff"
C_TEXT = "#1c2333"
C_SUB = "#5a6478"


def box(ax, x, y, w, h, text, sub=None, fc=C_BOX, ec=C_EDGE, fs=11, bold=True, lw=1.4):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.06",
                                fc=fc, ec=ec, lw=lw))
    cx, cy = x + w / 2, y + h / 2
    if sub:
        ax.text(cx, cy + h * 0.16, text, ha="center", va="center", fontsize=fs,
                fontweight="bold" if bold else "normal", color=C_TEXT)
        ax.text(cx, cy - h * 0.22, sub, ha="center", va="center", fontsize=fs - 2.5, color=C_SUB)
    else:
        ax.text(cx, cy, text, ha="center", va="center", fontsize=fs,
                fontweight="bold" if bold else "normal", color=C_TEXT)


def arrow(ax, x1, y1, x2, y2, style="-|>", color=C_EDGE, lw=1.6, ls="-", label=None, lx=None, ly=None, fs=9):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle=style, mutation_scale=14,
                                 color=color, lw=lw, linestyle=ls))
    if label:
        ax.text(lx if lx is not None else (x1 + x2) / 2, ly if ly is not None else (y1 + y2) / 2 + 0.03,
                label, ha="center", va="bottom", fontsize=fs, color="#3b5bfd")


# ══════════════════════ 图1:总体分层架构 ══════════════════════
fig, ax = plt.subplots(figsize=(11.5, 8.2), dpi=200)
ax.set_xlim(0, 10); ax.set_ylim(0, 10.6); ax.axis("off")

layers = [
    ("接入层", ["Web 聊天前端\n(SPA · SSE 流式渲染)", "知识库管理端\n(录入 / 检索 / 热更新)", "运行看板\n(统计 / 监控)", "开放 API\n(预留 · 移动端)"]),
    ("网关边界层", ["统一路由 / 反向代理(Nginx)", "CORS · 静态资源托管", "限流(令牌桶 → Redis)", "认证(X-User-Token → JWT)"]),
    ("应用服务层", ["问答编排服务\nchat · SSE", "知识管理服务\nknowledge", "会话服务\nconversations", "运维统计服务\nadmin/stats"]),
    ("RAG 引擎层", ["摄取管道\n清洗 · QA分块", "混合检索\nBM25 ∥ 向量", "RRF 融合\n+ 重排序", "生成 Provider\n本地抽取式 / GLM"]),
    ("数据层", ["业务库\nSQLite(演示)→ PostgreSQL", "知识语料\ncampus_qa.json", "内存倒排/向量索引\n(热更新)", "向量数据库\n(生产:Milvus/pgvector)"]),
]
y = 10.3
H, GAP = 1.5, 0.42
for i, (name, items) in enumerate(layers):
    y -= H
    ax.add_patch(FancyBboxPatch((0.7, y), 9.0, H, boxstyle="round,pad=0.02,rounding_size=0.08",
                                fc=C_LAYER[i], ec="#c9d4f5", lw=1))
    ax.text(0.52, y + H / 2, name, rotation=90, ha="center", va="center",
            fontsize=10.5, fontweight="bold", color="#3b5bfd")
    bw = 2.02
    for j, it in enumerate(items):
        box(ax, 1.0 + j * (bw + 0.1), y + 0.19, bw, H - 0.38, it, fs=8.8, bold=False, lw=1)
    if i < len(layers) - 1:
        arrow(ax, 5.2, y, 5.2, y - GAP, lw=2)

ax.text(5.2, 0.28, "▼  一次提问的纵向调用链:接入 → 编排 → 检索 → 生成 → 溯源  ▼",
        ha="center", va="center", fontsize=10.5, color="#3b5bfd", fontweight="bold")
ax.set_title("图 1  「智问校园」总体分层架构(逻辑视图)", fontsize=14, fontweight="bold", pad=14)
plt.tight_layout(); plt.savefig("/Users/yaya/SHU/2601/软件体系结构/campus-qa/docs/assets/arch_layers.png",
                                bbox_inches="tight", facecolor="white"); plt.close()

# ══════════════════════ 图2:RAG 问答核心时序 ══════════════════════
fig, ax = plt.subplots(figsize=(12.5, 7.6), dpi=200)
ax.set_xlim(0, 12); ax.set_ylim(0, 10); ax.axis("off")

actors = [("学生用户", 1.1), ("Web 前端\n(SPA)", 3.2), ("问答编排\nAPI", 5.4), ("混合检索\n服务", 7.6), ("生成服务\nProvider", 9.8), ("数据层\nSQLite/索引", 11.6)]
for name, x in actors:
    box(ax, x - 0.85, 9.05, 1.7, 0.72, name, fs=9.5, lw=1.3)
    ax.plot([x, x], [0.5, 9.05], color="#c9d4f5", lw=1.1, ls=(0, (4, 3)))

steps = [
    ("① 输入问题", 1.1, 3.2, 8.45),
    ("② POST /api/chat(限流检查)", 3.2, 5.4, 7.75),
    ("③ retrieve(query)", 5.4, 7.6, 7.05),
    ("④ BM25 检索 ∥ 向量检索(并行)", 7.6, 7.6, 6.35),
    ("⑤ RRF 融合 → 重排序 Top-K", 7.6, 7.6, 5.65),
    ("⑥ 返回候选片段+分数", 7.6, 5.4, 4.95),
    ("⑦ event: meta(引用来源先行推送)", 5.4, 3.2, 4.25),
    ("⑧ stream 生成(本地抽取式 / GLM API)", 5.4, 9.8, 3.55),
    ("⑨ event: delta × N(token 流)", 9.8, 3.2, 2.85),
    ("⑩ 落库(消息/查询日志)", 5.4, 11.6, 2.15),
    ("⑪ event: done(耗时/会话ID)", 5.4, 3.2, 1.45),
    ("⑫ 渲染回答 + 引用溯源卡片", 3.2, 1.1, 0.75),
]
for label, x1, x2, yv in steps:
    solid = not label.startswith(("④", "⑤"))
    arrow(ax, x1, yv, x2, yv, ls="-" if solid else "--", lw=1.5,
          color="#3b5bfd" if solid else "#7c4dff", label=label,
          lx=(x1 + x2) / 2, ly=yv + 0.04, fs=8.8)
ax.set_title("图 2  RAG 问答核心链路时序(SSE 流式 + 引用溯源)", fontsize=14, fontweight="bold", pad=10)
plt.tight_layout(); plt.savefig("/Users/yaya/SHU/2601/软件体系结构/campus-qa/docs/assets/arch_sequence.png",
                                bbox_inches="tight", facecolor="white"); plt.close()

# ══════════════════════ 图3:部署视图 ══════════════════════
fig, ax = plt.subplots(figsize=(11.5, 6.8), dpi=200)
ax.set_xlim(0, 12); ax.set_ylim(0, 7.6); ax.axis("off")

# 演示环境
ax.add_patch(FancyBboxPatch((0.2, 0.35), 5.4, 6.6, boxstyle="round,pad=0.02,rounding_size=0.1",
                            fc="#f4f8ff", ec="#b9c6ff", lw=1.4))
ax.text(2.9, 6.6, "演示/开发环境(单机 · 离线可跑)", ha="center", fontsize=12, fontweight="bold", color="#3b5bfd")
box(ax, 0.55, 5.35, 4.7, 0.78, "浏览器(前端 SPA)", sub="http://127.0.0.1:8000 · FastAPI StaticFiles 托管", fs=10)
box(ax, 0.55, 4.15, 4.7, 0.78, "FastAPI 应用(单体分层)", sub="uvicorn · 限流(进程内令牌桶)", fs=10)
box(ax, 0.55, 2.95, 4.7, 0.78, "RAG 引擎(进程内)", sub="BM25 + TF-IDF 向量 + RRF + 轻量重排 + 抽取式生成", fs=9.5)
box(ax, 0.55, 1.75, 4.7, 0.78, "SQLite + JSON 语料", sub="campusqa.db(WAL) · campus_qa.json", fs=10)
box(ax, 0.55, 0.62, 4.7, 0.78, "LLM Provider:本地抽取式(默认)", sub="零外部依赖 · 熔断降级兜底", fs=10, ec="#12b76a")
for y1, y2 in [(5.35, 4.93), (4.15, 3.73), (2.95, 2.53), (1.75, 1.40)]:
    arrow(ax, 2.9, y1, 2.9, y2, lw=1.5)

# 生产环境
ax.add_patch(FancyBboxPatch((6.3, 0.35), 5.5, 6.6, boxstyle="round,pad=0.02,rounding_size=0.1",
                            fc="#fdf9f2", ec="#f0d9b5", lw=1.4))
ax.text(9.05, 6.6, "生产部署方案(容器化 · 云端)", ha="center", fontsize=12, fontweight="bold", color="#c07a1a")
box(ax, 6.65, 5.35, 4.8, 0.78, "CDN + Nginx", sub="静态资源 · 反向代理 · TLS", fs=10)
box(ax, 6.65, 4.15, 2.28, 0.78, "FastAPI ×N\n(无状态水平扩展)", fs=9.5)
box(ax, 9.12, 4.15, 2.33, 0.78, "摄取 Worker\n(异步重建索引)", fs=9.5)
box(ax, 6.65, 2.95, 4.8, 0.78, "检索引擎升级", sub="Milvus / pgvector(语义向量)+ BM25 全文", fs=9.5)
box(ax, 6.65, 1.75, 4.8, 0.78, "PostgreSQL + Redis", sub="业务数据 · 限流计数 · 会话缓存", fs=10)
box(ax, 6.65, 0.62, 4.8, 0.78, "LLM Provider:GLM-4(云端)", sub="SSE 流式 · 超时熔断 → 本地降级", fs=10, ec="#c07a1a")
for y1, y2 in [(5.35, 4.93), (4.15, 3.73), (2.95, 2.53), (1.75, 1.40)]:
    arrow(ax, 9.05, y1, 9.05, y2, lw=1.5, color="#c07a1a")

arrow(ax, 5.6, 3.6, 6.3, 3.6, lw=2.2, style="-|>", color="#12b76a", label="平滑演进(接口不变)", ly=3.68, fs=10)
ax.set_title("图 3  部署视图:单机演示 → 生产集群的演进路径", fontsize=14, fontweight="bold", pad=10)
plt.tight_layout(); plt.savefig("/Users/yaya/SHU/2601/软件体系结构/campus-qa/docs/assets/arch_deploy.png",
                                bbox_inches="tight", facecolor="white"); plt.close()
print("diagrams done")
