from abc import ABC, abstractmethod
from collections.abc import Callable

from contracts.events.base import BaseEvent


class EventBus(ABC):
    """
    Abstract Interface for the Event Bus.
    """
    @abstractmethod
    def subscribe(self, event_type: str, handler: Callable[[BaseEvent], None]) -> None:
        pass

    @abstractmethod
    def publish(self, event: BaseEvent) -> None:
        pass

class InMemoryEventBus(EventBus):
    """
    In-memory implementation of the Event Bus.
    """
    def __init__(self):
        self._subscribers: dict[str, list[Callable[[BaseEvent], None]]] = {}

    def subscribe(self, event_type: str, handler: Callable[[BaseEvent], None]) -> None:
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)

    def publish(self, event: BaseEvent) -> None:
        event_type = event.__class__.__name__
        if event_type in self._subscribers:
            for handler in self._subscribers[event_type]:
                handler(event)
