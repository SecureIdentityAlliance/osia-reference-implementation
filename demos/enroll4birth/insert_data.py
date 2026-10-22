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
    buf = open('data/aiony.jpg','rb').read()
    data = {
        "enrollmentType": "PARENT",
        "requestData": {
            "UIN": "AH"
        },
        "contextualData":
        {
            "enrollmentDate": "2026-09-29T12:00:00+02:00",
        },
        "biographicData": {
            "firstName": "Aiony",
            "lastName": "Haust",
            "dateOfBirth": "2005-11-30",
            "gender": "F",
            "parentUIN": ""
        },
        "biometricData": [
            {
                "biometricType": "FACE",
                "biometricSubType": "PORTRAIT",
                "image": base64.b64encode(buf).decode('ascii'),
                "width": 300,
                "height": 389,
                "mimeType": "image/jpg"
            }
        ]
    }

    with requests.post(args.enr_url+'v1/enrollments/AH', json=data, params={'finalize':'true', 'transactionId': 'prepare'},**get_ssl_context()) as r:
        if r.status_code!=204:
            logging.error("[%d]: %s" , r.status_code,r.content)
        else:
            logging.info("AH successfully enrolled")


    #
    # AD
    #
    buf = open('data/albert.jpg','rb').read()
    data = {
        "enrollmentType": "PARENT",
        "requestData": {
            "UIN": "AD"
        },
        "contextualData":
        {
            "enrollmentDate": "2026-09-29T12:00:00+02:00",
        },
        "biographicData": {
            "firstName": "Albert",
            "lastName": "Dera",
            "dateOfBirth": "2002-09-12",
            "gender": "M",
            "parentUIN": ""
        },
        "biometricData": [
            {
                "biometricType": "FACE",
                "biometricSubType": "PORTRAIT",
                "image": base64.b64encode(buf).decode('ascii'),
                "width": 294,
                "height": 400,
                "mimeType": "image/jpg"
            }
        ]
    }

    with requests.post(args.enr_url+'v1/enrollments/AD', json=data, params={'finalize':'true', 'transactionId': 'prepare'},**get_ssl_context()) as r:
        if r.status_code!=204:
            logging.error("[%d]: %s" , r.status_code,r.content)
        else:
            logging.info("AD successfully enrolled")

    #
    # AG
    #
    buf = open('data/alyona.jpg','rb').read()
    data = {
        "enrollmentType": "PARENT",
        "requestData": {
            "UIN": "AG"
        },
        "contextualData":
        {
            "enrollmentDate": "2026-09-29T12:00:00+02:00",
        },
        "biographicData": {
            "firstName": "Alyona",
            "lastName": "Grishina",
            "dateOfBirth": "2005-11-30",
            "gender": "M",
            "parentUIN": ""
        },
        "biometricData": [
            {
                "biometricType": "FACE",
                "biometricSubType": "PORTRAIT",
                "image": base64.b64encode(buf).decode('ascii'),
                "width": 300,
                "height": 389,
                "mimeType": "image/jpg"
            }
        ]
    }

    with requests.post(args.enr_url+'v1/enrollments/AG', json=data, params={'finalize':'true', 'transactionId': 'prepare'},**get_ssl_context()) as r:
        if r.status_code!=204:
            logging.error("[%d]: %s" , r.status_code,r.content)
        else:
            logging.info("AG successfully enrolled")

    #
    # JF
    #
    buf = open('data/jimmy.jpg','rb').read()
    data = {
        "enrollmentType": "PARENT",
        "requestData": {
            "UIN": "JF"
        },
        "contextualData":
        {
            "enrollmentDate": "2026-09-29T12:00:00+02:00",
        },
        "biographicData": {
            "firstName": "Jimmy",
            "lastName": "Fermin",
            "dateOfBirth": "1999-05-10",
            "gender": "F",
            "parentUIN": ""
        },
        "biometricData": [
            {
                "biometricType": "FACE",
                "biometricSubType": "PORTRAIT",
                "image": base64.b64encode(buf).decode('ascii'),
                "width": 300,
                "height": 389,
                "mimeType": "image/jpg"
            }
        ]
    }

    with requests.post(args.enr_url+'v1/enrollments/JF', json=data, params={'finalize':'true', 'transactionId': 'prepare'},**get_ssl_context()) as r:
        if r.status_code!=204:
            logging.error("[%d]: %s" , r.status_code,r.content)
        else:
            logging.info("JF successfully enrolled")

    #
    # JK
    #
    buf = open('data/jurica.jpg','rb').read()
    data = {
        "enrollmentType": "PARENT",
        "requestData": {
            "UIN": "JK"
        },
        "contextualData":
        {
            "enrollmentDate": "2026-09-29T12:00:00+02:00",
        },
        "biographicData": {
            "firstName": "Jurica",
            "lastName": "Koletic",
            "dateOfBirth": "2001-05-10",
            "gender": "M",
            "parentUIN": ""
        },
        "biometricData": [
            {
                "biometricType": "FACE",
                "biometricSubType": "PORTRAIT",
                "image": base64.b64encode(buf).decode('ascii'),
                "width": 300,
                "height": 389,
                "mimeType": "image/jpg"
            }
        ]
    }

    with requests.post(args.enr_url+'v1/enrollments/JK', json=data, params={'finalize':'true', 'transactionId': 'prepare'},**get_ssl_context()) as r:
        if r.status_code!=204:
            logging.error("[%d]: %s" , r.status_code,r.content)
        else:
            logging.info("JK successfully enrolled")

    #
    # MR
    #
    buf = open('data/matt.jpg','rb').read()
    data = {
        "enrollmentType": "PARENT",
        "requestData": {
            "UIN": "MR"
        },
        "contextualData":
        {
            "enrollmentDate": "2026-09-29T12:00:00+02:00",
        },
        "biographicData": {
            "firstName": "Matt",
            "lastName": "Reiter",
            "dateOfBirth": "2002-03-01",
            "gender": "F",
            "parentUIN": ""
        },
        "biometricData": [
            {
                "biometricType": "FACE",
                "biometricSubType": "PORTRAIT",
                "image": base64.b64encode(buf).decode('ascii'),
                "width": 300,
                "height": 389,
                "mimeType": "image/jpg"
            }
        ]
    }

    with requests.post(args.enr_url+'v1/enrollments/MR', json=data, params={'finalize':'true', 'transactionId': 'prepare'},**get_ssl_context()) as r:
        if r.status_code!=204:
            logging.error("[%d]: %s" , r.status_code,r.content)
        else:
            logging.info("MR successfully enrolled")

    #
    # RM
    #
    buf = open('data/rachel.jpg','rb').read()
    data = {
        "enrollmentType": "PARENT",
        "requestData": {
            # "UIN": "RM"
        },
        "contextualData":
        {
            "enrollmentDate": "2026-09-29T12:00:00+02:00",
        },
        "biographicData": {
            "firstName": "Rachel",
            "lastName": "MacDermott",
            "dateOfBirth": "1998-03-01",
            "gender": "F",
            "parentUIN": ""
        },
        "biometricData": [
            {
                "biometricType": "FACE",
                "biometricSubType": "PORTRAIT",
                "image": base64.b64encode(buf).decode('ascii'),
                "width": 300,
                "height": 389,
                "mimeType": "image/jpg"
            }
        ]
    }

    with requests.post(args.enr_url+'v1/enrollments/RM', json=data, params={'finalize':'true', 'transactionId': 'prepare'},**get_ssl_context()) as r:
        if r.status_code!=204:
            logging.error("[%d]: %s" , r.status_code,r.content)
        else:
            logging.info("RM successfully enrolled")


    # # Create Topic
    # with requests.post(args.notification_url+"v1/topics",params={'name':'enrollment'}) as r:
    #     assert r.status_code == 200
    # logging.info("Topic [enrollment] created")
    # with requests.post(args.notification_url+"v1/topics",params={'name':'CR'}) as r:
    #     assert r.status_code == 200
    # logging.info("Topic [CR] created")


def main(argv=sys.argv[1:]):

    parser = argparse.ArgumentParser(description='Script to insert test data')
    parser.add_argument("-l", "--loglevel", default='INFO', dest='loglevel', help="Log level")

    parser.add_argument("--enr-url", dest='enr_url',
                        default='http://localhost:8000/',
                        help='The URL to the enrollment server')

    args = parser.parse_args(argv)

    logging.basicConfig(format='%(asctime)-15s %(levelname)s - %(message)s',    # NOSONAR
                        level=logging.INFO)

    return args

if __name__ == '__main__':
    args = main()
    prepare_data(args)

