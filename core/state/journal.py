from contracts.schemas.delta import WorldStateDelta
from core.telemetry.logging import get_logger

logger = get_logger("core.state.journal")


class DeltaJournal:
    """
    Event-sourced store for all accepted WorldStateDeltas.
    Provides auditability, debugging, and replay capabilities.
    """

    def __init__(self) -> None:
        self._journal: list[WorldStateDelta] = []

    def append(self, delta: WorldStateDelta) -> None:
        self._journal.append(delta)
        logger.info(
            f"Appended Delta {delta.id} to journal from capability {delta.capability} (Operations: {len(delta.operations)})"
        )

    def get_history(self) -> list[WorldStateDelta]:
        return list(self._journal)

    def clear(self) -> None:
        self._journal.clear()
