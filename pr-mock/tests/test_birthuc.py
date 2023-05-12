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

    def test_birth(self):
        # Create 2 persons
        data = {
            "status": "ACTIVE",
            "physicalStatus": "ALIVE"
        }
        with requests.post(self.url+'v1/persons/A', json=data, params={'transactionId': 'birth'},**get_ssl_context()) as r:
            assert 201 == r.status_code

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
            assert 201 == r.status_code

        data = {
            "status": "ACTIVE",
            "physicalStatus": "ALIVE"
        }
        with requests.post(self.url+'v1/persons/B', json=data, params={'transactionId': 'birth'},**get_ssl_context()) as r:
            assert 201 == r.status_code

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
            assert 201 == r.status_code


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

