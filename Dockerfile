FROM python:3.11-alpine3.21
WORKDIR /memo

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

COPY . .

RUN mkdir -p src/logs /data/www/html && \
    chmod 777 /data && \
    touch /data/www/html/index.html

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]