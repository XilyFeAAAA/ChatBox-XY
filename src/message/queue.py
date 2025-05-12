from src.utils import logger,safe_create_task
import functools
import asyncio
import time


class MessageQueue:
    
    _instance: "MessageQueue" = None
    
    def __init__(self, interval) -> None:
        self.interval = interval
        self.queue: list[dict] = []
        self.running: bool = False
        self.last_end_time = 0
        self._processing_task = None
        
    @classmethod
    def get_instance(cls, interval: float = 2):
        if cls._instance is None:
            cls._instance = cls(interval)
        return cls._instance
    
    def start(self):
        if not self.running:
            self.running = True
            self._processing_task = safe_create_task(self._process_queue())
    
    def stop(self):
        self.running = False
        if self._processing_task and not self._processing_task.done():
            self._processing_task.cancel()
        
    def add_message(self, func: callable, *args, **kwargs):
        if not self.running:
            self.start()
            
        future = asyncio.Future()
        
        message = {
            "func": func,
            "args": args,
            "kwargs": kwargs,
            "future": future,
            "time": time.time()
        }
        self.queue.append(message)
        
        return future
    
    async def _process_queue(self):
        while self.running:
            if self.queue:
                now = time.time()
                duration = now - self.last_end_time
                
                if duration >= self.interval:
                    message = self.queue.pop(0)
                    self.last_end_time = time.time()
                    
                    try:
                        safe_create_task(self._send_message(
                            func=message["func"],
                            args=message["args"],
                            kwargs=message["kwargs"],
                            future=message["future"]
                        ))
                                        
                    except Exception as e:
                        logger.error(f"处理消息队列时出错: {e}")
                
                else:
                    wait_time = self.interval - duration
                    await asyncio.sleep(wait_time)
            else:
                await asyncio.sleep(0.1)
    
    async def _send_message(self, *, func, args, kwargs, future):
        try:
            result = await func(*args, **kwargs)
            if not future.done():
                future.set_result(result)
        except Exception as e:
            logger.error(f"发送消息失败: {e}")
            # 设置future异常
            if not future.done():
                future.set_exception(e)
                
    @property
    def size(self):
        return len(self.queue)
    
