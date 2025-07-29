
import os
import logging
import datetime

import os
import requests
from notification.celery import app

@app.task(bind=True)
def request_confirmation(self,protocol,address,token,topicId, subscriptionId, policy):
    logging.info("request_confirmation: Parameters: %s",(protocol,address,token,policy) )
    countdown,max = [int(x) for x in policy.split(',')]

    # Build confirmation URL
    sub_url = os.environ.get("ROOT_URL","http://localhost:8080")
    if sub_url and sub_url[-1]=='/':
        sub_url += "v1/subscriptions/confirm"
    else:
        sub_url += "/v1/subscriptions/confirm"

    # Build the message
    m = dict(type="SubscriptionConfirmation",
             token=token,
             topic=topicId,
             message="",
             messageId="",
             subject="",
             confirmURL=sub_url,
             timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat())
    # headers
    h = {
        'Message-Type': 'SubscriptionConfirmation',
        'Subscription-Id': subscriptionId,
        'Message-Id': "",
        'Topic-Id': topicId
    }
    try:
        with requests.post(address, headers=h, json=m) as r:
            r.raise_for_status()
    except Exception as exc2:
        # error while sending the result
        logging.exception("Unable to send the request for confirmation - will retry later")
        raise self.retry(countdown=countdown,max_retries=max,exc=exc2)

@app.task(bind=True)
def notify(self,protocol,address,subject,body,topicId, subscriptionId,policy):
    logging.debug("Notify: Parameters: %s",(protocol, address, subject,body,policy) )
    countdown,max = [int(x) for x in policy.split(',')]
    # Build the message
    m = dict(type="Notification",
             topic=topicId,
             message=body,
             messageId="",
             subject=subject,
             timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat())
    # headers
    h = {
        'Message-Type': 'Notification',
        'Subscription-Id': subscriptionId,
        'Message-Id': "",
        'Topic-Id': topicId
    }
    try:
        with requests.post(address,headers=h, json=m) as r:
            r.raise_for_status()
    except Exception as exc2:
        # error while sending the result
        logging.exception("Unable to send the notification - will retry later")
        raise self.retry(countdown=countdown,max_retries=max,exc=exc2)

