class Whitelist:
    def __init__(self):
        self._users = set()
        self._chatrooms = set()
        self._enabled = False
    
    def is_enabled(self):
        return self._enabled
    
    def enable(self):
        self._enabled = True
    
    def disable(self):
        self._enabled = False
    
    def add_user(self, user_id):
        self._users.add(user_id)
    
    def remove_user(self, user_id):
        self._users.discard(user_id)
    
    def add_chatroom(self, chatroom_id):
        self._chatrooms.add(chatroom_id)
    
    def remove_chatroom(self, chatroom_id):
        self._chatrooms.discard(chatroom_id)
    
    def is_user_allowed(self, user_id):
        return not self._enabled or user_id in self._users
    
    def is_chatroom_allowed(self, chatroom_id):
        return not self._enabled or chatroom_id in self._chatrooms