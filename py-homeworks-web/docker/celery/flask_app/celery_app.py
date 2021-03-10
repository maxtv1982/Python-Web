from flask_mail import Message
from app import app, mail
from models import Users
import errors

import os
from celery import Celery

CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://redis'),
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://redis')

celery = Celery('workerA', broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)


class ContextTask(celery.Task):
    def __call__(self, *args, **kwargs):
        with app.app_context():
            return self.run(*args, **kwargs)


celery.Task = ContextTask


# def get_mail(user_id):
#     obj = Users.query.get(user_id)
#     if obj:
#         email = obj.email
#         return email
#     else:
#         raise errors.NotFound


@celery.task()
def send_email(email):
    msg = Message('Hello', sender="maxtv@mail.ru", recipients=[email])
    msg.body = "testing"
    msg.html = "<b>testing</b>"
    mail.send(msg)
