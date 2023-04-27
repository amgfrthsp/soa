from avro.schema import parse
from avro.io import DatumReader, DatumWriter, BinaryDecoder, BinaryEncoder
from io import BytesIO

schema = parse("""
{
  "type": "record",
  "name": "House",
  "fields": [
    {"name": "name", "type": "string"},
    {"name": "materials", "type": {"type": "array", "items": "string"}},
    {"name": "owners", "type": {"type": "map", "values": "int"}},
    {"name": "year_built", "type": "int"},
    {"name": "square", "type": "float"}
  ]
}
""")


class AvroSerializer:

    def serialize(self, obj):
        writer = DatumWriter(schema)
        bytes_writer = BytesIO()
        encoder = BinaryEncoder(bytes_writer)
        writer.write(obj, encoder)
        return bytes_writer.getvalue()

    def deserialize(self, obj):
        reader = DatumReader(schema)
        bytes_reader = BytesIO(obj)
        decoder = BinaryDecoder(bytes_reader)
        return reader.read(decoder)
