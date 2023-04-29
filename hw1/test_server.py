import os
import random
import socket
import string
import sys
import time


def generate_data():
    house = dict()
    house['name'] = gen_random_string(15)
    house['materials'] = gen_materials()
    house['owners'] = gen_owners()
    house['year_built'] = gen_random_int()
    house['square'] = gen_random_float()
    return house


def gen_owners():
    owners = dict()
    for _ in range(8):
        name = gen_random_string(10)
        year = gen_random_int()
        owners[name] = year
    return owners


def gen_materials():
    materials = []
    for _ in range(7):
        materials.append(gen_random_string(7))
    return materials


def gen_random_string(length):
    return ''.join(random.choices(
        string.ascii_letters + string.digits, k=length))


def gen_random_int():
    return random.randint(0, 2023)


def gen_random_float():
    return random.uniform(1000, 1000000)


def handle_request(format_name):
    data = generate_data()

    match format_name:
        case 'NAIVE':
            from naive_serializer import NaiveSerializer
            serializer = NaiveSerializer()
        case 'AVRO':
            from avro_serializer import AvroSerializer
            serializer = AvroSerializer()
        case 'JSON':
            from json_serializer import JSONSerializer
            serializer = JSONSerializer()
        case 'PBUFFER':
            from pbuffer_serializer import PBufferSerializer
            serializer = PBufferSerializer()
        case 'MPACK':
            from mpack_serializer import MessagePackSerializer
            serializer = MessagePackSerializer()
        case 'YAML':
            from yaml_serializer import YAMLSerializer
            serializer = YAMLSerializer()
        case 'XML':
            from xml_serializer import XMLSerializer
            serializer = XMLSerializer()

    start_time = time.time()
    serialized_data = serializer.serialize(data)
    serialization_time = time.time() - start_time

    start_time = time.time()
    _ = serializer.deserialize(serialized_data)
    deserialization_time = time.time() - start_time

    return f"{format_name} - {sys.getsizeof(serialized_data)} - {serialization_time * 1000:.3f}ms - {deserialization_time * 1000:.3f}ms"


if __name__ == '__main__':
    format_name = sys.argv[1]

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind(('0.0.0.0', int(os.environ.get(f'SERVER_PORT'))))

    while True:
        request, back = server_socket.recvfrom(1024)
        response = handle_request(format_name)
        server_socket.sendto(response.encode(), back)
