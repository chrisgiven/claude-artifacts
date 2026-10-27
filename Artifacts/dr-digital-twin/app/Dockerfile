FROM python:3.12-alpine
RUN pip install --no-cache-dir "psycopg[binary]>=3.2,<4"
WORKDIR /srv
COPY app.py lb.py ./
EXPOSE 8000 8080
CMD ["python", "app.py"]
