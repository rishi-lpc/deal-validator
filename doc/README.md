# Deal Validator

Salesforce loan validation system with Azure Functions deployment.

## Project Structure

```
deal-validator/
├── core/                              # Core validation logic
│   ├── __init__.py
│   ├── config.py                      # Salesforce credentials
│   ├── salesforce_fetcher.py          # Salesforce connector
│   ├── json_driven_validator.py       # Validation engine
│   ├── validation_rules.json          # Validation rules
│   └── reference code/                # Reference validator
│
├── regression_tests/                  # Regression test suite
│   ├── scripts/                       # Test creation & discovery
│   ├── test_*.json                    # 10 test case files
│   ├── test_manifest.json             # Test index
│   └── test_results.json              # Latest results
│
├── functionapp.py                     # Azure Functions wrapper
├── run_regression_tests.py            # Regression test runner
├── test_functionapp.py                # Integration tests
├── requirements.txt                   # Python dependencies
├── host.json                          # Azure Functions config
└── local.settings.json                # Local settings

```

## Local Testing

### Run Core Validator Directly

```bash
# Validate by ID
python -m core.json_driven_validator a0ial00000364X3AAI

# Validate by name
python -m core.json_driven_validator "Canyon Valley - Mezz"

# Search for loans
python -m core.json_driven_validator --search Canyon
```

### Run Azure Functions Locally

1. Install Azure Functions Core Tools:
   ```bash
   # macOS
   brew tap azure/functions
   brew install azure-functions-core-tools@4

   # Windows
   npm install -g azure-functions-core-tools@4
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Start the function app:
   ```bash
   func start
   ```

4. Test endpoints:
   ```bash
   # Health check
   curl http://localhost:7071/api/health

   # Validate by ID
   curl http://localhost:7071/api/validate/id/a0ial00000364X3AAI

   # Validate by name
   curl -X POST http://localhost:7071/api/validate/name \
     -H "Content-Type: application/json" \
     -d '{"loan_name": "Canyon Valley - Mezz", "exact_match": true}'

   # Search loans
   curl "http://localhost:7071/api/search?prefix=Canyon"

   # Batch validation
   curl -X POST http://localhost:7071/api/validate/batch \
     -H "Content-Type: application/json" \
     -d '{"loan_ids": ["a0ial00000364X3AAI", "a0iVy00000ETkIkIAL"]}'
   ```

## Azure Deployment

### Prerequisites

1. Azure CLI installed
2. Azure subscription
3. Azure Functions app created

### Deploy to Azure

```bash
# Login to Azure
az login

# Create resource group (if not exists)
az group create --name deal-validator-rg --location eastus

# Create storage account
az storage account create \
  --name dealvalidatorstorage \
  --resource-group deal-validator-rg \
  --location eastus \
  --sku Standard_LRS

# Create function app
az functionapp create \
  --resource-group deal-validator-rg \
  --consumption-plan-location eastus \
  --runtime python \
  --runtime-version 3.11 \
  --functions-version 4 \
  --name deal-validator-func \
  --storage-account dealvalidatorstorage \
  --os-type Linux

# Deploy the function
func azure functionapp publish deal-validator-func
```

### Configure Application Settings

Add Salesforce credentials as environment variables:

```bash
az functionapp config appsettings set \
  --name deal-validator-func \
  --resource-group deal-validator-rg \
  --settings \
    SF_CLIENT_ID="your_client_id" \
    SF_CLIENT_SECRET="your_client_secret" \
    SF_CLIENT_URL="your_salesforce_url"
```

Update `core/config.py` to read from environment variables in production:

```python
import os

SALESFORCE_CREDENTIALS = {
    "client_id": os.getenv("SF_CLIENT_ID", "default_value"),
    "client_secret": os.getenv("SF_CLIENT_SECRET", "default_value"),
    "client_url": os.getenv("SF_CLIENT_URL", "default_url")
}
```

## API Endpoints

### Health Check
- **URL**: `GET /api/health`
- **Auth**: Anonymous
- **Response**: Service status

### Validate by ID
- **URL**: `GET /api/validate/id/{loan_id}`
- **Auth**: Function key required
- **Response**: Validation results with warnings and errors

### Validate by Name
- **URL**: `POST /api/validate/name`
- **Auth**: Function key required
- **Body**: `{"loan_name": "...", "exact_match": true}`
- **Response**: Validation results

### Search Loans
- **URL**: `GET /api/search?prefix=Canyon`
- **Auth**: Function key required
- **Response**: List of matching loans

### Batch Validation
- **URL**: `POST /api/validate/batch`
- **Auth**: Function key required
- **Body**: `{"loan_ids": ["id1", "id2"]}`
- **Response**: Array of validation results

## Validation Output Format

```json
{
  "LOAN_NAME": "Canyon Valley - Mezz",
  "LOAN_ID": "a0ial00000554ePAAQ",
  "LOAN_AMOUNT": 6000000.00,
  "CLOSE_DATE": "2024-12-24",
  "WARNINGS": [
    {
      "TABLE": "DRAW",
      "ID": null,
      "FIELD": null,
      "MESSAGE": "Total draw amounts do not match loan amount"
    }
  ],
  "ERRORS": [
    {
      "TABLE": "DRAW",
      "ID": "a1PVy000006E2GDMA0",
      "FIELD": "CM_END_DATE__C",
      "MESSAGE": "\"Draw End Date\" is required."
    }
  ],
  "validation_passed": false
}
```

## Regression Testing

Simple curl-based API endpoint tests:

### Running Regression Tests

```bash
# Start function app locally
func start

# Run all regression tests
./regression_tests/run_all_tests.sh
```

This will test all endpoints and save JSON responses to timestamped folders.

### Test Suites

```bash
# Test validate by ID endpoint (10 loans)
./regression_tests/test_by_id.sh

# Test validate by name endpoint (5 loans)
./regression_tests/test_by_name.sh

# Test batch validation endpoint (6 batches)
./regression_tests/test_batch.sh
```

### Test Coverage

- **21 tests** covering all major endpoints
- **10 diverse loan types**: Preferred, Senior, Mezzanine, Tranches
- **Payment types**: IO, P&I, mixed, minimal data
- **Results saved as JSON** for easy review

See [regression_tests/README.md](regression_tests/README.md) for detailed documentation.

## Development

The code is organized to keep business logic separate from Azure Functions:
- **core/**: Contains all business logic - can be tested independently
- **functionapp.py**: Thin wrapper that exposes core functionality via HTTP
- **regression_tests/**: Comprehensive test suite with expected results

This separation allows you to:
- Run validation locally without Azure Functions
- Unit test the core logic easily
- Deploy the same code to different platforms (AWS Lambda, Google Cloud Functions, etc.)
- Maintain regression tests that validate against expected outcomes
