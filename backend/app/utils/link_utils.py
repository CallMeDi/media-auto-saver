# -*- coding: utf-8 -*-
# /usr/bin/env python3

from urllib.parse import urlparse
from typing import Optional

# 中文: 定义一些已知网站的域名映射, 用于更精确地识别网站名称
# English: Define domain mappings for some known websites for more accurate site name identification
KNOWN_SITES = {
    "twitter.com": "Twitter",
    "x.com": "Twitter", # 推特的新域名 / Twitter's new domain
    "youtube.com": "YouTube",
    "youtu.be": "YouTube",
    "bilibili.com": "Bilibili",
    "weibo.com": "Weibo",
    "weibo.cn": "Weibo",
    "pixiv.net": "Pixiv",
    "instagram.com": "Instagram",
    "douyin.com": "Douyin",
    "tiktok.com": "TikTok", # 国际版抖音 / International version of Douyin
    "kuaishou.com": "Kuaishou",
    "live.kuaishou.com": "Kuaishou",
    "xiaohongshu.com": "Xiaohongshu",
    "twitch.tv": "Twitch",
    "deviantart.com": "DeviantArt",
    "artstation.com": "ArtStation",
    "soundcloud.com": "SoundCloud",
    "vimeo.com": "Vimeo",
    # 可以根据需要添加更多网站 / Add more sites as needed
}

def extract_site_name(url: str) -> Optional[str]:
    """
    中文: 从 URL 中提取网站名称。
    English: Extract the site name from a URL.

    优先匹配 KNOWN_SITES 中的域名, 如果找不到, 则尝试提取二级域名并首字母大写。
    Prioritizes matching domains in KNOWN_SITES. If not found, attempts to extract
    the second-level domain and capitalize it.

    例如 / Examples:
    - https://twitter.com/user -> Twitter
    - https://www.youtube.com/watch?v=... -> YouTube
    - https://subdomain.unknownsite.co.uk/path -> Unknownsite
    - http://localhost:8000 -> localhost
    """
    try:
        parsed_url = urlparse(url)
        netloc = parsed_url.netloc.lower() # 获取域名部分并转小写 / Get the domain part and convert to lowercase

        if not netloc:
            return None

        # 中文: 移除端口号 (如果存在)
        # English: Remove port number (if exists)
        if ':' in netloc:
            netloc = netloc.split(':')[0]

        # 中文: 优先匹配已知站点
        # English: Prioritize matching known sites
        for domain, name in KNOWN_SITES.items():
            if netloc.endswith(domain):
                return name

        # 中文: 如果不在已知站点中, 尝试提取主域名部分
        # English: If not in known sites, try to extract the main domain part
        parts = netloc.split('.')
        if len(parts) >= 2:
            # 中文: 移除常见的 www. 前缀
            # English: Remove common www. prefix
            if parts[0] == 'www':
                parts = parts[1:]

            # 中文: 处理类似 .co.uk 的情况, 取倒数第二个部分
            # English: Handle cases like .co.uk, take the second to last part
            if len(parts) >= 2 and len(parts[-1]) <= 3 and len(parts[-2]) <= 3:
                 # 假设是 .co.uk, .org.cn 等 / Assume .co.uk, .org.cn etc.
                 if len(parts) >= 3:
                     return parts[-3].capitalize()
                 else: # 无法确定主域名 / Cannot determine main domain
                     return parts[0].capitalize() # 返回第一部分 / Return the first part
            else:
                # 中文: 取倒数第二个部分作为网站名 (例如 google.com -> Google)
                # English: Take the second to last part as the site name (e.g., google.com -> Google)
                return parts[-2].capitalize()
        elif len(parts) == 1:
             # 中文: 可能是 localhost 或类似情况
             # English: Might be localhost or similar cases
             return parts[0]
        else:
            return None # 无法解析 / Cannot parse

    except Exception:
        # 中文: 解析 URL 时发生任何错误, 都返回 None
        # English: Return None if any error occurs during URL parsing
        return None

if __name__ == "__main__":
    # 中文: 测试函数
    # English: Test the function
    test_urls = [
        "https://twitter.com/elonmusk",
        "https://x.com/SpaceX",
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtu.be/dQw4w9WgXcQ",
        "https://www.bilibili.com/video/BV1GJ411x7h7",
        "https://m.weibo.cn/status/4864988911141496",
        "https://weibo.com/1234567890/profile",
        "https://www.pixiv.net/en/artworks/88888888",
        "https://www.instagram.com/nasa/",
        "https://www.douyin.com/video/7000000000000000000",
        "https://www.tiktok.com/@charlidamelio/video/6900000000000000000",
        "https://live.kuaishou.com/u/123456",
        "https://www.kuaishou.com/short-video/abc",
        "https://www.xiaohongshu.com/explore/12345",
        "https://www.twitch.tv/ninja",
        "https://www.deviantart.com/tag/landscape",
        "https://www.artstation.com/artwork/12345",
        "https://soundcloud.com/user/track",
        "https://vimeo.com/12345678",
        "https://github.com/yt-dlp/yt-dlp",
        "http://example.co.uk/page",
        "http://localhost:8080/api",
        "invalid-url",
        "ftp://ftp.example.com/file",
        "https://sub.domain.longname.com/path"
    ]
    for url in test_urls:
        print(f"{url} -> {extract_site_name(url)}")
