# 使用官方 Python 基础镜像
FROM python:3.13.3-slim-bookworm


# 设置代理环境变量（构建时使用）
ARG HTTP_PROXY
ARG HTTPS_PROXY
ENV http_proxy=$HTTP_PROXY
ENV https_proxy=$HTTPS_PROXY
# 设置环境变量禁用 Python 输出缓冲
ENV PYTHONUNBUFFERED=1

# 设置时区为中国标准时间
ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 设置工作目录
WORKDIR /app

# 创建必要的目录结构
RUN mkdir -p /app/poster /app/output /app/font /app/myfont

# 复制主要Python文件
COPY *.py /app/

# 复制配置文件
COPY config/config.json /app/config/config.json

COPY font/* /app/font/
# 复制其他必要文件
COPY requirements.txt /app/
COPY README.md /app/

# 复制启动脚本
COPY start.sh /app/
RUN chmod +x /app/start.sh

# 使用代理安装依赖项
RUN  pip install -i https://pypi.tuna.tsinghua.edu.cn/simple/ --trusted-host pypi.tuna.tsinghua.edu.cn -r requirements.txt

# 清除代理设置（如果不需要在运行时使用）
ENV http_proxy=
ENV https_proxy=

# 使用启动脚本运行程序
CMD ["/app/start.sh"]