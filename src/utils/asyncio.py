from .exception import global_exception_handler
import asyncio


def handle_task_exception(task):
    try:
        task.result()
    except asyncio.CancelledError:
        # 忽略任务取消异常
        pass
    except Exception as e:
        global_exception_handler(type(e), e, e.__traceback__)
        

def safe_create_task(coro):
    task = asyncio.create_task(coro)
    task.add_done_callback(handle_task_exception)
    return task

import inspect

async def call_func(func, *args, **kwargs):
    if inspect.iscoroutinefunction(func):
        return await func(*args, **kwargs)
    else:
        return func(*args, **kwargs)