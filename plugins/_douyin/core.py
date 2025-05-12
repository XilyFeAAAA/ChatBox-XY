from src.utils import logger
from src.bot import Bot
from dataclasses import dataclass
from typing import Optional
import re
import aiohttp
import ssl

bot = Bot.get_instance()



@dataclass
class DouyinVideo:
    desc: str
    media_type: int
    aweme_list: Optional[dict] = None
    images: Optional[dict] = None



class Douyin:
    
    
    async def get_profile(self):
        pass
    

    async def get_videos(self, sec_user_id: str):
        """
        爬取指定抖音用户的所有视频，返回视频列表
        :param sec_user_id: 抖音用户的sec_user_id
        :return: 所有视频的列表
        """
        url = "http://121.41.2.180:9123/api/douyin/web/fetch_user_post_videos"
        max_cursor = 0
        count = 5
        all_videos = []
        has_more = True

        async with aiohttp.ClientSession() as session:
            params = {
                "sec_user_id": sec_user_id,
                "max_cursor": max_cursor,
                "count": count
            }
            try:
                async with session.get(url, params=params, timeout=15) as resp:
                    if resp.status != 200:
                        logger.error(f"请求失败，状态码: {resp.status}")
                    result = await resp.json()
                # 适配新返回格式
                data = result.get("data", {})                        
                has_more = bool(data.get("has_more", 0))
                videos = data.get("aweme_list", [])
                all_videos.extend([DouyinVideo(video) for video in videos])
                logger.debug(f"已获取{len(videos)}条，累计{len(all_videos)}条，has_more={has_more}, max_cursor={max_cursor}")
            except Exception as e:
                logger.error(f"获取抖音视频失败: {e}")
        return all_videos
    
    
    async def parse_video(self, video_url: str):
        """解析视频链接"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1'
            }

            # 获取重定向后的真实链接
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(video_url, allow_redirects=False) as response:
                    if response.status == 302:
                        video_url = response.headers.get('Location')

                # 获取页面内容
                async with session.get(video_url, headers=headers) as response:
                    if response.status != 200:
                        raise RuntimeError(f"获取页面失败，状态码：{response.status}")

                    html_content = await response.text()
                    if not html_content:
                        raise RuntimeError("页面内容为空")

                    # 合并后的正则表达式
                    pattern = re.compile(
                        r'"play_addr":\s*{\s*"uri":\s*"[^"]*",\s*"url_list":\s*\[([^\]]*)\]'
                    )
                    match = pattern.search(html_content)

                    if not match:
                        raise RuntimeError("未找到视频链接")

                    url_list_str = match.group(1)
                    urls = [url.strip().strip('"') for url in url_list_str.split(',')]

                    if not urls:
                        raise RuntimeError("视频链接列表为空")

                    # 解码并处理所有URL
                    decoded_urls = [url.strip().strip('"').encode().decode('unicode-escape').replace("playwm", "play") for url in urls]

                    # 优先选择aweme.snssdk.com域名的链接
                    snssdk_urls = [url for url in decoded_urls if 'aweme.snssdk.com' in url]
                    if not snssdk_urls:
                        raise RuntimeError("未找到有效的视频源链接")

                    video_url = snssdk_urls[0]

                    # 处理重定向，确保获取最终的视频地址
                    max_redirects = 3
                    redirect_count = 0

                    while redirect_count < max_redirects:
                        async with session.get(video_url, headers=headers, allow_redirects=False) as response:
                            if response.status == 302:
                                new_url = response.headers.get('Location')
                                if 'aweme.snssdk.com' in new_url:
                                    video_url = new_url
                                    redirect_count += 1
                                else:
                                    break
                            else:
                                break

                    if not video_url:
                        raise RuntimeError("无法获取有效的视频地址")

                    # 提取标题等信息
                    title_pattern = re.compile(r'"desc":\s*"([^"]+)"')
                    author_pattern = re.compile(r'"nickname":\s*"([^"]+)"')
                    cover_pattern = re.compile(r'"cover":\s*{\s*"url_list":\s*\[\s*"([^"]+)"\s*\]\s*}')

                    title_match = title_pattern.search(html_content)
                    author_match = author_pattern.search(html_content)
                    cover_match = cover_pattern.search(html_content)

                    return {
                        "url": video_url,
                        "title": title_match.group(1) if title_match else "",
                        "author": author_match.group(1) if author_match else "",
                        "cover": cover_match.group(1) if cover_match else ""
                    }

        except Exception as e:
            raise RuntimeError(f"解析过程发生错误：{str(e)}")
    
    
    async def send_card(self, from_wxid, video_info: dict):
        try:
            title = video_info.get("title", "")
            author = video_info.get("author", "")
            # 根据是否有作者信息组装标题
            display_title = f"{title[:30]} - {author[:10]}" if author else title[:40]
            if not display_title:
                display_title = "抖音视频"

            video_url = video_info.get('url', '')
            thumb_url=video_info.get("cover_url", "https://is1-ssl.mzstatic.com/image/thumb/Purple221/v4/7c/49/e1/7c49e1af-ce92-d1c4-9a93-0a316e47ba94/AppIcon_TikTok-0-0-1x_U007epad-0-1-0-0-85-220.png/512x512bb.jpg")
            description = f"抖音-{author}的作品"
            
            res = await bot.send_link(
                to_wxid=from_wxid,
                url=video_url,
                title=title,
                desc=description,
                thumb_url=thumb_url
            )
            logger.debug(f"发生卡片成功:{res}")
        except Exception as e:
            logger.error(f"Error in _send_video_card for group {from_wxid}", exc_info=True)
            logger.error(f"发送卡片消息失败: {str(e)}", exc_info=True)
            # 发送普通文本消息作为备选
            message = f"视频标题：{video_info.get('title', '未知')}\n视频链接：{video_info.get('url', '')}\n"
            await bot.send_text(from_wxid, message)