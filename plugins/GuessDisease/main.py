from src.message import TextMessage
from src.bot import Bot
from src.plugin import PluginBase
from src.model import MessageSource
from src.utils import logger
from src.matcher.rule import to_me, from_chatroom
from aiohttp import ClientSession, FormData
from datetime import datetime


rules = [to_me(), from_chatroom()]

class GuessDisease(PluginBase):
    
    __description__ = "每日挑战 - 猜病"
    __author__ = "xilyfe"
    __version__ = "1.0.0"

    def __init__(self) -> None:
        super().__init__()
        self.sessions: dict[str, list[ClientSession, str]] = {} # chatroom_id: session, chatId
    
    async def send_message(self, chatroom_id: str, text: str):
        url = "https://xiaoce.fun/api/v0/quiz/daily/guessDisease/sendMessage"

        session, chat_id = self.sessions[chatroom_id]
        # 表单数据（multipart/form-data）
        form_data = FormData()
        form_data.add_field('date', datetime.today().strftime('%Y%m%d'))
        form_data.add_field('message', text)
        if chat_id is not None:
            form_data.add_field("chatId", chat_id)
        resp = await session.post(url, data=form_data)
        return await resp.json()
        

    @PluginBase.on_message(rules=rules)
    async def chat(self, bot: Bot, msg: TextMessage):
        cid = msg.chatroom.chatroom_id
        if cid not in self.sessions:
            self.sessions[cid] = [ClientSession(), None]
        
        resp = await self.send_message(cid, msg.text)
        if resp.get("success", False):
            self.sessions[cid][1] = resp.get("data", {}).get("chatId")
            if resp.get("data", {}).get("right", False):
                await bot.send_text(cid, "恭喜你，你猜对了！")
                self.sessions.pop(cid, None)
            else:
                answer = resp.get("data", {}).get("answer", "返回null")
                await bot.send_text(cid, answer)
        else:
            logger.error(f"群聊{cid}消息发送失败, 报错: {resp}")
            await bot.send_text(cid, "消息发送失败")
    
    @PluginBase.on_fullmatch(text="重开", rules=rules, priority=10,block=True)
    async def reload(self, bot: Bot, msg: TextMessage):
        cid = msg.chatroom.chatroom_id
        if cid in self.sessions:
            self.sessions.pop(cid, None)
            await bot.send_text(cid, "重置成功")