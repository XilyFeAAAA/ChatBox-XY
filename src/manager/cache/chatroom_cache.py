from src.bot import Bot
from src.model import Chatroom, CachedData, ChatroomMember, CacheType
from src.utils import logger
from .cache import Cache
import asyncio

bot = Bot.get_instance()

class ChatroomCache(Cache):
    
    def __init__(self) -> None:
        super().__init__(CacheType.CHATROOM)
        self._locks: dict[str, asyncio.Lock] = {}
        
    async def update(self, chatroom_id: str) -> CachedData:
        """调用接口更新群聊信息"""
        resp = await bot.get_chatroom_info(chatroom_id)
        member_list = await bot.get_chatroom_member(chatroom_id)
        if resp is None:
            raise RuntimeError(f"获取群聊{chatroom_id}信息失败: get_chatroom_info接口返回null")
        elif resp.get("ContactCount", 0) != 1:
            raise RuntimeError(f"获取群聊{chatroom_id}信息失败: ContactCount != 1")
        else:
            chatroom = resp.get("ContactList", [])[0]
            return self._set(chatroom_id, {
                "chatroom_id": chatroom.get("UserName", {}).get("string", ""),
                "nickname": chatroom.get("NickName", {}).get("string", ""),
                "remark": chatroom.get("Remark", {}).get("string", ""),
                "chatroom_owner": chatroom.get("ChatRoomOwner", ""),
                "small_image": chatroom.get("SmallHeadImgUrl", ""),
                "member_list": [{
                    "wxid": member.get("UserName", ""),
                    "nickname": member.get("NickName", ""),
                    "invite_wxid": member.get("InviterUserName", ""),
                    "displayname": member.get("DisplayName", ""),
                    "big_image": member.get("BigHeadImgUrl", ""),
                    "small_image": member.get("SmallHeadImgUrl", "")
                    } for member in member_list]
            })
            
    
    async def get(self, chatroom_id) -> Chatroom:
        """获取群聊缓存"""
        if group_info := self._get(chatroom_id):
            return group_info
        lock = self._locks.setdefault(chatroom_id, asyncio.Lock())
        async with lock:
            if not (group_info := self._get(chatroom_id)):   
                logger.warning(f"群聊{chatroom_id}缓存不存在，正在获取.")
                group_info = await self.update(chatroom_id)
            return group_info


    async def  get_member(self, wxid: str, chatroom_id: str) -> ChatroomMember | None:
        """由群聊id和和微信id获取用户信息"""
        group = await self.get(chatroom_id)
        return next((member for member in group.member_list if member.wxid == wxid), None)
    