FROM python:3.11.3-alpine3.17

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
