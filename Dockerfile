FROM python:3.10-alpine

ARG REP_NAME="glowing-enigma"

WORKDIR /opt/

ENV LC_CTYPE='C.UTF-8'
ENV TZ='Asia/Tokyo'
ENV DEBIAN_FRONTEND=noninteractive

RUN set -x && \
    apk add --no-cache git && \
    cp /usr/share/zoneinfo/Asia/Tokyo /etc/localtime && \
    git clone https://github.com/being24/${REP_NAME}.git && \
    python3 -m pip install --no-cache-dir -r ./${REP_NAME}/requirements.txt && \
    apk del git  && \
    rm -rf /var/cache/apk/*  && \
    echo "Hello, ${REP_NAME} ready!"

CMD ["/opt/glowing-enigma/main.py"]