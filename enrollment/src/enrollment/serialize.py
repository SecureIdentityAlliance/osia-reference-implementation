# https://marshmallow-sqlalchemy.readthedocs.io/en/latest/index.html
# https://marshmallow.readthedocs.io/en/3.x-line/index.html

import base64

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
def _ext2int(data,key,prefix):
    # Get all content from data.*key* and copy as bgd_zzz
    for k,v in data.setdefault(key,{}).items():
        data[prefix+k] = v
    del data[key]
    return data

def _int2ext(data,key,prefix):
    # Get all key of the form '*prefix*_zzz' and move it in data.*key*.zzz
    bgd = {}
    data2 = {}
    for k,v in data.items():
        if not k.startswith(prefix) and v is not None:
            data2[k] = v
            continue
        # Do not dump if None (no value in database)
        if v is not None:
            bgd[k[len(prefix):]] = v
    data2[key] = bgd
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
class DocumentPartSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = model.DocumentPart
        load_instance = True
        include_fk = False
        exclude = ['id']
    pages = fields.List(fields.Int())
    data = LargeBinary()

    @post_dump
    def post_dump(self,obj,**kwargs):
        # remove all keys with value None
        d = {}
        for k, v in obj.items():
            if v is not None:
                d[k] = v
        return d

class DocumentDataSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = model.DocumentData
        load_instance = True
        include_fk = False
        exclude = ['id']
    parts = Nested(DocumentPartSchema, many=True)

    @post_dump
    def post_dump(self,obj,**kwargs):
        # remove all keys with value None
        d = {}
        for k, v in obj.items():
            if v is not None:
                d[k] = v
        return d

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


class EnrollmentSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = model.Enrollment
        load_instance = True
        include_fk = False
#        dump_only = ['enrollmentId']
        exclude = ['id']
    biometricData = Nested(BiometricDataSchema, many=True)
    documentData = Nested(DocumentDataSchema, many=True)

    @post_dump
    def post_dump(self,obj,**kwargs):
        return int2ext(obj)

    @pre_load
    def pre_load(self,in_data,**kwargs):
        return ext2int(in_data)

def ext2int(data):
    return _ext2int(
                _ext2int(
                    _ext2int(
                        _ext2int(
                            data,
                            key='requestData',
                            prefix='rqd_'),
                        key='enrollmentFlags',
                        prefix='enf_'),
                    key='contextualData',
                    prefix='ctx_'),
                key='biographicData',
                prefix='bgd_')

def int2ext(data):
    return _int2ext(
                _int2ext(
                    _int2ext(
                        _int2ext(
                            data,
                            key='requestData',
                            prefix='rqd_'),
                        key='enrollmentFlags',
                        prefix='enf_'),
                    key='contextualData',
                    prefix='ctx_'),
                key='biographicData',
                prefix='bgd_')
# [---CUSTO---]