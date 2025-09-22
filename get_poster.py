import os
import requests
import json
import random
import sys
from datetime import datetime
import config
from logger import get_module_logger

# 获取模块日志记录器
logger = get_module_logger("get_poster")


def ensure_poster_directory(poster_dir, name):
    """确保海报文件夹存在，如果不存在则创建"""
    full_path = os.path.join(poster_dir, name)
    if not os.path.exists(full_path):
        os.makedirs(full_path)
        logger.info(
            f"[{config.JELLYFIN_CONFIG['SERVER_NAME']}][{name}] 创建海报文件夹: {full_path}"
        )
    else:
        # 清空文件夹中的旧文件
        for file_name in os.listdir(full_path):
            if file_name.endswith((".jpg", ".jpeg", ".png")):
                os.remove(os.path.join(full_path, file_name))
        logger.info(
            f"[{config.JELLYFIN_CONFIG['SERVER_NAME']}][{name}] 清空海报文件夹中的旧文件"
        )
    return full_path


def get_items(parent_id, library_name=None):
    """获取媒体项列表"""
    # 根据库名从TEMPLATE_MAPPING中获取排序方式
    sort_by = "DateCreated"  # 默认排序方式
    
    if library_name:
        # 查找匹配的媒体库配置
        for lib_config in config.TEMPLATE_MAPPING:
            if lib_config["library_name"] == library_name and "poster_sort" in lib_config:
                sort_by = lib_config["poster_sort"]
                break
    logger.info(f"[{config.JELLYFIN_CONFIG['SERVER_NAME']}][{library_name}] 使用配置的排序方式: {sort_by}")

    # 修改为获取用户的媒体库列表
    url = f"{config.JELLYFIN_CONFIG['BASE_URL']}/Users/{config.JELLYFIN_CONFIG['USER_ID']}/Items/?ParentId={parent_id}&&Recursive=true&SortBy={sort_by},SortName&SortOrder=Descending&IncludeItemTypes=Movie,Series,Audio,Music,Game,Book,MusicVideo"

    headers = {
        "Authorization": f'MediaBrowser Token="{config.JELLYFIN_CONFIG["ACCESS_TOKEN"]}"'
    }
    try:
        log_prefix = f"[{config.JELLYFIN_CONFIG['SERVER_NAME']}]"
        if library_name:
            log_prefix += f"[{library_name}]"

        logger.info(f"{log_prefix} 正在从 Jellyfin 获取媒体列表...")
        response = requests.get(url, headers=headers, timeout=30)

        if response.status_code == 200:
            data = response.json()
            if len(data) > 0:
                logger.info(
                    f"{log_prefix} 成功获取到 {len(data.get('Items', []))} 个媒体项"
                )
                return data.get("Items", [])
            else:
                logger.warning(f"{log_prefix} 未找到任何媒体项")
                return []
        else:
            logger.error(
                f"{log_prefix} 获取媒体列表失败，状态码: {response.status_code}"
            )
            return []
    except Exception as e:
        if library_name:
            logger.error(
                f"[{config.JELLYFIN_CONFIG['SERVER_NAME']}][{library_name}] 获取媒体列表时出错: {e}"
            )
        else:
            logger.error(
                f"[{config.JELLYFIN_CONFIG['SERVER_NAME']}] 获取媒体列表时出错: {e}"
            )
        return []


def sort_and_select_items(items, count=9, library_name=None):
    """根据日期排序并选择特定数量的媒体项，剔除没有封面图片的项目"""
    if not items:
        return []

    log_prefix = f"[{config.JELLYFIN_CONFIG['SERVER_NAME']}]"
    if library_name:
        log_prefix += f"[{library_name}]"

    logger.info(f"{log_prefix} 正在过滤媒体项...")

    # 先过滤掉没有封面图片的项目
    filtered_items = []
    for item in items:
        if "ImageTags" in item and "Primary" in item.get("ImageTags", {}):
            filtered_items.append(item)

    logger.info(
        f"{log_prefix} 过滤后剩余 {len(filtered_items)}/{len(items)} 个有效媒体项"
    )

    if not filtered_items:
        logger.warning(f"{log_prefix} 警告: 过滤后没有包含封面图片的媒体项")
        return []

    # 直接选择前 count 个项目
    selected_items = filtered_items[:count]
    logger.info(f"{log_prefix} 已选择 {len(selected_items)} 个媒体项")

    return selected_items


