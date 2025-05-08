from src.model import Chatroom, CachedData, CacheType
from src.utils import logger
from abc import ABC, abstractmethod
import time


class Cache(ABC):
    
    def __init__(self, cache_type: CacheType, cache_ttl: int = 60 * 30) -> None:    
        self.cache: dict[str, CachedData] = {}
        self.cache_ttl: int = cache_ttl
        self.cache_type: CacheType = cache_type
    
    @abstractmethod
    async def update(self):
        raise NotImplementedError
    
    
    def _get(self, cache_id: str) -> any:
        """获取Cache信息"""
        cache_data = self.cache.get(cache_id)
        
        if cache_data and time.time() - cache_data.timestamp > self.cache_ttl:
            logger.warning(f"缓存[{self.cache_type}:{cache_id}]已过期")
            self.remove(cache_id)
            
        return cache_data.data if cache_data else None
    
    
    def _set(self, cache_id: str, cache_data: dict) -> any:
        """设置Cache信息,存在则覆盖"""
        self.cache[cache_id] = CachedData.new(cache_data, self.cache_type)
        return self.cache[cache_id].data
    
        
    def remove(self, cache_id: str) -> None:
        """移除指定群聊的缓存"""
        if cache_id in self.cache:
            del self.cache[cache_id]
            logger.debug(f"缓存[{self.cache_type}:{cache_id}]已移除")  
        
        
    def clear(self):
        """清空所有缓存"""
        self.cache.clear()
        logger.debug(f"缓存[{self.cache_type}]已清空") 
        
        