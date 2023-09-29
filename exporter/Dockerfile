FROM python:3.9-slim

ARG HTTPS_PROXY

ENV http_proxy $HTTPS_PROXY
ENV https_proxy $HTTPS_PROXY

RUN apt-get update && apt-get install --no-install-recommends -y ssh \
    && rm -rf /var/lib/apt/lists/*

ADD . /exporter

COPY build.sh .
RUN --mount=type=cache,target=/root/.cache ./build.sh

WORKDIR /exporter