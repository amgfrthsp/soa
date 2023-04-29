FROM python:latest

RUN pip install --upgrade pip
RUN pip install xml_marshaller
COPY test_server.py .
COPY serializers/xml_serializer.py .

CMD ["python", "test_server.py", "XML"]