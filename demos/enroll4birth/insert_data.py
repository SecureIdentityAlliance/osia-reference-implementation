import sys
import logging
import argparse
import base64

import requests

def get_ssl_context():
    kw = {}
    kw['verify'] = False
    return kw

def prepare_data(args):
    # Create N persons

    #
    # AH
    #
    data = {
        "status": "ACTIVE",
        "physicalStatus": "ALIVE"
    }
    with requests.post(args.pr_url+'v1/persons/AH', json=data, params={'transactionId': 'prepare'},**get_ssl_context()) as r:
        assert r.status_code in [201, 409]

    # Create identity
    data = {
        "identityType": "PARENT",
        "status": "VALID",
        "galleries": ["DEMO"],
        "contextualData": {
            "enrollmentDate": "2026-09-29T12:00:00+02:00",
        },
        "biographicData": {
            "firstName": "Aiony",
            "lastName": "Haust",
            "dateOfBirth": "2005-11-30",
            "gender": "F",
        }
    }
    with requests.post(args.pr_url+'v1/persons/AH/identities/001', json=data, params={'transactionId': 'prepare'},**get_ssl_context()) as r:
        assert r.status_code in [201, 409]
    with requests.put(args.pr_url+'v1/persons/AH/identities/001/reference', params={'transactionId': 'prepare'},**get_ssl_context()) as r:
        assert 204 == r.status_code

    # Create encounter
    buf = open('data/aiony.jpg','rb').read()
    data = {
        "encounterType": "PARENT",
        "status": "ACTIVE",
        "galleries": ["DEMO"],
        "contextualData": {
            "enrollmentDate": "2026-09-29T12:00:00+02:00",
        },
        "biographicData": {
        },
        "biometricData": [
            {
                "biometricType": "FACE",
                "image": base64.b64encode(buf).decode('ascii'),
                "width": 300,
                "height": 389,
                "mimeType": "image/jpg"
            }
        ]
    }
    with requests.post(args.abis_url+'v1/persons/AH/encounters/001', json=data, params={'transactionId': 'prepare'},**get_ssl_context()) as r:
        assert r.status_code in [200, 201, 409]
    logging.info("AH created")

    #
    # AD
    #
    data = {
        "status": "ACTIVE",
        "physicalStatus": "ALIVE"
    }
    with requests.post(args.pr_url+'v1/persons/AD', json=data, params={'transactionId': 'prepare'},**get_ssl_context()) as r:
        assert r.status_code in [201, 409]

    # Create identity
    data = {
        "identityType": "PARENT",
        "status": "VALID",
        "galleries": ["DEMO"],
        "contextualData": {
            "enrollmentDate": "2026-09-29T12:00:00+02:00",
        },
        "biographicData": {
            "firstName": "Albert",
            "lastName": "Dera",
            "dateOfBirth": "2002-09-12",
            "gender": "M",
        }
    }
    with requests.post(args.pr_url+'v1/persons/AD/identities/001', json=data, params={'transactionId': 'prepare'},**get_ssl_context()) as r:
        assert r.status_code in [201, 409]
    with requests.put(args.pr_url+'v1/persons/AD/identities/001/reference', params={'transactionId': 'prepare'},**get_ssl_context()) as r:
        assert 204 == r.status_code

    # Create encounter
    buf = open('data/albert.jpg','rb').read()
    data = {
        "encounterType": "PARENT",
        "status": "ACTIVE",
        "galleries": ["DEMO"],
        "contextualData": {
            "enrollmentDate": "2026-09-29T12:00:00+02:00",
        },
        "biographicData": {
        },
        "biometricData": [
            {
                "biometricType": "FACE",
                "image": base64.b64encode(buf).decode('ascii'),
                "width": 294,
                "height": 400,
                "mimeType": "image/jpg"
            }
        ]
    }
    with requests.post(args.abis_url+'v1/persons/AD/encounters/001', json=data, params={'transactionId': 'prepare'},**get_ssl_context()) as r:
        assert r.status_code in [200, 201, 409]
    logging.info("AD created")

    #
    # AG
    #
    data = {
        "status": "ACTIVE",
        "physicalStatus": "ALIVE"
    }
    with requests.post(args.pr_url+'v1/persons/AG', json=data, params={'transactionId': 'prepare'},**get_ssl_context()) as r:
        assert r.status_code in [201, 409]

    # Create identity
    data = {
        "identityType": "PARENT",
        "status": "VALID",
        "galleries": ["DEMO"],
        "contextualData": {
            "enrollmentDate": "2026-09-29T12:00:00+02:00",
        },
        "biographicData": {
            "firstName": "Alyona",
            "lastName": "Grishina",
            "dateOfBirth": "2005-11-30",
            "gender": "M",
        }
    }
    with requests.post(args.pr_url+'v1/persons/AG/identities/001', json=data, params={'transactionId': 'prepare'},**get_ssl_context()) as r:
        assert r.status_code in [201, 409]
    with requests.put(args.pr_url+'v1/persons/AG/identities/001/reference', params={'transactionId': 'prepare'},**get_ssl_context()) as r:
        assert 204 == r.status_code

    # Create encounter
    buf = open('data/alyona.jpg','rb').read()
    data = {
        "encounterType": "PARENT",
        "status": "ACTIVE",
        "galleries": ["DEMO"],
        "contextualData": {
            "enrollmentDate": "2026-09-29T12:00:00+02:00",
        },
        "biographicData": {
        },
        "biometricData": [
            {
                "biometricType": "FACE",
                "image": base64.b64encode(buf).decode('ascii'),
                "width": 300,
                "height": 389,
                "mimeType": "image/jpg"
            }
        ]
    }
    with requests.post(args.abis_url+'v1/persons/AG/encounters/001', json=data, params={'transactionId': 'prepare'},**get_ssl_context()) as r:
        assert r.status_code in [200, 201, 409]
    logging.info("AG created")

    #
    # JF
    #
    data = {
        "status": "ACTIVE",
        "physicalStatus": "ALIVE"
    }
    with requests.post(args.pr_url+'v1/persons/JF', json=data, params={'transactionId': 'prepare'},**get_ssl_context()) as r:
        assert r.status_code in [201, 409]

    # Create identity
    data = {
        "identityType": "PARENT",
        "status": "VALID",
        "galleries": ["DEMO"],
        "contextualData": {
            "enrollmentDate": "2026-09-30T12:00:00+02:00",
        },
        "biographicData": {
            "firstName": "Jimmy",
            "lastName": "Fermin",
            "dateOfBirth": "1999-05-10",
            "gender": "F",
        }
    }
    with requests.post(args.pr_url+'v1/persons/JF/identities/001', json=data, params={'transactionId': 'prepare'},**get_ssl_context()) as r:
        assert r.status_code in [201, 409]
    with requests.put(args.pr_url+'v1/persons/JF/identities/001/reference', params={'transactionId': 'prepare'},**get_ssl_context()) as r:
        assert 204 == r.status_code

    # Create encounter
    buf = open('data/jimmy.jpg','rb').read()
    data = {
        "encounterType": "PARENT",
        "status": "ACTIVE",
        "galleries": ["DEMO"],
        "contextualData": {
            "enrollmentDate": "2026-09-29T12:00:00+02:00",
        },
        "biographicData": {
        },
        "biometricData": [
            {
                "biometricType": "FACE",
                "image": base64.b64encode(buf).decode('ascii'),
                "width": 300,
                "height": 389,
                "mimeType": "image/jpg"
            }
        ]
    }
    with requests.post(args.abis_url+'v1/persons/JF/encounters/001', json=data, params={'transactionId': 'prepare'},**get_ssl_context()) as r:
        assert r.status_code in [200, 201, 409]
    logging.info("JF created")

    #
    # JK
    #
    data = {
        "status": "ACTIVE",
        "physicalStatus": "ALIVE"
    }
    with requests.post(args.pr_url+'v1/persons/JK', json=data, params={'transactionId': 'prepare'},**get_ssl_context()) as r:
        assert r.status_code in [201, 409]

    # Create identity
    data = {
        "identityType": "PARENT",
        "status": "VALID",
        "galleries": ["DEMO"],
        "contextualData": {
            "enrollmentDate": "2026-09-30T12:00:00+02:00",
        },
        "biographicData": {
            "firstName": "Jurica",
            "lastName": "Koletic",
            "dateOfBirth": "2001-05-10",
            "gender": "M",
        }
    }
    with requests.post(args.pr_url+'v1/persons/JK/identities/001', json=data, params={'transactionId': 'prepare'},**get_ssl_context()) as r:
        assert r.status_code in [201, 409]
    with requests.put(args.pr_url+'v1/persons/JK/identities/001/reference', params={'transactionId': 'prepare'},**get_ssl_context()) as r:
        assert 204 == r.status_code

    # Create encounter
    buf = open('data/jurica.jpg','rb').read()
    data = {
        "encounterType": "PARENT",
        "status": "ACTIVE",
        "galleries": ["DEMO"],
        "contextualData": {
            "enrollmentDate": "2026-09-29T12:00:00+02:00",
        },
        "biographicData": {
        },
        "biometricData": [
            {
                "biometricType": "FACE",
                "image": base64.b64encode(buf).decode('ascii'),
                "width": 300,
                "height": 389,
                "mimeType": "image/jpg"
            }
        ]
    }
    with requests.post(args.abis_url+'v1/persons/JK/encounters/001', json=data, params={'transactionId': 'prepare'},**get_ssl_context()) as r:
        assert r.status_code in [200, 201, 409]
    logging.info("JK created")

    #
    # MR
    #
    data = {
        "status": "ACTIVE",
        "physicalStatus": "ALIVE"
    }
    with requests.post(args.pr_url+'v1/persons/MR', json=data, params={'transactionId': 'prepare'},**get_ssl_context()) as r:
        assert r.status_code in [201, 409]

    # Create identity
    data = {
        "identityType": "PARENT",
        "status": "VALID",
        "galleries": ["DEMO"],
        "contextualData": {
            "enrollmentDate": "2026-09-30T12:00:00+02:00",
        },
        "biographicData": {
            "firstName": "Matt",
            "lastName": "Reiter",
            "dateOfBirth": "2002-03-01",
            "gender": "F",
        }
    }
    with requests.post(args.pr_url+'v1/persons/MR/identities/001', json=data, params={'transactionId': 'prepare'},**get_ssl_context()) as r:
        assert r.status_code in [201, 409]
    with requests.put(args.pr_url+'v1/persons/MR/identities/001/reference', params={'transactionId': 'prepare'},**get_ssl_context()) as r:
        assert 204 == r.status_code

    # Create encounter
    buf = open('data/matt.jpg','rb').read()
    data = {
        "encounterType": "PARENT",
        "status": "ACTIVE",
        "galleries": ["DEMO"],
        "contextualData": {
            "enrollmentDate": "2026-09-29T12:00:00+02:00",
        },
        "biographicData": {
        },
        "biometricData": [
            {
                "biometricType": "FACE",
                "image": base64.b64encode(buf).decode('ascii'),
                "width": 300,
                "height": 389,
                "mimeType": "image/jpg"
            }
        ]
    }
    with requests.post(args.abis_url+'v1/persons/MR/encounters/001', json=data, params={'transactionId': 'prepare'},**get_ssl_context()) as r:
        assert r.status_code in [200, 201, 409]
    logging.info("MR created")

    #
    # RM
    #
    data = {
        "status": "ACTIVE",
        "physicalStatus": "ALIVE"
    }
    with requests.post(args.pr_url+'v1/persons/RM', json=data, params={'transactionId': 'prepare'},**get_ssl_context()) as r:
        assert r.status_code in [201, 409]

    # Create identity
    data = {
        "identityType": "PARENT",
        "status": "VALID",
        "galleries": ["DEMO"],
        "contextualData": {
            "enrollmentDate": "2026-09-30T12:00:00+02:00",
        },
        "biographicData": {
            "firstName": "Rachel",
            "lastName": "MacDermott",
            "dateOfBirth": "1998-03-01",
            "gender": "F",
        }
    }
    with requests.post(args.pr_url+'v1/persons/RM/identities/001', json=data, params={'transactionId': 'prepare'},**get_ssl_context()) as r:
        assert r.status_code in [201, 409]
    with requests.put(args.pr_url+'v1/persons/RM/identities/001/reference', params={'transactionId': 'prepare'},**get_ssl_context()) as r:
        assert 204 == r.status_code

    # Create encounter
    buf = open('data/rachel.jpg','rb').read()
    data = {
        "encounterType": "PARENT",
        "status": "ACTIVE",
        "galleries": ["DEMO"],
        "contextualData": {
            "enrollmentDate": "2026-09-29T12:00:00+02:00",
        },
        "biographicData": {
        },
        "biometricData": [
            {
                "biometricType": "FACE",
                "image": base64.b64encode(buf).decode('ascii'),
                "width": 300,
                "height": 389,
                "mimeType": "image/jpg"
            }
        ]
    }
    with requests.post(args.abis_url+'v1/persons/RM/encounters/001', json=data, params={'transactionId': 'prepare'},**get_ssl_context()) as r:
        assert r.status_code in [200, 201, 409]
    logging.info("RM created")

    # Create Topic
    with requests.post(args.notification_url+"v1/topics",params={'name':'enrollment'}) as r:
        assert r.status_code == 200
    logging.info("Topic [enrollment] created")
    with requests.post(args.notification_url+"v1/topics",params={'name':'CR'}) as r:
        assert r.status_code == 200
    logging.info("Topic [CR] created")


def main(argv=sys.argv[1:]):

    parser = argparse.ArgumentParser(description='Script to insert test data in PR and ABIS')
    parser.add_argument("-l", "--loglevel", default='INFO', dest='loglevel', help="Log level")

    parser.add_argument("--pr-url", dest='pr_url',
                        default='http://localhost:8010/',
                        help='The URL to the PR service')
    parser.add_argument("--abis-url", dest='abis_url',
                        default='http://localhost:8030/',
                        help='The URL to the PR service')
    parser.add_argument("--notification-url", dest='notification_url',
                        default='http://localhost:8040/',
                        help='The URL to the notification service')

    args = parser.parse_args(argv)

    logging.basicConfig(format='%(asctime)-15s %(levelname)s - %(message)s',    # NOSONAR
                        level=logging.INFO)

    return args

if __name__ == '__main__':
    args = main()
    prepare_data(args)

