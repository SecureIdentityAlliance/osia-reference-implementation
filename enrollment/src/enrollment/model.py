import io
import logging
import json
import datetime
from typing import Optional

import yaml

import enrollment

import sqlalchemy as sa
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.ext.associationproxy import association_proxy, AssociationProxy
from sqlalchemy.ext.orderinglist import ordering_list
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import select
from sqlalchemy import create_engine, create_mock_engine
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.types import TypeDecorator, VARCHAR

QCONV = {}

#______________________________________________________________________________
# The persistent schema
#______________________________________________________________________________
class Base(AsyncAttrs,DeclarativeBase):
    pass

# [---CUSTO---]
# Data model classes and global variables

CUSTO_RQD = {}
CUSTO_ENF = {}
CUSTO_BGD = {}
CUSTO_CTX = {}

class Buffer(Base):
    __tablename__ = 'BUFFER'
    id: Mapped[str] = mapped_column(primary_key=True)
    enrollment_id: Mapped[str] = mapped_column(sa.String(100))
    content_type: Mapped[Optional[str]] = mapped_column(sa.String(100))
    buffer: Mapped[Optional[bytes]] = mapped_column(sa.LargeBinary)

    @staticmethod
    def find_by_id(session, enrollment_id, id):
        res = session.scalars(select(Buffer).where(Buffer.id==id, Buffer.enrollment_id==enrollment_id))
        return list(res)

    @staticmethod
    async def afind_by_id(session, enrollment_id, id):
        res = await session.execute(select(Buffer).where(Buffer.id==id, Buffer.enrollment_id==enrollment_id))
        return list(res.scalars())

    @staticmethod
    def find_by_enrollment_id(session, enrollment_id):
        res = session.scalars(select(Buffer).where(Buffer.enrollment_id==enrollment_id))
        return list(res)

    @staticmethod
    async def afind_by_enrollment_id(session, enrollment_id):
        res = await session.execute(select(Buffer).where(Buffer.enrollment_id==enrollment_id))
        return list(res.scalars())

class Missing(Base):
    __tablename__ = 'BIOMETRIC_DATA_MISSING'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    biometricData_id: Mapped[int] = mapped_column(sa.ForeignKey("BIOMETRIC_DATA.id"))
    biometricSubType: Mapped[str] = mapped_column(sa.Enum(*['UNKNOWN', 'RIGHT_THUMB', 'RIGHT_INDEX', 'RIGHT_MIDDLE', 'RIGHT_RING', 'RIGHT_LITTLE', 'LEFT_THUMB', 'LEFT_INDEX', 'LEFT_MIDDLE', 'LEFT_RING', 'LEFT_LITTLE', 'PLAIN_RIGHT_FOUR_FINGERS', 'PLAIN_LEFT_FOUR_FINGERS', 'PLAIN_THUMBS', 'UNKNOWN_PALM', 'RIGHT_FULL_PALM', 'RIGHT_WRITERS_PALM', 'LEFT_FULL_PALM', 'LEFT_WRITERS_PALM', 'RIGHT_LOWER_PALM', 'RIGHT_UPPER_PALM', 'LEFT_LOWER_PALM', 'LEFT_UPPER_PALM', 'RIGHT_OTHER', 'LEFT_OTHER', 'RIGHT_INTERDIGITAL', 'RIGHT_THENAR', 'LEFT_INTERDIGITAL', 'LEFT_THENAR', 'LEFT_HYPOTHENAR', 'RIGHT_INDEX_AND_MIDDLE', 'RIGHT_MIDDLE_AND_RING', 'RIGHT_RING_AND_LITTLE', 'LEFT_INDEX_AND_MIDDLE', 'LEFT_MIDDLE_AND_RING', 'LEFT_RING_AND_LITTLE', 'RIGHT_INDEX_AND_LEFT_INDEX', 'RIGHT_INDEX_AND_MIDDLE_AND_RING', 'RIGHT_MIDDLE_AND_RING_AND_LITTLE', 'LEFT_INDEX_AND_MIDDLE_AND_RING', 'LEFT_MIDDLE_AND_RING_AND_LITTLE', 'EYE_UNDEF', 'EYE_RIGHT', 'EYE_LEFT', 'PORTRAIT', 'LEFT_PROFILE', 'RIGHT_PROFILE'], name='missing_bio_subtype_enum'))
    presence: Mapped[str] = mapped_column(sa.Enum(*['BANDAGED', 'AMPUTATED', 'DAMAGED'], name='missing_presence_enum'))

