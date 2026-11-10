"""LLM客户端：封装DeepSeek API调用，含异常处理。"""
from openai import APIError, APITimeoutError, OpenAI

from .config import Config


class LLMError(Exception):
    """LLM调用失败的统一异常，message面向用户可读。"""


class LLMClient:
    def __init__(self, config: Config) -> None:
        self._client = OpenAI(
            api_key=config.api_key,
            base_url=config.base_url,
            timeout=config.timeout,
        )
        self._model = config.model

    def chat(self, system_prompt: str, user_prompt: str, json_mode: bool = True) -> str:
        """调用LLM，返回文本内容；失败时抛出LLMError。

        json_mode=True时强制模型输出json（DeepSeek要求提示词中含"json"字样）。
        """
        try:
            kwargs: dict = {}
            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}
            resp = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.2,
                **kwargs,
            )
        except APITimeoutError as e:
            raise LLMError("模型响应超时，请稍后重试") from e
        except APIError as e:
            raise LLMError(f"模型API调用失败：{e.message}") from e

        content = resp.choices[0].message.content
        if not content:
            raise LLMError("模型返回了空内容，请重试")
        return content
