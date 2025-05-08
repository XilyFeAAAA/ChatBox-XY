from openai import OpenAI
import os
import json
import random
import logging

model = ""
base_url = "https://api.deepseek.com"


class GameSession:
    # 全局存储所有群聊的session
    sessions = {}

    def __init__(self):
        self.question = ""
        self.answer = ""
        self.client = OpenAI(
            # api_key="xai-hR0PuvhxqYmyKSCgpQbCaoPm7pWKaN4Nvr7mhbYcl5gg7jow9qcsv7vehR730W3DFcJswMEQgOjgCJjp",
            api_key="sk-IOngWCiVG5lPcgZU5zx2YTtg9BB6YAXqYsEFfjDhdJUz3TZt",
            # base_url="https://api.x.ai/v1",
            base_url="https://api.chatanywhere.tech/v1"
        )
        self.search_soup()
    

    @classmethod
    def new(cls, chatroom_id: str):
        if chatroom_id in cls.sessions:
            return None
        session = cls()
        cls.sessions[chatroom_id] = session
        logging.info(f"创建新的Session{chatroom_id}")
        return session

    @classmethod
    def end(cls, chatroom_id):
        if chatroom_id not in cls.sessions:
            return None
        session = cls.sessions.pop(chatroom_id)
        return session


    @classmethod
    def get(cls, chatroom_id):
        return cls.sessions.get(chatroom_id, None)


    def ask_gpt(self, guess):
        self.history.append({"role": "user", "content": guess })
        completion = self.client.chat.completions.create(
            model="deepseek-v3",
            messages=self.history
        )
        reply = completion.choices[0].message.content
        self.history.append({"role": "assistant", "content": reply})
        return reply
    
    
    def search_soup(self):
        # 读取题库文件路径
        data_path = os.path.join(os.path.dirname(__file__), 'data.jsonl')
        with open(data_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        item = json.loads(random.choice(lines))
        self.question = item.get('soup_surface') or item.get('question')
        self.answer = item.get('soup_bottom') or item.get('answer')
        self.history = [{
            "role": "system",
            "content": f"""
                你是一个聪明的“海龟汤”游戏助手。
                你收到一个固定的谜面（汤面）和谜底（真相），玩家通过提问来猜测真相。你的任务如下：
                【游戏规则】：
                1. 用户会根据谜面提出各种问题，你必须根据“汤底”（真相）判断他们的问题是否帮助他们接近真相。
                2. 你只能回复以下三种之一：  
                - “是”：如果用户的问题内容在逻辑上与汤底相符，且对猜出真相有帮助。  
                - “不是”：如果用户的问题内容与汤底矛盾，或方向错误。  
                - “无关”：如果用户的问题与汤底没有关系或太模糊，无法判断。

                【特殊规则】：
                - 如果你判断用户的猜测**已经非常接近真实的汤底**，请停止是/不是的回答，直接告诉他们完整的汤底。
                - “非常接近”指的是：用户猜测中已经包含汤底的核心情节或关键设定，哪怕语言有偏差，也算接近。
                - 不要提前暴露真相或进行引导。除非用户猜得足够接近。

                【你将使用的谜题如下】：
                【汤面】：{self.question}。
                【汤底】：{self.answer}

                请保持冷静理性，只使用“是 / 不是 / 无关”三个词中的一个来答复用户，除非他们的回答已经非常接近真相，那时请完整说出汤底，不要保留。"""
        }]
        
    
    
__all__ = ["Soup"]