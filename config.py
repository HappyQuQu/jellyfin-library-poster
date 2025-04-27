import os
import json
from logger import get_module_logger

# 获取模块日志记录器
logger = get_module_logger("config")

# 获取当前脚本所在目录
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# 加载JSON配置文件
CONFIG_JSON_PATH = os.path.join(CURRENT_DIR, "config", "config.json")
try:
    with open(CONFIG_JSON_PATH, "r", encoding="utf-8") as f:
        JSON_CONFIG = json.load(f)
    logger.info(f"成功加载配置文件: {CONFIG_JSON_PATH}")
except (FileNotFoundError, json.JSONDecodeError) as e:
    logger.error(f"无法加载配置文件 config.json: {e}")


# 文件路径配置
POSTER_FOLDER = os.path.join(CURRENT_DIR, "poster")  # 海报图片文件夹
TEMPLATE_FOLDER = os.path.join(CURRENT_DIR, "template")  # 模板图片
OUTPUT_FOLDER = os.path.join(CURRENT_DIR, "output")  # 输出文件夹
if isinstance(JSON_CONFIG["jellyfin"], list):
    JELLYFIN_CONFIGS = []  # 如果有多个配置，初始化为空列表
    for json_config in JSON_CONFIG["jellyfin"]:
        JELLYFIN_CONFIGS.append(
            {
                "SERVER_NAME": json_config.get("server_name", json_config["base_url"]),
                "SERVER_TYPE": json_config.get("server_type", ""),
                "BASE_URL": json_config["base_url"],  # 从JSON配置获取Jellyfin服务地址
                "USER_NAME": json_config["user_name"],  # 用户名
                "PASSWORD": json_config["password"],  # 密码
                "AUTHORIZATION": 'MediaBrowser Client="other", Device="client", DeviceId="123", Version="0.0.0"',  # 是否需要认证
                "ACCESS_TOKEN": "",  # API密钥
                "USER_ID": "",  # 用户ID
                "IMAGE_TYPE": "Primary",  # 图片类型
                "IMAGE_PATH": "poster.png",  # 图片文件名
                "UPDATE_POSTER": json_config.get(
                    "update_poster", False
                ),  # 是否更新海报
            }
        )
else:
    JELLYFIN_CONFIG = {
        "SERVER_NAME": JSON_CONFIG["jellyfin"].get(
            "server_name", JSON_CONFIG["jellyfin"]["base_url"]
        ),
        "SERVER_TYPE": JSON_CONFIG["jellyfin"].get("server_type", ""),
        "BASE_URL": JSON_CONFIG["jellyfin"][
            "base_url"
        ],  # 从JSON配置获取Jellyfin服务地址
        "USER_NAME": JSON_CONFIG["jellyfin"]["user_name"],  # 用户名
        "PASSWORD": JSON_CONFIG["jellyfin"]["password"],  # 密码
        "AUTHORIZATION": 'MediaBrowser Client="other", Device="client", DeviceId="123", Version="0.0.0"',  # 是否需要认证
        "ACCESS_TOKEN": "",  # API密钥
        "USER_ID": "",  # 用户ID
        "IMAGE_TYPE": "Primary",  # 图片类型
        "IMAGE_PATH": "poster.png",  # 图片文件名
        "UPDATE_POSTER": JSON_CONFIG["jellyfin"].get(
            "update_poster", False
        ),  # 是否更新海报
    }
    JELLYFIN_CONFIGS = [JELLYFIN_CONFIG]

JELLYFIN_CONFIG = {
    "SERVER_NAME": "",  # 服务器名称
    "SERVER_TYPE": "",
    "BASE_URL": "",  # 从JSON配置获取Jellyfin服务地址
    "USER_NAME": "",  # 用户名
    "PASSWORD": "",  # 密码
    "SERVER_NAME": "",
    "SERVER_TYPE": "",
    "AUTHORIZATION": 'MediaBrowser Client="other", Device="client", DeviceId="123", Version="0.0.0"',  # 是否需要认证
    "ACCESS_TOKEN": "",  # API密钥
    "USER_ID": "",  # 用户ID
    "IMAGE_TYPE": "Primary",  # 图片类型
    "IMAGE_PATH": "poster.png",  # 图片文件名
    "UPDATE_POSTER": False,  # 是否更新海报
}

CRON = JSON_CONFIG.get("cron", "0 1 * * *")  # 默认每天1点执行一次

EXCLUDE_LIBRARY = JSON_CONFIG["exclude_update_library"]  # 排除更新的媒体库列表

TEMPLATE_MAPPING = JSON_CONFIG["template_mapping"]

# 海报生成配置
POSTER_GEN_CONFIG = {
    "ROWS": 3,  # 每列图片数
    "COLS": 3,  # 总列数
    "MARGIN": 22,  # 图片垂直间距
    "CORNER_RADIUS": 46.1,  # 圆角半径
    "ROTATION_ANGLE": -15.8,  # 旋转角度
    "START_X": 835,  # 第一列的 x 坐标
    "START_Y": -362,  # 第一列的 y 坐标
    "COLUMN_SPACING": 100,  # 列间距
    "SAVE_COLUMNS": True,  # 是否保存每列图片
    "CELL_WIDTH": 410,  # 海报宽度
    "CELL_HEIGHT": 610,  # 海报高度
}

# 海报下载配置
POSTER_DOWNLOAD_CONFIG = {
    "POSTER_COUNT": 9,  # 要下载的海报数量
    "POSTER_DIR": POSTER_FOLDER,  # 海报保存目录
}


# 初始化认证信息
def init_auth():
    """初始化认证信息并更新JELLYFIN_CONFIG"""
    from auth import authenticate

    # 进行认证
    logger.info(f"正在初始化服务器 {JELLYFIN_CONFIG['SERVER_NAME']} 的认证信息")
    auth_info = authenticate(
        JELLYFIN_CONFIG["BASE_URL"],
        JELLYFIN_CONFIG["USER_NAME"],
        JELLYFIN_CONFIG["PASSWORD"],
    )

    if auth_info:
        # 更新JELLYFIN_CONFIG
        JELLYFIN_CONFIG["ACCESS_TOKEN"] = auth_info.get("access_token", "")
        JELLYFIN_CONFIG["USER_ID"] = auth_info.get("user_id", "")
        logger.info(f"认证信息已更新: 用户ID={JELLYFIN_CONFIG['USER_ID'][:8]}...")
        return True
    else:
        logger.error("认证失败，无法获取认证信息")
        return False


# 获取认证信息
def get_auth_info():
    """获取认证信息，如果尚未认证则进行认证"""
    # 如果尚未进行认证，先初始化认证
    if not JELLYFIN_CONFIG["ACCESS_TOKEN"] or not JELLYFIN_CONFIG["USER_ID"]:
        logger.debug("未找到有效的令牌，重新进行认证")
        init_auth()

    # 返回认证相关信息
    return {
        "user_id": JELLYFIN_CONFIG["USER_ID"],
        "access_token": JELLYFIN_CONFIG["ACCESS_TOKEN"],
        "base_url": JELLYFIN_CONFIG["BASE_URL"],
    }


# 刷新认证信息
def refresh_auth():
    """强制刷新认证信息"""
    logger.info("强制刷新认证信息")
    return init_auth()


# 模块加载时不自动进行认证，改为按需认证
# try:
#     init_auth()
# except Exception as e:
#     logger.error(f"初始化认证时出错: {e}", exc_info=True)
