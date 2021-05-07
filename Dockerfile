FROM yimura/pytalib

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt

COPY . .

ENTRYPOINT [ "python", "CryptoBotV2-Test.py" ]
