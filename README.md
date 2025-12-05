Production-ready OnshapeApp skeleton.
Regenerate modules individually.

Manually set up by me, not the codex generated version
Development / Production switch for JSON data

project-root/
│
├── app/
│   ├── __init__.py
│   ├── main.py                      # Flask/FastAPI entrypoint
│   │
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py              # API_VERSION, CREDS_PATH, BASE_URL
│   │   ├── feature_namespaces.py    # from featureNamespaces.py
│   │
│   ├── onshape/
│   │   ├── __init__.py
│   │   ├── client.py                # OnshapeClient wrapper
│   │   ├── parser.py                # URL parsing logic
│   │
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── config_handler.py        # from configHandler.py
│   │   ├── encoding_handler.py      # from configuration_encoding.py
│   │   ├── export_handler.py        # coordinates STEP + ZIP exports
│   │   ├── bom_handler.py           # from assembly_bom.py
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── configuration_service.py # Converts Onshape config JSON → UI schema
│   │   ├── encoding_service.py      # Cleans config values → encodable format
│   │   ├── geometry_service.py      # from geometry_test_functions.py + functions.py
│   │   ├── step_export_service.py   # from step_export.py
│   │   ├── zip_export_service.py    # from zip_export.py
│   │
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── validators.py
│   │   ├── logging.py
│   │   ├── file_ops.py              # temp file handling, safe writes, cleanup
│
│
├── public_api/
│   ├── __init__.py
│   ├── config_routes.py             # Frontend → backend
│   ├── export_routes.py             # Export STEP/ZIP endpoints
│   ├── bom_routes.py                # Fetch + filter assembly BOM
│
├── static/
│   ├── js/
│   │   ├── config-widget.js         # Render configuration UI in Elementor
│   │   ├── export-widget.js         # Trigger STEP/ZIP generation
│
├── passenger_wsgi.py
├── requirements.txt
├── runtime.txt
└── README.md

