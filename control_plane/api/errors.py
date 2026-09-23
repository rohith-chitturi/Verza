from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from contracts.schemas.runtime import IllegalStateTransitionError
from control_plane.application.errors import (
    DuplicateWorkflowError,
    RunNotFoundError,
    WorkflowNotFoundError,
)


def register_exception_handlers(app: FastAPI):
    @app.exception_handler(WorkflowNotFoundError)
    async def workflow_not_found_handler(request: Request, exc: WorkflowNotFoundError):
        return JSONResponse(
            status_code=404,
            content={"detail": str(exc)},
        )

    @app.exception_handler(RunNotFoundError)
    async def run_not_found_handler(request: Request, exc: RunNotFoundError):
        return JSONResponse(
            status_code=404,
            content={"detail": str(exc)},
        )

    @app.exception_handler(DuplicateWorkflowError)
    async def duplicate_workflow_handler(request: Request, exc: DuplicateWorkflowError):
        return JSONResponse(
            status_code=409,
            content={"detail": str(exc)},
        )

    @app.exception_handler(IllegalStateTransitionError)
    async def illegal_state_transition_handler(request: Request, exc: IllegalStateTransitionError):
        return JSONResponse(
            status_code=409,
            content={"detail": str(exc)},
        )
