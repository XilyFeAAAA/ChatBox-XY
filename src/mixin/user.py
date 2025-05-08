from src.utils.http import post_json
from .base import BaseMixIn


class UserMixIn(BaseMixIn):
    
    
    async def get_profile(self) -> dict:
        param = {
             "Wxid": self.wxid
        }
        resp = await post_json(f'/GetProfile', body=param)        
        if resp.get("Success"):
            return resp.get("Data").get("userInfo")
        else:
            self.error_handler(resp)
