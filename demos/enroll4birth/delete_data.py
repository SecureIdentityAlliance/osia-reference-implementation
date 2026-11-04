import sys
import logging
import argparse

import requests

def get_ssl_context():
    kw = {}
    kw['verify'] = False
    return kw

def delete_data(args):
    event =     {
        "source": "script",
        "uin": args.uin,
        "transactionId": "cleanup"
    }

    params = {'subject':'deleteEnrollment'}
    with requests.post(args.notification_url+'v1/topics/enrollment/publish', json=event, params=params,**get_ssl_context()) as r:
        if r.status_code!=200:
            logging.error("[%d]: %s" , r.status_code,r.content)
        else:
            logging.info(f"{args.uin} successfully deleted")

def main(argv=sys.argv[1:]):

    parser = argparse.ArgumentParser(description='Script to insert test data')
    parser.add_argument("-l", "--loglevel", default='INFO', dest='loglevel', help="Log level")

    parser.add_argument("--notification-url", dest='notification_url',
                        default='http://localhost:8040/',
                        help='The URL to the notification server')
    parser.add_argument("--uin", dest='uin',
                        help='The UIN to remove')

    args = parser.parse_args(argv)

    logging.basicConfig(format='%(asctime)-15s %(levelname)s - %(message)s',    # NOSONAR
                        level=logging.INFO)

    return args

if __name__ == '__main__':
    args = main()
    delete_data(args)

