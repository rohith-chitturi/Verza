from contracts.schemas.delta import Operation, WorldStateDelta
from contracts.schemas.world import WorldState
from core.telemetry.logging import get_logger

logger = get_logger("core.state.merger")

class DeltaMerger:
    """
    Blindly applies a validated WorldStateDelta to a WorldState.
    Returns a new immutable WorldState.
    """
    
    def merge(self, state: WorldState, delta: WorldStateDelta) -> WorldState:
        state_dict = state.model_dump()
        
        for op in delta.operations:
            domain_parts = op.domain.split('.')
            if len(domain_parts) < 2 or len(domain_parts) > 3:
                logger.warning(f"Invalid domain format {op.domain}, skipping operation {op.change_id}")
                continue
            
            section = domain_parts[0]
            collection = domain_parts[1]
            
            if section not in state_dict or collection not in state_dict[section]:
                logger.warning(f"Unknown domain path {op.domain}, skipping operation {op.change_id}")
                continue
            
            # Resolve target list or dict
            target = state_dict[section][collection]
            if len(domain_parts) == 3:
                sub_collection = domain_parts[2]
                if sub_collection not in target:
                    logger.warning(f"Unknown sub-domain {op.domain}, skipping operation {op.change_id}")
                    continue
                target = target[sub_collection]
            
            if op.operation == Operation.ADD or op.operation == Operation.LINK:
                if isinstance(target, list):
                    if "id" not in op.payload and op.entity_id:
                        op.payload["id"] = op.entity_id
                    target.append(op.payload)
                elif isinstance(target, dict):
                    if op.entity_id:
                        target[op.entity_id] = op.payload
            
            elif op.operation == Operation.UPDATE:
                if isinstance(target, list):
                    for i, item in enumerate(target):
                        if item.get("id") == op.entity_id:
                            item.update(op.payload)
                            break
                elif isinstance(target, dict) and op.entity_id in target:
                    target[op.entity_id].update(op.payload)
            
            elif op.operation == Operation.REMOVE or op.operation == Operation.UNLINK:
                if isinstance(target, list):
                    # We can't easily replace the list reference if it's deeply nested without keeping parent track.
                    # Instead, we mutate it in place
                    items_to_remove = [item for item in target if item.get("id") == op.entity_id]
                    for item in items_to_remove:
                        target.remove(item)
                elif isinstance(target, dict) and op.entity_id in target:
                    del target[op.entity_id]
                    
        return WorldState(**state_dict)
