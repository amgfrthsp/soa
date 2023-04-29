from data_pb2 import House
from google.protobuf.json_format import ParseDict


class PBufferSerializer:

    def serialize(self, obj):
        scheme = House()
        ParseDict(obj, scheme)
        return scheme.SerializeToString()

    def deserialize(self, obj):
        deserialized_obj = House()
        deserialized_obj.ParseFromString(obj)
        return deserialized_obj
