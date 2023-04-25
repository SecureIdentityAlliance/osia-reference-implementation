ARG D4R6Y=
FROM ${D4R6Y}python:3.11.3-alpine3.17

ARG PIP_CONF=
RUN echo -e  $PIP_CONF > /etc/pip.conf

ARG APK_ARGS='http://dl-cdn.alpinelinux.org/alpine/v3.17/main\nhttp://dl-cdn.alpinelinux.org/alpine/v3.17/community'
RUN echo -e $APK_ARGS > /etc/apk/repositories

RUN apk add tzdata
ENV TZ=Europe/Paris

RUN addgroup -S uin
RUN adduser --disabled-password --gecos "" --home /home/uin --ingroup uin uin
RUN mkdir /opt/uin && chown uin:uin /opt/uin
RUN mkdir /opt/uin/conf && chown uin:uin /opt/uin/conf
WORKDIR /opt/uin

COPY --chown=uin:uin requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY --chown=uin:uin src/ ./
USER uin:uin
ENTRYPOINT ["python", "-m", "uin"]

