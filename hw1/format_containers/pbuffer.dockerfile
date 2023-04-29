FROM python:latest

RUN pip install --upgrade pip
RUN pip install protobuf grpcio grpcio-tools
COPY serializers/data.proto .
COPY serializers/pbuffer_serializer.py .
RUN python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. data.proto
COPY test_server.py .
CMD ["python", "test_server.py", "PBUFFER"]