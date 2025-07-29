import ssl
import logging
import json
import copy
import uuid
import base64
import io
import asyncio

import aiohttp
from aiohttp import web

import yaml
import jsonschema
import referencing
import referencing.jsonschema

import pr
import pr.model

from sqlalchemy.orm import Session, make_transient
from sqlalchemy import select
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

import livemetrics
import livemetrics.publishers.aiohttp

routes = web.RouteTableDef()

def is_healthy():
    return True

LM = livemetrics.LiveMetrics(json.dumps(dict(version=pr.__version__)), "pr", is_healthy)

def ok_status(ret):
    return str(ret.status)

# An exception class to propagate web.Response
class ResponseException(BaseException):
    def __init__(self, response):
        self.response = response

# _____________________________________________________________________________
@web.middleware
async def error_middleware(request, handler):
    try:
        response = await handler(request)
        if response.status >= 400:
            logging.info("Request failed with HTTP error %d", response.status)
        return response
    except KeyError as exc:
        if exc.args==('transactionId',):
                return web.json_response({'code':1, 'message': 'Missing transactionId'}, status=400)
        raise
    except ResponseException as resp:
        return resp.response
    except aiohttp.web_exceptions.HTTPException:
        raise
    except Exception as exc:
        logging.exception("Exception caught in middleware: [%s]", str(exc))
        return web.json_response(dict(code=0, message=str(exc)), status=500)


# _____________________________________________________________________________
def get_ssl_context():
    ctx = None
    if pr.args.server_certfile:
        logging.debug("Setup SSL context for this server: %s - %s", pr.args.server_certfile, pr.args.server_keyfile)
        if pr.args.server_ca_certfile:
            # used ssl.CERT_REQUIRED for mutual authent needed, ssl.CERT_OPTIONAL if not
            logging.debug("SSL context setup for cafile: %s", pr.args.server_ca_certfile)
            ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH,
                                            cafile=pr.args.server_ca_certfile)
            ctx.verify_mode = ssl.CERT_REQUIRED
            ctx.check_hostname = True
        else:
            ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ctx.load_cert_chain(pr.args.server_certfile,
                            pr.args.server_keyfile,
                            password=pr.args.server_keyfile_password)
        logging.debug("certfile/keyfile loaded for SSL Context")
    return ctx


# _____________________________________________________________________________
async def _strip_server(req, res):
    if 'Server' in res.headers:
        del res.headers['Server']


# _____________________________________________________________________________
async def start_monitoring(app):
    app2 = web.Application(middlewares=[error_middleware])
    app2.add_routes(livemetrics.publishers.aiohttp.routes(LM))
    runner = web.AppRunner(app2)
    await runner.setup()
    site = web.TCPSite(runner, host=pr.args.ip, port=pr.args.monitoring_port)
    await site.start()

# _____________________________________________________________________________
def get_app():
    app = web.Application(client_max_size=pr.args.input_max_size*1024*1024,
                          middlewares=[error_middleware])
    app.add_routes(routes)
    if pr.args.monitoring_port<=0 or pr.args.monitoring_port==pr.args.port:
        app.add_routes(livemetrics.publishers.aiohttp.routes(LM))
    else:
        app.on_startup.append(start_monitoring)
    # Remove Server header for security reason
    app.on_response_prepare.append(_strip_server)

    return app


# _____________________________________________________________________________
def serve():
    app = get_app()
    if pr.args.do_not_start:
        logging.warning('Not starting the application')
        return
    logging.info('Starting application...')
    web.run_app(app, host=pr.args.ip, port=pr.args.port, access_log=None, ssl_context=get_ssl_context())
    logging.info('Closing application...')
    if pr.aengine:
        # proper cleanup of async engine
        asyncio.run(pr.aengine.dispose())
        logging.info('Async engine closed')

# _____________________________________________________________________________
def to_bool(x):
    if x in [True, 'True', 'true', 1, '1', 'yes', 'y', 'Y', 'Yes', 'YES']:
        return True
    return False

