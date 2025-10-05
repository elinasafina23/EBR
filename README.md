# Custom MES Integration for AspenTech system:inmation QMIB

This repository contains a lightweight Manufacturing Execution System (MES) integration
service that exposes REST endpoints for batch management and delegates data exchange to
AspenTech **system:inmation** via the **QMIB** interface. The implementation focuses on the
core components required to:

- Manage local batch records and persist them in a relational data store.
- Fetch batch templates and equipment information from QMIB.
- Publish completed batch execution data back to QMIB.
- Acknowledge events and alarms within QMIB.

## Project Structure

```
├── config/                # Configuration templates
├── src/mes/               # Python package with the MES service implementation
│   ├── api/               # FastAPI route definitions
│   ├── connectors/        # Clients for external systems (QMIB)
│   ├── services/          # Domain/business services
│   ├── config.py          # Settings management (env + YAML support)
│   ├── main.py            # FastAPI application factory
│   └── models.py          # Shared Pydantic models
└── pyproject.toml         # Python package metadata and dependencies
```

## Getting Started

1. **Install dependencies**

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -e .
   ```

2. **Configure the service**

   Update `config/mes_config.yaml` with your QMIB gateway URL and credentials, or create an
   `.env` file with the following variables:

   ```env
   MES_QMIB__BASE_URL=https://inmation-gateway/api/qmib
   MES_QMIB__USERNAME=mes-service
   MES_QMIB__PASSWORD=change-me
   MES_QMIB__VERIFY_SSL=false
   MES_DATABASE__URL=sqlite:///./mes.db
   ```

3. **Run the API**

   ```bash
   uvicorn mes.main:create_app --factory --reload
   ```

   The API will be available at `http://127.0.0.1:8000`. Interactive documentation is
   provided via FastAPI at `/docs` and `/redoc`.

## Key Components

### QMIB Client (`mes.connectors.qmib_client.QMIBClient`)

Wraps HTTP interactions with the AspenTech system:inmation QMIB gateway, including retry
logic and convenience methods for commonly used endpoints.

### Batch Service (`mes.services.batch_service.BatchService`)

Persists batch execution data to a relational database (SQLite by default) using SQLAlchemy.
Utility methods allow converting QMIB templates to internal batch records.

### Integration Service (`mes.services.integration_service.IntegrationService`)

Coordinates operations between the local MES and QMIB, such as creating batches from QMIB
templates, publishing completed batches, and acknowledging events.

## Extending the Service

- **Authentication**: Replace HTTP basic authentication in `QMIBClient` with the mechanism
  required by your QMIB deployment (e.g., OAuth2, API tokens).
- **Database**: Update `MES_DATABASE__URL` to target PostgreSQL, SQL Server, or another
  supported backend.
- **Batch Logic**: Expand `BatchService` with additional states, validation rules, or
  integration with manufacturing equipment data sources.

## License

This project is provided under the MIT License. See `LICENSE` (to be supplied by the
implementing organization) for details.
