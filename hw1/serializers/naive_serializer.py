import pickle


class NaiveSerializer:

    def serialize(self, obj):
        return pickle.dumps(obj)

    def deserialize(self, obj):
        return pickle.loads(obj)
