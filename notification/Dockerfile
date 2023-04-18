FROM python:3.11.3-alpine3.17

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

