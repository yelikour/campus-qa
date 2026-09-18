/* 《智问校园 CampusMind》答辩 PPT —— pptxgenjs,16:9 宽版(13.33x7.5")
 * 品牌:深空蓝紫(与系统 UI 一致)+ 橙色强调;三明治结构(深封面/浅内容/深结尾) */
const pptxgen = require("pptxgenjs");
const fs = require("fs");

const W = 13.33, H = 7.5, M = 0.55;
const DEEP = "171C36", DEEP2 = "232B52";
const BG = "F7F8FC", CARD = "FFFFFF";
const PRIMARY = "3B5BFD", PRIMARY_SOFT = "E9EDFF", PURPLE = "7C4DFF";
const ACCENT = "FF8A3D", ACCENT_SOFT = "FFF1E5";
const TEXT = "1C2333", MUTED = "6A7390", LINE = "E3E7F2";
const FONT = "PingFang SC";

const ROOT = "/Users/yaya/SHU/2601/\u8f6f\u4ef6\u4f53\u7cfb\u7ed3\u6784/campus-qa";
const ASSETS = `${ROOT}/docs/assets`;
const SHOTS = `${ROOT}/video/frames`;

let p = new pptxgen();
p.layout = "LAYOUT_WIDE";
p.author = "CampusMind \u9879\u76ee\u7ec4";
p.title = "\u667a\u95ee\u6821\u56ed CampusMind \u00b7 \u67b6\u6784\u7b54\u8fa9";

/* ---------- 组件工厂 ---------- */
const sh = () => ({ type: "outer", color: "232B52", blur: 8, offset: 2, angle: 60, opacity: 0.12 });
function page(s, n, total, title, sub) {
  s.background = { color: BG };
  if (title) {
    s.addText(title, { x: M, y: 0.32, w: W - 2 * M, h: 0.62, fontSize: 27, bold: true, color: TEXT, fontFace: FONT, margin: 0 });
    if (sub) s.addText(sub, { x: M, y: 0.94, w: W - 2 * M, h: 0.34, fontSize: 12.5, color: MUTED, fontFace: FONT, margin: 0 });
  }
  s.addText(`${n}`, { x: W - 0.75, y: H - 0.42, w: 0.45, h: 0.3, fontSize: 11, color: MUTED, fontFace: FONT, align: "right", margin: 0 });
}
function card(s, x, y, w, h, fill = CARD) {
  s.addShape(p.shapes.ROUNDED_RECTANGLE, { x, y, w, h, fill: { color: fill }, rectRadius: 0.09, line: { color: LINE, width: 0.75 }, shadow: sh() });
}
function stat(s, x, y, w, big, label, color = PRIMARY, sub) {
  s.addText(big, { x, y, w, h: 0.85, fontSize: 44, bold: true, color, fontFace: FONT, align: "center", margin: 0 });
  s.addText(label, { x, y: y + 0.88, w, h: 0.34, fontSize: 13, color: TEXT, bold: true, fontFace: FONT, align: "center", margin: 0 });
  if (sub) s.addText(sub, { x, y: y + 1.22, w, h: 0.3, fontSize: 10.5, color: MUTED, fontFace: FONT, align: "center", margin: 0 });
}
function bullets(s, items, opt) {
  const bu = () => ({ code: "25B8", indent: 12 });
  s.addText(items.map((t, i) => ({ text: t, options: { bullet: bu(), breakLine: i < items.length - 1 } })),
    { fontSize: 13, color: TEXT, fontFace: FONT, paraSpaceAfter: 8, margin: 0, valign: "top", ...opt });
}
function chip(s, x, y, w, text, fill = PRIMARY_SOFT, color = PRIMARY) {
  s.addShape(p.shapes.ROUNDED_RECTANGLE, { x, y, w, h: 0.34, fill: { color: fill }, rectRadius: 0.17, line: { type: "none" } });
  s.addText(text, { x, y: y + 0.015, w, h: 0.31, fontSize: 10.5, bold: true, color, fontFace: FONT, align: "center", margin: 0 });
}

/* ============ 1 封面 ============ */
let s = p.addSlide();
s.background = { color: DEEP };
s.addShape(p.shapes.RECTANGLE, { x: -2, y: -2.4, w: 9, h: 12, fill: { color: DEEP2, transparency: 55 }, rotate: 18, line: { type: "none" } });
s.addShape(p.shapes.RECTANGLE, { x: 7.6, y: -2.4, w: 9, h: 12, fill: { color: PRIMARY, transparency: 82 }, rotate: -14, line: { type: "none" } });
s.addShape(p.shapes.ROUNDED_RECTANGLE, { x: 5.7, y: 0.72, w: 1.9, h: 1.9, fill: { color: PRIMARY }, rectRadius: 0.32, line: { type: "none" }, shadow: sh() });
s.addText("\u667a", { x: 5.7, y: 0.72, w: 1.9, h: 1.9, fontSize: 66, bold: true, color: "FFFFFF", fontFace: FONT, align: "center", valign: "middle", margin: 0 });
s.addText("\u667a\u95ee\u6821\u56ed CampusMind", { x: 1.2, y: 2.9, w: W - 2.4, h: 1.0, fontSize: 51, bold: true, color: "FFFFFF", fontFace: FONT, align: "center", margin: 0 });
s.addText("\u57fa\u4e8e AI + RAG \u7684\u6821\u56ed\u667a\u80fd\u95ee\u7b54\u7cfb\u7edf \u00b7 \u8f6f\u4ef6\u4f53\u7cfb\u7ed3\u6784\u8bfe\u7a0b\u7b54\u8fa9", { x: 1.2, y: 3.98, w: W - 2.4, h: 0.5, fontSize: 19, color: "C9D2F5", fontFace: FONT, align: "center", margin: 0 });
[["\u6df7\u5408\u68c0\u7d22 BM25 \u2225 \u5411\u91cf", 3.35], ["RRF \u878d\u5408 + \u91cd\u6392\u5e8f", 5.75], ["SSE \u6d41\u5f0f\u751f\u6210", 7.8], ["\u5f15\u7528\u6eaf\u6e90", 9.45]].forEach(([t, x]) => {
  s.addShape(p.shapes.ROUNDED_RECTANGLE, { x, y: 4.78, w: t.length * 0.19 + 0.42, h: 0.4, fill: { color: DEEP2 }, rectRadius: 0.2, line: { color: "3D4A85", width: 0.75 } });
  s.addText(t, { x, y: 4.8, w: t.length * 0.19 + 0.42, h: 0.36, fontSize: 12, color: "AFBCF0", fontFace: FONT, align: "center", margin: 0 });
});
s.addText([
  { text: "\u6c47\u62a5\u4eba\uff1aCampusMind \u9879\u76ee\u7ec4\uff083\u20135 \u4eba\uff09", options: { breakLine: true } },
  { text: "2026 \u5e74 9 \u6708 18 \u65e5", options: {} },
], { x: 1.2, y: 6.15, w: W - 2.4, h: 0.75, fontSize: 13, color: "8B97C9", fontFace: FONT, align: "center", paraSpaceAfter: 4, margin: 0 });
s.addNotes("\u5f00\u573a:\u5927\u5bb6\u597d,\u6211\u4eec\u7684\u8bfe\u7a0b\u9879\u76ee\u662f\u667a\u95ee\u6821\u56ed\u2014\u2014\u4e00\u4e2a\u57fa\u4e8eAI+RAG\u7684\u6821\u56ed\u667a\u80fd\u95ee\u7b54\u7cfb\u7edf\u3002\u5148\u770b44\u79d2\u6f14\u793a\u518d\u5c55\u5f00\u8bb2\u67b6\u6784\u3002");

/* ============ 2 提纲 ============ */
s = p.addSlide();
page(s, 2, 16, "\u6c47\u62a5\u63d0\u7eb2", "\u4ece\u95ee\u9898\u5230\u67b6\u6784\u518d\u5230\u9a8c\u8bc1\uff0c\u56db\u4e2a\u73af\u8282\u5c55\u5f00");
const outline = [
  ["01", "\u80cc\u666f\u4e0e\u9700\u6c42", "\u75db\u70b9\u8c03\u7814 \u00b7 \u8d28\u91cf\u5c5e\u6027\u573a\u666f \u00b7 \u7ea6\u675f\u6761\u4ef6"],
  ["02", "\u67b6\u6784\u8bbe\u8ba1", "\u4e94\u5c42\u5206\u5c42 \u00b7 RAG \u6838\u5fc3\u94fe\u8def \u00b7 6 \u9879\u5173\u952e\u51b3\u7b56 ADR"],
  ["03", "\u5b9e\u73b0\u4e0e\u9a8c\u8bc1", "\u53ef\u8fd0\u884c\u7cfb\u7edf \u00b7 \u68c0\u7d22\u8bc4\u6d4b \u00b7 \u6027\u80fd\u538b\u6d4b \u00b7 \u6f14\u793a\u5f55\u5c4f"],
  ["04", "\u6f14\u8fdb\u4e0e\u603b\u7ed3", "\u5355\u673a\u2192\u751f\u4ea7\u6f14\u8fdb \u00b7 8 \u5468\u8ba1\u5212 \u00b7 \u521b\u65b0\u70b9"],
];
outline.forEach(([num, t, d], i) => {
  const y = 1.62 + i * 1.32;
  card(s, M, y, W - 2 * M, 1.1);
  s.addText(num, { x: M + 0.35, y: y + 0.14, w: 1.0, h: 0.82, fontSize: 34, bold: true, color: i % 2 ? PURPLE : PRIMARY, fontFace: FONT, margin: 0 });
  s.addText(t, { x: M + 1.5, y: y + 0.16, w: 3.6, h: 0.5, fontSize: 19, bold: true, color: TEXT, fontFace: FONT, margin: 0 });
  s.addText(d, { x: M + 1.5, y: y + 0.62, w: 9.5, h: 0.36, fontSize: 12.5, color: MUTED, fontFace: FONT, margin: 0 });
});
s.addNotes("\u56db\u4e2a\u73af\u8282:\u80cc\u666f\u9700\u6c42\u3001\u67b6\u6784\u8bbe\u8ba1\u3001\u5b9e\u73b0\u9a8c\u8bc1\u3001\u6f14\u8fdb\u603b\u7ed3\u3002");

