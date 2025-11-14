# CustomSG_QlibFactor Adapter

## Overview

`CustomSG_QlibFactor` is a production-ready adapter that bridges Qlib machine learning predictions with Hikyuu's trading signal system. It implements both Hikyuu's `SignalBase` interface and the domain layer's `ISignalProvider` port, enabling seamless integration between the two frameworks.

## Features

- **Dual Interface Implementation**: Works with both Hikyuu backtesting and domain-driven design patterns
- **Time Alignment**: Handles timestamp conversion between pandas and Hikyuu formats
- **Top-K Selection**: Supports advanced stock selection strategies
- **Threshold-Based Signals**: Generates buy/sell signals based on configurable thresholds
- **Signal Strength**: Calculates signal strength (WEAK/MEDIUM/STRONG) based on prediction confidence
- **Performance Optimized**: Pre-calculates Top-K stocks for efficient signal generation

## Installation

The adapter is part of the `hikyuu_qlib` project. Ensure you have the required dependencies:

```bash
pip install pandas hikyuu  # Hikyuu optional for pure domain usage
```

## Quick Start

### Basic Usage with Hikyuu

```python
from adapters.hikyuu import CustomSG_QlibFactor
from hikyuu import *

# Initialize Hikyuu
load_hikyuu()

# Create signal provider
sg = CustomSG_QlibFactor(
    pred_pkl_path="output/LGBM/pred.pkl",
    buy_threshold=0.02,
    sell_threshold=-0.02,
    top_k=10,
    name="SG_QlibFactor"
)

# Use in trading system
tm = crtTM(init_cash=100000)
mm = MM_FixedCount(100)
sys = SYS_Simple(tm=tm, sg=sg, mm=mm)

# Run backtest
stock = sm['sz000001']
sys.run(stock, Query(-100))
```

### Domain Interface Usage

```python
from adapters.hikyuu import CustomSG_QlibFactor
from domain.entities.prediction import Prediction, PredictionBatch
from domain.value_objects.stock_code import StockCode
from datetime import datetime

# Create signal provider
sg = CustomSG_QlibFactor(
    pred_pkl_path="output/LGBM/pred.pkl",
    buy_threshold=0.02,
    sell_threshold=-0.02,
    top_k=10
)

# Create prediction batch
batch = PredictionBatch(model_id="LGBM_Model")
batch.add_prediction(Prediction(
    stock_code=StockCode("sh600000"),
    timestamp=datetime(2018, 9, 21),
    predicted_value=0.05,
    model_id="LGBM_Model"
))

# Generate signals
signal_batch = sg.generate_signals_from_predictions(batch)

# Query specific signal
signal = sg.get_signal_for_stock(
    StockCode("sh600000"),
    datetime(2018, 9, 21)
)
```

## API Reference

### Constructor Parameters

```python
CustomSG_QlibFactor(
    pred_pkl_path: str,
    buy_threshold: float = 0.02,
    sell_threshold: float = -0.02,
    top_k: Optional[int] = None,
    name: str = "SG_QlibFactor"
)
```

**Parameters:**

- `pred_pkl_path` (str): Path to Qlib prediction file (pred.pkl)
- `buy_threshold` (float): Buy signal threshold (default: 0.02)
  - Generates BUY signal when prediction > buy_threshold
- `sell_threshold` (float): Sell signal threshold (default: -0.02)
  - Generates SELL signal when prediction < sell_threshold
- `top_k` (Optional[int]): Top-K stock selection (default: None)
  - If set, only top K stocks by prediction value get buy signals
  - Sell signals are generated regardless of Top-K
- `name` (str): Signal indicator name (default: "SG_QlibFactor")

### ISignalProvider Interface Methods

#### generate_signals_from_predictions

```python
def generate_signals_from_predictions(
    self,
    prediction_batch: PredictionBatch,
    buy_threshold: float = 0.02,
    sell_threshold: float = -0.02,
    top_k: Optional[int] = None,
) -> SignalBatch:
```

Generates trading signals from prediction batch.

**Returns:**
- `SignalBatch`: Batch of trading signals with type, strength, and reason

**Signal Strength Logic:**
- STRONG: prediction > threshold * 2
- MEDIUM: prediction > threshold * 1.5
- WEAK: prediction > threshold

#### get_signal_for_stock

```python
def get_signal_for_stock(
    self,
    stock_code: StockCode,
    signal_date: datetime,
) -> Optional[TradingSignal]:
```

Retrieves signal for specific stock on specific date.

**Returns:**
- `TradingSignal` or `None` if not found

#### get_top_k_stocks

