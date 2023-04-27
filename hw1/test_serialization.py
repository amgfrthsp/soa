import random
import string
import sys
import time
from serializers.avro_serializer import AvroSerializer
from serializers.json_serializer import JSONSerializer
from serializers.mpack_serializer import MessagePackSerializer

from serializers.naive_serializer import NaiveSerializer
from serializers.pbuffer_serializer import PBufferSerializer
from serializers.xml_serializer import XMLSerializer
from serializers.yaml_serializer import YAMLSerializer


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


name2serializer = {
    'NAIVE': NaiveSerializer,
    'JSON': JSONSerializer,
    'XML': XMLSerializer,
    'YAML': YAMLSerializer,
    'MSGPACK': MessagePackSerializer,
    'PBUFFER': PBufferSerializer,
    'AVRO': AvroSerializer,
}


if __name__ == '__main__':
    format_name = sys.argv[1]
    data = generate_data()

    serializer = name2serializer[format_name]()

    start_time = time.time()
    serialized_data = serializer.serialize(data)
    serialization_time = time.time() - start_time

    start_time = time.time()
    deserialized_data = serializer.deserialize(serialized_data)
    deserialization_time = time.time() - start_time

    print(f"{format_name} - {sys.getsizeof(serialized_data)} - {serialization_time * 1000:.3f}ms - {deserialization_time * 1000:.3f}ms")
