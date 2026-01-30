# Project Structure

Clean, organized structure for the Deal Validator project.

## Root Directory

```
deal-validator/
├── core/                              # Business logic (deployable)
├── regression_tests/                  # Test suite (not deployed)
├── archive/                           # Old files (not deployed)
│
├── functionapp.py                     # Azure Functions app
├── run_regression_tests.py            # Test runner
├── test_functionapp.py                # Integration test
│
├── requirements.txt                   # Python dependencies
├── host.json                          # Azure config
├── local.settings.json                # Local settings
├── .funcignore                        # Deployment exclusions
│
├── README.md                          # Main documentation
├── QUICKSTART.md                      # Quick reference
└── REGRESSION_TESTS_SUMMARY.md        # Test suite summary
```

## Core Module (`core/`)

**Purpose**: Contains all business logic for validation
**Deployed**: ✅ Yes (to Azure Functions)

```
core/
├── __init__.py                        # Package init
├── config.py                          # Salesforce credentials
├── salesforce_fetcher.py              # Salesforce connector (22KB)
├── json_driven_validator.py           # Validation engine (21KB)
├── validation_rules.json              # Validation rules (6KB)
└── reference code/                    # Reference implementation
    └── step99.py                      # Metadata provider
```

### Key Files
- **salesforce_fetcher.py**: Fetches loan data from Salesforce
- **json_driven_validator.py**: JSON-driven validation engine
- **validation_rules.json**: Declarative validation rules
- **config.py**: Salesforce OAuth credentials

## Regression Tests (`regression_tests/`)

**Purpose**: Comprehensive test suite with 10 test cases
**Deployed**: ❌ No (local testing only)

```
regression_tests/
├── scripts/                           # Utility scripts
│   ├── quick_discover_loans.py        # Find test candidates
│   ├── create_regression_tests.py     # Generate tests
│   └── test_candidates.json           # Cached candidates
│
├── test_01_mezz_io.json              # Mezzanine + IO
├── test_02_senior_pi.json            # Senior + P&I
├── test_03_mezz_io_vantage.json      # Vantage Mezz
├── test_04_senior_pi_vantage.json    # Vantage Senior
├── test_05_preferred_io.json         # Preferred + IO
├── test_06_tranche_a_io.json         # A-Tranche
├── test_07_tranche_b_mixed.json      # B-Tranche (mixed)
├── test_08_preferred_minimal.json    # Minimal data
├── test_09_senior_minimal.json       # Minimal data
├── test_10_mezz_fees_only.json       # Fees only
│
├── test_manifest.json                 # Test index
├── test_results.json                  # Latest results
└── README.md                          # Test documentation
```

### Test Scripts
Located in `regression_tests/scripts/`:
- **quick_discover_loans.py**: Discover loan candidates from Salesforce
- **create_regression_tests.py**: Generate test JSON files
- **test_candidates.json**: Cached loan metadata

## Azure Functions Files

### Deployable
- **functionapp.py** (9.4KB): HTTP endpoints wrapper
- **requirements.txt**: Python dependencies
- **host.json**: Azure Functions configuration
- **.funcignore**: Exclusions (archive, tests, .md files)

### Local Only
- **local.settings.json**: Local development settings
- **test_functionapp.py**: Integration tests

## Documentation

| File | Purpose |
|------|---------|
| **README.md** | Main documentation with deployment guide |
| **QUICKSTART.md** | Quick reference for common tasks |
| **REGRESSION_TESTS_SUMMARY.md** | Comprehensive test suite overview |
| **PROJECT_STRUCTURE.md** | This file - project organization |

## Archive (`archive/`)

**Purpose**: Old files kept for reference
**Deployed**: ❌ No

Contains:
- Old README files
- example_usage.py
- test_fetcher.py
- test results JSON

## Deployment Exclusions

