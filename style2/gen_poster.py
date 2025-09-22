from PIL import Image, ImageFilter, ImageDraw, ImageFont
import os
import sys
import math
import random  # 添加随机模块
import colorsys

# 添加父目录到系统路径，以便能够导入项目根目录的模块
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

import config
from logger import get_module_logger

# 获取模块日志记录器
logger = get_module_logger("gen_poster")


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


def draw_text_on_image(
    image,
    text,
    position,
    font_path,
    default_font_path,
    font_size,
    fill_color=(255, 255, 255, 255),
):
    """
    在图像上绘制文字

    参数:
        image: PIL.Image对象
        text: 要绘制的文字
        position: 文字位置 (x, y)
        font_path: 字体文件路径
        font_size: 字体大小
        fill_color: 文字颜色，RGBA格式

    返回:
        添加了文字的图像
    """
    # 创建一个可绘制的图像副本
    img_copy = image.copy()
    draw = ImageDraw.Draw(img_copy)
    font_path = os.path.join(config.CURRENT_DIR, font_path)
    if not os.path.exists(font_path):
        logger.warning(f"自定义字体不存在:{font_path}，使用默认字体")
        font_path = os.path.join(config.CURRENT_DIR, "font", default_font_path)
    font = ImageFont.truetype(font_path, font_size)
    # 绘制文字
    draw.text(position, text, font=font, fill=fill_color)

    return img_copy


def create_gradient_background(width, height, name, color=None):
    """
    创建一个从左到右的渐变背景，从红色过渡到蓝色

    参数:
        width: 背景宽度
        height: 背景高度
        color: 颜色参数，此处不使用，保留参数是为了兼容性

    返回:
        渐变背景图像
    """
    # 创建一个带有线性渐变的背景
    gradient = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(gradient)

    # 定义渐变颜色（从红色到浅蓝色）
    left_color = (219, 93, 93)  # 红色
    right_color = (77, 196, 219)  # 浅蓝色

    # 为每一列创建渐变
    for x in range(width):
        # 计算当前位置的颜色
        r = int(left_color[0] * (width - x) / width + right_color[0] * x / width)
        g = int(left_color[1] * (width - x) / width + right_color[1] * x / width)
        b = int(left_color[2] * (width - x) / width + right_color[2] * x / width)

        # 绘制一条渐变线
        draw.line([(x, 0), (x, height)], fill=(r, g, b, 255))

    logger.info(f"[{config.JELLYFIN_CONFIG['SERVER_NAME']}][{name}] 创建了红蓝渐变背景")

    return gradient


def get_poster_primary_color(image_path):
    """
    分析图片并提取主色调

    参数:
        image_path: 图片文件路径

    返回:
        主色调颜色，RGBA格式
    """
    try:
        from collections import Counter

        # 打开图片
        img = Image.open(image_path)

        # 缩小图片尺寸以加快处理速度
        img = img.resize((100, 150), Image.LANCZOS)

        # 确保图片为RGBA模式
        if img.mode != "RGBA":
            img = img.convert("RGBA")

        # 获取图片中心部分的像素数据（避免边框和角落）
        # width, height = img.size
        # center_x1 = int(width * 0.2)
        # center_y1 = int(height * 0.2)
        # center_x2 = int(width * 0.8)
        # center_y2 = int(height * 0.8)

        # # 裁剪出中心区域
        # center_img = img.crop((center_x1, center_y1, center_x2, center_y2))

        # 获取所有像素
        pixels = list(img.getdata())

        # 过滤掉接近黑色和白色的像素，以及透明度低的像素
        filtered_pixels = []
        for pixel in pixels:
            r, g, b, a = pixel

            # 跳过透明度低的像素
            if a < 200:
                continue

            # 计算亮度
            brightness = (r + g + b) / 3

            # 跳过过暗或过亮的像素
            if brightness < 30 or brightness > 220:
                continue

            # 添加到过滤后的列表
            filtered_pixels.append((r, g, b, 255))

        # 如果过滤后没有像素，使用全部像素
        if not filtered_pixels:
            filtered_pixels = [(p[0], p[1], p[2], 255) for p in pixels if p[3] > 100]

        # 如果仍然没有像素，返回默认颜色
        if not filtered_pixels:
            return (150, 100, 50, 255)

        # 使用Counter找到出现最多的颜色
        color_counter = Counter(filtered_pixels)
        common_colors = color_counter.most_common(10)

        # 如果找到了颜色，返回最常见的颜色
        if common_colors:
            return common_colors

        # 如果无法找到主色调，使用平均值
        r_avg = sum(p[0] for p in filtered_pixels) // len(filtered_pixels)
        g_avg = sum(p[1] for p in filtered_pixels) // len(filtered_pixels)
        b_avg = sum(p[2] for p in filtered_pixels) // len(filtered_pixels)

        return [(r_avg, g_avg, b_avg, 255)]

    except Exception as e:
        logger.error(f"获取图片主色调时出错: {e}")
        # 返回默认颜色作为备选
        return [(150, 100, 50, 255)]


