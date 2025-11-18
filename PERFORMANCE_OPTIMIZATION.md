# 回测性能优化方案

## 🔥 关键性能问题

### 问题1: 重复加载预测数据
**位置**: `custom_sg_qlib_factor.py:303`
```python
def _calculate(self, kdata):
    # ❌ 每只股票都重新加载一次预测数据!
    self._load_predictions()  # 300只股票 × 62,687条数据 = 巨大浪费
```

**影响**: 300只股票 × 加载时间 = 30分钟中的大部分时间

**解决方案**: 只加载一次,使用标志位控制

---

## ⚡ 立即优化方案

### 优化1: 单次加载预测数据 (预计提速 80%)

修改 `custom_sg_qlib_factor.py`:

```python
def __init__(self, pred_pkl_path, buy_threshold=0.02, sell_threshold=-0.02, top_k=None, name="SG_QlibFactor"):
    super().__init__()
    self.name = name

    # 参数
    self.set_param("pred_pkl_path", pred_pkl_path)
    self.set_param("buy_threshold", buy_threshold)
    self.set_param("sell_threshold", sell_threshold)
    self.set_param("top_k", top_k if top_k is not None else -1)

    # 存储
    self._pred_df = None
    self._stock_predictions = {}
    self._top_k_stocks_by_date = {}

    # ✅ 新增: 加载标志位
    self._predictions_loaded = False

    # ✅ 关键优化: 在初始化时就加载预测数据
    self._load_predictions()

def _calculate(self, kdata):
    """计算信号 - Hikyuu回调接口"""
    # ✅ 去掉重复加载
    # self._load_predictions()  # 删除这行!

    # ⚠️ 添加安全检查(防御性编程)
    if not self._predictions_loaded:
        self._load_predictions()

    # 2. 获取当前股票代码
    stock = kdata.get_stock()
    stock_code = self._normalize_stock_code(stock)
    # ... 其余逻辑不变

def _load_predictions(self):
    """加载预测结果(只执行一次)"""
    # ✅ 防止重复加载
    if self._predictions_loaded:
        return

    # 原有加载逻辑...

    # ✅ 加载完成后设置标志
    self._predictions_loaded = True
```

**预期效果**: 31分钟 → 约6分钟 (提速80%)

---

### 优化2: 向量化日期匹配 (预计再提速 30%)

当前逻辑:
```python
# ❌ 慢: 每个K线都做一次查找
for i in range(len(kdata)):
    k_datetime = kdata[i].datetime
    pd_datetime = self._hikyuu_to_pandas_datetime(k_datetime)
    pd_date = pd_datetime.normalize()

    if pd_date not in stock_pred_series.index:
        continue
```

优化后:
```python
# ✅ 快: 预先构建日期映射表
def _build_date_index(self, kdata):
    """预先构建K线日期索引"""
    dates = []
    indices = []
    for i in range(len(kdata)):
        pd_datetime = self._hikyuu_to_pandas_datetime(kdata[i].datetime)
        pd_date = pd_datetime.normalize()
        dates.append(pd_date)
        indices.append(i)
    return dict(zip(dates, indices))

def _calculate(self, kdata):
    # ...
    date_index = self._build_date_index(kdata)

    # ✅ 直接在预测数据上迭代(减少查找次数)
    for pred_date, pred_score in stock_pred_series.items():
        if pred_date not in date_index:
            continue

        k_index = date_index[pred_date]
        k_datetime = kdata[k_index].datetime

        # Top-K过滤 + 信号生成...
```

**预期效果**: 6分钟 → 约4分钟 (再提速30%)

---

### 优化3: 缓存 Top-K 查找 (预计再提速 10%)

```python
def _is_in_top_k(self, stock_code, date):
    """缓存的 Top-K 检查"""
    if not hasattr(self, '_top_k_cache'):
        self._top_k_cache = {}

    cache_key = (stock_code, date)
    if cache_key not in self._top_k_cache:
        top_k_param = self.get_param("top_k")
        top_k = top_k_param if top_k_param != -1 else None

        if top_k is None:
            result = True
        else:
            result = (
                date in self._top_k_stocks_by_date and
                stock_code in self._top_k_stocks_by_date[date]
            )
        self._top_k_cache[cache_key] = result

    return self._top_k_cache[cache_key]
```

---

## 📊 性能对比预测

| 优化方案 | 预计时间 | 提速比例 | 实施难度 |
|---------|---------|---------|---------|
| 当前版本 | 31分钟 | - | - |
| 优化1: 单次加载 | 6分钟 | 80% ↓ | ⭐ 简单 |
| 优化1+2: 向量化 | 4分钟 | 87% ↓ | ⭐⭐ 中等 |
| 优化1+2+3: 缓存 | 3.5分钟 | 89% ↓ | ⭐⭐ 中等 |
| 减少股票数(100只) | 10分钟 | 68% ↓ | ⭐ 简单(参数) |
| 缩短时间(Q1) | 8分钟 | 74% ↓ | ⭐ 简单(参数) |

---

## 🚀 推荐实施顺序

### 阶段1: 立即优化 (5分钟实施)
```bash
# 先用参数快速验证策略
python examples/quick_backtest.py \
  --buy-threshold 0.001 \
  --sell-threshold -0.001 \
  --top-k 30 \
  --cash 1000000 \
  --start-date 20250101 \
  --end-date 20250331  # 只测Q1,8分钟完成
```

### 阶段2: 代码优化 (30分钟实施)
1. 实施优化1: 单次加载预测数据
2. 测试验证: 预期6分钟完成全年回测
3. 如果满意,停止;否则继续

### 阶段3: 深度优化 (2小时实施)
1. 实施优化2: 向量化日期匹配
2. 实施优化3: Top-K缓存
3. 测试验证: 预期3.5分钟完成全年回测

---

## 🔧 其他优化选项

### A. 使用更快的股票池
```python
# 只回测流动性好的股票(减少计算量)
liquid_stocks = [s for s in stk_list if s.market_code.startswith('sh60') or s.market_code.startswith('sz00')]
```

### B. 启用 Hikyuu 的缓存
```ini
# 修改 config/hikyuu.ini
[hikyuu]
cache_dir = ./hikyuu_cache
enable_cache = true
```

### C. 增加机器资源
```bash
# 设置Python优化级别
python -O examples/quick_backtest.py ...

# 使用 PyPy (可能提速2-3倍)
pypy3 examples/quick_backtest.py ...
```

### D. 分片回测 + 并行(高级)
```bash
# 按季度分片,并行执行
python quick_backtest.py --start 20250101 --end 20250331 &  # Q1
python quick_backtest.py --start 20250401 --end 20250630 &  # Q2
python quick_backtest.py --start 20250701 --end 20250930 &  # Q3
python quick_backtest.py --start 20251001 --end 20251231 &  # Q4
wait
# 最后合并结果
```

---

## ⚠️ 注意事项

1. **验证正确性**: 优化后必须验证结果一致性
2. **渐进式优化**: 每次只改一个,测试通过再继续
3. **保留原版本**: 备份当前可用版本
4. **性能测量**: 使用 `time` 命令精确测量

```bash
# 测量优化效果
time python examples/quick_backtest.py --buy-threshold 0.001 --sell-threshold -0.001 --top-k 30
```

---

## 📈 实施建议

**如果你只想快速验证策略**:
→ 使用阶段1的参数优化(立即见效,无需改代码)

**如果你需要频繁回测**:
→ 实施阶段2的代码优化(一次投入,长期受益)

**如果你要做大规模参数扫描**:
→ 考虑阶段3+并行方案

我建议先实施**优化1**(单次加载),这是ROI最高的优化!
