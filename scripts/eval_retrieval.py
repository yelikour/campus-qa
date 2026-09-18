#!/usr/bin/env python3
"""检索质量评测:同义改写问题 → 检验混合检索 Hit@1 / Hit@3 / MRR。"""
import sys

sys.path.insert(0, "backend")
from app.services import ingestion
from app.services.retrieval import retriever

ingestion.startup()

# (改写问法, 期望命中文档ID) —— 模拟学生非标准提问
CASES = [
    ("图书馆几点开门", "kb-008"),
    ("书能借多少天", "kb-009"),
    ("饭卡找不到了", "kb-019"),
    ("怎么给校园卡充钱", "kb-020"),
    (" wifi 连不上咋整", "kb-021"),
    ("密码忘了", "kb-022"),
    ("国奖啥条件", "kb-023"),
    ("勤工俭学怎么报名", "kb-025"),
    ("想加社团", "kb-026"),
    ("三方协议盖章流程", "kb-029"),
    ("心情不好想找人聊聊", "kb-031"),
    ("羽毛球场怎么订", "kb-033"),
    ("军训能不能不去", "kb-049"),
    ("挂科了怎么办", "kb-052"),
    ("保研要什么条件", "kb-047"),
    ("论文重复率要求", "kb-037"),
    ("宿舍晚上几点断电", "kb-013"),
    ("报销医药费", "kb-048"),
    ("火车票学生优惠", "kb-054"),
    ("暑假能住学校吗", "kb-050"),
]

hit1 = hit3 = 0
mrr = 0.0
for q, gold in CASES:
    results = retriever.retrieve(q, top_k=3)
    doc_ids = [r.chunk.doc_id for r in results]
    if doc_ids and doc_ids[0] == gold:
        hit1 += 1
    if gold in doc_ids:
        hit3 += 1
        mrr += 1.0 / (doc_ids.index(gold) + 1)
    flag = "✓" if gold in doc_ids else "✗"
    print(f"{flag} [{q}] -> {doc_ids[:2]} (期望 {gold})")

n = len(CASES)
print(f"\n样本数 {n} | Hit@1 = {hit1/n:.1%} | Hit@3 = {hit3/n:.1%} | MRR = {mrr/n:.3f}")
