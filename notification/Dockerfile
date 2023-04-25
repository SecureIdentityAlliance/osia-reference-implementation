ARG D4R6Y=
FROM ${D4R6Y}python:3.11.3-alpine3.17

ARG PIP_CONF=
RUN echo -e  $PIP_CONF > /etc/pip.conf

ARG APK_ARGS='http://dl-cdn.alpinelinux.org/alpine/v3.17/main\nhttp://dl-cdn.alpinelinux.org/alpine/v3.17/community'
RUN echo -e $APK_ARGS > /etc/apk/repositories

RUN apk add tzdata
ENV TZ=Europe/Paris

RUN addgroup -S notification
RUN adduser --disabled-password --gecos "" --home /home/notification --ingroup notification notification
RUN mkdir /opt/notification && chown notification:notification /opt/notification
RUN mkdir /opt/notification/conf && chown notification:notification /opt/notification/conf
WORKDIR /opt/notification

COPY --chown=notification:notification requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY --chown=notification:notification src/ ./
ADD --chown=notification:notification ./supervisord.conf ./supervisord.conf

USER notification:notification
ENTRYPOINT ["supervisord"]