def download_image(item_id, output_path, index, library_name=None):
    """下载指定 ID 的媒体项的封面图片"""
    url = f"{config.JELLYFIN_CONFIG['BASE_URL']}/Items/{item_id}/Images/{config.JELLYFIN_CONFIG['IMAGE_TYPE']}"

    headers = {
        "Authorization": f'MediaBrowser Token="{config.JELLYFIN_CONFIG["ACCESS_TOKEN"]}"'
    }

    log_prefix = f"[{config.JELLYFIN_CONFIG['SERVER_NAME']}]"
    if library_name:
        log_prefix += f"[{library_name}]"

    try:
        response = requests.get(url, headers=headers, stream=True, timeout=30)

        if response.status_code == 200:
            # 保存图片
            with open(output_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            # logger.debug(f"{log_prefix} 图片 {index} 已保存到: {output_path}")
            return True
        else:
            logger.warning(
                f"{log_prefix} 下载图片 {index} 失败，状态码: {response.status_code}"
            )
            return False
    except Exception as e:
        logger.error(f"{log_prefix} 下载图片 {index} 时出错: {e}")
        return False


def download_all_posters(selected_items, full_path, library_name):
    """下载所有选定的海报，如果不足9张则重复下载"""
    success_count = 0
    target_count = config.POSTER_DOWNLOAD_CONFIG["POSTER_COUNT"]
    downloaded_items = []

    # 首先尝试下载所有可用的海报
    for index, item in enumerate(selected_items, 1):
        # 检查 ID 是否存在
        if "Id" not in item:
            logger.warning(
                f"[{config.JELLYFIN_CONFIG['SERVER_NAME']}][{library_name}] 跳过第 {index} 个项目: 缺少 ID"
            )
            continue

        # 由于已经在sort_and_select_items中过滤，这里不再需要检查是否有Primary图片
        item_id = item["Id"]
        output_path = os.path.join(full_path, f"{success_count + 1}.jpg")

        if download_image(item_id, output_path, success_count + 1, library_name):
            success_count += 1
            downloaded_items.append(item)

        # 如果已经达到目标数量，退出循环
        if success_count >= target_count:
            break

    # 如果下载的图片数量不足目标数量，则重复下载已有的图片
    if success_count > 0 and success_count < target_count:
        logger.info(
            f"[{config.JELLYFIN_CONFIG['SERVER_NAME']}][{library_name}] 下载的图片数量({success_count})不足{target_count}张，将重复下载已有图片"
        )

        # 循环重复下载已有图片，直到达到目标数量
        repeat_index = 0
        while success_count < target_count:
            # 获取一个已下载项目（循环使用）
            repeat_item = downloaded_items[repeat_index % len(downloaded_items)]
            repeat_index += 1

            item_id = repeat_item["Id"]
            output_path = os.path.join(full_path, f"{success_count + 1}.jpg")

            if download_image(item_id, output_path, success_count + 1, library_name):
                success_count += 1

    return success_count


def download_posters_workflow(parent_id, name):
    """
    封装整个下载海报的工作流程，供main.py调用

    返回:
        tuple: (成功标志, 下载的海报数量, 配置信息)
    """
    try:
        logger.info(
            f"[{config.JELLYFIN_CONFIG['SERVER_NAME']}][{name}] [2/4] 下载海报..."
        )
        logger.info("-" * 40)

        # 确保海报文件夹存在
        full_path = ensure_poster_directory(config.POSTER_FOLDER, name)

        # 获取媒体项列表
        items = get_items(parent_id, name)
        if not items:
            logger.warning(
                f"[{config.JELLYFIN_CONFIG['SERVER_NAME']}][{name}] 没有可用的媒体封面"
            )
            return False, 0

        # 排序并选择媒体项
        selected_items = sort_and_select_items(
            items, config.POSTER_DOWNLOAD_CONFIG["POSTER_COUNT"], name
        )
        if not selected_items:
            logger.warning(
                f"[{config.JELLYFIN_CONFIG['SERVER_NAME']}][{name}] 没有可用的媒体封面"
            )
            return False, 0

        # 下载所有海报
        success_count = download_all_posters(selected_items, full_path, name)

        # 输出结果
        if success_count > 0:
            logger.info(
                f"[{config.JELLYFIN_CONFIG['SERVER_NAME']}][{name}] 成功下载 {success_count}/{config.POSTER_DOWNLOAD_CONFIG['POSTER_COUNT']} 张海报"
            )
            logger.info(
                f"[{config.JELLYFIN_CONFIG['SERVER_NAME']}][{name}] 海报已保存到: {full_path}"
            )
            return True, success_count
        else:
            logger.error(
                f"[{config.JELLYFIN_CONFIG['SERVER_NAME']}][{name}] 所有海报下载失败，程序终止"
            )
            return False, 0

    except Exception as e:
        logger.error(
            f"[{config.JELLYFIN_CONFIG['SERVER_NAME']}][{name}] 下载海报时出错: {e}",
            exc_info=True,
        )
        return False, 0