class BiometricData(Base):
    __tablename__ = 'BIOMETRIC_DATA'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    enrollment_id: Mapped[int] = mapped_column(sa.ForeignKey("ENROLLMENT.id"))
    enrollment: Mapped["Enrollment"] = relationship(back_populates="biometricData")

    biometricType: Mapped[str] = mapped_column(sa.Enum(*['FACE', 'FINGER', 'PALM', 'IRIS', 'UNKNOWN'], name='biometricdata_bio_type_enum'))
    biometricSubType: Mapped[Optional[str]] = mapped_column(sa.Enum(*['UNKNOWN', 'RIGHT_THUMB', 'RIGHT_INDEX', 'RIGHT_MIDDLE', 'RIGHT_RING', 'RIGHT_LITTLE', 'LEFT_THUMB', 'LEFT_INDEX', 'LEFT_MIDDLE', 'LEFT_RING', 'LEFT_LITTLE', 'PLAIN_RIGHT_FOUR_FINGERS', 'PLAIN_LEFT_FOUR_FINGERS', 'PLAIN_THUMBS', 'UNKNOWN_PALM', 'RIGHT_FULL_PALM', 'RIGHT_WRITERS_PALM', 'LEFT_FULL_PALM', 'LEFT_WRITERS_PALM', 'RIGHT_LOWER_PALM', 'RIGHT_UPPER_PALM', 'LEFT_LOWER_PALM', 'LEFT_UPPER_PALM', 'RIGHT_OTHER', 'LEFT_OTHER', 'RIGHT_INTERDIGITAL', 'RIGHT_THENAR', 'LEFT_INTERDIGITAL', 'LEFT_THENAR', 'LEFT_HYPOTHENAR', 'RIGHT_INDEX_AND_MIDDLE', 'RIGHT_MIDDLE_AND_RING', 'RIGHT_RING_AND_LITTLE', 'LEFT_INDEX_AND_MIDDLE', 'LEFT_MIDDLE_AND_RING', 'LEFT_RING_AND_LITTLE', 'RIGHT_INDEX_AND_LEFT_INDEX', 'RIGHT_INDEX_AND_MIDDLE_AND_RING', 'RIGHT_MIDDLE_AND_RING_AND_LITTLE', 'LEFT_INDEX_AND_MIDDLE_AND_RING', 'LEFT_MIDDLE_AND_RING_AND_LITTLE', 'EYE_UNDEF', 'EYE_RIGHT', 'EYE_LEFT', 'PORTRAIT', 'LEFT_PROFILE', 'RIGHT_PROFILE'], name='biometricdata_bio_subtype_enum'))
    instance: Mapped[Optional[str]] = mapped_column(sa.String(100))
    identityId: Mapped[Optional[str]] = mapped_column(sa.String(100))
    image: Mapped[Optional[bytes]] = mapped_column(sa.LargeBinary)
    imageRef: Mapped[Optional[str]] = mapped_column(sa.String(255))
    captureDate: Mapped[Optional[str]] = mapped_column(sa.DateTime(timezone=True))
    captureDevice: Mapped[Optional[str]] = mapped_column(sa.String(100))
    impressionType: Mapped[Optional[str]] = mapped_column(sa.Enum(*["LIVE_SCAN_PLAIN", "LIVE_SCAN_ROLLED", "NONLIVE_SCAN_PLAIN", "NONLIVE_SCAN_ROLLED", "LATENT_IMPRESSION", "LATENT_TRACING", "LATENT_PHOTO", "LATENT_LIFT", "LIVE_SCAN_SWIPE", "LIVE_SCAN_VERTICAL_ROLL", "LIVE_SCAN_PALM", "NONLIVE_SCAN_PALM", "LATENT_PALM_IMPRESSION", "LATENT_PALM_TRACING", "LATENT_PALM_PHOTO", "LATENT_PALM_LIFT", "LIVE_SCAN_OPTICAL_CONTACTLESS_PLAIN", "OTHER", "UNKNOWN"], name='biometricdata_impression_type_enum'))
    width: Mapped[Optional[int]]
    height: Mapped[Optional[int]]
    bitdepth: Mapped[Optional[int]]
    mimeType: Mapped[Optional[str]] = mapped_column(sa.String(100))
    resolution: Mapped[Optional[int]]
    compression: Mapped[Optional[str]] = mapped_column(sa.Enum(*['NONE', 'WSQ', 'JPEG', 'JPEG2000', 'PNG'], name='biometricdata_compression_type_enum'))
    missing: Mapped[list[Missing]] = relationship(cascade="all, delete-orphan", lazy='immediate')
    bio_metadata: Mapped[Optional[str]] = mapped_column(sa.String(1024))    # 'metadata' will conflict with sqlAlchemy. Mapping is defined in serialize.py
    comment: Mapped[Optional[str]] = mapped_column(sa.String(1024))
    template: Mapped[Optional[bytes]] = mapped_column(sa.LargeBinary)
    templateRef: Mapped[Optional[str]] = mapped_column(sa.String(255))
    templateFormat: Mapped[Optional[str]] = mapped_column(sa.String(100))
    quality: Mapped[Optional[int]]
    qualityFormat: Mapped[Optional[str]] = mapped_column(sa.String(100))
    algorithm: Mapped[Optional[str]] = mapped_column(sa.String(100))
    vendor: Mapped[Optional[str]] = mapped_column(sa.String(100))

