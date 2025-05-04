# -*- coding: utf-8 -*-
# /usr/bin/env python3

import yt_dlp
import gallery_dl
import os
import logging
import re # 正则表达式库, 用于解析 gallery-dl 输出 / Regex library for parsing gallery-dl output
import asyncio # 用于 subprocess
import subprocess # 用于 gallery-dl 调用 / For gallery-dl call
from typing import Dict, Any, Optional, Tuple, List
from app.core.config import settings
from app.models.link import Link, LinkType

# 中文: 获取日志记录器 (已在 main.py 中配置)
# English: Get logger (configured in main.py)
logger = logging.getLogger(__name__)

# 中文: 定义 yt-dlp 的默认选项
# English: Define default options for yt-dlp
YDL_DEFAULT_OPTS = {
    'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best', # 优先下载 mp4 格式 / Prioritize mp4 format
    'outtmpl': os.path.join(settings.MEDIA_ROOT, '%(uploader)s [%(channel_id)s]', '%(title)s [%(id)s].%(ext)s'), # 输出路径模板 / Output path template
    'writethumbnail': True, # 下载封面 / Download thumbnail
    'writesubtitles': True, # 下载字幕 / Download subtitles
    'writeautomaticsub': True, # 下载自动生成的字幕 / Download auto-generated subtitles
    'subtitleslangs': ['en', 'zh-Hans', 'zh-Hant'], # 字幕语言 / Subtitle languages
    'quiet': False, # 关闭静默模式以获取更多信息, 但仍抑制警告 / Turn off quiet mode for more info, but still suppress warnings
    'no_warnings': True, # 不显示警告 / Suppress warnings
    'progress_hooks': [], # 进度回调 (可以用于更新状态) / Progress hooks (can be used for status updates)
    # 'postprocessor_hooks': [], # 我们将动态添加后处理器钩子 / We will add postprocessor hooks dynamically
    'ignoreerrors': True, # 忽略下载错误, 继续处理播放列表中的其他项目 / Ignore download errors, continue with playlist items
    'download_archive': os.path.join(settings.MEDIA_ROOT, 'download_archive.txt'), # 下载记录文件, 避免重复下载 / Archive file to avoid re-downloading
    'concurrent_fragment_downloads': settings.MAX_CONCURRENT_DOWNLOADS, # 并发分片下载数 / Concurrent fragment downloads
    'retries': 5, # 重试次数 / Number of retries
    'fragment_retries': 5, # 分片下载重试次数 / Fragment retries
}

# 中文: 定义 gallery-dl 的默认选项 (通过命令行参数模拟)
# English: Define default options for gallery-dl (simulated via command-line arguments)
GDL_DEFAULT_ARGS = [
    "--directory", settings.MEDIA_ROOT, # 下载目录 / Download directory
    "--write-metadata", # 写入元数据文件 / Write metadata file
    "--ugoira-conv-lossless", # ugoira (动图) 转为无损格式 / Convert ugoira (animated images) to lossless format
    "--retries", "5", # 重试次数 / Number of retries
    "--sleep", "1-3", # 下载间隔随机睡眠 / Random sleep between downloads
    "--download-archive", os.path.join(settings.MEDIA_ROOT, 'gallery_dl_archive.sqlite'), # 下载记录数据库 (修正参数名) / Archive database (corrected parameter name)
    "--concurrent", str(settings.MAX_CONCURRENT_DOWNLOADS), # 并发下载数 / Concurrent downloads
]

