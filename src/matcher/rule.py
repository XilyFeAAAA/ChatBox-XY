from src.message import Message, TextMessage
from src.model import MessageSource
from typing_extensions import override
import abc
import re


class Rule(abc.ABC):

    def __str__(self):
        return self.__class__.__name__

    @abc.abstractmethod
    def check():
        raise NotImplementedError



class keyword(Rule):
    
    def __init__(self, keywords: list[str]):
        self.keywords = keywords
    
    @override
    def check(self, msg: TextMessage):
         return any(keyword in msg.text for keyword in self.keywords)


class regex(Rule):
    
    def __init__(self, patterns: list[str], flag: int) -> None:
        self.patterns = patterns
        self.flag = flag
        
    @override
    def check(self, msg: TextMessage):
        for pattern in self.patterns:
            if re.search(pattern, msg.text, self.flag):
                return True
        return False



class command(Rule):
    
    def __init__(self, cmd: str):
        self.cmd = cmd
        
    @override
    def check(self, msg: TextMessage):
        return False


class startswith(Rule):
    
    def __init__(self,text: str, ignorecase: bool):
        self.text = text
        self.ignorecase = ignorecase
        
    @override
    def check(self, msg: TextMessage):
        if self.ignorecase:
            return msg.text.lower().startswith(self.text.lower())
        else:
            return msg.text.startswith(self.text)


class endswith(Rule):
    
    def __init__(self,text: str, ignorecase: bool):
        self.text = text
        self.ignorecase = ignorecase
        
    @override
    def check(self, msg: TextMessage):
        if self.ignorecase:
            return msg.text.lower().startswith(self.text.lower())
        else:
            return msg.text.endswith(self.text)



class fullmatch(Rule):
    
    def __init__(self,text: str, ignorecase: bool):
        self.text = text
        self.ignorecase = ignorecase
        
    @override
    def check(self, msg: TextMessage):
        if self.ignorecase:
            return msg.text.lower() == self.text.lower()
        else:
            return msg.text == self.text


class to_me(Rule):
    
    @override
    def check(self, msg: TextMessage):
        return msg.at_me
    
    
class from_chatroom(Rule):
    
    @override
    def check(self,  msg: TextMessage):
        return msg.source == MessageSource.CHATROOM
    
class from_friend(Rule):
    
    @override
    def check(self, msg: TextMessage):
        return msg.source == MessageSource.FRIEND
    

