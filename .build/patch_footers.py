# -*- coding: utf-8 -*-
"""docx 页脚 PAGE 域格式后处理:
- 按文档节顺序定位各节 footer(Roman 前置节 / Arabic 正文节),注入显式格式开关(WPS 兼容)
- 移除封面节可能残留的空 <w:pgNumType/>
"""
import re
import shutil
import sys
import zipfile
from pathlib import Path

path = Path(sys.argv[1])
tmp = path.with_suffix(".tmp.docx")

with zipfile.ZipFile(path) as z:
    names = z.namelist()
    files = {n: z.read(n) for n in names}

doc = files["word/document.xml"].decode("utf-8")
rels = files["word/_rels/document.xml.rels"].decode("utf-8")

# rId -> footer 文件名
rel_map = dict(re.findall(r'<Relationship[^>]*Id="([^"]+)"[^>]*Target="(footer\d+\.xml)"', rels))
rel_map.update({rid: t for rid, t in re.findall(r'<Relationship[^>]*Target="(?:footer\d+\.xml)"[^>]*Id="([^"]+)"', rels) and []})

# 各节的 footerReference(按出现顺序)
sect_footers = []
for sect in re.findall(r"<w:sectPr[\s\S]*?</w:sectPr>|<w:sectPr[^>]*/>", doc):
    m = re.search(r'<w:footerReference[^>]*w:type="default"[^>]*r:id="([^"]+)"', sect)
    fmt = re.search(r'<w:pgNumType[^>]*w:fmt="([^"]+)"', sect)
    sect_footers.append((rel_map.get(m.group(1)) if m else None, fmt.group(1) if fmt else None))

print("sections:", sect_footers)

# 每节按 fmt 注入 PAGE 域开关;无 fmt 但带 footer 的前置节(目录)按 roman 处理
seen = set()
for footer, fmt in sect_footers:
    if not footer or footer in seen:
        continue
    seen.add(footer)
    key = "word/" + footer
    if key not in files:
        continue
    xml = files[key].decode("utf-8")
    switch = "ROMAN" if (fmt in (None, "upperRoman", "lowerRoman") and fmt != "decimal") else "arabic"
    xml2 = re.sub(r'(<w:instrText[^>]*>)\s*PAGE\s*(</w:instrText>)',
                  r"\g<1> PAGE \\* " + switch + r" \\* MERGEFORMAT \g<2>", xml)
    if xml2 != xml:
        files[key] = xml2.encode("utf-8")
        print(f"patched {footer} -> {switch}")

# 清理空 pgNumType
doc2 = doc.replace("<w:pgNumType/>", "")
if doc2 != doc:
    files["word/document.xml"] = doc2.encode("utf-8")
    print("stripped empty pgNumType")

with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
    for n in names:
        z.writestr(n, files[n])
shutil.move(tmp, path)
print("footer patch done:", path.name)
