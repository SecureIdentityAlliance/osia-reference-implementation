# https://www.sqlalchemy.org/

import io
import logging
import json
from typing import Optional

import yaml

import pr

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

#______________________________________________________________________________
# The persistent schema
#______________________________________________________________________________
class Base(AsyncAttrs,DeclarativeBase):
    pass

class Person(Base):
    __tablename__ = 'PERSON'

    personId: Mapped[str] = mapped_column(sa.String(100), primary_key=True)
    status: Mapped[str] = mapped_column(sa.Enum(*['ACTIVE','INACTIVE'], name='person_status_enum'), default='ACTIVE')
    physicalStatus: Mapped[str] = mapped_column(sa.Enum(*['ALIVE','DEAD'], name='person_physical_status_enum'), default='ALIVE')

    identities: Mapped[list["Identity"]] = relationship(
            back_populates="person", cascade="all, delete-orphan", lazy='select',
            order_by="Identity.position",
            collection_class=ordering_list("position"))

    # https://docs.sqlalchemy.org/en/20/orm/queryguide/select.html#writing-select-statements-for-orm-mapped-classes
    @staticmethod
    def find_by_id(session, personId):
        res = session.scalars(select(Person).where(Person.personId==personId))
        return list(res)

    @staticmethod
    async def afind_by_id(session, personId):
        res = await session.execute(select(Person).where(Person.personId==personId))
        return list(res.scalars())

    @property
    def reference(self):
        ref = [x for x in self.identities if x.isReference]
        if len(ref)==1:
            return ref[0]

class Missing(Base):
    __tablename__ = 'BIOMETRIC_DATA_MISSING'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    biometricData_id: Mapped[int] = mapped_column(sa.ForeignKey("BIOMETRIC_DATA.id"))
    biometricSubType: Mapped[str] = mapped_column(sa.Enum(*['UNKNOWN', 'RIGHT_THUMB', 'RIGHT_INDEX', 'RIGHT_MIDDLE', 'RIGHT_RING', 'RIGHT_LITTLE', 'LEFT_THUMB', 'LEFT_INDEX', 'LEFT_MIDDLE', 'LEFT_RING', 'LEFT_LITTLE', 'PLAIN_RIGHT_FOUR_FINGERS', 'PLAIN_LEFT_FOUR_FINGERS', 'PLAIN_THUMBS', 'UNKNOWN_PALM', 'RIGHT_FULL_PALM', 'RIGHT_WRITERS_PALM', 'LEFT_FULL_PALM', 'LEFT_WRITERS_PALM', 'RIGHT_LOWER_PALM', 'RIGHT_UPPER_PALM', 'LEFT_LOWER_PALM', 'LEFT_UPPER_PALM', 'RIGHT_OTHER', 'LEFT_OTHER', 'RIGHT_INTERDIGITAL', 'RIGHT_THENAR', 'LEFT_INTERDIGITAL', 'LEFT_THENAR', 'LEFT_HYPOTHENAR', 'RIGHT_INDEX_AND_MIDDLE', 'RIGHT_MIDDLE_AND_RING', 'RIGHT_RING_AND_LITTLE', 'LEFT_INDEX_AND_MIDDLE', 'LEFT_MIDDLE_AND_RING', 'LEFT_RING_AND_LITTLE', 'RIGHT_INDEX_AND_LEFT_INDEX', 'RIGHT_INDEX_AND_MIDDLE_AND_RING', 'RIGHT_MIDDLE_AND_RING_AND_LITTLE', 'LEFT_INDEX_AND_MIDDLE_AND_RING', 'LEFT_MIDDLE_AND_RING_AND_LITTLE', 'EYE_UNDEF', 'EYE_RIGHT', 'EYE_LEFT', 'PORTRAIT', 'LEFT_PROFILE', 'RIGHT_PROFILE'], name='missing_bio_subtype_enum'))
    presence: Mapped[str] = mapped_column(sa.Enum(*['BANDAGED', 'AMPUTATED', 'DAMAGED'], name='missing_presence_enum'))

