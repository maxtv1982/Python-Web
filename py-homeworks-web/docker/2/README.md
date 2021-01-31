# Домашнее задание к лекции «Docker»

## Задание 2  
Создайте контейнер для REST API сервера из решения ДЗ по теме «Flask»

1. Создайте типовой Docker-файл для запуска Python-приложения
2. Проверьте конфигурацию Flask на использование переменных окружения (environment)
3. Проверьте Docker-файл на передачу переменных окружения в Flask
4. Docker-контейнер запускается с приложением Flask

docker build -t my-flask 2   # создаём свой образ на основе Dockerfile
docker network create --driver=bridge --attachable flask-net  # создаём сеть
# При запуске контейнеров подключаемся к этой сети
docker run -dit --name flask-server -p 8900:5000 --network flask-net my-flask

docker run -it --name pg-docker -e POSTGRES_PASSWORD=1234 -e POSTGRES_USER=postgres -e POSTGRES_DB=flask_home -d -p 5432:5432 --network flask-net postgres
# подключаемся к контейнеру с flask приложением для запуска миграции.
docker exec -ti flask-server sh

    cd app
    
    flask db init
    
    export FLASK_APP=run.py
    
    flask db migrate -m "Initial migration"
    
    flask db upgrade
