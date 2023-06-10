pip install -r requirements.txt

python3 -m grpc_tools.protoc --proto_path=. ./proto/server.proto --python_out=. --grpc_python_out=.

docker-compose build
docker-compose up