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

# 複製依賴文件並安裝
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製其餘專案文件
COPY . .

# 設定執行權限
RUN chmod +x /app/backup.sh

# 預設啟動守護排程器 (scheduler.py)
CMD ["python", "scheduler.py"]