class IntList(TypeDecorator):
    impl = VARCHAR
    def process_bind_param(self, value, dialect):
        if value is not None:
            value = json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = json.loads(value)
        return value
    
class DocumentPart(Base):
    __tablename__ = 'DOCUMENT_PART'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    documentData_id: Mapped[int] = mapped_column(sa.ForeignKey("DOCUMENT_DATA.id"))

    # pages: Mapped[Optional[str]] = mapped_column(sa.JSON())
    pages: Mapped[Optional[list[int]]] = mapped_column(MutableList.as_mutable(IntList))
    data: Mapped[Optional[bytes]] = mapped_column(sa.LargeBinary)
    dataRef: Mapped[Optional[str]] = mapped_column(sa.String(255))
    width: Mapped[Optional[int]]
    height: Mapped[Optional[int]]
    mimeType: Mapped[Optional[str]] = mapped_column(sa.String(100))
    captureDate: Mapped[Optional[str]] = mapped_column(sa.DateTime(timezone=True))
    captureDevice: Mapped[Optional[str]] = mapped_column(sa.String(100))

class DocumentData(Base):
    __tablename__ = 'DOCUMENT_DATA'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    enrollment_id: Mapped[int] = mapped_column(sa.ForeignKey("ENROLLMENT.id"))
    enrollment: Mapped["Enrollment"] = relationship(back_populates="documentData")

    documentType: Mapped[str] = mapped_column(sa.Enum(*['ID_CARD', 'PASSPORT', 'INVOICE', 'BIRTH_CERTIFICATE', 'FORM', 'OTHER'], name='documentdata_document_type_enum'))
    documentTypeOther: Mapped[Optional[str]] = mapped_column(sa.String(100))
    instance: Mapped[Optional[str]] = mapped_column(sa.String(100))
    parts: Mapped[list[DocumentPart]] = relationship(cascade="all, delete-orphan", lazy='immediate')

