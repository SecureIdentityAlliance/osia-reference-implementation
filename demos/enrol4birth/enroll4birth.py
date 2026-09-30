import sys
import logging
import argparse
import datetime
import pathlib
import base64

import requests

args = None

def get_ssl_context():
    kw = {}
    kw['verify'] = False
    return kw

def do_birth(args):

    # Check ID of parent
    if args.parent_portrait_path:
        logging.info("Confirming parent's identity")
        with open(args.parent_portrait_path,'rb') as f:
            portrait = f.read()
            data = {"biometricData": [
                    {
                        "biometricType": "FACE",
                        "image": base64.b64encode(portrait).decode('ascii')
                    }
                ]}
        with requests.post(args.abis_url+'v1/verify/ALL/'+args.parent_uin, json=data, params={'transactionId': args.id},**get_ssl_context()) as r:
            assert 200 == r.status_code
            res = r.json()
            assert res['decision'] == True
            logging.info('CONFIRMED')
    else:
        logging.info("Cannot confirm parent's identity (no portrait provided)")

    # Get Parent data
    logging.info("Get parent data")
    with requests.get(args.pr_url+'v1/persons/'+args.parent_uin+'/reference', params={'transactionId': args.id},**get_ssl_context()) as r:
        assert 200 == r.status_code
        parent = r.json()
        logging.info('Parent name: %s %s' % (parent['biographicData']['firstName'], parent['biographicData']['lastName']))

    # Send data to enrollment server
    data = {
        "enrollmentType": "BABY",
        "requestData": {},
        "contextualData": {
            "enrollmentDate": "2026-09-29",
        },
        "biographicData": {
            "firstName": args.firstname,
            "lastName": args.lastname,
            "dateOfBirth": args.dob,
            "gender": args.gender,
            "parentUIN": args.parent_uin
        }
    }
    with requests.post(args.enr_url+'v1/enrollments/'+args.id, json=data, params={'finalize':'true', 'transactionId': args.id},**get_ssl_context()) as r:
        if r.status_code!=204:
            logging.error("[%d]: %s" , r.status_code,r.content)
        else:
            logging.info("Enrollment successfully submitted")


def main(argv=sys.argv[1:]):

    parser = argparse.ArgumentParser(description='CR mock')
    parser.add_argument("-l", "--loglevel", default='INFO', dest='loglevel', help="Log level")
    parser.add_argument("-f", "--logfile", default=None, dest='logfile', help="Log file")
    parser.add_argument("-i", "--ip", default='0.0.0.0', dest='ip', help="Listen IP")
    parser.add_argument("-p", "--port", default=8080, dest='port', type=int, help="Port number")

    parser.add_argument("--pr-url", dest='pr_url',
                        default='http://localhost:8010/',
                        help='The URL to the PR service')
    parser.add_argument("--abis-url", dest='abis_url',
                        default='http://localhost:8030/',
                        help='The URL to the ABIS service')
    parser.add_argument("--enrollment-url", dest='enr_url',
                        default='http://localhost:8000/',
                        help='The URL to the Enrollment Server')
    parser.add_argument("--id", default='001', dest='id', help="Enrollment/transaction ID")
    parser.add_argument("--fn", default='Baby', dest='firstname', help="First name of the baby")
    parser.add_argument("--ln", default='Smith', dest='lastname', help="Last name of the baby")
    parser.add_argument("--dob", default=datetime.date.today().isoformat(), dest='dob', help="Date of birth of the baby")
    parser.add_argument("--gender", default='M', dest='gender', help="Gender of the baby")
    parser.add_argument("--parent-uin", default='AH', dest='parent_uin', help="UIN of the parent of the baby")
    parser.add_argument("--parent-portrait", default=None, type=pathlib.Path, dest='parent_portrait_path', help="Path to the portrait image of the parent")

    args = parser.parse_args(argv)

    logging.basicConfig(format='%(asctime)-15s %(levelname)s - %(message)s',    # NOSONAR
                        level=logging.getLevelName(args.loglevel))
    if args.logfile:
        fh = logging.handlers.RotatingFileHandler(args.logfile, maxBytes=1000000, backupCount=20)
        fh.setLevel(logging.getLevelName(args.loglevel))
        formatter = logging.Formatter('%(asctime)-15s %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        logging.getLogger().addHandler(fh)


    do_birth(args)

if __name__ == '__main__':
    main()

