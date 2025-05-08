from .exception import global_exception_handler
import asyncio


def handle_task_exception(task):
    try:
        task.result()
    except Exception as e:
        global_exception_handler(type(e), e, e.__traceback__)
        

def safe_create_task(coro):
    task = asyncio.create_task(coro)
    task.add_done_callback(handle_task_exception)
    return task