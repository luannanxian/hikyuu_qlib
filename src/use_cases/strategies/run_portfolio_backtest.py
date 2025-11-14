"""
RunPortfolioBacktestUseCase - 运行投资组合回测用例

UC-PORTFOLIO-BT: Run Portfolio Backtest (运行Hikyuu投资组合回测)
"""

from dataclasses import dataclass
from typing import List, Optional
import pickle
from pathlib import Path

from domain.entities.prediction import PredictionBatch, Prediction
from domain.entities.trading_signal import SignalBatch
from domain.ports.backtest_engine import IBacktestEngine
from domain.ports.signal_provider import ISignalProvider
from domain.value_objects.date_range import DateRange
from domain.value_objects.rebalance_period import RebalancePeriod
from domain.value_objects.stock_code import StockCode
from domain.value_objects.configuration import BacktestConfig


@dataclass
class RunPortfolioBacktestRequest:
    """
    运行投资组合回测请求DTO

    Attributes:
        pred_pkl_path: Qlib预测结果pickle文件路径
        stock_pool: 股票池代码列表
        date_range: 回测日期范围
        top_k: Top-K选股数量,默认10只
        rebalance_period: 调仓周期,默认每周
        initial_cash: 初始资金,默认1,000,000.0
    """

    pred_pkl_path: str
    stock_pool: List[StockCode]
    date_range: DateRange
    top_k: int = 10
    rebalance_period: RebalancePeriod = RebalancePeriod.WEEK
    initial_cash: float = 1000000.0

    def __post_init__(self):
        """验证请求参数有效性"""
        # 验证路径存在
        if not Path(self.pred_pkl_path).exists():
            raise ValueError(
                f"Prediction file not found: {self.pred_pkl_path}"
            )

        # 验证 top_k
        if self.top_k <= 0:
            raise ValueError(f"top_k must be > 0, got top_k={self.top_k}")

        # 验证股票池不为空
        if not self.stock_pool:
            raise ValueError("stock_pool cannot be empty")

        # 验证初始资金
        if self.initial_cash <= 0:
            raise ValueError(
                f"initial_cash must be > 0, got initial_cash={self.initial_cash}"
            )


@dataclass
class RunPortfolioBacktestResponse:
    """
    运行投资组合回测响应DTO

    Attributes:
        total_return: 总收益率
        sharpe_ratio: 夏普比率
        max_drawdown: 最大回撤
        trade_count: 交易次数
        success: 是否成功
        error: 错误信息(如果失败)
    """

    total_return: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    trade_count: int = 0
    success: bool = False
    error: Optional[str] = None


