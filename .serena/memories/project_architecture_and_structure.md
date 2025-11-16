# Hikyuu-Qlib Project Architecture and Structure

## Project Overview
A quantitative trading platform combining Hikyuu (data) and Qlib (ML) using DDD + Hexagonal Architecture.

## Architecture Pattern
- **Design Pattern**: Domain-Driven Design (DDD) + Hexagonal Architecture
- **Language**: Python 3.11+
- **Core Frameworks**: Hikyuu (market data), Qlib (machine learning)
- **Database**: SQLite (model metadata)
- **Testing**: pytest with 707 tests

## Directory Structure
```
src/
├── domain/              # Core domain layer (entities, value objects, ports)
│   ├── entities/        # Stock, Model, Prediction, Portfolio, etc.
│   ├── value_objects/   # StockCode, Market, DateRange, KLineType, etc.
│   ├── ports/          # Interfaces: IDataProvider, IModelTrainer, IBacktestEngine
│   ├── services/       # Domain services
│   └── events/         # Domain events
├── use_cases/          # Application layer (business workflows)
│   ├── data/           # Data loading use cases
│   ├── model/          # Model training use cases
│   ├── backtest/       # Backtest execution
│   ├── portfolio/      # Portfolio management
│   └── signals/        # Signal generation
├── adapters/           # Adapter layer (framework integrations)
│   ├── hikyuu/         # Hikyuu data and backtest adapters
│   ├── qlib/           # Qlib model training adapters
│   ├── converters/     # Signal conversion
│   └── repositories/   # Data persistence (SQLite, YAML)
├── controllers/        # Interface layer
│   └── cli/           # Command-line interface
├── infrastructure/     # Infrastructure (config, logging, DI)
└── utils/             # Utility functions
```

## Key Components

### Domain Layer (Zero Dependencies)
- **Entities**: Stock, Model, Prediction, Portfolio, Backtest, TradingSignal
- **Value Objects**: StockCode, Market, DateRange, KLineType, Configuration
- **Ports**: Define interfaces for external dependencies

### Use Cases Layer
- Data loading and management
- Model training (LGBM, MLP, LSTM, GRU, Transformer)
- Batch training for index constituents
- Prediction generation
- Backtest execution
- Signal conversion

### Adapters Layer
- **Hikyuu Adapters**: Data loading, backtest engine, signal indicators
- **Qlib Adapters**: Model training, predictions
- **Repositories**: SQLite (models), YAML (configuration)

### CLI Controllers
- Data commands: load, list
- Model commands: train, list, delete, train-index
- Backtest commands: run
- Config commands: init, validate

## Code Quality Metrics
- **Total Tests**: 707 (good coverage)
- **Complexity Issues**: 42 (17 too many args, 9 complex structures)
- **Documentation Issues**: ~200 missing docstrings
- **Type Hints**: ~100 missing annotations
- **Code Style**: 11,667 total linting issues (mostly auto-fixable formatting)

## Technology Stack
- Python 3.11+
- Hikyuu (C++ binding for market data)
- Qlib (Microsoft quantitative investment platform)
- LightGBM, scikit-learn (ML models)
- SQLite (metadata storage)
- pytest (testing)
- click (CLI framework)
- pandas, numpy (data processing)
