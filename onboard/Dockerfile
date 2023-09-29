FROM alpine:3.14
RUN apk add --no-cache python3 python3-dev py3-pip build-base linux-headers libffi-dev openssh busybox-extras

ADD requirements.txt /requirements.txt

RUN if [ -z "$HTTPS_PROXY" ] ;\
    then pip3 install --upgrade pip ;\
    else pip3 install --proxy $HTTPS_PROXY --upgrade pip ;\
    fi
RUN if [ -z "$HTTPS_PROXY" ] ;\
    then pip3 install -r /requirements.txt ;\
    else pip3 install --proxy $HTTPS_PROXY -r /requirements.txt ;\
    fi