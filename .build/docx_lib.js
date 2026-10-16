// 共享 docx 构建库:品牌色板 + R2 封面配方(照抄 design-system.md,禁止自由发挥)+ 通用构件
const {
  Paragraph, TextRun, Table, TableRow, TableCell, WidthType, BorderStyle,
  ShadingType, AlignmentType, HeadingLevel, Header, Footer, PageNumber,
  TableLayoutType, VerticalAlign,
} = require("docx");

// ---- 色板:按 design-system「Custom Color Generation」规则从项目品牌色派生
const PALETTE = {
  primary: "1C2333", body: "243050", secondary: "5A6478",
  accent: "3B5BFD", surface: "EEF1FF",
  cover: {
    bg: "FEFEFE", titleColor: "1C2333", subtitleColor: "5A6478",
    metaColor: "707070", footerColor: "A0A0A0",
  },
  table: { headerBg: "3B5BFD", headerText: "FFFFFF", accentLine: "3B5BFD", innerLine: "D8DEF5", surface: "EEF1FF" },
};

const NB = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
const noBorders = { top: NB, bottom: NB, left: NB, right: NB };
const allNoBorders = { top: NB, bottom: NB, left: NB, right: NB, insideHorizontal: NB, insideVertical: NB };

// ---- 标题计算(design-system 原函数)
function splitTitleLines(title, charsPerLine) {
  if (title.length <= charsPerLine) return [title];
  const breakAfter = new Set([..."\uff0c\u3002\u3001\uff1b\uff1a\uff01\uff1f", ..."\u7684\u4e0e\u548c\u53ca\u4e4b\u5728\u4e8e\u4e3a", ..."-_\u2014\u2013\u00b7/", ..." \t"]);
  const lines = [];
  let remaining = title;
  while (remaining.length > charsPerLine) {
    let breakAt = -1;
    for (let i = charsPerLine; i >= Math.floor(charsPerLine * 0.6); i--) {
      if (i < remaining.length && breakAfter.has(remaining[i - 1])) { breakAt = i; break; }
    }
    if (breakAt === -1) {
      const limit = Math.min(remaining.length, Math.ceil(charsPerLine * 1.3));
      for (let i = charsPerLine + 1; i < limit; i++) {
        if (breakAfter.has(remaining[i - 1])) { breakAt = i; break; }
      }
    }
    if (breakAt === -1) {
      breakAt = charsPerLine;
      const prevChar = remaining[breakAt - 1], nextChar = remaining[breakAt];
      if (prevChar && nextChar && !breakAfter.has(prevChar) && !breakAfter.has(nextChar) &&
          /[\u4e00-\u9fff]/.test(prevChar) && /[\u4e00-\u9fff]/.test(nextChar)) breakAt = breakAt - 1;
    }
    lines.push(remaining.slice(0, breakAt).trim());
    remaining = remaining.slice(breakAt).trim();
  }
  if (remaining) lines.push(remaining);
  if (lines.length > 1 && lines[lines.length - 1].length <= 2) {
    const last = lines.pop();
    lines[lines.length - 1] += last;
  }
  return lines;
}

function calcTitleLayout(title, maxWidthTwips, preferredPt = 40, minPt = 24) {
  const charWidth = (pt) => pt * 20;
  const charsPerLine = (pt) => Math.floor(maxWidthTwips / charWidth(pt));
  let titlePt = preferredPt, lines;
  while (titlePt >= minPt) {
    const cpl = charsPerLine(titlePt);
    if (cpl < 2) { titlePt -= 2; continue; }
    lines = splitTitleLines(title, cpl);
    if (lines.length <= 3) break;
    titlePt -= 2;
  }
  if (!lines || lines.length > 3) {
    lines = splitTitleLines(title, charsPerLine(minPt));
    titlePt = minPt;
  }
  return { titlePt, titleLines: lines };
}

// ---- R2 双线框封面(design-system 原配方)
function buildCoverR2(config) {
  const P = config.palette;
  const padL = 1400, padR = 1400;
  const { titlePt, titleLines } = calcTitleLayout(config.title, 11906 - padL - padR, 40, 24);
  const titleSize = titlePt * 2;
  const thickBorder = { style: BorderStyle.SINGLE, size: 18, color: P.accent, space: 20 };
  const children = [];
  children.push(new Paragraph({
    indent: { left: padL - 400, right: padR - 400 }, spacing: { before: 1200, after: 200 },
    border: { top: thickBorder }, children: [],
  }));
  children.push(new Paragraph({ spacing: { before: 1800 } }));
  if (config.englishLabel) {
    children.push(new Paragraph({
      alignment: AlignmentType.CENTER, spacing: { after: 500 },
      children: [new TextRun({ text: config.englishLabel.split("").join("  "), size: 18, color: P.accent, font: { ascii: "Calibri" }, characterSpacing: 40 })],
    }));
  }
  for (let i = 0; i < titleLines.length; i++) {
    children.push(new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: i < titleLines.length - 1 ? 80 : 300, line: Math.ceil(titlePt * 23), lineRule: "atLeast" },
      children: [new TextRun({ text: titleLines[i], size: titleSize, bold: true, color: P.titleColor, font: { eastAsia: "SimHei", ascii: "Arial" } })],
    }));
  }
  if (config.subtitle) {
    children.push(new Paragraph({
      alignment: AlignmentType.CENTER, spacing: { after: 400 },
      children: [new TextRun({ text: config.subtitle, size: 24, color: P.subtitleColor, font: { eastAsia: "Microsoft YaHei", ascii: "Arial" } })],
    }));
  }
  children.push(new Paragraph({ spacing: { before: 1200 } }));
  for (const line of (config.metaLines || [])) {
    children.push(new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 100, line: Math.ceil(18 * 23), lineRule: "atLeast" },
      children: [new TextRun({ text: line, size: 36, color: P.metaColor, font: { eastAsia: "Microsoft YaHei", ascii: "Arial" } })],
    }));
  }
  children.push(new Paragraph({ spacing: { before: 2000 } }));
  children.push(new Paragraph({
    alignment: AlignmentType.CENTER,
    indent: { left: padL - 400, right: padR - 400 }, spacing: { before: 200 },
    border: { bottom: thickBorder },
    children: [new TextRun({ text: config.footerRight || "", size: 18, color: P.footerColor, font: { ascii: "Arial" } })],
  }));
  return [new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    layout: TableLayoutType.FIXED,
    borders: allNoBorders,
    rows: [new TableRow({
      height: { value: 16838, rule: "exact" },
      children: [new TableCell({ shading: { type: ShadingType.CLEAR, fill: P.bg }, borders: noBorders, children })],
    })],
  })];
}

