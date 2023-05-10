ARG D4R6Y=
FROM ${D4R6Y}python:3.11.3-alpine3.17

ARG PIP_CONF=
RUN echo -e  $PIP_CONF > /etc/pip.conf

ARG APK_ARGS='http://dl-cdn.alpinelinux.org/alpine/v3.17/main\nhttp://dl-cdn.alpinelinux.org/alpine/v3.17/community'
RUN echo -e $APK_ARGS > /etc/apk/repositories

RUN apk add tzdata
ENV TZ=Europe/Paris

RUN addgroup -S portal
RUN adduser --disabled-password --gecos "" --home /home/portal --ingroup portal portal
RUN mkdir /opt/portal && chown portal:portal /opt/portal
WORKDIR /opt/portal

COPY --chown=portal:portal requirements.txt .
RUN python -m venv .py \
    && .py/bin/pip install --no-cache-dir -U pip \
    && .py/bin/pip install --no-cache-dir -r requirements.txt
COPY --chown=portal:portal setup.py setup.cfg MANIFEST.in ./
COPY --chown=portal:portal src/ src/
RUN .py/bin/pip install --no-cache-dir -e .

USER portal:portal
RUN mkdir prsite \
    && .py/bin/django-admin startproject prsite prsite \
    && echo -e "\nINSTALLED_APPS += ['bootstrap5','pr.portal']" >> prsite/prsite/settings.py \
    && echo -e "\nALLOWED_HOSTS=['*']" >> prsite/prsite/settings.py \
    && echo -e "\nfrom django.urls import include\nurlpatterns+=[path('pr/', include('pr.portal.urls'))]" >> prsite/prsite/urls.py \
    && .py/bin/python prsite/manage.py migrate

ENTRYPOINT [".py/bin/python", "prsite/manage.py"]
CMD ["runserver", "0.0.0.0:8080"]
