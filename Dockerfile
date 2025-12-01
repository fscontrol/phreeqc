# Используем тот же базовый образ
FROM python:3.11-slim

# --- 1. Установка uv ---
# Копируем бинарник uv из официального образа (самый надежный способ)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Настраиваем переменные для uv
# UV_COMPILE_BYTECODE=1 — компилирует .pyc файлы сразу (ускоряет старт)
# UV_LINK_MODE=copy — копирует файлы вместо хардлинков (надежнее в Docker)
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# --- 2. Системные зависимости и IPhreeqc ---
WORKDIR /opt

# Устанавливаем инструменты сборки (нужны для компиляции IPhreeqc)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        wget \
        ca-certificates && \
    #
    # Скачивание и сборка IPhreeqc
    #
    mkdir -p /opt/iphreeqc && \
    cd /opt/iphreeqc && \
    wget https://water.usgs.gov/water-resources/software/PHREEQC/iphreeqc-3.8.6-17100.tar.gz -O iphreeqc.tar.gz && \
    tar -xzf iphreeqc.tar.gz && \
    cd iphreeqc-3.8.6-17100 && \
    mkdir build && cd build && \
    ../configure --prefix=/usr/local && \
    make -j4 && \
    make install && \
    #
    # Настройка базы данных и библиотек
    #
    mkdir -p /usr/local/share/phreeqc && \
    cp ../database/phreeqc.dat /usr/local/share/phreeqc/phreeqc.dat && \
    ldconfig && \
    #
    # Очистка мусора (удаляем исходники и кэш apt)
    #
    cd / && rm -rf /opt/iphreeqc && \
    apt-get remove -y build-essential wget && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

# --- 3. Установка Python-зависимостей через uv ---
WORKDIR /app
ENV UV_PROJECT_ENVIRONMENT="/opt/venv"
# Сначала копируем только файлы проекта, чтобы кэшировать слои Docker
COPY pyproject.toml .
# Если у вас есть uv.lock, раскомментируйте строку ниже:
# COPY uv.lock .

# Создаем venv и устанавливаем зависимости.
# --no-dev: не ставить пакеты для разработки
# --no-install-project: не ставить сам текущий проект как пакет (если это просто скрипт)
RUN uv sync --frozen --no-install-project || uv pip install -r pyproject.toml --system

# Копируем остальной код
COPY . /app

# Добавляем venv в PATH, чтобы можно было писать просто python или uvicorn
# uv создает venv в папке .venv по умолчанию
ENV PATH="/app/.venv/bin:$PATH"

# --- 4. Запуск ---
# Можно запускать через `uv run`, что гарантирует актуальность среды
CMD ["uv", "run", "main.py"]