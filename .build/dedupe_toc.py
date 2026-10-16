# -*- coding: utf-8 -*-
"""TOC 首条目去重 v2:定位含 PAGEREF _Toc1 的 hyperlink 段落,若下一段落文本相同则删除该 hyperlink 段落。"""
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

# hyperlink 条目内联在 TOC 域段落(separate 之后);其后的纯文本段落带页码,是保留版
hm = re.search(r'<w:hyperlink[^>]*>[\s\S]*?PAGEREF _Toc1 [\s\S]*?</w:hyperlink>', doc)
removed = 0
if hm:
    block = hm.group(0)
    t1 = "".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", block))
    after = doc[hm.end():hm.end() + 2000]
    t2m = re.search(r"<w:t[^>]*>([^<]*)</w:t>", after)
    if t2m and t1.strip() == t2m.group(1).strip():
        doc = doc.replace(block, "", 1)
        removed = 1
        print(f"deduped: {t1!r}")
    else:
        print("hyperlink found but next text differs:", repr(t1), repr(t2m.group(1) if t2m else None))
else:
    print("no hyperlink entry found")

if removed:
    files["word/document.xml"] = doc.encode("utf-8")
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
        for n in names:
            z.writestr(n, files[n])
    shutil.move(tmp, path)
else:
    print("no duplicate found")
print("done:", path.name)