# Schema validation
registry = None
schemas = None
api = None
def validate_json(data, schema_name, with_required=True):
    global schemas
    global api
    global registry
    if not schemas or not api:
        if pr.args and pr.args.api_file:
            with open(pr.args.api_file, 'r') as f:
                api = yaml.load(f, Loader=yaml.SafeLoader)
            schemas = api['components']['schemas']

            # patch schemas for readOnly attributes
            schemas['Identity']['required'].remove('identityId')

            # apply custo definition
            if pr.model.custo and 'BiographicData' in pr.model.custo:
                schemas['BiographicData'] = pr.model.custo['BiographicData']
            if pr.model.custo and 'ContextualData' in pr.model.custo:
                schemas['ContextualData'] = pr.model.custo['ContextualData']

            registry = referencing.Registry().with_resource(
                uri='',
                resource=referencing.Resource.from_contents(api, default_specification=referencing.jsonschema.DRAFT7)
            )
            registry = registry.crawl()
        else:
            logging.debug('No validation of incoming JSON')
            return None
    # validate the data against the schema
    v = jsonschema.Draft7Validator(schema=schemas[schema_name], registry=registry, _resolver = registry.resolver())
    if with_required:
        msg = "\n".join([error.message for error in v.iter_errors(instance=data)])
    else:
        # do not check required field or None value
        msg = "\n".join([error.message for error in v.iter_errors(instance=data) if error.message.find('is a required property')<0 and error.message.find('None is not of type')<0])
    
    if msg:
        logging.error(msg)
        return msg

# _____________________________________________________________________________
# PR interface
# _____________________________________________________________________________

# _____________________________________________________________________________
def _build_predicate(data, reference, gallery, group, limit, offset):
    if group:
        sel = select(pr.model.Identity.personId)
    else:
        sel = select(pr.model.Identity)
    for pred in data:
        k = pred['attributeName']
        found = False
        for pre, lis in [('',['personId']), ('bgd_', pr.model.CUSTO_BGD)]:
            if k in lis:
                found = True
                if pred['operator'] == '=':
                    sel = sel.where( getattr(pr.model.Identity, pre+k) == pred['value'])
                elif pred['operator']=='!=':
                    sel = sel.where( getattr(pr.model.Identity, pre+k) != pred['value'])
                elif pred['operator']=='<':
                    sel = sel.where( getattr(pr.model.Identity, pre+k) < pred['value'])
                elif pred['operator']=='>':
                    sel = sel.where( getattr(pr.model.Identity, pre+k) > pred['value'])
                elif pred['operator']=='<=':
                    sel = sel.where( getattr(pr.model.Identity, pre+k) <= pred['value'])
                elif pred['operator']=='>=':
                    sel = sel.where( getattr(pr.model.Identity, pre+k) >= pred['value'])
                else:
                    return web.json_response({'code':1, 'message': 'Invalid operator [{}] in query expression'.format(pred['operator'])}, status=400)
                break
        if not found:
            return web.json_response({'code':1, 'message': 'Unknown attribute [{}] in query expression'.format(k)}, status=400)

    if reference:
        sel = sel.where(pr.model.Identity.isReference)

    if group:
        sel = sel.group_by("personId")

    if gallery:
        sel = sel.join(pr.model.Gallery).where(pr.model.Gallery.galleryId == gallery)

    if limit:
        sel = sel.limit(limit)
    if offset:
        sel = sel.offset(offset)
    return sel

# _____________________________________________________________________________
@routes.post('/v1/persons')
@LM.timer("findPersons", ok_status, "error")
async def findPersons(request):
    transaction_id = request.query['transactionId']
    group = to_bool(request.query.get('group', False))
    reference = to_bool(request.query.get('reference', False))
    gallery = request.query.get('gallery', None)
    offset = int(request.query.get('offset', 0))
    limit = int(request.query.get('limit', 100))

    data = await request.json()
    logging.info("[%s] - findPersons", transaction_id)

    msg = validate_json(data, 'Expressions')
    if msg:
        return web.json_response(data={'code': 400, 'message': msg}, status=400)

    # build predicate
    async with AsyncSession(pr.aengine) as session, session.begin():
        sel = _build_predicate(data, reference, gallery, group, limit, offset)
        res = await session.execute(sel)
        # Execute
        ret = []
        for I in res.scalars():
            if not group:
                ret.append( dict(personId=I.personId, identityId=I.identityId) )
            else:
                ret.append( dict(personId=I) )
    
        return web.json_response(ret, status=200)


