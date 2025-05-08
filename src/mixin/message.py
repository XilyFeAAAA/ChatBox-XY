from src.utils.http import post_json
from .base import BaseMixIn


class MessageMixIn(BaseMixIn):
    

    # @BaseMixIn.require_login
    async def sync_message(self):
        param = {
            "Wxid": self.wxid,
            "Scene": 0,
            "Synckey": ""
        }
        resp = await post_json("/Sync", body=param)
        if resp.get("Success", False):
            return True, resp.get("Data")
        else:
            return False, resp.get("Message")
    
    async def send_text(self, to_wxid: str, content: str, at: str = "", type_: int = 1):
        """发送文本消息，type=1文本，at为@人wxid，多个用,隔开"""
        param = {
            "ToWxid": to_wxid,
            "Content": content,
            "At": at,
            "Type": type_,
            "Wxid": self.wxid
        }
        resp = await post_json("/SendTextMsg", body=param)
        if resp.get("Success"):
            return resp.get("Data")
        else:
            self.error_handler(resp)

    async def send_image(self, to_wxid: str, base64: str):
        """发送图片消息，base64为图片内容"""
        param = {
            "ToWxid": to_wxid,
            "Base64": base64,
            "Wxid": self.wxid
        }
        resp = await post_json("/SendImageMsg", body=param)
        if resp.get("Success"):
            return resp.get("Data")
        else:
            self.error_handler(resp)

    # async def send_voice(self, to_wxid: str, base64: str, type_: int, voice_time: int):
    #     """发送语音消息，type为音频类型，voice_time为时长(毫秒)"""
    #     param = {
    #         "ToWxid": to_wxid,
    #         "Base64": base64,
    #         "Type": type_,
    #         "VoiceTime": voice_time,
    #         "Wxid": self.wxid
    #     }
    #     resp = await post_json("/Msg/SendVoice", body=param)
    #     if resp.get("Success"):
    #         return resp.get("Data")
    #     else:
    #         self.error_handler(resp)

    # async def send_video(self, to_wxid: str, base64: str, image_base64: str, play_length: int):
    #     """发送视频消息，base64为视频内容，image_base64为封面，play_length为时长(秒)"""
    #     param = {
    #         "ToWxid": to_wxid,
    #         "Base64": base64,
    #         "ImageBase64": image_base64,
    #         "PlayLength": play_length,
    #         "Wxid": self.wxid
    #     }
    #     resp = await post_json("/Msg/SendVideo", body=param)
    #     if resp.get("Success"):
    #         return resp.get("Data")
    #     else:
    #         self.error_handler(resp)

    # async def share_card(self, to_wxid: str, card_wxid: str, card_nickname: str, card_alias: str):
    #     """分享名片"""
    #     param = {
    #         "ToWxid": to_wxid,
    #         "CardWxId": card_wxid,
    #         "CardNickName": card_nickname,
    #         "CardAlias": card_alias,
    #         "Wxid": self.wxid
    #     }
    #     resp = await post_json("/Msg/ShareCard", body=param)
    #     if resp.get("Success"):
    #         return resp.get("Data")
    #     else:
    #         self.error_handler(resp)

    async def send_link(self, to_wxid: str, title: str, desc: str, url: str, thumb_url: str):
        """发送分享链接消息"""
        param = {
            "ToWxid": to_wxid,
            "Title": title,
            "Desc": desc,
            "Url": url,
            "ThumbUrl": thumb_url,
            "Wxid": self.wxid
        }
        resp = await post_json("/SendShareLink", body=param)
        if resp.get("Success"):
            return resp.get("Data")
        else:
            self.error_handler(resp)

    async def revoke(self, client_msg_id: int, create_time: int, new_msg_id: int, to_wxid: str):
        """撤回消息"""
        param = {
            "ClientMsgId": client_msg_id,
            "CreateTime": create_time,
            "NewMsgId": new_msg_id,
            "ToWxid": to_wxid,
            "Wxid": self.wxid
        }
        resp = await post_json("/RevokeMsg", body=param)
        if resp.get("Success"):
            return resp.get("Data")
        else:
            self.error_handler(resp)