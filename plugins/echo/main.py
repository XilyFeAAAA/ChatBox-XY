from src.message import TextMessage
from src.bot import Bot
from src.plugin import PluginBase
from src.model import MessageSource
from src.utils import logger


class Echo(PluginBase):
    
    __description__ = "消息提示"
    __author__ = "xilyfe"
    __version__ = "1.0.0"

    @PluginBase.on_message()
    async def echo(self, bot: Bot, msg: TextMessage):
        if msg.source ==  MessageSource.FRIEND:
            source_ = '私聊' 
            from_ = msg.sender.name
        else:
            source_ = '群聊'
            from_ = msg.chatroom.nickname
        logger.info(f"接受到{source_}消息,来自{from_},内容为{msg.text}")