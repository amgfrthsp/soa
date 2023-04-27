import json


class JSONSerializer:

    def serialize(self, obj):
        return json.dumps(obj)

    def deserialize(self, obj):
        return json.loads(obj)
