
import sys
import asyncio
import argparse
import logging

import aiohttp

logger = logging.getLogger('cr')


#______________________________________________________________________________
async def readPersonAttributes(url, transaction_id, person_id):
    params = {
            'transactionId': transaction_id,
            "attributeNames": ["firstName", "lastName", "dateOfBirth", "gender", "nationality"]
        }
    async with aiohttp.ClientSession() as session:
        async with session.get(url+'/'+person_id,
                                headers={'content-type': 'application/json'},
                                params=params) as resp:
            if resp.status in [200]:
                ret = await resp.json()
                return ret
            if resp.status in [400, 404]:
                ret = await resp.json()
                logger.error("CR::readPersonAttributes error %d with url %s", resp.status, resp.real_url)
                return
            try:
                error = await resp.json()
            except:
                error = {'message': ''}
            raise Exception("Could not read person attributes:\n" + error['message'])


#______________________________________________________________________________
def main(argv):
    parser = argparse.ArgumentParser(description="CR client")

    parser.add_argument('--url', dest='url',
                        default="http://localhost:8080/v1/persons",
                        help="URL to reach the CR server")
    parser.set_defaults(func=None)
    subparsers = parser.add_subparsers(title='Operations')

    parser2 = subparsers.add_parser('readPersonAttributes')
    parser2.add_argument('--transaction-id', required=True, dest='transaction_id')
    parser2.add_argument('--person-id', required=True, dest='person_id')
    parser2.set_defaults(func=readPersonAttributes)

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
