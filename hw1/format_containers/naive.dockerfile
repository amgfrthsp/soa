FROM python:latest

COPY test_server.py .
COPY serializers/naive_serializer.py .

CMD ["python", "test_server.py", "NAIVE"]