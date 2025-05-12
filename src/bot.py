from src.mixin import *
from src.utils import logger, Whitelist
from src.config import conf
import sys
import asyncio


class Bot(MessageMixIn, LoginMixIn, StatusMixIn, UserMixIn, 
          ChatroomMixIn, FriendMixIn, ProtocolMixin, ToolMixIn, PluginMixin):
    """机器人"""
    _instance = None

    def __init__(self):
        super().__init__()
        self.whitelist = Whitelist()
    
    async def preload(self):
        self.load_status()
        await self.load_plugin_from_dictionary()
        self.load_whitelist()
        self.use_queue()
        await self.start_protocol(
            executable_path=conf().get("PROTOCOL_PATH"),
            port=conf().get("PROTOCOL_PORT"),
            mode=conf().get("PROTOCOL_MODE"),
            redis_host=conf().get("REDIS_HOST"),
            redis_port=conf().get("REDIS_PORT"),
            redis_password=conf().get("REDIS_PASSWORD"),
            redis_db=conf().get("REDIS_DB")
        )
        time_out = 4
        while not await self.is_running() and time_out > 0:
            logger.info("等待WechatAPI启动中")
            await asyncio.sleep(2)
            time_out -= 2
        
        if time_out <= 0:
            logger.error("WechatAPI服务启动超时")
            sys.exit()
        
        logger.info(f"耗时{10-time_out}s,WechatAPI服务启动成功")

    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    
    def load_whitelist(self):
        whitelist_config = conf().get("WHITELIST", {})
        self.whitelist.enable() if whitelist_config.get("enable") else self.whitelist.disable()
        
        for user in whitelist_config.get("users", []):
            self.whitelist.add_user(user)
        
        for group in whitelist_config.get("chatrooms", []):
            self.whitelist.add_chatroom(group)
               
    
    def use_queue(self):
        
        enable =  conf().get("MESSAGE_QUEUE",{}).get("enable", False)
        interval = conf().get("MESSAGE_QUEUE",{}).get("interval", 1.0)
        try:
            if enable:
                from src.message import  MessageQueue
                MessageQueue.get_instance(interval).start()
                logger.info(f"消息队列已启动，全局发送间隔 {interval} 秒")
            else:
                logger.info("消息队列已禁用，消息将立即发送")
        except Exception as e:
            logger.warning(f"初始化消息队列失败: {e}")
            
    
    async def keeplive(self):
        if not await self.status_auto_heartbeat():
            await self.start_auto_heartbeat()
    
    
    async def destory(self):
        from src.message import MessageQueue
        self.is_logged = False
        if await self.status_auto_heartbeat():
            await self.stop_auto_heartbeat()
        try:
            await self.stop_protocol()
            logger.info("微信协议已关闭")
            MessageQueue.get_instance().stop()
            logger.info("消息队列已关闭")
        except Exception as e:
            logger.warning(f"关闭消息队列时出错: {e}")
            
        self.save_status()

    