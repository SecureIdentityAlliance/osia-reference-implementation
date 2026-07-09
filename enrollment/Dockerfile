# [---CUSTO---]
ARG D4R6Y=
FROM ${D4R6Y}python:3.14.6-alpine3.24

ARG PIP_CONF=
RUN echo -e  $PIP_CONF > /etc/pip.conf

ARG APK_ARGS='http://dl-cdn.alpinelinux.org/alpine/v3.24/main\nhttp://dl-cdn.alpinelinux.org/alpine/v3.24/community'
RUN echo -e $APK_ARGS > /etc/apk/repositories
# [---CUSTO---]

RUN apk add tzdata

RUN addgroup -S enrollment
RUN adduser --disabled-password --gecos "" --home /home/enrollment --ingroup enrollment enrollment
RUN mkdir /opt/enrollment && chown enrollment:enrollment /opt/enrollment
RUN mkdir /opt/enrollment/conf && chown enrollment:enrollment /opt/enrollment/conf
WORKDIR /opt/enrollment

COPY --chown=enrollment:enrollment requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY --chown=enrollment:enrollment src/ ./
COPY --chown=enrollment:enrollment conf/* ./conf/
USER enrollment:enrollment
ENTRYPOINT ["python", "-m", "enrollment"]