/* ============ 3 背景与痛点 ============ */
s = p.addSlide();
page(s, 3, 16, "\u80cc\u666f\uff1a\u6821\u56ed\u54a8\u8be2\u7684\u4e09\u4e2a\u75db\u70b9", "\u8c03\u7814\u7ed3\u8bba\u9a71\u52a8\u9009\u9898\uff1a\u9ad8\u9891\u3001\u5206\u6563\u3001\u65e0\u53e3\u5f84");
const pains = [
  ["\u5206\u6563", "\u89c4\u7ae0\u5206\u5c5e\u4e0d\u540c\u90e8\u95e8\u7f51\u7ad9\uff0c\u5b66\u751f\u96be\u4ee5\u5b9a\u4f4d\u4fe1\u606f\u6765\u6e90", "\u9009\u8bfe/\u5956\u52a9/\u5bbf\u820d/\u5c31\u4e1a \u5404\u81ea\u4e3a\u653f"],
  ["\u4f4e\u6548", "\u4eba\u5de5\u54a8\u8be2\u53d7\u5de5\u4f5c\u65f6\u95f4\u9650\u5236\uff0c\u665a\u95f4\u4e0e\u5047\u671f\u65e0\u6cd5\u54cd\u5e94", "\u8f85\u5bfc\u5458\u4e0b\u73ed\u540e\u65e0\u4eba\u56de\u5e94"],
  ["\u65e0\u6eaf\u6e90", "\u540c\u4e00\u95ee\u9898\u4e0d\u540c\u6e20\u9053\u7b54\u6848\u4e0d\u4e00\uff0c\u7f3a\u4e4f\u6743\u5a01\u53e3\u5f84", "\u7f51\u7edc\u56de\u7b54\u65e0\u6765\u6e90\u6807\u6ce8"],
];
pains.forEach(([t, d, tag], i) => {
  const x = M + i * 4.18;
  card(s, x, 1.55, 3.9, 2.5);
  s.addText(t, { x: x + 0.3, y: 1.8, w: 3.3, h: 0.55, fontSize: 24, bold: true, color: i === 1 ? ACCENT : PRIMARY, fontFace: FONT, margin: 0 });
  s.addText(d, { x: x + 0.3, y: 2.42, w: 3.3, h: 0.95, fontSize: 12.5, color: TEXT, fontFace: FONT, margin: 0, lineSpacingMultiple: 1.25 });
  chip(s, x + 0.3, 3.48, 3.0, tag, "F1F3FA", MUTED);
});
card(s, M, 4.45, W - 2 * M, 2.35, DEEP);
s.addText("\u9009\u9898\u601d\u8def", { x: M + 0.4, y: 4.72, w: 2.2, h: 0.4, fontSize: 14, bold: true, color: ACCENT, fontFace: FONT, margin: 0 });
s.addText([
  { text: "\u4e3a\u4ec0\u4e48\u662f AI + RAG\uff1f", options: { bold: true, color: "FFFFFF", fontSize: 15 } },
  { text: "\u2014\u2014 \u5927\u6a21\u578b\u76f4\u63a5\u56de\u7b54\u4f1a\u5e7b\u89c9\uff0c\u800c\u6821\u56ed\u4fe1\u606f\u8981\u6c42\u51c6\u786e\u53ef\u6eaf\u6e90\u3002RAG \u5148\u68c0\u7d22\u518d\u751f\u6210\uff0c\u628a\u77e5\u8bc6\u5e93\u4f5c\u4e3a\u56de\u7b54\u7684\u552f\u4e00\u4e8b\u5b9e\u6765\u6e90\u3002", options: { color: "C9D2F5", fontSize: 13.5 } },
], { x: M + 0.4, y: 5.15, w: 11.4, h: 1.45, fontFace: FONT, margin: 0, valign: "top", paraSpaceAfter: 6, lineSpacingMultiple: 1.3 });
s.addNotes("\u75db\u70b9:\u5206\u6563\u3001\u4f4e\u6548\u3001\u65e0\u6eaf\u6e90\u3002\u6821\u56ed\u4fe1\u606f\u5bf9\u51c6\u786e\u6027\u8981\u6c42\u9ad8,\u7eaf\u5927\u6a21\u578b\u4f1a\u5e7b\u89c9,\u6240\u4ee5\u9009RAG\u3002");

/* ============ 4 需求:质量属性场景 ============ */
s = p.addSlide();
page(s, 4, 16, "\u9700\u6c42\u5206\u6790\uff1a\u516d\u5143\u7ec4\u8d28\u91cf\u5c5e\u6027\u573a\u666f", "\u6bcf\u4e2a\u8d28\u91cf\u5c5e\u6027\u90fd\u6709\u53ef\u9a8c\u8bc1\u7684\u91cf\u5316\u76ee\u6807\uff0c\u5e76\u6620\u5c04\u5230\u67b6\u6784\u5c42\u6b21");
const rows = [
  ["\u5c5e\u6027", "\u5173\u952e\u573a\u666f\uff08\u523a\u6fc0\u6e90 \u2192 \u54cd\u5e94\uff09", "\u91cf\u5316\u76ee\u6807", "\u843d\u70b9\u5c42\u6b21"],
  ["\u6027\u80fd", "\u5956\u52a9\u7533\u62a5\u5b63\u5e76\u53d1 5 \u500d\u5cf0\u503c\uff0c\u54cd\u5e94\u4e0d\u962a\u5854", "\u9996\u5b57 < 1s \u00b7 \u68c0\u7d22 P95 < 50ms", "RAG \u5f15\u64ce\u5c42"],
  ["\u53ef\u7528\u6027", "\u4e91\u7aef LLM \u8d85\u65f6/\u6545\u969c\u65f6\u81ea\u52a8\u964d\u7ea7\u7ee7\u7eed\u670d\u52a1", "\u964d\u7ea7\u96f6\u4eba\u5de5 \u00b7 \u53ef\u7528\u6027 \u2265 99.5%", "\u751f\u6210 Provider"],
  ["\u53ef\u4fee\u6539\u6027", "\u77e5\u8bc6\u65b0\u589e/\u4fee\u6b63\u540e\u65b0\u77e5\u8bc6\u7acb\u5373\u751f\u6548", "\u7d22\u5f15\u70ed\u66f4\u65b0 < 5s \u65e0\u9700\u91cd\u542f", "\u6444\u53d6+\u7d22\u5f15"],
  ["\u53ef\u6269\u5c55\u6027", "\u7528\u6237\u589e\u957f\u9760\u52a0\u526f\u672c\u800c\u975e\u91cd\u6784", "\u5e94\u7528\u65e0\u72b6\u6001 \u00b7 N \u526f\u672c\u8d1f\u8f7d\u5747\u8861", "\u5e94\u7528\u670d\u52a1\u5c42"],
  ["\u5b89\u5168\u6027", "\u5355\u7528\u6237\u9ad8\u9891\u8bf7\u6c42\u4e0d\u62d6\u57ae\u670d\u52a1", "\u4ee4\u724c\u6876 5 QPS/\u7528\u6237 \u00b7 \u8d85\u9650 429", "\u7f51\u5173\u8fb9\u754c\u5c42"],
];
s.addTable(rows.map((r, i) => r.map((c, j) => ({
  text: c,
  options: i === 0
    ? { bold: true, color: "FFFFFF", fill: { color: PRIMARY }, fontSize: 12.5, align: j === 1 ? "left" : "left", valign: "middle" }
    : { color: j === 0 ? PRIMARY : TEXT, bold: j === 0, fill: { color: i % 2 ? "F2F4FB" : "FFFFFF" }, fontSize: 11.5, valign: "middle" },
}))), {
  x: M, y: 1.62, w: W - 2 * M, colW: [1.55, 5.4, 3.6, 1.65],
  border: { pt: 0.5, color: LINE }, fontFace: FONT, rowH: 0.62, margin: 0.09,
});
s.addText("\u7ea6\u675f\u6761\u4ef6\uff1a8 \u5468\u5de5\u671f \u00b7 3\u20135 \u4eba\u56e2\u961f \u00b7 \u96f6\u9884\u7b97\u6f14\u793a \u00b7 \u56de\u7b54\u5fc5\u987b\u53ef\u6eaf\u6e90\u4e0d\u7f16\u9020", { x: M, y: 6.0, w: W - 2 * M, h: 0.35, fontSize: 12, color: MUTED, fontFace: FONT, margin: 0 });
s.addNotes("\u8d28\u91cf\u5c5e\u6027\u573a\u666f\u516d\u5143\u7ec4:\u6bcf\u4e2a\u5c5e\u6027\u6709\u573a\u666f\u3001\u76ee\u6807\u3001\u843d\u70b9\u3002\u7ea6\u675f:\u77ed\u5de5\u671f\u3001\u96f6\u9884\u7b97\u3001\u53ef\u6eaf\u6e90\u3002");

