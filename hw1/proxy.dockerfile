FROM python:latest

COPY ./proxy_server.py .

CMD ["python", "proxy_server.py"]