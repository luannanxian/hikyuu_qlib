# Hikyuu × Qlib CLI User Guide

## Installation

The CLI is part of the Hikyuu × Qlib Trading Platform. No additional installation is required beyond the main project dependencies.

## Quick Start

### View Available Commands
```bash
python -m controllers.cli.main --help
```

### Get Version
```bash
python -m controllers.cli.main --version
```

## Commands

### 1. Data Management

#### Load Stock Data
```bash
# Load single stock
python -m controllers.cli.main data load \
  --code sh600000 \
  --start 2023-01-01 \
  --end 2023-12-31

# Load with different K-line type
python -m controllers.cli.main data load \
  --code sz000001 \
  --start 2023-01-01 \
  --end 2023-12-31 \
  --kline-type WEEK
```

**Options**:
- `--code`: Stock code (format: sh/sz + 6 digits)
- `--start`: Start date (YYYY-MM-DD)
- `--end`: End date (YYYY-MM-DD)
- `--kline-type`: K-line type (DAY, WEEK, MONTH, MIN5, MIN15, MIN30, MIN60)

#### List Available Data
```bash
# List all data
python -m controllers.cli.main data list

# Filter by market
python -m controllers.cli.main data list --market sh

# Verbose output
python -m controllers.cli.main data list --verbose
```

### 2. Model Management

#### Train a Model
```bash
# Basic training
python -m controllers.cli.main model train \
  --type LGBM \
  --name my_first_model

# With configuration file
python -m controllers.cli.main model train \
  --type LGBM \
  --name my_model \
  --config config.yaml
```

**Model Types**:
- LGBM (LightGBM)
- MLP (Multi-Layer Perceptron)
- LSTM (Long Short-Term Memory)
- GRU (Gated Recurrent Unit)
- TRANSFORMER

#### List Models
```bash
# List all models
python -m controllers.cli.main model list

# Filter by status
python -m controllers.cli.main model list --status TRAINED

# Verbose output
python -m controllers.cli.main model list --verbose
```

#### Delete a Model
```bash
# With confirmation prompt
python -m controllers.cli.main model delete <model-id>

# Force deletion (no prompt)
python -m controllers.cli.main model delete <model-id> --force
```

### 3. Configuration

#### Show Configuration
```bash
# Show all configuration
python -m controllers.cli.main config show

# Show specific section
python -m controllers.cli.main config show --section data
python -m controllers.cli.main config show --section model
python -m controllers.cli.main config show --section backtest
```

#### Update Configuration
```bash
# Set a configuration value
python -m controllers.cli.main config set \
  --key HIKYUU_DATA_PATH \
  --value /path/to/data

# Set numeric value
python -m controllers.cli.main config set \
  --key INITIAL_CAPITAL \
  --value 200000
```

**Note**: Configuration changes made via CLI are not persistent. To make permanent changes, edit the `.env` file or set environment variables.

## Error Handling

The CLI provides clear error messages:

### Invalid Stock Code
```bash
python -m controllers.cli.main data load --code invalid ...
# Error: Invalid stock code format: invalid
```

### Invalid Date Format
```bash
python -m controllers.cli.main data load --code sh600000 --start 2023/01/01 ...
# Error: Invalid date format: 2023/01/01. Expected format: YYYY-MM-DD
```

### Missing Required Arguments
```bash
python -m controllers.cli.main data load
# Error: Missing option '--code'
```

## Output Formatting

The CLI uses Rich formatting for beautiful output:

- ✓ Green checkmark for success
- ✗ Red cross for errors
- ⚠ Yellow warning for warnings
- ℹ Blue info for information
- Tables with colored status indicators
- Progress bars for long operations (coming soon)

## Configuration

### Environment Variables

Set these in a `.env` file or as environment variables:

```bash
# Data sources
HIKYUU_DATA_PATH=./data/hikyuu
QLIB_DATA_PATH=./data/qlib

# Model settings
MODEL_STORAGE_PATH=./models
DEFAULT_MODEL_TYPE=LGBM

# Backtest settings
INITIAL_CAPITAL=100000
COMMISSION_RATE=0.0003

# Application settings
LOG_LEVEL=INFO
ENVIRONMENT=dev
```

## Advanced Usage

### Chaining Commands
```bash
# Load data and then train model
python -m controllers.cli.main data load --code sh600000 --start 2023-01-01 --end 2023-12-31 && \
python -m controllers.cli.main model train --type LGBM --name model_600000
```

### Using with Scripts
```python
import subprocess

# Load data programmatically
subprocess.run([
    "python", "-m", "controllers.cli.main",
    "data", "load",
    "--code", "sh600000",
    "--start", "2023-01-01",
    "--end", "2023-12-31"
])
```

## Troubleshooting

### Command Not Found
If you get "command not found", make sure you're in the project root directory and have activated the correct Python environment.

### Import Errors
Ensure all dependencies are installed:
```bash
pip install click rich
```

### Database Errors
If you encounter database errors, check that the database path in configuration is correct and writable.

## Getting Help

For any command, use `--help`:
```bash
python -m controllers.cli.main --help
python -m controllers.cli.main data --help
python -m controllers.cli.main model train --help
```

## Examples

### Complete Workflow Example
```bash
# 1. Check configuration
python -m controllers.cli.main config show

# 2. Load stock data
python -m controllers.cli.main data load \
  --code sh600000 \
  --start 2020-01-01 \
  --end 2023-12-31

# 3. Train a model
python -m controllers.cli.main model train \
  --type LGBM \
  --name production_model

# 4. List trained models
python -m controllers.cli.main model list --status TRAINED
```

## Support

For issues or questions, please refer to the main project documentation or create an issue in the project repository.

---

**Version**: 0.1.0
**Last Updated**: 2025-01-12
