from src.utils.http import post_json
from .base import BaseMixIn


class ToolMixIn(BaseMixIn):
    
    async def set_step(self, count: int) -> bool:
        param = {"Wxid": self.wxid, "StepCount": count}
        resp = await post_json('/SetStep', body=param)
        if resp.get("Success"):
            return True
        else:
            self.error_handler(resp)