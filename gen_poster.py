from PIL import Image, ImageFilter, ImageDraw, ImageFont
import os
import math
import config
import random  # 添加随机模块
from logger import get_module_logger
import colorsys

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
    image, text, position, font_path,default_font_path, font_size, fill_color=(255, 255, 255, 255)
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


def create_gradient_background(width, height, name,color=None):
    """
    创建一个从左到右的渐变背景，使用遮罩技术实现渐变效果
    左侧颜色更深，右侧颜色适中，提供更明显的渐变效果
    
    参数:
        width: 背景宽度
        height: 背景高度
        color: 颜色数组或单个颜色，如果为None则随机生成
              如果是数组，会依次尝试每个颜色，跳过太黑或太淡的颜色
        
    返回:
        渐变背景图像
    """
    def normalize_rgb(input_rgb):
        """
        将各种可能的输入格式，统一提取成 (r, g, b) 三元组。
        支持：
        - (r, g, b)
        - (r, g, b, a)
        - ((r, g, b), idx) or ((r, g, b, a), idx)
        """
        if isinstance(input_rgb, tuple):
            # 情况 3: ((r,g,b,a), idx) 或 ((r,g,b), idx)
            if len(input_rgb) == 2 and isinstance(input_rgb[0], tuple):
                return normalize_rgb(input_rgb[0])
            # 情况 2: RGBA
            if len(input_rgb) == 4 and all(isinstance(v, (int, float)) for v in input_rgb):
                return input_rgb[:3]
            # 情况 1: RGB
            if len(input_rgb) == 3 and all(isinstance(v, (int, float)) for v in input_rgb):
                return input_rgb
        raise ValueError(f"无法识别的颜色格式: {input_rgb!r}")

    def is_mid_bright(input_rgb, min_lum=80, max_lum=200):
        """
        基于相对亮度判断：不过暗（>=min_lum）也不过白（<=max_lum）。
        input_rgb 可为多种格式，函数内部会 normalize。
        """
        r, g, b = normalize_rgb(input_rgb)
        lum = 0.299*r + 0.587*g + 0.114*b
        return min_lum <= lum <= max_lum
    # 定义用于判断颜色是否合适的函数
    def is_mid_bright_hsl(input_rgb, min_l=0.3, max_l=0.7):
        """
        基于 HSL Lightness 判断。Lightness 在 [0,1]。
        """
        r, g, b = normalize_rgb(input_rgb)
        # 归一到 [0,1]
        r1, g1, b1 = r/255.0, g/255.0, b/255.0
        h, l, s = colorsys.rgb_to_hls(r1, g1, b1)
        return min_l <= l <= max_l
    
    selected_color = None
    
    # 如果传入的是颜色数组
    if isinstance(color, list) and len(color) > 0:
        # 尝试找到合适的颜色，最多尝试5个
        for i in range(min(10, len(color))):
            if is_mid_bright_hsl(color[i]):
                # 如果是(color_tuple, count)格式，提取颜色元组
                if isinstance(color[i], tuple) and len(color[i]) == 2 and isinstance(color[i][0], tuple):
                    selected_color = color[i][0]
                else:
                    selected_color = color[i]
                logger.info(f"[{config.JELLYFIN_CONFIG['SERVER_NAME']}][{name}] 海报主题色:[{selected_color}]适合做背景")
                break
            else:
                logger.info(f"[{config.JELLYFIN_CONFIG['SERVER_NAME']}][{name}] 海报主题色:[{color[i]}]不适合做背景,尝试做下一个颜色")
    
    # 如果没有找到合适的颜色，随机生成一个颜色
    if selected_color is None:

        def random_hsl_to_rgb(
            hue_range=(0, 360),
            sat_range=(0.5, 1.0),
            light_range=(0.5, 0.8)
        ):
            """
            hue_range: 色相范围，取值 0~360
            sat_range: 饱和度范围，取值 0~1
            light_range: 明度范围，取值 0~1
            返回值：RGB 三元组，每个通道 0~255
            """
            h = random.uniform(hue_range[0]/360.0, hue_range[1]/360.0)
            s = random.uniform(sat_range[0], sat_range[1])
            l = random.uniform(light_range[0], light_range[1])
            # colorsys.hls_to_rgb 接受 H, L, S (注意顺序) 都是 0~1
            r, g, b = colorsys.hls_to_rgb(h, l, s)
            # 转回 0~255
            return (int(r*255), int(g*255), int(b*255))

        # 生成颜色示例
        selected_color = random_hsl_to_rgb()
        logger.info(f"[{config.JELLYFIN_CONFIG['SERVER_NAME']}][{name}] 海报所有主题色不适合做背景，随机生成一个颜色[{selected_color}]。")

    # 如果是已经提供的颜色，将其加深
    # 降低各通道的亮度，使颜色更深
    r = int(selected_color[0] * 0.65)  # 降低35%
    g = int(selected_color[1] * 0.65)  # 降低35%
    b = int(selected_color[2] * 0.65)  # 降低35%
    
    # 确保RGB值不会小于0
    r = max(0, r)
    g = max(0, g)
    b = max(0, b)
    
    # 更新颜色
    selected_color = (r, g, b, selected_color[3] if len(selected_color) > 3 else 255)

    # 确保selected_color包含alpha通道
    if len(selected_color) == 3:
        selected_color = (selected_color[0], selected_color[1], selected_color[2], 255)
    
    # 基于selected_color自动生成浅色版本作为右侧颜色
    # 将selected_color的RGB值增加更合适的比例，使右侧颜色适中
    # 限制最大值为255
    r = min(255, int(selected_color[0] * 1.9))  # 从2.2降到1.9
    g = min(255, int(selected_color[1] * 1.9))  # 从2.2降到1.9
    b = min(255, int(selected_color[2] * 1.9))  # 从2.2降到1.9
    
    # 确保至少有一定的亮度增加，但比之前小
    r = max(r, selected_color[0] + 80)  # 从100降到80
    g = max(g, selected_color[1] + 80)  # 从100降到80
    b = max(b, selected_color[2] + 80)  # 从100降到80
    
    # 确保右侧颜色不会太亮
    r = min(r, 230)  # 限制最大亮度
    g = min(g, 230)  # 限制最大亮度
    b = min(b, 230)  # 限制最大亮度
    
    # 创建右侧浅色
    color2 = (r, g, b, selected_color[3])
    
    # 创建左右两个纯色图像
    left_image = Image.new("RGBA", (width, height), selected_color)
    right_image = Image.new("RGBA", (width, height), color2)
    
    # 创建渐变遮罩（从黑到白的横向线性渐变）
    mask = Image.new("L", (width, height), 0)
    mask_data = []
    
    # 生成遮罩数据，使用更加平滑的过渡
    for y in range(height):
        for x in range(width):
            # 计算从左到右的渐变值 (0-255)
            # 使用更加非线性的渐变，使左侧深色区域更大
            mask_value = int(255.0 * (x / width) ** 0.7)  # 从0.85改为0.7
            mask_data.append(mask_value)
    
    # 应用遮罩数据到遮罩图像
    mask.putdata(mask_data)
    
    # 使用遮罩合成左右两个图像
    # 遮罩中黑色部分(0)显示left_image，白色部分(255)显示right_image
    gradient = Image.composite(right_image, left_image, mask)
    
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
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
            
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
    将多张电影海报排列成三列，每列三张，然后将每列作为整体旋转并放在渐变背景上
    不再依赖外部模板文件，直接生成渐变背景
    """

    try:
        logger.info(
            f"[{config.JELLYFIN_CONFIG['SERVER_NAME']}][{name}] [3/4] 正在生成海报..."
        )
        logger.info("-" * 40)
        poster_folder = os.path.join(config.POSTER_FOLDER, name)
        first_image_path = os.path.join(poster_folder, "1.jpg")
        output_path = os.path.join(config.OUTPUT_FOLDER, f"{name}.png")
        rows = config.POSTER_GEN_CONFIG["ROWS"]
        cols = config.POSTER_GEN_CONFIG["COLS"]
        margin = config.POSTER_GEN_CONFIG["MARGIN"]
        corner_radius = config.POSTER_GEN_CONFIG["CORNER_RADIUS"]
        rotation_angle = config.POSTER_GEN_CONFIG["ROTATION_ANGLE"]
        start_x = config.POSTER_GEN_CONFIG["START_X"]
        start_y = config.POSTER_GEN_CONFIG["START_Y"]
        column_spacing = config.POSTER_GEN_CONFIG["COLUMN_SPACING"]
        save_columns = config.POSTER_GEN_CONFIG["SAVE_COLUMNS"]

        # 定义模板尺寸（可以根据需要调整）
        template_width = 1920  # 或者从配置中获取
        template_height = 1080  # 或者从配置中获取
        color=  get_poster_primary_color(first_image_path)
        # 创建渐变背景作为模板
        gradient_bg = create_gradient_background(template_width, template_height, name, color)


        # 创建保存中间文件的文件夹
        output_dir = os.path.dirname(output_path)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        columns_dir = os.path.join(output_dir, "columns")
        if save_columns and not os.path.exists(columns_dir):
            os.makedirs(columns_dir)

        # 支持的图片格式
        supported_formats = (".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp")
        # 自定义排序顺序,如果custom_order=123456789,则代表九宫格图第一列第一行(1,1)为1.jpg，第一列第二行(1,2)为2.jpg，第一列第三行(1,3)为3.jpg,(2,1)=4.jpg以此类推，(3,3)=9.jpg
        custom_order = "315426987"
        # 这个顺序是优先把最开始的两张图1.jpg和2.jpg放在最显眼的位置(1,2)和(2,2)，而最后一个9.jpg放在看不见的位置(3,1)
        order_map = {num: index for index, num in enumerate(custom_order)}

        # 获取并排序图片
        poster_files = sorted(
            [
                os.path.join(poster_folder, f)
                for f in os.listdir(poster_folder)
                if os.path.isfile(os.path.join(poster_folder, f))
                and f.lower().endswith(supported_formats)
                and os.path.splitext(f)[0]
                in order_map  # 文件名（不含扩展名）必须在自定义顺序里
            ],
            key=lambda x: order_map[os.path.splitext(os.path.basename(x))[0]],
        )

        # 确保至少有一张图片
        if not poster_files:
            logger.error(
                f"[{config.JELLYFIN_CONFIG['SERVER_NAME']}][{name}] 错误: 在 {poster_folder} 中没有找到支持的图片文件"
            )
            return False

        # 限制最多处理 rows*cols 张图片
        max_posters = rows * cols
        poster_files = poster_files[:max_posters]

        # 固定海报尺寸
        cell_width = config.POSTER_GEN_CONFIG["CELL_WIDTH"]
        cell_height = config.POSTER_GEN_CONFIG["CELL_HEIGHT"]

        # 将图片分成3组，每组3张
        grouped_posters = [
            poster_files[i : i + rows] for i in range(0, len(poster_files), rows)
        ]

        # 以渐变背景作为起点
        result = gradient_bg.copy()
        # 处理每一组（每一列）图片
        for col_index, column_posters in enumerate(grouped_posters):
            if col_index >= cols:
                break

            # 计算当前列的 x 坐标
            column_x = start_x + col_index * column_spacing

            # 计算当前列所有图片组合后的高度（包括间距）
            column_height = rows * cell_height + (rows - 1) * margin

            # 创建一个透明的画布用于当前列的所有图片，增加宽度以容纳右侧阴影
            shadow_extra_width = 20 + 20 * 2  # 右侧阴影需要的额外宽度
            shadow_extra_height = 20 + 20 * 2  # 底部阴影需要的额外高度

            # 修改列画布的尺寸，确保有足够空间容纳阴影
            column_image = Image.new(
                "RGBA",
                (cell_width + shadow_extra_width, column_height + shadow_extra_height),
                (0, 0, 0, 0),
            )

            # 在列画布上放置每张图片
            for row_index, poster_path in enumerate(column_posters):
                try:
                    # 打开海报
                    poster = Image.open(poster_path)

                    # 调整海报大小为固定尺寸
                    resized_poster = poster.resize(
                        (cell_width, cell_height), Image.LANCZOS
                    )

                    # 创建圆角遮罩（如果需要）
                    if corner_radius > 0:
                        # 创建一个透明的遮罩
                        mask = Image.new("L", (cell_width, cell_height), 0)

                        # 绘制圆角
                        from PIL import ImageDraw

                        draw = ImageDraw.Draw(mask)
                        draw.rounded_rectangle(
                            [(0, 0), (cell_width, cell_height)],
                            radius=corner_radius,
                            fill=255,
                        )

                        # 应用遮罩
                        poster_with_corners = Image.new(
                            "RGBA", resized_poster.size, (0, 0, 0, 0)
                        )
                        poster_with_corners.paste(resized_poster, (0, 0), mask)
                        resized_poster = poster_with_corners

                    # 添加阴影效果到每张海报
                    resized_poster_with_shadow = add_shadow(
                        resized_poster,
                        offset=(20, 20),  # 较大的偏移量
                        shadow_color=(
                            0,
                            0,
                            0,
                            255,
                        ),  # 更深的黑色，但不要超过255的透明度
                        blur_radius=20,  # 保持模糊半径
                    )

                    # 计算在列画布上的位置（垂直排列）
                    y_position = row_index * (cell_height + margin)
                    x_position = 0  # 一般为0，但在有阴影时可能需要调整

                    # 粘贴到列画布上时，不要减去偏移量，确保阴影有空间
                    column_image.paste(
                        resized_poster_with_shadow,
                        (0, y_position),  # 不减去偏移量，确保阴影有空间
                        resized_poster_with_shadow,
                    )

                except Exception as e:
                    logger.error(
                        f"[{config.JELLYFIN_CONFIG['SERVER_NAME']}][{name}] 处理图片 {os.path.basename(poster_path)} 时出错: {e}"
                    )
                    continue

            # 保存原始列图像（旋转前）
            if save_columns:
                column_orig_path = os.path.join(
                    columns_dir, f"{name}_column_{col_index+1}_original.png"
                )
                column_image.save(column_orig_path)
                logger.debug(
                    f"[{config.JELLYFIN_CONFIG['SERVER_NAME']}][{name}] 已保存原始列图像到: {column_orig_path}"
                )

            # 现在我们有了完整的一列图片，准备旋转它
            # 创建一个足够大的画布来容纳旋转后的列
            rotation_canvas_size = int(
                math.sqrt(
                    (cell_width + shadow_extra_width) ** 2
                    + (column_height + shadow_extra_height) ** 2
                )
                * 1.5
            )
            rotation_canvas = Image.new(
                "RGBA", (rotation_canvas_size, rotation_canvas_size), (0, 0, 0, 0)
            )

            # 将列图片放在旋转画布的中央
            paste_x = (rotation_canvas_size - cell_width) // 2
            paste_y = (rotation_canvas_size - column_height) // 2
            rotation_canvas.paste(column_image, (paste_x, paste_y), column_image)

            # 旋转整个列
            rotated_column = rotation_canvas.rotate(
                rotation_angle, Image.BICUBIC, expand=True
            )

            # 保存旋转后的列图像
            if save_columns:
                column_rotated_path = os.path.join(
                    columns_dir, f"column_{col_index+1}_rotated.png"
                )
                rotated_column.save(column_rotated_path)
                logger.debug(
                    f"[{config.JELLYFIN_CONFIG['SERVER_NAME']}][{name}] 已保存旋转后的列图像到: {column_rotated_path}"
                )

            # 计算列在模板上的位置（不同的列有不同的y起点）
            column_center_y = start_y + column_height // 2
            column_center_x = column_x

            # 根据列索引调整位置
            if col_index == 1:  # 中间列
                column_center_x += cell_width - 50
            elif col_index == 2:  # 右侧列
                column_center_y += -155
                column_center_x += (cell_width) * 2 - 40

            # 计算最终放置位置
            final_x = column_center_x - rotated_column.width // 2 + cell_width // 2
            final_y = column_center_y - rotated_column.height // 2

            # 粘贴旋转后的列到结果图像
            result.paste(rotated_column, (final_x, final_y), rotated_column)

        # 获取第一张图片的随机点颜色
        if poster_files:
            first_image_path = poster_files[0]
            random_color = get_random_color(first_image_path)
        else:
            # 如果没有图片，生成一个随机颜色
            random_color = (
                random.randint(50, 200),
                random.randint(50, 200),
                random.randint(50, 200),
                255,
            )

        # 根据name匹配template_mapping中的配置
        library_ch_name = name  # 默认使用输入的name作为中文名
        library_eng_name = ""  # 默认英文名为空

        # 查找匹配的模板配置
        matched_template = None
        for template in config.TEMPLATE_MAPPING:
            if template.get("library_name") == name:
                matched_template = template
                break

        # 如果找到匹配的模板配置，使用模板中的中英文名
        if matched_template:
            if "library_ch_name" in matched_template:
                library_ch_name = matched_template["library_ch_name"]
            if "library_eng_name" in matched_template:
                library_eng_name = matched_template["library_eng_name"]
        style_name = "style1"  # 假设我们需要获取的样式名称
        style_config = next(
            (style for style in config.STYLE_CONFIGS if style.get("style_name") == style_name),
            None
        )
        # 添加中文名文字
        fangzheng_font_path = os.path.join("myfont", style_config.get("style_ch_font"))
        result = draw_text_on_image(
            result, library_ch_name, (73.32, 427.34), fangzheng_font_path, "ch.ttf", 163
        )

        # 如果有英文名，才添加英文名文字
        if library_eng_name:
            # 动态调整字体大小，但统一使用一个字体大小
            base_font_size = 50  # 默认字体大小
            line_spacing = 5  # 行间距

            # 计算行数和调整字体大小
            word_count = len(library_eng_name.split())
            max_chars_per_line = max([len(word) for word in library_eng_name.split()])

            # 根据单词数量或最长单词长度调整字体大小
            if max_chars_per_line > 10 or word_count > 3:
                # 字体大小与文本长度成反比
                font_size = (
                    base_font_size
                    * (10 / max(max_chars_per_line, word_count * 3)) ** 0.8
                )
                # 设置最小字体大小限制，确保文字不会太小
                font_size = max(font_size, 30)
            else:
                font_size = base_font_size

            # 打印调试信息
            logger.debug(
                f"[{config.JELLYFIN_CONFIG['SERVER_NAME']}][{name}] 英文名 '{library_eng_name}' 单词数量: {word_count}, 最长单词长度: {max_chars_per_line}"
            )
            logger.debug(
                f"[{config.JELLYFIN_CONFIG['SERVER_NAME']}][{name}] 使用字体大小: {font_size:.2f}"
            )


            # 使用多行文本绘制
            melete_font_path = os.path.join("myfont", style_config.get("style_eng_font"))
            result, line_count = draw_multiline_text_on_image(
                result,
                library_eng_name,
                (124.68, 624.55),
                melete_font_path, "en.otf",
                int(font_size),
                line_spacing,
            )

            # 根据行数调整色块高度
            color_block_position = (84.38, 620.06)
            # 基础高度为55，每增加一行增加(font_size + line_spacing)的高度
            color_block_height = 55 + (line_count - 1) * (int(font_size) + line_spacing)
            color_block_size = (21.51, color_block_height)

            logger.debug(
                f"[{config.JELLYFIN_CONFIG['SERVER_NAME']}][{name}] 色块高度调整为: {color_block_height} (行数: {line_count})"
            )

            result = draw_color_block(
                result, color_block_position, color_block_size, random_color
            )
        # 保存结果
        result.save(output_path)
        logger.info(
            f"[{config.JELLYFIN_CONFIG['SERVER_NAME']}][{name}] 成功: 图片已保存到 {output_path}"
        )
        return True

    except Exception as e:
        logger.error(
            f"[{config.JELLYFIN_CONFIG['SERVER_NAME']}][{name}] 创建九宫格图片时出错: {e}",
            exc_info=True,
        )
        return False


if __name__ == "__main__":
    get_poster_primary_color(config.CURRENT_DIR  +"\\poster\\Hot TV\\1.jpg")
