# [---CUSTO---]
ARG D4R6Y=
FROM ${D4R6Y}python:3.14.6-alpine3.24

ARG PIP_CONF=
RUN echo -e  $PIP_CONF > /etc/pip.conf

ARG APK_ARGS='http://dl-cdn.alpinelinux.org/alpine/v3.24/main\nhttp://dl-cdn.alpinelinux.org/alpine/v3.24/community'
RUN echo -e $APK_ARGS > /etc/apk/repositories
# [---CUSTO---]

RUN apk add tzdata

RUN addgroup -S dashboard
RUN adduser --disabled-password --gecos "" --home /home/dashboard --ingroup dashboard dashboard
RUN mkdir /opt/dashboard && chown dashboard:dashboard /opt/dashboard
RUN mkdir /opt/dashboard/conf && chown dashboard:dashboard /opt/dashboard/conf
WORKDIR /opt/dashboard

COPY --chown=dashboard:dashboard requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY --chown=dashboard:dashboard dashboard.yaml .
USER dashboard:dashboard
ENTRYPOINT ["livemetrics-dashboard"]
CMD ["-i", "dashboard.yaml"]
