from typing import Any, Callable

class CapabilityRegistry:
    """
    Maps stable string identifiers (from YAML workflows) to DI-managed 
    capability instances or factories.
    """
    def __init__(self, resolvers: dict[str, Callable[[], Any]]):
        self._resolvers = resolvers

    def get(self, name: str) -> Any:
        if name not in self._resolvers:
            raise ValueError(f"Capability '{name}' is not registered.")
        
        # Resolve the dependency using the factory/provider
        return self._resolvers[name]()