/* ============ 5 总体架构 ============ */
s = p.addSlide();
page(s, 5, 16, "\u603b\u4f53\u67b6\u6784\uff1a\u4e94\u5c42\u5206\u5c42 + \u6a21\u5757\u5316\u5355\u4f53", "\u63a5\u5165 \u2192 \u7f51\u5173\u8fb9\u754c \u2192 \u5e94\u7528\u670d\u52a1 \u2192 RAG \u5f15\u64ce \u2192 \u6570\u636e\uff1b\u6a21\u5757\u95f4\u4ec5\u63a5\u53e3\u4f9d\u8d56\uff0c\u9884\u7559\u670d\u52a1\u5316\u8fb9\u754c");
s.addImage({ path: `${ASSETS}/arch_layers.png`, x: 1.7, y: 1.42, w: 9.9, h: 5.45 });
s.addNotes("\u4e94\u5c42\u67b6\u6784:\u6bcf\u5c42\u804c\u8d23\u6e05\u6670;\u8d28\u91cf\u5c5e\u6027\u53ef\u5b9a\u4f4d\u5230\u5c42:\u6027\u80fd\u2192\u5f15\u64ce\u5c42,\u53ef\u4fee\u6539\u6027\u2192\u6570\u636e\u5c42,\u6269\u5c55\u6027\u2192\u65e0\u72b6\u6001\u5e94\u7528\u5c42\u3002");

/* ============ 6 RAG 核心链路 ============ */
s = p.addSlide();
page(s, 6, 16, "RAG \u6838\u5fc3\u94fe\u8def\uff1a\u68c0\u7d22 \u2192 \u878d\u5408 \u2192 \u91cd\u6392 \u2192 \u6d41\u5f0f\u751f\u6210", "SSE \u4e8b\u4ef6\u6d41\uff1ameta\uff08\u5148\u63a8\u5f15\u7528\u6765\u6e90\uff09\u2192 delta\uff08token \u6d41\uff09\u2192 done\uff08\u843d\u5e93\uff09");
s.addImage({ path: `${ASSETS}/arch_sequence.png`, x: 0.95, y: 1.5, w: 11.45, h: 5.35 });
s.addNotes("\u65f6\u5e8f\u7684\u4e24\u4e2a\u5173\u952e\u8bbe\u8ba1:\u2460\u68c0\u7d22\u5b8c\u6210\u5148\u63a8meta\u4e8b\u4ef6\u8ba9\u524d\u7aef\u5148\u770b\u5230\u6b63\u5728\u53c2\u8003\u54ea\u4e9b\u8d44\u6599;\u2461\u751f\u6210\u5b8c\u6210\u624d\u843d\u5e93\u3002");

/* ============ 7 混合检索设计(原生图示) ============ */
s = p.addSlide();
page(s, 7, 16, "\u6df7\u5408\u68c0\u7d22\uff1a\u4e3a\u4ec0\u4e48\u8981\u4e24\u6761\u901a\u9053", "\u5355 BM25 \u4e0d\u61c2\u540c\u4e49\u6539\u5199\uff0c\u5411\u91cf\u901a\u9053\u73b0\u4e3a TF-IDF \u8bcd\u888b\uff08\u79bb\u7ebf\u5982\u5b9e\u6807\u6ce8\uff09\uff0c\u4e91\u7aef\u8bed\u4e49\u5411\u91cf Provider \u5df2\u5b9e\u73b0\u5f85\u63a5\u5165");
const flow = [
  ["\u5b66\u751f\u63d0\u95ee", "\u300c\u996d\u5361\u627e\u4e0d\u5230\u4e86\u300d", DEEP, "FFFFFF"],
  ["BM25 \u7a00\u758f\u901a\u9053", "\u5173\u952e\u8bcd\u7cbe\u786e\u5339\u914d", PRIMARY, "FFFFFF"],
  ["TF-IDF \u5411\u91cf\u901a\u9053", "\u79bb\u7ebf\u8bcd\u888b \u00b7 \u53ef\u63d2\u62d4\u8bed\u4e49\u5411\u91cf", PURPLE, "FFFFFF"],
  ["RRF \u878d\u5408", "\u6309\u6392\u540d\u878d\u5408 k=60", DEEP2, "FFFFFF"],
  ["\u91cd\u6392\u5e8f(\u53ef\u9009\u5f00\u5173)", "\u9ed8\u8ba4\u5173\u95ed RERANK_ENABLED", ACCENT, "FFFFFF"],
];
const fx = [0.55, 2.75, 2.75, 5.45, 7.5], fy = [2.7, 1.66, 3.74, 2.7, 2.7], fw = 2.05, fh = 1.06;
s.addShape(p.shapes.ROUNDED_RECTANGLE, { x: fx[0], y: fy[0], w: fw, h: fh, fill: { color: flow[0][2] }, rectRadius: 0.09, line: { type: "none" }, shadow: sh() });
s.addText(flow[0][0], { x: fx[0], y: fy[0] + 0.12, w: fw, h: 0.4, fontSize: 14, bold: true, color: flow[0][3], fontFace: FONT, align: "center", margin: 0 });
s.addText(flow[0][1], { x: fx[0], y: fy[0] + 0.54, w: fw, h: 0.4, fontSize: 10, color: "C9D2F5", fontFace: FONT, align: "center", margin: 0 });
[[1], [2]].forEach(([i]) => {
  s.addShape(p.shapes.ROUNDED_RECTANGLE, { x: fx[i], y: fy[i], w: fw, h: fh, fill: { color: flow[i][2] }, rectRadius: 0.09, line: { type: "none" }, shadow: sh() });
  s.addText(flow[i][0], { x: fx[i], y: fy[i] + 0.12, w: fw, h: 0.4, fontSize: 13.5, bold: true, color: flow[i][3], fontFace: FONT, align: "center", margin: 0 });
  s.addText(flow[i][1], { x: fx[i], y: fy[i] + 0.54, w: fw, h: 0.42, fontSize: 10, color: "E7EBFF", fontFace: FONT, align: "center", margin: 0 });
});
[3, 4].forEach((i) => {
  s.addShape(p.shapes.ROUNDED_RECTANGLE, { x: fx[i], y: fy[i], w: fw, h: fh, fill: { color: flow[i][2] }, rectRadius: 0.09, line: { type: "none" }, shadow: sh() });
  s.addText(flow[i][0], { x: fx[i], y: fy[i] + 0.12, w: fw, h: 0.4, fontSize: 13.5, bold: true, color: flow[i][3], fontFace: FONT, align: "center", margin: 0 });
  s.addText(flow[i][1], { x: fx[i], y: fy[i] + 0.54, w: fw, h: 0.42, fontSize: 10, color: "FFF3E8", fontFace: FONT, align: "center", margin: 0 });
});
s.addShape(p.shapes.LINE, { x: fx[0] + fw, y: fy[0] + fh / 2, w: fx[1] - fx[0] - fw, h: fy[1] + fh / 2 - fy[0] - fh / 2, line: { color: MUTED, width: 2, endArrowType: "triangle" } });
s.addShape(p.shapes.LINE, { x: fx[0] + fw, y: fy[0] + fh / 2, w: fx[2] - fx[0] - fw, h: fy[2] + fh / 2 - fy[0] - fh / 2, line: { color: MUTED, width: 2, endArrowType: "triangle" } });
s.addShape(p.shapes.LINE, { x: fx[1] + fw, y: fy[1] + fh / 2, w: fx[3] - fx[1] - fw, h: fy[3] + fh / 2 - fy[1] - fh / 2, line: { color: MUTED, width: 2, endArrowType: "triangle" } });
s.addShape(p.shapes.LINE, { x: fx[2] + fw, y: fy[2] + fh / 2, w: fx[3] - fx[2] - fw, h: fy[3] - fy[2], line: { color: MUTED, width: 2, endArrowType: "triangle" } });
s.addShape(p.shapes.LINE, { x: fx[3] + fw, y: fy[3] + fh / 2, w: fx[4] - fx[3] - fw, h: 0, line: { color: MUTED, width: 2, endArrowType: "triangle" } });
s.addShape(p.shapes.ROUNDED_RECTANGLE, { x: 10.35, y: 2.42, w: 2.45, h: 1.6, fill: { color: PRIMARY_SOFT }, rectRadius: 0.1, line: { color: PRIMARY, width: 1 } });
s.addText("\u751f\u6210 Provider", { x: 10.35, y: 2.58, w: 2.45, h: 0.4, fontSize: 14, bold: true, color: PRIMARY, fontFace: FONT, align: "center", margin: 0 });
s.addText("\u672c\u5730\u62bd\u53d6\u5f0f \u2225 \u4e91\u7aef GLM\n\u63d2\u4ef6\u5316\u53cc\u6a21\n\u6545\u969c\u81ea\u52a8\u964d\u7ea7", { x: 10.35, y: 3.0, w: 2.45, h: 0.95, fontSize: 10.5, color: TEXT, fontFace: FONT, align: "center", margin: 0, lineSpacingMultiple: 1.2 });
s.addShape(p.shapes.LINE, { x: fx[4] + fw, y: fy[4] + fh / 2, w: 10.35 - fx[4] - fw, h: 0, line: { color: MUTED, width: 2, endArrowType: "triangle" } });
card(s, M, 5.35, W - 2 * M, 1.5, "FFFFFF");
s.addText([
  { text: "\u53ef\u89c2\u5bdf\u6027\u8bbe\u8ba1\uff1a", options: { bold: true, color: PRIMARY, fontSize: 13.5 } },
  { text: "\u8c03\u8bd5\u63a5\u53e3\u4e0e\u524d\u7aef\u5f15\u7528\u5361\u7247\u540c\u6b65\u66b4\u9732\u53cc\u901a\u9053\u6392\u540d\u4e0e\u878d\u5408\u5206\u6570 \u2014\u2014 \u68c0\u7d22\u8fc7\u7a0b\u53ef\u89e3\u91ca\u3001\u53ef\u8bfe\u4ef6\u5316\u3001\u53ef\u8c03\u53c2\uff08\u5982\u53f3\u56fe\uff1aBM25#1 \u00b7 VEC#1 \u00b7 85%\uff09", options: { color: TEXT, fontSize: 13 } },
], { x: M + 0.35, y: 5.55, w: W - 2 * M - 0.7, h: 1.1, fontFace: FONT, margin: 0, valign: "middle", lineSpacingMultiple: 1.35 });
s.addNotes("\u6df7\u5408\u68c0\u7d22\u4e09\u6bb5\u5f0f:\u4e24\u8def\u5e76\u884c\u53ec\u56de\u2192RRF\u878d\u5408\u2192\u91cd\u6392\u7cbe\u9009\u3002\u53cc\u6a21\u751f\u6210:\u672c\u5730\u62bd\u53d6\u5f0f\u4fdd\u964d\u7ea7,\u4e91\u7aefGLM\u4fdd\u6548\u679c\u3002");

