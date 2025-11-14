# Hikyuu QLib 架构改进实施计划

**日期**: 2025-11-13
**版本**: 1.0
**项目状态**: Phase 1-6 完成 (91.5%), 462/462 测试通过

---

## 执行摘要

本文档基于全面的代码审查结果，提供了hikyuu_qlib量化交易平台的架构改进路线图。项目当前采用**六边形架构 + DDD + TDD**，整体质量优秀，但存在一些可以提升的空间。

### 当前状态

**优势** ✅:
- 完美的依赖方向（Domain层零外部依赖）
- 优秀的Ports & Adapters实现（7个接口）
- 丰富的领域模型（非贫血模型）
- 全面的测试覆盖（462个测试，100%通过）
- 强类型配置管理（Pydantic）

**改进机会** 🔄:
- Aggregates目录为空（聚合根在entities/目录）
- Services目录为空（业务逻辑泄露到适配器）
- Events目录为空（无领域事件实现）
- 缺少限界上下文划分
- 部分端口使用`any`和`dict`类型

---

## 审查报告摘要

### 架构审查
- **总体评分**: B+ (85/100)
- **详细报告**: [ARCHITECTURE_REVIEW_REPORT.md](./ARCHITECTURE_REVIEW_REPORT.md)
- **关键发现**: 14个架构问题，从CRITICAL到LOW级别

### 安全审计
- **风险等级**: 低-中等
- **关键发现**:
  - 0个严重问题
  - 2个高优先级问题（数据加密、未来API认证）
  - 5个中优先级问题
- **预计修复时间**: 4-6周

### 性能分析
- **详细报告**: [PERFORMANCE_ANALYSIS.md](./PERFORMANCE_ANALYSIS.md)
- **关键瓶颈**: 12个性能问题
- **预期提升**: 15-100倍性能改进（在各个操作上）

---

## 改进路线图

### Phase 1: 组织结构优化 (优先级: CRITICAL)

**目标**: 将聚合根移动到正确的目录，建立清晰的DDD结构

**时间**: 1-2周
**风险**: 中等（需要更新100+导入语句）

#### 任务清单

**1.1 创建Aggregates目录结构**
```bash
# 目标结构
src/domain/aggregates/
├── __init__.py
├── signal_batch.py      # 从 entities/trading_signal.py 移动
├── prediction_batch.py  # 从 entities/prediction.py 移动
├── portfolio.py         # 从 entities/portfolio.py 移动
└── backtest_result.py   # 从 entities/backtest.py 移动
```

**影响范围**:
- 需要更新的文件: ~50个
- 需要更新的测试: ~80个
- 需要更新的import语句: ~150条

**实施步骤**:
1. 在 `aggregates/` 目录创建新文件（复制）
2. 更新所有导入路径:
   ```python
   # 旧导入
   from domain.entities.trading_signal import SignalBatch

   # 新导入
   from domain.aggregates.signal_batch import SignalBatch
   ```
3. 运行所有测试验证
4. 删除 `entities/` 中的旧文件
5. 提交变更

**自动化脚本**:
```bash
# 可使用以下命令批量替换导入
find src tests -name "*.py" -type f -exec sed -i '' \
  's/from domain\.entities\.trading_signal/from domain.aggregates.signal_batch/g' {} +
find src tests -name "*.py" -type f -exec sed -i '' \
  's/from domain\.entities\.prediction/from domain.aggregates.prediction_batch/g' {} +
find src tests -name "*.py" -type f -exec sed -i '' \
  's/from domain\.entities\.portfolio/from domain.aggregates.portfolio/g' {} +
find src tests -name "*.py" -type f -exec sed -i '' \
  's/from domain\.entities\.backtest/from domain.aggregates.backtest_result/g' {} +
```

**验证标准**:
- [ ] 所有462个测试通过
- [ ] 无导入错误
- [ ] 代码覆盖率不降低

---

### Phase 2: 领域服务实现 (优先级: HIGH)

**目标**: 将业务逻辑从适配器移动到领域服务

**时间**: 2-3周
**风险**: 低（纯重构，不改变行为）

#### 2.1 创建 SignalGenerationService

