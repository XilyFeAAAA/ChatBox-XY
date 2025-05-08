from src.model import MessageType, Chatroom, ChatroomMember, Friend, MessageSource
from src.manager import cache
from src.utils import logger
from src.bot import Bot
from xml.etree import ElementTree
import re
import time

bot = Bot.get_instance()

class Message:
    _type_registry: dict = {}

    def __init__(self,
                *, 
                data: dict,
                from_wxid: str,
                to_wxid: str, 
                msg_type: MessageType,
                content: str,
                create_time: int,
                msg_source: str,
                new_msg_id: int,
                msg_seq: int,
                chatroom: Chatroom | None = None,
                sender: Friend | ChatroomMember | None = None,
                source: MessageSource = MessageSource.OTHER):
        # 原始数据
        self.data = data
        # 发送人wxid
        self.from_wxid = from_wxid
        # 接收人wxid
        self.to_wxid = to_wxid
        # 消息类型
        self.msg_type = msg_type
        # 消息内容
        self.content = content
        # 发送时间
        self.create_time = create_time
        # 消息来源字段
        self.msg_source = msg_source
        # 消息id
        self.new_msg_id = new_msg_id
        # 消息序列化
        self.msg_seq = msg_seq
        # 群聊对象
        self.chatroom = chatroom
        # 私聊对象
        self.sender = sender
        # 聊天类型
        self.source = source


    @classmethod
    def register_type(cls, msg_type):
        def decorator(subclass):
            cls._type_registry[msg_type] = subclass
            return subclass
        return decorator


    @classmethod
    async def new(cls, data) -> "Message":
        # 处理通用信息
        from_wxid = data.get("FromUserName", {}).get("string")
        to_wxid = data.get("ToUserName", {}).get("string")
        msg_type = data.get("MsgType")
        content = data.get("Content", {}).get("string")
        create_time = data.get("CreateTime")
        msg_source = data.get("MsgSource")
        new_msg_id = data.get("NewMsgId")
        msg_seq = data.get("MsgSeq")
        # 过滤过期信息
        if time.time() - create_time >= 60 * 5:
            return None
        # 过滤自己发的消息
        if data["FromUserName"]["string"] == bot.wxid: return
        # 白名单过滤
        # 群聊 or 私聊判断
        if from_wxid.endswith("@chatroom"):
            if not bot.whitelist.is_chatroom_allowed(from_wxid): return
            source = MessageSource.CHATROOM
            chatroom = await cache.chatroom.get(from_wxid)
        else:
            if not bot.whitelist.is_user_allowed(from_wxid): return
            source = MessageSource.FRIEND
            sender = await cache.friend.get(from_wxid)
        # 根据消息类型分发
        if (subclass := cls._type_registry.get(msg_type)) is not None:
            cls = subclass(
                data=data,
                from_wxid=from_wxid,
                to_wxid=to_wxid,
                msg_type=msg_type,
                content=content,
                create_time=create_time,
                msg_source=msg_source,
                new_msg_id=new_msg_id,
                msg_seq=msg_seq,
                chatroom=chatroom if source == MessageSource.CHATROOM else None,
                sender=sender if source == MessageSource.FRIEND else None,
                source=source
            )
        else:
            logger.warning(f"未识别的消息类型:{msg_type}")
            return None
        return await cls.parse()
        

# 文字消息
@Message.register_type(MessageType.Text)
class TextMessage(Message):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.text: str = ""
        self.ats: list[ChatroomMember] = []
        self.at_me: bool = False
        

    async def parse(self) -> "TextMessage":
        if self.source == MessageSource.CHATROOM:
            # 分割群聊消息发送人
            sender_wxid, self.content = self.content.split(':\n')
            # 去掉at信息，获得纯文本
            self.text = re.sub(r'@[^\u2005]*\u2005', '', self.content) if '\u2005' in self.content else self.content
            # 获取发送人信息
            self.sender = await cache.chatroom.get_member(sender_wxid, self.chatroom.chatroom_id)
            # 获取at信息
            self.ats = await self.get_ats()
            self.at_me = any(at.wxid == bot.wxid for at in self.ats)
        elif self.source == MessageSource.FRIEND:
            self.text = self.content
        return self

    async def get_ats(self) -> list[ChatroomMember]:
        """群内at,如果设置了群内昵称则会显示群内昵称displayName,否则为微信名nickName"""
        root = ElementTree.fromstring(self.msg_source)
        ats = root.find("atuserlist").text if root.find("atuserlist") is not None else ""
        ats = ats.lstrip(",")
        ats = ats.split(",") if ats else []
        return [await cache.chatroom.get_member(at, self.from_wxid) for at in ats]


    def __repr__(self):
        return f"<TextMessage sender={self.sender} text={self.text}>"


@Message.register_type(MessageType.AppMsg)
class XmlMessage(TextMessage):
   
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.xml_root = None
        self.xml_type
    
    async def parse(self) -> "XmlMessage":
        await super().parse()
        try:
            self.xml_root = ElementTree.fromstring(self.content)
            self.xml_type = int(root.find("appmsg").find("type").text)
        except Exception as e:
            logger.error(f"解析xml消息失败: {e}")
            return

        if type == 57:
            await self.process_quote_message(message)
        elif type == 6:
            await self.process_file_message(message)
        elif type == 74:  # 文件消息，但还在上传，不用管
            pass

        else:
            logger.info("未知的xml消息类型: {}", message)

# 视频消息
@Message.register_type(MessageType.Video)
class VideoMessage(Message):
    def __init__(self, data):
        super().__init__(data)
        self.video_url = data.get("VideoUrl")
        self.thumb_url = data.get("ThumbUrl")

    def __repr__(self):
        return f"<VideoMessage sender={self.sender} video_url={self.video_url}>"