/* ============ 8 架构决策 ADR ============ */
s = p.addSlide();
page(s, 8, 16, "\u5173\u952e\u67b6\u6784\u51b3\u7b56\uff08ADR \u6458\u8981\uff09", "\u6bcf\u4e2a\u51b3\u7b56\u90fd\u6709\u88ab\u5426\u51b3\u7684\u5907\u9009\u65b9\u6848\u4e0e\u7406\u7531");
const adr = [
  ["ADR-1 \u6a21\u5757\u5316\u5355\u4f53\u8d77\u6b65", "\u5426\u51b3\u5fae\u670d\u52a1\u5168\u5bb6\u6876\uff088 \u5468\u5de5\u671f\u4e0d\u5bb9\u8bb8\uff09\u4e0e\u7eaf\u5206\u5c42\uff08\u62c6\u5206\u4ee3\u4ef7\u9ad8\uff09\uff0c\u4fdd\u7559\u670d\u52a1\u5316\u8fb9\u754c"],
  ["ADR-2 \u6df7\u5408\u68c0\u7d22\u9ed8\u8ba4 RRF", "\u5426\u51b3\u5355\u4e00\u901a\u9053\uff1b\u91cd\u6392\u5b9e\u6d4b\u65e0\u6536\u76ca\u964d\u4e3a\u5f00\u5173\uff1b\u5411\u91cf\u73b0\u6001 TF-IDF\uff08ADR-7\uff09"],
  ["ADR-3 SSE \u627f\u8f7d\u6d41\u5f0f\u56de\u7b54", "\u5426\u51b3 WebSocket\uff1a\u5355\u5411\u63a8\u9001\u573a\u666f\u66f4\u8f7b\u91cf\u3001\u5bf9\u7f51\u5173\u53cb\u597d\uff1bWS \u7559\u5f85\u540e\u7eed\u53cc\u5411\u573a\u666f"],
  ["ADR-4 \u751f\u6210 Provider \u63d2\u4ef6\u5316", "\u5426\u51b3\u5f3a\u4f9d\u8d56\u4e91\u7aef LLM\uff1a\u6f14\u793a\u53ef\u79bb\u7ebf\u8dd1\uff0c\u4e91\u7aef\u6545\u969c\u81ea\u52a8\u964d\u7ea7\u4e0d\u4e2d\u65ad"],
  ["ADR-5 \u5185\u5b58\u7d22\u5f15+\u70ed\u91cd\u5efa", "\u5426\u51b3\u6bcf\u8bf7\u6c42\u91cd\u5efa\u7d22\u5f15\uff1b\u4e07\u7ea7 chunk \u5185\u5b58\u8db3\u591f\uff0c\u8d85\u51fa\u518d\u8fc1\u5411\u91cf\u5e93"],
  ["ADR-6 \u4ee4\u724c\u6876\u5165\u53e3\u9650\u6d41", "\u6f14\u793a\u4ee3\u7806\u65e0\u7edf\u4e00\u8eab\u4efd\uff1b\u534f\u8bae\u517c\u5bb9\uff0c\u751f\u4ea7\u6362 Redis \u6ed1\u52a8\u7a97\u53e3"],
];
adr.forEach(([t, d], i) => {
  const x = M + (i % 3) * 4.18, y = 1.6 + Math.floor(i / 3) * 2.55;
  card(s, x, y, 3.9, 2.3);
  s.addText(t, { x: x + 0.28, y: y + 0.22, w: 3.35, h: 0.75, fontSize: 14.5, bold: true, color: PRIMARY, fontFace: FONT, margin: 0, lineSpacingMultiple: 1.1 });
  s.addText(d, { x: x + 0.28, y: y + 1.0, w: 3.35, h: 1.15, fontSize: 11.5, color: TEXT, fontFace: FONT, margin: 0, lineSpacingMultiple: 1.28 });
});
s.addNotes("\u516d\u9879ADR\u90fd\u6709\u5907\u9009\u65b9\u6848\u548c\u5426\u51b3\u7406\u7531,\u4f53\u73b0\u67b6\u6784\u5408\u7406\u6027\u4e0e\u6743\u8861\u3002");

/* ============ 9 技术选型对比 ============ */
s = p.addSlide();
page(s, 9, 16, "\u6280\u672f\u9009\u578b\uff1a\u5173\u952e\u7ef4\u5ea6\u5bf9\u6bd4", "\u9009\u578b\u4f9d\u636e\uff1a\u5de5\u671f\u7ea6\u675f \u00b7 \u79bb\u7ebf\u53ef\u8dd1 \u00b7 \u63a5\u53e3\u4e0d\u53d8\u7684\u6f14\u8fdb\u80fd\u529b");
const cmp = [
  ["\u7ef4\u5ea6", "\u9009\u578b", "\u5907\u9009\u65b9\u6848", "\u51b3\u5b9a\u6027\u7406\u7531"],
  ["Web \u6846\u67b6", "FastAPI + \u539f\u751f JS SPA", "Django / Spring Cloud", "SSE/async \u539f\u751f\u652f\u6301\uff0c\u96f6\u6784\u5efa\u524d\u7aef"],
  ["\u68c0\u7d22\u67b6\u6784", "\u81ea\u5b9e\u73b0 BM25+TF-IDF \u5411\u91cf", "Elasticsearch / Milvus", "\u96f6\u4f9d\u8d56\u6f14\u793a\uff1b\u63a5\u53e3\u5df2\u9884\u7559\u5347\u7ea7\u4f4d"],
  ["LLM \u63a5\u5165", "\u667a\u8c31 GLM(openai \u517c\u5bb9)", "\u81ea\u90e8\u5f00\u6e90\u6a21\u578b", "\u6807\u51c6\u534f\u8bae\u53ef\u5e73\u6ed1\u66ff\u6362\u4f9b\u5e94\u5546"],
  ["\u4e1a\u52a1\u5b58\u50a8", "SQLite(WAL)", "PostgreSQL / MySQL", "\u5355\u6587\u4ef6\u5907\u4efd\uff1b\u4ed3\u50a8\u5c42\u63a5\u53e3\u4e0d\u53d8\u76f4\u63a5\u5e73\u79fb"],
  ["\u6d41\u5f0f\u534f\u8bae", "SSE", "WebSocket / \u8f6e\u8be2", "\u5355\u5411\u63a8\u9001\u8db3\u591f\uff0c\u7f51\u5173\u53cb\u597d\u4e14\u5b9e\u73b0\u7b80\u5355"],
  ["Embedding", "TF-IDF \u79bb\u7ebf + \u4e91\u7aef Provider \u5df2\u5b9e\u73b0", "\u672c\u5730\u6df1\u5ea6\u6a21\u578b", "\u65e0 Key \u5982\u5b9e\u56de\u9000 TF-IDF\uff1b\u914d Key \u5373\u5207\u8bed\u4e49\u5411\u91cf\uff0c\u63a5\u53e3\u4e0d\u53d8"],
];
s.addTable(cmp.map((r, i) => r.map((c, j) => ({
  text: c,
  options: i === 0
    ? { bold: true, color: "FFFFFF", fill: { color: DEEP2 }, fontSize: 12.5, valign: "middle" }
    : { color: j === 1 ? PRIMARY : (j === 0 ? TEXT : MUTED), bold: j <= 1, fill: { color: i % 2 ? "F2F4FB" : "FFFFFF" }, fontSize: 12, valign: "middle" },
}))), {
  x: M, y: 1.62, w: W - 2 * M, colW: [1.9, 3.7, 3.1, 4.0],
  border: { pt: 0.5, color: LINE }, fontFace: FONT, rowH: 0.66, margin: 0.09,
});
s.addNotes("\u9009\u578b\u539f\u5219:\u6f14\u793a\u96f6\u4f9d\u8d56\u53ef\u79bb\u7ebf\u8dd1,\u4f46\u6bcf\u4e2a\u9009\u62e9\u90fd\u9884\u7559\u4e86\u63a5\u53e3\u4e0d\u53d8\u7684\u5347\u7ea7\u8def\u5f84\u3002");

