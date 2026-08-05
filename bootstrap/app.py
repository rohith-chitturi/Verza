from fastapi import FastAPI, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from bootstrap.container import VerzaContainer
from core.telemetry.logging import configure_logging, get_logger

# Configure logging before app starts
configure_logging()
logger = get_logger("bootstrap.app")

app = FastAPI(title="Verza Platform API")
container = VerzaContainer()
app.container = container

@app.get("/health")
def health_check():
    """Basic liveness check."""
    return {"status": "ok"}

@app.get("/ready")
def readiness_check():
    """Check if dependencies are available."""
    # Example: could ping Postgres or Redis here.
    return {"status": "ready"}

@app.get("/live")
def liveness_check():
    """Process alive."""
    return {"status": "alive"}

@app.get("/metrics")
def metrics():
    """Prometheus metrics endpoint."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

if __name__ == "__main__":
    import uvicorn
    logger.info("verza_api_starting")
    uvicorn.run(app, host="0.0.0.0", port=8000)
