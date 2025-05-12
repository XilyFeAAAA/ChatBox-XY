from src.message import TextMessage
from src.matcher import on_regex
from src.bot import Bot
from src.utils import logger
from .core import Douyin
import re


douyin = Douyin()
bot = Bot.get_instance()
share_pattern = r'复制打开抖音|打开抖音|抖音视频'
url_pattern = r'https?://[^\s<>"]+?(?:douyin\.com|iesdouyin\.com)[^\s<>"]*'


basic_rules = [()]
@on_regex([share_pattern, url_pattern])
async def shared_video(bot: Bot, msg: TextMessage):
    if (match := re.search(url_pattern, msg.text)) is None: return
    douyin_url = match.group(0)
    try:
        result = await douyin.parse_video(douyin_url)
        logger.debug(f"抖音解析结果: {result}")
        await douyin.send_card(msg.from_wxid, result)
    except Exception as e:
        logger.error(f"处理抖音链接时发生错误: {str(e)}")
        await bot.send_text(msg.from_wxid, "解析失败，请稍后重试")