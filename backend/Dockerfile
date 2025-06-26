FROM python:3.12

WORKDIR /app

COPY requirements.txt .

COPY data/ ./data/

RUN pip install -r requirements.txt --no-cache-dir

COPY . .

RUN python manage.py collectstatic --noinput

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "foodgram.wsgi:application"]