class Enrollment(Base):
    __tablename__ = 'ENROLLMENT'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    enrollmentId: Mapped[str] = mapped_column(sa.String(100))
    status: Mapped[str] = mapped_column(sa.Enum(*['FINALIZED','IN_PROGRESS'], name='enrollment_status_enum'), default='IN_PROGRESS')
    enrollmentType: Mapped[str] = mapped_column(sa.String(100))

    biometricData: Mapped[list["BiometricData"]] = relationship(
            cascade="all, delete-orphan", lazy='immediate')
    documentData: Mapped[list["DocumentData"]] = relationship(
            cascade="all, delete-orphan", lazy='immediate')


    # https://docs.sqlalchemy.org/en/20/orm/queryguide/select.html#writing-select-statements-for-orm-mapped-classes
    @staticmethod
    def find_by_id(session, enrollmentId):
        res = session.scalars(select(Enrollment).where(Enrollment.enrollmentId==enrollmentId))
        return list(res)

    @staticmethod
    async def afind_by_id(session, enrollmentId):
        res = await session.execute(select(Enrollment).where(Enrollment.enrollmentId==enrollmentId))
        return list(res.scalars())
# [---CUSTO---]



#
# Mechanism to build a predicate
#
def _build_predicate(data,
# [---CUSTO---]
# [---CUSTO---]
                     limit, offset):
    global QCONV
    sel = select(Enrollment)
# [---CUSTO---]
# [---CUSTO---]
    for pred in data:
        k = pred['attributeName']
        found = False
        for pre, lis in [
# [---CUSTO---]
                         ('',['enrollmentId', 'enrollmentStatus', 'enrollmentType']),
                         ('rqd_', CUSTO_RQD),
                         ('enf_', CUSTO_ENF),
                         ('bgd_', CUSTO_BGD),
                         ('ctx_', CUSTO_CTX),
# [---CUSTO---]
                         ]:
            if k in lis:
                found = True
                qv = pred['value']
                col_name = pre+k
                col = getattr(Enrollment, col_name)
                if col_name in QCONV:
                    qv = QCONV[col_name](qv)
                if pred['operator'] == '=':
                    sel = sel.where( col == qv)
                elif pred['operator']=='!=':
                    sel = sel.where( col != qv)
                elif pred['operator']=='<':
                    sel = sel.where( col < qv)
                elif pred['operator']=='>':
                    sel = sel.where( col > qv)
                elif pred['operator']=='<=':
                    sel = sel.where( col <= qv)
                elif pred['operator']=='>=':
                    sel = sel.where( col >= qv)
                else:
                    {'code':1, 'message': 'Invalid operator [{}] in query expression'.format(pred['operator'])}
                break
        if not found:
            return {'code':1, 'message': 'Unknown attribute [{}] in query expression'.format(k)}

# [---CUSTO---]
# [---CUSTO---]

    if limit:
        sel = sel.limit(limit)
    if offset:
        sel = sel.offset(offset)
    return sel

#______________________________________________________________________________
# Mechanism to load the custo and inject its definition in the data model
# Custo definition is inspired by OpenAPI v3 (https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.0.md#dataTypes)
# See also https://docs.sqlalchemy.org/en/20/core/type_basics.html
#______________________________________________________________________________

