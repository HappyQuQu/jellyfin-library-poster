import os
import requests
import sys
import base64
from urllib.parse import urljoin
import config
from PIL import Image, ImageFilter, ImageEnhance
from logger import get_module_logger

# 获取模块日志记录器
logger = get_module_logger("update_poster")


def load_config():
    """加载配置信息"""
    return config.JELLYFIN_CONFIG


def read_image_file(path):
    """读取图片文件并转换为base64编码"""
    try:
        with open(path, "rb") as img_file:
            image_data = img_file.read()
            image_data_base64 = base64.b64encode(image_data).decode("utf-8")
            return image_data_base64
    except Exception as e:
        logger.error(f"错误: 读取图片文件时出错: {e}")
        raise IOError(f"错误: 读取图片文件时出错: {e}")


def upload_image(item_id, image_data, library_name):
    """上传图片到Jellyfin服务器"""
    try:
        # 构造 URL 和请求头
        url = f"{config.JELLYFIN_CONFIG['BASE_URL']}/Items/{item_id}/Images/{config.JELLYFIN_CONFIG['IMAGE_TYPE']}"
        headers = config.get_auth_headers()
        headers["Content-Type"] = "image/png"
        response = requests.post(url, headers=headers, data=image_data, timeout=30)

        if response.status_code in (200, 204):
            logger.info(
                f"[{config.JELLYFIN_CONFIG['SERVER_NAME']}][{library_name}] 成功: 图片上传成功"
            )
            return True
        else:
            logger.error(
                f"[{config.JELLYFIN_CONFIG['SERVER_NAME']}][{library_name}] 错误: 图片上传失败，状态码: {response.status_code}"
            )
            try:
                logger.error(
                    f"[{config.JELLYFIN_CONFIG['SERVER_NAME']}][{library_name}] 错误详情: {response.json()}"
                )
            except ValueError:
                logger.error(
                    f"[{config.JELLYFIN_CONFIG['SERVER_NAME']}][{library_name}] 错误详情: {response.text[:500]}"
                )
            return False
    except requests.exceptions.RequestException as e:
        logger.error(
            f"[{config.JELLYFIN_CONFIG['SERVER_NAME']}][{library_name}] 错误: 请求过程中出错: {e}"
        )
        return False


def add_shadow(img, offset=(5, 5), shadow_color=(0, 0, 0, 100), blur_radius=3):
    """
    给图片添加右侧和底部阴影

    参数:
        img: 原始图片（PIL.Image对象）
        offset: 阴影偏移量，(x, y)格式
        shadow_color: 阴影颜色，RGBA格式
        blur_radius: 阴影模糊半径

    返回:
        添加了阴影的新图片
    """
    # 创建一个透明背景，比原图大一些，以容纳阴影
    shadow_width = img.width + offset[0] + blur_radius * 2
    shadow_height = img.height + offset[1] + blur_radius * 2

    shadow = Image.new("RGBA", (shadow_width, shadow_height), (0, 0, 0, 0))

    # 创建阴影层
    shadow_layer = Image.new("RGBA", img.size, shadow_color)

    # 将阴影层粘贴到偏移位置
    shadow.paste(shadow_layer, (blur_radius + offset[0], blur_radius + offset[1]))

    # 模糊阴影
    shadow = shadow.filter(ImageFilter.GaussianBlur(blur_radius))

    # 创建结果图像
    result = Image.new("RGBA", shadow.size, (0, 0, 0, 0))

    # 将原图粘贴到结果图像上
    result.paste(img, (blur_radius, blur_radius), img if img.mode == "RGBA" else None)

    # 合并阴影和原图（保持原图在上层）
    shadow_img = Image.alpha_composite(shadow, result)

    return shadow_img


def upload_poster_workflow(item_id, name):
    """
    封装上传海报到Jellyfin的完整工作流程

    返回:
        bool: 上传是否成功
    """
    try:
        logger.info(
            f"[{config.JELLYFIN_CONFIG['SERVER_NAME']}][{name}] [4/4] 正在更新Jellyfin海报..."
        )
        logger.info("-" * 40)

        file_path = os.path.join(config.OUTPUT_FOLDER, f"{name}.png")
        # 读取图片文件
        image_data_base64 = read_image_file(file_path)

        # 上传图片
        success = upload_image(item_id, image_data_base64, name)

        if success:
            logger.info(
                f"[{config.JELLYFIN_CONFIG['SERVER_NAME']}][{name}] 海报上传成功！"
            )
            return True
        else:
            logger.warning(
                f"[{config.JELLYFIN_CONFIG['SERVER_NAME']}][{name}] 海报上传失败！"
            )
            return False

    except Exception as e:
        logger.error(
            f"[{config.JELLYFIN_CONFIG['SERVER_NAME']}][{name}] 上传海报时出错: {e}",
            exc_info=True,
        )
        return False
