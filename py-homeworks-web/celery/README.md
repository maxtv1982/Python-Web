# Домашнее задание к лекции «Docker»
docker-compose up -d

# подключаемся к контейнеру с flask приложением для запуска миграции.
docker exec -ti celery_app sh

    cd app
    flask db init
    export FLASK_APP=run.py
    flask db migrate -m "Initial migration"
    flask db upgrade

