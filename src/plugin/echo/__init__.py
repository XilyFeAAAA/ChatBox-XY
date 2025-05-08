from src.message import TextMessage
from src.matcher import from_chatroom, on_message
from src.model import MessageSource
from src.utils import logger

@on_message()
async def echo(msg: TextMessage):
    if msg.source ==  MessageSource.FRIEND:
        logger.debug(msg.sender)
        source_ = '私聊' 
        from_ = msg.sender.name
    else:
        source_ = '群聊'
        from_ = msg.chatroom.nickname
    logger.info(f"接受到{source_}消息,来自{from_},内容为{msg.text}")