// ---- 正文构件
const F = { ascii: "Calibri", eastAsia: "Microsoft YaHei" };
const FH = { ascii: "Calibri", eastAsia: "SimHei" };

function h1(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1, spacing: { before: 360, after: 140 },
    children: [new TextRun({ text, bold: true, size: 32, color: PALETTE.primary, font: FH })],
  });
}
function h2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2, spacing: { before: 260, after: 110 },
    children: [new TextRun({ text, bold: true, size: 28, color: PALETTE.primary, font: FH })],
  });
}
function h3(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_3, spacing: { before: 200, after: 90 },
    children: [new TextRun({ text, bold: true, size: 24, color: PALETTE.primary, font: FH })],
  });
}
function body(text, opts = {}) {
  const runs = Array.isArray(text) ? text : [new TextRun({ text, size: 24, color: PALETTE.body, font: F })];
  return new Paragraph({
    alignment: AlignmentType.JUSTIFIED,
    indent: opts.noIndent ? undefined : { firstLine: 420 },
    spacing: { line: 312, after: opts.after != null ? opts.after : 60 },
    keepNext: opts.keepNext || false,
    children: runs,
  });
}
function run(text, o = {}) {
  return new TextRun({ text, size: o.size || 24, bold: o.bold || false, color: o.color || PALETTE.body, font: F });
}
function bullet(text, level = 0) {
  return new Paragraph({
    alignment: AlignmentType.JUSTIFIED,
    indent: { left: 420 + level * 360, hanging: 240 },
    spacing: { line: 312, after: 40 },
    children: [new TextRun({ text: "\u25AA  ", size: 24, color: PALETTE.accent, font: F }),
               new TextRun({ text, size: 24, color: PALETTE.body, font: F })],
  });
}
function caption(text) {
  return new Paragraph({
    alignment: AlignmentType.CENTER, spacing: { before: 80, after: 200 },
    children: [new TextRun({ text, size: 18, color: PALETTE.secondary, font: F })],
  });
}
function tableTitle(text) {
  return new Paragraph({
    keepNext: true, spacing: { before: 160, after: 80 },
    children: [new TextRun({ text, bold: true, size: 21, color: PALETTE.primary, font: F })],
  });
}

// 横线表(Horizontal-Only,Profile A 默认)
function hTable(headerCells, dataRows, widths) {
  const T = PALETTE.table;
  const mk = (text, isHeader, alignLeft) => new TableCell({
    children: [new Paragraph({
      alignment: alignLeft ? AlignmentType.LEFT : AlignmentType.CENTER,
      spacing: { line: 280 },
      children: [new TextRun({ text: String(text), bold: isHeader, size: 21, color: isHeader ? T.headerText : PALETTE.body, font: F })],
    })],
    shading: isHeader ? { type: ShadingType.CLEAR, fill: T.headerBg } : undefined,
    margins: { top: 70, bottom: 70, left: 120, right: 120 },
    verticalAlign: VerticalAlign.CENTER,
  });
  return new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    layout: TableLayoutType.FIXED,
    columnWidths: widths,
    borders: {
      top: { style: BorderStyle.SINGLE, size: 4, color: T.accentLine },
      bottom: { style: BorderStyle.SINGLE, size: 4, color: T.accentLine },
      left: NB, right: NB,
      insideHorizontal: { style: BorderStyle.SINGLE, size: 1, color: T.innerLine },
      insideVertical: NB,
    },
    rows: [
      new TableRow({ tableHeader: true, cantSplit: true, children: headerCells.map((t, i) => mk(t, true, i === 0)) }),
      ...dataRows.map(r => new TableRow({ cantSplit: true, children: r.map((t, i) => mk(t, false, i === 0)) })),
    ],
  });
}

function pageFooter() {
  return new Footer({
    children: [new Paragraph({
      alignment: AlignmentType.CENTER,
      children: [new TextRun({ children: [PageNumber.CURRENT], size: 18, color: PALETTE.secondary, font: F })],
    })],
  });
}
function pageHeader(text) {
  return new Header({
    children: [new Paragraph({
      alignment: AlignmentType.RIGHT,
      border: { bottom: { style: BorderStyle.SINGLE, size: 2, color: PALETTE.table.innerLine } },
      children: [new TextRun({ text, size: 16, color: PALETTE.secondary, font: F })],
    })],
  });
}

module.exports = {
  PALETTE, buildCoverR2, h1, h2, h3, body, run, bullet, caption, tableTitle, hTable,
  pageFooter, pageHeader, F, FH,
};