**问题识别**:
当前 `SignalConverterAdapter` 包含业务逻辑：
```python
# src/adapters/signal/signal_converter_adapter.py
# ❌ 业务逻辑在适配器中
def convert_predictions_to_signals(self, predictions: PredictionBatch) -> SignalBatch:
    # 复杂的信号生成逻辑
    if pred.value > top_threshold:
        signal_type = SignalType.BUY
    elif pred.value < bottom_threshold:
        signal_type = SignalType.SELL
```

**解决方案**:
创建 `SignalGenerationService` 领域服务：

```python
# src/domain/services/signal_generation_service.py
"""
SignalGenerationService - 信号生成领域服务

职责:
- 根据预测结果生成交易信号
- 应用信号强度分类逻辑
- 确保信号生成的业务规则一致性
"""
from typing import Dict, Any
from domain.aggregates.prediction_batch import PredictionBatch, Prediction
from domain.aggregates.signal_batch import SignalBatch, TradingSignal, SignalType, SignalStrength
from domain.value_objects.stock_code import StockCode


class SignalGenerationService:
    """
    信号生成领域服务

    纯业务逻辑,不依赖外部框架
    """

    def __init__(self, strategy_config: Dict[str, Any]):
        """
        初始化服务

        Args:
            strategy_config: 策略配置(阈值、参数等)
        """
        self.strategy_config = strategy_config
        self._load_thresholds()

    def _load_thresholds(self):
        """从配置加载阈值"""
        self.buy_threshold_strong = self.strategy_config.get('buy_threshold_strong', 0.8)
        self.buy_threshold_medium = self.strategy_config.get('buy_threshold_medium', 0.6)
        self.sell_threshold_strong = self.strategy_config.get('sell_threshold_strong', -0.8)
        self.sell_threshold_medium = self.strategy_config.get('sell_threshold_medium', -0.6)

    def generate_signals(
        self,
        predictions: PredictionBatch,
        strategy_name: str
    ) -> SignalBatch:
        """
        根据预测生成交易信号

        Args:
            predictions: 预测批次
            strategy_name: 策略名称

        Returns:
            SignalBatch: 生成的信号批次
        """
        signal_batch = SignalBatch(
            strategy_name=strategy_name,
            batch_date=predictions.batch_date
        )

        for prediction in predictions.predictions:
            signal = self._create_signal_from_prediction(prediction)
            if signal:
                signal_batch.add_signal(signal)

        return signal_batch

    def _create_signal_from_prediction(
        self,
        prediction: Prediction
    ) -> TradingSignal | None:
        """
        从单个预测创建信号

        业务规则:
        1. 预测值 > 0.8: 强买入
        2. 预测值 > 0.6: 中等买入
        3. 预测值 < -0.8: 强卖出
        4. 预测值 < -0.6: 中等卖出
        5. 其他: 持有(不生成信号)
        """
        value = float(prediction.value)

        # 确定信号类型和强度
        if value >= self.buy_threshold_strong:
            signal_type = SignalType.BUY
            signal_strength = SignalStrength.STRONG
            reason = f"Strong buy signal: prediction={value:.3f}"
        elif value >= self.buy_threshold_medium:
            signal_type = SignalType.BUY
            signal_strength = SignalStrength.MEDIUM
            reason = f"Medium buy signal: prediction={value:.3f}"
        elif value <= self.sell_threshold_strong:
            signal_type = SignalType.SELL
            signal_strength = SignalStrength.STRONG
            reason = f"Strong sell signal: prediction={value:.3f}"
        elif value <= self.sell_threshold_medium:
            signal_type = SignalType.SELL
            signal_strength = SignalStrength.MEDIUM
            reason = f"Medium sell signal: prediction={value:.3f}"
        else:
            # 持有,不生成信号
            return None

        return TradingSignal(
            stock_code=prediction.stock_code,
            signal_date=prediction.prediction_date,
            signal_type=signal_type,
            signal_strength=signal_strength,
            price=prediction.target_price,
            reason=reason
        )
```

