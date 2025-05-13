# 🤖 ChatBox-XY

ChatBox-XY 是一个基于 Python 的微信机器人框架，支持插件扩展、消息分发、白名单、消息队列等功能，适合二次开发和自定义微信自动化场景。

---

## 免责声明

- 本项目免费开源，仅供学习和技术研究使用，不得用于任何商业或非法行为。
- 作者不对本工具的安全性、完整性、可靠性、有效性、正确性或适用性做任何明示或暗示的保证，也不对本工具的使用或滥用造成的任何直接或间接的损失、责任、索赔、要求或诉讼承担任何责任。
- 使用者应遵守相关法律法规，尊重微信的版权和隐私，不得侵犯微信或其他第三方的合法权益。
- 使用本工具即表示已阅读并同意本免责声明。如有异议，请立即停止使用并删除所有相关文件。

---

## TODO
1. ProtocolMixIn 修复
2. 多账户管理
3. 多协议管理（多个 mixin 文件夹，协议相关全放 mixin 里面，然后最外层直接 from xxx import *）
4. 完善引用类型消息处理
5. 完善图片和语音消息，文件
6. 后台web

---

## ✨ 主要功能

- 支持多种消息类型（文本、图片、视频、XML、系统等）
- 插件化架构，自动发现与注册，功能可扩展
- 白名单管理，灵活控制机器人服务对象
- 消息队列，支持消息限流与异步处理
- 消息分发与规则匹配，支持优先级与阻断
- 协议服务本地化，兼容多平台
- 支持 LLM（大模型）上下文与摘要能力

---

## 📁 目录结构

```
.
├── main.py                # 项目入口，启动与主循环
├── config.json            # 主要配置文件
├── pyproject.toml         # 依赖与元信息
├── src/
│   ├── bot.py             # Bot 主体，生命周期与协议管理
│   ├── plugin.py          # 插件基类与注册机制
│   ├── message/           # 消息对象与解析
│   ├── model.py           # 数据结构与枚举
│   ├── config.py          # 配置加载
│   ├── error.py           # 错误定义
│   ├── matcher/           # 消息分发与规则
│   ├── manager/           # 缓存与管理器
│   ├── mixin/             # 多协议与功能混入
│   ├── llm/               # 大模型相关能力
│   ├── utils/             # 工具与通用组件
│   └── XYWechatPad.exe    # 微信协议本地服务
├── plugins/               # 插件目录（每个插件为一个子文件夹）
└── README.md              # 项目说明文档
```

---

## 🚀 安装与运行

### 环境要求

- Python >= 3.11
- Redis（用于缓存与消息队列）

### 安装依赖

```bash
pip install -r requirements.txt
# 或使用 pyproject.toml
pip install .
```

### 启动项目

```bash
python main.py
```

---

## ⚙️ 配置说明

编辑 `config.json` 进行个性化配置：

- `BASEURL`：协议服务地址
- `MESSAGE_QUEUE`：消息队列开关与发送间隔
- `WHITELIST`：白名单控制（可限制用户/群聊）
- `PROTOCOL_PATH`：协议服务可执行文件路径
- `PROTOCOL_PORT`：协议服务端口
- `REDIS_HOST/PORT/PASSWORD/DB`：Redis 连接信息

示例：

```json
{
    "BASEURL": "http://127.0.0.1:9000",
    "MESSAGE_QUEUE": {"enable": true, "interval": 1.0},
    "WHITELIST": {"enable": false, "users": [], "chatrooms": []},
    "PROTOCOL_PATH": "src/XYWechatPad.exe",
    "PROTOCOL_PORT": 9000,
    "PROTOCOL_MODE": "release",
    "REDIS_HOST": "127.0.0.1",
    "REDIS_PORT": 6379,
    "REDIS_PASSWORD": "",
    "REDIS_DB": 0
}
```

---

## 🧩 插件机制

- 所有插件放在 `plugins/` 目录下，每个插件为一个子文件夹，需实现插件类并继承 `PluginBase`。
- 插件自动加载，无需手动引入，支持异步处理。
- 插件需通过装饰器（如 `@PluginBase.on_message()`）注册消息处理函数，支持多种消息类型和规则匹配。
- 插件可定义元信息（作者、描述、版本等）。

**插件示例：echo**

`plugins/echo/main.py` 示例：

```python
from src.message import TextMessage
from src.bot import Bot
from src.plugin import PluginBase
from src.model import MessageSource
from src.utils import logger

class Echo(PluginBase):
    __description__ = "消息提示"
    __author__ = "xilyfe"
    __version__ = "1.0.0"

    @PluginBase.on_message()
    async def echo(self, bot: Bot, msg: TextMessage):
        if msg.source == MessageSource.FRIEND:
            source_ = '私聊'
            from_ = msg.sender.name
        else:
            source_ = '群聊'
            from_ = msg.chatroom.nickname
        logger.info(f"接受到{source_}{msg.from_wxid}消息,来自{from_},内容为{msg.text}")
```

---

## 🛠️ 插件开发指南

1. 在 `plugins/` 下新建文件夹（如 myplugin），并添加 `main.py`。
2. 在 `main.py` 中编写插件类，继承 `PluginBase`，并用装饰器注册消息处理函数。
3. 支持多种消息类型（TextMessage、XmlMessage、VideoMessage 等）。
4. 可通过 `msg.text`、`msg.sender`、`msg.chatroom` 获取消息内容和来源。

---

## 📨 消息类型

- `TextMessage`：文本消息，支持群聊 at、at_me 检测
- `XmlMessage`：公众号/文件/小程序/引用/转账等 xml 消息
- `VideoMessage`：视频消息
- 其他类型详见 `src/model.py` 和 `src/message/message.py`

---

## 🧠 LLM 能力

- 支持上下文管理、摘要、历史存储等大模型相关能力，详见 `src/llm/` 目录

---

## ❓ 常见问题 FAQ

1. **协议服务无法启动？**
   - 检查 `PROTOCOL_PATH` 路径和端口是否被占用。
2. **Redis 连接失败？**
   - 检查 Redis 服务是否启动，配置项是否正确。
3. **插件未生效？**
   - 确认插件目录结构正确，且未以 `_` 开头。
4. **消息收发异常？**
   - 检查消息队列和白名单配置。

---

## 📦 依赖列表

- aiohttp
- dacite
- fastapi
- loguru
- openai
- pillow
- qrcode
- uvicorn

详见 `pyproject.toml`。

---

## 💻 贡献与开发

欢迎提交 Issue 和 PR，建议插件开发遵循现有目录结构和注册机制。

---

如需更详细的开发文档或二次开发支持，请查阅源码注释或联系维护者。