# «Фудграм» — сайт, на котором пользователи могут публиковать свои рецепты, добавлять чужие рецепты в избранное и подписываться на публикации других авторов. Зарегистрированным пользователям также доступен сервис «Список покупок». Он позволит создавать список продуктов, которые нужно купить для приготовления выбранных блюд.

# С сайтом можно ознакомиться тут:
https://pet-foodgram.ddns.net/

## Иcпользованные технологии:
### Backend:
- Django
- DRF
- Gunicorn
- Djoser
- Pillow

### Server:
- Nginx

### CI/CD:
- Docker
- Docker compose
- Github Workflow

### DB:
- PostgreSQL

## Как развернуть проект на сервере linux
Скачайте docker-compose.yml из [репозитория](https://github.com/NRmously/foodgram)

Создайте файл с переменными окружения с названием .env и наполните его своими данными:
```
touch .env
```

Пример заполнения:
```
POSTGRES_USER=user
POSTGRES_PASSWORD=password
POSTGRES_DB=django
DB_HOST=db
DB_PORT=5432
SECRET_KEY=django-insecure-cg6*%6d51ef8f#4!r3*$vmxm4)abgAgfasgasf
ALLOWED_HOSTS=127.0.0.1,localhost,923.223.70.175,pet-kittygram.ddns.net
DEBUG=True
# Что бы использовать sqlite - раскомментируйте строку ниже
# USE_SQLITE=1
```

Запустите Docker compose:
```
sudo docker compose -f docker-compose.yml pull
sudo docker compose -f docker-compose.yml down
sudo docker compose -f docker-compose.yml up -d
```

Примените миграции и соберите статику:
```
sudo docker compose -f docker-compose.yml exec backend python manage.py migrate
sudo docker compose -f docker-compose.yml exec backend python manage.py collectstatic
sudo docker compose -f docker-compose.yml exec backend cp -r /app/collected_static/. /backend_static/static/
```

Для автодеплоя на гитхабе нужно добавить перменные в Secrets на гитхабе:
```
DOCKER_PASSWORD - пароль от Docker Hub
DOCKER_USERNAME - имя пользователя Docker Hub
HOST - ip сервера
SSH_KEY - ключ ssh для доступа к удаленному серверу
SSH_PASSPHRASE - пароль ssh
TELEGRAM_TO - id пользователя TELEGRAM
TELEGRAM_TOKEN - TELEGRAM токен
USER - имя пользователя сервера
```

## Автор [NRmously](https://github.com/NRmously)