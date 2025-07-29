Population Registry
===================

This directory contains a Population Registry (PR) implementation.

Services
--------

The following services are implemented:

.. list-table:: PR Services
    :header-rows: 1

    * - Service
      - Status

    * - findPersons
      - 100%
    * - createPerson
      - 100%
    * - readPerson
      - 100%
    * - updatePerson
      - 100%
    * - deletePerson
      - 100%
    * - mergePerson
      - 100%
    * - readIdentities
      - 100%
    * - createIdentity
      - 100%
    * - createIdentityWithId
      - 100%
    * - readIdentity
      - 100%
    * - updateIdentity
      - 100%
    * - partialUpdateIdentity
      - 100%
    * - deleteIdentity
      - 100%
    * - moveIdentity
      - 100%
    * - setIdentityStatus
      - 100%
    * - defineReference
      - 100%
    * - readReference
      - 100%
    * - readGalleries
      - 100%
    * - readGalleryContent
      - 100%

and:

.. list-table:: Data Access Services
    :header-rows: 1

    * - Service
      - Status

    * - queryPersonList
      - 100%
    * - readPersonAttributes
      - 100%
    * - matchPersonAttributes
      - 100%
    * - verifyPersonAttributes
      - 100%
    * - readDocument
      - 100%



Links:

- https://docs.sqlalchemy.org/en/20/_modules/examples/asyncio/async_orm.html

Tests
-----

Using Docker::

    docker build -t pr .
    docker run -ti --entrypoint /bin/sh pr
    docker run -v /<PATH>/pr/tests:/tests -p 8080:8080 pr --custo-filename /tests/custo.yaml

Starting from the command line::

    pip install -e .
    PR_CUSTO_FILENAME=tests/custo.yaml PR_DATABASE_URL=postgresql+psycopg2://admin:SuperSecret@localhost/plug2db python -m pr

To test with PostgreSQL::

    docker compose -f docker-compose-postgres.yml up -d --force-recreate --build
    source .tox/py/bin/activate # or another venv with the prerequisite libs installed
    pytest tests/test_server.py
    # or
    python tests/test_server.py http://localhost:8080/
    docker compose -f docker-compose-postgres.yml down --remove-orphans -v
    docker system prune -f

TODO
----

- Keep TZ in PG (returned as UTC when reading data)

