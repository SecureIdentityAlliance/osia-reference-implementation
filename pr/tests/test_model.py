import unittest
import json
from pprint import pprint

import marshmallow.exceptions
import pytest

import pr.model

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy import select

#_______________________________________________________________________________
class TestNominal(unittest.TestCase):
    def setUp(self):
        self.engine = pr.engine
        pr.model.Base.metadata.drop_all(self.engine)
        pr.model.Base.metadata.create_all(self.engine)

    def tearDown(self):
        self.engine = pr.engine
        pr.model.Base.metadata.drop_all(self.engine)
        pr.model.Base.metadata.create_all(self.engine)

    def test_person(self):
        with Session(self.engine) as session:
            bob = pr.model.Person(
                personId='0001',
                status='INACTIVE',
                physicalStatus='ALIVE',
                identities=[
                    pr.model.Identity(
                        identityId='001',
                        status='VALID',
                        galleries=['VIP'],
                        isReference=True,
                        clientData=b'ABC',
                        bgd_firstName="John",
                        bgd_lastName="Doo",
                        biometricData=[
                            pr.model.BiometricData(
                                biometricType='FINGER',
                                biometricSubType='RIGHT_INDEX',
                                imageRef='http://media/1234'
                            )
                        ]
                    ),
                    pr.model.Identity(
                        identityId='002',
                        status='CLAIMED',
                        galleries=['GAL1'],
                        isReference=False,
                        bgd_firstName="John",
                        bgd_lastName="Doo",
                    )
                ]
            )
            session.add(bob)
            session.commit()

            # check galleries and clientData
            assert bob.reference.galleries == ['VIP']
            assert bob.reference.clientData == b'ABC'
            assert bob.identities[0].galleries == ['VIP']

            # change galleries
            bob.identities[0].galleries = ['A','B']
            bob.identities[1].galleries = ['GAL1','B']
            session.add(bob)
            session.commit()
            assert bob.identities[0].galleries == ['A', 'B']
            assert bob.identities[1].galleries == ['GAL1', 'B']

            # query person
            res = pr.model.Person.find_by_id(session,'0001')
            assert len(res) == 1
            assert res[0].identities[0].identityId == '001'
            assert res[0].identities[0].galleries == ['A', 'B']
            assert res[0].reference.clientData == b'ABC'

            # list of galleries
            galleries = pr.model.Gallery.values(session)
            self.assertCountEqual(galleries, ['A', 'B', 'GAL1'])
            assert galleries == ['A', 'B', 'GAL1']

            # Get a gallery
            ids = pr.model.Gallery.get_identities(session, 'A')
            assert len(ids) == 1
            ids = pr.model.Gallery.get_identities(session, 'B')
            assert len(ids) == 2

    def test_serialize_person(self):
        import pr.serialize
        with Session(self.engine) as session:
            bob_json = """
{
    "status": "INACTIVE",
    "physicalStatus": "ALIVE"
}
"""
            person_schema = pr.serialize.PersonSchema()
            bob = person_schema.load(json.loads(bob_json), session=session)
            bob.personId = '0002'
            session.add(bob)
            session.commit()

            res = pr.model.Person.find_by_id(session,'0002')
            assert len(res) == 1

            # dump
            # personId was added
            bob_json = """
{
    "personId": "0002",
    "status": "INACTIVE",
    "physicalStatus": "ALIVE"
}
"""
            assert json.loads(bob_json) == person_schema.dump(res[0])

    def test_serialize_person_identities(self):
        import pr.serialize
        with Session(self.engine) as session:
            # Create in Python
            bob = pr.model.Person(
                personId='0003',
                status='INACTIVE',
                physicalStatus='ALIVE',
                identities=[
                    pr.model.Identity(
                        identityId='001',
                        status='VALID',
                        identityType='TEST',
                        galleries=['VIP'],
                        isReference=True,
                        clientData=b'ABC',
                        bgd_firstName="John",
                        bgd_lastName="Doo",
                    ),
                ]
            )
            session.add(bob)
            session.commit()

            # check it was inserted in the database
            res = pr.model.Person.find_by_id(session,'0003')
            assert len(res) == 1
            assert len(res[0].identities) == 1
            assert res[0].identities[0].galleries == ['VIP']

            # Check we can serialize the person
            person_schema = pr.serialize.PersonSchema()
            bob_json = person_schema.dump(bob)
            # pprint(bob_json)
            assert bob_json == {'personId': '0003',
                'physicalStatus': 'ALIVE',
                'status': 'INACTIVE'}

            # Check we can deserialize the person from a (modified) json
            del bob_json['personId']
            bob_json['status'] = 'ACTIVE'
            person_schema = pr.serialize.PersonSchema()
            bob = person_schema.load(bob_json, instance=bob, session=session)
            assert bob.status == 'ACTIVE'
            session.commit()

            # Retrieve from the database and check the data is still correct
            res = pr.model.Person.find_by_id(session,'0003')
            assert len(res) == 1
            assert res[0].status == 'ACTIVE'

    def test_serialize_person_error(self):
        import pr.serialize
        with Session(self.engine) as session:
            # unknown field is detected
            bob_json = """
{
    "status": "ACTIVE",
    "physicalStatus": "ALIVE",
    "totot": "undefined"
}
"""
            with pytest.raises( marshmallow.exceptions.ValidationError):
                person_schema = pr.serialize.PersonSchema()
                bob = person_schema.load(json.loads(bob_json), session=session)

if __name__ == '__main__':
    unittest.main(argv=['-v'])