# _____________________________________________________________________________
def _get_person(session, person_id):
    res = pr.model.Person.find_by_id(session, person_id)
    if len(res) > 1:
        # not sure we can reach this code since personId is a PK
        raise ResponseException(web.Response(status=400))
    if len(res) < 1:
        raise ResponseException(web.Response(status=404))
    return res[0]

# _____________________________________________________________________________
async def _aget_person(session, person_id):
    res = await pr.model.Person.afind_by_id(session, person_id)
    if len(res) > 1:
        # not sure we can reach this code since personId is a PK
        raise ResponseException(web.Response(status=400))
    if len(res) < 1:
        raise ResponseException(web.Response(status=404))
    return res[0]

# _____________________________________________________________________________
@routes.post('/v1/persons/{personId}')
@LM.timer("createPerson", ok_status, "error")
async def createPerson(request):
    transaction_id = request.query['transactionId']
    person_id = request.match_info['personId']

    data = await request.json()
    logging.info("[%s] - createPerson for personId [%s]", transaction_id, person_id)

    msg = validate_json(data, 'Person')
    if msg:
        return web.json_response(data={'code': 400, 'message': msg}, status=400)

    import pr.serialize
    async with AsyncSession(pr.aengine) as session, session.begin():
        # check that person does not exist
        res = await pr.model.Person.afind_by_id(session, person_id)
        if res:
            return web.Response(status=409)

        person_schema = pr.serialize.PersonSchema()
        np = person_schema.load(data, session=session)
        np.personId = person_id
        session.add(np)

    return web.Response(status=201)

# _____________________________________________________________________________
@LM.timer("readPerson", ok_status, "error")
async def readPerson(transaction_id, person_id):
    logging.info("[%s] - readPerson for personId [%s]", transaction_id, person_id)

    import pr.serialize
    async with AsyncSession(pr.aengine) as session, session.begin():
        p = await _aget_person(session, person_id)
        person_schema = pr.serialize.PersonSchema()
        data = person_schema.dump(p)
        # del data['identities']
        # data['personId'] = person_id
        return web.json_response(data, status=200)


# _____________________________________________________________________________
@routes.put('/v1/persons/{personId}')
@LM.timer("updatePerson", ok_status, "error")
async def updatePerson(request):
    transaction_id = request.query['transactionId']
    person_id = request.match_info['personId']

    data = await request.json()
    logging.info("[%s] - updatePerson for personId [%s]", transaction_id, person_id)

    msg = validate_json(data, 'Person')
    if msg:
        return web.json_response(data={'code': 400, 'message': msg}, status=400)

    import pr.serialize
    async with AsyncSession(pr.aengine) as session, session.begin():
        np = await _aget_person(session, person_id)
        person_schema = pr.serialize.PersonSchema()
        person_schema.load(data, instance=np, session=session)
        session.add(np)

    return web.Response(status=204)

# _____________________________________________________________________________
@routes.delete('/v1/persons/{personId}')
@LM.timer("deletePerson", ok_status, "error")
async def deletePerson(request):
    transaction_id = request.query['transactionId']
    person_id = request.match_info['personId']

    logging.info("[%s] - deletePerson for personId [%s]", transaction_id, person_id)

    async with AsyncSession(pr.aengine) as session, session.begin():
        p = await _aget_person(session, person_id)
        await session.delete(p)

    return web.Response(status=204)

# _____________________________________________________________________________
@routes.post('/v1/persons/{personIdTarget}/merge/{personIdSource}')
@LM.timer("mergePerson", ok_status, "error")
async def mergePerson(request):
    transaction_id = request.query['transactionId']
    person_id_target = request.match_info['personIdTarget']
    person_id_source = request.match_info['personIdSource']

    logging.info("[%s] - mergePerson with personId [%s] in personId [%s]", transaction_id, person_id_source, person_id_target)

    async with AsyncSession(pr.aengine) as session, session.begin():
        p_source = await _aget_person(session, person_id_source)
        p_target = await _aget_person(session, person_id_target)

        # Check the ID
        target_ids = set()
        for ident in await p_target.awaitable_attrs.identities:
            target_ids.add(ident.identityId)
        for ident in await p_source.awaitable_attrs.identities:
            if ident.identityId in target_ids:
                return web.Response(status=409)
        
        # all good, do the merge and delete the source
        for ident in p_source.identities:
            ident.isReference = False
            ident.personId = person_id_target
        await session.flush()
        await session.refresh(p_source)
        await session.delete(p_source)

    return web.Response(status=204)


