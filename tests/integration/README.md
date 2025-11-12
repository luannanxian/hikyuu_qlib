# Integration Tests - Phase 6

## Overview

This directory contains **59 integration tests** that verify the end-to-end functionality of the Hikyuu × Qlib quantitative trading platform. The tests validate the interaction between different layers of the application (Domain, Use Cases, Adapters, Infrastructure, and Controllers).

## Test Structure

```
tests/integration/
├── __init__.py
├── conftest.py                             # Shared fixtures and test data factories
├── test_data_workflow.py                   # Data loading workflow (9 tests)
├── test_model_workflow.py                  # Model training workflow (9 tests)
├── test_backtest_workflow.py               # Backtest workflow (10 tests)
├── test_end_to_end.py                      # End-to-end scenarios (8 tests)
├── test_configuration_integration.py       # Configuration management (10 tests)
├── test_error_handling_integration.py      # Error propagation (13 tests)
└── README.md                               # This file
```

## Test Categories

### 1. Data Workflow Tests (test_data_workflow.py)
Tests the complete data loading flow from adapters through use cases to domain entities.

**Key scenarios:**
- Loading stock data with validation
- Handling empty results
- Data quality validation
- Provider error handling
- Multiple stock loading
- Different K-line types
- Performance testing
- Caching behavior

**Status:** ✅ 9/9 tests passing

### 2. Model Workflow Tests (test_model_workflow.py)
Tests the complete model training flow including persistence and state transitions.

**Key scenarios:**
- Model training integration
- Training multiple models
- Metrics validation
- Error handling
- Repository persistence
- Hyperparameter tuning
- Insufficient data handling
- State transitions

**Status:** ⚠️ Partially complete (needs fixture adjustments)

### 3. Backtest Workflow Tests (test_backtest_workflow.py)
Tests the complete backtesting flow with various configurations and signals.

**Key scenarios:**
- Basic backtest execution
- Buy/sell signal handling
- Empty signal handling
- Performance metrics calculation
- Commission and slippage
- Date range filtering
- Error handling
- Different capital amounts

**Status:** ⚠️ Partially complete (needs import fixes)

### 4. End-to-End Tests (test_end_to_end.py)
Tests complete trading workflows from data loading through backtesting.

**Key scenarios:**
- Complete trading workflow
- Multi-stock trading
- Model retraining
- Strategy comparison
- Incremental prediction
- Error recovery
- Full validation workflow
- Performance tracking

**Status:** ⚠️ Partially complete (needs use case parameter adjustments)

### 5. Configuration Integration Tests (test_configuration_integration.py)
Tests configuration loading, validation, and usage across the system.

**Key scenarios:**
- Configuration loading
- Configuration updates
- Validation integration
- Component usage
- Different formats
- Environment overrides
- Default values
- Hot reload
- Multi-environment support
- Versioning

**Status:** ⚠️ Partially complete (needs BacktestConfig adjustment)

### 6. Error Handling Integration Tests (test_error_handling_integration.py)
Tests error propagation and handling across system layers.

**Key scenarios:**
- Data provider error propagation
- Model training error propagation
- Backtest engine error propagation
- Value object validation errors
- Domain rule violations
- Partial failure handling
- Error context preservation
- Recovery strategies
- Cascading errors
- Error logging
- Cleanup after errors
- Timeout handling

**Status:** ✅ 6/13 tests passing

## Fixtures and Test Data

### Shared Fixtures (conftest.py)

**Database Fixtures:**
- `in_memory_db`: SQLite in-memory database for testing
- `mock_model_repository`: Mocked model repository with real DB

**Configuration Fixtures:**
- `temp_config_file`: Temporary YAML config file
- `temp_config_dir`: Temporary configuration directory

**Mock Adapters:**
- `mock_stock_data_provider`: Mocked stock data provider
- `mock_model_trainer`: Mocked model trainer
- `mock_backtest_engine`: Mocked backtest engine
- `mock_signal_converter`: Signal converter adapter

