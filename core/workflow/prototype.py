import sys
import os

# Add workspace roots to path for M0 prototype execution
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from core.event_bus.bus import EventBus
from capabilities.speech_recognition import SpeechRecognitionCapability
from providers.speech.whisper.provider import WhisperRecognizer

def run_m0_prototype():
    print("=== Verza M0 Prototype Executing ===\n")
    
    # 1. Initialize Event Bus
    bus = EventBus()
    bus.subscribe("WorkflowStarted", lambda payload: print(f"Received WorkflowStarted: {payload}"))
    
    bus.publish("WorkflowStarted", {"workflow_id": "WF-001"})
    
    # 2. Setup AI Context
    context = {
        "tenant_id": "TENANT-001",
        "language": "en",
        "scene": "outdoor"
    }
    
    # 3. Load Provider (Reference)
    provider = WhisperRecognizer()
    
    # 4. Load Capability
    capability = SpeechRecognitionCapability(provider)
    
    # 5. Execute Capability (End-to-End Prototype)
    transcript = capability.execute("sample_audio.wav", context)
    
    print(f"\nFinal Result: {transcript}")
    print("\n=== Verza M0 Prototype Completed ===")

if __name__ == "__main__":
    run_m0_prototype()
