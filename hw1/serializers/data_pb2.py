# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: data.proto
"""Generated protocol buffer code."""
from google.protobuf.internal import builder as _builder
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\ndata.proto\"\x9f\x01\n\x05House\x12\x0c\n\x04name\x18\x01 \x01(\t\x12\x11\n\tmaterials\x18\x02 \x03(\t\x12\"\n\x06owners\x18\x03 \x03(\x0b\x32\x12.House.OwnersEntry\x12\x12\n\nyear_built\x18\x04 \x01(\x05\x12\x0e\n\x06square\x18\x05 \x01(\x02\x1a-\n\x0bOwnersEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\x05:\x02\x38\x01\x62\x06proto3')

_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, globals())
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'data_pb2', globals())
if _descriptor._USE_C_DESCRIPTORS == False:

    DESCRIPTOR._options = None
    _HOUSE_OWNERSENTRY._options = None
    _HOUSE_OWNERSENTRY._serialized_options = b'8\001'
    _HOUSE._serialized_start = 15
    _HOUSE._serialized_end = 174
    _HOUSE_OWNERSENTRY._serialized_start = 129
    _HOUSE_OWNERSENTRY._serialized_end = 174
# @@protoc_insertion_point(module_scope)
