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
        # Create a deep mutable copy of the state dictionaries for applying operations
        state_dict = state.model_dump()
        
        for op in delta.operations:
            domain_parts = op.domain.split('.')
            if len(domain_parts) != 2:
                logger.warning(f"Invalid domain format {op.domain}, skipping operation {op.change_id}")
                continue
            
            section, collection = domain_parts
            if section not in state_dict or collection not in state_dict[section]:
                logger.warning(f"Unknown domain path {op.domain}, skipping operation {op.change_id}")
                continue
                
            target_list = state_dict[section][collection]
            
            if op.operation == Operation.ADD:
                if isinstance(target_list, list):
                    # Ensure entity has an ID
                    if "id" not in op.payload and op.entity_id:
                        op.payload["id"] = op.entity_id
                    target_list.append(op.payload)
                elif isinstance(target_list, dict):
                    if op.entity_id:
                        target_list[op.entity_id] = op.payload
            
            elif op.operation == Operation.UPDATE:
                if isinstance(target_list, list):
                    for i, item in enumerate(target_list):
                        if item.get("id") == op.entity_id:
                            item.update(op.payload)
                            break
                elif isinstance(target_list, dict) and op.entity_id in target_list:
                    target_list[op.entity_id].update(op.payload)
            
            elif op.operation == Operation.REMOVE:
                if isinstance(target_list, list):
                    state_dict[section][collection] = [item for item in target_list if item.get("id") != op.entity_id]
                elif isinstance(target_list, dict) and op.entity_id in target_list:
                    del target_list[op.entity_id]
            
            # LINK, UNLINK, SPLIT, MERGE logic deferred
        
        # Instantiate a new WorldState with the updated dictionaries
        # Because WorldState fields (media, visual, etc.) are Pydantic models, 
        # we can unpack the dictionaries.
        new_state = WorldState(**state_dict)
        return new_state
