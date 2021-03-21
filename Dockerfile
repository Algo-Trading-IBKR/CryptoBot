FROM python:3.7-buster

WORKDIR /app

COPY . .

RUN ./install.sh

ENTRYPOINT [ "python", "NoStopLossV4.py" ]