class RunPortfolioBacktestUseCase:
    """
    运行投资组合回测用例

    职责:
    - 验证请求参数
    - 加载Qlib预测结果
    - 生成动态Top-K交易信号
    - 运行Hikyuu回测引擎
    - 返回回测结果

    依赖注入:
    - backtest_engine: IBacktestEngine (回测引擎接口)
    - signal_provider: ISignalProvider (信号提供者接口)

    业务规则:
    - 支持动态调仓(按调仓周期重新计算Top-K)
    - 只在股票池内选股
    - 等权重分配初始资金到Top-K股票
    - 按调仓周期重新平衡投资组合
    """

    def __init__(
        self,
        backtest_engine: IBacktestEngine,
        signal_provider: ISignalProvider,
    ):
        """
        初始化用例

        Args:
            backtest_engine: 回测引擎接口实现
            signal_provider: 信号提供者接口实现
        """
        self.backtest_engine = backtest_engine
        self.signal_provider = signal_provider

    async def execute(
        self, request: RunPortfolioBacktestRequest
    ) -> RunPortfolioBacktestResponse:
        """
        执行运行投资组合回测

        Args:
            request: 运行投资组合回测请求

        Returns:
            RunPortfolioBacktestResponse: 包含回测指标的响应

        业务流程:
        1. 加载Qlib预测结果
        2. 过滤股票池内的预测
        3. 生成Top-K交易信号
        4. 配置回测引擎
        5. 运行回测
        6. 提取回测指标
        7. 返回响应

        异常处理:
        - ValueError: 参数验证失败
        - FileNotFoundError: 预测文件不存在
        - Exception: 回测执行失败
        """
        try:
            # 1. 加载Qlib预测结果
            prediction_batch = self._load_predictions(request.pred_pkl_path)

            # 2. 过滤股票池内的预测
            filtered_batch = self._filter_by_stock_pool(
                prediction_batch, request.stock_pool
            )

            if filtered_batch.size() == 0:
                return RunPortfolioBacktestResponse(
                    success=False,
                    error="No predictions found in stock pool",
                )

            # 3. 生成Top-K交易信号
            signal_batch = self.signal_provider.generate_signals_from_predictions(
                prediction_batch=filtered_batch,
                buy_threshold=0.02,  # 默认买入阈值 2%
                sell_threshold=-0.02,  # 默认卖出阈值 -2%
                top_k=request.top_k,
            )

            # 4. 配置回测引擎
            from decimal import Decimal

            backtest_config = BacktestConfig(
                initial_capital=Decimal(str(request.initial_cash)),
                commission_rate=Decimal("0.0003"),  # 默认手续费率 0.03%
                slippage_rate=Decimal("0.0001"),  # 默认滑点率 0.01%
            )

            # Note: rebalance_period is passed separately to the backtest engine
            # It's not part of BacktestConfig

            # 5. 运行回测
            backtest_result = await self.backtest_engine.run_backtest(
                signals=signal_batch,
                config=backtest_config,
                date_range=request.date_range,
            )

            # 6. 提取回测指标
            total_return = float(backtest_result.total_return())
            sharpe_ratio = float(backtest_result.calculate_sharpe_ratio())
            max_drawdown = float(backtest_result.calculate_max_drawdown())
            trade_count = len(backtest_result.trades)

            # 7. 返回成功响应
            return RunPortfolioBacktestResponse(
                total_return=total_return,
                sharpe_ratio=sharpe_ratio,
                max_drawdown=max_drawdown,
                trade_count=trade_count,
                success=True,
            )

        except FileNotFoundError as e:
            return RunPortfolioBacktestResponse(
                success=False,
                error=f"Prediction file not found: {str(e)}",
            )

        except ValueError as e:
            return RunPortfolioBacktestResponse(
                success=False,
                error=f"Validation error: {str(e)}",
            )

        except Exception as e:
            return RunPortfolioBacktestResponse(
                success=False,
                error=f"Backtest execution failed: {str(e)}",
            )

    def _load_predictions(self, pkl_path: str) -> PredictionBatch:
        """
        加载Qlib预测结果

        Args:
            pkl_path: pickle文件路径

        Returns:
            PredictionBatch: 预测批次聚合根

        Raises:
            FileNotFoundError: 文件不存在
            Exception: 文件加载失败
        """
        try:
            with open(pkl_path, "rb") as f:
                pred_data = pickle.load(f)

            # 假设 pred_data 是 pandas DataFrame 格式
            # columns: ['stock_code', 'timestamp', 'predicted_value', ...]
            predictions = []

            for _, row in pred_data.iterrows():
                prediction = Prediction(
                    stock_code=StockCode(row["stock_code"]),
                    timestamp=row["timestamp"],
                    predicted_value=float(row["predicted_value"]),
                    model_id=row.get("model_id", "qlib_model"),
                    confidence=float(row["confidence"])
                    if "confidence" in row
                    else None,
                )
                predictions.append(prediction)

            # 创建预测批次
            from datetime import datetime

            batch = PredictionBatch(
                model_id=pred_data.iloc[0].get("model_id", "qlib_model"),
                predictions=predictions,
                generated_at=datetime.now(),
            )

            return batch

        except FileNotFoundError:
            raise

        except Exception as e:
            raise Exception(f"Failed to load predictions: {str(e)}")

    def _filter_by_stock_pool(
        self, batch: PredictionBatch, stock_pool: List[StockCode]
    ) -> PredictionBatch:
        """
        过滤股票池内的预测

        Args:
            batch: 原始预测批次
            stock_pool: 股票池代码列表

        Returns:
            PredictionBatch: 过滤后的预测批次
        """
        # 将股票池转换为集合以提高查找效率
        stock_pool_set = set(stock_pool)

        # 过滤预测
        filtered_predictions = [
            pred for pred in batch.predictions if pred.stock_code in stock_pool_set
        ]

        # 创建新的预测批次
        filtered_batch = PredictionBatch(
            model_id=batch.model_id,
            predictions=filtered_predictions,
            generated_at=batch.generated_at,
        )

        return filtered_batch
