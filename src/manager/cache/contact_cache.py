from src.bot import Bot
from src.model import CachedData, Contact, CacheType
from src.utils import logger
from .cache import Cache
import asyncio

bot = Bot.get_instance()

class ContactCache(Cache):
    
    def __init__(self) -> None:
        super().__init__(CacheType.CONTACT)
        self._locks: dict[str, asyncio.Lock] = {}
        
    async def update(self) -> CachedData:
        """
        调用接口更新联系人信息
        TODO 暂时只有好友列表
        """
        contact = {
            "friends": await bot.get_friends()
        }
        self._set("contact", contact)
        

    async def get(self) -> Contact | None:
        if contact_info := self._get("contact"):
            return contact_info
        async with self._lock:
            if contact_info := self._get("contact"):
                return contact_info
            logger.warning(f"联系人缓存不存在，正在获取")
            contact_info = await self.update()
            return contact_info