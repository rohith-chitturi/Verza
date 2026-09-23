class DomainError(Exception):
    """Base class for all application/domain errors."""
    pass


class WorkflowNotFoundError(DomainError):
    def __init__(self, name: str, version: str):
        super().__init__(f"Workflow {name} v{version} not found.")


class RunNotFoundError(DomainError):
    def __init__(self, run_id: str):
        super().__init__(f"Run {run_id} not found.")


class DuplicateWorkflowError(DomainError):
    def __init__(self, name: str, version: str):
        super().__init__(f"Workflow {name} v{version} already exists.")
