import msgpack


class MessagePackSerializer:

    def serialize(self, obj):
        return msgpack.packb(obj)

    def deserialize(self, obj):
        return msgpack.unpackb(obj)
