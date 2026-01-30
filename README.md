# Deal Validator

Salesforce loan validation system with Azure Functions deployment.

## Quick Links

📖 **[Full Documentation](doc/README.md)** - Complete setup and usage guide
🚀 **[Quick Start](doc/QUICKSTART.md)** - Get started quickly
🧪 **[Regression Tests](doc/REGRESSION_TESTS.md)** - Testing guide
🏗️ **[Project Structure](doc/PROJECT_STRUCTURE.md)** - Architecture overview

## Overview

The Deal Validator fetches loan data from Salesforce and validates it against configurable rules, exposing results through HTTP endpoints.

### Key Features

- **Salesforce Integration**: Fetches loan data via OAuth
- **JSON-Driven Validation**: Declarative validation rules
- **HTTP API**: RESTful endpoints for validation
- **Regression Tests**: 21 curl-based API tests
- **Azure Functions**: Serverless deployment
- **CI/CD**: Automated deployment via GitHub Actions

## Project Structure

```
deal-validator/
├── core/                   # Business logic
│   ├── salesforce_fetcher.py
│   ├── json_driven_validator.py
│   └── validation_rules.json
├── functionapp.py          # Azure Functions wrapper
├── regression_tests/       # API endpoint tests
├── doc/                    # Documentation
└── .github/workflows/      # CI/CD pipelines
```

## Quick Start

### Local Testing

```bash
# Test core validator directly
python -m core.json_driven_validator <loan_id>

# Run regression tests
./regression_tests/run_all_tests_direct.sh
```

### Run as Azure Function Locally

```bash
# Start function app
func start

# Test endpoint
curl http://localhost:7071/api/validate/id/<loan_id>
```

## API Endpoints

### Health Check
```bash
GET /api/health
```

### Validate by ID
```bash
GET /api/validate/id/{loan_id}
```

### Validate by Name
```bash
POST /api/validate/name
Content-Type: application/json

{
  "loan_name": "Canyon Valley - Mezz",
  "exact_match": true
}
```

### Search Loans
```bash
GET /api/search?prefix=Canyon
```

### Batch Validation
```bash
POST /api/validate/batch
Content-Type: application/json

{
  "loan_ids": ["id1", "id2", "id3"]
}
```

## Deployment

### Prerequisites

1. Azure Function App named `deal-validator-v1`
2. GitHub repository with Azure credentials configured
3. Push to `dev` branch triggers deployment

### GitHub Actions

The project includes automated deployment:
- **Branch**: `dev`
- **Workflow**: `.github/workflows/deploy-to-azure-dev.yml`
- **Function App**: `deal-validator-v1`
- **Resource Group**: `LPC_amortengine_dev`

### Secrets Required

Configure in GitHub repository settings:
- `AZURE_CREDENTIALS` - Azure Service Principal credentials

See [full deployment guide](doc/README.md#azure-deployment) for details.

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Test locally
python -m core.json_driven_validator <loan_id>

# Run integration tests
python test_functionapp.py

# Run regression tests
./regression_tests/run_all_tests_direct.sh
```

## Documentation

All documentation is in the [`doc/`](doc/) folder:

- **[README.md](doc/README.md)** - Complete documentation
- **[QUICKSTART.md](doc/QUICKSTART.md)** - Quick reference guide
- **[REGRESSION_TESTS.md](doc/REGRESSION_TESTS.md)** - Testing documentation
- **[PROJECT_STRUCTURE.md](doc/PROJECT_STRUCTURE.md)** - Architecture details

## License

Proprietary - Loan Programs Corporation

## Support

For issues or questions, contact the development team or file an issue in the repository.
