from abc import ABC, abstractmethod
from typing import Any


class Queue(ABC):
    @abstractmethod
    def push(self, topic: str, message: Any) -> None:
        pass

    @abstractmethod
    def pop(self, topic: str) -> Any:
        pass


class MemoryQueue(Queue):
    def __init__(self):
        self._queues = {}

    def push(self, topic: str, message: Any) -> None:
        if topic not in self._queues:
            self._queues[topic] = []
        self._queues[topic].append(message)

    def pop(self, topic: str) -> Any:
        if self._queues.get(topic):
            return self._queues[topic].pop(0)
        return None
