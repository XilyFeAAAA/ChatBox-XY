import json



class Config(dict):
    def __init__(self, d=None):
        super().__init__()
        if d is None:
            d = {}
        for k, v in d.items():
            self[k] = v

    def __getitem__(self, key):
        return super().__getitem__(key)

    def __setitem__(self, key, value):
        return super().__setitem__(key, value)

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError as e:
            return default
        except Exception as e:
            raise e
            
    def set(self, key, value):
        try:
            self[key] = value
        except Exception as e:
            raise e


def load_config():
    global config
    # 修改配置文件路径，指向项目根目录
    config_str = read_file("./config.json")
    # 将json字符串反序列化为dict类型
    config = Config(json.loads(config_str))



def save_config():
    global config
    config_path = "./config.json"
    try:
        config_dict = dict(config)  # 将Config对象转换为普通字典
        # 创建一个按键排序的有序字典
        sorted_config = {key: config_dict[key] for key in sorted(config_dict.keys())}
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(sorted_config, f, indent=4, ensure_ascii=False)
            print("[Config] Configuration saved.")
    except Exception as e:
        print(f"[Config] Save configuration error: {e}")




def read_file(path):
    with open(path, mode="r", encoding="utf-8") as f:
        return f.read()


def conf():
    return config


config = Config()
load_config()


