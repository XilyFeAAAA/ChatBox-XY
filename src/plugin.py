from src.model import MessageType
from src.utils import call_func
from typing_extensions import TYPE_CHECKING
import abc
import json
import inspect


class PluginBase(abc.ABC):
    """
    Base class for all plugins to interact with chatbox
    """
    
    # MetaData
    __description__: str = ""
    __author__: str = ""
    __version__: str = "1.0.0"
        
    
    def __init__(self) -> None:
        super().__init__()
        self.matchers = {}
        self._register_matchers()
        
    async def async_init(self):
        """
        初始化插件的异步操作
        """
        return
        
    
    def get_system_prompt(self) -> str:
        """
        获取系统提示词
        """
        return ""
    
    
    def get_summarize_prompt(self) -> str:
        """
        获取总结提示词
        """
        return ""
    
    
    def define_tools(self) -> list[dict]:
        """
        example:
        [{
            "type": "function",
            "function": {
                "name": "roll_dice",
                "description": "掷一个或多个COC规则的骰子。例如 d100, 2d6, 奖励骰, 惩罚骰。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "dice_type": {
                            "type": "string",
                            "description": "骰子类型，如 'd100', 'd6', 'd10', 'd4', 'd8', 'd20'等。"
                        },
                        "num_dice": {
                            "type": "integer",
                            "description": "要掷的骰子数量，默认为1。",
                            "default": 1
                        },
                        "bonus_dice": {
                            "type": "integer",
                            "description": "奖励骰的数量 (0, 1, or 2)。奖励骰会多掷这些数量的十位骰，并取结果中较好的一个十位。",
                            "default": 0
                        },
                        "penalty_dice": {
                            "type": "integer",
                            "description": "惩罚骰的数量 (0, 1, or 2)。惩罚骰会多掷这些数量的十位骰，并取结果中较差的一个十位。",
                            "default": 0
                        },
                        "reason": {
                            "type": "string",
                            "description": "掷骰的原因或对应的技能/属性，例如 '侦查检定', '图书馆使用', '伤害骰'。"
                        }
                    },
                    "required": ["dice_type", "reason"]
                }
            }
        }]
        """
        return []
    
    
    async def handle_tool_call(self, tool_call: dict) -> str:
        """
        Handle a single tool call from LLM
        example: 
        {
            "id": "call_abc123xyz",
            "type": "function",
            "function": {
                "name": "get_current_weather",
                "arguments": "{\"location\": \"Boston, MA\"}"
        }
        """
        tool_id = tool_call.get("id", "unknow_tool_id")
        func_name = tool_call.get("function", {}).get("name")
        func_args_json = tool_call.get("function", {}).get("arguments")
        try:
            func_args = json.loads(func_args_json)
        except json.JSONDecodeError:
            raise Exception(f"Invalid JSON arguments for tool '{func_name}': {func_args_json}")

        if hasattr(self, func_name):
            try:
                func = getattr(self, func_name)
                result = call_func(func, **func_args)
                if not isinstance(result, str):
                    raise Exception("Warning: Tool {func_name} did not return a string. ")
                return result
            except TypeError as e:
                raise Exception(f"Argument mismatch for tool '{func_name}': {e}")
            except Exception as e:
                raise Exception(f"Error executing tool '{func_name}': {str(e)}")
        else:
            raise Exception(f"Tool function '{func_name}' not implemented in plugin.")
        
    
    @staticmethod
    def on_message(**kwargs):
        kwargs.setdefault("type", MessageType.Text)
        def decorator(func):
            if not hasattr(func, '_event_handlers'):
                func._event_handlers = []
                
            func._event_handlers.append(kwargs)
            return func
        return decorator
    
    @staticmethod
    def on_startswith(
        text: str,
        rules: list["Rule"] = [],
        ignorecase: bool = False,
        **kwargs
    ):
        kwargs.setdefault("type", MessageType.Text)
        def decorator(func):
            from src.matcher.rule import startswith
            if not hasattr(func, '_event_handlers'):
                func._event_handlers = []
            
            kwargs["rules"] = [startswith(text, ignorecase)] + rules
            func._event_handlers.append(kwargs)
            return func
        return decorator
    
    @staticmethod
    def on_endswith(
        text: str,
        rules: list["Rule"] = [],
        ignorecase: bool = False,
        **kwargs
    ):
        kwargs.setdefault("type", MessageType.Text)
        def decorator(func):
            from src.matcher.rule import endswith
            if not hasattr(func, '_event_handlers'):
                func._event_handlers = []
            
            kwargs["rules"] = [endswith(text, ignorecase)] + rules
            func._event_handlers.append(kwargs)
            return func
        return decorator
    
    @staticmethod
    def on_fullmatch(
        text: str,
        rules: list["Rule"] = [],
        ignorecase: bool = False,
        **kwargs
    ):
        kwargs.setdefault("type", MessageType.Text)
        def decorator(func):
            from src.matcher.rule import fullmatch
            if not hasattr(func, '_event_handlers'):
                func._event_handlers = []
            
            kwargs["rules"] = [fullmatch(text, ignorecase)] + rules
            func._event_handlers.append(kwargs)
            return func
        return decorator
    
    @staticmethod
    def on_keyword(
        keywords: set[str],
        rules: list["Rule"] = [],
        **kwargs
    ):     
        kwargs.setdefault("type", MessageType.Text)
        def decorator(func):
            from src.matcher.rule import keyword
            if not hasattr(func, '_event_handlers'):
                func._event_handlers = []
       
            kwargs["rules"] = [keyword(keywords)] + rules
            func._event_handlers.append(kwargs)
            return func
        return decorator
    
    
    @staticmethod
    def on_regex(
        patterns: list[str],
        rules: list["Rule"] = [],
        flags: int = 0,
        **kwargs
    ):
        kwargs.setdefault("type", MessageType.Text)
        def decorator(func):
            from src.matcher.rule import regex
            if not hasattr(func, '_event_handlers'):
                func._event_handlers = []
            
            kwargs["rules"] = [regex(patterns, flags)] + rules
            func._event_handlers.append(kwargs)
            return func
        return decorator
    
    
    def _register_matchers(self):
        """
        注册所有用on装饰器装饰的方法到matcher系统
        """
        from src.matcher.matcher import Matcher
        for func_name, func in inspect.getmembers(self.__class__, predicate=inspect.isfunction):
            if hasattr(func, '_event_handlers'):
                for kwargs in func._event_handlers:
                    # 将实例方法绑定到matcher系统
                    bound_func = getattr(self, func_name)
                    func.matcher = Matcher.new(bound_func, **kwargs)