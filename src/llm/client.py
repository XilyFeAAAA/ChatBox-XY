from src.utils import logger
from . import config
from openai import OpenAI, RateLimitError, APITimeoutError, APIError, AsyncOpenAI
import asyncio

class LLMClient:
    
    def __init__(self, api_key: str) -> None:
        if not api_key:
            raise KeyError("大模型 API_KEY 为空")
        self.client = AsyncOpenAI(api_key=api_key)
        
        
    async def _request(self, method, *args, **kwargs):
        for attempt in range(config.MAX_RETRIES):
            try:
                return await method(*args, **kwargs)
            except RateLimitError:
                logger.error(f"超出速率限制, 第{attempt}/{config.MAX_RETRIES}次尝试")
                await asyncio.sleep(config.RETRY_DELAY)
            except APITimeoutError:
                logger.error(f"超出连接时间限制, 第{attempt}/{config.MAX_RETRIES}次尝试")
                await asyncio.sleep(config.RETRY_DELAY)
            except APIError as e:
                logger.error(f"OPAI API错误: {e}, 第{attempt}/{config.MAX_RETRIES}次尝试")
                await asyncio.sleep(config.RETRY_DELAY)
            except Exception as e:
                logger.error(f"未知错误: {e}, 第{attempt}/{config.MAX_RETRIES}次尝试")
                await asyncio.sleep(config.RETRY_DELAY)
        raise Exception("连接OPENAI失败")
    
    async def get_chat_completion(self, _messages: list[dict], model: str, max_token: int):
        messages = _messages.copy()
        if config.SYSTEM_PROMPT_OVERRIDE:
            if messages and messages[0]["role"] == "system":
                messages[0]["content"] = config.DEFUALT_SYSTEM_PROMPT
            else:
                messages.insert(0, {"role": "system", "content": config.DEFUALT_SYSTEM_PROMPT})
        try:
            response = await self._request(
                self.client.chat.completions.create,
                model=model,
                messages=messages,
                max_token=max_token,
                temperature=config.CHAT_TEMPERTURE,
                timeout=config.REQUEST_TIMEOUT
            )
            if response.choices and (text := response.choices[0].message):
                return text.strip()
            return None
        except Exception as e:
            logger.error(f"获取对话结果失败: {e}")
            return None
        
        
    async def get_summary(self, text_to_summarize: str, sumary_prompt: str, model: str, max_token: int):
        messages = [
            {"role": "system", "content": sumary_prompt},
            {"role": "user", "content": text_to_summarize}
        ]
        try:
            response = await self._request(
                self.client.chat.completions.create,
                model=model,
                messages=messages,
                max_token=max_token,
                temperature=config.SUMMARY_TEMPERTURE,
                timeout=config.REQUEST_TIMEOUT
            )
            if response.choices and (text := response.choices[0].message):
                return text.strip()
            return None
        except Exception as e:
            logger.error(f"获取Summary结果失败: {e}")
            return None