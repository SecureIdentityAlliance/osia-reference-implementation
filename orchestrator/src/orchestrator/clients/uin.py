
import sys
import asyncio
import argparse
import logging

import aiohttp

logger = logging.getLogger('uin')

#______________________________________________________________________________
async def generate(url, transaction_id, data, target=None):
    async with aiohttp.ClientSession() as session:
        async with session.post(url,
                                json=data,
                                params={'transactionId': transaction_id}) as resp:
            if resp.status == 200:
                return await resp.json()
            if resp.status in [400, 404]:
                logger.error("UIN::generate error %d with url %s", resp.status, resp.real_url)
                return False
            try:
                error = await resp.json()
            except:
                error = {'message': ''}
            raise Exception("Could not generate UIN:\n" + error['message'])

#______________________________________________________________________________
def main(argv):
    parser = argparse.ArgumentParser(description="UIN client")

    parser.add_argument('--url', dest='url',
                        default="http://localhost:8080/v1/uin",
                        help="URL to reach the UIN server")
    parser.set_defaults(func=None)
    subparsers = parser.add_subparsers(title='Operations')

    parser2 = subparsers.add_parser('generate')
    parser2.add_argument('--transaction-id', required=True, dest='transaction_id')
    parser2.add_argument('--file', required=True, type=argparse.FileType('rb'), dest='data')
    parser2.set_defaults(func=generate)

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
