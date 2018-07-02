FROM python:3.4-alpine
MAINTAINER Nealyip

RUN apk --no-cache add git && \
    git clone https://github.com/nealyip/oauth2-playground.git /app

EXPOSE 8000 8080
WORKDIR /app

CMD ["/usr/local/bin/python", "index.py"]