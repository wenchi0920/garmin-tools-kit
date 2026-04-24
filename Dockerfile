# 使用 Python 3.10 slim 作為基礎鏡像
FROM python:3.10-slim

# 設定工作目錄
WORKDIR /app

# 防止 Python 產生 .pyc 檔案並強制即時輸出日誌
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 安裝基本依賴與時區工具
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libc6-dev \
    tzdata \
    vim \
    procps \
    git \
    && rm -rf /var/lib/apt/lists/*

# 設定時區為台北
ENV TZ=Asia/Taipei
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 建立 app 使用者與群組 (uid=1000, gid=1000)
RUN groupadd -g 1000 app && \
    useradd -u 1000 -g app -s /bin/bash -d /app app && \
    chown -R app:app /app

# 複製依賴文件並安裝
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製其餘專案文件並設定擁有者
COPY --chown=app:app . .

# 切換到 app 使用者
USER app

# 預設啟動守護排程器 (scheduler.py)
CMD ["python", "scheduler.py"]