# _____________________________________________________________________________
async def _create_identity(transaction_id, person_id, identity_id, data):
    msg = validate_json(data, 'Identity')
    if msg:
        return web.json_response(data={'code': 400, 'message': msg}, status=400)

    import pr.serialize

    async with AsyncSession(pr.aengine) as session, session.begin():
        p = await _aget_person(session, person_id)

        # check the identity does not exist in this person
        for ident in await p.awaitable_attrs.identities:
            if ident.identityId == identity_id:
                return web.json_response(data={'code': 1, 'message': 'identityId [{}] already present in person [{}]'.format(identity_id, person_id)}, status=409)

        identity_schema = pr.serialize.IdentitySchema()
        ni = identity_schema.load(data, session=session)
        ni.identityId = identity_id
        session.add(ni)
        p.identities.append(ni)
        session.add(p)

        return web.json_response(data={'identityId': identity_id}, status=200)

# _____________________________________________________________________________
@routes.post('/v1/persons/{personId}/identities')
@LM.timer("createIdentity", ok_status, "error")
async def createIdentity(request):
    transaction_id = request.query['transactionId']
    person_id = request.match_info['personId']
    data = await request.json()
    logging.info("[%s] - createIdentity for personId [%s]", transaction_id, person_id)
    identity_id = uuid.uuid4().hex
    return await _create_identity(transaction_id, person_id, identity_id, data)


# _____________________________________________________________________________
@routes.post('/v1/persons/{personId}/identities/{identityId}')
@LM.timer("createIdentityWithId", ok_status, "error")
async def createIdentityWithId(request):
    transaction_id = request.query['transactionId']
    person_id = request.match_info['personId']
    identity_id = request.match_info['identityId']

    data = await request.json()
    logging.info("[%s] - createIdentityWithId for personId [%s]/[%s]", transaction_id, person_id, identity_id)
    return await _create_identity(transaction_id, person_id, identity_id, data)


# _____________________________________________________________________________
@routes.get('/v1/persons/{personId}/identities/{identityId}')
@LM.timer("readIdentity", ok_status, "error")
async def readIdentity(request):
    transaction_id = request.query['transactionId']
    person_id = request.match_info['personId']
    identity_id = request.match_info['identityId']

    logging.info("[%s] - readIdentity for personId [%s]/[%s]", transaction_id, person_id, identity_id)

    import pr.serialize

    async with AsyncSession(pr.aengine) as session, session.begin():
        p = await _aget_person(session, person_id)

        # get the identity from this person
        for ident in await p.awaitable_attrs.identities:
            if ident.identityId == identity_id:

                identity_schema = pr.serialize.IdentitySchema()
                data = identity_schema.dump(ident)
                return web.json_response(data, status=200)
        return web.Response(status=404)


# _____________________________________________________________________________
@routes.get('/v1/persons/{personId}/identities')
@LM.timer("readIdentities", ok_status, "error")
async def readIdentities(request):
    transaction_id = request.query['transactionId']
    person_id = request.match_info['personId']

    logging.info("[%s] - readIdentities for personId [%s]", transaction_id, person_id)

    import pr.serialize

    async with AsyncSession(pr.aengine) as session, session.begin():
        p = await _aget_person(session, person_id)
        ret = []
        identity_schema = pr.serialize.IdentitySchema()
        for ident in await p.awaitable_attrs.identities:
            data = identity_schema.dump(ident)
            ret.append(data)
        return web.json_response(ret, status=200)


