from typing import Any, Callable, Dict, List

class EventBus:
    """
    Central Event Bus for the Verza Core.
    """
    def __init__(self):
        self._subscribers: Dict[str, List[Callable[[Any], None]]] = {}

    def subscribe(self, event_type: str, handler: Callable[[Any], None]) -> None:
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)

    def publish(self, event_type: str, payload: Any) -> None:
        """Publishes an event to all subscribers."""
        if event_type in self._subscribers:
            for handler in self._subscribers[event_type]:
                handler(payload)
        # Emit telemetry
        print(f"[EventBus] Published: {event_type} | Payload: {payload}")
