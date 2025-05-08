from src.utils.http import post_json
from .base import BaseMixIn


class ChatroomMixIn(BaseMixIn):
    
    async def get_chatroom_info(self, chatroom_id: str):
        """获取群详情(不带公告内容)"""
        param = {
            "Chatroom": chatroom_id,
            "Wxid": self.wxid
        }
        resp = await post_json("/GetChatroomInfoNoAnnounce", body=param)
        return resp.get("Data") if resp.get("Success") else None

    # async def get_chatroom_info_detail(self, qid: str):
    #     """获取群信息(带公告内容)"""
    #     param = {
    #         "QID": qid,
    #         "Wxid": self.wxid
    #     }
    #     resp = await post_json("/Group/GetChatRoomInfoDetail", body=param)
    #     if resp.get("Success"):
    #         return resp.get("Data")
    #     else:
    #         self.error_handler(resp)

    async def get_chatroom_member(self, chatroom_id: str):
        """获取群成员"""
        param = {
            "Chatroom": chatroom_id,
            "Wxid": self.wxid
        }
        resp = await post_json("/GetChatroomMemberDetail", body=param)
        return resp.get("Data", {}).get("NewChatroomData", {}).get("ChatRoomMember", []) if resp.get("Success") else []
    

    # async def create_chatroom(self, to_wxids: str):
    #     """创建群聊"""
    #     param = {
    #         "ToWxids": to_wxids,
    #         "Wxid": self.wxid
    #     }
    #     resp = await post_json("/Group/CreateChatRoom", body=param)
    #     if resp.get("Success"):
    #         return resp.get("Data")
    #     else:
    #         self.error_handler(resp)

    # async def add_chatroom_member(self, chatroom_name: str, to_wxids: str):
    #     """增加群成员(40人以内)"""
    #     param = {
    #         "ChatRoomName": chatroom_name,
    #         "InviteWxids": to_wxids,
    #         "Wxid": self.wxid
    #     }
    #     resp = await post_json("/AddChatroomMember", body=param)
    #     if resp.get("Success"):
    #         return resp.get("Data")
    #     else:
    #         self.error_handler(resp)

    # async def del_chatroom_member(self, chatroom_name: str, to_wxids: str):
    #     """删除群成员"""
    #     param = {
    #         "ChatRoomName": chatroom_name,
    #         "ToWxids": to_wxids,
    #         "Wxid": self.wxid
    #     }
    #     resp = await post_json("/Group/DelChatRoomMember", body=param)
    #     if resp.get("Success"):
    #         return resp.get("Data")
    #     else:
    #         self.error_handler(resp)

    # async def set_chatroom_announcement(self, qid: str, content: str):
    #     """设置群公告"""
    #     param = {
    #         "QID": qid,
    #         "Content": content,
    #         "Wxid": self.wxid
    #     }
    #     resp = await post_json("/Group/SetChatRoomAnnouncement", body=param)
    #     if resp.get("Success"):
    #         return resp.get("Data")
    #     else:
    #         self.error_handler(resp)

    # async def set_chatroom_name(self, qid: str, content: str):
    #     """设置群名称"""
    #     param = {
    #         "QID": qid,
    #         "Content": content,
    #         "Wxid": self.wxid
    #     }
    #     resp = await post_json("/Group/SetChatRoomName", body=param)
    #     if resp.get("Success"):
    #         return resp.get("Data")
    #     else:
    #         self.error_handler(resp)

    # async def set_nickname(self, qid: str, nickname: str):
    #     """设置自己所在群的昵称"""
    #     param = {
    #         "QID": qid,
    #         "Nickname": nickname,
    #         "Wxid": self.wxid
    #     }
    #     resp = await post_json("/Group/SetNickname", body=param)
    #     if resp.get("Success"):
    #         return resp.get("Data")
    #     else:
    #         self.error_handler(resp)