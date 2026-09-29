# [---CUSTO---]
ARG D4R6Y=
FROM ${D4R6Y}python:3.14.6-alpine3.24

ARG PIP_CONF=
RUN echo -e  $PIP_CONF > /etc/pip.conf

ARG APK_ARGS='http://dl-cdn.alpinelinux.org/alpine/v3.24/main\nhttp://dl-cdn.alpinelinux.org/alpine/v3.24/community'
RUN echo -e $APK_ARGS > /etc/apk/repositories
# [---CUSTO---]

RUN apk add tzdata

RUN addgroup -S abis
RUN adduser --disabled-password --gecos "" --home /home/abis --ingroup abis abis
RUN mkdir /opt/abis && chown abis:abis /opt/abis
RUN mkdir /opt/abis/conf && chown abis:abis /opt/abis/conf
WORKDIR /opt/abis

COPY --chown=abis:abis requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY --chown=abis:abis src/ ./
USER abis:abis
ENTRYPOINT ["python", "-m", "abis"]