```python
def get_top_k_stocks(
    self,
    prediction_batch: PredictionBatch,
    k: int,
) -> List[StockCode]:
```

Selects top K stocks by prediction value.

**Returns:**
- List of `StockCode` in descending order by prediction value

### Hikyuu SignalBase Methods

The adapter overrides the following Hikyuu methods:

- `_calculate(kdata)`: Core signal calculation logic
- `_reset()`: Reset internal state
- `_clone()`: Create a copy of the signal indicator

## Prediction File Format

The `pred.pkl` file must be a pandas DataFrame with:

**Index:**
- MultiIndex with 2 levels:
  - Level 0: datetime (pandas Timestamp)
  - Level 1: instrument (str, e.g., "SH600000")

**Columns:**
- `score`: Prediction value (primary)
- Alternative names: `score_0`, `pred`, `prediction`

**Example:**

```python
import pandas as pd

# Create sample predictions
dates = pd.date_range('2018-09-21', periods=5)
instruments = ['SH600000', 'SZ000001', 'SH600519']

index = pd.MultiIndex.from_product(
    [dates, instruments],
    names=['datetime', 'instrument']
)

pred_df = pd.DataFrame({
    'score': [0.05, 0.03, -0.02, 0.04, 0.01, ...]
}, index=index)

pred_df.to_pickle('pred.pkl')
```

## Stock Code Format

The adapter handles stock code normalization:

- **Qlib format**: Uppercase with market (e.g., "SH600000", "SZ000001")
- **Hikyuu format**: May be lowercase (e.g., "sh600000")
- **Domain format**: `StockCode` value object (e.g., StockCode("sh600000"))

Conversion is handled automatically.

## Time Alignment

The adapter performs day-level time alignment:

1. Qlib predictions are typically daily (00:00:00)
2. Hikyuu KData can be intraday (minute-level)
3. Alignment: `pd_datetime.normalize()` matches only date part

**Example:**

```
Hikyuu KData: 2018-09-21 09:30:00  ─┐
                                     ├─> Matched to: 2018-09-21 00:00:00
Qlib Prediction: 2018-09-21 00:00:00 ┘
```

## Signal Generation Logic

### Basic Threshold Strategy

```python
if prediction_value > buy_threshold:
    signal = BUY
elif prediction_value < sell_threshold:
    signal = SELL
else:
    signal = HOLD
```

### Top-K Strategy

When `top_k` is set:

1. For each date, predictions are sorted by value
2. Top K stocks are selected
3. Only Top-K stocks can generate BUY signals
4. All stocks can generate SELL signals (no Top-K filtering)

**Example:**

```python
# 5 stocks with predictions: 0.08, 0.05, 0.03, -0.01, -0.05
# top_k = 2

# Stock 1 (0.08): In Top-2 → BUY signal
# Stock 2 (0.05): In Top-2 → BUY signal
# Stock 3 (0.03): Not in Top-2 → HOLD (no BUY)
# Stock 4 (-0.01): HOLD
# Stock 5 (-0.05): SELL signal (always generated)
```

## Performance Optimization

The adapter implements several optimizations:

1. **Lazy Loading**: Predictions loaded only on first use
2. **Pre-computation**: Top-K stocks calculated once during load
3. **Dictionary Lookup**: O(1) stock prediction retrieval
4. **Date Normalization**: Day-level grouping reduces comparisons

## Error Handling

The adapter validates inputs and provides clear error messages:

```python
# File not found
FileNotFoundError: Prediction file not found: /path/to/pred.pkl

# Invalid format
ValueError: pred.pkl must have MultiIndex(datetime, instrument)

# Missing score column
ValueError: Score column not found in pred.pkl. Available columns: ['label', 'feature1']

# Invalid stock code
ValueError: Invalid stock code: INVALID. Expected format: [sh|sz|bj]XXXXXX
```

## Testing

Comprehensive unit tests cover:

- Time conversion (Hikyuu ↔ pandas)
- Prediction loading and validation
- Top-K calculation
- Signal generation logic
- Edge cases (empty predictions, missing stocks)

Run tests:

```bash
pytest tests/unit/adapters/hikyuu/test_custom_sg_qlib_factor.py -v
```

## Examples

See `examples/signal_conversion/example_custom_sg_qlib_factor.py` for comprehensive usage examples:

1. Basic usage with pred.pkl
2. Hikyuu backtest integration
3. Domain interface usage
4. Top-K stock selection
5. Query specific signals
6. Parameter tuning

Run examples:

```bash
python examples/signal_conversion/example_custom_sg_qlib_factor.py
```

## Best Practices

### 1. Threshold Selection