def get_downloader_for_link(link: Link) -> Tuple[str, Dict[str, Any] | List[str]]:
    """
    中文: 根据链接信息选择合适的下载器及其配置。
    English: Select the appropriate downloader and its configuration based on link information.

    返回: (下载器名称, 下载器选项/参数)
    Returns: (downloader_name, downloader_options/arguments)
    """
    site = link.site_name.lower() if link.site_name else ""
    link_type = link.link_type

    # 中文: 优先使用 gallery-dl 处理图片站和特定网站
    # English: Prioritize gallery-dl for image sites and specific websites
    if site in ["pixiv", "instagram", "deviantart", "artstation", "weibo", "xiaohongshu"]:
        logger.info(f"Using gallery-dl for site: {site}")
        gdl_args = GDL_DEFAULT_ARGS[:] # 复制默认参数 / Copy default arguments
        # 中文: 优先使用链接特定的 Cookies, 其次使用全局设置
        # English: Prioritize link-specific cookies, then global settings
        cookie_path_to_use = None
        if link.cookies_path and os.path.exists(link.cookies_path):
             cookie_path_to_use = link.cookies_path
             logger.info(f"Using link-specific cookies for link {link.id}: {cookie_path_to_use}")
        elif link.cookies_path:
             logger.warning(f"Link-specific cookies file specified for link {link.id} but not found at: {link.cookies_path}. Checking global settings.")

        if not cookie_path_to_use:
            global_cookie_path = settings.SITE_COOKIES.get(site)
            if global_cookie_path and os.path.exists(global_cookie_path):
                cookie_path_to_use = global_cookie_path
                logger.info(f"Using global cookies for site '{site}': {cookie_path_to_use}")
            elif global_cookie_path:
                 logger.warning(f"Global cookies file specified for site '{site}' but not found at: {global_cookie_path}")

        if cookie_path_to_use:
            gdl_args.extend(["--cookies", cookie_path_to_use])

        # TODO: 可以根据 link.settings 添加特定参数 / TODO: Add specific arguments based on link.settings
        return "gallery-dl", gdl_args

    # 中文: 其他情况默认使用 yt-dlp
    # English: Default to yt-dlp for other cases
    logger.info(f"Using yt-dlp for site: {site or 'unknown'}")
    ydl_opts = YDL_DEFAULT_OPTS.copy() # 复制默认选项 / Copy default options

    # 中文: 为直播链接调整选项
    # English: Adjust options for live links
    if link_type == LinkType.LIVE:
        ydl_opts['outtmpl'] = os.path.join(settings.MEDIA_ROOT, 'Live Recordings', '%(uploader)s [%(channel_id)s]', '%(title)s - %(timestamp)s [%(id)s].%(ext)s')
        ydl_opts['live_from_start'] = True # 从头开始录制 / Record from the start
        # 可以在这里添加其他直播相关选项 / Add other live-related options here

    # 中文: 检查 yt-dlp 是否也需要 Cookies (同样优先链接特定, 其次全局)
    # English: Check if yt-dlp also needs cookies (prioritize link-specific, then global)
    cookie_path_to_use_ydl = None
    if link.cookies_path and os.path.exists(link.cookies_path):
        cookie_path_to_use_ydl = link.cookies_path
        logger.info(f"Using link-specific cookies for link {link.id} (yt-dlp): {cookie_path_to_use_ydl}")
    elif link.cookies_path:
        logger.warning(f"Link-specific cookies file specified for link {link.id} (yt-dlp) but not found at: {link.cookies_path}. Checking global settings.")

    if not cookie_path_to_use_ydl:
        global_cookie_path_ydl = settings.SITE_COOKIES.get(site)
        if global_cookie_path_ydl and os.path.exists(global_cookie_path_ydl):
            cookie_path_to_use_ydl = global_cookie_path_ydl
            logger.info(f"Using global cookies for site '{site}' (yt-dlp): {cookie_path_to_use_ydl}")
        elif global_cookie_path_ydl:
            logger.warning(f"Global cookies file specified for site '{site}' (yt-dlp) but not found at: {global_cookie_path_ydl}")

    if cookie_path_to_use_ydl:
        ydl_opts['cookiefile'] = cookie_path_to_use_ydl


    # TODO: 可以根据 link.settings 覆盖或添加特定选项 / TODO: Override or add specific options based on link.settings
    # Example: if 'output_template' in link.settings: ydl_opts['outtmpl'] = link.settings['output_template']

    return "yt-dlp", ydl_opts


