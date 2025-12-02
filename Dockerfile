FROM python:3.13-slim AS builder-c
WORKDIR /src
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential wget ca-certificates && \
    rm -rf /var/lib/apt/lists/*

RUN wget https://water.usgs.gov/water-resources/software/PHREEQC/iphreeqc-3.8.6-17100.tar.gz && \
    tar -xzf iphreeqc-3.8.6-17100.tar.gz && \
    cd iphreeqc-3.8.6-17100 && \
    mkdir build && cd build && \
    ../configure --prefix=/usr/local && \
    make -j4 && make install

RUN mkdir -p /usr/local/share/phreeqc && \
    cp iphreeqc-3.8.6-17100/database/phreeqc.dat /usr/local/share/phreeqc/

FROM python:3.13-slim AS builder-py
WORKDIR /app

RUN apt-get update 
RUN apt-get install -y --no-install-recommends build-essential
RUN rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN python -m venv /opt/venv
RUN /opt/venv/bin/pip install --upgrade pip
RUN /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

FROM python:3.13-slim

WORKDIR /app

# install runtime-only deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Copy IPhreeqc library
COPY --from=builder-c /usr/local/lib/libiphreeqc* /usr/local/lib/
COPY --from=builder-c /usr/local/include/ /usr/local/include/
COPY --from=builder-c /usr/local/share/phreeqc /usr/local/share/phreeqc
RUN ldconfig

# Copy Python venv from builder-py
COPY --from=builder-py /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy source code
COPY . /app

EXPOSE 8000
CMD ["python", "main.py"]
