from src.model import ChatroomMember
from src.manager import cache
from src.bot import Bot
import os
import json
import random
import logging


bot = Bot.get_instance()

class Player:
    
    def __init__(self, member: ChatroomMember) -> None:
        self.member = member          # ChatroomMember对象
        self.role = None              # "卧底" 或 "平民"
        self.word = None              # 词语
        self.is_alive = True          # 是否存活
        self.has_vote = False
        self.vote_count = 0           # 本轮被投票数

    @property
    def wxid(self):
        return self.member.wxid
    

class GameSession:
    sessions = {}
    
    def __init__(self, chatroom_id: str, max_player_number, min_player_number) -> None:
        self.chatroom_id = chatroom_id
        self.max_player_number = max_player_number
        self.min_player_number = min_player_number
        self.players: list[Player] = []
        self.round: int = 1
    
    
    @classmethod
    def new(cls, chatroom_id: str, *, max_player_number: int, min_player_number: int):
        if chatroom_id in cls.sessions:
            return None
        session = cls(chatroom_id, max_player_number, min_player_number)
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
        
    
    async def join(self, user: ChatroomMember) -> bool:
        # 判断是否有好友
        if await cache.chatroom.get_member(user.wxid, self.chatroom_id) is None:
            return False
        self.players.append(Player(user))
        return True

    async def start(self):
        """
        1. 抽一个题目
        2. 随机抽一个卧底
        3. 每个人私聊发送身份牌
        4. 开始
        """
        data_path = os.path.join(os.path.dirname(__file__), 'data.jsonl')
        with open(data_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        item = json.loads(random.choice(lines))
        self.spy_word = item.get("spy")
        self.civilian_word = item.get("civilian")
        spy_player = random.choice(self.players)
        try:
            # 私聊发送身份
            for player in self.players:
                if player == spy_player:
                    player.word = self.spy_word
                    player.role = "卧底"
                else:
                    player.word = self.civilian_word
                    player.role = "平民"
                await bot.send_text(player.wxid, f"你的身份是{player.role},卡片是{player.word}。")
        except Exception as e:
            await bot.send_text(self.chatroom_id, f"发送身份牌时出错")
            raise e
    
    async def vote(self, from_wxid: str, vote_wxid: str):
        voter = next((p for p in self.players if p.wxid == from_wxid and p.is_alive), None)
        voted = next((p for p in self.players if p.wxid == vote_wxid and p.is_alive), None)
        if not voter or not voted:
            return await bot.send_text(self.chatroom_id, "无效的投票", [voter.member])
        if voter.has_vote:
            return await bot.send_text(self.chatroom_id, "你已经投过票了。", [voter.member])
        voter.has_vote = True
        voted.vote_count += 1
        await bot.send_text(self.chatroom_id, f"{voter.member.name} 投票给了 {voted.member.name}")
        
        if all(p.has_vote for p in self.players if p.is_alive):
            await self.end_vote_round()
        
    async def end_vote_round(self):
        # 统计票数，找出得票最多者
        max_votes = max(p.vote_count for p in self.players if p.is_alive)
        candidates = [p for p in self.players if p.is_alive and p.vote_count == max_votes]
        eliminated = random.choice(candidates)  # 平票随机淘汰
        eliminated.is_alive = False
        await bot.send_text(self.chatroom_id, f"本轮淘汰：{eliminated.member.name}，身份：{eliminated.role}")
        
        # 结算
        if eliminated.role == "卧底" or sum(1 for p in self.players if p.is_alive) == 2:
            return await self.reveal()
        
        # 重新回合信息
        for p in self.players:
            p.vote_count = 0
            p.has_vote = False
        self.round += 1
        await bot.send_text(self.chatroom_id, f"第{self.round}轮开始，请继续发言并投票。")
    
    async def reveal(self):
        msg = "游戏结束，身份如下：\n"
        for p in self.players:
            msg += f"{p.member.name}: {p.role}\n"
        msg += f"卧底词：{self.spy_word}，平民词：{self.civilian_word}"
        await bot.send_text(self.chatroom_id, msg)
        
        # 游戏结束，销毁session
        GameSession.end(self.chatroom_id)
        
        
    @property
    def player_number(self):
        return len(self.players)