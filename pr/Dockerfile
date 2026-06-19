# [---CUSTO---]
FROM python:3.13.1-alpine3.21
# [---CUSTO---]

RUN apk add tzdata

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
