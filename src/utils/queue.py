from .log import logger
from .asyncio import safe_create_task
import functools
import asyncio
import time


class MessageQueue:
    
    _instance: "MessageQueue" = None
    
    def __init__(self, interval: float = 1) -> None:
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
                    message = self.queue.pop()
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
    

class MessageWrapper:
    """
    消息发送方法包装器
    将原有的消息发送方法包装，将消息添加到全局队列以控制发送速率
    """
    
    @staticmethod
    def wrap_send_methods(cls):
        """
        包装一个类的所有消息发送方法
        
        Args:
            cls: 要包装的类，通常是MessageMixIn
        """
        # 要包装的方法列表
        methods_to_wrap = [
            'send_text', 'send_image', 'send_voice', 
            'send_video', 'share_card', 'send_link'
        ]
        
        # 保存原始方法
        original_methods = {}
        
        # 包装每个方法
        for method_name in methods_to_wrap:
            if hasattr(cls, method_name):
                # 保存原始方法
                original_method = getattr(cls, method_name)
                original_methods[method_name] = original_method
                
                # 创建包装方法
                @functools.wraps(original_method)
                async def wrapped_method(self, *args, **kwargs):
                    # 获取消息队列实例
                    queue = MessageQueue.get_instance()
                    
                    # 获取对应的原始方法
                    current_method_name = method_name  # 捕获当前方法名
                    orig_method = original_methods[current_method_name]
                    
                    # 将消息添加到队列
                    return queue.add_message(
                        lambda *a, **kw: orig_method(self, *a, **kw),
                        *args,  # 保留所有参数
                        **kwargs
                    )
                
                # 设置方法的名称和签名，使其与原始方法匹配
                wrapped_method.__name__ = method_name
                wrapped_method.__qualname__ = f"{cls.__name__}.{method_name}"
                
                # 替换原始方法
                setattr(cls, method_name, wrapped_method)