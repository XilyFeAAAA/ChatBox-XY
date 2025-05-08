from .base import BaseMixIn
from src.utils import logger
import functools
import json

class StatusMixIn(BaseMixIn):
    
    # 白名单字段
    STATUS_FIELDS = [
        'uuid', 'wxid', 'nickname', 'alias', 'phone', 'is_logged', 'device_name', 'device_id'
    ]
    
    def __init__(self):
        self.uuid: str = ""
        self.wxid: str = ""
        self.nickname: str = ""
        self.alias: str = ""
        self.phone: str = ""
        self.is_logged: bool = False
        self.device_name: str = ""
        self.device_id: str = ""
        
    
    def load_status(self):
        with open("status.json", 'r', encoding='utf-8') as f:
            data = json.load(f)
        for k in self.STATUS_FIELDS:
            setattr(self, k, data.get(k))


    def save_status(self):
        data = {k: getattr(self, k) for k in self.STATUS_FIELDS}
        with open("status.json", 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    
    
    @staticmethod
    def require_login(func):
        @functools.wraps(func)
        async def wrapper(self, *args, **kwargs):
            if not self.is_logged:
                return logger.warning(f"未登录，接口{func.__name__}未执行")
            return await func(self, *args, **kwargs)
        return wrapper
    
            
    async def is_logged_in(self):
        try:
            logger.debug("is_logged_in")
            await self.get_profile()
            self.is_logged = True
            return True
        except Exception as e:
            logger.error(f"is_logged_in: {e}")
            return False
        
