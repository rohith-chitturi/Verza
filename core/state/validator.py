from contracts.schemas.delta import Operation, WorldStateDelta
from contracts.schemas.world import WorldState
from core.telemetry.logging import get_logger

logger = get_logger("core.state.validator")


class ValidationError(Exception):
    pass


class DeltaValidator:
    """
    Validates WorldStateDeltas in 3 passes:
    1. Schema Validation (Structure and Fields)
    2. Semantic Validation (Logical correctness, e.g. bounds)
    3. Consistency Validation (Referential integrity, e.g. entities exist)
    """

    def validate(self, delta: WorldStateDelta, current_state: WorldState) -> bool:
        try:
            self._validate_schema(delta)
            self._validate_semantic(delta)
            self._validate_consistency(delta, current_state)
            return True
        except ValidationError as e:
            logger.error(f"Delta Validation Failed [Delta ID: {delta.id}]: {e!s}")
            return False

    def _validate_schema(self, delta: WorldStateDelta) -> None:
        if not delta.operations:
            raise ValidationError("Delta contains no operations.")

        for op in delta.operations:
            if not op.domain:
                raise ValidationError(f"Change ID {op.change_id} is missing domain.")
            if (
                op.operation in [Operation.UPDATE, Operation.REMOVE]
                and not op.entity_id
            ):
                raise ValidationError(
                    f"Change ID {op.change_id} ({op.operation}) requires an entity_id."
                )

    def _validate_semantic(self, delta: WorldStateDelta) -> None:
        # Example Semantic Checks
        for op in delta.operations:
            if op.domain == "visual.scenes" and op.operation in [
                Operation.ADD,
                Operation.UPDATE,
            ]:
                start = op.payload.get("start_frame")
                end = op.payload.get("end_frame")
                if start is not None and end is not None and start >= end:
                    raise ValidationError(
                        f"Scene end_frame ({end}) must be greater than start_frame ({start})."
                    )

            # Confidence checks
            if op.confidence.confidence < 0.0 or op.confidence.confidence > 1.0:
                raise ValidationError(
                    f"Confidence score {op.confidence.confidence} must be between 0.0 and 1.0."
                )

    def _validate_consistency(self, delta: WorldStateDelta, state: WorldState) -> None:
        # Check referential integrity
        for op in delta.operations:
            if op.operation in [Operation.UPDATE, Operation.REMOVE]:
                # We should conceptually verify the entity exists in the state
                pass  # Deferred for deeper implementation

            if op.operation == Operation.LINK:
                # E.g., Character -> Activity link
                # Verify both exist
                pass  # Deferred
