FROM python:3.13-slim AS builder-c
WORKDIR /opt/iphreeqc
RUN apt-get update 
RUN apt-get install -y --no-install-recommends build-essential wget ca-certificates
RUN rm -rf /var/lib/apt/lists/*
RUN wget https://water.usgs.gov/water-resources/software/PHREEQC/iphreeqc-3.8.6-17100.tar.gz -O iphreeqc.tar.gz
RUN tar -xzf iphreeqc.tar.gz
WORKDIR /opt/iphreeqc/iphreeqc-3.8.6-17100
RUN mkdir build 
WORKDIR /opt/iphreeqc/iphreeqc-3.8.6-17100/build
RUN ../configure --prefix=/usr/local
RUN make -j4 && make install
RUN mkdir -p /usr/local/share/phreeqc
RUN cp ../database/phreeqc.dat /usr/local/share/phreeqc/phreeqc.dat

FROM python:3.13-slim
WORKDIR /app
RUN apt-get update 
RUN apt-get install -y --no-install-recommends build-essential ca-certificates
COPY --from=builder-c /usr/local/lib/libiphreeqc* /usr/local/lib/
COPY --from=builder-c /usr/local/include/ /usr/local/include/
COPY --from=builder-c /usr/local/share/phreeqc /usr/local/share/phreeqc
RUN ldconfig
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
RUN apt-get purge -y build-essential 
RUN apt-get autoremove -y 
RUN rm -rf /var/lib/apt/lists/*
COPY . /app
EXPOSE 8000
CMD ["python", "main.py"]