async def download_media(link: Link) -> Dict[str, Any]:
    """
    中文: 使用合适的下载器下载或录制链接内容。
    English: Download or record link content using the appropriate downloader.

    返回: 包含结果信息的字典 (例如: status, error, downloaded_files)
    Returns: A dictionary containing result information (e.g., status, error, downloaded_files)
    """
    downloader_name, config = get_downloader_for_link(link)
    result = {"status": "error", "error": None, "downloaded_files": []}
    downloaded_files_list = [] # 用于收集文件名的列表 / List to collect filenames

    try:
        if downloader_name == "yt-dlp":
            ydl_opts = config

            # --- yt-dlp 文件名捕获钩子 (改进版) ---
            # --- yt-dlp filename capture hook (improved) ---
            def ydl_filename_hook(d):
                if d['status'] == 'finished':
                    # 优先使用 info_dict 中的 filepath, 这是处理后的最终路径
                    # Prioritize filepath from info_dict, this is the final processed path
                    filepath = d.get('info_dict', {}).get('filepath')
                    if not filepath:
                        # 如果 info_dict 中没有, 尝试使用顶层的 filename (可能是原始或临时名)
                        # If not in info_dict, try top-level filename (might be original or temp name)
                        filepath = d.get('filename')

                    if filepath:
                        # 确保文件存在且不是临时文件
                        # Ensure file exists and is not a temporary file
                        if not filepath.endswith(('.part', '.temp', '.ytdl')) and os.path.exists(filepath) and os.path.isfile(filepath):
                            logger.debug(f"yt-dlp hook: Detected finished file: {filepath}")
                            downloaded_files_list.append(filepath)
                        else:
                            logger.debug(f"yt-dlp hook: Ignoring potential temp file or non-existent file: {filepath}")
                    else:
                         logger.debug(f"yt-dlp hook: No filepath found in finished status dict: {d}")

            # 将钩子添加到选项中 / Add hook to options
            # 注意: progress_hooks 也可以用来获取信息, 但 postprocessor_hooks 更适合获取最终文件
            # Note: progress_hooks can also get info, but postprocessor_hooks are better for final files
            ydl_opts['progress_hooks'] = [ydl_filename_hook] # 使用 progress hook 更通用 / Using progress hook is more general
            # --------------------------

            # 中文: 确保输出目录存在 (yt-dlp 通常会自动创建, 但以防万一)
            # English: Ensure output directory exists (yt-dlp usually creates it, but just in case)
            output_template = ydl_opts.get('outtmpl', YDL_DEFAULT_OPTS['outtmpl'])
            output_dir = os.path.dirname(output_template) # 提取目录部分 / Extract directory part
            # 注意: 模板中的变量此时无法解析, 我们只创建基础目录结构
            # Note: Variables in the template cannot be resolved at this point, we only create the base directory structure
            # 实际目录由 yt-dlp 在下载时根据信息创建 / Actual directory is created by yt-dlp during download based on info
            base_output_dir = settings.MEDIA_ROOT
            if '%(uploader)s' in output_dir or '%(channel_id)s' in output_dir:
                 # 如果模板包含动态部分, 只创建 MEDIA_ROOT
                 # If template contains dynamic parts, only create MEDIA_ROOT
                 pass # yt-dlp will handle it
            else:
                 base_output_dir = output_dir # 如果是固定路径 / If it's a fixed path
            os.makedirs(base_output_dir, exist_ok=True)

            logger.info(f"Starting yt-dlp download for {link.url}") # 选项可能过长, 不打印 / Options might be too long, don't print
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    # download() 返回 0 表示成功, 非 0 表示有错误 (但 ignoreerrors=True 时仍可能下载了部分文件)
                    # download() returns 0 on success, non-zero indicates errors (but with ignoreerrors=True, some files might still be downloaded)
                    ydl.download([link.url])
                    # 即使有错误, 我们也认为任务完成, 但状态可能不是 success
                    # Even with errors, we consider the task finished, but status might not be success
                    # 最终状态和文件列表由钩子决定 / Final status and file list determined by hooks
                    # yt-dlp download() returns 0 on success, non-zero indicates errors.
                    # With ignoreerrors=True, it might return 0 even if some items failed,
                    # but it will log errors. We rely on the hook for file detection.
                    # If the hook found files, assume success for the link, otherwise check for errors.
                    if downloaded_files_list:
                         result["status"] = "success"
                         result["downloaded_files"] = list(set(downloaded_files_list)) # Deduplicate
                         logger.info(f"yt-dlp download finished for {link.url}. Status: success, Files: {len(result['downloaded_files'])}")
                    else:
                         # If no files were detected, it might be a real failure or no media was found.
                         # yt-dlp logs will have more details.
                         result["error"] = "yt-dlp finished, but no files were detected by the hook. Check logs for details."
                         result["status"] = "error"
                         logger.warning(f"yt-dlp download finished for {link.url}. Status: error (no files detected).")


            except yt_dlp.utils.DownloadError as de:
                 # Catch specific download errors (even with ignoreerrors=True, some critical errors are raised)
                 logger.error(f"yt-dlp DownloadError for {link.url}: {de}", exc_info=False)
                 result["error"] = f"yt-dlp DownloadError: {de}"
                 result["status"] = "error"
                 # Even on error, check if some files were downloaded by the hook
                 if downloaded_files_list:
                     result["downloaded_files"] = list(set(downloaded_files_list))
                     logger.info(f"yt-dlp download finished with error for {link.url}, but some files were detected: {len(result['downloaded_files'])}")
                 else:
                     logger.error(f"yt-dlp download failed for {link.url} with DownloadError.")


        elif downloader_name == "gallery-dl":
            gdl_args = config
            # English: gallery-dl needs the URL as a separate argument
            # English: gallery-dl needs the URL as a separate argument
            full_args = gdl_args + [link.url]
            logger.info(f"Starting gallery-dl download for {link.url} with args: {full_args}")
            # --- 使用 subprocess 调用 gallery-dl ---
            # --- Using subprocess to call gallery-dl ---
            try:
                process = await asyncio.create_subprocess_exec(
                    'gallery-dl', *full_args,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                stdout_bytes, stderr_bytes = await process.communicate()
                stdout = stdout_bytes.decode(errors='ignore') # 解码输出 / Decode output
                stderr = stderr_bytes.decode(errors='ignore')

                # --- 解析 gallery-dl 输出以获取文件名 (改进版) ---
                # --- Parse gallery-dl output for filenames (improved) ---
                # 尝试匹配 gallery-dl 输出中指示写入文件的行
                # Try matching lines indicating file writing in gallery-dl output
                # 常见格式: '/path/to/file' 或 "[debug] Writing data to '/path/to/file'"
                # Common formats: '/path/to/file' or "[debug] Writing data to '/path/to/file'"
                # 正则: 匹配以 MEDIA_ROOT 开头的路径, 可能被引号包围, 忽略行首的日志前缀
                # Regex: Match paths starting with MEDIA_ROOT, possibly quoted, ignore leading log prefix
                path_pattern = re.compile(
                    # 可选的日志前缀 / Optional log prefix
                    r"^(?:\[[^\]]+\]\s*)*"
                    # 路径部分, 可能被引号包围 / Path part, possibly quoted
                    r"(?:Writing data to\s*)?" # 可选的 "Writing data to" / Optional "Writing data to"
                    r"['\"]?(" + re.escape(settings.MEDIA_ROOT) + r"/[^'\"\s]+)['\"]?"
                )

                for line in stdout.splitlines():
                    match = path_pattern.search(line.strip()) # 移除首尾空格 / Remove leading/trailing whitespace
                    if match:
                        filepath = match.group(1).strip()
                        # 再次检查文件是否存在且是文件 / Double-check file existence and type
                        if os.path.exists(filepath) and os.path.isfile(filepath):
                            logger.debug(f"gallery-dl parser: Found potential file: {filepath}")
                            downloaded_files_list.append(filepath)
                        else:
                             logger.debug(f"gallery-dl parser: Ignoring non-existent or non-file path: {filepath}")

                # ------------------------------------

                if process.returncode == 0:
                    result["status"] = "success"
                    result["downloaded_files"] = list(set(downloaded_files_list)) # 去重 / Deduplicate
                    if not result["downloaded_files"]:
                         logger.warning(f"gallery-dl for {link.url} finished successfully but no files were parsed from output.")
                    logger.info(f"gallery-dl stdout for {link.url}:\n{stdout[:500]}...") # 只记录部分输出 / Log partial output
                else:
                    result["error"] = f"gallery-dl failed with code {process.returncode}. Stderr: {stderr}"
                    result["status"] = "error"
                    # 即使失败, 也记录可能已下载的文件 / Even on failure, log potentially downloaded files
                    result["downloaded_files"] = list(set(downloaded_files_list))
                    logger.error(f"gallery-dl stderr for {link.url}:\n{stderr}")

            except FileNotFoundError:
                 logger.error("gallery-dl command not found. Please ensure gallery-dl is installed and in PATH.")
                 result["error"] = "gallery-dl command not found."
                 result["status"] = "error"
            except Exception as e:
                 logger.error(f"Error running gallery-dl for {link.url}: {e}", exc_info=True)
                 result["error"] = f"Exception during gallery-dl execution: {e}"
                 result["status"] = "error"

            logger.info(f"gallery-dl download finished for {link.url}. Status: {result['status']}, Files: {len(result.get('downloaded_files', []))}")

        else:
            result["error"] = f"Unknown downloader: {downloader_name}"
            result["status"] = "error"

    except Exception as e:
        logger.error(f"Unexpected error during download preparation for {link.url}: {e}", exc_info=True)
        result["error"] = f"Unexpected error during preparation: {e}"
        result["status"] = "error"

    # 确保即使发生意外错误, 也能返回收集到的文件列表
    # Ensure the collected file list is returned even if unexpected errors occur
    if downloaded_files_list and "downloaded_files" not in result:
         result["downloaded_files"] = list(set(downloaded_files_list))

    return result

if __name__ == "__main__":
    # 中文: 测试下载功能 (需要一个有效的链接)
    # English: Test download function (requires a valid link)
    async def test():
        test_link_data = {
            "id": 1,
            "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", # Rick Astley :)
            "link_type": LinkType.CREATOR,
            "site_name": "YouTube",
            "is_enabled": True,
            "settings": {}
            # 其他字段省略 / Other fields omitted
        }
        # 中文: 创建一个临时的 Link 对象用于测试
        # English: Create a temporary Link object for testing
        test_link = Link.model_validate(test_link_data)

        print(f"Testing download for: {test_link.url}")
        download_result = await download_media(test_link)
        print("Download Result:")
        import json
        print(json.dumps(download_result, indent=2))

        # 测试 gallery-dl (如果安装了)
        # Test gallery-dl (if installed)
        test_link_gdl_data = {
             "id": 2,
             "url": "https://www.instagram.com/nasa/", # NASA Instagram
             "link_type": LinkType.CREATOR,
             "site_name": "Instagram",
             "is_enabled": True,
             "settings": {}
        }
        test_link_gdl = Link.model_validate(test_link_gdl_data)
        print(f"\nTesting download for: {test_link_gdl.url}")
        download_result_gdl = await download_media(test_link_gdl)
        print("Download Result (gallery-dl):")
        print(json.dumps(download_result_gdl, indent=2))

    import asyncio
    # asyncio.run(test()) # 取消注释以运行测试 / Uncomment to run the test
    print("Downloader service module loaded. Run with test() function for basic checks.")
