
Technical Details of Exchanges
==============================

(3) Enrollment Data
-------------------

The Enrollment Server is expecting from the station::

    {
        "enrollmentType": "CHILD",
        "requestData": {},
        "contextualData":
        {
            "enrollmentDate": "2026-09-29T12:00:00+02:00",
        },
        "biographicData":
        {
            "firstName": "John",
            "lastName": "Doe",
            "dateOfBirth": "2026-10-05",
            "gender": "M",
            "parentUIN": "<UIN>"
        },
        "biometricData":
        [
            {
                "biometricType": "FACE",
                "image": "<base64-encode image>"
            }
        ]
    }


(4) Event Published after Enrollment
------------------------------------

The enrollment server is publishing on the topic ``enrollment`` the event ``birthEnrollment:

.. code-source:: json

    {
        "source": "EnrollmentServer",
        "enrollmentId": "<enrollment ID>",
        "transactionId": "<transaction ID>"
    }

(10) Event Published after Child Registration in CR
---------------------------------------------------

The civil registry is publishing on the topic ``CR`` the event ``liveBirth``:

.. code-source:: json

    {
        "source": "CR",
        "uin": "<UIN of child>",
        "uin1": "<UIN of parent>",
        "uin2": "",
        "enrollmentId": "<enrollment ID>",
        "transactionId": "<transaction ID>"
    }

(15) Create Identity
--------------------

.. code-source:: json

    {
        "status": "VALID",
        "identityType": "CHILD",
        "galleries": ["DEMO"],
        "contextualData":
        {
            "enrollmentDate": "2026-09-29T12:00:00+02:00"
        },
        "biographicData":
        {
            "firstName": "John",
            "lastName": "Doe",
            "dateOfBirth": "2026-10-05",
            "gender": "M"
        },
        "biometricData":
        [
        ]
    }

``identityType`` is copied from the ``enrollmentType`` field.
``contextualData`` is copied from the enrollment's contextual data block.
No biometric data are included in the identity.

(17) Create Encounter
---------------------

.. code-source:: json

    {
        "status": "ACTIVE",
        "encounterType": "CHILD",
        "galleries": ["DEMO"],
        "contextualData":
        {
            "enrollmentDate": "2026-09-29T12:00:00+02:00"
        },
        "biographicData": {},
        "biometricData":
        [
            {
                "biometricType": "FACE",
                "image": "<base64-encode image>"
            }
        ]
    }

``encounterType`` is copied from the ``enrollmentType`` field.
``contextualData`` is copied from the enrollment's contextual data block.
No biographic data are included in the encounter.

(18) Create Credential Request
------------------------------

.. code-source:: json

    {
        "status": "PENDING",
        "requestData":
        {
            "priority": 1,
            "credentialProfileId": "ID_CARD",
            "requestType": "FIRST_ISSUANCE",
            "validFromDate": "<today>",
            "validToDate": "<today + 4 years>",
            "issuingAuthority": "OSIA"
        },
        "personId": "<UIN>",
        "biographicData":
        {
            "firstName": "John",
            "lastName": "Doe",
            "dateOfBirth": "2026-10-05",
            "gender": "M"
        },
        "biometricData":
        [
            {
                "biometricType": "FACE",
                "image": "<base64-encode image>"
            }
        ]
    }


