import requests
import json

import config
from logger import get_module_logger

# 获取模块日志记录器
logger = get_module_logger("get_library")


def get_libraries():
    """
    获取Jellyfin的媒体库列表，并排除配置中指定的媒体库

    Returns:
        list: 包含媒体库信息的字典列表，每个字典包含'Id'和'Name'
    """
    # 确保已经完成认证
    config.get_auth_info()
    logger.info(f"[{config.JELLYFIN_CONFIG['SERVER_NAME']}] [1/4] 获取媒体库列表...")
    logger.info("-" * 40)
    url = f"{config.JELLYFIN_CONFIG['BASE_URL']}/Library/MediaFolders"

    headers = {
        "Authorization": f'MediaBrowser Token="{config.JELLYFIN_CONFIG["ACCESS_TOKEN"]}"'
    }

    try:
        response = requests.request("GET", url, headers=headers)
        response.raise_for_status()  # 检查HTTP错误

        data = response.json()
        libraries = []

        # 解析返回的JSON数据，提取每个媒体库的ID和名称
        if "Items" in data:
            for item in data["Items"]:
                if "Id" in item and "Name" in item:
                    # 排除在EXCLUDE_LIBRARY列表中的媒体库
                    if item["Name"] not in config.EXCLUDE_LIBRARY:
                        libraries.append({"Id": item["Id"], "Name": item["Name"]})
                    else:
                        logger.info(f"已排除媒体库: {item['Name']}")

        return libraries
    except requests.exceptions.RequestException as e:
        logger.error(
            f"[{config.JELLYFIN_CONFIG['SERVER_NAME']}] 获取媒体库列表失败: {str(e)}"
        )
        return []
    except (json.JSONDecodeError, KeyError) as e:
        logger.error(
            f"[{config.JELLYFIN_CONFIG['SERVER_NAME']}] 解析媒体库列表数据失败: {str(e)}"
        )
        return []
