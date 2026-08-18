from contracts.schemas.result import ExecutionResult


def test_execution_result_defaults():
    """Test that ExecutionResult initializes with default metadata and errors."""
    result = ExecutionResult(
        success=True, duration_ms=100, provider="test_provider", model="test_model"
    )

    assert result.success is True
    assert result.duration_ms == 100
    assert result.provider == "test_provider"
    assert result.model == "test_model"
    assert result.metadata == {}
    assert result.warnings == []
    assert result.errors == []
