
import sys
import asyncio
import argparse
import logging

import aiohttp

logger = logging.getLogger('abis')

#______________________________________________________________________________
async def createEncounter(url, transaction_id, person_id, encounter_id, encounter, target=None):
    async with aiohttp.ClientSession() as session:
        async with session.post(url+'/'+person_id+'/encounters/'+encounter_id,
                                data=encounter,
                                headers={'content-type': 'application/json'},
                                params={'transactionId': transaction_id}) as resp:
            if resp.status == 200:
                await resp.json()
                return
            if resp.status in [400, 404]:
                logger.error("ABIS::createEncounter error %d with url %s", resp.status, resp.real_url)
                return False
            try:
                error = await resp.json()
            except:
                error = {'message': ''}
            raise Exception("Could not create encounter:\n" + error['message'])

#______________________________________________________________________________
def main(argv):
    parser = argparse.ArgumentParser(description="ABIS client")

    parser.add_argument('--url', dest='url',
                        default="http://localhost:8080/v1/persons",
                        help="URL to reach the ABIS server")
    parser.set_defaults(func=None)
    subparsers = parser.add_subparsers(title='Operations')

    parser2 = subparsers.add_parser('createEncounter')
    parser2.add_argument('--transaction-id', required=True, dest='transaction_id')
    parser2.add_argument('--person-id', required=True, dest='person_id')
    parser2.add_argument('--encounter-id', required=True, dest='encounter_id')
    parser2.add_argument('--file', required=True, type=argparse.FileType('rb'), dest='encounter')
    parser2.set_defaults(func=createEncounter)

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
