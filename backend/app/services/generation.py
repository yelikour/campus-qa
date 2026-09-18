"""生成服务:可插拔 LLM Provider —— 本地抽取式(离线演示/降级)与智谱 GLM(云端)。

架构说明(对应架构文档 §6.3):
- 统一 Generator 接口,流式产出 token 序列(SSE 推送);
- 本地模式:基于检索片段的抽取式合成,保证零依赖、离线可演示,
  同时作为云端 LLM 超时/故障时的降级路径(熔断降级设计);
- 云端模式:智谱 GLM(openai 兼容协议),带引用上下文的提示词模板。
"""
from __future__ import annotations

import asyncio
import re
from typing import AsyncIterator

from ..config import settings
from .retrieval import RetrievedChunk, tokenize


class GeneratorProvider:
    name = "base"

    async def stream(self, query: str, contexts: list[RetrievedChunk]) -> AsyncIterator[str]:
        raise NotImplementedError
        yield ""


# ---------------------------------------------------------------- 本地抽取式生成
class LocalExtractiveGenerator(GeneratorProvider):
    name = "local-extractive"

    @staticmethod
    def _relevant_sentences(query: str, text: str, limit: int = 4) -> list[str]:
        q_tokens = set(tokenize(query))
        sents = [s.strip() for s in re.split(r"[。;!;?\n]", text) if len(s.strip()) >= 6]
        scored = []
        for s in sents:
            s_tokens = set(tokenize(s))
            scored.append((len(q_tokens & s_tokens), len(s), s))
        scored.sort(key=lambda x: (-x[0], -x[1]))
        picked = [s for sc, _, s in scored[:limit] if sc > 0] or \
                 [s for _, _, s in scored[:limit]]
        # 保序输出,符合原文逻辑
        return [s for s in sents if s in picked][:limit]

    async def stream(self, query: str, contexts: list[RetrievedChunk]) -> AsyncIterator[str]:
        top = contexts[0]
        body = self._relevant_sentences(query, top.chunk.answer_text or top.chunk.text)
        answer = "。".join(body) + ("。" if body else top.chunk.text)
        lead = f"根据《{top.chunk.source}》的相关规定:{answer}"
        tail = f"\n\n📋 信息来源:{top.chunk.source}(分类:{top.chunk.category})"
        # 按 2-4 字粒度切片流式输出,模拟 LLM token 流
        for piece in re.findall(r"[^。]{1,18}[。]?", lead + tail):
            yield piece
            await asyncio.sleep(0.045)


# ---------------------------------------------------------------- 智谱 GLM 云端生成
class ZhipuGenerator(GeneratorProvider):
    name = "zhipu-glm"

    SYSTEM_PROMPT = (
        "你是高校校园事务智能助手「智问校园」。请仅依据提供的参考资料回答学生问题,"
        "用简洁的中文分点作答;若资料不足请如实说明并建议咨询对应部门,不要编造。"
    )

    def _build_prompt(self, query: str, contexts: list[RetrievedChunk]) -> str:
        refs = "\n\n".join(
            f"[{i+1}] (来源:{c.chunk.source}) {c.chunk.text}" for i, c in enumerate(contexts)
        )
        return f"参考资料:\n{refs}\n\n学生问题:{query}"

    async def stream(self, query: str, contexts: list[RetrievedChunk]) -> AsyncIterator[str]:
        import httpx

        payload = {
            "model": settings.ZHIPU_MODEL,
            "messages": [
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": self._build_prompt(query, contexts)},
            ],
            "stream": True,
            "temperature": 0.3,
        }
        headers = {"Authorization": f"Bearer {settings.ZHIPU_API_KEY}"}
        try:
            async with httpx.AsyncClient(timeout=settings.LLM_TIMEOUT) as client:
                async with client.stream(
                    "POST", settings.ZHIPU_BASE_URL + "chat/completions",
                    json=payload, headers=headers,
                ) as resp:
                    resp.raise_for_status()
                    async for line in resp.aiter_lines():
                        if not line.startswith("data:"):
                            continue
                        data = line[5:].strip()
                        if data == "[DONE]":
                            break
                        import json
                        delta = json.loads(data)["choices"][0].get("delta", {})
                        if content := delta.get("content"):
                            yield content
        except Exception:
            # 熔断降级:云端不可用时回退本地抽取式生成,保证可用性
            async for piece in LocalExtractiveGenerator().stream(query, contexts):
                yield piece


def get_generator() -> GeneratorProvider:
    if settings.LLM_PROVIDER == "zhipu" and settings.ZHIPU_API_KEY:
        return ZhipuGenerator()
    return LocalExtractiveGenerator()
