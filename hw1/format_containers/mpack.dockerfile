FROM python:latest

RUN pip install --upgrade pip
RUN pip install msgpack
COPY test_server.py .
COPY serializers/mpack_serializer.py .

CMD ["python", "test_server.py", "MPACK"]