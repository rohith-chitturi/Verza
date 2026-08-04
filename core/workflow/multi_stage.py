import sys
import os
import uuid
import time

# Add workspace roots to path for M1 execution
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from bootstrap.container import VerzaContainer
from contracts.schemas.context import AIContext
from contracts.events.base import WorkflowStarted
from core.telemetry.logging import configure_logging, get_logger

def run_m1_prototype():
    configure_logging()
    logger = get_logger("workflow.engine")
    
    logger.info("m1_workflow_starting")
    
    # Initialize DI Container
    container = VerzaContainer()
    
    event_bus = container.event_bus()
    speech_cap = container.speech_recognition_capability()
    
    scene_cap = container.scene_analysis_capability()
    trans_cap = container.translation_capability()
    tts_cap = container.tts_capability()
    
    trace_id = str(uuid.uuid4())
    workflow_id = "WF-M1-001"
    
    # Subscribe to Event Bus to prove events are working
    event_bus.subscribe("StageFinished", lambda ev: logger.info("event_received", event_type="StageFinished", stage=ev.stage_name, duration_ms=ev.duration_ms))
    
    # 1. Start Workflow
    event_bus.publish(WorkflowStarted(
        workflow_id=workflow_id,
        trace_id=trace_id,
        correlation_id="corr-m1",
        tenant_id="tenant-local"
    ))
    
    # 2. Setup AI Context
    context = AIContext(
        tenant_id="tenant-local",
        workflow_id=workflow_id,
        language="en",
        scene="indoor_conversation"
    )
    
    # 3. Simulate Pipeline
    logger.info("branch_starting", branch="scene_analysis", trace_id=trace_id)
    scene_result = scene_cap.execute(context, trace_id=trace_id)
    
    logger.info("branch_starting", branch="speech_recognition", trace_id=trace_id)
    speech_result = speech_cap.execute("sample_audio.wav", context, trace_id)
    
    logger.info("branch_starting", branch="translation", trace_id=trace_id)
    trans_result = trans_cap.execute(speech_result.transcript, context, trace_id=trace_id)
    
    logger.info("branch_starting", branch="tts", trace_id=trace_id)
    tts_result = tts_cap.execute(trans_result, context, trace_id=trace_id)
    
    # 4. Simulate Parallel Branch: Evaluation
    logger.info("branch_starting", branch="evaluation", trace_id=trace_id)
    time.sleep(0.1)
    
    logger.info(
        "m1_workflow_completed",
        trace_id=trace_id,
        final_transcript=speech_result.transcript,
        confidence=speech_result.confidence
    )

if __name__ == "__main__":
    run_m1_prototype()
