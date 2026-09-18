"""全局配置:环境变量驱动,支持本地/云端 LLM 双模部署。"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

class Settings:
    # 应用
    APP_NAME = "智问校园 CampusMind"
    APP_VERSION = "1.0.0"
    HOST = os.getenv("APP_HOST", "127.0.0.1")
    PORT = int(os.getenv("APP_PORT", "8000"))

    # 数据
    DB_PATH = Path(os.getenv("DB_PATH", BASE_DIR / "data" / "campusqa.db"))
    SEED_QA_PATH = BASE_DIR / "data" / "campus_qa.json"

    # 检索参数(RAG 流水线)
    CHUNK_TOP_K = 5          # 融合后送入重排的候选数
    FINAL_TOP_K = 3          # 最终送入生成的上下文条数
    RRF_K = 60               # Reciprocal Rank Fusion 常数
    # 低于该分数视为无相关知识,触发兜底话术(62 条评测标定:0.15 会误杀
    # 口语化弱重叠的正解,0.06 以下会放入无关命中,取 0.08)
    MIN_RELEVANCE = float(os.getenv("MIN_RELEVANCE", "0.08"))

    # 限流(令牌桶,演示单机实现;生产用 Redis + 滑动窗口)
    RATE_LIMIT_QPS = float(os.getenv("RATE_LIMIT_QPS", "5"))
    RATE_LIMIT_BURST = int(os.getenv("RATE_LIMIT_BURST", "10"))

    # LLM 生成:可插拔 Provider
    # local  = 内置抽取式生成器(离线可跑,用于演示与降级)
    # zhipu  = 智谱 GLM(openai 兼容协议,需 ZHIPUAI_API_KEY)
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "local")
    ZHIPU_API_KEY = os.getenv("ZHIPUAI_API_KEY", "")
    ZHIPU_BASE_URL = "https://open.bigmodel.cn/api/paas/v4/"
    ZHIPU_MODEL = os.getenv("ZHIPU_MODEL", "glm-4-flash")
    LLM_TIMEOUT = 30.0

    # Embedding:可插拔向量提供者(auto = 有 Key 用云端语义向量,否则 TF-IDF)
    # tfidf  = TF-IDF 加权词袋(离线 fallback,无语义嵌入能力)
    # zhipu  = 智谱 embedding-3(openai 兼容 /embeddings,需 ZHIPUAI_API_KEY)
    EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "auto")

settings = Settings()
