# [---CUSTO---]
ARG D4R6Y=
FROM ${D4R6Y}python:3.14.6-alpine3.24

ARG PIP_CONF=
RUN echo -e  $PIP_CONF > /etc/pip.conf

ARG APK_ARGS='http://dl-cdn.alpinelinux.org/alpine/v3.24/main\nhttp://dl-cdn.alpinelinux.org/alpine/v3.24/community'
RUN echo -e $APK_ARGS > /etc/apk/repositories
# [---CUSTO---]

RUN apk add tzdata

RUN addgroup -S cms
RUN adduser --disabled-password --gecos "" --home /home/cms --ingroup cms cms
RUN mkdir /opt/cms && chown cms:cms /opt/cms
RUN mkdir /opt/cms/conf && chown cms:cms /opt/cms/conf
WORKDIR /opt/cms

COPY --chown=cms:cms requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY --chown=cms:cms src/ ./
USER cms:cms
ENTRYPOINT ["python", "-m", "cms"]
