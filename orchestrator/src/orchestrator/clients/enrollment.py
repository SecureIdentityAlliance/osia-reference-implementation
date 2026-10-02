
import sys
import asyncio
import argparse
import logging

import aiohttp

logger = logging.getLogger('abis')

#______________________________________________________________________________
async def readEnrollment(url, transaction_id, enrollment_id, target=None):
    async with aiohttp.ClientSession() as session:
        async with session.get(url+'/'+enrollment_id,
                                headers={'content-type': 'application/json'},
                                params={'transactionId': transaction_id}) as resp:
            if resp.status == 200:
                res = await resp.json()
                return res
            if resp.status in [400, 404]:
                logger.error("Enrollment::readEnrollment error %d with url %s", resp.status, resp.real_url)
                return False
            try:
                error = await resp.json()
            except:
                error = {'message': ''}
            raise Exception("Could not read enrollment:\n" + error['message'])

#______________________________________________________________________________
async def deleteEnrollment(url, transaction_id, enrollment_id, target=None):
    async with aiohttp.ClientSession() as session:
        async with session.delete(url+'/'+enrollment_id,
                                params={'transactionId': transaction_id}) as resp:
            if resp.status == 204:
                return True
            if resp.status in [400, 404]:
                logger.error("Enrollment::deleteEnrollment error %d with url %s", resp.status, resp.real_url)
                return False
            try:
                error = await resp.json()
            except:
                error = {'message': ''}
            raise Exception("Could not delete enrollment:\n" + error['message'])

#______________________________________________________________________________
def main(argv):
    parser = argparse.ArgumentParser(description="Enrollment client")

    parser.add_argument('--url', dest='url',
                        default="http://localhost:8080/v1/enrollments",
                        help="URL to reach the Enrollment server")
    parser.set_defaults(func=None)
    subparsers = parser.add_subparsers(title='Operations')

    parser2 = subparsers.add_parser('readEnrollment')
    parser2.add_argument('--transaction-id', required=True, dest='transaction_id')
    parser2.add_argument('--enrollment-id', required=True, dest='enrollment_id')
    parser2.set_defaults(func=readEnrollment)

    args = parser.parse_args(argv)
    logging.basicConfig(format='%(asctime)-15s - %(message)s',
                        level=logging.INFO)

    if args.func:
        v = {}
        v.update(vars(args))
        del v['func']
        asyncio.run(args.func(**v))

if __name__=='__main__':
    main(sys.argv[1:])
