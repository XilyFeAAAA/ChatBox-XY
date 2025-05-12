from src.utils import logger, get_json
from .base import BaseMixIn
import os
import aiohttp
import asyncio
import subprocess

class ProtocolMixin(BaseMixIn):
    
    async def is_running(self):
        try:
            resp = await get_json("/IsRunning")
            return await resp.text() == 'OK'
        except aiohttp.client_exceptions.ClientConnectorError:
            return False
    
    
    async def start_protocol(self, executable_path, port, mode, redis_host, redis_port, redis_password, redis_db):
        """异步启动服务"""
        command = [
            "D:/@DevCode/projects/chatbox/chatbot-xy/src/XYWechatPad.exe",
            "-p", str(port),
            "-m", mode,
            "-rh", redis_host,
            "-rp", str(redis_port),
            "-rpwd", redis_password,
            "-rdb", str(redis_db)
        ]
        # 使用异步创建子进程
        self.process = await asyncio.create_subprocess_exec(
            *command,
            cwd=os.path.dirname(os.path.abspath(__file__)),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
        
        
    async def stop_protocol(self):
        """异步停止服务"""
        if hasattr(self, 'process'):
            try:
                self.process.terminate()
                await self.process.wait()
            except ProcessLookupError:
                logger.warning("尝试终止已退出的进程")
    
    