# _____________________________________________________________________________
@routes.put('/v1/persons/{personId}/identities/{identityId}')
@LM.timer("updateIdentity", ok_status, "error")
async def updateIdentity(request):
    transaction_id = request.query['transactionId']
    person_id = request.match_info['personId']
    identity_id = request.match_info['identityId']

    data = await request.json()
    logging.info("[%s] - updateIdentity for personId [%s]/[%s]", transaction_id, person_id, identity_id)

    msg = validate_json(data, 'Identity')
    if msg:
        return web.json_response(data={'code': 400, 'message': msg}, status=400)

    import pr.serialize

    async with AsyncSession(pr.aengine) as session, session.begin():
        p = await _aget_person(session, person_id)
        # get the identity from this person
        pos = -1
        for ident in await p.awaitable_attrs.identities:
            pos += 1
            if ident.identityId == identity_id:
                # Check status, only in CLAIMED an update is allowed
                if ident.status!='CLAIMED':
                    return web.json_response(data={'code': 1, 'message': 'Illegal status of the identity - update is forbidden'}, status=403)
                    
                # we need to replace the identity (this is not a partial update) to make sure
                # optional field not present in input are also updated to their default value
                # XXX probably not as efficient as it could be. Investigate if we can do better
                await session.delete(ident)
                await session.flush()
                identity_schema = pr.serialize.IdentitySchema()
                ni = identity_schema.load(data, session=session)
                ni.identityId = identity_id
                p.identities[pos] = ni
                return web.Response(status=204)
        return web.Response(status=404)

# _____________________________________________________________________________
@routes.patch('/v1/persons/{personId}/identities/{identityId}')
@LM.timer("partialUpdateIdentity", ok_status, "error")
async def partialUpdateIdentity(request):
    transaction_id = request.query['transactionId']
    person_id = request.match_info['personId']
    identity_id = request.match_info['identityId']

    data = await request.json()
    logging.info("[%s] - updateIdentity for personId [%s]/[%s]", transaction_id, person_id, identity_id)

    # nothing is mandatory for a patch
    msg = validate_json(data, 'Identity', with_required=False)
    if msg:
        return web.json_response(data={'code': 400, 'message': msg}, status=400)

    import pr.serialize

    async with AsyncSession(pr.aengine) as session, session.begin():
        p = await _aget_person(session, person_id)
        # get the identity from this person
        for ident in await p.awaitable_attrs.identities:
            if ident.identityId == identity_id:
                # Check status, only in CLAIMED an update is allowed
                if ident.status!='CLAIMED':
                    return web.json_response(data={'code': 1, 'message': 'Illegal status of the identity - update is forbidden'}, status=403)
                # update the object with whatever was defined in the input
                identity_schema = pr.serialize.IdentitySchema()
                identity_schema.load(data, instance=ident, session=session, partial=True)
                session.add(ident)
                return web.Response(status=204)
        return web.Response(status=404)

# _____________________________________________________________________________
@routes.delete('/v1/persons/{personId}/identities/{identityId}')
@LM.timer("deleteIdentity", ok_status, "error")
async def deleteIdentity(request):
    transaction_id = request.query['transactionId']
    person_id = request.match_info['personId']
    identity_id = request.match_info['identityId']

    logging.info("[%s] - deleteIdentity for personId [%s]/[%s]", transaction_id, person_id, identity_id)

    async with AsyncSession(pr.aengine) as session, session.begin():
        p = await _aget_person(session, person_id)
        # get the identity from this person
        for ident in await p.awaitable_attrs.identities:
            if ident.identityId == identity_id:
                await session.delete(ident)
                return web.Response(status=204)
        return web.Response(status=404)


# _____________________________________________________________________________
@routes.post('/v1/persons/{personIdTarget}/move/{personIdSource}/identities/{identityId}')
@LM.timer("moveIdentity", ok_status, "error")
async def moveIdentity(request):
    transaction_id = request.query['transactionId']
    person_id_target = request.match_info['personIdTarget']
    person_id_source = request.match_info['personIdSource']
    identity_id_source = request.match_info['identityId']

    logging.info("[%s] - moveIdentity [%s] from person [%s] into person [%s]", transaction_id, identity_id_source, person_id_source, person_id_target)

    async with AsyncSession(pr.aengine) as session, session.begin():
        p_source = await _aget_person(session, person_id_source)
        p_target = await _aget_person(session, person_id_target)

        # Check the ID
        target_ids = set()
        for ident in await p_target.awaitable_attrs.identities:
            target_ids.add(ident.identityId)
        for ident in await p_source.awaitable_attrs.identities:
            if ident.identityId == identity_id_source:
                if identity_id_source in target_ids:
                    return web.Response(status=409)
        
                # do the move
                ident.isReference = False
                ident.personId = person_id_target
                return web.Response(status=204)

    return web.Response(status=404)


