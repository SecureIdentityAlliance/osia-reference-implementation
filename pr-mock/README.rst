Population Registry Mock
========================

This directory contains a PR mock that can be used in the context of tests or demonstration.
It is not suitable for production.

Services
--------

The following services are implemented:

.. list-table:: PR Services
    :header-rows: 1

    * - Service
      - Status

    * - findPersons
      - 90% (galleries not supported)
    * - createPerson
      - 100%
    * - readPerson
      - 100%
    * - updatePerson
      - 100%
    * - deletePerson
      - 100%
    * - mergePerson
      - 0%
    * - readIdentities
      - 100%
    * - createIdentity
      - 100%
    * - createIdentityWithId
      - 100%
    * - readIdentity
      - 100%
    * - updateIdentity
      - 0%
    * - partialUpdateIdentity
      - 0%
    * - deleteIdentity
      - 0%
    * - moveIdentity
      - 0%
    * - setIdentityStatus
      - 0%
    * - defineReference
      - 100%
    * - readReference
      - 100%
    * - readGalleries
      - 0%
    * - readGalleryContent
      - 0%

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
      - 0%
    * - readDocument
      - 0%

