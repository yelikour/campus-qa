#!/usr/bin/env python3
"""检索评测矩阵:62 条口语化改写 × 四条链路。

链路:
  BM25-only        —— 仅稀疏通道(jieba+BM25)
  Vector-only      —— 仅稠密通道(演示环境为 TF-IDF 词袋,非语义嵌入)
  Hybrid+RRF       —— 双通道召回 + RRF 融合,无重排
  Hybrid+Rerank    —— 生产全链路(RRF + 特征化轻量重排 + MIN_RELEVANCE 阈值)

指标:Hit@1 / Hit@3 / MRR(评估单位为文档级,chunk 命中按 doc_id 去重保序)。
口径:四条链路统一为文档级去重口径(Hybrid+RRF 直接消费 fuse_rrf 原始融合输出,
每通道 top-20 chunks 取前 10,再按文档去重 —— 与 BM25/Vector 路径口径一致)。
注:早期版本 RRF 口径存在"同文档双通道 chunk 重复占位"失真(Hit@3=95.2),
生产链路补齐文档级去重后统一口径实测 Hit@3=98.4,以此为准。
"""
import sys

sys.path.insert(0, "backend")
from app.services import ingestion
from app.services.retrieval import retriever

ingestion.startup()

# (口语化/同义改写问法, 期望命中文档ID)
CASES = [
    ("什么时候能选课", "kb-001"), ("过了退课时间还能改吗", "kb-002"),
    ("绩点在哪里查", "kb-003"), ("GPA是怎么算的", "kb-004"),
    ("生病了没法考试怎么办", "kb-005"), ("能修别的学院的课吗", "kb-006"),
    ("想休学一年怎么弄", "kb-007"), ("图书馆几点开门", "kb-008"),
    ("书能借多少天", "kb-009"), ("小组讨论室怎么订", "kb-010"),
    ("在校外怎么查文献数据库", "kb-011"), ("本校没有的书怎么借", "kb-012"),
    ("宿舍晚上几点断电", "kb-013"), ("宿舍可以用电饭锅吗", "kb-014"),
    ("想换宿舍怎么申请", "kb-015"), ("宿舍网怎么开通", "kb-016"),
    ("哪个食堂好吃", "kb-017"), ("外卖能送到宿舍吗", "kb-018"),
    ("饭卡找不到了", "kb-019"), ("怎么给校园卡充钱", "kb-020"),
    ("wifi连不上咋整", "kb-021"), ("密码忘了", "kb-022"),
    ("国奖啥条件", "kb-023"), ("家里困难有什么补助", "kb-024"),
    ("勤工俭学怎么报名", "kb-025"), ("想加社团", "kb-026"),
    ("社团活动教室怎么申请", "kb-027"), ("宣讲会在哪看", "kb-028"),
    ("三方协议盖章流程", "kb-029"), ("自己找的实习算学分吗", "kb-030"),
    ("心情不好想找人聊聊", "kb-031"), ("最近失眠焦虑怎么办", "kb-032"),
    ("羽毛球场怎么订", "kb-033"), ("体测不及格会怎样", "kb-034"),
    ("开学报到要准备什么", "kb-035"), ("学费怎么交", "kb-036"),
    ("论文重复率要求", "kb-037"), ("毕业要办哪些手续", "kb-038"),
    ("可以修双学位吗", "kb-039"), ("考试带手机会怎么样", "kb-040"),
    ("怎么在图书馆找到一本书", "kb-041"), ("学校邮箱怎么登录", "kb-042"),
    ("宿舍水管坏了找谁", "kb-043"), ("想自己创办一个社团", "kb-044"),
    ("档案留学校影响考公吗", "kb-045"), ("综测是怎么算的", "kb-046"),
    ("保研要什么条件", "kb-047"), ("在校医院看病怎么报销", "kb-048"),
    ("军训能不能不去", "kb-049"), ("暑假能住学校吗", "kb-050"),
    ("写论文用什么管理文献", "kb-051"), ("挂科了怎么办", "kb-052"),
    ("数学建模比赛怎么参加", "kb-053"), ("回家火车票有优惠吗", "kb-054"),
    ("什么情况拿不到学位证", "kb-055"), ("心理工作坊怎么报名", "kb-056"),
    ("食堂有隐性资助吗", "kb-057"), ("校运会怎么报名", "kb-058"),
    ("快递到了去哪取", "kb-059"), ("补考要交钱吗", "kb-052"),
    ("考试周图书馆延长开放吗", "kb-008"), ("借的书到期了怎么续", "kb-009"),
]


def doc_ranking(chunk_hits):
    """chunk 级命中列表 → 文档级去重保序排名。"""
    seen, docs = set(), []
    for idx, *_ in chunk_hits:
        doc = retriever.chunks[idx].doc_id
        if doc not in seen:
            seen.add(doc)
            docs.append(doc)
    return docs


def evaluate(name, fn):
    hit1 = hit3 = 0
    mrr = 0.0
    misses = []
    for q, gold in CASES:
        docs = fn(q)
        if docs and docs[0] == gold:
            hit1 += 1
        if gold in docs[:3]:
            hit3 += 1
            mrr += 1.0 / (docs.index(gold) + 1)
        else:
            misses.append((q, gold, docs[:2]))
    n = len(CASES)
    print(f"{name:16s} Hit@1={hit1/n:.1%}  Hit@3={hit3/n:.1%}  MRR={mrr/n:.3f}")
    return misses


if __name__ == "__main__":
    print(f"评测集:{len(CASES)} 条 | 索引:{len(retriever.chunks)} chunks | "
          f"向量通道:{retriever.embedder_name}(非语义嵌入,见材料说明)\n")
    m_bm25 = evaluate("BM25-only", lambda q: doc_ranking(retriever.bm25.search(q, 10)))
    m_vec = evaluate("Vector-only", lambda q: doc_ranking(retriever.vector.search(q, 10)))
    # 口径说明:RRF 评测直接使用 fuse_rrf 原始融合输出(每通道 top-20 chunks,取前 10),
    # 与 BM25/Vector 路径同口径;生产 retrieve(rerank=False) 内部的文档级去重不参与评测
    m_rrf = evaluate("Hybrid+RRF", lambda q: doc_ranking(retriever.fuse_rrf(q, candidate_k=20)[:10]))
    m_full = evaluate("Hybrid+Rerank", lambda q: [r.chunk.doc_id for r in retriever.retrieve(q, top_k=10)])

    print("\nHybrid+Rerank 未命中样例(供归因):")
    for q, gold, got in m_full[:6]:
        print(f"  ✗ [{q}] 期望 {gold} 实得 {got}")