**重构 SignalConverterAdapter**:
```python
# src/adapters/signal/signal_converter_adapter.py
"""
SignalConverterAdapter - 信号转换适配器

职责:
- 调用领域服务
- 适配外部接口
- 不包含业务逻辑
"""
from domain.services.signal_generation_service import SignalGenerationService
from domain.ports.signal_converter import ISignalConverter
from domain.aggregates.prediction_batch import PredictionBatch
from domain.aggregates.signal_batch import SignalBatch


class SignalConverterAdapter(ISignalConverter):
    """信号转换适配器 - 委托给领域服务"""

    def __init__(self, strategy_config: Dict[str, Any]):
        # 创建领域服务
        self.signal_service = SignalGenerationService(strategy_config)

    async def convert(
        self,
        predictions: PredictionBatch,
        strategy_name: str
    ) -> SignalBatch:
        """
        转换预测为信号

        直接委托给领域服务,不含业务逻辑
        """
        # 委托给领域服务
        return self.signal_service.generate_signals(predictions, strategy_name)
```

**测试策略**:
```python
# tests/unit/domain/services/test_signal_generation_service.py
"""测试信号生成服务"""
import pytest
from decimal import Decimal
from datetime import datetime

from domain.services.signal_generation_service import SignalGenerationService
from domain.aggregates.prediction_batch import PredictionBatch, Prediction
from domain.aggregates.signal_batch import SignalType, SignalStrength
from domain.value_objects.stock_code import StockCode


class TestSignalGenerationService:
    """测试信号生成服务"""

    def test_generate_strong_buy_signal(self):
        """测试生成强买入信号"""
        # Arrange
        config = {
            'buy_threshold_strong': 0.8,
            'buy_threshold_medium': 0.6
        }
        service = SignalGenerationService(config)

        prediction = Prediction(
            stock_code=StockCode("sh600000"),
            prediction_date=datetime(2024, 1, 1),
            value=Decimal("0.85"),  # > 0.8
            target_price=Decimal("10.5")
        )

        # Act
        signal = service._create_signal_from_prediction(prediction)

        # Assert
        assert signal is not None
        assert signal.signal_type == SignalType.BUY
        assert signal.signal_strength == SignalStrength.STRONG
        assert "Strong buy signal" in signal.reason

    def test_no_signal_for_hold(self):
        """测试持有不生成信号"""
        config = {
            'buy_threshold_medium': 0.6,
            'sell_threshold_medium': -0.6
        }
        service = SignalGenerationService(config)

        prediction = Prediction(
            stock_code=StockCode("sh600000"),
            prediction_date=datetime(2024, 1, 1),
            value=Decimal("0.3"),  # 在阈值之间
            target_price=Decimal("10.5")
        )

        # Act
        signal = service._create_signal_from_prediction(prediction)

        # Assert
        assert signal is None  # 持有不生成信号
```

**实施检查清单**:
- [ ] 创建 `domain/services/` 目录
- [ ] 实现 `SignalGenerationService`
- [ ] 编写服务单元测试(>85%覆盖率)
- [ ] 重构 `SignalConverterAdapter` 使用服务
- [ ] 更新适配器测试
- [ ] 运行所有测试验证
- [ ] 文档化服务职责

---

### Phase 3: 领域事件基础设施 (优先级: MEDIUM)

**目标**: 实现领域事件机制，支持解耦和异步处理

**时间**: 2-3周
**风险**: 低

#### 3.1 创建领域事件基类

```python
# src/domain/events/base.py
"""
领域事件基础设施

领域事件用于:
- 记录领域中发生的重要业务事件
- 解耦聚合根之间的依赖
- 支持事件溯源和审计
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict
import uuid


@dataclass
class DomainEvent:
    """
    领域事件基类

    所有领域事件必须继承此类
    """
    # 事件唯一标识
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    # 事件发生时间
    occurred_at: datetime = field(default_factory=datetime.now)

    # 事件版本(用于事件演化)
    event_version: int = 1

    # 事件元数据
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """验证事件数据"""
        if not self.event_id:
            raise ValueError("event_id cannot be empty")
        if not self.occurred_at:
            raise ValueError("occurred_at cannot be empty")
```

#### 3.2 定义关键领域事件

```python
# src/domain/events/signal_events.py
"""信号相关领域事件"""
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from domain.events.base import DomainEvent
from domain.value_objects.stock_code import StockCode


@dataclass
class SignalGeneratedEvent(DomainEvent):
    """信号生成事件"""
    stock_code: StockCode
    signal_type: str  # "BUY" | "SELL" | "HOLD"
    signal_strength: str  # "STRONG" | "MEDIUM" | "WEAK"
    price: Decimal
    strategy_name: str
    signal_date: datetime
    reason: str


@dataclass
class SignalBatchCompletedEvent(DomainEvent):
    """信号批次完成事件"""
    batch_id: str
    strategy_name: str
    batch_date: datetime
    total_signals: int
    buy_signals: int
    sell_signals: int
    hold_signals: int
```

