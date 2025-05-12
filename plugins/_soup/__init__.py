from src.matcher import on_fullmatch, on_message, to_me, from_chatroom
from src.message import TextMessage
from src.utils import logger
from src.bot import Bot
from .game import GameSession
import logging


rules = [to_me(), from_chatroom()]


# 开始游戏
@on_fullmatch(text="海龟汤", rules=rules, block=True)
async def start_game(bot: Bot, message: TextMessage):
    chatroom_id = message.chatroom.chatroom_id
    if session := GameSession.new(chatroom_id):
        logger.debug("发送")
        await bot.send_text(chatroom_id, f"""🐢 海龟汤游戏开始      
游戏目标：
玩家通过提问（仅限“是/否/无关”问题）逐步推理出谜题背后的完整故事。
机器人会直接回答“是”“否”或“无关”，不提供额外信息。
关键词指令：
【开始游戏】：随机抽取一道海龟汤谜题，开始新游戏。
【结束游戏】：立即终止当前游戏，并公布完整答案。
【切换题目】：放弃当前题目，重新抽取一道新谜题。
""")
        await bot.send_text(chatroom_id, f"海龟汤汤面：{session.question}")


# 问答
@on_message(rules=rules, priority=0)
async def ask(bot: Bot, message: TextMessage):
    chatroom_id = message.chatroom.chatroom_id
    if session := GameSession.get(chatroom_id):
        logging.info(f"用户{message.sender.name}发送:{message.text}")
        reply = session.ask_gpt(message.text)
        await bot.send_text(chatroom_id, reply, message.sender.wxid)


# 切换题目
@on_fullmatch(text="切换题目", rules=rules)
async def change(bot: Bot, message: TextMessage):
    chatroom_id = message.chatroom.chatroom_id
    if session := GameSession.get(chatroom_id):
        session.search_soup()
        await bot.send_text(chatroom_id, f"游戏已经切换, 汤面:{session.question}")


# 结束游戏
@on_fullmatch(text="结束游戏", rules=rules)
async def end_game(bot: Bot, message: TextMessage):
    chatroom_id = message.chatroom.chatroom_id
    if session := GameSession.end(chatroom_id):
        await bot.send_text(chatroom_id, f"游戏已结束, 汤底为：{session.answer}")

