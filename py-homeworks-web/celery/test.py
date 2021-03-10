import os

from flask import Flask
from flask import request
from flask.views import MethodView
from flask import jsonify
from celery import Celery
from celery.result import AsyncResult


app = Flask('test')
celery = Celery(app.name, backend='redis://localhost:6379/3', broker='redis://localhost:6379/4')
celery.conf.update(app.config)


class ContextTask(celery.Task):
    def __call__(self, *args, **kwargs):
        with app.app_context():
            return self.run(*args, **kwargs)


celery.Task = ContextTask


@celery.task()
def send_email(a, b):
    return a + b


class Comparison(MethodView):

    def get(self, task_id):
        task = AsyncResult(task_id, app=celery)
        return jsonify({'status': task.status,
                        'result': task.result})

    def post(self, user_id):
        task = send_email.delay(3, 4)
        print(task.status)
        print(task.result)
        return jsonify({'tasks_id': task.id})


comparison_view = Comparison.as_view('comparison')
app.add_url_rule('/email/<string:task_id>', view_func=comparison_view, methods=['GET'])
app.add_url_rule('/email-send/<int:user_id>', view_func=comparison_view, methods=['POST'])



#
#
# @app.route('/email/<string:task_id>', methods=['GET'])
# def get(task_id):
#     print(task_id)
#     task = celery.AsyncResult(task_id)
#     return jsonify({'status': task.status,
#                     'result': task.result})
#
#
# @app.route('/email-send/<int:user_id>', methods=['POST'])
# def post(user_id):
#     task = send_email.delay(3, 4)
#     print(task.status)
#     print(task.result)
#     return jsonify({'tasks_id': task.id})


if __name__ == '__main__':
    app.run()