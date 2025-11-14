"""
SQLiteModelRepository - SQLite 模型仓储

使用 SQLite 数据库存储模型元数据,实现 IModelRepository 接口
"""

import json
from typing import List, Optional
from datetime import datetime
import aiosqlite

from domain.ports.model_repository import IModelRepository
from domain.entities.model import Model, ModelType, ModelStatus


class SQLiteModelRepository(IModelRepository):
    """
    SQLite 模型仓储

    实现 IModelRepository 接口,使用 SQLite 存储模型元数据
    """

    def __init__(self, db_path: str = ":memory:"):
        """
        初始化仓储

        Args:
            db_path: SQLite 数据库路径,默认使用内存数据库
                    支持格式: "path/to/db.db" 或 "sqlite:///path/to/db.db"
        """
        # 解析 SQLite URL 格式
        if db_path.startswith("sqlite:///"):
            db_path = db_path.replace("sqlite:///", "")

        self.db_path = db_path
        self._connection: Optional[aiosqlite.Connection] = None

    async def initialize(self) -> None:
        """
        初始化数据库

        创建表结构
        """
        self._connection = await aiosqlite.connect(self.db_path)

        # 创建模型表
        await self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS models (
                id TEXT PRIMARY KEY,
                model_type TEXT NOT NULL,
                hyperparameters TEXT NOT NULL,
                training_date TEXT,
                metrics TEXT,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        await self._connection.commit()

    async def close(self) -> None:
        """关闭数据库连接"""
        if self._connection:
            await self._connection.close()

    def _serialize_model(self, model: Model) -> dict:
        """
        序列化模型为字典

        Args:
            model: 模型实体

        Returns:
            dict: 序列化后的字典
        """
        from decimal import Decimal

        # Convert Decimal to float for JSON serialization
        def convert_decimals(obj):
            """递归转换Decimal为float"""
            if isinstance(obj, Decimal):
                return float(obj)
            elif isinstance(obj, dict):
                return {k: convert_decimals(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_decimals(item) for item in obj]
            else:
                return obj

        # 转换metrics中的Decimal
        metrics_dict = {}
        for key, value in model.metrics.items():
            metrics_dict[key] = float(value) if isinstance(value, Decimal) else value

        # 转换hyperparameters中的Decimal
        hyperparams_clean = convert_decimals(model.hyperparameters)

        return {
            "id": model.id,
            "model_type": model.model_type.value,
            "hyperparameters": json.dumps(hyperparams_clean),
            "training_date": (
                model.training_date.isoformat() if model.training_date else None
            ),
            "metrics": json.dumps(metrics_dict),
            "status": model.status.value,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

    def _deserialize_model(self, row: tuple) -> Model:
        """
        反序列化数据库行为模型实体

        Args:
            row: 数据库行

        Returns:
            Model: 模型实体
        """
        (
            model_id,
            model_type,
            hyperparameters,
            training_date,
            metrics,
            status,
            created_at,
            updated_at,
        ) = row

        model = Model(
            model_type=ModelType(model_type),
            hyperparameters=json.loads(hyperparameters),
            training_date=(
                datetime.fromisoformat(training_date) if training_date else None
            ),
            metrics=json.loads(metrics),
            status=ModelStatus(status),
        )
        # 设置实体ID
        object.__setattr__(model, "id", model_id)

        return model

    async def save(self, model: Model) -> None:
        """
        保存模型

        Args:
            model: 模型实体

        Raises:
            Exception: 当保存失败时
        """
        try:
            # 检查模型是否已存在
            existing = await self.find_by_id(model.id)

            if existing is None:
                # 插入新模型
                data = self._serialize_model(model)
                await self._connection.execute(
                    """
                    INSERT INTO models (id, model_type, hyperparameters, training_date,
                                        metrics, status, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        data["id"],
                        data["model_type"],
                        data["hyperparameters"],
                        data["training_date"],
                        data["metrics"],
                        data["status"],
                        data["created_at"],
                        data["updated_at"],
                    ),
                )
            else:
                # 更新现有模型
                data = self._serialize_model(model)
                await self._connection.execute(
                    """
                    UPDATE models
                    SET model_type = ?, hyperparameters = ?, training_date = ?,
                        metrics = ?, status = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (
                        data["model_type"],
                        data["hyperparameters"],
                        data["training_date"],
                        data["metrics"],
                        data["status"],
                        data["updated_at"],
                        data["id"],
                    ),
                )

            await self._connection.commit()

        except Exception as e:
            raise Exception(f"Failed to save model: {e}") from e

    async def find_by_id(self, model_id: str) -> Optional[Model]:
        """
        根据ID查找模型

        Args:
            model_id: 模型ID

        Returns:
            Optional[Model]: 找到的模型,或 None
        """
        try:
            cursor = await self._connection.execute(
                """
                SELECT id, model_type, hyperparameters, training_date,
                       metrics, status, created_at, updated_at
                FROM models
                WHERE id = ?
                """,
                (model_id,),
            )

            row = await cursor.fetchone()
            if row is None:
                return None

            return self._deserialize_model(row)

        except Exception as e:
            raise Exception(f"Failed to find model by id: {e}") from e

    async def find_all(self) -> List[Model]:
        """
        查找所有模型

        Returns:
            List[Model]: 所有模型列表
        """
        try:
            cursor = await self._connection.execute(
                """
                SELECT id, model_type, hyperparameters, training_date,
                       metrics, status, created_at, updated_at
                FROM models
                ORDER BY created_at DESC
                """
            )

            rows = await cursor.fetchall()
            return [self._deserialize_model(row) for row in rows]

        except Exception as e:
            raise Exception(f"Failed to find all models: {e}") from e

    async def delete(self, model_id: str) -> None:
        """
        删除模型

        Args:
            model_id: 模型ID

        Raises:
            Exception: 当删除失败时
        """
        try:
            await self._connection.execute(
                "DELETE FROM models WHERE id = ?", (model_id,)
            )
            await self._connection.commit()

        except Exception as e:
            raise Exception(f"Failed to delete model: {e}") from e
