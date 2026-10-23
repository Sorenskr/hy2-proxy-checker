FROM python:3.11-slim

# 安装下载工具
RUN apt-get update && apt-get install -y curl tar ca-certificates && rm -rf /var/lib/apt/lists/*

# 下载 Linux amd64 版 sing-box 并解压到系统路径
RUN curl -Lo /tmp/sing-box.tar.gz https://github.com/SagerNet/sing-box/releases/latest/download/sing-box-1.9.0-linux-amd64.tar.gz \
    && tar -zxvf /tmp/sing-box.tar.gz -C /tmp \
    && mv /tmp/sing-box-*/sing-box /usr/local/bin/sing-box \
    && chmod +x /usr/local/bin/sing-box \
    && rm -rf /tmp/sing-box*

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY . .

# 暴露 Render 默认端口
EXPOSE 10000

# 启动服务
CMD ["python", "main.py"]