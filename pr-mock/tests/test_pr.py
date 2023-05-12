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

    def test_person(self):
        # Read, person does not exist
        with requests.get(self.url+'v1/persons/MISS', params={'transactionId': 'T0001'},**get_ssl_context()) as r:
            assert 404 == r.status_code

        # Create person
        data = {
            "status": "ACTIVE",
            "physicalStatus": "DEAD"
        }
        with requests.post(self.url+'v1/persons/0001', json=data, params={'transactionId': 'T0001'},**get_ssl_context()) as r:
            assert 201 == r.status_code

        # Read
        with requests.get(self.url+'v1/persons/0001', params={'transactionId': 'T0001'},**get_ssl_context()) as r:
            assert 200 == r.status_code
            assert {"personId": "0001", "status": "ACTIVE", "physicalStatus": "DEAD"} == r.json()

        # Create identity
        datai = {
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
        with requests.post(self.url+'v1/persons/0001/identities/001', json=datai, params={'transactionId': 'T0001'},**get_ssl_context()) as r:
            assert 201 == r.status_code

        # Read
        with requests.get(self.url+'v1/persons/0001', params={'transactionId': 'T0001'},**get_ssl_context()) as r:
            assert 200 == r.status_code
            assert {"personId": "0001", "status": "ACTIVE", "physicalStatus": "DEAD"} == r.json()
        with requests.get(self.url+'v1/persons/MISS/identities', params={'transactionId': 'T0001'},**get_ssl_context()) as r:
            assert 404 == r.status_code

        # Update
        data = {
            "status": "ACTIVE",
            "physicalStatus": "ALIVE"
        }
        with requests.put(self.url+'v1/persons/0001', json=data, params={'transactionId': 'T0001'},**get_ssl_context()) as r:
            assert 204 == r.status_code
        with requests.put(self.url+'v1/persons/MISS', json=data, params={'transactionId': 'T0001'},**get_ssl_context()) as r:
            assert 404 == r.status_code

        # Read
        with requests.get(self.url+'v1/persons/0001', params={'transactionId': 'T0001'},**get_ssl_context()) as r:
            assert 200 == r.status_code
            assert {"personId": "0001", "status": "ACTIVE", "physicalStatus": "ALIVE"} == r.json()

        # delete
        with requests.delete(self.url+'v1/persons/0001', params={'transactionId': 'T0001'},**get_ssl_context()) as r:
            assert 204 == r.status_code
        with requests.delete(self.url+'v1/persons/MISS', params={'transactionId': 'T0001'},**get_ssl_context()) as r:
            assert 404 == r.status_code

        # Read, person does not exist
        with requests.get(self.url+'v1/persons/MISS', params={'transactionId': 'T0001'},**get_ssl_context()) as r:
            assert 404 == r.status_code

    def test_identity(self):
        # Create person
        data = {
            "status": "ACTIVE",
            "physicalStatus": "DEAD"
        }
        with requests.post(self.url+'v1/persons/0000', json=data, params={'transactionId': 'T0001'},**get_ssl_context()) as r:
            assert 201 == r.status_code
        with requests.post(self.url+'v1/persons/0000', json=data, params={'transactionId': 'T0001'},**get_ssl_context()) as r:
            assert 409 == r.status_code

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
                "firstName": "Jane",
                "lastName": "Doe",
                "dateOfBirth": "1985-11-30",
                "gender": "F",
                "nationality": "FRA",
            }
        }
        with requests.post(self.url+'v1/persons/0001/identities/001', json=datai, params={'transactionId': 'T0001'},**get_ssl_context()) as r:
            assert 201 == r.status_code
        with requests.post(self.url+'v1/persons/MISS/identities/001', json=datai, params={'transactionId': 'T0001'},**get_ssl_context()) as r:
            assert 404 == r.status_code
        with requests.post(self.url+'v1/persons/0001/identities/001', json=datai, params={'transactionId': 'T0001'},**get_ssl_context()) as r:
            assert 409 == r.status_code

        datai["contextualData"]["enrollmentDate"] = "2020-01-11"
        with requests.post(self.url+'v1/persons/0001/identities', json=datai, params={'transactionId': 'T0001'},**get_ssl_context()) as r:
            assert 200 == r.status_code
            assert r.json()['identityId'] != ''
        with requests.post(self.url+'v1/persons/MISS/identities', json=datai, params={'transactionId': 'T0001'},**get_ssl_context()) as r:
            assert 404 == r.status_code

        # Read all identities
        with requests.get(self.url+'v1/persons/0001/identities', params={'transactionId': 'T0001'},**get_ssl_context()) as r:
            assert 200 == r.status_code
            assert 2 == len(r.json())
            assert r.json()[0]["contextualData"]["enrollmentDate"] != r.json()[1]["contextualData"]["enrollmentDate"]

        # Read 1 identity
        with requests.get(self.url+'v1/persons/0001/identities/001', params={'transactionId': 'T0001'},**get_ssl_context()) as r:
            assert 200 == r.status_code

        # Read missing identity
        with requests.get(self.url+'v1/persons/0001/identities/MISS', params={'transactionId': 'T0001'},**get_ssl_context()) as r:
            assert 404 == r.status_code
        with requests.get(self.url+'v1/persons/MISS/identities/001', params={'transactionId': 'T0001'},**get_ssl_context()) as r:
            assert 404 == r.status_code

        # reference not yet defined
        with requests.get(self.url+'v1/persons/0001/reference', params={'transactionId': 'T0001'},**get_ssl_context()) as r:
            assert 404 == r.status_code

        with requests.put(self.url+'v1/persons/0001/identities/001/reference', params={'transactionId': 'T0001'},**get_ssl_context()) as r:
            assert 204 == r.status_code
        with requests.put(self.url+'v1/persons/MISS/identities/001/reference', params={'transactionId': 'T0001'},**get_ssl_context()) as r:
            assert 404 == r.status_code
        with requests.put(self.url+'v1/persons/0001/identities/MISS/reference', params={'transactionId': 'T0001'},**get_ssl_context()) as r:
            assert 404 == r.status_code

        # reference
        with requests.get(self.url+'v1/persons/0001/reference', params={'transactionId': 'T0001'},**get_ssl_context()) as r:
            assert 200 == r.status_code
            assert r.json()['identityId'] != ''

        # person does not exist
        with requests.get(self.url+'v1/persons/MISS/reference', params={'transactionId': 'T0001'},**get_ssl_context()) as r:
            assert 404 == r.status_code
        with requests.get(self.url+'v1/persons/0000/reference', params={'transactionId': 'T0001'},**get_ssl_context()) as r:
            assert 404 == r.status_code

    def test_find_person(self):
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

        # query for all records
        with requests.post(self.url+'v1/persons', json=[{
                "attributeName":"firstName",
                "operator":"!=",
                "value":""
            }], params={'transactionId': 'T0001'},**get_ssl_context()) as r:
            assert 200 == r.status_code
            assert 3==len(r.json())
        with requests.post(self.url+'v1/persons', json=[{
                "attributeName":"firstName",
                "operator":"!=",
                "value":""
            }], params={'transactionId': 'T0001', 'offset':1, 'limit':1},**get_ssl_context()) as r:
            assert 200 == r.status_code
            assert 1==len(r.json())

        with requests.post(self.url+'v1/persons', json=[{
                "attributeName":"firstName",
                "operator":"!=",
                "value":""
            }], params={'transactionId': 'T0001', 'group':'true'},**get_ssl_context()) as r:
            assert 200 == r.status_code
            assert 2==len(r.json())

        with requests.post(self.url+'v1/persons', json=[{
                "attributeName":"firstName",
                "operator":"!=",
                "value":""
            }], params={'transactionId': 'T0001', 'reference':'true'},**get_ssl_context()) as r:
            assert 200 == r.status_code
            assert 1==len(r.json())

        with requests.post(self.url+'v1/persons', json=[{
                "attributeName":"age",
                "operator":"<",
                "value":40
            }], params={'transactionId': 'T0001'},**get_ssl_context()) as r:
            assert 200 == r.status_code
            assert 2==len(r.json())

if __name__ == '__main__':
    unittest.main(argv=['-v'])

