FROM python:3.8-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libgmp-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# 安装Python依赖
RUN pip install gevent charm-crypto pycryptodome

# 复制项目代码
COPY . .

# 设置环境变量
ENV PYTHONPATH=/app/adaptive/commoncoin:/app/adaptive/ecdsa:/app/adaptive/threshenc:/app/adaptive/core:/app/adaptive
ENV LIBRARY_PATH=/usr/lib/x86_64-linux-gnu:$LIBRARY_PATH
ENV LD_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH

# 默认命令（standalone模式）
CMD ["python3", "-m", "adaptive.test.honest_party_test", "-k", "thsig4_1.keys", "-e", "ecdsa.keys", "-b", "100", "-n", "4", "-t", "1", "-c", "thenc4_1.keys"]