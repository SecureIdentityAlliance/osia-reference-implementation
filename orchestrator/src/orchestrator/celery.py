from celery import Celery
import celery.app.log
import os
import logging

app = Celery('orchestrator',
             broker=os.environ.get("REDIS_URL",'redis://localhost:6379/1'),
             backend=os.environ.get("REDIS_URL",'redis://localhost:6379/1'),
             include=['orchestrator.tasks'])

app.conf.task_acks_late = True
app.conf.task_reject_on_worker_lost = True

celery.app.log.Logging(app).get_default_logger().setLevel(logging.WARNING)

if __name__ == '__main__':
    app.start()