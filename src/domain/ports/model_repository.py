"""模型仓储端口"""

from abc import ABC, abstractmethod

from domain.entities.model import Model


class IModelRepository(ABC):
    """模型仓储接口"""

    @abstractmethod
    async def save(self, model: Model) -> None:
        """保存模型"""

    @abstractmethod
    async def find_by_id(self, model_id: str) -> Model | None:
        """根据ID查找模型"""

    @abstractmethod
    async def find_all(self) -> list[Model]:
        """查找所有模型"""

    @abstractmethod
    async def delete(self, model_id: str) -> None:
        """删除模型"""
