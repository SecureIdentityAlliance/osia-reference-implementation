import unittest
import sys
import os

import pr.model

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
    def test_person(self):
        # Create person, bad input
        data = {
            "status": "INACTIVE",
            "physicalStatus": "ALIVE",
            "notDefined": 12
        }
        with requests.post(self.url+'v1/persons/P0001', json=data, params={'transactionId': 'T0001'},**get_ssl_context()) as r:
            assert 400 == r.status_code

        # Create person
        data = {
            "status": "INACTIVE",
            "physicalStatus": "ALIVE",
        }
        with requests.post(self.url+'v1/persons/P0001', json=data, params={'transactionId': 'T0001'},**get_ssl_context()) as r:
            assert 201 == r.status_code

        # Create person already existing
        data = {
            "status": "INACTIVE",
            "physicalStatus": "ALIVE",
        }
        with requests.post(self.url+'v1/persons/P0001', json=data, params={'transactionId': 'T0001'},**get_ssl_context()) as r:
            assert 409 == r.status_code

        # read the created person
        with requests.get(self.url+'v1/persons/P0001', params={'transactionId': 'T0001'},**get_ssl_context()) as r:
            assert 200 == r.status_code
            assert 'Server' not in r.headers
            res = r.json()
            assert res['personId'] == 'P0001'
            assert list(res.keys()) == ['personId', 'status', 'physicalStatus']

        # read missing person
        with requests.get(self.url+'v1/persons/P0001-UNDEF', params={'transactionId': 'T0001'},**get_ssl_context()) as r:
            assert 404 == r.status_code

        # update the person
        data = {
            "status": "ACTIVE",
            "physicalStatus": "DEAD",
        }
        with requests.put(self.url+'v1/persons/P0001-UNDEF', json=data, params={'transactionId': 'T0001'},**get_ssl_context()) as r:
            assert 404 == r.status_code
        with requests.put(self.url+'v1/persons/P0001', json=data, params={'transactionId': 'T0001'},**get_ssl_context()) as r:
            assert 204 == r.status_code

        # check the data was modified in database
        with requests.get(self.url+'v1/persons/P0001', params={'transactionId': 'T0001'},**get_ssl_context()) as r:
            assert 200 == r.status_code
            assert 'Server' not in r.headers
            res = r.json()
            assert res['personId'] == 'P0001'
            assert res['status'] == 'ACTIVE'
            assert res['physicalStatus'] == 'DEAD'

        # update with non compliant json
        data = {
            "statusN": "ACTIVE",
            "physicalStatusN": "DEAD",
        }
        with requests.put(self.url+'v1/persons/P0001', json=data, params={'transactionId': 'T0001'},**get_ssl_context()) as r:
            assert 400 == r.status_code

        # delete the person
        with requests.delete(self.url+'v1/persons/P0001', params={'transactionId': 'T0001'},**get_ssl_context()) as r:
            assert 204 == r.status_code
        with requests.delete(self.url+'v1/persons/P0001', params={'transactionId': 'T0001'},**get_ssl_context()) as r:
            assert 404 == r.status_code
        # make sure it is no longer there
        with requests.get(self.url+'v1/persons/P0001', params={'transactionId': 'T0001'},**get_ssl_context()) as r:
            assert 404 == r.status_code

    def test_identity(self):
        # Create person
        data = {
            "status": "ACTIVE",
            "physicalStatus": "ALIVE",
        }
        with requests.post(self.url+'v1/persons/P0002', json=data, params={'transactionId': 'T0002'},**get_ssl_context()) as r:
            assert 201 == r.status_code

        # Create identity, bad data
        data = {
            "status": "ACTIVE",
            "physicalStatus": "ALIVE",
        }
        with requests.post(self.url+'v1/persons/P0002/identities', json=data, params={'transactionId': 'T0002'},**get_ssl_context()) as r:
            assert 400 == r.status_code

        # Create identity, missing mandatory custo field (firstName)
        data = {
            "status":"VALID",
            "identityType": "TEST",
            "galleries":["TEST"],
            "biographicData": {
                "lastName": "Doo"
            }
        }
        with requests.post(self.url+'v1/persons/P0002/identities', json=data, params={'transactionId': 'T0002'},**get_ssl_context()) as r:
            assert 400 == r.status_code

        # Create identity
        data = {
            "status":"VALID",
            "identityType": "TEST",
            "galleries":["TEST"],
            "biographicData": {
                "firstName": "John",
                "lastName": "Doo"
            },
            "documentData": [],
            "biometricData": [],
            "contextualData": {}
        }
        with requests.post(self.url+'v1/persons/P0002/identities', json=data, params={'transactionId': 'T0002'},**get_ssl_context()) as r:
            assert 200 == r.status_code
            res = r.json()
            assert res['identityId'] != ''
            assert list(res.keys()) == ['identityId']

        # Read the identity created
        with requests.get(self.url+'v1/persons/P0002/identities/'+res['identityId'], json=data, params={'transactionId': 'T0002'},**get_ssl_context()) as r:
            assert 200 == r.status_code
            res = r.json()
            del res['identityId']
            # default nationality defined in custo was added
            data['biographicData']['nationality'] = 'USA'
            assert res==data

        # Create identity with an ID
        data = {
            "status":"VALID",
            "identityType": "TEST",
            "galleries":["TEST"],
            "biographicData": {
                "firstName": "John2",
                "lastName": "Doo2"
            }
        }
        with requests.post(self.url+'v1/persons/P0002/identities/002', json=data, params={'transactionId': 'T0002'},**get_ssl_context()) as r:
            assert 200 == r.status_code
            res = r.json()
            assert res['identityId'] == '002'
            assert list(res.keys()) == ['identityId']

        # Read the identity created
        with requests.get(self.url+'v1/persons/P0002/identities/002', json=data, params={'transactionId': 'T0002'},**get_ssl_context()) as r:
            assert 200 == r.status_code

        # Create identity with an existing ID
        data = {
            "status":"VALID",
            "identityType": "TEST",
            "galleries":["TEST"],
            "biographicData": {
                "firstName": "John3",
                "lastName": "Doo3"
            }
        }
        with requests.post(self.url+'v1/persons/P0002/identities/002', json=data, params={'transactionId': 'T0002'},**get_ssl_context()) as r:
            assert 409 == r.status_code

        # Read all identities and check we have the 2 we have just created
        with requests.get(self.url+'v1/persons/P0002/identities', json=data, params={'transactionId': 'T0002'},**get_ssl_context()) as r:
            assert 200 == r.status_code
            res = r.json()
            assert len(res)==2
            assert res[1]['identityId'] == '002'

        # Update identity 002 when status is not CLAIMED
        data = {
            "status":"VALID",
            "identityType": "TEST2b",
            "galleries":["TEST"],
            "biographicData": {
                "firstName": "John2b",
                "lastName": "Doo2b"
            }
        }
        with requests.put(self.url+'v1/persons/P0002/identities/002', json=data, params={'transactionId': 'T0002'},**get_ssl_context()) as r:
            assert 403 == r.status_code

        # Change the status
        with requests.put(self.url+'v1/persons/P0002/identities/002/status', params={'transactionId': 'T0002', 'status': 'CLAIMED'},**get_ssl_context()) as r:
            assert 204 == r.status_code

        # Read the identity
        with requests.get(self.url+'v1/persons/P0002/identities/002', json=data, params={'transactionId': 'T0002'},**get_ssl_context()) as r:
            assert 200 == r.status_code
            res = r.json()
            assert res['status'] == 'CLAIMED'

        # Update identity 002
        data = {
            "status":"CLAIMED",
            "identityType": "TEST2b",
            "galleries":["TEST"],
            "biographicData": {
                "firstName": "John2b",
                "lastName": "Doo2b"
            }
        }
        with requests.put(self.url+'v1/persons/P0002/identities/002', json=data, params={'transactionId': 'T0002'},**get_ssl_context()) as r:
            assert 204 == r.status_code

        # Check data was updated
        with requests.get(self.url+'v1/persons/P0002/identities/002', json=data, params={'transactionId': 'T0002'},**get_ssl_context()) as r:
            assert 200 == r.status_code
            res = r.json()
            assert res['biographicData']['firstName'] == 'John2b'
            assert res['biographicData']['lastName'] == 'Doo2b'

        # Update identity 002 with bad json
        data = {
            "statusN":"CLAIMED",
            "identityType": "TEST2b",
            "galleries":["TEST"],
            "biographicData": {
                "firstName": "John2b",
                "lastName": "Doo2b"
            }
        }
        with requests.put(self.url+'v1/persons/P0002/identities/002', json=data, params={'transactionId': 'T0002'},**get_ssl_context()) as r:
            assert 400 == r.status_code

        # Update undef identity
        data = {
            "status":"CLAIMED",
            "identityType": "TEST2b",
            "galleries":["TEST"],
            "biographicData": {
                "firstName": "John2b",
                "lastName": "Doo2b"
            }
        }
        with requests.put(self.url+'v1/persons/P0002/identities/002-UNDEF', json=data, params={'transactionId': 'T0002'},**get_ssl_context()) as r:
            assert 404 == r.status_code

        # define the reference on identity 002
        with requests.put(self.url+'v1/persons/P0002/identities/002/reference', params={'transactionId': 'T0002'},**get_ssl_context()) as r:
            assert 403 == r.status_code
        # Change the status
        with requests.put(self.url+'v1/persons/P0002/identities/002/status', params={'transactionId': 'T0002', 'status': 'VALID'},**get_ssl_context()) as r:
            assert 204 == r.status_code
        with requests.put(self.url+'v1/persons/P0002/identities/002/reference', params={'transactionId': 'T0002'},**get_ssl_context()) as r:
            assert 204 == r.status_code
        with requests.put(self.url+'v1/persons/P0002/identities/002-UNDEF/status', params={'transactionId': 'T0002', 'status': 'VALID'},**get_ssl_context()) as r:
            assert 404 == r.status_code

        # read the reference
        with requests.get(self.url+'v1/persons/P0002/reference', params={'transactionId': 'T0002'},**get_ssl_context()) as r:
            assert 200 == r.status_code
            assert res['biographicData']['firstName'] == 'John2b'
            assert res['biographicData']['lastName'] == 'Doo2b'

        # delete identity
        with requests.delete(self.url+'v1/persons/P0002/identities/002', params={'transactionId': 'T0002'},**get_ssl_context()) as r:
            assert 204 == r.status_code
        with requests.get(self.url+'v1/persons/P0002/identities/002', json=data, params={'transactionId': 'T0002'},**get_ssl_context()) as r:
            assert 404 == r.status_code
        with requests.get(self.url+'v1/persons/P0002/identities', json=data, params={'transactionId': 'T0002'},**get_ssl_context()) as r:
            assert 200 == r.status_code
            res = r.json()
            assert len(res)==1
        with requests.delete(self.url+'v1/persons/P0002/identities/002', params={'transactionId': 'T0002'},**get_ssl_context()) as r:
            assert 404 == r.status_code

        # delete the person
        with requests.delete(self.url+'v1/persons/P0002', params={'transactionId': 'T0002'},**get_ssl_context()) as r:
            assert 204 == r.status_code

    def test_update_identity(self):
        # Create person
        data = {
            "status": "ACTIVE",
            "physicalStatus": "ALIVE",
        }
        with requests.post(self.url+'v1/persons/P0002', json=data, params={'transactionId': 'T0002'},**get_ssl_context()) as r:
            assert 201 == r.status_code

        # Create identity
        data = {
            "status":"CLAIMED",
            "identityType": "TEST",
            "galleries":["TEST"],
            "biographicData": {
                "firstName": "John",
                "lastName": "Doo",
                "nationality": "FRA"
            },
            "documentData": [],
            "biometricData": [
                {
                    "biometricType": "FINGER",
                    "biometricSubType": "RIGHT_INDEX",
                    "image": "SU1BR0U=", # "IMAGE" base64-encoded
                    "width": 500,
                    "height": 500,
                    "mimeType": "image/png",
                    "missing": [
                        {
                            "biometricSubType": "RIGHT_INDEX",
                            "presence": "BANDAGED"
                        }
                    ]
                }
            ],
            "contextualData": {}
        }
        with requests.post(self.url+'v1/persons/P0002/identities/001', json=data, params={'transactionId': 'T0002'},**get_ssl_context()) as r:
            assert 200 == r.status_code
            res = r.json()
            assert res['identityId'] == '001'
            assert list(res.keys()) == ['identityId']

        # Read the identity created
        with requests.get(self.url+'v1/persons/P0002/identities/001', params={'transactionId': 'T0002'},**get_ssl_context()) as r:
            assert 200 == r.status_code
            res = r.json()
            del res['identityId']
            assert res==data

        # Update identity - missing mandatory field
        data = {
            "status":"CLAIMED",
            # "identityType": "TEST2b",
            "galleries":["TEST"],
            "biographicData": {
                "firstName": "John2b",
                "lastName": "Doo2b"
            }
        }
        with requests.put(self.url+'v1/persons/P0002/identities/001', json=data, params={'transactionId': 'T0002'},**get_ssl_context()) as r:
            assert 400 == r.status_code

        # Update identity
        data = {
            "status":"CLAIMED",
            "identityType": "TEST2b",
            "galleries":["TEST"],
            "biographicData": {
                "firstName": "John2b",
                "lastName": "Doo2b"
            }
        }
        with requests.put(self.url+'v1/persons/P0002/identities/001', json=data, params={'transactionId': 'T0002'},**get_ssl_context()) as r:
            assert 204 == r.status_code

        # Check data was updated
        with requests.get(self.url+'v1/persons/P0002/identities/001', json=data, params={'transactionId': 'T0002'},**get_ssl_context()) as r:
            assert 200 == r.status_code
            res = r.json()
            assert res['biographicData']['firstName'] == 'John2b'
            assert res['biographicData']['lastName'] == 'Doo2b'
            assert res['biographicData']['nationality'] == 'USA'    # back to default since we did not specify FRA in the update payload
            assert len(res['biometricData']) == 0

        with requests.get(self.url+'monitoring/v1/metrics/gauges/nb_persons/count') as r:
            assert 200 == r.status_code
            assert 1 == r.json()
        with requests.get(self.url+'monitoring/v1/metrics/gauges/nb_identities/count') as r:
            assert 200 == r.status_code
            assert 1 == r.json()

        # delete the person
        with requests.delete(self.url+'v1/persons/P0002', params={'transactionId': 'T0002'},**get_ssl_context()) as r:
            assert 204 == r.status_code

    def test_partial_update_identity(self):
        # Create person
        data = {
            "status": "ACTIVE",
            "physicalStatus": "ALIVE",
        }
        with requests.post(self.url+'v1/persons/P0002', json=data, params={'transactionId': 'T0002'},**get_ssl_context()) as r:
            assert 201 == r.status_code

        # Create identity
        data = {
            "status":"CLAIMED",
            "identityType": "TEST",
            "galleries":["TEST"],
            "biographicData": {
                "firstName": "John",
                "lastName": "Doo",
                "nationality": "FRA"
            },
            "documentData": [],
            "biometricData": [
                {
                    "biometricType": "FINGER",
                    "biometricSubType": "RIGHT_INDEX",
                    "image": "SU1BR0U=", # "IMAGE" base64-encoded
                    "width": 500,
                    "height": 500,
                    "mimeType": "image/png",
                    "missing": [
                        {
                            "biometricSubType": "RIGHT_INDEX",
                            "presence": "BANDAGED"
                        }
                    ]
                }
            ],
            "contextualData": {
                "operator": 'OPE'
            }
        }
        with requests.post(self.url+'v1/persons/P0002/identities/001', json=data, params={'transactionId': 'T0002'},**get_ssl_context()) as r:
            assert 200 == r.status_code
            res = r.json()
            assert res['identityId'] == '001'
            assert list(res.keys()) == ['identityId']

        # Read the identity created
        with requests.get(self.url+'v1/persons/P0002/identities/001', params={'transactionId': 'T0002'},**get_ssl_context()) as r:
            assert 200 == r.status_code
            res = r.json()
            del res['identityId']
            assert res==data

        # Update identity - extra undefined field
        data = {
            "status":"CLAIMED",
            "identityType": "TEST2b",
            "galleries":["TEST"],
            "biographicData": {
                "firstName": "John2b",
                "lastName": "Doo2b",
                "undefined": "value"
            }
        }
        with requests.patch(self.url+'v1/persons/P0002/identities/001', json=data, params={'transactionId': 'T0002'},**get_ssl_context()) as r:
            assert 400 == r.status_code

        # Update identity
        data = {
            "biographicData": {
                "firstName": "John2b",
                "lastName": "Doo2b"
            }
        }
        with requests.patch(self.url+'v1/persons/P0002/identities/001', json=data, params={'transactionId': 'T0002'},**get_ssl_context()) as r:
            assert 204 == r.status_code

        # Check data was updated
        with requests.get(self.url+'v1/persons/P0002/identities/001', json=data, params={'transactionId': 'T0002'},**get_ssl_context()) as r:
            assert 200 == r.status_code
            res = r.json()
            assert res['biographicData']['firstName'] == 'John2b'
            assert res['biographicData']['lastName'] == 'Doo2b'
            assert res['biographicData']['nationality'] == 'FRA'    # was not changed
            assert len(res['biometricData']) == 1                   # was not changed
            assert res['contextualData']['operator'] == 'OPE'       # was not changed

        # Delete one field
        data = {
            "contextualData": {
                "operator": None
            }
        }
        with requests.patch(self.url+'v1/persons/P0002/identities/001', json=data, params={'transactionId': 'T0002'},**get_ssl_context()) as r:
            assert 204 == r.status_code

        # Check data was updated
        with requests.get(self.url+'v1/persons/P0002/identities/001', json=data, params={'transactionId': 'T0002'},**get_ssl_context()) as r:
            assert 200 == r.status_code
            res = r.json()
            assert res['biographicData']['firstName'] == 'John2b'
            assert res['biographicData']['lastName'] == 'Doo2b'
            assert res['biographicData']['nationality'] == 'FRA'    # was not changed
            assert len(res['biometricData']) == 1                   # was not changed
            assert 'operator' not in res['contextualData']          # was removed

        # Delete all biometricData
        data = {
            "biometricData": []
        }
        with requests.patch(self.url+'v1/persons/P0002/identities/001', json=data, params={'transactionId': 'T0002'},**get_ssl_context()) as r:
            assert 204 == r.status_code

        # Check data was updated
        with requests.get(self.url+'v1/persons/P0002/identities/001', json=data, params={'transactionId': 'T0002'},**get_ssl_context()) as r:
            assert 200 == r.status_code
            res = r.json()
            assert res['biographicData']['firstName'] == 'John2b'
            assert res['biographicData']['lastName'] == 'Doo2b'
            assert res['biographicData']['nationality'] == 'FRA'    # was not changed
            assert len(res['biometricData']) == 0                   # was removed

        with requests.get(self.url+'monitoring/v1/metrics/gauges/nb_persons/count') as r:
            assert 200 == r.status_code
            assert 1 == r.json()
        with requests.get(self.url+'monitoring/v1/metrics/gauges/nb_identities/count') as r:
            assert 200 == r.status_code
            assert 1 == r.json()
        with requests.get(self.url+'monitoring/v1/metrics/gauges/nb_biometricdata/count') as r:
            assert 200 == r.status_code
            assert 0 == r.json()
        
        # delete the person
        with requests.delete(self.url+'v1/persons/P0002', params={'transactionId': 'T0002'},**get_ssl_context()) as r:
            assert 204 == r.status_code

    def test_query(self):
        # Insert test data
        # Create person1 with 1 identity
        data = {
            "status": "ACTIVE",
            "physicalStatus": "ALIVE",
        }
        with requests.post(self.url+'v1/persons/P0003-1', json=data, params={'transactionId': 'T0003'},**get_ssl_context()) as r:
            assert 201 == r.status_code
        data = {
            "status":"VALID",
            "identityType": "TEST",
            "galleries":["TESTA"],
            "biographicData": {
                "firstName": "JohnA",
                "lastName": "Doo"
            }
        }
        with requests.post(self.url+'v1/persons/P0003-1/identities/001', json=data, params={'transactionId': 'T0003'},**get_ssl_context()) as r:
            assert 200 == r.status_code

        # Create person2 with 2 identity
        data = {
            "status": "ACTIVE",
            "physicalStatus": "ALIVE",
        }
        with requests.post(self.url+'v1/persons/P0003-2', json=data, params={'transactionId': 'T0003'},**get_ssl_context()) as r:
            assert 201 == r.status_code
        data = {
            "status":"VALID",
            "identityType": "TEST",
            "galleries":["TESTA"],
            "biographicData": {
                "firstName": "JohnBA",
                "lastName": "Doo"
            }
        }
        with requests.post(self.url+'v1/persons/P0003-2/identities/001', json=data, params={'transactionId': 'T0003'},**get_ssl_context()) as r:
            assert 200 == r.status_code
        with requests.put(self.url+'v1/persons/P0003-2/identities/001/reference', params={'transactionId': 'T0003'},**get_ssl_context()) as r:
            assert 204 == r.status_code
        data = {
            "status":"VALID",
            "identityType": "TEST",
            "galleries":["TESTB"],
            "biographicData": {
                "firstName": "JohnBB",
                "lastName": "Doo"
            }
        }
        with requests.post(self.url+'v1/persons/P0003-2/identities/002', json=data, params={'transactionId': 'T0003'},**get_ssl_context()) as r:
            assert 200 == r.status_code

        # test galleries
        with requests.get(self.url+'v1/galleries', params={'transactionId': 'T0003'},**get_ssl_context()) as r:
            assert 200 == r.status_code
            assert r.json() == ['TESTA', 'TESTB'] or r.json() == ['TESTB', 'TESTA']

        # Now we can test the queries
        
        # Run query, bad input
        data = dict(
            enrollmentId= "0001",
        )
        with requests.post(self.url+'v1/persons', json=data, params={'transactionId': 'T0003'},**get_ssl_context()) as r:
            assert 400 == r.status_code

        # Run query, no candidates
        data = [dict(
            attributeName="firstName",
            operator="=",
            value="John"
        )]
        with requests.post(self.url+'v1/persons', json=data, params={'transactionId': 'T0003'},**get_ssl_context()) as r:
            assert 200 == r.status_code
            assert 'Server' not in r.headers
            res = r.json()
            assert len(res) == 0

        # Run query, 1 candidate
        data = [dict(
            attributeName="firstName",
            operator="=",
            value="JohnA"
        )]
        with requests.post(self.url+'v1/persons', json=data, params={'transactionId': 'T0003'},**get_ssl_context()) as r:
            assert 200 == r.status_code
            res = r.json()
            assert len(res) == 1
            assert res == [{'personId': 'P0003-1', 'identityId': '001'}]

        # Run query, 2 predicates
        data = [
            dict(
                attributeName="firstName",
                operator=">",
                value="John"
            ),
            dict(
                attributeName="firstName",
                operator="<",
                value="JohnZ"
            ),
        ]
        with requests.post(self.url+'v1/persons', json=data, params={'transactionId': 'T0003'},**get_ssl_context()) as r:
            assert 200 == r.status_code
            res = r.json()
            assert len(res) == 3
            assert res == [
                {'personId': 'P0003-1', 'identityId': '001'},
                {'personId': 'P0003-2', 'identityId': '001'},
                {'personId': 'P0003-2', 'identityId': '002'}
                ]

        # Run query, N candidates
        data = [dict(
            attributeName="lastName",
            operator="=",
            value="Doo"
        )]
        with requests.post(self.url+'v1/persons', json=data, params={'transactionId': 'T0003'},**get_ssl_context()) as r:
            assert 200 == r.status_code
            res = r.json()
            assert len(res) == 3
            assert res == [
                {'personId': 'P0003-1', 'identityId': '001'},
                {'personId': 'P0003-2', 'identityId': '001'},
                {'personId': 'P0003-2', 'identityId': '002'}
                ]
            
        # Run query, remaining operators
        data = [
            dict(
                attributeName="firstName",
                operator=">=",
                value="John"
            ),
            dict(
                attributeName="firstName",
                operator="<=",
                value="JohnZ"
            ),
            dict(
                attributeName="firstName",
                operator="!=",
                value="Bob"
            ),
        ]
        with requests.post(self.url+'v1/persons', json=data, params={'transactionId': 'T0003'},**get_ssl_context()) as r:
            assert 200 == r.status_code
            res = r.json()
            assert len(res) == 3
            assert res == [
                {'personId': 'P0003-1', 'identityId': '001'},
                {'personId': 'P0003-2', 'identityId': '001'},
                {'personId': 'P0003-2', 'identityId': '002'}
                ]

        # Run query, bad operator
        data = [
            dict(
                attributeName="firstName",
                operator="#",
                value="John"
            ),
        ]
        with requests.post(self.url+'v1/persons', json=data, params={'transactionId': 'T0003'},**get_ssl_context()) as r:
            assert 400 == r.status_code

        #
        # Test options
        #

        # group option
        data = [dict(
            attributeName="lastName",
            operator="=",
            value="Doo"
        )]
        with requests.post(self.url+'v1/persons', json=data, params={'transactionId': 'T0003', 'group':'true'},**get_ssl_context()) as r:
            assert 200 == r.status_code
            res = r.json()
            assert len(res) == 2
            assert res == [
                {'personId': 'P0003-1'},
                {'personId': 'P0003-2'}
                ]

        # reference option
        data = [dict(
            attributeName="lastName",
            operator="=",
            value="Doo"
        )]
        with requests.post(self.url+'v1/persons', json=data, params={'transactionId': 'T0003', 'reference':'true'},**get_ssl_context()) as r:
            assert 200 == r.status_code
            res = r.json()
            assert len(res) == 1
            assert res == [
                {'personId': 'P0003-2', 'identityId': '001'}
                ]

        # reference & group option
        data = [dict(
            attributeName="lastName",
            operator="=",
            value="Doo"
        )]
        with requests.post(self.url+'v1/persons', json=data, params={'transactionId': 'T0003', 'reference':'true', 'group':'true'},**get_ssl_context()) as r:
            assert 200 == r.status_code
            res = r.json()
            assert len(res) == 1
            assert res == [
                {'personId': 'P0003-2'}
                ]

        # gallery option
        data = [dict(
            attributeName="lastName",
            operator="=",
            value="Doo"
        )]
        with requests.post(self.url+'v1/persons', json=data, params={'transactionId': 'T0003', 'gallery':'TESTB'},**get_ssl_context()) as r:
            assert 200 == r.status_code
            res = r.json()
            assert len(res) == 1
            assert res == [
                {'personId': 'P0003-2', 'identityId': '002'}
                ]
        with requests.post(self.url+'v1/persons', json=data, params={'transactionId': 'T0003', 'gallery':'TESTA'},**get_ssl_context()) as r:
            assert 200 == r.status_code
            res = r.json()
            assert len(res) == 2
            assert res == [
                {'personId': 'P0003-1', 'identityId': '001'},
                {'personId': 'P0003-2', 'identityId': '001'}
                ]

        # limit & offset
        data = [dict(
            attributeName="lastName",
            operator="=",
            value="Doo"
        )]
        with requests.post(self.url+'v1/persons', json=data, params={'transactionId': 'T0003', 'limit':'1'},**get_ssl_context()) as r:
            assert 200 == r.status_code
            res = r.json()
            assert len(res) == 1
            assert res == [
                {'personId': 'P0003-1', 'identityId': '001'},
                # {'personId': 'P0003-2', 'identityId': '001'},
                # {'personId': 'P0003-2', 'identityId': '002'}
                ]
        with requests.post(self.url+'v1/persons', json=data, params={'transactionId': 'T0003', 'limit':'1', 'offset':'1'},**get_ssl_context()) as r:
            assert 200 == r.status_code
            res = r.json()
            assert len(res) == 1
            assert res == [
                # {'personId': 'P0003-1', 'identityId': '001'},
                {'personId': 'P0003-2', 'identityId': '001'},
                # {'personId': 'P0003-2', 'identityId': '002'}
                ]

        # delete the person
        with requests.delete(self.url+'v1/persons/P0003-1', params={'transactionId': 'T0003'},**get_ssl_context()) as r:
            assert 204 == r.status_code
        with requests.delete(self.url+'v1/persons/P0003-2', params={'transactionId': 'T0003'},**get_ssl_context()) as r:
            assert 204 == r.status_code

    def test_fullcusto(self):
        # Create person1 with 1 identity
        data = {
            "status": "ACTIVE",
            "physicalStatus": "ALIVE",
        }
        with requests.post(self.url+'v1/persons/P0003-1', json=data, params={'transactionId': 'T0003'},**get_ssl_context()) as r:
            assert 201 == r.status_code
        data = {
            "status":"VALID",
            "identityType": "TEST",
            "galleries":["TESTA"],
            "biographicData": {
                "firstName": "JohnA",
                "lastName": "Doo",
                "dateOfBirth": "1980-12-25",
                "nationality": "FRA",
                "fByte": "VEVTVA==",    # base64 for 'TEST'
                "fBoolean": True,
                "fInteger32": 32,
                "fInteger64": 64,
                "fNumberFloat": 1.2,
                "fNumberDouble": 2.3
            },
            "documentData": [],
            "biometricData": [],
            "contextualData": {
                "operator": "OSIA",
                "operationDateTime": "2024-01-31T18:26:00+00:00",
                "device": {
                    "name": "FROS1-0000",
                    "brand": "HP"
                }
            }
        }
        if os.environ.get('SQLITE', '0')=='1':
            # timezone not supported by sqlite
            data['contextualData']['operationDateTime'] = "2024-01-31T18:26:00"
        with requests.post(self.url+'v1/persons/P0003-1/identities/001', json=data, params={'transactionId': 'T0003'},**get_ssl_context()) as r:
            assert 200 == r.status_code

        # Read the identity created
        with requests.get(self.url+'v1/persons/P0003-1/identities/001', params={'transactionId': 'T0003'},**get_ssl_context()) as r:
            assert 200 == r.status_code
            res = r.json()
            del res['identityId']
            assert res==data

        # test galleries
        with requests.get(self.url+'v1/galleries', params={'transactionId': 'T0003'},**get_ssl_context()) as r:
            assert 200 == r.status_code
            assert r.json() == ['TESTA']

        # test missing required property in subobject of custo (JSON type)
        data = {
            "status":"VALID",
            "identityType": "TEST",
            "galleries":["TESTA"],
            "biographicData": {
                "firstName": "JohnA",
                "lastName": "Doo",
                "dateOfBirth": "1980-12-25",
                "nationality": "FRA",
                "fByte": "VEVTVA==",    # base64 for 'TEST'
                "fBoolean": True,
                "fInteger32": 32,
                "fInteger64": 64,
                "fNumberFloat": 1.2,
                "fNumberDouble": 2.3
            },
            "documentData": [],
            "biometricData": [],
            "contextualData": {
                "operator": "OSIA",
                "operationDateTime": "2024-01-31T18:26:00+00:00",
                "device": {
                    "brand": "HP"
                }
            }
        }
        if os.environ.get('SQLITE', '0')=='1':
            # timezone not supported by sqlite
            data['contextualData']['operationDateTime'] = "2024-01-31T18:26:00"
        with requests.post(self.url+'v1/persons/P0003-1/identities/002', json=data, params={'transactionId': 'T0003'},**get_ssl_context()) as r:
            assert 400 == r.status_code

        with requests.delete(self.url+'v1/persons/P0003-1', params={'transactionId': 'T0003'},**get_ssl_context()) as r:
            assert 204 == r.status_code

    def test_identity_biometric_data(self):
        # Create person
        data = {
            "status": "ACTIVE",
            "physicalStatus": "ALIVE",
        }
        with requests.post(self.url+'v1/persons/P0004', json=data, params={'transactionId': 'T0004'},**get_ssl_context()) as r:
            assert 201 == r.status_code

        # Create identity
        data = {
            "status":"VALID",
            "identityType": "TEST",
            "galleries":["TEST"],
            "biographicData": {
                "firstName": "John",
                "lastName": "Doo"
            },
            "biometricData": [
                {
                    "biometricType": "FINGER",
                    "biometricSubType": "RIGHT_INDEX",
                    "image": "SU1BR0U=", # "IMAGE" base64-encoded
                    "width": 500,
                    "height": 500,
                    "mimeType": "image/png",
                    "missing": [
                        {
                            "biometricSubType": "RIGHT_INDEX",
                            "presence": "BANDAGED"
                        }
                    ]
                }
            ],
            "documentData": [],
            "contextualData": {}
        }
        with requests.post(self.url+'v1/persons/P0004/identities/001', json=data, params={'transactionId': 'T0004'},**get_ssl_context()) as r:
            assert 200 == r.status_code
            res = r.json()
            assert res['identityId'] == '001'

        # Read the identity created
        with requests.get(self.url+'v1/persons/P0004/identities/001',params={'transactionId': 'T0004'},**get_ssl_context()) as r:
            assert 200 == r.status_code
            res = r.json()
            del res['identityId']
            # default nationality defined in custo was added
            data['biographicData']['nationality'] = 'USA'
            assert res==data

        with requests.delete(self.url+'v1/persons/P0004', params={'transactionId': 'T0004'},**get_ssl_context()) as r:
            assert 204 == r.status_code

    def test_identity_document_data(self):
        # Create person
        data = {
            "status": "ACTIVE",
            "physicalStatus": "ALIVE",
        }
        with requests.post(self.url+'v1/persons/P0005', json=data, params={'transactionId': 'T0005'},**get_ssl_context()) as r:
            assert 201 == r.status_code

        # Create identity
        data = {
            "status":"VALID",
            "identityType": "TEST",
            "galleries":["TEST"],
            "biographicData": {
                "firstName": "John",
                "lastName": "Doo"
            },
            "biometricData": [],
            "documentData": [
                {
                    "documentType": "FORM",
                    "documentTypeOther": "string",
                    "instance": "string",
                    "parts": [
                        {
                            "pages": [
                                1
                            ],
                            "data": "c3RyaW5n",
                            "dataRef": "http://server.com/buffer?id=00003",
                            "width": 1980,
                            "height": 1200,
                            "mimeType": "application/pdf",
                            "captureDate": "2019-05-21T12:00:00+00:00",
                            "captureDevice": "string"
                        }
                    ]
                }
            ],
            "contextualData": {}
        }
        if os.environ.get('SQLITE', '0')=='1':
            # timezone not supported by sqlite
            data['documentData'][0]['parts'][0]['captureDate'] = "2019-05-21T12:00:00"
        with requests.post(self.url+'v1/persons/P0005/identities/001', json=data, params={'transactionId': 'T0005'},**get_ssl_context()) as r:
            assert 200 == r.status_code
            res = r.json()
            assert res['identityId'] == '001'

        # Read the identity created
        with requests.get(self.url+'v1/persons/P0005/identities/001',params={'transactionId': 'T0005'},**get_ssl_context()) as r:
            assert 200 == r.status_code
            res = r.json()
            del res['identityId']
            # default nationality defined in custo was added
            data['biographicData']['nationality'] = 'USA'
            assert res==data

        with requests.delete(self.url+'v1/persons/P0005', params={'transactionId': 'T0005'},**get_ssl_context()) as r:
            assert 204 == r.status_code

    def test_merge_person(self):
        # Insert test data
        # Create person1 with 1 identity
        data = {
            "status": "ACTIVE",
            "physicalStatus": "ALIVE",
        }
        with requests.post(self.url+'v1/persons/P0006-1', json=data, params={'transactionId': 'T0006'},**get_ssl_context()) as r:
            assert 201 == r.status_code
        data = {
            "status":"VALID",
            "identityType": "TEST",
            "galleries":["TESTA"],
            "biographicData": {
                "firstName": "JohnA",
                "lastName": "Doo"
            }
        }
        with requests.post(self.url+'v1/persons/P0006-1/identities/001', json=data, params={'transactionId': 'T0006'},**get_ssl_context()) as r:
            assert 200 == r.status_code

        # Create person2 with 2 identity
        data = {
            "status": "ACTIVE",
            "physicalStatus": "ALIVE",
        }
        with requests.post(self.url+'v1/persons/P0006-2', json=data, params={'transactionId': 'T0006'},**get_ssl_context()) as r:
            assert 201 == r.status_code
        data = {
            "status":"VALID",
            "identityType": "TEST",
            "galleries":["TESTA"],
            "biographicData": {
                "firstName": "JohnBA",
                "lastName": "Doo"
            }
        }
        with requests.post(self.url+'v1/persons/P0006-2/identities/001', json=data, params={'transactionId': 'T0006'},**get_ssl_context()) as r:
            assert 200 == r.status_code
        with requests.put(self.url+'v1/persons/P0006-2/identities/001/reference', params={'transactionId': 'T0006'},**get_ssl_context()) as r:
            assert 204 == r.status_code
        data = {
            "status":"VALID",
            "identityType": "TEST",
            "galleries":["TESTB"],
            "biographicData": {
                "firstName": "JohnBB",
                "lastName": "Doo"
            }
        }
        with requests.post(self.url+'v1/persons/P0006-2/identities/002', json=data, params={'transactionId': 'T0006'},**get_ssl_context()) as r:
            assert 200 == r.status_code

        # Create person3 with 1 identity
        data = {
            "status": "ACTIVE",
            "physicalStatus": "ALIVE",
        }
        with requests.post(self.url+'v1/persons/P0006-3', json=data, params={'transactionId': 'T0006'},**get_ssl_context()) as r:
            assert 201 == r.status_code
        data = {
            "status":"VALID",
            "identityType": "TEST",
            "galleries":["TESTA"],
            "biographicData": {
                "firstName": "JohnA",
                "lastName": "Doo"
            }
        }
        with requests.post(self.url+'v1/persons/P0006-3/identities/999', json=data, params={'transactionId': 'T0006'},**get_ssl_context()) as r:
            assert 200 == r.status_code

        # should be OK
        with requests.post(self.url+'v1/persons/P0006-2/merge/P0006-3', params={'transactionId': 'T0006'},**get_ssl_context()) as r:
            assert 204 == r.status_code
        # Read the identity created
        with requests.get(self.url+'v1/persons/P0006-2/identities',params={'transactionId': 'T0006'},**get_ssl_context()) as r:
            assert 200 == r.status_code
            res = r.json()
            assert len(res) == 3

        # merge should fail
        with requests.post(self.url+'v1/persons/P0006-2/merge/P0006-3', params={'transactionId': 'T0006'},**get_ssl_context()) as r:
            assert 404 == r.status_code

        # merge should fail (identityId duplicate)
        with requests.post(self.url+'v1/persons/P0006-2/merge/P0006-1', params={'transactionId': 'T0006'},**get_ssl_context()) as r:
            assert 409 == r.status_code

        with requests.get(self.url+'monitoring/v1/metrics/gauges/nb_persons/count') as r:
            assert 200 == r.status_code
            assert 2 == r.json()
        with requests.get(self.url+'monitoring/v1/metrics/gauges/nb_identities/count') as r:
            assert 200 == r.status_code
            assert 4 == r.json()

        # test galleries
        with requests.get(self.url+'v1/galleries', params={'transactionId': 'T0006'},**get_ssl_context()) as r:
            assert 200 == r.status_code
            assert r.json() == ['TESTA', 'TESTB'] or r.json() == ['TESTB', 'TESTA']

        # test gallery content
        with requests.get(self.url+'v1/galleries/TESTA', params={'transactionId': 'T0006'},**get_ssl_context()) as r:
            assert 200 == r.status_code
            assert r.json() == [ {'personId': 'P0006-1', 'identityId': '001'}, {'personId': 'P0006-2', 'identityId': '001'}, {'personId': 'P0006-2', 'identityId': '999'}]
        with requests.get(self.url+'v1/galleries/TESTB', params={'transactionId': 'T0006'},**get_ssl_context()) as r:
            assert 200 == r.status_code
            assert r.json() == [{'personId': 'P0006-2', 'identityId': '002'}]

        # test offset & limit
        with requests.get(self.url+'v1/galleries/TESTA', params={'transactionId': 'T0006', 'offset': 1, 'limit': 1},**get_ssl_context()) as r:
            assert 200 == r.status_code
            assert r.json() == [ 
                # {'personId': 'P0006-1', 'identityId': '001'}, 
                {'personId': 'P0006-2', 'identityId': '001'}, 
                # {'personId': 'P0006-2', 'identityId': '999'}
                ]

        # clean up data
        with requests.delete(self.url+'v1/persons/P0006-1', params={'transactionId': 'T0006'},**get_ssl_context()) as r:
            assert 204 == r.status_code
        with requests.delete(self.url+'v1/persons/P0006-2', params={'transactionId': 'T0006'},**get_ssl_context()) as r:
            assert 204 == r.status_code

        with requests.get(self.url+'monitoring/v1/metrics/gauges/nb_persons/count') as r:
            assert 200 == r.status_code
            assert 0 == r.json()
        with requests.get(self.url+'monitoring/v1/metrics/gauges/nb_identities/count') as r:
            assert 200 == r.status_code
            assert 0 == r.json()

    def test_move_identity(self):
        # Insert test data
        # Create person1 with 1 identity
        data = {
            "status": "ACTIVE",
            "physicalStatus": "ALIVE",
        }
        with requests.post(self.url+'v1/persons/P0007-1', json=data, params={'transactionId': 'T0007'},**get_ssl_context()) as r:
            assert 201 == r.status_code
        data = {
            "status":"VALID",
            "identityType": "TEST",
            "galleries":["TESTA"],
            "biographicData": {
                "firstName": "JohnA",
                "lastName": "Doo"
            }
        }
        with requests.post(self.url+'v1/persons/P0007-1/identities/001', json=data, params={'transactionId': 'T0007'},**get_ssl_context()) as r:
            assert 200 == r.status_code

        # Create person2 with 2 identity
        data = {
            "status": "ACTIVE",
            "physicalStatus": "ALIVE",
        }
        with requests.post(self.url+'v1/persons/P0007-2', json=data, params={'transactionId': 'T0007'},**get_ssl_context()) as r:
            assert 201 == r.status_code
        data = {
            "status":"VALID",
            "identityType": "TEST",
            "galleries":["TESTA"],
            "biographicData": {
                "firstName": "JohnBA",
                "lastName": "Doo"
            }
        }
        with requests.post(self.url+'v1/persons/P0007-2/identities/001', json=data, params={'transactionId': 'T0007'},**get_ssl_context()) as r:
            assert 200 == r.status_code
        with requests.put(self.url+'v1/persons/P0007-2/identities/001/reference', params={'transactionId': 'T0007'},**get_ssl_context()) as r:
            assert 204 == r.status_code
        data = {
            "status":"VALID",
            "identityType": "TEST",
            "galleries":["TESTB"],
            "biographicData": {
                "firstName": "JohnBB",
                "lastName": "Doo"
            }
        }
        with requests.post(self.url+'v1/persons/P0007-2/identities/002', json=data, params={'transactionId': 'T0006'},**get_ssl_context()) as r:
            assert 200 == r.status_code


        # move should fail
        with requests.post(self.url+'v1/persons/P0007-1/move/P0007-2/identities/001', params={'transactionId': 'T0007'},**get_ssl_context()) as r:
            assert 409 == r.status_code
        with requests.post(self.url+'v1/persons/P0007-1/move/P0007-2/identities/003', params={'transactionId': 'T0007'},**get_ssl_context()) as r:
            assert 404 == r.status_code
        with requests.post(self.url+'v1/persons/P0007-1/move/P0099-2/identities/001', params={'transactionId': 'T0007'},**get_ssl_context()) as r:
            assert 404 == r.status_code

        # OK
        with requests.post(self.url+'v1/persons/P0007-1/move/P0007-2/identities/002', params={'transactionId': 'T0007'},**get_ssl_context()) as r:
            assert 204 == r.status_code

        # Read the identity created
        with requests.get(self.url+'v1/persons/P0007-1/identities',params={'transactionId': 'T0007'},**get_ssl_context()) as r:
            assert 200 == r.status_code
            res = r.json()
            assert len(res) == 2

        with requests.get(self.url+'monitoring/v1/metrics/gauges/nb_persons/count') as r:
            assert 200 == r.status_code
            assert 2 == r.json()
        with requests.get(self.url+'monitoring/v1/metrics/gauges/nb_identities/count') as r:
            assert 200 == r.status_code
            assert 3 == r.json()

        with requests.delete(self.url+'v1/persons/P0007-1', params={'transactionId': 'T0007'},**get_ssl_context()) as r:
            assert 204 == r.status_code
        with requests.delete(self.url+'v1/persons/P0007-2', params={'transactionId': 'T0007'},**get_ssl_context()) as r:
            assert 204 == r.status_code

        with requests.get(self.url+'monitoring/v1/metrics/gauges/nb_persons/count') as r:
            assert 200 == r.status_code
            assert 0 == r.json()
        with requests.get(self.url+'monitoring/v1/metrics/gauges/nb_identities/count') as r:
            assert 200 == r.status_code
            assert 0 == r.json()

    def test_no_transaction_id(self):
        data = {
            "status": "INACTIVE",
            "physicalStatus": "ALIVE",
        }
        with requests.post(self.url+'v1/persons/P0001', json=data, **get_ssl_context()) as r:
            assert 400 == r.status_code

# XXX test insert with all fields and check all fields are returned
# XXX test update with all fields and check all fields are returned modified

if __name__ == '__main__':
    unittest.main(argv=['-v'])

