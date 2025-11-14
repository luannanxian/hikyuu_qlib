# Quick Reference: CustomSG_QlibFactor

## Import
```python
from adapters.hikyuu import CustomSG_QlibFactor
```

## Basic Usage
```python
sg = CustomSG_QlibFactor(
    pred_pkl_path="output/LGBM/pred.pkl",
    buy_threshold=0.02,
    sell_threshold=-0.02,
    top_k=10
)
```

## Hikyuu Integration
```python
from hikyuu import *

sys = SYS_Simple(
    tm=crtTM(init_cash=100000),
    sg=sg,
    mm=MM_FixedCount(100)
)
sys.run(sm['sz000001'], Query(-100))
```

## Domain Interface
```python
signal_batch = sg.generate_signals_from_predictions(prediction_batch)
signal = sg.get_signal_for_stock(StockCode("sh600000"), datetime(2018, 9, 21))
top_stocks = sg.get_top_k_stocks(prediction_batch, k=10)
```

## Run Tests
```bash
pytest tests/unit/adapters/hikyuu/test_custom_sg_qlib_factor.py -v
```

## Run Examples
```bash
python examples/signal_conversion/example_custom_sg_qlib_factor.py
```

## Files
- Implementation: `src/adapters/hikyuu/custom_sg_qlib_factor.py`
- Tests: `tests/unit/adapters/hikyuu/test_custom_sg_qlib_factor.py`
- Examples: `examples/signal_conversion/example_custom_sg_qlib_factor.py`
- Docs: `docs/adapters/CUSTOM_SG_QLIB_FACTOR.md`

## Test Results
30/30 tests passing ✅
