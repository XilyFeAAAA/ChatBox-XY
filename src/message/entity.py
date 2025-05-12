import xml.etree.ElementTree as ET
from typing import Optional, Dict, Any

class Quote:
    def __init__(self, root: ET.Element):
        self.valid = False
        try:
            appmsg = root.find("appmsg")
            self.title = appmsg.find("title").text if appmsg.find("title") is not None else None
            refermsg = appmsg.find("refermsg")
            self.msg_type = int(refermsg.find("type").text) if refermsg.find("type") is not None else None
            self.new_msg_id = refermsg.find("svrid").text if refermsg.find("svrid") is not None else None
            self.to_wxid = refermsg.find("fromusr").text if refermsg.find("fromusr") is not None else None
            self.from_wxid = refermsg.find("chatusr").text if refermsg.find("chatusr") is not None else None
            self.nickname = refermsg.find("displayname").text if refermsg.find("displayname") is not None else None
            self.msg_source = refermsg.find("msgsource").text if refermsg.find("msgsource") is not None else None
            self.createtime = refermsg.find("createtime").text if refermsg.find("createtime") is not None else None
            self.content = refermsg.find("content").text if refermsg.find("content") is not None else None

            # 递归解析嵌套引用
            if self.msg_type == 49 and self.content:
                try:
                    quote_root = ET.fromstring(self.content)
                    quote_appmsg = quote_root.find("appmsg")
                    self.nested = {
                        "title": quote_appmsg.find("title").text if quote_appmsg.find("title") is not None else None,
                        "des": quote_appmsg.find("des").text if quote_appmsg.find("des") is not None else None,
                        "action": quote_appmsg.find("action").text if quote_appmsg.find("action") is not None else None,
                        "type": int(quote_appmsg.find("type").text) if quote_appmsg.find("type") is not None else None,
                        "showtype": int(quote_appmsg.find("showtype").text) if quote_appmsg.find("showtype") is not None else None,
                        "soundtype": int(quote_appmsg.find("soundtype").text) if quote_appmsg.find("soundtype") is not None else None,
                        "url": quote_appmsg.find("url").text if quote_appmsg.find("url") is not None else None,
                        "lowurl": quote_appmsg.find("lowurl").text if quote_appmsg.find("lowurl") is not None else None,
                        "dataurl": quote_appmsg.find("dataurl").text if quote_appmsg.find("dataurl") is not None else None,
                        "lowdataurl": quote_appmsg.find("lowdataurl").text if quote_appmsg.find("lowdataurl") is not None else None,
                        "songlyric": quote_appmsg.find("songlyric").text if quote_appmsg.find("songlyric") is not None else None,
                        "appattach": {
                            "totallen": int(quote_appmsg.find("appattach").find("totallen").text) if quote_appmsg.find("appattach") is not None and quote_appmsg.find("appattach").find("totallen") is not None else None,
                            "attachid": quote_appmsg.find("appattach").find("attachid").text if quote_appmsg.find("appattach") is not None and quote_appmsg.find("appattach").find("attachid") is not None else None,
                            "emoticonmd5": quote_appmsg.find("appattach").find("emoticonmd5").text if quote_appmsg.find("appattach") is not None and quote_appmsg.find("appattach").find("emoticonmd5") is not None else None,
                            "fileext": quote_appmsg.find("appattach").find("fileext").text if quote_appmsg.find("appattach") is not None and quote_appmsg.find("appattach").find("fileext") is not None else None,
                            "cdnthumbaeskey": quote_appmsg.find("appattach").find("cdnthumbaeskey").text if quote_appmsg.find("appattach") is not None and quote_appmsg.find("appattach").find("cdnthumbaeskey") is not None else None,
                            "aeskey": quote_appmsg.find("appattach").find("aeskey").text if quote_appmsg.find("appattach") is not None and quote_appmsg.find("appattach").find("aeskey") is not None else None,
                        },
                        "extinfo": quote_appmsg.find("extinfo").text if quote_appmsg.find("extinfo") is not None else None,
                        "sourceusername": quote_appmsg.find("sourceusername").text if quote_appmsg.find("sourceusername") is not None else None,
                        "sourcedisplayname": quote_appmsg.find("sourcedisplayname").text if quote_appmsg.find("sourcedisplayname") is not None else None,
                        "thumburl": quote_appmsg.find("thumburl").text if quote_appmsg.find("thumburl") is not None else None,
                        "md5": quote_appmsg.find("md5").text if quote_appmsg.find("md5") is not None else None,
                        "statextstr": quote_appmsg.find("statextstr").text if quote_appmsg.find("statextstr") is not None else None,
                        "directshare": int(quote_appmsg.find("directshare").text) if quote_appmsg.find("directshare") is not None else None,
                    }
                except Exception as e:
                    self.nested = {"error": str(e)}
            else:
                self.nested = None
            self.valid = True
        except Exception as e:
            self.error = str(e)

class File:
    def __init__(self, xml_str: str):
        self.valid = False
        try:
            root = ET.fromstring(xml_str)
            appmsg = root.find("appmsg")
            self.filename = appmsg.find("title").text if appmsg.find("title") is not None else None
            appattach = appmsg.find("appattach")
            self.attach_id = appattach.find("attachid").text if appattach is not None and appattach.find("attachid") is not None else None
            self.file_ext = appattach.find("fileext").text if appattach is not None and appattach.find("fileext") is not None else None
            self.totallen = int(appattach.find("totallen").text) if appattach is not None and appattach.find("totallen") is not None else None
            self.valid = True
        except Exception as e:
            self.error = str(e) 