# _____________________________________________________________________________
@routes.put('/v1/persons/{personId}/identities/{identityId}/status')
@LM.timer("setIdentityStatus", ok_status, "error")
async def setIdentityStatus(request):
    transaction_id = request.query['transactionId']
    person_id = request.match_info['personId']
    identity_id = request.match_info['identityId']
    status = request.query['status']

    logging.info("[%s] - setIdentityStatus for personId [%s]/[%s]", transaction_id, person_id, identity_id)

    async with AsyncSession(pr.aengine) as session, session.begin():
        p = await _aget_person(session, person_id)
        # get the identity from this person
        for ident in await p.awaitable_attrs.identities:
            if ident.identityId == identity_id:
                ident.status = status
                session.add(ident)
                return web.Response(status=204)
        return web.Response(status=404)

# _____________________________________________________________________________
@routes.put('/v1/persons/{personId}/identities/{identityId}/reference')
@LM.timer("defineReference", ok_status, "error")
async def defineReference(request):
    transaction_id = request.query['transactionId']
    person_id = request.match_info['personId']
    identity_id = request.match_info['identityId']

    logging.info("[%s] - defineReference for personId [%s]/[%s]", transaction_id, person_id, identity_id)

    import pr.serialize

    async with AsyncSession(pr.aengine) as session, session.begin():
        p = await _aget_person(session, person_id)
        # get the identity from this person
        found = False
        for ident in await p.awaitable_attrs.identities:
            if ident.identityId == identity_id:
                # Check status, only in VALID state an identity can be the reference
                if ident.status!='VALID':
                    return web.json_response(data={'code': 1, 'message': 'Illegal status of the identity - defineReference is forbidden'}, status=403)
                found = True
                ident.isReference = True
                session.add(ident)
                break
        if not found:
            return web.Response(status=404)
        for ident in await p.awaitable_attrs.identities:
            if ident.identityId != identity_id and ident.isReference:
                ident.isReference = False
                session.add(ident)

    return web.Response(status=204)

# _____________________________________________________________________________
@routes.get('/v1/persons/{personId}/reference')
@LM.timer("readReference", ok_status, "error")
async def readReference(request):
    transaction_id = request.query['transactionId']
    person_id = request.match_info['personId']

    logging.info("[%s] - readReference for personId [%s]", transaction_id, person_id)

    import pr.serialize

    async with AsyncSession(pr.aengine) as session, session.begin():
        p = await _aget_person(session, person_id)
        # get the reference identity from this person
        for ident in await p.awaitable_attrs.identities:
            if ident.isReference:
                identity_schema = pr.serialize.IdentitySchema()
                data = identity_schema.dump(ident)
                return web.json_response(data, status=200)
        return web.Response(status=404)

# _____________________________________________________________________________
@routes.get('/v1/galleries')
@LM.timer("readGalleries", ok_status, "error")
async def readGalleries(request):
    transaction_id = request.query['transactionId']

    logging.info("[%s] - readGalleries", transaction_id)

    async with AsyncSession(pr.aengine) as session, session.begin():
        ret = await pr.model.Gallery.avalues(session)
        return web.json_response(ret, status=200)

# _____________________________________________________________________________
@routes.get('/v1/galleries/{galleryId}')
@LM.timer("readGalleryContent", ok_status, "error")
async def readGalleryContent(request):
    transaction_id = request.query['transactionId']
    gallery_id = request.match_info['galleryId']
    offset = int(request.query.get('offset', 0))
    limit = int(request.query.get('limit', 1000))

    logging.info("[%s] - readGalleryContent for gallery [%s]", transaction_id, gallery_id)

    async with AsyncSession(pr.aengine) as session, session.begin():
        ret = await pr.model.Gallery.aget_identities(session, gallery_id, offset, limit)
        return web.json_response([{'personId': x.personId, 'identityId': x.identityId} for x in ret], status=200)

# _____________________________________________________________________________
# Services with the same URL in PR and DataAccess
# _____________________________________________________________________________
# _____________________________________________________________________________
@routes.get('/v1/persons/{id}')
async def getPersonWithId(request):
    id = request.match_info['id']
    names = request.query.getall('attributeNames', [])
    if names or 'transactionId' not in request.query:
        return await readPersonAttributes(id, names)
    transaction_id = request.query['transactionId']
    return await readPerson(transaction_id, id)


# _____________________________________________________________________________
# Data Access interface
# Note: when there is no reference identity, the latest one is used
# _____________________________________________________________________________