/* ============ 10 系统演示 ============ */
s = p.addSlide();
page(s, 10, 16, "\u7cfb\u7edf\u6f14\u793a\uff1a\u6d41\u5f0f\u56de\u7b54\u4e0e\u8fd0\u884c\u770b\u677f", "\u5b9e\u673a\u622a\u56fe \u2014\u2014 \u5b8c\u6574\u6f14\u793a\u89c1 60 \u79d2\u5f55\u5c4f video/demo_frontend_v2.webm");
card(s, M, 1.55, 7.35, 4.0, "FFFFFF");
s.addImage({ path: `${SHOTS}/f8.png`, x: M + 0.12, y: 1.67, w: 7.11, h: 3.76 });
chip(s, M + 0.25, 5.05, 3.2, "\u6d41\u5f0f\u56de\u7b54 + \u5f15\u7528\u6eaf\u6e90\u5361\u7247");
card(s, 8.25, 1.55, 4.5, 4.0, "FFFFFF");
s.addImage({ path: `${SHOTS}/f38.png`, x: 8.37, y: 1.67, w: 4.26, h: 3.76 });
chip(s, 8.5, 5.05, 3.2, "\u8fd0\u884c\u770b\u677f\uff1a\u547d\u4e2d\u7387/\u65f6\u5ef6/\u70ed\u70b9");
stat(s, M + 0.3, 5.75, 3.4, "100%", "\u77e5\u8bc6\u547d\u4e2d\u7387\uff08\u6f14\u793a\u4f1a\u8bdd\uff09", PRIMARY);
stat(s, M + 4.0, 5.75, 3.4, "4.5ms", "\u65b0\u77e5\u8bc6\u5373\u65f6\u68c0\u7d22\u547d\u4e2d", ACCENT);
stat(s, M + 7.7, 5.75, 3.4, "v6", "\u7d22\u5f15\u7248\u672c(\u9876\u680f\u53ef\u89c1)", PURPLE);
s.addNotes("\u6f14\u793a\u4e24\u4e2a\u753b\u9762:\u804a\u5929\u6d41\u5f0f\u56de\u7b54+\u5f15\u7528\u5361\u7247;\u8fd0\u884c\u770b\u677f\u3002\u5f55\u5c4f\u91cc\u8fd8\u6709\u77e5\u8bc6\u5e93\u7ba1\u7406\u548c\u70ed\u66f4\u65b0\u73af\u8282\u3002");

/* ============ 11 知识热更新闭环 ============ */
s = p.addSlide();
page(s, 11, 16, "\u77e5\u8bc6\u70ed\u66f4\u65b0\u95ed\u73af\uff1a\u5f55\u5165\u5373\u53ef\u7b54", "\u5f55\u5c4f\u5b9e\u51b5\uff1a\u65b0\u589e\u300c\u5feb\u9012\u9a7f\u7ad9\u53d6\u4ef6\u300d\u6761\u76ee \u2192 \u7d22\u5f15\u70ed\u91cd\u5efa \u2192 \u7acb\u5373\u547d\u4e2d\u56de\u7b54");
const steps = [
  ["1", "\u5f55\u5165\u65b0\u77e5\u8bc6", "\u7ba1\u7406\u7aef\u586b\u5199\u95ee\u6cd5/\u7b54\u6848/\u6765\u6e90"],
  ["2", "\u7d22\u5f15\u70ed\u91cd\u5efa", "136 chunks \u00b7 \u7248\u672c\u9012\u589e \u00b7 \u65e0\u9700\u91cd\u542f"],
  ["3", "\u63d0\u95ee\u9a8c\u8bc1", "\u300c\u5feb\u9012\u9a7f\u7ad9\u600e\u4e48\u53d6\u4ef6\u300d"],
  ["4", "\u547d\u4e2d\u56de\u7b54", "BM25#1 \u00b7 VEC#1 \u00b7 \u7f6e\u4fe1 100%"],
];
steps.forEach(([n, t, d], i) => {
  const x = M + i * 3.22;
  s.addShape(p.shapes.OVAL, { x, y: 1.75, w: 0.62, h: 0.62, fill: { color: i === 3 ? ACCENT : PRIMARY }, line: { type: "none" }, shadow: sh() });
  s.addText(n, { x, y: 1.75, w: 0.62, h: 0.62, fontSize: 20, bold: true, color: "FFFFFF", fontFace: FONT, align: "center", valign: "middle", margin: 0 });
  if (i < 3) s.addShape(p.shapes.LINE, { x: x + 0.72, y: 2.06, w: 2.42, h: 0, line: { color: LINE, width: 2, endArrowType: "triangle" } });
  s.addText(t, { x: x - 0.55, y: 2.55, w: 1.75, h: 0.4, fontSize: 14, bold: true, color: TEXT, fontFace: FONT, align: "center", margin: 0 });
  s.addText(d, { x: x - 0.75, y: 2.95, w: 2.15, h: 0.62, fontSize: 10.5, color: MUTED, fontFace: FONT, align: "center", margin: 0, lineSpacingMultiple: 1.2 });
});
card(s, M, 3.9, 6.1, 2.9, "FFFFFF");
s.addImage({ path: `${SHOTS}/f27.png`, x: M + 0.1, y: 4.0, w: 5.9, h: 2.7 });
chip(s, M + 0.25, 6.35, 4.2, "\u5f55\u5c4f\uff1a\u7ba1\u7406\u7aef\u5f55\u5165\u4e0e\u63d0\u4ea4");
card(s, 7.0, 3.9, 5.75, 2.9, "FFFFFF");
s.addImage({ path: `${SHOTS}/f55.png`, x: 7.1, y: 4.0, w: 5.55, h: 2.7 });
chip(s, 7.25, 6.35, 4.6, "\u5f55\u5c4f\uff1a\u65b0\u77e5\u8bc6\u88ab\u7acb\u5373\u68c0\u7d22\u56de\u7b54");
s.addNotes("\u70ed\u66f4\u65b0\u95ed\u73af:\u5f55\u5165\u5230\u53ef\u88ab\u68c0\u7d22\u4e0d\u9700\u8981\u91cd\u542f\u670d\u52a1,\u8fd9\u662f\u53ef\u4fee\u6539\u6027\u573a\u666f\u7684\u76f4\u63a5\u9a8c\u8bc1\u3002");

