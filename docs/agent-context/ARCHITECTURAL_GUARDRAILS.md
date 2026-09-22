# ARCHITECTURAL GUARDRAILS

To preserve Verza's modularity, the following rules MUST be strictly followed:

## 1. Provider Abstraction Principle
```text
Domain / Capability -> Interface -> Concrete Provider Implementation
```
**NOT:**
```text
Domain / Capability -> Concrete Provider (e.g. OpenAI)
```
If a Capability requires a Language Model, it injects `VLMProvider`, not the OpenAI SDK.

## 2. WorldState Mutation Pipeline
```text
Capability -> WorldStateDelta -> Validator -> Consistency Checker -> Merger -> New Immutable WorldState
```
**NOT:**
```text
Capability -> Mutate WorldState variables directly
```
The WorldState is immutable. All updates are deterministic and pass through the state machine.

## 3. Dependency Injection Flow
```text
Workflow -> Capability Registry -> DI Container -> Capability -> Interface -> Provider
```
Manual instantiation of services deep in the domain logic is strictly prohibited. Everything must be declared in `bootstrap/container.py` and resolved automatically.

## 4. Asynchronous Boundary (Events)
If a side-effect needs to occur (e.g. Logging, Telemetry, triggering a downstream webhook), it should be done by publishing an Event to the Event Bus, NOT by calling the side-effect inline within the workflow runtime.
