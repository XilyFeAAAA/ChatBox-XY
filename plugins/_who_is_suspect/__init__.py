from src.matcher import on_fullmatch, to_me, from_chatroom
from src.message import TextMessage
from src.utils import logger
from src.bot import Bot
from .game import GameSession


rules = [from_chatroom()]


@on_fullmatch(text="谁是卧底", rules=rules)
async def create_game(bot: Bot, message: TextMessage):
    chatroom_id = message.chatroom.chatroom_id
    if GameSession.new(chatroom_id, max_player_number=8, min_player_number=2):
        await bot.send_text(
            chatroom_id,
            "谁是卧底游戏开始！\n"
            "【游戏规则】\n"
            "1. 每位玩家会收到一个词语，只有一人拿到与其他人不同的“卧底词”。\n"
            "2. 每轮每位玩家依次用一句话描述自己拿到的词，但不能直接说出词语本身。\n"
            "3. 描述结束后，大家投票选出最可疑的人，被投票最多者淘汰。\n"
            "4. 如果卧底被淘汰，平民获胜；如果只剩两人且卧底未被淘汰，则卧底获胜。\n"
            "5. 指令：\n"
            "  - @我 加入游戏\n"
            "  - @我 开始游戏\n"
            "  - @我 投票 @某人\n"
            "请大家踊跃加入，达到最少人数后可开始游戏！"
        )


@on_fullmatch(text="加入游戏", rules=rules)
async def join_game(bot: Bot, message: TextMessage):
    chatroom_id = message.chatroom.chatroom_id
    if session := GameSession.get(chatroom_id):
        status, text = await session.join(message.sender)
        if status:
            await bot.send_text(chatroom_id, f"{message.sender.name}加入游戏,\n当前游戏人数{session.player_number}/{session.max_player_number}")
        else:
            await bot.send_text(chatroom_id, f"加入失败,{text}")


@on_fullmatch(text="开始游戏", rules=rules)
async def start_game(bot: Bot, message: TextMessage):
    chatroom_id = message.chatroom.chatroom_id
    if session := GameSession.get(chatroom_id):
        if session.player_number >= session.min_player_number:
            return await session.start()
        else:
            return await bot.send_text(chatroom_id, f"游戏不满{session.min_player_number}人")

@on_fullmatch(text="投票", rules=rules)
async def vote(bot: Bot, message: TextMessage):
    logger.debug("进入投票")
    chatroom_id = message.chatroom.chatroom_id
    if session := GameSession.get(chatroom_id):
        logger.debug(f"at人数{len(message.ats)}")
        at = next(member for member in message.ats if member.wxid != bot.wxid)
        if at is None:
            return await bot.send_text(chatroom_id, "格式错误", message.sender.wxid)
        await session.vote(message.sender.wxid, at.wxid)

@on_fullmatch(text="结束游戏", rules=rules)
async def vote(bot: Bot, message: TextMessage):
    chatroom_id = message.chatroom.chatroom_id
    GameSession.end(chatroom_id)
    return await bot.send_text(chatroom_id, f"游戏结束")