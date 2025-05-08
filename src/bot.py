from src.mixin import *
from src.utils import logger, MessageWrapper, MessageQueue, Whitelist
from src.config import conf
import sys
import asyncio
import pkgutil
import importlib


class Bot(MessageMixIn, LoginMixIn, StatusMixIn, UserMixIn, ChatroomMixIn, FriendMixIn, ProtocolMixin, ToolMixIn):
    """机器人"""
    _instance = None

    def __init__(self):
        super().__init__()
        self.whitelist = Whitelist()
    
    async def preload(self):
        self.load_status()
        self.load_plugin()
        self.load_whitelist()
        await self.start_protocol(
            executable_path=conf().get("PROTOCOL_PATH"),
            port=conf().get("PROTOCOL_PORT"),
            mode=conf().get("PROTOCOL_MODE"),
            redis_host=conf().get("REDIS_HOST"),
            redis_port=conf().get("REDIS_PORT"),
            redis_password=conf().get("REDIS_PASSWORD"),
            redis_db=conf().get("REDIS_DB")
        )
        time_out = 10
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

    def load_plugin(self):
        plugin_packages = pkgutil.iter_modules(path=["src/plugin"])
        
        # 2. 遍历扫描到的模块/包
        for _, name, ispkg in plugin_packages:
            # 3. 检查是否是包（文件夹，而非单文件）
            if ispkg and not name.startswith('_'):  # 如果是包（文件夹）
                # 4. 动态导入该包（如 "plugin.plugin1"）
                importlib.import_module(f"src.plugin.{name}")
                logger.info(f"成功导入插件：{name}")
    
    def load_whitelist(self):
        whitelist_config = conf().get("WHITELIST", {})
        self.whitelist.enable() if whitelist_config.get("enable") else self.whitelist.disable()
        
        for user in whitelist_config.get("users", []):
            self.whitelist.add_user(user)
        
        for group in whitelist_config.get("chatrooms", []):
            self.whitelist.add_chatroom(group)
               
    
    def use_queue(self):
        enable =  conf().get("Message_QUEUE",{}).get("enable", False)
        interval = conf().get("Message_QUEUE",{}).get("interval", 1.0)
        try:
            if enable:
                queue = MessageQueue(interval)
                queue.start()
                MessageWrapper.wrap_send_methods(MessageMixIn)
                logger.info(f"消息队列已启动，全局发送间隔 {interval} 秒")
            else:
                logger.info("消息队列已禁用，消息将立即发送")
        except Exception as e:
            logger.warning(f"初始化消息队列失败: {e}")
            
    
    async def keeplive(self):
        if not await self.status_auto_heartbeat():
            await self.start_auto_heartbeat()
    
    
    async def destory(self):
        self.is_logged = False
        if await self.status_auto_heartbeat():
            await self.stop_auto_heartbeat()
        try:
            await self.stop_protocol()
            logger.info("微信协议已关闭")
            queue = MessageQueue.get_instance()
            queue.stop()
            logger.info("消息队列已关闭")
        except Exception as e:
            logger.warning(f"关闭消息队列时出错: {e}")
            
        self.save_status()

    