```python
# src/domain/events/model_events.py
"""模型相关领域事件"""
from dataclasses import dataclass
from datetime import datetime

from domain.events.base import DomainEvent


@dataclass
class ModelTrainedEvent(DomainEvent):
    """模型训练完成事件"""
    model_id: str
    model_type: str
    training_date: datetime
    metrics: dict  # {"accuracy": 0.85, "mse": 0.12}


@dataclass
class ModelDeployedEvent(DomainEvent):
    """模型部署事件"""
    model_id: str
    deployment_environment: str  # "test" | "production"
    deployed_at: datetime
```

```python
# src/domain/events/backtest_events.py
"""回测相关领域事件"""
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from domain.events.base import DomainEvent


@dataclass
class BacktestStartedEvent(DomainEvent):
    """回测开始事件"""
    backtest_id: str
    strategy_name: str
    start_date: datetime
    end_date: datetime
    initial_capital: Decimal


@dataclass
class BacktestCompletedEvent(DomainEvent):
    """回测完成事件"""
    backtest_id: str
    strategy_name: str
    final_capital: Decimal
    total_return: Decimal
    sharpe_ratio: Decimal
    max_drawdown: Decimal
    total_trades: int
```

#### 3.3 创建事件分发器

```python
# src/domain/events/dispatcher.py
"""
事件分发器

职责:
- 注册事件处理器
- 分发事件到相应处理器
- 支持同步和异步处理
"""
from typing import Callable, Dict, List, Type
import logging
from domain.events.base import DomainEvent


logger = logging.getLogger(__name__)


class EventDispatcher:
    """
    领域事件分发器

    使用观察者模式
    """

    def __init__(self):
        # 事件类型 -> 处理器列表
        self._handlers: Dict[Type[DomainEvent], List[Callable]] = {}

    def register(
        self,
        event_type: Type[DomainEvent],
        handler: Callable[[DomainEvent], None]
    ):
        """
        注册事件处理器

        Args:
            event_type: 事件类型
            handler: 处理器函数
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []

        self._handlers[event_type].append(handler)
        logger.info(f"Registered handler for {event_type.__name__}")

    def dispatch(self, event: DomainEvent):
        """
        分发事件

        Args:
            event: 领域事件
        """
        event_type = type(event)

        if event_type not in self._handlers:
            logger.debug(f"No handlers for {event_type.__name__}")
            return

        handlers = self._handlers[event_type]
        logger.info(f"Dispatching {event_type.__name__} to {len(handlers)} handlers")

        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(
                    f"Error in handler {handler.__name__} for {event_type.__name__}: {e}",
                    exc_info=True
                )


# 全局事件分发器单例
_global_dispatcher = EventDispatcher()


def get_event_dispatcher() -> EventDispatcher:
    """获取全局事件分发器"""
    return _global_dispatcher
```

#### 3.4 使用示例

```python
# 在聚合根中发布事件
# src/domain/aggregates/signal_batch.py

from domain.events.dispatcher import get_event_dispatcher
from domain.events.signal_events import SignalGeneratedEvent, SignalBatchCompletedEvent


class SignalBatch:
    def add_signal(self, signal: TradingSignal) -> None:
        """添加信号并发布事件"""
        # ... 原有逻辑 ...
        self.signals.append(signal)

        # 发布信号生成事件
        event = SignalGeneratedEvent(
            stock_code=signal.stock_code,
            signal_type=signal.signal_type.value,
            signal_strength=signal.signal_strength.value,
            price=signal.price,
            strategy_name=self.strategy_name,
            signal_date=signal.signal_date,
            reason=signal.reason or ""
        )
        get_event_dispatcher().dispatch(event)
```

