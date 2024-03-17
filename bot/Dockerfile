FROM rust:latest as swww-builder
RUN apt update
RUN apt install -y liblz4-dev
RUN cargo install --git https://github.com/LGFae/swww.git swww
RUN cargo install --git https://github.com/LGFae/swww.git swww-daemon

FROM python:3.12-slim
WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . .
copy --from=swww-builder /usr/local/cargo/bin/swww /usr/local/bin/swww
copy --from=swww-builder /usr/local/cargo/bin/swww-daemon /usr/local/bin/swww-daemon

CMD ["python", "main.py"]
