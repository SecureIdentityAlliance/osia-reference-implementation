ARG D4R6Y=
FROM ${D4R6Y}python:3.11.3-alpine3.17

ARG PIP_CONF=
RUN echo -e  $PIP_CONF > /etc/pip.conf

ARG APK_ARGS='http://dl-cdn.alpinelinux.org/alpine/v3.17/main\nhttp://dl-cdn.alpinelinux.org/alpine/v3.17/community'
RUN echo -e $APK_ARGS > /etc/apk/repositories

RUN apk add tzdata
ENV TZ=Europe/Paris

RUN addgroup -S pr
RUN adduser --disabled-password --gecos "" --home /home/pr --ingroup pr pr
RUN mkdir /opt/pr && chown pr:pr /opt/pr
RUN mkdir /opt/pr/conf && chown pr:pr /opt/pr/conf
WORKDIR /opt/pr

COPY --chown=pr:pr requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY --chown=pr:pr src/ ./
USER pr:pr
ENTRYPOINT ["python", "-m", "pr"]