**Use Case Fixtures:**
- `load_stock_data_use_case`: Complete data loading use case
- `train_model_use_case`: Complete model training use case
- `generate_predictions_use_case`: Prediction generation use case
- `convert_predictions_to_signals_use_case`: Signal conversion use case
- `run_backtest_use_case`: Backtest execution use case

**Integration Container:**
- `integration_container`: Assembled container with all use cases

**Test Data Factories:**
- `TestDataFactory`: Factory for creating test data
  - `create_kline_data()`: Generate K-line data
  - `create_trained_model()`: Generate trained models
  - `create_predictions()`: Generate predictions
  - `create_signals()`: Generate trading signals

## Running the Tests

### Run all integration tests:
```bash
pytest tests/integration/ -v
```

### Run specific test file:
```bash
pytest tests/integration/test_data_workflow.py -v
```

### Run with coverage:
```bash
pytest tests/integration/ --cov=src --cov-report=html
```

### Run specific test:
```bash
pytest tests/integration/test_data_workflow.py::test_load_stock_data_integration -v
```

## Test Performance

Expected execution times:
- Data workflow tests: < 1s
- Model workflow tests: < 2s
- Backtest workflow tests: < 2s
- End-to-end tests: < 5s
- Configuration tests: < 1s
- Error handling tests: < 2s

**Total expected time:** < 10s for all 59 tests

## Current Status

### Summary:
- **Total Tests:** 59
- **Passing:** 23 (39%)
- **Needs Adjustment:** 36 (61%)

### Next Steps:

1. **Adjust Use Case Fixtures:**
   - Fix `GeneratePredictionsUseCase` initialization (needs repository + trainer)
   - Add `strategy_params` to signal conversion calls
   - Ensure proper async/await patterns

2. **Fix BacktestConfig Usage:**
   - Ensure all required parameters are provided
   - Check for default values in configuration

3. **Complete Model Repository Integration:**
   - Fix SQLite repository initialization
   - Ensure proper database connection handling

4. **Configuration System:**
   - Add missing configuration fields
   - Implement default value fallbacks

## Integration Test Principles

### Test Independence
Each test is isolated and can run independently without affecting others.

### Real Component Integration
Tests use real implementations where possible, mocking only external dependencies (Hikyuu/Qlib frameworks).

### Mock Strategy
- ✅ **Mock:** External frameworks (Hikyuu, Qlib)
- ✅ **Mock:** File system (use tempfile)
- ✅ **Real:** Domain layer (never mock)
- ✅ **Real:** Use Cases (test real logic)
- ✅ **Real:** Infrastructure (SQLite in-memory)

### Test Data Management
All test data is created through `TestDataFactory` to ensure consistency and maintainability.

## Coverage Goals

Target coverage for integration tests:
- **Data Workflow:** 100%
- **Model Workflow:** 100%
- **Backtest Workflow:** 100%
- **End-to-End:** 90%
- **Configuration:** 90%
- **Error Handling:** 95%

## Known Issues and Improvements Needed

1. Some fixtures need parameter adjustments to match actual use case signatures
2. Configuration system needs default value support
3. Some async mock assertions need updating (assert_not_awaited vs assert_not_called)
4. Need to implement signal conversion strategy parameters

## Contributing

When adding new integration tests:

1. Follow the existing structure and naming conventions
2. Use shared fixtures from `conftest.py`
3. Use `TestDataFactory` for test data creation
4. Keep tests isolated and independent
5. Add appropriate docstrings explaining the test scenario
6. Ensure tests complete within performance targets

## Related Documentation

- `/Users/zhenkunliu/project/hikyuu_qlib/src/ARCHITECTURE.md` - System architecture
- `/Users/zhenkunliu/project/hikyuu_qlib/src/PROJECT_STATUS.md` - Project status
- `/Users/zhenkunliu/project/hikyuu_qlib/tests/unit/` - Unit tests (402 tests)

---

**Generated:** Phase 6 - Integration Testing
**Framework:** pytest + pytest-asyncio
**Python Version:** 3.11+
