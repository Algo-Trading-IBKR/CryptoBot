FROM debian:buster-slim as base

RUN apt update && apt install wget make gcc -y
RUN wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz \
&& tar -xzf ta-lib-0.4.0-src.tar.gz \
&& cd ta-lib/ \
&& wget 'http://git.savannah.gnu.org/gitweb/?p=config.git;a=blob_plain;f=config.guess;hb=HEAD' -O config.guess \
&& wget 'http://git.savannah.gnu.org/gitweb/?p=config.git;a=blob_plain;f=config.sub;hb=HEAD' -O config.sub \
&& ./configure --prefix=/usr \
&& make \
&& make install

FROM python:3.7-buster as cryptobot

# copy the built binaries of ta-lib to our main image
COPY --from=base /usr/ /usr/

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt

COPY . .

ENTRYPOINT [ "python", "-u", "main.py" ]
