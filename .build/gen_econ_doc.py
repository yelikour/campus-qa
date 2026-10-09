#!/usr/bin/env python3
"""生成《智问校园 CampusMind 经济适用型与运营方案》DOCX。

配套答辩 PPT 第 17–19 页「经济适用型」章节的完整支撑文档:
售卖模式 / 部署与运营成本 / 大模型调用成本 / 高并发容量 / 反向代理。

口径原则(与项目诚实实验原则一致):
- 实测数字引用 scripts/bench.py(2026-09-18)与评测矩阵,可复现;
- 外部价格为 2026-10 时点查询的公开市场/活动价,均标注来源与波动风险;
- 商业定价为假设示例,非承诺。
"""
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

PRIMARY = RGBColor(0x3B, 0x5B, 0xFD)
ACCENT = RGBColor(0xE0, 0x5A, 0x00)
MUTED = RGBColor(0x6A, 0x73, 0x90)

doc = Document()
for sec in doc.sections:
    sec.top_margin, sec.bottom_margin = Cm(2.4), Cm(2.2)
    sec.left_margin, sec.right_margin = Cm(2.6), Cm(2.6)


def set_font(run, east="宋体", ascii_f="Times New Roman", size=12, bold=False, color=None):
    run.font.name = ascii_f
    run._element.rPr.rFonts.set(qn("w:eastAsia"), east)
    run.font.size = Pt(size)
    run.font.bold = bold
    if color:
        run.font.color.rgb = color


def para(text="", size=12, bold=False, east="宋体", color=None, align=None, space_after=6, indent=None):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = 1.35
    if align:
        p.alignment = align
    if indent:
        p.paragraph_format.first_line_indent = Pt(indent)
    if text:
        r = p.add_run(text)
        set_font(r, east=east, size=size, bold=bold, color=color)
    return p


