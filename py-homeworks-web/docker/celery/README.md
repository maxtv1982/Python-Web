# Домашнее задание к лекции «Celery»

1. создан файл celery_app.py 
2. добавлены вьюхи и роуты во views.py 

# запускаем
docker-compose up -d

# подключаемся к контейнеру с flask приложением для запуска миграции и celery.
docker exec -ti celery_flask_app_1 sh

    cd app
    flask db init
    export FLASK_APP=run.py
    flask db migrate -m "Initial migration"
    flask db upgrade

# запускаем celery
    celery -A celery_app.celery worker --loglevel=info