```python
# Conservative (fewer signals, higher confidence)
sg = CustomSG_QlibFactor(
    pred_pkl_path="pred.pkl",
    buy_threshold=0.05,
    sell_threshold=-0.05
)

# Aggressive (more signals, lower confidence)
sg = CustomSG_QlibFactor(
    pred_pkl_path="pred.pkl",
    buy_threshold=0.01,
    sell_threshold=-0.01
)
```

### 2. Top-K Selection

```python
# Focus on top performers only
sg = CustomSG_QlibFactor(
    pred_pkl_path="pred.pkl",
    top_k=10  # Only top 10 stocks daily
)

# No filtering (all stocks)
sg = CustomSG_QlibFactor(
    pred_pkl_path="pred.pkl",
    top_k=None  # All stocks with prediction > threshold
)
```

### 3. Signal Strength Usage

```python
signal_batch = sg.generate_signals_from_predictions(batch)

# Only act on strong signals
strong_signals = signal_batch.filter_by_strength(SignalStrength.STRONG)

# Combine type and strength
strong_buys = [
    s for s in signal_batch.signals
    if s.signal_type == SignalType.BUY
    and s.signal_strength == SignalStrength.STRONG
]
```

### 4. Backtesting Integration

```python
# Use with Hikyuu's trading system
sys = SYS_Simple(
    tm=crtTM(init_cash=100000),
    sg=CustomSG_QlibFactor(
        pred_pkl_path="pred.pkl",
        buy_threshold=0.02,
        top_k=10
    ),
    mm=MM_FixedCount(100),
    st=ST_FixedPercent(0.03),  # Stop loss at -3%
    tp=TP_FixedPercent(0.10)   # Take profit at +10%
)
```

## Troubleshooting

### Issue: No signals generated

**Possible causes:**
1. Stock not in Top-K selection
2. No predictions for date range
3. Predictions below threshold

**Solution:**
```python
# Check if stock has predictions
sg._load_predictions()
if "SH600000" in sg._stock_predictions:
    print(sg._stock_predictions["SH600000"])
else:
    print("No predictions for SH600000")

# Adjust thresholds
sg.setParam("buy_threshold", 0.01)  # Lower threshold
```

### Issue: Time alignment mismatch

**Problem:** Hikyuu KData times don't match Qlib prediction times

**Solution:** The adapter normalizes to date-level automatically. Ensure:
1. Qlib predictions are date-indexed (not intraday)
2. Hikyuu KData includes the prediction dates

### Issue: Stock code format error

**Problem:** Stock codes not matching between Qlib and Hikyuu

**Solution:** The adapter normalizes automatically, but verify:
- Qlib uses uppercase: "SH600000"
- Domain uses lowercase: StockCode("sh600000")
- Both formats work with the adapter

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Qlib Predictions                      │
│                      (pred.pkl)                          │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│              CustomSG_QlibFactor Adapter                 │
│  ┌─────────────────────────────────────────────────┐   │
│  │  SignalBase (Hikyuu)   │  ISignalProvider (DDD) │   │
│  ├─────────────────────────────────────────────────┤   │
│  │  - _calculate()         │  - generate_signals()  │   │
│  │  - _addBuySignal()      │  - get_signal()        │   │
│  │  - _addSellSignal()     │  - get_top_k_stocks()  │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
              │                           │
              ▼                           ▼
    ┌──────────────────┐      ┌──────────────────┐
    │ Hikyuu Backtester│      │  Domain Services  │
    │ (SYS_Simple)     │      │  (SignalBatch)    │
    └──────────────────┘      └──────────────────┘
```

## Related Documentation

- [SIGNAL_CONVERSION_SOLUTION.md](../../docs/integration/SIGNAL_CONVERSION_SOLUTION.md): Technical design
- [ISignalProvider](../../src/domain/ports/signal_provider.py): Port interface
- [Prediction Entity](../../src/domain/entities/prediction.py): Domain model
- [TradingSignal Entity](../../src/domain/entities/trading_signal.py): Signal model

## Contributing

When extending the adapter:

1. Maintain backward compatibility with both interfaces
2. Add comprehensive unit tests
3. Update documentation
4. Follow DDD principles for domain integration
5. Optimize for performance (pre-computation, caching)

## License

Part of the hikyuu_qlib project. See project LICENSE file.

## Support

For issues or questions:
1. Check [troubleshooting](#troubleshooting) section
2. Review [examples](../../examples/signal_conversion/)
3. Run tests to verify setup
4. Check technical design document for details

---

**Version**: 1.0.0
**Last Updated**: 2025-11-14
**Author**: Claude Code + User Collaboration