Files excluded from Azure deployment (via `.funcignore`):
- `archive/` - Old files
- `regression_tests/` - Test suite
- `.git*` - Git files
- `*.md` - Documentation
- `__pycache__/` - Python cache
- `.venv/`, `venv/` - Virtual environments

## What Gets Deployed to Azure

```
Azure Functions Deployment:
├── core/                      # ✅ Business logic
│   ├── salesforce_fetcher.py
│   ├── json_driven_validator.py
│   ├── validation_rules.json
│   ├── config.py
│   └── reference code/
│
├── functionapp.py             # ✅ HTTP endpoints
├── requirements.txt           # ✅ Dependencies
└── host.json                  # ✅ Configuration
```

Total deployment size: ~60KB Python code + dependencies

## What Stays Local

```
Local Development Only:
├── regression_tests/          # ❌ Test suite
├── archive/                   # ❌ Old files
├── *.md                       # ❌ Documentation
├── test_functionapp.py        # ❌ Tests
├── run_regression_tests.py    # ❌ Test runner
├── local.settings.json        # ❌ Local config
└── .venv/                     # ❌ Virtual env
```

## File Size Summary

### Core Module (Deployed)
- `salesforce_fetcher.py`: 22.9 KB
- `json_driven_validator.py`: 21.1 KB
- `validation_rules.json`: 6.0 KB
- `config.py`: 0.4 KB
- **Total**: ~50 KB

### Function App (Deployed)
- `functionapp.py`: 9.4 KB
- `host.json`: 0.4 KB
- **Total**: ~10 KB

### Tests (Not Deployed)
- 10 test JSON files: ~15 KB
- Test scripts: ~10 KB
- Test results: ~2 KB
- **Total**: ~27 KB

### Documentation (Not Deployed)
- README files: ~20 KB

## Usage Patterns

### Local Development
```bash
# Validate directly
python -m core.json_driven_validator <loan_id>

# Run integration test
python test_functionapp.py

# Run regression tests
python run_regression_tests.py
```

### Creating Tests
```bash
# Discover loans
python regression_tests/scripts/quick_discover_loans.py

# Create test files
python regression_tests/scripts/create_regression_tests.py

# Run tests
python run_regression_tests.py
```

### Azure Deployment
```bash
# Deploy to Azure
func azure functionapp publish <app-name>

# Only deploys:
# - core/
# - functionapp.py
# - requirements.txt
# - host.json
```

## Design Principles

### 1. Separation of Concerns
- **core/**: Business logic only
- **functionapp.py**: HTTP wrapper only
- **regression_tests/**: Testing only

### 2. Deploy Only What's Needed
- Core logic goes to Azure
- Tests stay local
- Documentation stays local

### 3. Easy to Test
- Core can be tested directly
- Integration tests in test_functionapp.py
- Regression tests in regression_tests/

### 4. Clean Root Directory
- Only essential files in root
- Scripts in appropriate subfolders
- Old files in archive/

### 5. Self-Documenting
- README files at each level
- Clear folder names
- Comprehensive documentation

## Key Benefits

1. **Clean Structure**: Everything in logical locations
2. **Fast Deployment**: Only ~60KB of code deployed
3. **Easy Testing**: Comprehensive test suite included
4. **Good Documentation**: Multiple README files
5. **Portable Core**: Core logic can be used anywhere

## Quick Navigation

| Want to... | Go to... |
|------------|----------|
| Understand the project | [README.md](README.md) |
| Quick reference | [QUICKSTART.md](QUICKSTART.md) |
| Run tests | [regression_tests/README.md](regression_tests/README.md) |
| See test results | [REGRESSION_TESTS_SUMMARY.md](REGRESSION_TESTS_SUMMARY.md) |
| Deploy to Azure | [README.md](README.md#azure-deployment) |
| Create new tests | [regression_tests/scripts/](regression_tests/scripts/) |
| Modify validation | [core/validation_rules.json](core/validation_rules.json) |
| Add API endpoints | [functionapp.py](functionapp.py) |