```python
# 注册事件处理器
# src/infrastructure/events/handlers.py

from domain.events.signal_events import SignalGeneratedEvent
from domain.events.dispatcher import get_event_dispatcher
import logging

logger = logging.getLogger(__name__)


def log_signal_generated(event: SignalGeneratedEvent):
    """记录信号生成事件"""
    logger.info(
        f"Signal generated: {event.stock_code.value} "
        f"{event.signal_type} ({event.signal_strength}) "
        f"at {event.price}"
    )


def send_notification(event: SignalGeneratedEvent):
    """发送信号通知(可扩展)"""
    if event.signal_strength == "STRONG":
        # 发送强信号通知
        logger.warning(f"STRONG signal: {event.stock_code.value} {event.signal_type}")


# 初始化时注册处理器
def register_signal_handlers():
    dispatcher = get_event_dispatcher()
    dispatcher.register(SignalGeneratedEvent, log_signal_generated)
    dispatcher.register(SignalGeneratedEvent, send_notification)
```

**实施检查清单**:
- [ ] 创建 `domain/events/` 目录
- [ ] 实现事件基类和分发器
- [ ] 定义关键领域事件
- [ ] 在聚合根中发布事件
- [ ] 创建事件处理器
- [ ] 编写事件测试
- [ ] 文档化事件流

---

### Phase 4: 限界上下文重组 (优先级: LOW)

**目标**: 按限界上下文(Bounded Context)重组代码

**时间**: 3-4周
**风险**: 高（大规模重构）

#### 4.1 识别限界上下文

根据业务领域,识别以下限界上下文:

1. **Data Context** (数据上下文)
   - 股票数据管理
   - K线数据
   - 数据加载和验证

2. **Model Context** (模型上下文)
   - 模型训练
   - 模型管理
   - 预测生成

3. **Trading Context** (交易上下文)
   - 信号生成
   - 投资组合管理
   - 交易执行

4. **Backtest Context** (回测上下文)
   - 回测执行
   - 绩效分析
   - 风险评估

#### 4.2 目标目录结构

```
src/
├── contexts/
│   ├── data/
│   │   ├── domain/
│   │   │   ├── entities/
│   │   │   │   ├── kline_data.py
│   │   │   │   └── stock.py
│   │   │   ├── value_objects/
│   │   │   │   ├── stock_code.py
│   │   │   │   └── kline_type.py
│   │   │   └── ports/
│   │   │       └── stock_data_provider.py
│   │   ├── use_cases/
│   │   │   └── load_stock_data.py
│   │   └── adapters/
│   │       ├── hikyuu_data_adapter.py
│   │       └── qlib_data_adapter.py
│   │
│   ├── model/
│   │   ├── domain/
│   │   │   ├── aggregates/
│   │   │   │   ├── model.py
│   │   │   │   └── prediction_batch.py
│   │   │   └── ports/
│   │   │       ├── model_trainer.py
│   │   │       └── model_repository.py
│   │   ├── use_cases/
│   │   │   ├── train_model.py
│   │   │   └── generate_predictions.py
│   │   └── adapters/
│   │       └── qlib_model_trainer_adapter.py
│   │
│   ├── trading/
│   │   ├── domain/
│   │   │   ├── aggregates/
│   │   │   │   ├── signal_batch.py
│   │   │   │   └── portfolio.py
│   │   │   ├── services/
│   │   │   │   └── signal_generation_service.py
│   │   │   └── events/
│   │   │       └── signal_events.py
│   │   ├── use_cases/
│   │   │   ├── convert_predictions_to_signals.py
│   │   │   └── manage_portfolio.py
│   │   └── adapters/
│   │       └── signal_converter_adapter.py
│   │
│   └── backtest/
│       ├── domain/
│       │   ├── aggregates/
│       │   │   └── backtest_result.py
│       │   └── ports/
│       │       └── backtest_engine.py
│       ├── use_cases/
│       │   ├── run_backtest.py
│       │   └── analyze_backtest_result.py
│       └── adapters/
│           └── hikyuu_backtest_adapter.py
│
└── shared/
    ├── domain/
    │   ├── value_objects/
    │   │   ├── date_range.py
    │   │   └── configuration.py
    │   └── events/
    │       └── base.py
    └── infrastructure/
        ├── config/
        ├── app_logging/
        └── errors/
```

#### 4.3 迁移策略

**原则**:
1. 保持向后兼容
2. 渐进式迁移
3. 持续测试验证

**步骤**:
1. 创建新的上下文目录结构
2. 逐个上下文迁移代码(先Data, 后Model, Trading, Backtest)
3. 每迁移一个上下文,运行测试验证
4. 更新导入路径
5. 删除旧结构

