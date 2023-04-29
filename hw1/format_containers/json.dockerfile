FROM python:latest

RUN pip install --upgrade pip

COPY test_server.py .
COPY serializers/json_serializer.py .
CMD ["python", "test_server.py", "JSON"]