"""Integration Example: Using Infrastructure Layer in Use Cases

This example demonstrates how to use the infrastructure layer (errors, config, logging, monitoring)
in your use cases and adapters.
"""
import asyncio

# 1. Configuration Management
from src.infrastructure.config import Settings

# 2. Logging
from src.infrastructure.app_logging import (
    configure_logging,
    generate_trace_id,
    get_logger,
    set_trace_id,
)

# 3. Error Handling
from src.infrastructure.errors import (
    DataLoadException,
    ErrorCode,
    handle_exceptions,
)

# 4. Monitoring
from src.infrastructure.monitoring import monitor_performance

# Configure application on startup
settings = Settings(
    ENVIRONMENT="dev",
    LOG_LEVEL="INFO",
    HIKYUU_DATA_PATH="./data/hikyuu",
    QLIB_DATA_PATH="./data/qlib",
)

# Configure logging
configure_logging(
    level=settings.LOG_LEVEL,
    format="json",
    log_file=settings.LOG_FILE_PATH,
)

logger = get_logger(__name__)


class LoadStockDataUseCase:
    """Example use case with infrastructure integration."""

    @handle_exceptions()
    @monitor_performance
    async def execute(self, stock_code: str):
        """Load stock data with full infrastructure support.

        Args:
            stock_code: Stock code to load

        Returns:
            Stock data

        Raises:
            DataLoadException: If loading fails
        """
        # Generate and set trace ID for request tracking
        trace_id = generate_trace_id()
        set_trace_id(trace_id)

        logger.info(
            "Starting stock data load",
            extra={"stock_code": stock_code, "trace_id": trace_id},
        )

        try:
            # Simulate data loading
            await asyncio.sleep(0.1)

            # Simulate success or failure
            if stock_code == "000001":
                data = {"code": stock_code, "prices": [100, 101, 102]}
                logger.info(
                    "Data loaded successfully",
                    extra={"stock_code": stock_code, "records": len(data["prices"])},
                )
                return data
            else:
                # Raise exception with proper error code and context
                raise DataLoadException(
                    f"Stock {stock_code} not found",
                    code=ErrorCode.DATA_NOT_FOUND,
                    context={"stock_code": stock_code, "source": "hikyuu"},
                )

        except Exception as e:
            logger.error(
                "Failed to load stock data",
                extra={"stock_code": stock_code, "error": str(e)},
            )
            raise


def main():
    """Main function demonstrating the integration."""
    use_case = LoadStockDataUseCase()

    # Example 1: Successful load
    print("\\n=== Example 1: Successful Load ===")
    result = asyncio.run(use_case.execute("000001"))
    print(f"Loaded data: {result}")

    # Example 2: Failed load with error handling
    print("\\n=== Example 2: Failed Load (Error Handling) ===")
    try:
        asyncio.run(use_case.execute("999999"))
    except Exception as e:
        print(f"Caught exception: {e}")

    # Example 3: Show how configuration works
    print("\\n=== Example 3: Configuration ===")
    print(f"App Name: {settings.APP_NAME}")
    print(f"Environment: {settings.ENVIRONMENT}")
    print(f"Log Level: {settings.LOG_LEVEL}")
    print(f"Hikyuu Data Path: {settings.HIKYUU_DATA_PATH}")
    print(f"Initial Capital: {settings.INITIAL_CAPITAL}")


if __name__ == "__main__":
    main()
