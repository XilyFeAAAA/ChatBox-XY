from src.error import *

class BaseMixIn:
    
    
    @staticmethod
    def error_handler(json_resp):
        code = json_resp.get("Code")
        if code == -1:  # 参数错误
            raise ValueError(json_resp.get("Message"))
        elif code == -2:  # 其他错误
            raise Exception(json_resp.get("Message"))
        elif code == -3:  # 序列化错误
            raise MarshallingError(json_resp.get("Message"))
        elif code == -4:  # 反序列化错误
            raise UnmarshallingError(json_resp.get("Message"))
        elif code == -5:  # MMTLS初始化错误
            raise MMTLSError(json_resp.get("Message"))
        elif code == -6:  # 收到的数据包长度错误
            raise PacketError(json_resp.get("Message"))
        elif code == -7:  # 已退出登录
            raise UserLoggedOut("Already logged out")
        elif code == -8:  # 链接过期
            raise Exception(json_resp.get("Message"))
        elif code == -9:  # 解析数据包错误
            raise ParsePacketError(json_resp.get("Message"))
        elif code == -10:  # 数据库错误
            raise DatabaseError(json_resp.get("Message"))
        elif code == -11:  # 登陆异常
            raise UserLoggedOut(json_resp.get("Message"))
        elif code == -12:  # 操作过于频繁
            raise Exception(json_resp.get("Message"))
        elif code == -13:  # 上传失败
            raise Exception(json_resp.get("Message"))