FROM python:3.12-alpine

WORKDIR /app

COPY . .

RUN apk update && apk upgrade && apk add git
RUN pip install -r requirements.txt

ENTRYPOINT ["python", "src/main.py"]
