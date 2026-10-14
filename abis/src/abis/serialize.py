# https://marshmallow-sqlalchemy.readthedocs.io/en/latest/index.html
# https://marshmallow.readthedocs.io/en/3.x-line/index.html

import base64
import logging

from . import model

# import marshmallow as ma
from marshmallow import fields, ValidationError
from marshmallow_sqlalchemy import SQLAlchemySchema, SQLAlchemyAutoSchema, auto_field
from marshmallow_sqlalchemy.fields import Related, Nested
from marshmallow import post_dump, pre_load

# [---CUSTO---]
# Additional imports
# [---CUSTO---]

# Utilities for embedding custo data with an additional prefix
def _ext2int(data,key,prefix, only=[]):
    logging.debug('_ext2int::IN: %s', data)
    # Get all content from data.*key*.zzz and copy as data.*prefix*_zzz
    for k,v in list(data.setdefault(key,{}).items()):
        if k in only or not only:
            data[prefix+k] = v
            del data[key][k]
    if not data[key] or not only:
        del data[key]
    logging.debug('_ext2int::OUT: %s', data)
    return data

def _int2ext(data,key,prefix, only=[]):
    logging.debug('_int2ext::IN: %s', data)
    # Get all key of the form data.*prefix*_zzz and move it in data.*key*.zzz
    if key in data and data[key] and only:
        sub_object = data[key]
    else:
        sub_object = {}
    data2 = {key: sub_object}
    for k,v in data.items():
        if k==key:
            continue
        if k.startswith(prefix) and v is not None and (not only or k[len(prefix):] in only):
            sub_object[k[len(prefix):]] = v
            continue
        # Do not keep it if None (no value in database)
        if v is not None:
            data2[k] = v
    data2[key].update(sub_object)
    logging.debug('_int2ext::OUT: %s', data2)
    return data2

# Field that serializes to a base64 encoded string a bytes.
class LargeBinary(fields.Field):

    def _serialize(self, value, attr, obj, **kwargs):
        # binary -> base64
        if value is None:
            return None
        return base64.b64encode(value).decode('ascii')

    def _deserialize(self, value, attr, data, **kwargs):
        # base64 -> binary
        try:
            return base64.b64decode(value)
        except ValueError as error:
            raise ValidationError("Buffer must be base64 encoded") from error

# [---CUSTO---]
# Place it your serializer
class MissingSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = model.Missing
        load_instance = True
        include_fk = False
        exclude = ['id']

class BiometricDataSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = model.BiometricData
        load_instance = True
        include_fk = False
        exclude = ['id']
    image = LargeBinary()
    template = LargeBinary()
    bio_metadata = auto_field(data_key='metadata')
    missing = Nested(MissingSchema, many=True)

    @post_dump
    def post_dump(self,obj,**kwargs):
        # remove all keys with value None
        d = {}
        for k, v in obj.items():
            if k=='missing':
                if type(v) is list and len(v)==0:
                    continue
            else:
                if v is None:
                    continue
            d[k] = v
        return d

class EncounterSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = model.Encounter
        load_instance = True
        include_fk = False
        dump_only = ['personId', 'encounterId']
        exclude = ['id']
    galleries = auto_field()
    clientData = LargeBinary()
    biometricData = Nested(BiometricDataSchema, many=True)

    @post_dump
    def post_dump(self,obj,**kwargs):
        return int2ext(obj)

    @pre_load
    def pre_load(self,in_data,**kwargs):
        return ext2int(in_data)

def ext2int(data):
    return _ext2int(
                _ext2int(
                    data,
                    key='contextualData',
                    prefix='ctx_', only=model.CUSTO_CTX.keys()),
                key='biographicData',
                prefix='bgd_', only=model.CUSTO_BGD.keys())

def int2ext(data):
    return _int2ext(
                _int2ext(
                    data,
                    key='contextualData',
                    prefix='ctx_', only=model.CUSTO_CTX.keys()),
                key='biographicData',
                prefix='bgd_', only=model.CUSTO_BGD.keys())

# [---CUSTO---]