# _____________________________________________________________________________
@routes.post('/v1/persons/{uin}/match')
@LM.timer("matchPersonAttributes", ok_status, "error")
async def matchPersonAttributes(request):
    uin = request.match_info['uin']

    data = await request.json()
    logging.info("matchPersonAttributes for UIN [%s]", uin)

    import pr.serialize

    async with AsyncSession(pr.aengine) as session, session.begin():
        p = await _aget_person(session, uin)
        # get the reference identity from this person
        for ident in await p.awaitable_attrs.identities:
            if ident.isReference:
                identity_schema = pr.serialize.IdentitySchema()
                ident_data = identity_schema.dump(ident)
                ret = []
                for k, v in data.items():
                    if k not in ident_data['biographicData'] and \
                       k not in ident_data['contextualData'] and \
                       k not in ident_data:
                        ret.append(dict(attributeName=k, errorCode=0))
                    elif k in ident_data['biographicData'] and ident_data['biographicData'][k] != v:
                        ret.append(dict(attributeName=k, errorCode=1))
                    elif k in ident_data['contextualData'] and ident_data['contextualData'][k] != v:
                        ret.append(dict(attributeName=k, errorCode=1))
                    elif k in ident_data and ident_data[k] != v:
                        ret.append(dict(attributeName=k, errorCode=1))
                return web.json_response(ret, status=200)
        return web.Response(status=404)


# _____________________________________________________________________________
@routes.get('/v1/persons')
@LM.timer("queryPersonList", ok_status, "error")
async def queryPersonList(request):
    offset = int(request.query.get('offset', 0))
    limit = int(request.query.get('limit', 100))
    names = request.query.getall('names', [])
    attributes = {}
    for k, v in request.query.items():
        if k in ['names', 'offset', 'limit']:
            continue
        attributes[k] = v
    logging.info("queryPersonList for attributes [%s]", attributes)

    import pr.serialize

    async with AsyncSession(pr.aengine) as session, session.begin():
        data = []
        for k,v in attributes.items():
            data.append(dict(
                attributeName=k,
                operator='=',
                value=v
            ))
        sel = _build_predicate(data, reference=True, gallery=None, group=False, limit=limit, offset=offset)
        if type(sel) is web.Response:
            return sel

        # Execute
        ret = []
        identity_schema = pr.serialize.IdentitySchema()
        result = await session.execute(sel)
        for ident in result.scalars():
            if not names:
                ret.append(ident.personId)
                continue
            ident_data = identity_schema.dump(ident)
            obj = {}
            for k in names:
                if k not in ident_data['biographicData'] and \
                    k not in ident_data['contextualData'] and \
                    k not in ident_data:
                    return web.json_response(dict(code=2, message="Unknown name [{}]".format(k)), status=400)
                if k in ident_data['biographicData']:
                    obj[k] = ident_data['biographicData'][k]
                elif k in ident_data['contextualData']:
                    obj[k] = ident_data['contextualData'][k]
                elif k in ident_data:
                    obj[k] = ident_data[k]
            ret.append(obj)
        return web.json_response(ret, status=200)


# _____________________________________________________________________________
@LM.timer("readPersonAttributes", ok_status, "error")
async def readPersonAttributes(uin, names):
    logging.info("readPersonAttributes for UIN [%s]", uin)

    if not names:
        return web.json_response(dict(code=2, message="No names specified"), status=400)

    import pr.serialize

    async with AsyncSession(pr.aengine) as session, session.begin():
        identity_schema = pr.serialize.IdentitySchema()
        p = await _aget_person(session, uin)
        # get the reference identity from this person
        for ident in await p.awaitable_attrs.identities:
            if ident.isReference:
                ident_data = identity_schema.dump(ident)
                obj = {}
                for k in names:
                    if k not in ident_data['biographicData'] and \
                        k not in ident_data['contextualData'] and \
                        k not in ident_data:
                        obj[k] = dict(code=2, message="Unknown attribute name [{}]".format(k))
                    elif k in ident_data['biographicData']:
                        obj[k] = ident_data['biographicData'][k]
                    elif k in ident_data['contextualData']:
                        obj[k] = ident_data['contextualData'][k]
                    elif k in ident_data:
                        obj[k] = ident_data[k]
                return web.json_response(obj, status=200)
        return web.Response(status=404)

