import os
import unittest
import sys

import requests

import pr.pr

URL = "http://localhost:8080/"

# ______________________________________________________________________________
if __name__ == '__main__':

    if len(sys.argv)>1:
        URL = sys.argv[1]

    class TestPR(unittest.TestCase):

        @property
        def url(self):
            global URL
            return URL

else:
    from . import TestPR

def get_ssl_context():
    kw = {}
    kw['verify'] = False
    return kw

#_______________________________________________________________________________
class TestNominal(TestPR):
    def setUp(self):
        pr.pr.PERSONS = {}

    def test_match(self):
        # Create person
        data = {
            "status": "ACTIVE",
            "physicalStatus": "DEAD"
        }
        with requests.post(self.url+'v1/persons/0001', json=data, params={'transactionId': 'T0001'},**get_ssl_context()) as r:
            assert 201 == r.status_code

        # Create identity
        data = {
            "identityType": "CIVIL",
            "status": "CLAIMED",
            "contextualData": {
                "enrollmentDate": "2019-01-11",
            },
            "biographicData": {
                "firstName": "Jane",
                "lastName": "Doe",
                "dateOfBirth": "1985-01-02",
                "gender": "F",
                "nationality": "FRA",
            }
        }
        with requests.post(self.url+'v1/persons/0001/identities/001', json=data, params={'transactionId': 'T0001'},**get_ssl_context()) as r:
            assert 201 == r.status_code

        # Tests some matchings
        data = {
            "firstName": "Jane",
            "lastName": "Doe",
        }
        with requests.post(self.url+'v1/persons/0001/match', json=data,**get_ssl_context()) as r:
            assert 200 == r.status_code
            assert [] == r.json()

        data = {
            "firstName": "Jane",
            "lastName": "Doe2",
            "noname": "blabla,"
        }
        with requests.post(self.url+'v1/persons/0001/match', json=data, **get_ssl_context()) as r:
            assert 200 == r.status_code
            assert [{'attributeName': 'lastName', 'errorCode': 1}, {'attributeName': 'noname', 'errorCode': 0}] == r.json()

        with requests.post(self.url+'v1/persons/MISS/match', json=data, **get_ssl_context()) as r:
            assert 404 == r.status_code

        # data = {
        #     "dateOfBirth": "1985-1-2"
        # }
        # with requests.post(self.url+'v1/persons/0001/match', json=data, **get_ssl_context()) as r:
        #     assert 200 == r.status_code
        #     assert [] == r.json()

    def test_query(self):
        # Create persons
        for n in range(10):
            data = {
                "status": "ACTIVE",
                "physicalStatus": "DEAD"
            }
            with requests.post(self.url+f'v1/persons/{n}', json=data, params={'transactionId': 'T0002'},**get_ssl_context()) as r:
                assert 201 == r.status_code

            # Create identity
            data = {
                "identityType": "CIVIL",
                "status": "CLAIMED",
                "contextualData": {
                    "enrollmentDate": "2019-01-11",
                },
                "biographicData": {
                    "firstName": "John",
                    "lastName": f"Doe{n}",
                    "dateOfBirth": "1985-11-30",
                    "gender": "M",
                    "nationality": "FRA",
                }
            }
            with requests.post(self.url+f'v1/persons/{n}/identities/001', json=data, params={'transactionId': 'T0002'},**get_ssl_context()) as r:
                assert 201 == r.status_code

        # Tests some queries
        # 1 result
        params = {
            "firstName": "John",
            "lastName": "Doe1",
        }
        with requests.get(self.url+'v1/persons', params=params,**get_ssl_context()) as r:
            assert 200 == r.status_code
            assert ['1'] == r.json()

        # no result
        params = {
            "firstName": "Jane",
            "lastName": "Doe1",
        }
        with requests.get(self.url+'v1/persons', params=params,**get_ssl_context()) as r:
            assert 200 == r.status_code
            assert [] == r.json()

        # large number of result
        params = {
            "firstName": "John",
        }
        with requests.get(self.url+'v1/persons', params=params,**get_ssl_context()) as r:
            assert 200 == r.status_code
            assert ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9'] == r.json()

        # one result + attributes
        params = {
            "firstName": "John",
            "lastName": "Doe1",
            "names":['lastName', 'gender']
        }
        with requests.get(self.url+'v1/persons', params=params,**get_ssl_context()) as r:
            assert 200 == r.status_code
            assert [{'lastName': 'Doe1', 'gender': 'M'}] == r.json()

        # large number of result with offset and limit
        params = {
            "firstName": "John",
            "offset": 2,
            "limit": 3,
        }
        with requests.get(self.url+'v1/persons', params=params,**get_ssl_context()) as r:
            assert 200 == r.status_code
            assert ['2', '3', '4'] == r.json()

    def test_read(self):
        # Create person
        data = {
            "status": "ACTIVE",
            "physicalStatus": "ALIVE"
        }
        with requests.post(self.url+'v1/persons/0002', json=data, params={'transactionId': 'T0001'},**get_ssl_context()) as r:
            assert 201 == r.status_code

        # Create identity
        data = {
            "identityType": "CIVIL",
            "status": "CLAIMED",
            "contextualData": {
                "enrollmentDate": "2019-01-11",
            },
            "biographicData": {
                "firstName": "Bob",
                "lastName": "Doe",
                "dateOfBirth": "1985-11-30",
                "gender": "F",
                "nationality": "FRA",
            }
        }
        with requests.post(self.url+'v1/persons/0002/identities/001', json=data, params={'transactionId': 'T0001'},**get_ssl_context()) as r:
            assert 201 == r.status_code

        # Tests some reads
        params = {
            "attributeNames": ["firstName", "lastName"]
        }
        with requests.get(self.url+'v1/persons/0002', params=params,**get_ssl_context()) as r:
            assert 200 == r.status_code
            assert {"firstName": "Bob", "lastName": "Doe",} == r.json()

    def test_reference(self):
        # Create person
        data = {
            "status": "ACTIVE",
            "physicalStatus": "DEAD"
        }
        with requests.post(self.url+'v1/persons/0000', json=data, params={'transactionId': 'T0001'},**get_ssl_context()) as r:
            assert 201 == r.status_code

        # Create person
        data = {
            "status": "ACTIVE",
            "physicalStatus": "DEAD"
        }
        with requests.post(self.url+'v1/persons/0001', json=data, params={'transactionId': 'T0001'},**get_ssl_context()) as r:
            assert 201 == r.status_code

        # Create identity
        datai = {
            "identityType": "CIVIL",
            "status": "CLAIMED",
            "contextualData": {
                "enrollmentDate": "2019-01-11",
            },
            "biographicData": {
                "firstName": "Jane1",
                "lastName": "Doe",
                "dateOfBirth": "1985-11-30",
                "age":37,
                "gender": "F",
                "nationality": "FRA",
            }
        }
        with requests.post(self.url+'v1/persons/0001/identities/001', json=datai, params={'transactionId': 'T0001'},**get_ssl_context()) as r:
            assert 201 == r.status_code

        # Create identity
        datai = {
            "identityType": "CIVIL",
            "status": "CLAIMED",
            "contextualData": {
                "enrollmentDate": "2019-01-11",
            },
            "biographicData": {
                "firstName": "Jane2",
                "lastName": "Doe",
                "dateOfBirth": "1985-11-30",
                "age":47,
                "gender": "F",
                "nationality": "FRA",
            }
        }
        with requests.post(self.url+'v1/persons/0001/identities/002', json=datai, params={'transactionId': 'T0001'},**get_ssl_context()) as r:
            assert 201 == r.status_code
        with requests.put(self.url+'v1/persons/0001/identities/002/reference', params={'transactionId': 'T0001'},**get_ssl_context()) as r:
            assert 204 == r.status_code

        # Create person
        data = {
            "status": "ACTIVE",
            "physicalStatus": "DEAD"
        }
        with requests.post(self.url+'v1/persons/0002', json=data, params={'transactionId': 'T0001'},**get_ssl_context()) as r:
            assert 201 == r.status_code

        # Create identity
        datai = {
            "identityType": "CIVIL",
            "status": "CLAIMED",
            "contextualData": {
                "enrollmentDate": "2019-01-11",
            },
            "biographicData": {
                "firstName": "John1",
                "lastName": "Doe",
                "dateOfBirth": "1985-11-30",
                "age":37,
                "gender": "M",
                "nationality": "FRA",
            }
        }
        with requests.post(self.url+'v1/persons/0002/identities/001', json=datai, params={'transactionId': 'T0001'},**get_ssl_context()) as r:
            assert 201 == r.status_code

        # query
        with requests.get(self.url+'v1/persons?names=firstName&names=lastName&names=personId&lastName=Doe',**get_ssl_context()) as r:
            assert 200 == r.status_code
            assert 2==len(r.json())
        with requests.get(self.url+'v1/persons?names=firstName&names=lastName&names=personId&firstName=Jane1',**get_ssl_context()) as r:
            assert 200 == r.status_code
            assert 0==len(r.json())
        with requests.get(self.url+'v1/persons?names=firstName&names=lastName&names=personId&firstName=Jane2',**get_ssl_context()) as r:
            assert 200 == r.status_code
            assert 1==len(r.json())

        # Match
        data = {
            "firstName": "Jane1",
            "lastName": "Doe",
        }
        with requests.post(self.url+'v1/persons/0001/match', json=data,**get_ssl_context()) as r:
            assert 200 == r.status_code
            assert 1==len(r.json())
        data = {
            "firstName": "Jane2",
            "lastName": "Doe",
        }
        with requests.post(self.url+'v1/persons/0001/match', json=data,**get_ssl_context()) as r:
            assert 200 == r.status_code
            assert 0==len(r.json())
        with requests.post(self.url+'v1/persons/MISS/match', json=data,**get_ssl_context()) as r:
            assert 404 == r.status_code
        with requests.post(self.url+'v1/persons/0000/match', json=data,**get_ssl_context()) as r:
            assert 404 == r.status_code

        # read
        params = {
            "attributeNames": ["firstName", "lastName"]
        }
        with requests.get(self.url+'v1/persons/0001', params=params,**get_ssl_context()) as r:
            assert 200 == r.status_code
            assert {"firstName": "Jane2", "lastName": "Doe",} == r.json()
        with requests.get(self.url+'v1/persons/0002', params=params,**get_ssl_context()) as r:
            assert 200 == r.status_code
            assert {"firstName": "John1", "lastName": "Doe",} == r.json()
        with requests.get(self.url+'v1/persons/MISS', params=params,**get_ssl_context()) as r:
            assert 404 == r.status_code
        with requests.get(self.url+'v1/persons/0000', params=params,**get_ssl_context()) as r:
            assert 404 == r.status_code

if __name__ == '__main__':
    unittest.main(argv=['-v'])

