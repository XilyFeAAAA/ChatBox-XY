from src.utils import logger
from . import config
from .tokenizer import Tokenizer
from dataclasses import dataclass, field
from typing_extensions import Literal, Optional
import uuid
import time


# MessageRole 中需要记录 Summary 避免被二次总结, 输出位 OpenAI 消息时转为 Assistant
MessageRole = Literal["user", "system", "assistant", "tool", "summary"]

@dataclass
class LLM_Message:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    role: MessageRole
    content: str
    is_summary: bool = False
    token_nums: Optional[int] = None
    original_message_ids: list[str] = field(default_factory=list)
    timestamp: int = field(default_factory=lambda: int(time.time()))
    # For tool calls
    tool_call_id: Optional[str] = None
    tool_call_name: Optional[str] = None
    
    def to_openai_message(self):
        """Convert LLM_Message to OpenAI's Message"""
        msg_dict = {
            "role": "assistant" if self.role == "summary" else self.role,
            "content": self.content
        }
        if self.tool_call_id and self.tool_call_name:
            msg_dict["tool_call_id"] = self.tool_call_id
        
        return msg_dict
    
    
class History_Store:
    
    def __init__(self, llm_model: str = config.CHAT_MODEL) -> None:
        self.messages: list[LLM_Message] = []
        self.tokenizer = Tokenizer(llm_model)
        
    def _count_token_nums(self, message_content: str) -> int:
        return self.tokenizer.count_token_for_string(message_content)
    
    def add_message(self, 
                    role: MessageRole,
                    content: str,
                    is_summary: bool = False,
                    original_message_ids: Optional[list[str]] = None,
                    tool_call_id: Optional[str] = None,
                    tool_call_name: Optional[str] = None) -> LLM_Message:
        token_nums = self._count_token_nums(content)
        message = LLM_Message(
            role=role,
            content=content,
            is_summary=is_summary,
            token_nums=token_nums,
            original_message_ids=original_message_ids or [],
            tool_call_id=tool_call_id,
            tool_call_name=tool_call_name
        )
        self.messages.append(message)
        return message
    
    
    def add_user_message(self, content: str) -> LLM_Message:
        return self.add_message(role="user", content=content)
    
    
    def add_system_message(self, content: str) -> LLM_Message:
        return self.add_message(role="system", content=content)
    
    
    def add_assistant_message(self, content: str) -> LLM_Message:
        return self.add_message(role="assistant", content=content)
    
    
    def add_tool_response_message(self, content: str, tool_call_id: str, tool_call_name: str) -> LLM_Message:
        return self.add_message(role="tool", content=content, tool_call_id=tool_call_id, tool_call_name=tool_call_name)
    
    
    def add_summary_message(self, content: str, summarized_message_ids: list[str]) -> LLM_Message:
        token_nums = self.tokenizer.count_token_for_string(content)
        summary = LLM_Message(
            role="summary",
            content=content,
            is_summary=True,
            token_nums=token_nums,
            original_message_ids=summarized_message_ids          
        )
        
        new_messages = []
        first_summarized_message_index = -1
        has_insert = False
        
        for i, message in enumerate(self.messages):
            if message.id in summarized_message_ids:
                first_summarized_message_index = i
                break
            
        if first_summarized_message_index == -1 and summarized_message_ids:
            logger.warning("未找到带总结的消息")
            
        for i, message in enumerate(self.messages):
            if message.id in summarized_message_ids:
                if first_summarized_message_index == i:
                    new_messages.append(summary)
                    has_insert = True
            else:
                new_messages.append(message)
        
        if not has_insert and summarized_message_ids:
            new_messages.append(summary)
            logger.warning("Summary插入在消息列表末尾")
        
        self.messages = new_messages
        logger.info(f"添加Summary成功, 耗费token: {token_nums}, 代替消息{len(summarized_message_ids)}条")
        return self.messages
        
    
    
    def get_history(self) -> list[LLM_Message]:
        return self.messages.copy()
    
    
    def get_messages_for_summary(self, protected_length: int) -> list[LLM_Message]:
        """返回待总结的消息列表"""
        candidates = []
        end_index = max(0, len(self.messages) - protected_length)
        
        for message in self.messages[:end_index]:
            if message.role != 'summary':
                candidates.append(message)
                
        return candidates
    
    
    def get_total_tokens(self) -> int:
        return self.tokenizer.count_token_for_message_list(self.messages)
    
    
    def clear(self) -> None:
        self.messages.clear()
        logger.info("[History_Store]历史消息已移除")