# _____________________________________________________________________________
@routes.post('/v1/persons/{uin}/verify')
@LM.timer("verifyPersonAttributes", ok_status, "error")
async def verifyPersonAttributes(request):
    uin = request.match_info['uin']

    data = await request.json()
    logging.info("verifyPersonAttributes for UIN [%s]", uin)

    import pr.serialize

    async with AsyncSession(pr.aengine) as session, session.begin():
        p = await _aget_person(session, uin)
        
        data.append(dict(
            attributeName='personId',
            operator='=',
            value=uin
        ))
        sel = _build_predicate(data, reference=True, gallery=None, group=True, limit=100, offset=0)
        if type(sel) is web.Response:
            return sel
        result = await session.execute(sel)
        for ident in result.scalars():
            # we found one
            return web.json_response(True, status=200)
        return web.json_response(False, status=200)

# _____________________________________________________________________________
@routes.get('/v1/persons/{uin}/document')
@LM.timer("readDocument", ok_status, "error")
async def readDocument(request):
    # Limitation: no conversion to the requested format (format)
    uin = request.match_info['uin']
    logging.info("readDocument for UIN [%s]", uin)

    sec_uin = request.query.get('secondaryUin', None)
    if sec_uin:
        return web.json_response(dict(code=3, message="readDocument: secondaryUin is not supported"), status=400)

    doctype = request.query.get('doctype', None)
    format = request.query.get('format', None)
    if not doctype or not format or not format in ['pdf', 'jpeg', 'png']:
        return web.json_response(dict(code=4, message="readDocument: incorrect parameters for doctype or format"), status=400)

    mtype_map = {
        'pdf': 'application/pdf',
        'jpeg': 'image/jpeg',
        'png': 'image/png',
    }
    import pr.serialize

    mime_parts = []
    async with AsyncSession(pr.aengine) as session, session.begin():
        p = await _aget_person(session, uin)
        # get the reference identity from this person
        for ident in await p.awaitable_attrs.identities:
            if ident.isReference:
                # loop therough the documents
                for doc in ident.documentData:
                    if doc.documentType==doctype or \
                    (doc.documentType=='OTHER' and doc.documentTypeOther==doctype):
                        # we found the doc
                        for part in doc.parts:
                            if part.data and part.mimeType==mtype_map[format]:
                                mime_parts.append( (part.data, part.mimeType, None))
                            elif part.dataRef and part.mimeType==mtype_map[format]:
                                mime_parts.append( (None, part.mimeType, part.dataRef))

    if len(mime_parts)==1:
        # not exactly in the specs but more convenient to use like that
        if mime_parts[0][0]:
            return web.Response(status=200, body=mime_parts[0][0], content_type=mime_parts[0][1])
        else:
            # redirect
            raise web.HTTPFound(mime_parts[0][2])
    if len(mime_parts)>1:
        resp = web.StreamResponse(status=200,
            headers={
                'Content-Type': 'multipart/mixed; boundary=**xx**BOUNDARY**xx**'
            })
        await resp.prepare(request)

        mpwriter = aiohttp.MultipartWriter('mixed', boundary='**xx**BOUNDARY**xx**')
        for p in mime_parts:
            if p[0]:
                mpwriter.append(p[0], {'Content-Type': p[1]})
            else:
                mpwriter.append(p[2], {"Content-Type":"text/uri-list", "location": p[2]})
        await mpwriter.write(resp)
        return resp

    return web.Response(status=404)


#
# Monitoring interface
#

# _____________________________________________________________________________
def gauge_nb_persons():
    if not pr.engine:
        return 0
    with Session(pr.engine) as session, session.begin():
        return session.query(pr.model.Person).count()
LM.gauge('nb_persons', gauge_nb_persons)

# _____________________________________________________________________________
def gauge_nb_identities():
    if not pr.engine:
        return 0
    with Session(pr.engine) as session, session.begin():
        return session.query(pr.model.Identity).count()
LM.gauge('nb_identities', gauge_nb_identities)

# _____________________________________________________________________________
def gauge_nb_biometricdata():
    if not pr.engine:
        return 0
    with Session(pr.engine) as session, session.begin():
        return session.query(pr.model.BiometricData).count()
LM.gauge('nb_biometricdata', gauge_nb_biometricdata)

