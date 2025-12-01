FROM python:3.13-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy
WORKDIR /opt
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        wget \
        ca-certificates && \
    mkdir -p /opt/iphreeqc && \
    cd /opt/iphreeqc && \
    wget https://water.usgs.gov/water-resources/software/PHREEQC/iphreeqc-3.8.6-17100.tar.gz -O iphreeqc.tar.gz && \
    tar -xzf iphreeqc.tar.gz && \
    cd iphreeqc-3.8.6-17100 && \
    mkdir build && cd build && \
    ../configure --prefix=/usr/local && \
    make -j4 && \
    make install && \
    mkdir -p /usr/local/share/phreeqc && \
    cp ../database/phreeqc.dat /usr/local/share/phreeqc/phreeqc.dat && \
    ldconfig && \
    cd / && rm -rf /opt/iphreeqc && \
    apt-get remove -y build-essential wget && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*
WORKDIR /app
ENV UV_PROJECT_ENVIRONMENT="/opt/venv"
COPY pyproject.toml .
RUN uv sync --frozen --no-install-project || uv pip install -r pyproject.toml --system
COPY . /app
ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8000
CMD ["uv", "run", "main.py"]