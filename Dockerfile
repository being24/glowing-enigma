FROM python:3.10-slim-bullseye

ARG REP_NAME="glowing-enigma"

WORKDIR /opt/

ENV LC_CTYPE='C.UTF-8'
ENV TZ='Asia/Tokyo'
ENV DEBIAN_FRONTEND=noninteractive

RUN set -x && \
    apt-get update && \
    apt-get upgrade && \
    apt-get install --no-install-recommends git -y && \
    cp /usr/share/zoneinfo/Asia/Tokyo /etc/localtime && \
    git clone https://github.com/being24/${REP_NAME}.git && \
    python3 -m pip install --no-cache-dir -r ./${REP_NAME}/requirements.txt && \
    apt-get purge -y git && \
    apt-get autoremove -y && \
    apt-get autoclean -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    echo "Hello, ${REP_NAME} ready!"

CMD ["/opt/glowing-enigma/main.py"]