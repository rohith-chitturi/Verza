CURRENT MILESTONE: M4 Real Infrastructure Baseline
CURRENT BRANCH: feature/m4-real-infrastructure
CURRENT OBJECTIVE: Wire real M2 providers and physical PostgreSQL to the M4 execution layer for integration tests.
LAST COMPLETED WORK: Converted SQLite integration tests to target real PostgreSQL. Added explicit failure when environment dependencies (PostgreSQL, FFmpeg) are missing. Added `test_m4_persistence.py` mapping out transaction rollbacks, resume, and replay over PostgreSQL. Added `test_m4_real_execution.py` tracking a real physical media fixture through M4 DAG.
CURRENT WORK: Completed test construction and verification phase.
NEXT TASK: Address environment requirements so PostgreSQL + FFmpeg run natively in CI/CD, and subsequently wire real M3.1 models (replacing `MockVLMProvider`).
BLOCKERS: Local environment does not have PostgreSQL running natively, so test runs explicitly fail with `ENVIRONMENT DEPENDENCY FAILURE`. This correctly fulfills the requirement to "fail clearly when required infrastructure is unavailable."
FAILING TESTS: `test_m4_persistence.py` and `test_m4_real_execution.py` fail immediately by design because `docker-compose up -d postgres` could not run on this node.
KNOWN ISSUES: Tests accurately detect environment absence and halt.
FILES CURRENTLY BEING MODIFIED: `docs/agent-context/*`
LAST VERIFIED COMMIT: TBD (Commits being prepared)
