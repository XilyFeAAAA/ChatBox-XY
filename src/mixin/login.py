from src.utils import post_json, create_device_id, create_device_name, logger
from src.model import Friend
from .base import BaseMixIn
import sys
import qrcode
import asyncio


class LoginMixIn(BaseMixIn):

    
    async def login(self):
        if not await self.is_logged_in():
            if await self.get_cached_info():
                logger.debug("尝试唤醒登录")
                if uuid :=await self.revoke_login():
                    self.uuid = uuid
                    logger.success(f"唤醒登录成功,获取到登录uuid: {self.wxid}")
                else:
                    logger.error("唤醒登录失败,尝试二维码登录")
                    await self.qrcode_login()
            else:
                await self.qrcode_login()
        else:
            profile = await self.get_profile()
            self.nickname = profile.get("NickName", {}).get("string", "")
            self.alias = profile.get("Alias", "")
            self.phone = profile.get("BindMobile", {}).get("string", "")
        self.is_logged = True
        logger.info("设备登录成功")
        logger.info(f"登录账号信息: wxid: {self.wxid}  昵称: {self.nickname} 微信号: {self.alias}  手机号: {self.phone}")     
        
        
    async def get_cached_info(self):
        param = {
            "Wxid": self.wxid
        }
        resp = await post_json("/GetCachedInfo", body=param)
        return resp.get("Data") if resp.get("Success") else None
        
        
    
    async def revoke_login(self):
        param = {
            "Wxid": self.wxid
        }
        resp = await post_json("/AwakenLogin", body=param)
        if resp.get("Success"):
            return resp.get("Data", {}).get("QrCodeResponse", {}).get("Uuid", "") 
        else:
            return None
            
    async def qrcode_login(self):
        if not self.device_name:
            self.device_name = create_device_name()
        if not self.device_id:
            self.device_id = create_device_id
        param = {
            'DeviceName': self.device_name,
            'DeviceID': self.device_id
        }
        resp = await post_json("/GetQRCode", body=param)
        if resp.get("Success"):
            qr = qrcode.QRCode(
                        version=1,
                        error_correction=qrcode.constants.ERROR_CORRECT_L,
                        box_size=10,
                        border=4,
            )
            qr.add_data(f'http://weixin.qq.com/x/{resp.get("Data").get("Uuid")}')
            qr.make(fit=True)
            qr.print_ascii()
            self.uuid, url = resp.get("Data").get("Uuid"), resp.get("Data").get("QrUrl")
            logger.info(f"登录uuid: {self.uuid}, 二维码url: {url}")
        else:
            self.error_handler(resp)
        
        while True:
            stat, data = await self.check_login()
            if stat: break
            logger.info(f"等待登录中，过期倒计时：{data}")
            await asyncio.sleep(5)
        logger.debug(data)
        self.wxid = data.get("userName")
        self.nickname = data.get("NickName")
        self.alias = data.get("Alais")
        self.phone = data.get("Mobile")
        
    
    async def check_login(self):
        param = {
            "Uuid": self.uuid
        }
        resp = await post_json("/CheckUuid", body=param)
        if resp.get("Success"):
            if resp.get("Data").get("acctSectResp", ""):
                return True, resp.get("Data").get("acctSectResp")
            else:
                return False, resp.get("Data").get("expiredTime")
        else:
            self.error_handler(resp)
            
                       
    async def start_auto_heartbeat(self):
        param = {
            "Wxid": self.wxid
        }
        resp = await post_json("/AutoHeartbeatStart", body=param)
        if resp.get("Success"):
            logger.success("已开启自动心跳")
        else:
            logger.error(f"开启自动心跳失败: {resp}")
            sys.exit()
    
    
    async def stop_auto_heartbeat(self):
        param = {
            "Wxid": self.wxid
        }
        resp = await post_json("/AutoHeartbeatStop", body=param)
        if resp.get("Success"):
            logger.success("已关闭自动心跳")
        else:
            logger.error(f"关闭自动心跳失败: {resp}")
    
    
    
    async def status_auto_heartbeat(self):
        param = {
            "Wxid": self.wxid
        }
        resp = await post_json("/AutoHeartbeatStatus", body=param)
        if resp.get("Success"):
            return resp.get("Running")
        else:
            self.error_handler(resp)