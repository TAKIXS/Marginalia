"""AI 感悟生成服务 — DeepSeek (OpenAI 兼容接口)"""

import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.deepseek.com")
LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-chat")

_client = None  # lazy init after openai is verified available


def _ensure_client():
    """延迟初始化 LLM 客户端，未安装 openai 或未配置 Key 时给出明确提示"""
    global _client
    if not LLM_API_KEY:
        raise RuntimeError("AI 服务未配置，请在 .env 中设置 LLM_API_KEY")
    if _client is None:
        try:
            from openai import AsyncOpenAI
        except ImportError:
            raise RuntimeError("openai 库未安装，请执行: pip install openai")
        _client = AsyncOpenAI(
            api_key=LLM_API_KEY,
            base_url=LLM_BASE_URL,
            timeout=30.0,
        )
    return _client


SYSTEM_PROMPT = """你是一位深度阅读者。根据用户提供的摘抄原文，写一段简洁的个人感悟或思考。
要求：
- 2-4 句话，不超过150字
- 可以涉及：这段文字为什么触动人心、它在现实生活中的映射、与其他知识的关联
- 语气自然，像随手写下的读书笔记，不要 AI 腔"""


async def generate_insights(content: str, book_title: Optional[str] = None) -> str:
    """调用 LLM 为摘抄内容生成个人感悟"""
    client = _ensure_client()

    user_prompt = f"摘抄原文：\n{content}"
    if book_title:
        user_prompt = f"摘抄来源：《{book_title}》\n\n摘抄原文：\n{content}"

    response = await client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.8,
        max_tokens=300,
    )

    text = response.choices[0].message.content
    if not text:
        return "AI 暂无法生成感悟，请手动填写"
    return text.strip()