/* ============ 12 评测矩阵:四条链路对比(原生图表) ============ */
s = p.addSlide();
page(s, 12, 18, "\u8bc4\u6d4b\u77e9\u9635\uff1a62 \u6761\u53e3\u8bed\u5316\u6539\u5199 \u00d7 \u56db\u6761\u94fe\u8def", "\u8bc4\u4f30\u5355\u4f4d\u4e3a\u6587\u6863\u7ea7\uff1b\u5411\u91cf\u901a\u9053\u4e3a TF-IDF \u8bcd\u888b\uff08\u975e\u8bed\u4e49\u5d4c\u5165\uff0c\u5982\u5b9e\u6807\u6ce8\uff09");
const evLabels = ["BM25-only", "Vector(TF-IDF)", "Hybrid+RRF(\u9ed8\u8ba4)", "Hybrid+Rerank(\u5f00\u5173)"];
s.addChart(p.charts.BAR, [
  { name: "Hit@1", labels: evLabels, values: [80.6, 75.8, 80.6, 74.2] },
  { name: "Hit@3", labels: evLabels, values: [98.4, 93.5, 98.4, 90.3] },
], {
  x: M, y: 1.7, w: 7.1, h: 4.35, barDir: "col", barGapWidthPct: 55,
  chartColors: ["A8B5E8", PRIMARY],
  chartArea: { fill: { color: "FFFFFF" }, roundedCorners: true },
  catAxisLabelColor: MUTED, valAxisLabelColor: MUTED, catAxisLabelFontSize: 9.5, valAxisLabelFontSize: 10,
  valAxisMaxVal: 100, valGridLine: { color: LINE, size: 0.5 }, catGridLine: { style: "none" },
  showValue: true, dataLabelPosition: "outEnd", dataLabelColor: TEXT, dataLabelFontSize: 9.5,
  showLegend: true, legendPos: "b", legendColor: MUTED, legendFontSize: 11,
  valAxisTitle: "\u547d\u4e2d\u7387 %", showValAxisTitle: true, valAxisTitleColor: MUTED, valAxisTitleFontSize: 10,
});
s.addText("\u6570\u636e\u6e90\uff1ascripts/eval_matrix.py\uff0cn=62\uff0c\u7edf\u4e00\u6587\u6863\u7ea7\u53bb\u91cd\u53e3\u5f84\uff0cMRR\uff1a0.884 / 0.844 / 0.884 / 0.815", { x: M, y: 6.12, w: 7.1, h: 0.3, fontSize: 10, color: MUTED, fontFace: FONT, margin: 0 });
card(s, 7.95, 1.7, 4.8, 2.15, "FFFFFF");
s.addText([
  { text: "\u8c03\u4f18\u8fc7\u7a0b\u4fee\u590d\u4e09\u4e2a\u771f\u5b9e\u7f3a\u9677\uff1a", options: { bold: true, color: ACCENT, fontSize: 12.5, breakLine: true } },
  { text: "\u2460 \u505c\u7528\u8bcd\u8868\u6784\u9020 bug\uff08\u6574\u4e32\u672a split\uff09\u2461 RRF \u5019\u9009\u6c60\u622a\u65ad\u538b\u7f29\u6587\u6863\u591a\u6837\u6027 \u2462 \u7f3a\u6587\u6863\u7ea7\u53bb\u91cd\uff08\u5f15\u7528\u5361\u7247\u91cd\u590d\u6839\u56e0\uff09\uff0c\u7edf\u4e00\u53e3\u5f84\u540e RRF \u5b9e\u6d4b 98.4%\uff08\u65e7\u53e3\u5f84 95.2% \u5b58\u5728\u91cd\u590d\u5360\u4f4d\u5931\u771f\uff09", options: { color: TEXT, fontSize: 11.5 } },
], { x: 8.2, y: 1.92, w: 4.3, h: 1.8, fontFace: FONT, margin: 0, valign: "top", paraSpaceAfter: 5, lineSpacingMultiple: 1.25 });
card(s, 7.95, 4.0, 4.8, 2.0, DEEP);
s.addText([
  { text: "\u5b9e\u8bc1\u7ed3\u8bba\uff1a", options: { bold: true, color: ACCENT, fontSize: 12.5 } },
  { text: "BM25 \u5bf9\u5173\u952e\u8bcd\u5bc6\u96c6\u578b\u89c4\u7ae0\u95ee\u9898\u6700\u597d\uff1bTF-IDF \u5411\u91cf\u8865\u5145\u53e6\u4e00\u89c6\u89d2\u4f46\u672a\u7a33\u5b9a\u8d85\u8fc7 BM25\uff1b\u8f7b\u91cf Reranker \u5b9e\u6d4b\u65e0\u6536\u76ca\uff0c\u9ed8\u8ba4\u5173\u95ed\u4fdd\u6301 Provider \u5316\uff0c\u5f85\u66ff\u6362 Cross-Encoder \u540e\u518d\u8bc4\u4f30", options: { color: "C9D2F5", fontSize: 11.5 } },
], { x: 8.2, y: 4.22, w: 4.3, h: 1.65, fontFace: FONT, margin: 0, valign: "top", paraSpaceAfter: 5, lineSpacingMultiple: 1.3 });
s.addNotes("\u56db\u8def\u8bc4\u6d4b:BM25\u6700\u5f3a\u3002\u8c03\u4f18\u4fee\u590d\u4e09\u7f3a\u9677\u540e\u751f\u4ea7\u94fe\u8def\u63d0\u5347\u523087%\u4ee5\u4e0a0\u8fd1\u6c34\u5e73\u3002\u5b9e\u8bc1\u7ed3\u8bba\u8bda\u5b9e\u5448\u73b0\u3002");

/* ============ 13 性能基准:retrieval-only 与 E2E 拆分 ============ */
s = p.addSlide();
page(s, 13, 18, "\u6027\u80fd\u57fa\u51c6\uff1a\u68c0\u7d22\u4e0e\u5168\u94fe\u8def\u62c6\u5206\u5b9e\u6d4b", "retrieval-only \u8fdb\u7a0b\u5185\u76f4\u8c03\uff1blocal-extractive E2E \u542b\u68c0\u7d22+\u6d41\u5f0f\u751f\u6210+\u843d\u5e93\uff08HTTP\uff0c\u5e76\u53d1 20\uff09");
const perfRows = [
  ["\u57fa\u51c6", "\u6837\u672c", "QPS", "p50", "p95", "p99", "\u5931\u8d25"],
  ["retrieval-only", "300", "251.4", "3.4ms", "7.0ms", "7.2ms", "0"],
  ["local-extractive E2E", "200", "44.1", "415.7ms", "601.0ms", "611.1ms", "0"],
];
s.addTable(perfRows.map((r, i) => r.map((c) => ({
  text: c,
  options: i === 0
    ? { bold: true, color: "FFFFFF", fill: { color: DEEP2 }, fontSize: 12, valign: "middle", align: "center" }
    : { color: i === 1 ? PRIMARY : TEXT, bold: i > 0, fill: { color: i % 2 ? "F2F4FB" : "FFFFFF" }, fontSize: 12.5, valign: "middle", align: "center" },
}))), {
  x: M, y: 1.75, w: W - 2 * M, colW: [3.3, 1.3, 1.5, 1.6, 1.6, 1.6, 1.28],
  border: { pt: 0.5, color: LINE }, fontFace: FONT, rowH: 0.58, margin: 0.06,
});
stat(s, M + 0.4, 4.15, 5.4, "251.4", "retrieval-only \u541e\u5410\uff08QPS\uff09", PRIMARY, "p95 7.0ms\uff0c\u8fdc\u4f18\u4e8e 50ms \u76ee\u6807");
stat(s, M + 6.6, 4.15, 5.4, "44.1", "E2E \u541e\u5410\uff08QPS\uff0c\u542b\u751f\u6210\uff09", PURPLE, "p99 611ms\uff0c200/200 \u6210\u529f");
card(s, M, 5.85, W - 2 * M, 0.95, "FFFFFF");
s.addText([
  { text: "\u5982\u5b9e\u8bf4\u660e\uff1a", options: { bold: true, color: ACCENT, fontSize: 12 } },
  { text: "\u5386\u53f2\u5bf9\u7167\uff1aRerank \u9ed8\u8ba4\u65f6\u671f 217.8 / 42.0 QPS\uff0c\u521d\u7248 67.8 QPS\uff1b\u9ed8\u8ba4\u5207\u6362\u81f3 RRF \u540e\u68c0\u7d22\u8ba1\u7b97\u91cf\u4e0b\u964d\uff0c\u541e\u5410\u56de\u5347\uff0c\u6570\u636e\u5982\u5b9e\u5448\u73b0\u3002", options: { color: TEXT, fontSize: 12 } },
], { x: M + 0.3, y: 6.02, w: W - 2 * M - 0.6, h: 0.62, fontFace: FONT, margin: 0, valign: "middle" });
s.addText("\u6570\u636e\u6e90\uff1ascripts/bench.py\uff08retrieval / e2e \u4e24\u6a21\u5f0f\uff09\uff0c2026-09-18 \u5b9e\u6d4b", { x: M, y: 6.95, w: W - 2 * M, h: 0.3, fontSize: 10, color: MUTED, fontFace: FONT, margin: 0 });
s.addNotes("\u6027\u80fd\u62c6\u5206:\u68c0\u7d22217QPS\u8fdc\u8d85\u76ee\u6807;E2E\u542b\u751f\u621042QPS\u3002\u541e\u5410\u4e0b\u964d\u7684\u539f\u56e0\u5982\u5b9e\u8bf4\u660e\u3002");