def gen_poster_workflow(name):
    """
    第一张海报底部对齐居中，第二张和第三张在其下方，分别左右偏移300像素并倾斜10°，并缩小、下移避免遮挡，主图最上层。
    """
    try:
        logger.info(
            f"[{config.JELLYFIN_CONFIG['SERVER_NAME']}][{name}] [3/4] 正在生成海报..."
        )
        poster_folder = os.path.join(config.POSTER_FOLDER, name)
        output_path = os.path.join(config.OUTPUT_FOLDER, f"{name}.png")
        template_width, template_height = 1920, 1080
        gradient_bg = create_gradient_background(template_width, template_height, name)
        supported_formats = (".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp")
        poster_files = [
            os.path.join(poster_folder, f)
            for f in sorted(os.listdir(poster_folder))
            if os.path.isfile(os.path.join(poster_folder, f))
            and f.lower().endswith(supported_formats)
        ][:3]  # 最多3张
        if len(poster_files) < 1:
            logger.error(
                f"[{config.JELLYFIN_CONFIG['SERVER_NAME']}][{name}] 错误: 在 {poster_folder} 中没有找到图片文件"
            )
            return False
        base_width, base_height = 420, 600
        center_x = template_width // 2
        y = template_height - base_height  # 主图底部对齐
        result = gradient_bg.copy()
        # 再画第一张（顶层）
        poster_path = poster_files[0]
        try:
            w, h = base_width, base_height
            poster = Image.open(poster_path).resize((w, h), Image.LANCZOS)
            mask = Image.new("L", (w, h), 0)
            ImageDraw.Draw(mask).rounded_rectangle(
                [(0, 0), (w, h)], radius=int(0.07 * w), fill=255
            )
            poster_rgba = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            poster_rgba.paste(poster, (0, 0), mask)
            poster_rgba = add_shadow(
                poster_rgba,
                offset=(8, 12),
                shadow_color=(0, 0, 0, 120),
                blur_radius=12,
            )
            paste_x = int(center_x - w // 2)
            paste_y = y+20
            # 先画第二、三张（底层）
            if len(poster_files) > 1:
                # 第二张，左移300像素，左倾10°，缩小，下移
                w2, h2 = base_width, base_height
                poster2 = Image.open(poster_files[1]).resize((w2, h2), Image.LANCZOS)
                mask2 = Image.new("L", (w2, h2), 0)
                ImageDraw.Draw(mask2).rounded_rectangle(
                    [(0, 0), (w2, h2)], radius=int(0.07 * w2), fill=255
                )
                poster2_rgba = Image.new("RGBA", (w2, h2), (0, 0, 0, 0))
                poster2_rgba.paste(poster2, (0, 0), mask2)
                poster2_rgba = add_shadow(
                    poster2_rgba,
                    offset=(8, 12),
                    shadow_color=(0, 0, 0, 120),
                    blur_radius=12,
                )
                poster2_rgba = poster2_rgba.rotate(10, expand=True, resample=Image.BICUBIC)
                paste2_x = int(center_x -w2-w2/2+50)
                paste2_y = y +70
                result.paste(poster2_rgba, (paste2_x, paste2_y), poster2_rgba)
            if len(poster_files) > 2:
                # 第三张，右移300像素，右倾10°，缩小，下移
                w3, h3 =  base_width, base_height
                poster3 = Image.open(poster_files[2]).resize((w3, h3), Image.LANCZOS)
                mask3 = Image.new("L", (w3, h3), 0)
                ImageDraw.Draw(mask3).rounded_rectangle(
                    [(0, 0), (w3, h3)], radius=int(0.07 * w3), fill=255
                )
                poster3_rgba = Image.new("RGBA", (w3, h3), (0, 0, 0, 0))
                poster3_rgba.paste(poster3, (0, 0), mask3)
                poster3_rgba = add_shadow(
                    poster3_rgba,
                    offset=(8, 12),
                    shadow_color=(0, 0, 0, 120),
                    blur_radius=12,
                )
                poster3_rgba = poster3_rgba.rotate(-10, expand=True, resample=Image.BICUBIC)
                paste3_x = int(center_x + w3 // 2 -150)
                paste3_y = y +70
                result.paste(poster3_rgba, (paste3_x, paste3_y), poster3_rgba)
            # 再画第一张（最上层）
            result.paste(poster_rgba, (paste_x, paste_y), poster_rgba)
        except Exception as e:
            logger.error(
                f"[{config.JELLYFIN_CONFIG['SERVER_NAME']}][{name}] 处理图片 {os.path.basename(poster_path)} 时出错: {e}"
            )
        # 标题
        library_ch_name = name
        library_eng_name = ""
        matched_template = None
        for template in config.TEMPLATE_MAPPING:
            if template.get("library_name") == name:
                matched_template = template
                break
        if matched_template:
            if "library_ch_name" in matched_template:
                library_ch_name = matched_template["library_ch_name"]
            if "library_eng_name" in matched_template:
                library_eng_name = matched_template["library_eng_name"]
        style_name = "style1"
        style_config = next(
            (
                style
                for style in config.STYLE_CONFIGS
                if style.get("style_name") == style_name
            ),
            None,
        )
        fangzheng_font_path = os.path.join("myfont", style_config.get("style_ch_font"))
        # 居中上方
        title_x = template_width // 2 - len(library_ch_name) * 80
        title_y = 60
        result = draw_square_title(
            result,
            library_ch_name,
            (title_x, title_y),
            fangzheng_font_path,
            "ch.ttf",
            120,
        )
        if library_eng_name:
            melete_font_path = os.path.join(
                "myfont", style_config.get("style_eng_font")
            )
            eng_x = template_width // 2 - len(library_eng_name) * 25
            eng_y = title_y + 140
            result = draw_text_on_image(
                result, library_eng_name, (eng_x, eng_y), melete_font_path, "en.otf", 60
            )
        result.save(output_path)
        logger.info(
            f"[{config.JELLYFIN_CONFIG['SERVER_NAME']}][{name}] 成功: 图片已保存到 {output_path}"
        )
        return True
    except Exception as e:
        logger.error(
            f"[{config.JELLYFIN_CONFIG['SERVER_NAME']}][{name}] 创建卡牌散开图片时出错: {e}",
            exc_info=True,
        )
        return False


def get_random_color(image_path):
    """
    获取图片随机位置的颜色

    参数:
        image_path: 图片文件路径

    返回:
        随机点颜色，RGBA格式
    """
    try:
        img = Image.open(image_path)
        # 获取图片尺寸
        width, height = img.size

        # 在图片范围内随机选择一个点
        # 避免边缘区域，缩小范围到图片的20%-80%区域
        random_x = random.randint(int(width * 0.5), int(width * 0.8))
        random_y = random.randint(int(height * 0.5), int(height * 0.8))

        # 获取随机点的颜色
        if img.mode == "RGBA":
            r, g, b, a = img.getpixel((random_x, random_y))
            return (r, g, b, a)
        elif img.mode == "RGB":
            r, g, b = img.getpixel((random_x, random_y))
            return (r + 100, g + 50, b, 255)
        else:
            img = img.convert("RGBA")
            r, g, b, a = img.getpixel((random_x, random_y))
            return (r, g, b, a)
    except Exception as e:
        logger.error(f"获取图片颜色时出错: {e}")
        # 返回随机颜色作为备选
        return (
            random.randint(50, 200),
            random.randint(50, 200),
            random.randint(50, 200),
            255,
        )


def draw_color_block(image, position, size, color):
    """
    在图像上绘制色块

    参数:
        image: PIL.Image对象
        position: 色块位置 (x, y)
        size: 色块大小 (width, height)
        color: 色块颜色，RGBA格式

    返回:
        添加了色块的图像
    """
    # 创建一个可绘制的图像副本
    img_copy = image.copy()
    draw = ImageDraw.Draw(img_copy)

    # 绘制矩形色块
    draw.rectangle(
        [position, (position[0] + size[0], position[1] + size[1])], fill=color
    )

    return img_copy


def draw_multiline_text_on_image(
    image,
    text,
    position,
    font_path,
    default_font_path,
    font_size,
    line_spacing=10,
    fill_color=(255, 255, 255, 255),
):
    """
    在图像上绘制多行文字，根据空格自动换行

    参数:
        image: PIL.Image对象
        text: 要绘制的文字
        position: 第一行文字位置 (x, y)
        font_path: 字体文件路径
        font_size: 字体大小
        line_spacing: 行间距
        fill_color: 文字颜色，RGBA格式

    返回:
        添加了文字的图像和行数
    """
    # 创建一个可绘制的图像副本
    img_copy = image.copy()
    draw = ImageDraw.Draw(img_copy)
    font_path = os.path.join(config.CURRENT_DIR, font_path)
    if not os.path.exists(font_path):
        logger.warning(f"自定义字体不存在:{font_path}，使用默认字体")
        font_path = os.path.join(config.CURRENT_DIR, "font", default_font_path)
    font = ImageFont.truetype(font_path, font_size)

    # 按空格分割文本
    lines = text.split(" ")

    # 如果只有一行，直接绘制并返回
    if len(lines) <= 1:
        draw.text(position, text, font=font, fill=fill_color)
        return img_copy, 1

    # 绘制多行文本
    x, y = position
    for i, line in enumerate(lines):
        current_y = y + i * (font_size + line_spacing)
        draw.text((x, current_y), line, font=font, fill=fill_color)

    # 返回图像和行数
    return img_copy, len(lines)


def draw_square_title(
    image,
    text,
    position,
    font_path,
    default_font_path,
    font_size,
    fill_color=(255, 255, 255, 255),
):
    """
    在图像上绘制方块字标题，为每个汉字创建一个方块背景

    参数:
        image: PIL.Image对象
        text: 要绘制的文字
        position: 文字位置 (x, y)
        font_path: 字体文件路径
        default_font_path: 默认字体文件路径
        font_size: 字体大小
        fill_color: 文字颜色，RGBA格式

    返回:
        添加了方块字标题的图像
    """
    # 创建一个可绘制的图像副本
    img_copy = image.copy()
    draw = ImageDraw.Draw(img_copy)

    # 加载字体
    font_path = os.path.join(config.CURRENT_DIR, font_path)
    if not os.path.exists(font_path):
        logger.warning(f"自定义字体不存在:{font_path}，使用默认字体")
        font_path = os.path.join(config.CURRENT_DIR, "font", default_font_path)
    font = ImageFont.truetype(font_path, font_size)

    # 设置方块参数
    char_spacing = 20  # 字符间距
    padding = 20  # 方块内边距

    # 计算每个汉字的宽度和高度
    char_width, char_height = (
        max([font.getbbox(char)[2:] for char in text]) if text else (0, 0)
    )

    # 方块大小（正方形）
    box_size = max(char_width, char_height) + padding * 2

    # 绘制每个汉字
    x, y = position
    for i, char in enumerate(text):
        # 方块位置
        box_x = x + i * (box_size + char_spacing)
        box_y = y

        # 绘制方块背景（半透明白色）
        draw.rectangle(
            [(box_x, box_y), (box_x + box_size, box_y + box_size)],
            fill=(255, 255, 255, 80),  # 半透明白色
            outline=(255, 255, 255, 200),  # 白色边框
            width=2,  # 边框宽度
        )

        # 计算文字位置，使其在方块内居中
        # PIL的getbbox返回一个(left, top, right, bottom)元组
        text_size = font.getbbox(char)[2:]
        text_x = box_x + (box_size - text_size[0]) // 2
        text_y = box_y + (box_size - text_size[1]) // 2

        # 绘制文字
        draw.text((text_x, text_y), char, font=font, fill=fill_color)

    return img_copy


if __name__ == "__main__":
    gen_poster_workflow("Hot TV")
