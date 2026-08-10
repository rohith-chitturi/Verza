from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from contracts.schemas.snapshot import Snapshot

T = TypeVar('T')

class Repository(ABC, Generic[T]):
    """Generic Repository Interface"""
    @abstractmethod
    def save(self, entity: T) -> None:
        pass
        
    @abstractmethod
    def get(self, entity_id: str) -> T:
        pass

class SnapshotRepository(Repository[Snapshot]):
    pass

class AssetRepository(Repository[Any]):
    pass

class WorkflowRepository(Repository[Any]):
    pass

class ProviderRepository(Repository[Any]):
    pass

class LocalSnapshotRepository(SnapshotRepository):
    def __init__(self):
        self._store = {}
        
    def save(self, snapshot: Snapshot) -> None:
        self._store[snapshot.id] = snapshot
        
    def get(self, snapshot_id: str) -> Snapshot:
        return self._store.get(snapshot_id)