/* ============ 14 追踪矩阵与四项架构验收 ============ */
s = p.addSlide();
page(s, 14, 18, "\u8ffd\u8e2a\u77e9\u9635\u4e0e\u56db\u9879\u67b6\u6784\u9a8c\u6536", "\u9700\u6c42 \u2192 \u8d28\u91cf\u5c5e\u6027 \u2192 ADR \u2192 \u6a21\u5757 \u2192 \u6d4b\u8bd5 \u2192 \u8bc1\u636e\uff0c\u5168\u94fe\u6761\u53ef\u8ffd\u6eaf\uff08\u89c1 docs/traceability.md\uff09");
const acc = [
  ["A1 \u751f\u6210\u964d\u7ea7", "\u4e91\u7aef GLM \u65e0\u6548 Key \u2192 \u6d41\u5185\u56de\u9000\u672c\u5730\u62bd\u53d6\u5f0f", "PASS", "\u964d\u7ea7\u4ea7\u51fa 139 \u5b57\u6b63\u89e3\uff0c\u670d\u52a1\u4e0d\u4e2d\u65ad"],
  ["A2 \u5165\u53e3\u9650\u6d41", "\u5355\u7528\u6237\u5e76\u53d1\u7a81\u53d1 15\uff08\u6876\u5bb9\u91cf 10\uff09", "PASS", "200\u00d710 + 429\u00d75\uff0c\u8d85\u5bb9\u8bf7\u6c42\u88ab\u62d2"],
  ["A3 \u77e5\u8bc6\u70ed\u66f4\u65b0", "\u5f55\u5165\u5373\u68c0\u7d22\uff0c\u65e0\u9700\u91cd\u542f\uff0c\u9a8c\u540e\u6e05\u7406", "PASS", "\u7d22\u5f15\u7248\u672c 1\u21922\u21923 \u9012\u589e\uff0c\u5373\u65f6\u547d\u4e2d\u5e76\u6b63\u786e\u56de\u7b54"],
  ["A4 \u65e0\u77e5\u8bc6\u5151\u5e95", "\u65e0\u76f8\u5173\u77e5\u8bc6\u65f6\u4e0d\u7f16\u9020", "PASS", "sources=0\uff0c\u8fd4\u56de\u5f15\u5bfc\u6027\u56de\u9000\u8bdd\u672f"],
];
s.addTable(acc.map((r, i) => r.map((c, j) => ({
  text: c,
  options: i === 0
    ? { bold: true, color: "FFFFFF", fill: { color: PRIMARY }, fontSize: 12, valign: "middle" }
    : { color: j === 2 ? "12B76A" : (j === 0 ? PRIMARY : TEXT), bold: j <= 1, fill: { color: i % 2 ? "F2F4FB" : "FFFFFF" }, fontSize: 11.5, valign: "middle", align: j === 2 ? "center" : "left" },
}))), {
  x: M, y: 1.62, w: W - 2 * M, colW: [2.5, 4.3, 1.1, 4.53],
  border: { pt: 0.5, color: LINE }, fontFace: FONT, rowH: 0.56, margin: 0.07,
});
const chain = ["\u9700\u6c42 FR/NFR", "\u8d28\u91cf\u5c5e\u6027\u573a\u666f", "ADR \u00d77", "\u5b9e\u73b0\u6a21\u5757", "\u6d4b\u8bd5/\u9a8c\u6536\u811a\u672c", "\u5b9e\u6d4b\u8bc1\u636e"];
chain.forEach((t, i) => {
  const x = M + i * 2.12;
  s.addShape(p.shapes.CHEVRON, { x, y: 4.35, w: 2.0, h: 0.72, fill: { color: i === 5 ? ACCENT : (i % 2 ? PURPLE : PRIMARY) }, line: { type: "none" } });
  s.addText(t, { x: x + 0.12, y: 4.38, w: 1.82, h: 0.66, fontSize: 10.5, bold: true, color: "FFFFFF", fontFace: FONT, align: "center", valign: "middle", margin: 0 });
});
card(s, M, 5.4, W - 2 * M, 1.35, "FFFFFF");
s.addText([
  { text: "\u8bc1\u636e\u4f53\u7cfb\uff1a", options: { bold: true, color: PRIMARY, fontSize: 12.5 } },
  { text: "62 \u6761\u8bc4\u6d4b\u96c6\uff08\u56db\u8def\u5bf9\u6bd4\uff09\u3001300+200 \u6027\u80fd\u57fa\u51c6\uff08\u542b p50/p95/p99\uff09\u3001\u56db\u9879\u9a8c\u6536 4/4 PASS\u300160 \u79d2\u6f14\u793a\u5f55\u5c4f \u2014\u2014 \u5168\u90e8\u7531 scripts/ \u4e0b\u53ef\u590d\u73b0\u811a\u672c\u4ea7\u51fa\uff0c\u4efb\u4f55\u7ed3\u8bba\u53ef\u91cd\u8dd1\u9a8c\u8bc1", options: { color: TEXT, fontSize: 12.5 } },
], { x: M + 0.3, y: 5.6, w: W - 2 * M - 0.6, h: 0.95, fontFace: FONT, margin: 0, valign: "middle", lineSpacingMultiple: 1.3 });
s.addNotes("\u56db\u9879\u9a8c\u6536\u5168\u90e8PASS\u3002\u8ffd\u8e2a\u94fe\u4ece\u9700\u6c42\u5230\u8bc1\u636e\u5168\u94fe\u6761\u53ef\u8ffd\u6eaf\uff0c\u811a\u672c\u53ef\u590d\u73b0\u3002");

/* ============ 13 安全与稳定性 ============ */
s = p.addSlide();
page(s, 15, 18, "\u5b89\u5168\u4e0e\u7a33\u5b9a\u6027\uff1a\u4e09\u9053\u9632\u7ebf", "\u9650\u6d41\u62d7\u6d41\u91cf \u00b7 \u964d\u7ea7\u4fdd\u53ef\u7528 \u00b7 \u6eaf\u6e90\u62d7\u5e7b\u89c9");
const sec = [
  ["\u4ee4\u724c\u6876\u9650\u6d41", "5 QPS/\u7528\u6237 \u00b7 \u7a81\u53d1 10\uff0c\u8d85\u9650\u8fd4\u56de 429\uff1bPydantic \u5f3a\u6821\u9a8c\u8f93\u5165\u957f\u5ea6\u4e0e\u5185\u5bb9", "\u6f14\u793a\u4ee3\u7806 \u2192 \u751f\u4ea7 Redis \u6ed1\u52a8\u7a97\u53e3", PRIMARY],
  ["\u751f\u6210\u964d\u7ea7\u7194\u65ad", "\u4e91\u7aef GLM 30s \u8d85\u65f6\uff1b\u4efb\u4f55\u5f02\u5e38\u6d41\u5185\u56de\u9000\u672c\u5730\u62bd\u53d6\u5f0f\u751f\u6210\uff0c\u670d\u52a1\u4e0d\u4e2d\u65ad", "\u68c0\u7d22\u6c38\u8fdc\u53ef\u7528 \u00b7 \u751f\u6210\u53ef\u964d\u7ea7", ACCENT],
  ["\u5f15\u7528\u6eaf\u6e90\u62d7\u5e7b\u89c9", "\u56de\u7b54\u5f3a\u5236\u6807\u6ce8\u6765\u6e90\u4e0e\u5206\u7c7b\uff1b\u65e0\u547d\u4e2d\u4e0d\u7f16\u9020\uff0c\u56de\u9000\u8bdd\u672f\u5e76\u5f15\u5bfc\u6362\u95ee\u6cd5", "\u63d0\u793a\u300c\u4ee5\u5b98\u65b9\u901a\u77e5\u4e3a\u51c6\u300d", PURPLE],
];
sec.forEach(([t, d, tag, c], i) => {
  const y = 1.62 + i * 1.72;
  card(s, M, y, W - 2 * M, 1.5);
  s.addShape(p.shapes.OVAL, { x: M + 0.32, y: y + 0.42, w: 0.66, h: 0.66, fill: { color: c }, line: { type: "none" } });
  s.addText(["\u2460", "\u2461", "\u2462"][i], { x: M + 0.32, y: y + 0.42, w: 0.66, h: 0.66, fontSize: 18, bold: true, color: "FFFFFF", fontFace: FONT, align: "center", valign: "middle", margin: 0 });
  s.addText(t, { x: M + 1.3, y: y + 0.2, w: 4.4, h: 0.5, fontSize: 17, bold: true, color: TEXT, fontFace: FONT, margin: 0 });
  s.addText(d, { x: M + 1.3, y: y + 0.72, w: 8.6, h: 0.62, fontSize: 12, color: MUTED, fontFace: FONT, margin: 0, lineSpacingMultiple: 1.2 });
  chip(s, M + 10.2, y + 0.55, 2.35, tag.split(" ")[0], c === ACCENT ? ACCENT_SOFT : PRIMARY_SOFT, c);
});
s.addNotes("\u4e09\u9053\u9632\u7ebf:\u9650\u6d41\u9632\u6d41\u91cf,\u964d\u7ea7\u9632\u6545\u969c,\u6eaf\u6e90\u62d7\u5e7b\u89c9\u3002\u65e0Key\u73af\u5883\u4e0b\u7cfb\u7edf\u4ecd\u5b8c\u6574\u670d\u52a1\u5c31\u662f\u964d\u7ea7\u8def\u5f84\u7684\u6d3b\u8bc1\u660e\u3002");

/* ============ 14 部署演进 ============ */
s = p.addSlide();
page(s, 16, 18, "\u90e8\u7f72\u6f14\u8fdb\uff1a\u63a5\u53e3\u4e0d\u53d8\uff0c\u7ec4\u4ef6\u53ef\u66ff\u6362", "\u5355\u673a\u6f14\u793a \u2192 \u751f\u4ea7\u96c6\u7fa4\u7684\u5e73\u6ed1\u6f14\u8fdb\u8def\u5f84");
s.addImage({ path: `${ASSETS}/arch_deploy.png`, x: 0.85, y: 1.5, w: 11.6, h: 5.35 });
s.addNotes("\u6bcf\u4e00\u6b65\u66ff\u6362(SQLite\u2192PG\u3001\u5185\u5b58\u7d22\u5f15\u2192Milvus\u3001\u672c\u5730\u2192GLM\u3001\u4ee3\u7806\u2192Redis)\u90fd\u662f\u4e00\u4e2a\u53ef\u5355\u72ec\u8bc4\u5206\u7684\u67b6\u6784\u51b3\u7b56\u3002");