class BiometricData(Base):
    __tablename__ = 'BIOMETRIC_DATA'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    identity_id: Mapped[int] = mapped_column(sa.ForeignKey("IDENTITY.id"))
    identity: Mapped["Identity"] = relationship(back_populates="biometricData")

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
    identity_id: Mapped[int] = mapped_column(sa.ForeignKey("IDENTITY.id"))
    identity: Mapped["Identity"] = relationship(back_populates="documentData")

    documentType: Mapped[str] = mapped_column(sa.Enum(*['ID_CARD', 'PASSPORT', 'INVOICE', 'BIRTH_CERTIFICATE', 'FORM', 'OTHER'], name='documentdata_document_type_enum'))
    documentTypeOther: Mapped[Optional[str]] = mapped_column(sa.String(100))
    instance: Mapped[Optional[str]] = mapped_column(sa.String(100))
    parts: Mapped[list[DocumentPart]] = relationship(cascade="all, delete-orphan", lazy='immediate')


# See https://docs.sqlalchemy.org/en/20/orm/extensions/associationproxy.html#module-sqlalchemy.ext.associationproxy
class Gallery(Base):
    __tablename__ = 'GALLERY'
    galleryId: Mapped[str] = mapped_column(sa.String(100), primary_key=True)
    identity_id: Mapped[int] = mapped_column(sa.ForeignKey("IDENTITY.id"), primary_key=True)
    identity: Mapped["Identity"] = relationship(back_populates="_galleries")

    identityId: AssociationProxy[str] = association_proxy("IDENTITY", "identityId")

    def __init__(self, gallery: str):
        self.galleryId = gallery

    @staticmethod
    def values(session):
        res = session.scalars(select(Gallery.galleryId).distinct())
        return list(res)

    @staticmethod
    async def avalues(session):
        sel = select(Gallery.galleryId).distinct()
        res = await session.execute(sel)
        return list(res.scalars())

    @staticmethod
    def get_identities(session, galleryId, offset=None, limit=None):
        sel = select(Identity).where(Gallery.galleryId==galleryId, Gallery.identity_id==Identity.id)
        if limit:
            sel = sel.limit(limit)
        if offset:
            sel = sel.offset(offset)

        res = session.scalars(sel)
        return list(res)

    @staticmethod
    async def aget_identities(session, galleryId, offset=None, limit=None):
        sel = select(Identity).where(Gallery.galleryId==galleryId, Gallery.identity_id==Identity.id)
        if limit:
            sel = sel.limit(limit)
        if offset:
            sel = sel.offset(offset)
        res = await session.execute(sel)
        return list(res.scalars())