def h1(num, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(14)
    p.paragraph_format.space_after = Pt(8)
    p.paragraph_format.keep_with_next = True
    r = p.add_run(f"{num}  {text}")
    set_font(r, east="黑体", size=16, bold=True, color=PRIMARY)


def h2(text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.keep_with_next = True
    r = p.add_run(text)
    set_font(r, east="黑体", size=13, bold=True)


def table(headers, rows, widths=None, font_size=10.5):
    t = doc.add_table(rows=len(rows) + 1, cols=len(headers))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for j, htext in enumerate(headers):
        cell = t.rows[0].cells[j]
        cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = cell.paragraphs[0].add_run(htext)
        set_font(r, east="黑体", size=font_size, bold=True)
        shd = OxmlElement("w:shd"); shd.set(qn("w:fill"), "E9EDFF")
        cell._tc.get_or_add_tcPr().append(shd)
    for i, row in enumerate(rows, 1):
        for j, ctext in enumerate(row):
            cell = t.rows[i].cells[j]
            r = cell.paragraphs[0].add_run(str(ctext))
            set_font(r, size=font_size)
            if i % 2 == 0:
                shd = OxmlElement("w:shd"); shd.set(qn("w:fill"), "F7F8FC")
                cell._tc.get_or_add_tcPr().append(shd)
    # 分页友好:首行跨页重复表头,数据行不在行内断开
    trPr = t.rows[0]._tr.get_or_add_trPr()
    tblHeader = OxmlElement("w:tblHeader"); tblHeader.set(qn("w:val"), "true")
    trPr.append(tblHeader)
    for row in t.rows:
        rpr = row._tr.get_or_add_trPr()
        cant = OxmlElement("w:cantSplit")
        rpr.append(cant)
    if widths:
        for j, w in enumerate(widths):
            for row in t.rows:
                row.cells[j].width = Cm(w)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return t


def code_block(lines):
    for line in lines:
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.left_indent = Pt(18)
        p.paragraph_format.line_spacing = 1.15
        r = p.add_run(line)
        r.font.name = "Consolas"
        r._element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")
        r.font.size = Pt(9.5)
        r.font.color.rgb = RGBColor(0x1C, 0x23, 0x33)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def note(text):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(8)
    r = p.add_run(text)
    set_font(r, size=10, color=MUTED)


# ---------------- 封面区 ----------------
para("智问校园 CampusMind", size=22, bold=True, east="黑体", color=PRIMARY,
     align=WD_ALIGN_PARAGRAPH.CENTER, space_after=4)
para("经济适用型与运营方案", size=26, bold=True, east="黑体",
     align=WD_ALIGN_PARAGRAPH.CENTER, space_after=10)
para("—— 系统怎么卖、真实成本多少、怎么扛并发 ——", size=13, color=MUTED,
     align=WD_ALIGN_PARAGRAPH.CENTER, space_after=14)
para("《软件体系结构》课程项目补充交付物 · 2026 年 10 月 · "
     "王若璋 · 何俐 · 郭祚梁", size=11, color=MUTED,
     align=WD_ALIGN_PARAGRAPH.CENTER, space_after=16)

p = para(space_after=12)
r = p.add_run("口径声明(诚实原则)")
set_font(r, east="黑体", size=11, bold=True, color=ACCENT)
para("本方案所有数字分三类,均如实标注:① 实测数字来自本项目可复现脚本"
     "(scripts/bench.py、eval_matrix.py,2026-09-18 运行);② 外部价格为 2026 年 10 月"
     "查询的公开市场价/新用户活动价,存在波动与续费涨价风险,以官方页面为准;"
     "③ 商业定价(SaaS 订阅价、买断价)为商业假设示例,不是承诺。"
     "此外,大模型调用成本一律按真实收费价核算,不依赖任何限时免费活动"
     "(现行免费活动仅作如实备注、未计入方案)。四者不混用、不夸大。", size=10.5)

# ---------------- 1 摘要 ----------------
h1("1", "摘要:为什么「经济适用」是架构决策的自然结果")
para("本系统的全部架构决策(生成端插件化、本地抽取式兜底、内存索引热更新、"
     "模块化单体)共同导向一个经济结论:默认链路 0 GPU,云端生成按真实收费价"
     "核算在保守档下也仅约两百元/月,一台入门级云服务器即可承载一所高校的"
     "日常问答量。这使得系统可以以可控的、可预测的边际成本售卖和运营——"
     "免费版靠本地抽取式生成真正零成本获客,付费版在数百元月成本上构建毛利,"
     "且任何情况下可切回本地生成,成本存在硬上限。", indent=24)
para("三个关键事实支撑上述判断:", space_after=4)
table(["事实", "数值", "来源"],
      [["单实例全链路吞吐(E2E,含流式生成)", "44.1 QPS · p99 611ms · 0 失败", "scripts/bench.py 实测"],
       ["云端生成模型按量计费(保守档)", "¥1/百万 token → 日均 5,000 问 ≈¥195/月", "公开定价档位 × 代码 token 估算"],
       ["本地兜底生成", "内置抽取式生成器,离线 0 成本", "代码实现,验收 A1 通过"]],
      widths=[6.2, 5.6, 4.2])
note("说明:E2E 指从 HTTP 请求进入至流式回答完成的完整链路;44.1 QPS 为"
     "local-extractive 提供者、并发 20、200 样本的实测口径。")

# ---------------- 2 售卖模式 ----------------
h1("2", "售卖模式:三档产品矩阵")
para("按「数据敏感度 × 运维能力」划分客群,提供三档产品形态:", indent=24, space_after=8)
table(["模式", "定价(假设示例)", "目标客群与场景", "我方成本"],
      [["SaaS 订阅(推荐起步)", "¥4,999 /校/年",
        "中小院校/高职:零运维,我方托管,含升级维保,先试用后签约",
        "服务器 + 按量 API(保守价),≈¥210–230/月"],
       ["私有化部署买断", "¥29,999 买断 + 15%/年维保",
        "数据不出校的高校:部署进校园内网,复用校内已有虚拟机",
        "一次性实施(人力),运行成本由校方承担,边际≈0"],
       ["免费社区版", "¥0",
        "获客入口:本项目形态直接可用,本地抽取式生成零 API 成本",
        "近零(用户自部署)"]],
      widths=[3.2, 3.6, 5.6, 3.6])
h2("2.1 销售路径")
para("高校信息化采购以年度预算与项目制为主,路径设计为:① 免费社区版在"
     "院系/社团级试点,积累真实问答数据与口碑;② 试用期结束后以 SaaS 订阅"
     "进入校级预算(定价低于一次人工咨询外包的月度成本);③ 对数据合规要求"
     "高的学校升级为私有化买断。三档形态共享同一代码基座,仅为部署方式与"
     "合同形态差异——这直接降低了多形态维护成本。", indent=24)
h2("2.2 定价依据")
para("SaaS 年费 ¥4,999 对应我方直接成本约 ¥2,520–2,760/年(服务器 ¥165–379/年"
     "+ 域名证书 ≈¥60/年 + 保守档 API ≈¥2,340/年,按日均 5,000 问、¥1/百万 "
     "token),毛利率约 44%;若大模型处于历史挂牌价档(GLM-4-Flash 付费时期 "
     "¥0.06–0.1/百万 token),API 仅 ≈¥144–240/年,毛利率升至约 88%。两档真实"
     "价位下定价均有安全垫,方案不依赖任何限时免费活动。私有化买断价对标"
     "同类校园知识库项目人天实施费(约 15–25 人天)。", indent=24)

# ---------------- 3 部署方案与成本 ----------------
h1("3", "部署方案与月度成本核算")
table(["方案", "适用场景", "服务器", "大模型", "月成本估算"],
      [["A 云端 SaaS(我方托管)", "绝大多数学校",
        "轻量 2C4G:阿里云 ¥379/年或腾讯云 ¥165–220/年(新用户活动价) ≈ ¥14–32/月",
        "GLM 按量计费,保守档 ¥1/百万 token(日均 5,000 问 ≈¥195/月);embedding-3 重建 ≈¥0.01/次",
        "≈ ¥210–230/月"],
       ["B 私有化 CPU(校内虚机)", "数据不出校",
        "复用校内已有虚拟机(2C4G 即可),边际成本 ¥0",
        "校方自备 API Key,或使用本地抽取式(¥0)",
        "边际 ≈ ¥0"],
       ["C 全离线 GPU(内网隔离)", "数据最敏感",
        "RTX 4090 租用包月 ¥1,000–1,500;或买断二手 4090 ≈¥15,000(电费另计 ≈¥190/月)",
        "本地量化模型(GLM/Qwen 7B AWQ · vLLM/Ollama)",
        "≈ ¥1,000–1,500/月"]],
      widths=[3.0, 2.2, 4.4, 3.8, 2.6], font_size=9.5)
note("价格时点 2026-10:轻量服务器为新用户活动价,续费价更高;GPU 价格来自"
     "算力租赁平台公开报价区间。方案 C 仅在要求数据完全不出内网时选择,"
     "对本项目目标场景(公开校务知识问答)通常不必要。")
h2("3.1 部署形态(Docker 单机起步)")
para("生产最小形态为「1 台服务器 + Docker Compose + Nginx」:应用容器"
     "(uvicorn --workers 4)+ Nginx 反代(TLS 终止、静态直出、SSE 直通)。"
     "无需向量数据库、无需消息队列、无需 GPU——检索索引常驻内存,SQLite "
     "单文件存储,备份即复制文件。", indent=24)

# ---------------- 4 大模型调用成本 ----------------
h1("4", "大模型调用成本:Token 构成与敏感性测算")
h2("4.1 每问 Token 构成(按实现代码估算)")
table(["构成", "内容", "估算量级"],
      [["系统提示", "角色设定+引用约束,约 60 字", "≈60 token"],
       ["检索上下文", "Top-3 知识条目(FINAL_TOP_K=3),每条约 150–400 字", "≈900 token"],
       ["用户问题", "口语化提问", "≈20 token"],
       ["模型输出", "分点回答+来源标注", "≈300 token"],
       ["合计", "输入 ≈1,000 + 输出 ≈300", "≈1,300 token/问"]],
      widths=[3.0, 7.8, 3.2])
note("估算口径:中文按 1 字≈1 token 保守计;实际取决于分词器,量级不变。")
h2("4.2 生成端成本:真实收费价三档")
table(["计价情景", "单价", "每问成本", "日均 5,000 问月成本"],
      [["历史挂牌价档(GLM-4-Flash 付费时期公开价)", "¥0.06–0.1 / 百万 token", "≈¥0.0001", "≈¥12–20/月"],
       ["保守档(方案基准,当代主力模型价位)", "¥1 / 百万 token", "≈¥0.0013", "≈¥195/月"],
       ["压力上限档", "¥5 / 百万 token", "≈¥0.0065", "≈¥975/月"]],
      widths=[6.2, 3.2, 2.6, 4.0])
note("现行官方对 GLM-4-Flash 有限时免费活动,本方案未计入该优惠,一律按"
     "常态收费价核算;免费活动若持续仅为额外安全垫。")
para("三档真实价位下 SaaS 定价均有毛利(§2.2 给出基准档与历史档测算);且系统"
     "可随时切回本地抽取式生成(验收 A1 的降级路径),成本存在硬上限——这是"
     "「双模生成架构」在商业上的直接价值:API 价格波动不构成经营风险。", indent=24)
h2("4.3 Embedding 成本")
para("embedding-3 约 0.5 元/百万 token 档。当前 62 条知识全量重建 ≈2 万 "
     "token ≈¥0.01,仅在知识库变更时发生;扩展到 5,000 条知识(≈160 万 "
     "token)单次重建也仅 ≈¥0.8。相对服务器租金可忽略。", indent=24)
h2("4.4 若坚持本地部署大模型(方案 C 补充)")
para("4090(24GB)可流畅运行 7B–14B 量化模型(vLLM,AWQ/GPTQ),满足校园问答"
     "质量需求。租用包月 ¥1,000–1,500;若买断二手 4090(≈¥15,000),按电费 "
     "450W×24h×30 天×¥0.6/度 ≈¥190/月,约 12–15 个月收回买断成本(相对租用)。"
     "注意 2026 年市场仍存在高端卡供应紧张(「抢卡」)现象,采购周期需预留。", indent=24)

# ---------------- 5 高并发 ----------------
h1("5", "高并发:实测容量与扩展规划")
h2("5.1 容量外推(基于实测)")
para("容量估算口径:日问量集中在约 8 小时活跃时段,峰值按均值×10 保守估计。"
     "单实例 44.1 QPS 为下限基准(未开多 worker)。", indent=24, space_after=6)
table(["场景", "日问量", "峰值 RPS(估)", "所需配置", "月服务器成本"],
      [["单校 1 万人", "5,000", "<3", "1× 2C4G 单实例", "≈¥32"],
       ["10 校 SaaS", "50,000", "≈20–30", "1× 4C8G(workers 4)或 2× 2C4G", "≈¥65–100"],
       ["50 校 SaaS", "250,000", "≈90–150", "4× 4C8G + Nginx 负载均衡", "≈¥390"],
       ["远期千级 QPS", "—", "1,000", "≈25 实例 + Nginx", "≈¥800"]],
      widths=[3.2, 2.4, 3.0, 4.6, 3.0])
para("结论:校园场景的并发压力远低于单实例容量(余量 10 倍以上),「高并发」"
     "对本系统是线性加机器问题而非架构难题;容量与成本线性挂钩,无雪崩点。", indent=24)
h2("5.2 扩展三级路径")
para("① 进程内:uvicorn --workers 4,同机吞吐约 2–3 倍(CPU 核数限制);"
     "② 主机间:Nginx 反向代理多实例负载均衡,应用层无状态设计(会话不落本机),"
     "加机器即扩容;③ 组件级:限流计数与会话外置 Redis(与部署演进页的四项"
     "替换一致:SQLite→PG、内存索引→Milvus、本地→GLM、代理→Redis)。"
     "每一级都是独立的、可单独决策的演进步骤。", indent=24)

# ---------------- 6 反向代理 ----------------
h1("6", "反向代理与生产部署拓扑(Nginx)")
para("生产拓扑:客户端 → Nginx(443,TLS 终止)→ 应用实例×N(uvicorn :8000)。"
     "Nginx 承担四项职责:TLS 终止、静态资源直出、SSE 流式直通、入口级限流。", indent=24)
h2("6.1 关键配置(SSE 直通是重中之重)")
code_block([
    "upstream campusmind {",
    "    least_conn;",
    "    server 127.0.0.1:8000;      # uvicorn app.main:app --workers 4",
    "    # server 10.0.0.12:8000;    # 扩容时追加实例",
    "}",
    "limit_req_zone $binary_remote_addr zone=qa:10m rate=10r/s;",
    "",
    "server {",
    "    listen 443 ssl;",
    "    server_name qa.example.edu.cn;",
    "    ssl_certificate     /etc/letsencrypt/live/qa/fullchain.pem;",
    "    ssl_certificate_key /etc/letsencrypt/live/qa/privkey.pem;",
    "",
    "    location /api/ {                     # SSE 流式问答接口",
    "        limit_req zone=qa burst=20 nodelay;   # 入口级限流(第一层)",
    "        proxy_pass http://campusmind;",
    "        proxy_buffering off;             # 关键:SSE 直通,禁用响应缓冲",
    "        proxy_cache off;",
    "        proxy_http_version 1.1;",
    "        proxy_set_header Connection \"\";",
    "        proxy_read_timeout 60s;          # 防长回答被默认超时掐断",
    "        proxy_set_header X-Real-IP $remote_addr;",
    "        add_header X-Accel-Buffering no; # 双保险",
    "    }",
    "    location /static/ { root /var/www/campusmind; expires 7d; }",
    "    location /  { proxy_pass http://campusmind; }",
    "}",
])
h2("6.2 双层限流说明")
para("Nginx limit_req(IP 级,10 r/s+突发 20)负责挡掉恶意脚本与突发扫描;"
     "应用内令牌桶(5 QPS/用户,突发 10,验收 A2 实测)负责业务级公平性。"
     "两层职责不同:前者保护整机,后者保护单用户体验。生产多实例时应用层"
     "限流计数外置 Redis,避免各实例独立计数导致限流阈值被 N 倍放大。", indent=24)

# ---------------- 7 运营模型 ----------------
h1("7", "运营成本模型:SaaS 单校月度损益示例(真实收费价)")
table(["项目", "历史挂牌价档(¥0.06–0.1/百万)", "保守档(¥1/百万,方案基准)"],
      [["收入(¥4,999/年 ÷ 12)", "¥417/月", "¥417/月"],
       ["服务器(2C4G 活动价)", "¥32/月", "¥32/月"],
       ["域名 + TLS(Let's Encrypt 免费,域名 ≈¥60/年)", "¥5/月", "¥5/月"],
       ["对象存储备份(≈10GB)", "¥3/月", "¥3/月"],
       ["大模型 API(日均 5,000 问,按真实收费价)", "¥12–20/月", "¥195/月"],
       ["直接成本小计", "≈¥52–60/月", "≈¥235/月"],
       ["直接毛利", "≈¥357–365/月(86–88%)", "≈¥182/月(44%)"]],
      widths=[6.6, 4.2, 4.2])
note("诚实标注:两列均为真实收费价口径(免费活动未计入,若免费持续仅是"
     "额外安全垫)。本表仅含直接资源成本,不含人力(实施、维保响应、知识库"
     "代运营)与获客成本;3 人团队按兼职运营假设,10 校规模下人力成本被"
     "摊薄,模型才真正成立。")

# ---------------- 8 风险与局限 ----------------
h1("8", "风险与局限(如实)")
para("① 计价风险:本方案不依赖限时免费活动,按真实收费价核算;若厂商调价,"
     "§4.2 三档区间覆盖至 ¥5/百万 token 仍有毛利,且可随时切回本地抽取式"
     "生成(¥0),成本存在硬上限;② 活动价风险:服务器与 GPU 价格引用的是"
     "2026-10 新用户活动价/市场区间,续费与量产价更高,采购前以官方页面为准;"
     "③ 并发数字口径:44.1 QPS 为 local-extractive 提供者的实测,云端 GLM "
     "模式下吞吐受 API 时延影响,首字延迟取决于网络;④ token 估算为代码"
     "静态估算,非线上埋点实测;⑤ 商业定价为课堂假设,未经真实市场验证;"
     "⑥ 方案 C 的 GPU 市场存在供应波动,成本与交付周期需预留余量。", indent=24)

# ---------------- 9 价格来源 ----------------
h1("9", "价格来源(2026-10 查证)")
for line in [
    "· 智谱开放平台:GLM-4-Flash 付费时期历史挂牌价 ¥0.06–0.1/百万 token;",
    "  当代主力模型公开档位约 ¥1/百万 token;embedding-3 约 0.5 元/百万 token 档。",
    "  (现行 GLM-4-Flash 限时免费活动未计入本方案,仅如实备注。)",
    "· 阿里云/腾讯云轻量应用服务器活动价页:2C4G ¥165–379/年;4C8G ¥1,159/年(新用户专享)。",
    "· 算力租赁平台公开报价(AutoDL 等):RTX 4090 时租 ¥1.65–1.98,包月 ¥1,000–1,500;",
    "  二手 4090 市场价 ≈¥15,000(2026 年中)。",
    "· 电费按居民/校园电价 ¥0.6/度估算。",
    "· 性能与验收数字:本项目 scripts/bench.py、scripts/acceptance.py 实测存档",
    "  (artifacts/final_validation.txt),可复现。",
]:
    para(line, size=10.5, space_after=2)

doc.save("/Users/yaya/SHU/2601/软件体系结构/campus-qa/docs/智问校园CampusMind经济适用型与运营方案.docx")
print("DOCX saved")
