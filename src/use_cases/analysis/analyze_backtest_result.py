"""
AnalyzeBacktestResultUseCase - 分析回测结果用例

UC-010: Analyze Backtest Result (分析回测结果)
"""

from typing import Any, Dict

from domain.entities.backtest import BacktestResult


class AnalyzeBacktestResultUseCase:
    """
    分析回测结果用例

    职责:
    - 计算关键指标（夏普比率、最大回撤、胜率等）
    - 生成分析报告
    - 使用 BacktestResult 聚合根的方法

    注意:
    - 不依赖外部 Port，直接使用领域对象
    """

    async def execute(self, backtest_result: BacktestResult) -> Dict[str, Any]:
        """
        执行回测结果分析

        Args:
            backtest_result: 回测结果聚合根

        Returns:
            Dict[str, Any]: 分析报告字典，包含以下指标：
                - total_return: 总收益率
                - sharpe_ratio: 夏普比率
                - max_drawdown: 最大回撤
                - win_rate: 胜率
                - total_trades: 交易总数
                - strategy_name: 策略名称
                - start_date: 开始日期
                - end_date: 结束日期
        """
        # 1. 计算总收益率
        total_return = backtest_result.total_return()

        # 2. 计算夏普比率
        sharpe_ratio = backtest_result.calculate_sharpe_ratio()

        # 3. 计算最大回撤
        max_drawdown = backtest_result.calculate_max_drawdown()

        # 4. 计算胜率
        win_rate = backtest_result.get_win_rate()

        # 5. 统计交易数量
        total_trades = len(backtest_result.trades)

        # 6. 构建分析报告
        analysis_report = {
            "strategy_name": backtest_result.strategy_name,
            "start_date": backtest_result.start_date,
            "end_date": backtest_result.end_date,
            "initial_capital": backtest_result.initial_capital,
            "final_capital": backtest_result.final_capital,
            "total_return": total_return,
            "sharpe_ratio": sharpe_ratio,
            "max_drawdown": max_drawdown,
            "win_rate": win_rate,
            "total_trades": total_trades,
        }

        return analysis_report
