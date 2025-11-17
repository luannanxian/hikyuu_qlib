"""
AnalyzeBacktestResultUseCase 单元测试

测试 UC-010: Analyze Backtest Result (分析回测结果) 用例
"""

from datetime import datetime
from decimal import Decimal

import pytest

from domain.entities.backtest import BacktestResult, Trade
from domain.value_objects.stock_code import StockCode
from use_cases.analysis.analyze_backtest_result import AnalyzeBacktestResultUseCase


class TestAnalyzeResultSuccess:
    """测试成功分析回测结果"""

    @pytest.mark.asyncio
    async def test_analyze_result_success(self):
        """测试成功分析回测结果"""
        # Arrange: 创建回测结果
        result = BacktestResult(
            strategy_name="测试策略",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 12, 31),
            initial_capital=Decimal(100000),
            final_capital=Decimal(120000),
            equity_curve=[
                Decimal(100000),
                Decimal(105000),
                Decimal(110000),
                Decimal(115000),
                Decimal(120000),
            ],
        )

        # 添加一些交易
        result.add_trade(
            Trade(
                stock_code=StockCode("sh600000"),
                direction="BUY",
                quantity=1000,
                price=Decimal("10.00"),
                trade_date=datetime(2024, 1, 10),
                commission=Decimal(5),
            ),
        )
        result.add_trade(
            Trade(
                stock_code=StockCode("sh600000"),
                direction="SELL",
                quantity=1000,
                price=Decimal("12.00"),
                trade_date=datetime(2024, 6, 10),
                commission=Decimal(6),
            ),
        )

        use_case = AnalyzeBacktestResultUseCase()

        # Act: 分析结果
        analysis = await use_case.execute(backtest_result=result)

        # Assert: 验证分析报告
        assert "total_return" in analysis
        assert "sharpe_ratio" in analysis
        assert "max_drawdown" in analysis
        assert "win_rate" in analysis
        assert "total_trades" in analysis

        # 总收益率 = (120000 - 100000) / 100000 = 0.20
        assert analysis["total_return"] == Decimal("0.2")

        # 交易总数 = 2
        assert analysis["total_trades"] == 2


class TestCalculateSharpeRatio:
    """测试计算夏普比率"""

    @pytest.mark.asyncio
    async def test_calculate_sharpe_ratio(self):
        """测试计算夏普比率"""
        # Arrange: 创建回测结果 (需要多个数据点以计算有效的标准差)
        result = BacktestResult(
            strategy_name="测试策略",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 12, 31),
            initial_capital=Decimal(100000),
            final_capital=Decimal(120000),
            equity_curve=[
                Decimal(100000),
                Decimal(105000),
                Decimal(110000),
                Decimal(115000),
                Decimal(120000),
            ],
        )

        use_case = AnalyzeBacktestResultUseCase()

        # Act: 分析结果
        analysis = await use_case.execute(backtest_result=result)

        # Assert: 验证夏普比率存在且为正数
        assert "sharpe_ratio" in analysis
        assert analysis["sharpe_ratio"] > 0


class TestCalculateMaxDrawdown:
    """测试计算最大回撤"""

    @pytest.mark.asyncio
    async def test_calculate_max_drawdown(self):
        """测试计算最大回撤"""
        # Arrange: 创建有明显回撤的权益曲线
        result = BacktestResult(
            strategy_name="测试策略",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 12, 31),
            initial_capital=Decimal(100000),
            final_capital=Decimal(90000),
            equity_curve=[
                Decimal(100000),  # 起点
                Decimal(120000),  # 最高点
                Decimal(90000),  # 回撤到 90000
                Decimal(95000),
            ],
        )

        use_case = AnalyzeBacktestResultUseCase()

        # Act: 分析结果
        analysis = await use_case.execute(backtest_result=result)

        # Assert: 最大回撤 = (120000 - 90000) / 120000 = 0.25
        assert "max_drawdown" in analysis
        assert analysis["max_drawdown"] == Decimal("0.25")


class TestAnalyzeEmptyResult:
    """测试分析空结果"""

    @pytest.mark.asyncio
    async def test_analyze_empty_result(self):
        """测试空交易列表的回测结果"""
        # Arrange: 创建没有交易的回测结果
        result = BacktestResult(
            strategy_name="测试策略",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 12, 31),
            initial_capital=Decimal(100000),
            final_capital=Decimal(100000),
            equity_curve=[Decimal(100000)],
        )

        use_case = AnalyzeBacktestResultUseCase()

        # Act: 分析结果
        analysis = await use_case.execute(backtest_result=result)

        # Assert: 应该返回默认值
        assert analysis["total_return"] == Decimal(0)
        assert analysis["total_trades"] == 0
        assert analysis["win_rate"] == Decimal(0)

    @pytest.mark.asyncio
    async def test_analyze_empty_equity_curve(self):
        """测试空权益曲线"""
        # Arrange: 创建空权益曲线的回测结果
        result = BacktestResult(
            strategy_name="测试策略",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 12, 31),
            initial_capital=Decimal(100000),
            final_capital=Decimal(100000),
            equity_curve=[],  # 空权益曲线
        )

        use_case = AnalyzeBacktestResultUseCase()

        # Act: 分析结果
        analysis = await use_case.execute(backtest_result=result)

        # Assert: 最大回撤应该为 0
        assert analysis["max_drawdown"] == Decimal(0)
