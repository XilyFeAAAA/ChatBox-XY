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
            r"D:/@DevCode/github/XYBotV2/WechatAPI/core/XYWechatPad.exe",
            "-p", "9000",
            "-m", "release",
            "-rh", "127.0.0.1",
            "-rp", "6379",
            "-rpwd", "",
            "-rdb", "0"
        ]
        logger.debug("准备启动服务")
        # 使用异步创建子进程
        self.process = await asyncio.create_subprocess_exec(
            *command,
            cwd=os.path.dirname(os.path.abspath(__file__)),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
        logger.debug(f"服务已启动，PID: {self.process.pid}")
        logger.debug("已启动服务")
        
        
        
    async def stop_protocol(self):
        """异步停止服务"""
        if hasattr(self, 'process'):
            try:
                self.process.terminate()
                await self.process.wait()
            except ProcessLookupError:
                logger.warning("尝试终止已退出的进程")
    
    