FROM python:3.11.3-alpine3.17

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
