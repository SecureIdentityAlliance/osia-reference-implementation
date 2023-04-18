
# notification

In Linux::

    docker run -p 6379:6379 redis:7.0.9-alpine

in WSL::

    sudo apt install redis
    sudo service redis-server start

Start::

    python -m notification --redis-url=redis://localhost:6379
    celery -A notification worker -l INFO

Test::

    pytest tests/test_notification.py -v -s

Redis::

    redis-cli

