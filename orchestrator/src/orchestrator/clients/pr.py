
# Client of the PR API
# Run with::
#   python -m orchestrator.clients.pr --url http://localhost:8080/v1/persons <operation> arguments
# Examples::
#   python -m orchestrator.clients.pr --url http://localhost:8002/v1/persons createPerson --person-id SAMPLE --file tests/PR/person.json --transaction-id 111
#   python -m orchestrator.clients.pr --url http://localhost:8002/v1/persons updatePerson --person-id SAMPLE --file tests/PR/person.json --transaction-id 111
#   python -m orchestrator.clients.pr --url http://localhost:8002/v1/persons createIdentity --person-id SAMPLE --file tests/PR/identity.json --transaction-id 111
#   python -m orchestrator.clients.pr --url http://localhost:8002/v1/persons createIdentityWithId --person-id SAMPLE --identity-id ID001 --file tests/PR/identity.json --transaction-id 111
#   python -m orchestrator.clients.pr --url http://localhost:8002/v1/persons deletePerson --person-id SAMPLE --transaction-id 111

import sys
import asyncio
import argparse
import logging

import aiohttp

logger = logging.getLogger('pr')


#______________________________________________________________________________
async def createPerson(url, transaction_id, person_id, person, target=None):
    async with aiohttp.ClientSession() as session:
        async with session.post(url+'/'+person_id,
                                data=person,
                                headers={'content-type': 'application/json'},
                                params={'transactionId': transaction_id}) as resp:
            if resp.status in [201, 409]:
                return True
            if resp.status in [400, 404]:
                logger.error("PR::createPerson error %d with url %s", resp.status, resp.real_url)
                return False
            try:
                error = await resp.json()
            except:
                error = {'message': ''}
            raise Exception("Could not create person:\n" + error['message'])

#______________________________________________________________________________
async def updatePerson(url, transaction_id, person_id, person, target=None):
    async with aiohttp.ClientSession() as session:
        async with session.put(url+'/'+person_id,
                                data=person,
                                headers={'content-type': 'application/json'},
                                params={'transactionId': transaction_id}) as resp:
            if resp.status == 204:
                return True
            if resp.status in [400, 404]:
                logger.error("PR::updatePerson error %d with url %s", resp.status, resp.real_url)
                return False
            try:
                error = await resp.json()
            except:
                error = {'message': ''}
            raise Exception("Could not update person:\n" + error['message'])

#______________________________________________________________________________
async def deletePerson(url, transaction_id, person_id, target=None):
    async with aiohttp.ClientSession() as session:
        async with session.delete(url+'/'+person_id,
                                params={'transactionId': transaction_id}) as resp:
            if resp.status == 204:
                logger.info("delete successful: %s", person_id)
                return
            raise Exception("Could not delete person")

#______________________________________________________________________________
async def createIdentity(url, transaction_id, person_id, identity, target=None):
    async with aiohttp.ClientSession() as session:
        async with session.post(url+'/'+person_id+'/identities',
                                data=identity,
                                headers={'content-type': 'application/json'},
                                params={'transactionId': transaction_id}) as resp:
            if resp.status == 200:
                identity_id = await resp.json()
                logger.info("identityId received: %s", identity_id)
                return identity_id
            if resp.status in [400, 404]:
                logger.error("PR::createIdentity error %d with url %s", resp.status, resp.real_url)
                return False
            try:
                error = await resp.json()
            except:
                error = {'message': ''}
            raise Exception("Could not create identity:\n" + error['message'])

#______________________________________________________________________________
async def createIdentityWithId(url, transaction_id, person_id, identity_id, identity, target=None):
    async with aiohttp.ClientSession() as session:
        async with session.post(url+'/'+person_id+'/identities/'+identity_id,
                                data=identity,
                                headers={'content-type': 'application/json'},
                                params={'transactionId': transaction_id}) as resp:
            if resp.status in [201, 409]:
                return True
            if resp.status in [400, 404]:
                logger.error("PR::createIdentityWithId error %d with url %s", resp.status, resp.real_url)
                return False
            try:
                error = await resp.json()
            except:
                error = {'message': ''}
            raise Exception("Could not create identity:\n" + error['message'])


#______________________________________________________________________________
def main(argv):
    parser = argparse.ArgumentParser(description="Person client")

    parser.add_argument('--url', dest='url',
                        default="http://localhost:8080/v1/persons",
                        help="URL to reach the person server")
    parser.set_defaults(func=None)
    subparsers = parser.add_subparsers(title='Operations')

    parser2 = subparsers.add_parser('createPerson')
    parser2.add_argument('--transaction-id', required=True, dest='transaction_id')
    parser2.add_argument('--person-id', required=True, dest='person_id')
    parser2.add_argument('--file', required=True, type=argparse.FileType('rb'), dest='person')
    parser2.set_defaults(func=createPerson)

    parser2 = subparsers.add_parser('updatePerson')
    parser2.add_argument('--transaction-id', required=True, dest='transaction_id')
    parser2.add_argument('--person-id', required=True, dest='person_id')
    parser2.add_argument('--file', required=True, type=argparse.FileType('rb'), dest='person')
    parser2.set_defaults(func=updatePerson)

    parser2 = subparsers.add_parser('deletePerson')
    parser2.add_argument('--transaction-id', required=True, dest='transaction_id')
    parser2.add_argument('--person-id', required=True, dest='person_id')
    parser2.set_defaults(func=deletePerson)

    parser2 = subparsers.add_parser('createIdentity')
    parser2.add_argument('--transaction-id', required=True, dest='transaction_id')
    parser2.add_argument('--person-id', required=True, dest='person_id')
    parser2.add_argument('--file', required=True, type=argparse.FileType('rb'), dest='identity')
    parser2.set_defaults(func=createIdentity)

    parser2 = subparsers.add_parser('createIdentityWithId')
    parser2.add_argument('--transaction-id', required=True, dest='transaction_id')
    parser2.add_argument('--person-id', required=True, dest='person_id')
    parser2.add_argument('--identity-id', required=True, dest='identity_id')
    parser2.add_argument('--file', required=True, type=argparse.FileType('rb'), dest='identity')
    parser2.set_defaults(func=createIdentityWithId)

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