class Identity(Base):
    __tablename__ = 'IDENTITY'
    __table_args__ = (
        sa.UniqueConstraint('personId','identityId'),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    isReference: Mapped[bool] = mapped_column(sa.Boolean, default=False)
    position: Mapped[int]
    personId: Mapped[str] = mapped_column(sa.ForeignKey("PERSON.personId"))
    person: Mapped["Person"] = relationship(back_populates="identities")

    identityId: Mapped[str] = mapped_column(sa.String(100))
    identityType: Mapped[str] = mapped_column(sa.String(100), default='')
    status: Mapped[str] = mapped_column(sa.Enum(*['CLAIMED', 'VALID', 'INVALID', 'REVOKED'], name='identity_status_enum'), default='CLAIMED')
    _galleries: Mapped[list[Gallery]] = relationship(back_populates="identity", cascade="all, delete-orphan", lazy='immediate')
    galleries: AssociationProxy[list[str]] = association_proxy(
        "_galleries", "galleryId"
    )
    clientData: Mapped[Optional[bytes]] = mapped_column(sa.LargeBinary)
    biometricData: Mapped[list["BiometricData"]] = relationship(
            cascade="all, delete-orphan", lazy='immediate')
    documentData: Mapped[list["DocumentData"]] = relationship(
            cascade="all, delete-orphan", lazy='immediate')


    @staticmethod
    def find_by_id(session, identityId):
        res = session.scalars(select(Identity).where(Identity.identityId==identityId))
        return list(res)

#______________________________________________________________________________
# Load the custo
# Custo definition is inspired by OpenAPI v3 (https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.0.md#dataTypes)
# See also https://docs.sqlalchemy.org/en/20/core/type_basics.html
#______________________________________________________________________________

def _add_field(n, c, prefix, required):
    # support the following properties: type, format, enum (for string), maxLength (for string), required, default
    # XXX min, max, pattern? or leave in JSON schema validation?

    kw = {}
    if n in required:
        kw['nullable'] = False
    else:
        kw['nullable'] = True
        
    n = prefix + n
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
                col = mapped_column(n, sa.Enum(*e, name=n+'_enum'),**kw)
            else:
                col = mapped_column(n, sa.String(c.get('maxLength',255)),**kw)
        elif f=='date':
            col = mapped_column(n, sa.Date(),**kw)
        elif f=='date-time':
            col = mapped_column(n, sa.DateTime(timezone=True),**kw)
        elif f=='byte':
            col = mapped_column(n, sa.Text(),**kw)
    elif t=='boolean':
        col = mapped_column(n, sa.Boolean(),**kw)
    elif t=='integer':
        f = c.get('format','int32')
        if f=='int32':
            col = mapped_column(n, sa.Integer(),**kw)
        elif f=='int64':
            col = mapped_column(n, sa.BigInteger(),**kw)
    elif t=='number':
        f = c.get('format','float')
        if f=='float':
            col = mapped_column(n, sa.Float(),**kw)
        elif f=='double':
            col = mapped_column(n, sa.Double(),**kw)
    elif t=='object':
        col = mapped_column(n, sa.JSON(),**kw)
    if col is None:
        raise Exception("Illegal type/format in custo definition for field [{}]/[{}]".format(n, t))
    # https://docs.sqlalchemy.org/en/14/orm/declarative_tables.html#appending-additional-columns-to-an-existing-declarative-mapped-class
    setattr(Identity, n, col)

CUSTO_BGD = {}
CUSTO_CTX = {}
def load_custo(custo):
    global CUSTO_BGD
    global CUSTO_CTX
    for n,c in custo.get('BiographicData',{}).get('properties', {}).items():
        _add_field(n,c,'bgd_', custo.get('BiographicData',{}).get('required', []))
        CUSTO_BGD[n] = c
    for n,c in custo.get('ContextualData',{}).get('properties', {}).items():
        _add_field(n,c,'ctx_', custo.get('ContextualData',{}).get('required', []))
        CUSTO_CTX[n] = c

custo = None
def _load_custo():
    global custo
    # Load the custo
    # WARNING: it has to be done before we setup the serializer
    if pr.args and pr.args.custo_filename and custo is None:
        with io.open(pr.args.custo_filename, 'rt', encoding='utf-8') as stream:
            custo = yaml.load(stream, Loader=yaml.Loader)
            load_custo(custo)
            logging.info("Custo from file [%s] was loaded", pr.args.custo_filename)

def setup():
    _load_custo()
    if pr.args and pr.args.database_url:
        # setup the database engine
        # See https://docs.sqlalchemy.org/en/20/core/engines.html#database-urls
        engine = create_engine(pr.args.database_url, echo=False)
        aengine = create_async_engine(pr.args.database_url.replace('psycopg2', 'asyncpg').replace('sqlite', 'sqlite+aiosqlite'), echo=False)
        if not pr.args.dont_create_schema:
            Base.metadata.create_all(engine)
        logging.info("DB engine created URL [%s]", pr.args.database_url)
        pr.engine = engine
        pr.aengine = aengine

def dump_sql(sql, *multiparams, **params):
    print(sql.compile(dialect=pr.engine.dialect))

def dump():
    _load_custo()
    if pr.args and pr.args.database_url:
        # setup the default engine
        engine = create_mock_engine(pr.args.database_url, dump_sql)
        pr.engine = engine
        Base.metadata.create_all(engine)
