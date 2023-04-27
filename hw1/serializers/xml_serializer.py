from xml_marshaller import xml_marshaller


class XMLSerializer:

    def serialize(self, obj):
        return xml_marshaller.dumps(obj)

    def deserialize(self, obj):
        return xml_marshaller.loads(obj, )
