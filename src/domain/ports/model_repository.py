"""模型仓储端口"""

from abc import ABC, abstractmethod
from typing import Optional, List
from domain.entities.model import Model


class IModelRepository(ABC):
    """模型仓储接口"""

    @abstractmethod
    async def save(self, model: Model) -> None:
        """保存模型"""
        pass

    @abstractmethod
    async def find_by_id(self, model_id: str) -> Optional[Model]:
        """根据ID查找模型"""
        pass

    @abstractmethod
    async def find_all(self) -> List[Model]:
        """查找所有模型"""
        pass

    @abstractmethod
    async def delete(self, model_id: str) -> None:
        """删除模型"""
        pass