/* ============ 15 8 周计划 ============ */
s = p.addSlide();
page(s, 17, 18, "8 \u5468\u8fed\u4ee3\u8ba1\u5212\u4e0e\u56e2\u961f\u5206\u5de5", "\u67b6\u6784\u5e08\u7275\u5934 \u00b7 \u524d\u540e\u7aef\u4e0e\u6570\u636e\u8fd0\u8425\u5e76\u884c \u00b7 \u6d4b\u8bd5\u8d2f\u7a7f\u5168\u7a0b");
const plan = [
  ["W1\u2013W2", "\u8c03\u7814+\u9700\u6c42+\u67b6\u6784\u539f\u578b", "\u8d28\u91cf\u5c5e\u6027\u573a\u666f\u00b7\u5206\u5c42\u56fe"],
  ["W3\u2013W4", "\u77e5\u8bc6\u5e93+\u6df7\u5408\u68c0\u7d22\u843d\u5730", "\u53cc\u901a\u9053\u53ec\u56de\u00b7RRF"],
  ["W5\u2013W6", "\u524d\u7aef+\u751f\u6210\u63d2\u4ef6\u5316", "SSE \u6d41\u5f0f\u00b7\u770b\u677f"],
  ["W7", "\u538b\u6d4b\u8c03\u4f18+\u6587\u6863 PPT", "\u8bc4\u6d4b\u62a5\u544a\u00b7\u5f55\u5c4f"],
  ["W8", "\u7b54\u8fa9\u6f14\u7ec3\u4e0e\u4ea4\u4ed8", "\u5f55\u5c4f\u526a\u8f91\u00b7\u6f14\u793a"],
];
const py = 1.85, px0 = M + 0.2, step = 2.45;
s.addShape(p.shapes.LINE, { x: px0, y: py + 0.31, w: step * 4, h: 0, line: { color: LINE, width: 2.5 } });
plan.forEach(([w, t, d], i) => {
  const x = px0 + i * step;
  s.addShape(p.shapes.OVAL, { x: x - 0.31, y: py, w: 0.62, h: 0.62, fill: { color: i === 4 ? ACCENT : PRIMARY }, line: { color: "FFFFFF", width: 2 }, shadow: sh() });
  s.addText(w.replace("W", ""), { x: x - 0.31, y: py, w: 0.62, h: 0.62, fontSize: 13, bold: true, color: "FFFFFF", fontFace: FONT, align: "center", valign: "middle", margin: 0 });
  s.addText(w, { x: x - 0.9, y: py + 0.75, w: 1.8, h: 0.35, fontSize: 12, bold: true, color: i === 4 ? ACCENT : PRIMARY, fontFace: FONT, align: "center", margin: 0 });
  s.addText(t, { x: x - 1.13, y: py + 1.12, w: 2.26, h: 0.72, fontSize: 12.5, bold: true, color: TEXT, fontFace: FONT, align: "center", margin: 0, lineSpacingMultiple: 1.15 });
  s.addText(d, { x: x - 1.13, y: py + 1.88, w: 2.26, h: 0.6, fontSize: 10.5, color: MUTED, fontFace: FONT, align: "center", margin: 0, lineSpacingMultiple: 1.2 });
});
card(s, M, 5.35, W - 2 * M, 1.45, DEEP);
s.addText([
  { text: "\u89d2\u8272\u5206\u5de5\uff1a", options: { bold: true, color: ACCENT, fontSize: 13.5 } },
  { text: "\u67b6\u6784\u5e08\uff08\u603b\u63a7\u67b6\u6784\u4e0e ADR\uff09\u00b7 \u540e\u7aef\u5de5\u7a0b \u00d72\uff08\u68c0\u7d22\u5f15\u64ce\u4e0e API\uff09\u00b7 \u524d\u7aef\u5de5\u7a0b\uff08\u804a\u5929\u4e0e\u770b\u677f\uff09\u00b7 \u6570\u636e\u8fd0\u8425\uff08\u77e5\u8bc6\u5e93\u4e0e\u540c\u4e49\u8bcd\uff09\u00b7 \u6d4b\u8bd5\uff08\u8bc4\u6d4b\u4e0e\u538b\u6d4b\uff09", options: { color: "C9D2F5", fontSize: 13 } },
], { x: M + 0.4, y: 5.6, w: W - 2 * M - 0.8, h: 0.95, fontFace: FONT, margin: 0, valign: "middle", lineSpacingMultiple: 1.35 });
s.addNotes("8\u5468\u4e94\u9636\u6bb5:\u539f\u578b\u2192\u68c0\u7d22\u843d\u5730\u2192\u524d\u7aef+\u63d2\u4ef6\u5316\u2192\u8c03\u4f18\u6587\u6863\u2192\u7b54\u8fa9\u3002");

/* ============ 16 总结 ============ */
s = p.addSlide();
s.background = { color: DEEP };
s.addShape(p.shapes.RECTANGLE, { x: -2, y: -2.4, w: 9, h: 12, fill: { color: DEEP2, transparency: 55 }, rotate: 18, line: { type: "none" } });
s.addShape(p.shapes.RECTANGLE, { x: 7.6, y: -2.4, w: 9, h: 12, fill: { color: PRIMARY, transparency: 82 }, rotate: -14, line: { type: "none" } });
s.addText("\u603b\u7ed3\u4e0e\u5c55\u671b", { x: 1.2, y: 0.75, w: W - 2.4, h: 0.8, fontSize: 34, bold: true, color: "FFFFFF", fontFace: FONT, align: "center", margin: 0 });
const sum = [
  ["\u53cc\u6a21\u751f\u6210\u67b6\u6784", "\u672c\u5730\u62bd\u53d6\u5f0f\u4e0e\u4e91\u7aef GLM \u5171\u4eab\u540c\u4e00 RAG \u94fe\u8def\uff0c\u79bb\u7ebf\u53ef\u6f14\u793a\u3001\u6545\u969c\u81ea\u964d\u7ea7"],
  ["\u68c0\u7d22\u53ef\u89c2\u5bdf", "\u53cc\u901a\u9053\u6392\u540d\u4e0e\u91cd\u6392\u5206\u6570\u540c\u6b65\u66b4\u9732\u7ed9\u524d\u7aef\u4e0e\u8c03\u8bd5\u63a5\u53e3\uff0c\u8fc7\u7a0b\u53ef\u89e3\u91ca"],
  ["\u77e5\u8bc6\u70ed\u66f4\u65b0\u95ed\u73af", "\u5f55\u5165\u5373\u5efa\u7d22\u5f15\u65e0\u9700\u91cd\u542f\uff0c\u540c\u4e49\u8bcd\u8fd0\u8425\u4f7f Hit@3 +5pp"],
  ["\u6f14\u8fdb\u578b\u67b6\u6784", "\u5355\u673a\u6f14\u793a\u4e0e\u751f\u4ea7\u96c6\u7fa4\u5171\u4eab\u63a5\u53e3\uff0c\u6bcf\u6b65\u66ff\u6362\u90fd\u662f\u53ef\u8bc4\u5206\u7684\u51b3\u7b56"],
];
sum.forEach(([t, d], i) => {
  const x = 1.05 + (i % 2) * 5.75, y = 1.95 + Math.floor(i / 2) * 1.75;
  s.addShape(p.shapes.ROUNDED_RECTANGLE, { x, y, w: 5.5, h: 1.5, fill: { color: DEEP2, transparency: 20 }, rectRadius: 0.1, line: { color: "3D4A85", width: 0.75 } });
  s.addText(t, { x: x + 0.3, y: y + 0.18, w: 4.9, h: 0.42, fontSize: 16, bold: true, color: "AFBCF0", fontFace: FONT, margin: 0 });
  s.addText(d, { x: x + 0.3, y: y + 0.62, w: 4.9, h: 0.75, fontSize: 11.5, color: "C9D2F5", fontFace: FONT, margin: 0, lineSpacingMultiple: 1.25 });
});
s.addText("\u4e0b\u4e00\u6b65\uff1a\u8bed\u4e49\u5411\u91cf + Cross-Encoder \u91cd\u6392 \u00b7 \u7edf\u4e00\u8eab\u4efd\u8ba4\u8bc1 \u00b7 \u77e5\u8bc6\u6e90\u81ea\u52a8\u91c7\u96c6 \u00b7 \u6301\u7eed\u8bc4\u6d4b", { x: 1.2, y: 5.6, w: W - 2.4, h: 0.4, fontSize: 13.5, color: "8B97C9", fontFace: FONT, align: "center", margin: 0 });
s.addText("\u6b22\u8fce\u63d0\u95ee \u00b7 \u8c22\u8c22\uff01", { x: 1.2, y: 6.25, w: W - 2.4, h: 0.75, fontSize: 30, bold: true, color: "FFFFFF", fontFace: FONT, align: "center", margin: 0 });
s.addNotes("\u56db\u4e2a\u521b\u65b0\u70b9\u6536\u5c3e,\u9884\u7559\u63d0\u95ee\u65f6\u95f4\u3002");

p.writeFile({ fileName: `${ROOT}/ppt/\u667a\u95ee\u6821\u56edCampusMind\u7b54\u8fa9PPT.pptx` }).then(() => console.log("PPT DONE"));
