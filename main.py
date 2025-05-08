from src.matcher import handle_message
from src.bot import Bot
from src.utils import logger, set_exception_handler, safe_create_task
import atexit
import asyncio


bot = Bot.get_instance()


async def main():
    # 前置检查
    await bot.preload()
    # 启动
    await bot.login()
    # 心跳机制
    await bot.keeplive()
    
    message_failure_count = 0
    max_failure_count = 3 
    while True:
        try:
            status, data = await bot.sync_message()
            if status:
                message_failure_count = 0
            if isinstance(data, dict):
                # logger.debug(data)
                if msgs := data.get("AddMsgs", []):
                    for msg in msgs:
                        safe_create_task(handle_message(msg))
            elif isinstance(data, str):
                if "已退出登录" in data or "会话已过期" in data:
                    message_failure_count += 1
            else:
                logger.warning(f"未知的数据类型:{type(data)}")
        except Exception as e:
            message_failure_count += 1
            raise e
        if message_failure_count > max_failure_count:
            return logger.warning(f"连续 {message_failure_count} 次获取消息失败，微信可能已离线")
        await asyncio.sleep(0.5)



async def on_exit():
    logger.info("程序即将退出，正在执行清理操作...")
    await bot.destory()
    

def sync_on_exit():
    asyncio.run(on_exit())

if __name__ == "__main__":
    atexit.register(sync_on_exit)
    set_exception_handler()
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        import sys
        sys.exit()