# src/service/group_service.py
from .cache import FriendCache, ContactCache, ChatroomCache

class CacheManager:
    
    _instance = None
    
    def __init__(self):
        self.friend: FriendCache = FriendCache()
        self.chatroom: ChatroomCache = ChatroomCache()
        self.contact: ContactCache = ContactCache()
    
    
cache = CacheManager()

__all__ = ["cache"]