import os
import unittest
import sys
import base64
import hashlib

import requests

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
    def test_match(self):
        # Create person
        data = {
            "status": "ACTIVE",
            "physicalStatus": "DEAD"
        }
        with requests.post(self.url+'v1/persons/0001', json=data, params={'transactionId': 'T0001'},**get_ssl_context()) as r:
            assert 200 == r.status_code

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
                "dateOfBirth": "1985-11-30",
                "gender": "F",
                "nationality": "FRA",
            }
        }
        with requests.post(self.url+'v1/persons/0001/identities/001', json=data, params={'transactionId': 'T0001'},**get_ssl_context()) as r:
            assert 200 == r.status_code

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

    def test_query(self):
        # Create persons
        for n in range(10):
            data = {
                "status": "ACTIVE",
                "physicalStatus": "DEAD"
            }
            with requests.post(self.url+f'v1/persons/{n}', json=data, params={'transactionId': 'T0002'},**get_ssl_context()) as r:
                assert 200 == r.status_code

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
                assert 200 == r.status_code

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
            assert 200 == r.status_code

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
            assert 200 == r.status_code

        # Tests some reads
        params = {
            "attributeNames": ["firstName", "lastName"]
        }
        with requests.get(self.url+'v1/persons/0002', params=params,**get_ssl_context()) as r:
            assert 200 == r.status_code
            assert {"firstName": "Bob", "lastName": "Doe",} == r.json()

    def test_birth(self):
        # Create 2 persons
        data = {
            "status": "ACTIVE",
            "physicalStatus": "ALIVE"
        }
        with requests.post(self.url+'v1/persons/A', json=data, params={'transactionId': 'birth'},**get_ssl_context()) as r:
            assert 200 == r.status_code

        # Create identity
        data = {
            "identityType": "CIVIL",
            "status": "VALID",
            "contextualData": {
                "enrollmentDate": "2019-01-11",
            },
            "biographicData": {
                "firstName": "Albert",
                "lastName": "Smith",
                "dateOfBirth": "1985-11-30",
                "gender": "M",
                "nationality": "FRA",
            }
        }
        with requests.post(self.url+'v1/persons/A/identities/001', json=data, params={'transactionId': 'birth'},**get_ssl_context()) as r:
            assert 200 == r.status_code

        data = {
            "status": "ACTIVE",
            "physicalStatus": "ALIVE"
        }
        with requests.post(self.url+'v1/persons/B', json=data, params={'transactionId': 'birth'},**get_ssl_context()) as r:
            assert 200 == r.status_code

        # Create identity
        data = {
            "identityType": "CIVIL",
            "status": "VALID",
            "contextualData": {
                "enrollmentDate": "2019-01-11",
            },
            "biographicData": {
                "firstName": "Alice",
                "lastName": "Smith",
                "dateOfBirth": "1987-11-30",
                "gender": "F",
                "nationality": "FRA",
            }
        }
        with requests.post(self.url+'v1/persons/B/identities/001', json=data, params={'transactionId': 'birth'},**get_ssl_context()) as r:
            assert 200 == r.status_code


        # match mother
        data = {
            "firstName": "Alice",
            "lastName": "Smith",
        }
        with requests.post(self.url+'v1/persons/B/match', json=data,**get_ssl_context()) as r:
            assert 200 == r.status_code
            assert [] == r.json()

        # match father
        data = {
            "firstName": "Albert",
            "lastName": "Smith",
        }
        with requests.post(self.url+'v1/persons/A/match', json=data,**get_ssl_context()) as r:
            assert 200 == r.status_code
            assert [] == r.json()

        # read mother attributes
        params = {
            "attributeNames": ["dateOfBirth"]
        }
        with requests.get(self.url+'v1/persons/B', params=params,**get_ssl_context()) as r:
            assert 200 == r.status_code
            assert {"dateOfBirth": "1987-11-30"} == r.json()

        # read father attributes
        params = {
            "attributeNames": ["dateOfBirth"]
        }
        with requests.get(self.url+'v1/persons/A', params=params,**get_ssl_context()) as r:
            assert 200 == r.status_code
            assert {"dateOfBirth": "1985-11-30"} == r.json()

        # check if new born exists
        params = {
            "firstName": "Baby",
            "lastName": "Smith",
            "dateOfBirth": "2023-04-15"
        }
        with requests.get(self.url+'v1/persons', params=params,**get_ssl_context()) as r:
            assert 200 == r.status_code
            assert [] == r.json()


if __name__ == '__main__':
    unittest.main(argv=['-v'])

