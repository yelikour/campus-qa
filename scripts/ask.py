#!/usr/bin/env python3
"""命令行快速验证 SSE 问答流:拼合 delta 输出完整回答。"""
import json
import sys

import httpx

query = sys.argv[1] if len(sys.argv) > 1 else "图书馆开放时间"
url = "http://127.0.0.1:8000/api/chat"
text, sources = [], []
with httpx.Client(timeout=60) as c:
    with c.stream("POST", url, json={"message": query}, headers={"X-User-Token": "cli-tester"}) as r:
        for line in r.iter_lines():
            if line.startswith("event: "):
                kind = line[7:].strip()
            elif line.startswith("data: "):
                data = json.loads(line[6:])
                if kind == "delta":
                    text.append(data["text"])
                elif kind == "meta":
                    sources = data["sources"]
                    print(f"[检索] {data['retrieval_ms']}ms,provider={data['provider']}")
                    for s in sources:
                        print(f"  - {s['doc_id']} {s['title']} score={s['score']} bm25#{s['bm25_rank']} vec#{s['vec_rank']}")
print("[回答]", "".join(text))
