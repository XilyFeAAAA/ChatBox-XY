from src.message import Message
from src.model import MessageType
from src.utils import logger
from .rule import Rule
from datetime import datetime


matchers: dict[int, list["Matcher"]] = {}

class Matcher:
    
    def __init__(
        self,
        type,
        rules,
        handler,
        priority: int,
        block: bool,
        temp: bool,
        expire_time: datetime = None,
        extra_args: dict = None
    ):
        self.type = type
        self.rules = rules
        self.handler = handler
        self.priority = priority
        self.block = block
        self.temp = temp
        self.expire_time = expire_time
        self.extra_args = extra_args or {}
    

    @classmethod
    def new(
        cls,
        handler: callable,
        type: MessageType = MessageType.Text,
        rules: list[Rule] = [],
        priority: int = 1,
        block: bool = False,
        temp: bool = False,
        expire_time: datetime = None,
        extra_args: dict = None,
    ):
        """
        创建新的Matcher对象并注册到全局matchers字典。
        :param type: 响应器类型
        :param rules: 匹配规则列表
        :param handlers: 事件处理函数列表
        :param priority: 优先级
        :param block: 是否阻止事件传播
        :param temp: 是否为临时响应器
        :param expire_time: 过期时间
        :param extra_args: 传递给处理函数的额外参数
        :return: Matcher实例
        """
        matcher = cls(type, rules, handler, priority, block, temp, expire_time, extra_args)
        if priority not in matchers:
            matchers[priority] = [matcher]
        else:
            matchers[priority].append(matcher)
        return matcher
    
    
    @staticmethod
    def destory(matcher: "Matcher"):
        if matcher.priority in matchers:
            matchers[matcher.priority].remove(matcher)
    
    def __repr__(self):
        return (
            f"<Matcher handler={self.handler.__name__} "
            f"type={self.type} "
            f"rules={[str(r) for r in self.rules]} "
            f"permissions={[str(p) for p in self.permissions]} "
            f"priority={self.priority} "
            f"block={self.block} "
            f"temp={self.temp} "
            f"expire_time={self.expire_time}>"
        )

async def check_and_run_matcher(matcher: Matcher, msg: Message) -> bool:
    # 类型检查
    if matcher.type != msg.msg_type:
        return False
    # 过期检查
    if matcher.expire_time and datetime.now() > matcher.expire_time:
        Matcher.destory(matcher)
        return False
    # 规则检查
    for rule in matcher.rules:
        if not rule.check(msg):
            return False
    # 运行 matcher
    await matcher.handler(msg, **matcher.extra_args)
    # 一次性检查
    if matcher.temp:
        Matcher.destory(matcher)
    return True


async def handle_message(msg: dict):
    if msg := await Message.new(msg):
        for priority in sorted(matchers.keys(), reverse=True):
            for matcher in matchers[priority]:
                if await check_and_run_matcher(matcher, msg) and matcher.block:
                    return
            
            
