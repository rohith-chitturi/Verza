import os

from celery import Celery  # type: ignore[import-untyped]

from bootstrap.container import VerzaContainer

# Setup the DI container
container = VerzaContainer()

# Fallback to local redis if not in environment
REDIS_URL = os.environ.get("VERZA_REDIS_URL", "redis://localhost:6379/0")

# Initialize Celery Application
celery_app = Celery(
    "verza_worker",
    broker=REDIS_URL,
    backend=REDIS_URL
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Rule 4: Separation of Retry Semantics
    # We disable Celery's implicit retries in favor of Verza's RetryPolicy
    task_acks_late=True,          # Acknowledge after execution ensures worker crash redelivers
    task_reject_on_worker_lost=True, 
    worker_prefetch_multiplier=1  # Prevent one worker hoarding long tasks
)

# We will define the tasks dynamically or register them here later.
# For now, we just expose celery_app for the infrastructure boundary.
