FROM python:latest

RUN pip install --upgrade pip
RUN pip install avro
COPY test_server.py .
COPY serializers/avro_serializer.py .

CMD ["python", "test_server.py", "AVRO"]