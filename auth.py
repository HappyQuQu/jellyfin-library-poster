import requests
import json
import socket
import uuid
from logger import get_module_logger

# 获取模块日志记录器
logger = get_module_logger("auth")


DEVICE_ID = uuid.uuid5(uuid.NAMESPACE_DNS, socket.gethostname()).hex


def get_request_headers(server_type="", access_token="", user_id=""):
    """提供完整客户端身份，并通过专用头传递认证信息，兼容反向代理。"""
    scheme = "Emby" if server_type.lower() == "emby" else "MediaBrowser"
    authorization = (
        f'{scheme} Client="jellyfin-library-poster", '
        f'Device="jellyfin-library-poster", DeviceId="{DEVICE_ID}", Version="1.0.0"'
    )
    if user_id:
        authorization += f', UserId="{user_id}"'
    if access_token:
        authorization += f', Token="{access_token}"'
    headers = {"X-Emby-Authorization": authorization}
    if access_token:
        headers["X-Emby-Token"] = access_token
    return headers


def authenticate(base_url, username, password, server_type=""):
    """
    进行Jellyfin/Emby身份验证并返回User.Id和AccessToken

    Returns:
        dict: 包含User.Id和AccessToken的字典，验证失败则返回None
    """

    base_url = base_url.rstrip("/")
    url = f"{base_url}/Users/AuthenticateByName"
    if not server_type and base_url.lower().endswith("/emby"):
        server_type = "emby"

    headers = get_request_headers(server_type)

    try:
        logger.info(f"正在连接服务器: {base_url}")
        response = requests.post(
            url, headers=headers, json={"Username": username, "Pw": password}, timeout=30
        )
        response.raise_for_status()  # 检查HTTP错误

        data = response.json()
        auth_info = {
            "user_id": data.get("User", {}).get("Id"),
            "access_token": data.get("AccessToken"),
            "base_url": base_url,  # 同时返回base_url方便后续使用
        }

        # 验证是否成功获取了必要信息
        if auth_info["user_id"] and auth_info["access_token"]:
            logger.info(f"认证成功: 用户 {username}")
            return auth_info
        else:
            logger.error("认证成功但未能获取User.Id或AccessToken")
            return None

    except requests.exceptions.RequestException as e:
        logger.error(f"认证请求失败: {str(e)}")
        if e.response is not None and e.response.status_code in (401, 403):
            logger.error(
                "请使用媒体服务器本地用户名和密码（不是 Emby Connect 账号），"
                "并检查用户的远程访问、设备访问权限及反向代理规则"
            )
        return None
    except json.JSONDecodeError:
        logger.error("无法解析服务器响应")
        return None
