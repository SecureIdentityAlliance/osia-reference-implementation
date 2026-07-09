
# enrollment

## Tests

Using Docker:

    docker build -t enrollment .
    docker run -ti --entrypoint /bin/sh enrollment
    docker run -v /<PATH>/enrollment/tests:/tests -p 8080:8080 enrollment --custo-filename /tests/custo.yaml

Starting from the command line::

    pip install -e .
    ENROLLMENT_CUSTO_FILENAME=tests/custo.yaml ENROLLMENT_DATABASE_URL=postgresql+psycopg2://admin:SuperSecret@localhost/plug2db python -m enrollment

    ENROLLMENT_CUSTO_FILENAME=tests/custo.yaml python -m enrollment --dump-schema

To test with PostgreSQL::

    docker compose -f docker-compose-postgres.yml up -d --force-recreate --build
    source .tox/py/bin/activate # or another venv with the prerequisite libs installed
    ENROLLMENT_CUSTO_FILENAME=tests/custo.yaml  SQLITE=0 pytest tests/test_enrollment.py
    # or
    ENROLLMENT_CUSTO_FILENAME=tests/custo.yaml  SQLITE=0 python tests/test_enrollment.py http://localhost:8080/
    docker compose -f docker-compose-postgres.yml down --remove-orphans -v
    docker system prune -f

TODO
----

- Keep TZ in PG (returned as UTC when reading data)

