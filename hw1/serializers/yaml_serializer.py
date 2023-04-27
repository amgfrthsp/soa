import yaml


class YAMLSerializer:

    def serialize(self, obj):
        return yaml.dump(obj)

    def deserialize(self, obj):
        return yaml.load(obj, Loader=yaml.Loader)
