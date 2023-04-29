FROM python:latest

RUN pip install --upgrade pip
RUN pip install pyyaml
COPY test_server.py .
COPY serializers/yaml_serializer.py .

CMD ["python", "test_server.py", "YAML"]