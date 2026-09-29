import sys
import logging
import argparse

import requests

def get_ssl_context():
    kw = {}
    kw['verify'] = False
    return kw

def prepare_data(args):
    # Create 2 persons
    data = {
        "status": "ACTIVE",
        "physicalStatus": "ALIVE"
    }
    with requests.post(args.pr_url+'v1/persons/A', json=data, params={'transactionId': 'prepare'},**get_ssl_context()) as r:
        assert r.status_code in [201, 409]

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
    with requests.post(args.pr_url+'v1/persons/A/identities/001', json=data, params={'transactionId': 'prepare'},**get_ssl_context()) as r:
        assert r.status_code in [201, 409]
    with requests.put(args.pr_url+'v1/persons/A/identities/001/reference', params={'transactionId': 'prepare'},**get_ssl_context()) as r:
        assert 204 == r.status_code
    logging.info("Father created (Albert Smith)")

    data = {
        "status": "ACTIVE",
        "physicalStatus": "ALIVE"
    }
    with requests.post(args.pr_url+'v1/persons/B', json=data, params={'transactionId': 'prepare'},**get_ssl_context()) as r:
        assert r.status_code in [201, 409]

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
    with requests.post(args.pr_url+'v1/persons/B/identities/001', json=data, params={'transactionId': 'prepare'},**get_ssl_context()) as r:
        assert r.status_code in [201, 409]
    with requests.put(args.pr_url+'v1/persons/B/identities/001/reference', params={'transactionId': 'prepare'},**get_ssl_context()) as r:
        assert 204 == r.status_code
    logging.info("Mother created (Alice Smith)")

    # Create Topic
    with requests.post(args.notification_url+"v1/topics",params={'name':'CR'}) as r:
        assert r.status_code == 200
    logging.info("Topic [CR] created")


def main(argv=sys.argv[1:]):

    parser = argparse.ArgumentParser(description='CR mock')
    parser.add_argument("-l", "--loglevel", default='INFO', dest='loglevel', help="Log level")
    parser.add_argument("-f", "--logfile", default=None, dest='logfile', help="Log file")

    parser.add_argument("--pr-url", dest='pr_url',
                        default='http://localhost:8010/',
                        help='The URL to the PR service')
    parser.add_argument("--uin-url", dest='uin_url',
                        default='http://localhost:8020/',
                        help='The URL to the UIN generator service')
    parser.add_argument("--notification-url", dest='notification_url',
                        default='http://localhost:8030/',
                        help='The URL to the notification service')

    args = parser.parse_args(argv)

    logging.basicConfig(format='%(asctime)-15s %(levelname)s - %(message)s',    # NOSONAR
                        level=logging.getLevelName(args.loglevel))
    if args.logfile:
        fh = logging.handlers.RotatingFileHandler(args.logfile, maxBytes=1000000, backupCount=20)
        fh.setLevel(logging.getLevelName(args.loglevel))
        formatter = logging.Formatter('%(asctime)-15s %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        logging.getLogger().addHandler(fh)

    return args

if __name__ == '__main__':
    args = main()
    prepare_data(args)