**注意**: 此阶段风险较高,建议在独立分支进行,充分测试后合并。

---

## 实施优先级矩阵

| Phase | 优先级 | 影响 | 风险 | 预计时间 | 建议时机 |
|-------|--------|------|------|----------|----------|
| Phase 1: Aggregates重组 | CRITICAL | 高 | 中 | 1-2周 | Phase 7后 |
| Phase 2: 领域服务 | HIGH | 高 | 低 | 2-3周 | Phase 7后 |
| Phase 3: 领域事件 | MEDIUM | 中 | 低 | 2-3周 | 有新功能需求时 |
| Phase 4: 限界上下文 | LOW | 低 | 高 | 3-4周 | 未来重构 |
| 安全改进(HIGH) | HIGH | 高 | 低 | 4-6周 | 生产环境前 |
| 性能优化(CRITICAL) | HIGH | 高 | 低 | 3-4周 | 性能问题时 |

---

## 技术债务记录

根据审查结果,记录以下技术债务:

### 架构债务
1. **聚合根位置不正确** - 应在 `aggregates/` 而非 `entities/`
2. **缺少领域服务** - 业务逻辑泄露到适配器
3. **无领域事件** - 聚合根之间紧耦合
4. **缺少限界上下文** - 单一庞大的domain模块
5. **Ports使用any类型** - 类型安全性不足

### 安全债务
1. **数据加密缺失** - 敏感交易数据未加密存储
2. **依赖管理缺失** - 无requirements.txt,无漏洞扫描
3. **日志敏感数据** - 需要实现日志过滤器
4. **路径遍历风险** - 文件路径验证不足

### 性能债务
1. **N+1查询问题** - 需要批量操作
2. **无连接池** - 数据库连接管理不当
3. **无缓存层** - 重复数据获取
4. **无分页支持** - 可能OOM
5. **假异步操作** - 声明async但执行阻塞I/O

---

## 度量指标

### 当前状态
- **架构评分**: B+ (85/100)
- **测试通过率**: 100% (462/462)
- **代码覆盖率**: >85%
- **项目完成度**: 91.5% (43/47任务)

### 目标状态 (完成所有改进后)
- **架构评分**: A+ (95+/100)
- **测试通过率**: 100%
- **代码覆盖率**: >90%
- **项目完成度**: 100%
- **技术债务**: 0个CRITICAL, <5个HIGH

---

## 建议的实施时机

### 当前阶段 (Phase 6完成)
- ✅ **继续Phase 7 (文档)**: 完成项目文档编写
- ✅ **准备生产环境**: 实施安全改进(数据加密、依赖扫描)
- ⏸️ **暂缓架构重构**: 避免在发布前大规模重构

### Phase 7完成后
- 🔧 **Phase 1实施**: 移动聚合根到正确位置
- 🔧 **Phase 2实施**: 创建领域服务
- 📊 **性能优化**: 实施关键性能改进(连接池、缓存)

### 生产环境稳定后
- 🏗️ **Phase 3实施**: 添加领域事件支持
- 🏗️ **Phase 4考虑**: 评估是否需要限界上下文重组

---

## 参考文档

1. **架构审查报告**: [ARCHITECTURE_REVIEW_REPORT.md](./ARCHITECTURE_REVIEW_REPORT.md)
2. **性能分析报告**: [PERFORMANCE_ANALYSIS.md](./PERFORMANCE_ANALYSIS.md)
3. **安全审计报告**: 已在代码审查响应中提供
4. **项目任务文档**: [docs/tasks.md](./docs/tasks.md)

---

## 结论

Hikyuu QLib项目展现了优秀的架构基础和工程实践。当前状态已经可以投入使用,建议的改进项主要用于:

1. **提升架构纯度**: 更好地遵循DDD原则
2. **提高可维护性**: 通过领域服务和事件解耦
3. **增强安全性**: 数据加密和漏洞管理
4. **优化性能**: 批量操作、缓存、连接池

这些改进可以**渐进式实施**,不会影响当前功能,但能为未来扩展奠定更坚实的基础。

---

**文档维护者**: Architecture Review Team
**最后更新**: 2025-11-13
**下次审查**: Phase 7完成后
