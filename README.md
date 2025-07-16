![Build Status](https://github.com/Botukh/foodgram/actions/workflows/main.yml/badge.svg?event=push)

«Фудграм» — сайт, на котором пользователи будут публиковать свои рецепты, добавлять чужие рецепты в избранное и подписываться на публикации других авторов. Зарегистрированным пользователям также будет доступен сервис «Список покупок». Он позволит создавать список продуктов, которые нужно купить для приготовления выбранных блюд.
 Разработка      | *Ботух Юлия*     | [Telegram](https://t.me/botuh) |
 
 ## Технологический стек

* **Python**
* **Django** + **Django REST Framework**
* **PostgreSQL**
* **Gunicorn** — WSGI-сервер
* **Nginx** — обратный прокси
* **Docker/ Docker Compose**
* CI/CD — **GitHub Actions** + **Docker Hub**

## Быстрый старт (без Docker, локально)

# 1 — Клонируем репозиторий
git clone https://github.com/Botukh/foodgram-project.git
cd foodgram-project

# 2 — Создаём и активируем вирт-окружение
python -m venv venv
source venv/bin/activate        Windows: venv\Scripts\activate

# 3 — Ставим зависимости
pip install -r requirements.txt

# 4 — Заполняем .env
cp .env.example .env

# 5 — Применяем миграции
python manage.py migrate

# 6 — Импортируем данные
python manage.py import_ingredients
python manage.py import_tags

# 6 — Создаём суперпользователя
python manage.py createsuperuser

# 7 — Запускаем сервер
python manage.py runserver


| Раздел              | URL                                                                  |
| ------------------- | -------------------------------------------------------------------- |
| Сервер           | [foodgamm.zapto.org](https://foodgamm.zapto.org)                     |
| Админка          | [foodgamm.zapto.org/admin/](https://foodgamm.zapto.org/admin/)       |
| Документация API | [foodgamm.zapto.org/api/docs/](https://foodgamm.zapto.org/api/docs/) |
