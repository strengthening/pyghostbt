FROM python:alpine

RUN mkdir -p /python/src/github.com/strengthening/pyghostbt
COPY . /python/src/github.com/strengthening/pyghostbt
