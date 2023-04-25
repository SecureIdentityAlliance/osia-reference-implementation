ARG D4R6Y=
FROM ${D4R6Y}python:3.11.3-alpine3.17

ARG PIP_CONF=
RUN echo -e  $PIP_CONF > /etc/pip.conf

ARG APK_ARGS='http://dl-cdn.alpinelinux.org/alpine/v3.17/main\nhttp://dl-cdn.alpinelinux.org/alpine/v3.17/community'
RUN echo -e $APK_ARGS > /etc/apk/repositories

RUN apk add tzdata
ENV TZ=Europe/Paris

RUN addgroup -S orchestrator
RUN adduser --disabled-password --gecos "" --home /home/orchestrator --ingroup orchestrator orchestrator
RUN mkdir /opt/orchestrator && chown orchestrator:orchestrator /opt/orchestrator
RUN mkdir /opt/orchestrator/conf && chown orchestrator:orchestrator /opt/orchestrator/conf
WORKDIR /opt/orchestrator

COPY --chown=orchestrator:orchestrator requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY --chown=orchestrator:orchestrator src/ ./
ADD --chown=orchestrator:orchestrator ./supervisord.conf ./supervisord.conf

USER orchestrator:orchestrator
ENTRYPOINT ["supervisord"]
