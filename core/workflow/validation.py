from typing import Any
from contracts.schemas.workflow import Workflow

class WorkflowValidationError(Exception):
    pass

class WorkflowValidator:
    """
    Validates a Workflow DAG before execution to ensure referential integrity,
    cycle-free dependencies, and resolvable capabilities.
    """
    
    def __init__(self, registered_capabilities: set[str], registered_providers: set[str]):
        self._registered_capabilities = registered_capabilities
        self._registered_providers = registered_providers

    def validate(self, workflow: Workflow) -> bool:
        self._check_duplicate_ids(workflow)
        self._check_missing_dependencies(workflow)
        self._check_cycles(workflow)
        self._check_capabilities_and_providers(workflow)
        return True

    def _check_duplicate_ids(self, workflow: Workflow) -> None:
        seen = set()
        for stage in workflow.stages:
            if stage.id in seen:
                raise WorkflowValidationError(f"Duplicate stage ID found: {stage.id}")
            seen.add(stage.id)

    def _check_missing_dependencies(self, workflow: Workflow) -> None:
        valid_ids = {stage.id for stage in workflow.stages}
        for stage in workflow.stages:
            for dep in stage.depends_on:
                if dep not in valid_ids:
                    raise WorkflowValidationError(f"Stage '{stage.id}' depends on unknown stage: '{dep}'")

    def _check_cycles(self, workflow: Workflow) -> None:
        graph = {stage.id: stage.depends_on for stage in workflow.stages}
        visited = set()
        path = set()
        
        def visit(node: str) -> None:
            if node in path:
                raise WorkflowValidationError(f"Circular dependency detected involving stage: '{node}'")
            if node in visited:
                return
                
            path.add(node)
            for neighbor in graph.get(node, []):
                visit(neighbor)
            path.remove(node)
            visited.add(node)
            
        for node in graph:
            visit(node)

    def _check_capabilities_and_providers(self, workflow: Workflow) -> None:
        for stage in workflow.stages:
            if stage.capability not in self._registered_capabilities:
                raise WorkflowValidationError(f"Stage '{stage.id}' requires unknown capability: '{stage.capability}'")
                
            policy = stage.provider_policy
            if policy.primary not in self._registered_providers:
                raise WorkflowValidationError(f"Stage '{stage.id}' requires unknown primary provider: '{policy.primary}'")
            for fallback in policy.fallback:
                if fallback not in self._registered_providers:
                    raise WorkflowValidationError(f"Stage '{stage.id}' requires unknown fallback provider: '{fallback}'")
