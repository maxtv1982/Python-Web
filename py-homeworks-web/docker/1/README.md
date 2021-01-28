# Домашнее задание к лекции «Docker»
## Задание 1  
По аналогии с практикой из лекции создайте свой docker image с http сервером nginx. Замените страницу приветсвия Nginx на своё (измените текст приветствия на той же странице). 


<details><summary>Подсказки: </summary>  
В официальном образе nginx стандартный путь к статичным файлам `/usr/share/nginx/html`.  
</details>  

На проверку присылается GitHub репозиторий с Dockerfile и статичными файлами для него.    
  > Для пользовательского html можно использовать пример в [каталоге](html/) с ДЗ.
  
 
docker pull nginx   # скачиваем образ, в рабочей директории создаем папку 1, в которую скопировал папку html c index.html, в папке 1 создаем Dockerfile
docker build -t my-nginx  docker-test  # создаём свой образ на основе Dockerfile
docker run --name my-nginx-server -d -p 8090:80 my-nginx  # запускаем контейнер
# проверяем localhost:8090