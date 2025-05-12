from src.config import conf
from loguru import logger
from urllib.parse import urlencode
import sys
import aiohttp
import asyncio

async def post_json(route, *, body={}, query={}, headers={}) -> dict:
    url = conf().get("BASEURL") + route
    if query:
        url += '?' + urlencode(query)
    try:
        async with aiohttp.ClientSession() as session:
            response = await session.post(url, headers=headers, json=body)
            return await response.json()
    except Exception as e:
        logger.error(f"http请求失败, 地址为{url}, 错误提示{e}")
        raise e


async def get_json(route, *, query={}, headers={}):
    url = conf().get("BASEURL") + route
    if query:
        url += '?' + urlencode(query)
    try:
        async with aiohttp.ClientSession() as session:
            response = await session.get(url, headers=headers)
        return response
    except Exception as e:
        logger.error(f"http请求失败, 地址为{url}, 错误提示{e}")
        raise e