def _add_field(name, c, prefix, required, klass):
    # support the following properties: type, format, enum (for string), maxLength (for string), required, default
    # XXX min, max, pattern? or leave in JSON schema validation?
    global QCONV
    kw = {}
    if name in required:
        kw['nullable'] = False
    else:
        kw['nullable'] = True
        
    name = prefix + name
    t = c.get('type','string')
    col = None
    d = c.get('default',None)
    if d is not None:
        kw['default'] = d
     
    if t=='string':
        f = c.get('format','')
        e = c.get('enum',None)
        if f=='':
            if e is not None:
                col = mapped_column(name, sa.Enum(*e, name=name+'_enum'),**kw)
            else:
                col = mapped_column(name, sa.String(c.get('maxLength',255)),**kw)
        elif f=='date':
            col = mapped_column(name, sa.Date(),**kw)
            QCONV[name] = datetime.date.fromisoformat
        elif f=='date-time':
            col = mapped_column(name, sa.DateTime(timezone=True),**kw)
            QCONV[name] = datetime.datetime.fromisoformat
        elif f=='byte':
            col = mapped_column(name, sa.Text(),**kw)
    elif t=='boolean':
        col = mapped_column(name, sa.Boolean(),**kw)
    elif t=='integer':
        f = c.get('format','int32')
        if f=='int32':
            col = mapped_column(name, sa.Integer(),**kw)
        elif f=='int64':
            col = mapped_column(name, sa.BigInteger(),**kw)
    elif t=='number':
        f = c.get('format','float')
        if f=='float':
            col = mapped_column(name, sa.Float(),**kw)
        elif f=='double':
            col = mapped_column(name, sa.Double(),**kw)
    elif t=='object':
        col = mapped_column(name, sa.JSON(),**kw)
    if col is None:
        raise Exception("Illegal type/format in custo definition for field [{}]/[{}]".format(name, t))
    # https://docs.sqlalchemy.org/en/14/orm/declarative_tables.html#appending-additional-columns-to-an-existing-declarative-mapped-class
    setattr(klass, name, col)

def inject_custo(custo):
    # [---CUSTO---]
    # Process the custo and inject in data model
    global CUSTO_RQD
    global CUSTO_ENF
    global CUSTO_BGD
    global CUSTO_CTX
    for name,c in custo.get('RequestData',{}).get('properties', {}).items():
        _add_field(name,c,'rqd_', custo.get('RequestData',{}).get('required', []), Enrollment)
        CUSTO_RQD[name] = c
    for name,c in custo.get('EnrollmentFlags',{}).get('properties', {}).items():
        _add_field(name,c,'enf_', custo.get('EnrollmentFlags',{}).get('required', []), Enrollment)
        CUSTO_ENF[name] = c
    for name,c in custo.get('BiographicData',{}).get('properties', {}).items():
        _add_field(name,c,'bgd_', custo.get('BiographicData',{}).get('required', []), Enrollment)
        CUSTO_BGD[name] = c
    for name,c in custo.get('ContextualData',{}).get('properties', {}).items():
        _add_field(name,c,'ctx_', custo.get('ContextualData',{}).get('required', []), Enrollment)
        CUSTO_CTX[name] = c
    # [---CUSTO---]

custo = None
def _load_custo():
    global custo
    # Load the custo
    # WARNING: it has to be done before we setup the serializer
    if enrollment.args and enrollment.args.custo_filename and custo is None:
        with io.open(enrollment.args.custo_filename, 'rt', encoding='utf-8') as stream:
            custo = yaml.load(stream, Loader=yaml.Loader)
            inject_custo(custo)
            logging.info("Custo from file [%s] was loaded", enrollment.args.custo_filename)

def setup():
    _load_custo()
    if enrollment.args and enrollment.args.database_url:
        # setup the database engine
        # See https://docs.sqlalchemy.org/en/20/core/engines.html#database-urls
        engine = create_engine(enrollment.args.database_url, echo=False)
        aengine = create_async_engine(enrollment.args.database_url.replace('psycopg2', 'asyncpg').replace('sqlite', 'sqlite+aiosqlite'), echo=False)
        if not enrollment.args.dont_create_schema:
            Base.metadata.create_all(engine)
        logging.info("DB engine created URL [%s]", enrollment.args.database_url)
        enrollment.engine = engine
        enrollment.aengine = aengine

def dump_sql(sql, *multiparams, **params):
    print(sql.compile(dialect=enrollment.engine.dialect))

def dump():
    _load_custo()
    if enrollment.args and enrollment.args.database_url:
        # setup the default engine
        engine = create_mock_engine(enrollment.args.database_url, dump_sql)
        enrollment.engine = engine
        Base.metadata.create_all(engine)