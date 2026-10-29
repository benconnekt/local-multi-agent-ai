
from unittest.mock import Mock

from app.tools.sandbox.docker_runner import (
    OutputCaptureState,
    _drain_stream,
    MAX_OUTPUT_BYTES,
    ExecutionResult,
)


def test_output_reader_failure_is_recorded():
    stream = Mock()
    stream.read.side_effect = OSError("Simulated read failure")

    buffer = bytearray()
    state = OutputCaptureState()

    _drain_stream(
        stream,
        buffer,
        MAX_OUTPUT_BYTES,
        state,
    )

    assert state.errors
    assert "Simulated read failure" in state.errors[0]


def test_stream_close_failure_is_recorded():
    stream = Mock()
    stream.read.return_value = b""
    stream.close.side_effect = OSError("Simulated close failure")

    buffer = bytearray()
    state = OutputCaptureState()

    _drain_stream(
        stream,
        buffer,
        MAX_OUTPUT_BYTES,
        state,
    )

    assert state.errors
    assert "Stream close failed" in state.errors[0]


def test_capture_failure_blocks_approval():
    result = ExecutionResult(
        exit_code=0,
        stdout="OK",
        stderr="",
        duration_seconds=0.1,
        timed_out=False,
        container_name="test-container",
        cleanup_succeeded=True,
        output_capture_succeeded=False,
    )

    assert not result.passed
