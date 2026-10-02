
import sys
import asyncio
import argparse
import logging

import aiohttp

logger = logging.getLogger('cms')

#______________________________________________________________________________
async def createCredentialRequest(url, transaction_id, enrollment_id, request, target=None):
    async with aiohttp.ClientSession() as session:
        async with session.post(url+'/v1/credentialRequests/'+enrollment_id,
                                data=request,
                                headers={'content-type': 'application/json'},
                                params={'transactionId': transaction_id}) as resp:
            if resp.status == 201:
                return True
            if resp.status in [400, 404]:
                logger.error("CMS::createCredentialRequest error %d with url %s", resp.status, resp.real_url)
                return False
            try:
                error = await resp.json()
            except:
                error = {'message': ''}
            raise Exception("Could not create CredentialRequest:\n" + error['message'])

#______________________________________________________________________________
def main(argv):
    parser = argparse.ArgumentParser(description="CMS client")

    parser.add_argument('--url', dest='url',
                        default="http://localhost:8080",
                        help="URL to reach the CMS server")
    parser.set_defaults(func=None)
    subparsers = parser.add_subparsers(title='Operations')

    parser2 = subparsers.add_parser('createCredentialRequest')
    parser2.add_argument('--transaction-id', required=True, dest='transaction_id')
    parser2.add_argument('--enrollment-id', required=True, dest='enrollment_id')
    parser2.add_argument('--encounter-id', required=True, dest='encounter_id')
    parser2.set_defaults(func=createCredentialRequest)

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
