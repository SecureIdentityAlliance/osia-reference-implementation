import unittest
import sys

import requests

# [---CUSTO---]
import os
import hashlib
# [---CUSTO---]

URL = "http://localhost:8080/"

# ______________________________________________________________________________
if __name__ == '__main__':

    if len(sys.argv)>1:
        URL = sys.argv[1]

    class TestEnrollment(unittest.TestCase):

        @property
        def url(self):
            global URL
            return URL

else:
    from . import TestEnrollment

def get_ssl_context():
    kw = {}
    kw['verify'] = False
    return kw

# [---CUSTO---]
#_______________________________________________________________________________
class TestNominal(TestEnrollment):
    def test_ok(self):
        data = dict(
            # enrollmentId= "0001",
            # status= "IN_PROGRESS",
            enrollmentType= "FULL",
            enrollmentFlags=dict(timeout=3600),
            requestData= dict(requestType= "DEMO"),
            contextualData= dict(
                enrollmentDate= "2019-01-11T17:26:00+00:00"
            ),
            biographicData= dict(
                firstName= "John",
                lastName= "Doe",
                dateOfBirth= "1985-11-30",
                gender= "M",
                nationality= "FRA"
            ),
            biometricData=[],
            documentData=[]
        )
        if os.environ.get('SQLITE', None)=='1':
            # SQLite is not processing date-time with the offset
            data['contextualData']['enrollmentDate'] = "2019-01-11T17:26:00"

        # Create enrollment
        with requests.post(self.url+'v1/enrollments/0001', json=data, params={'transactionId': 'T0001', 'finalize': 'false'},**get_ssl_context()) as r:
            assert 204 == r.status_code
            assert 'Server' not in r.headers
            enrollment_id = '0001'

        # Insert one buffer
        bdata = b'LEFT_INDEX'
        H = {'content-type': 'image/wsq'}
        S = hashlib.sha1()
        S.update(bdata)
        H['Digest'] = 'SHA='+S.hexdigest()
        with requests.post(self.url+'v1/enrollments/'+enrollment_id+'/buffer', data=bdata, params={'transactionId': 'T0001'}, headers=H, **get_ssl_context()) as r:
            assert 201 == r.status_code
            assert 'Server' not in r.headers
            buffer_id = r.json()['bufferId']

        # Read the buffer
        with requests.get(self.url+'v1/enrollments/'+enrollment_id+'/buffer/'+buffer_id, params={'transactionId': 'T0001'}, **get_ssl_context()) as r:
            assert 200 == r.status_code
            assert 'Server' not in r.headers
            assert 'image/wsq' == r.headers.get('content-type')
            assert bdata == r.content

        # Update enrollment with 2 biometric data
        data['biometricData'] = [
            dict(
                biometricType= "FINGER",
                biometricSubType= "RIGHT_INDEX",
                image= "UklHSFRfSU5ERVg=",
                mimeType='image/wsq'
            ),
            dict(
                biometricType= "FINGER",
                biometricSubType= "LEFT_INDEX",
                imageRef= self.url+'v1/enrollments/0001/buffer/'+buffer_id,
                mimeType='image/wsq'
            )
        ]
        with requests.put(self.url+'v1/enrollments/0001', json=data, params={'transactionId': 'T0001', 'finalize': 'false'},**get_ssl_context()) as r:
            assert 204 == r.status_code

        # use metrics to check data is well inserted
        with requests.get(self.url+'monitoring/v1/metrics/gauges/nb_enrollments/count',**get_ssl_context()) as r:
            assert 200 == r.status_code
            assert 1 == r.json()
        with requests.get(self.url+'monitoring/v1/metrics/gauges/nb_biometricdata/count',**get_ssl_context()) as r:
            assert 200 == r.status_code
            assert 2 == r.json()
        with requests.get(self.url+'monitoring/v1/metrics/gauges/nb_buffers/count',**get_ssl_context()) as r:
            assert 200 == r.status_code
            assert 1 == r.json()

        # Read enrollment
        with requests.get(self.url+'v1/enrollments/0001', params={'transactionId': 'T0001'},**get_ssl_context()) as r:
            assert 200 == r.status_code
            data2 = r.json()
            expected_data = {'enrollmentId': '0001', 'status': 'IN_PROGRESS'}
            expected_data.update(data)
            assert data2==expected_data

        # test partial update
        data3 = {
            "biographicData": {
                "firstName": "John2",
                "lastName": "Doe2"
            }
        }
        with requests.patch(self.url+'v1/enrollments/0001', json=data3, params={'transactionId': 'T0001'},**get_ssl_context()) as r:
            assert 204 == r.status_code

        # Read enrollment
        expected_data['biographicData']['firstName'] = "John2"
        expected_data['biographicData']['lastName'] = "Doe2"
        with requests.get(self.url+'v1/enrollments/0001', params={'transactionId': 'T0001'},**get_ssl_context()) as r:
            assert 200 == r.status_code
            data2 = r.json()
            assert data2==expected_data

        # Run query, bad input
        dataq = dict(
            personId= "0001",
        )
        with requests.post(self.url+'v1/enrollments', json=dataq, params={'transactionId': 'T0001'},**get_ssl_context()) as r:
            assert 400 == r.status_code

        # Run query, bad input
        dataq = [dict(
            attributeName="personId",
            operator="=",
            value="Bob"
        )]
        with requests.post(self.url+'v1/enrollments', json=dataq, params={'transactionId': 'T0001'},**get_ssl_context()) as r:
            assert 400 == r.status_code

        # Run query, no candidates
        dataq = [dict(
            attributeName="firstName",
            operator="=",
            value="Bob"
        )]
        with requests.post(self.url+'v1/enrollments', json=dataq, params={'transactionId': 'T0001'},**get_ssl_context()) as r:
            assert 200 == r.status_code
            assert 'Server' not in r.headers
            res = r.json()
            assert len(res) == 0

        # Run query, 1 candidate
        dataq = [dict(
            attributeName="firstName",
            operator="=",
            value="John2"
            ),
            dict(
                attributeName="lastName",
                operator="=",
                value="Doe2"
        )]
        with requests.post(self.url+'v1/enrollments', json=dataq, params={'transactionId': 'T0001'},**get_ssl_context()) as r:
            assert 200 == r.status_code
            res = r.json()
            assert len(res) == 1
            assert res[0] == expected_data

        # finalize
        with requests.put(self.url+'v1/enrollments/0001/finalize', params={'transactionId': 'T0001'},**get_ssl_context()) as r:
            assert 204 == r.status_code

        # Delete enrollment
        with requests.delete(self.url+'v1/enrollments/0001', params={'transactionId': 'T0001'},**get_ssl_context()) as r:
            assert 204 == r.status_code

        # Make sure the buffers are also deleted
        with requests.get(self.url+'v1/enrollments/'+enrollment_id+'/buffer/'+buffer_id, params={'transactionId': 'T0001'}, **get_ssl_context()) as r:
            assert 404 == r.status_code

        # use metrics to check everything is deleted
        with requests.get(self.url+'monitoring/v1/metrics/gauges/nb_enrollments/count',**get_ssl_context()) as r:
            assert 200 == r.status_code
            assert 0 == r.json()
        with requests.get(self.url+'monitoring/v1/metrics/gauges/nb_biometricdata/count',**get_ssl_context()) as r:
            assert 200 == r.status_code
            assert 0 == r.json()
        with requests.get(self.url+'monitoring/v1/metrics/gauges/nb_buffers/count',**get_ssl_context()) as r:
            assert 200 == r.status_code
            assert 0 == r.json()

    def test_error(self):
        # missing mandatory lastName
        data = dict(
            enrollmentId= "0002",
            status= "IN_PROGRESS",
            enrollmentType= "FULL",
            enrollmentFlags=dict(timeout=3600),
            requestData= dict(),
            contextualData= dict(
                enrollmentDate= "2019-01-11"
            ),
            biographicData= dict(
                firstName= "John",
                dateOfBirth= "1985-11-30",
                gender= "M",
                nationality= "FRA"
            ),
            biometricData=[],
            documentData=[]
        )

        # Create enrollment
        with requests.post(self.url+'v1/enrollments/0002', json=data, params={'transactionId': 'T0002', 'finalize': 'false'},**get_ssl_context()) as r:
            assert 400 == r.status_code
            assert "'requestType' is a required property\n'lastName' is a required property" == r.json()['message']

# [---CUSTO---]

if __name__ == '__main__':
    unittest.main(argv=['-v'])
