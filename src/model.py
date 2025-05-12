from enum import Enum
from typing import Optional
from dataclasses import dataclass, field
from dacite import from_dict
import time


class TypeName(str, Enum):
    Test = "Test"
    AddMsg = "AddMsg"
    ModContacts = "ModContacts"
    DelContacts = "DelContacts"
    Offline = "Offline"


class MessageSource(str, Enum):
    CHATROOM = "chatroom"
    FRIEND = "friend"
    OTHER = "other"


class MessageType(int, Enum):
    UNKNOWN = 0
    Text = 1
    Image = 3
    Voice = 34
    FriendAdd = 37
    NameCard = 42
    Video = 43
    Emoji = 47
    Location = 48
    AppMsg = 49 #  xml消息：公众号/文件/小程序/引用/转账/红包/视频号/群聊邀请
    Sync = 51 # 状态同步
    GroupOp = 10000 # 被踢出群聊/更换群主/修改群名称
    SystemMsg = 10002 # 撤回/拍一拍/成员被移出群聊/解散群聊/群公告/群待办
    

class CacheType(str, Enum):
    FRIEND = "friend"
    CHATROOM = "chatroom"
    CONTACT = "contact"
    
    
class XmlType(int, Enum):
    QUOTE = 57
    FILE = 6
    UPLOAD = 74

    
@dataclass
class ChatroomMember:
    """包含联系人和群成员的属性"""
    wxid: Optional[str] = None
    nickname: Optional[str] = None
    """微信昵称"""
    invite_wxid: Optional[str] = None
    displayname: Optional[str] = None
    """群名称"""
    big_image: Optional[str] = None
    small_image: Optional[str] = None
    
    @property
    def name(self) -> str:
        return self.displayname or self.nickname or self.wxid or "未知群聊成员" 
    
    
@dataclass
class Friend:
    wxid: Optional[str] = None
    nickname: Optional[str] = None
    avatar: Optional[str] = None
    remark: Optional[str] = None
    alias: Optional[str] = None
    
    @property
    def name(self) -> str:
        return self.nickname or self.wxid or "未知好友"


@dataclass
class Chatroom:
    chatroom_id: Optional[str] = None
    nickname: Optional[str] = None
    remark: Optional[str] = None
    chatroom_owner: Optional[str] = None
    small_image: Optional[str] = None
    member_list: list[ChatroomMember] = field(default_factory=list)
    
    @property
    def name(self) -> str:
        return self.nickname or self.chatroom_id or "未知群聊"

@dataclass
class Contact:
    """联系人列表数据"""
    friends: list[str] = field(default_factory=list)
    """好友列表"""
    chatrooms: list[str] = field(default_factory=list)
    """群聊列表"""
    ghs: list[str] = field(default_factory=list)
    """公众号列表"""    




@dataclass
class CachedData:
    
    data: Chatroom | Friend
    timestamp: float
    
    @classmethod
    def new(cls, raw_data: dict, cache_type: CacheType) -> "CachedData":
        
        if cache_type == CacheType.CHATROOM:
            data = from_dict(data_class=Chatroom, data=raw_data)
        elif cache_type == CacheType.FRIEND:
            data = from_dict(data_class=Friend, data=raw_data)
        elif cache_type == CacheType.CONTACT:
            data = from_dict(data_class=Contact, data=raw_data)
        else:
            raise RuntimeError(f"未识别的Cache类型:{cache_type}")
        return cls(data=data, timestamp=time.time())