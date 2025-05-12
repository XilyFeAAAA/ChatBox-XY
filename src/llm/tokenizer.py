from src.utils import logger
from . import config
import tiktoken

class Tokenizer:
    
    def __init__(self, llm_model: str) -> None:
        try:
            self.encoding = tiktoken.encoding_for_model(llm_model)
        except KeyError:
            logger.error(f"未找到模型：{llm_model}，使用 cl100k 编码")
            self.encoding = tiktoken.get_encoding("cl100k_base")
            
    def count_token_for_string(self, text: str):
        return len(self.encoding.encode(text))
    
    def count_token_for_message(self, message: dict):
        token_nums = 4
        for _, value in message.items():
            token_nums += self.count_token_for_string(value)
        return token_nums
    
    def count_token_for_message_list(self,  messages: list[dict]):
        token_nums = 0
        if messages:
            for message in messages:
                token_nums += self.count_token_for_message(message)
                
        
        