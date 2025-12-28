"""Tests for monitoring module."""

import json
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from ideation_claude.monitoring import (
    EvaluationMetrics,
    Phase,
    PhaseMetrics,
    PipelineMonitor,
    Status,
)


class TestPhaseMetrics:
    """Tests for PhaseMetrics."""

    def test_phase_metrics_creation(self):
        """Test creating PhaseMetrics."""
        metrics = PhaseMetrics(phase=Phase.RESEARCH)
        assert metrics.phase == Phase.RESEARCH
        assert metrics.status == Status.PENDING
        assert metrics.api_calls == 0

    def test_phase_metrics_start(self):
        """Test starting a phase."""
        metrics = PhaseMetrics(phase=Phase.RESEARCH)
        metrics.start()
        assert metrics.status == Status.RUNNING
        assert metrics.start_time is not None

    def test_phase_metrics_complete(self):
        """Test completing a phase."""
        metrics = PhaseMetrics(phase=Phase.RESEARCH)
        metrics.start()
        time.sleep(0.01)  # Small delay to ensure duration > 0
        metrics.complete(api_calls=1, tokens_used=1000)
        assert metrics.status == Status.COMPLETED
        assert metrics.duration is not None
        assert metrics.duration > 0
        assert metrics.api_calls == 1
        assert metrics.tokens_used == 1000

    def test_phase_metrics_fail(self):
        """Test failing a phase."""
        metrics = PhaseMetrics(phase=Phase.RESEARCH)
        metrics.start()
        metrics.fail("Test error")
        assert metrics.status == Status.FAILED
        assert metrics.error == "Test error"
        assert metrics.duration is not None

    def test_phase_metrics_skip(self):
        """Test skipping a phase."""
        metrics = PhaseMetrics(phase=Phase.RESEARCH)
        metrics.skip()
        assert metrics.status == Status.SKIPPED


class TestEvaluationMetrics:
    """Tests for EvaluationMetrics."""

    def test_evaluation_metrics_creation(self):
        """Test creating EvaluationMetrics."""
        metrics = EvaluationMetrics(topic="Test Idea", threshold=5.0)
        assert metrics.topic == "Test Idea"
        assert metrics.threshold == 5.0
        assert metrics.start_time is not None

    def test_add_phase(self):
        """Test adding phase metrics."""
        metrics = EvaluationMetrics(topic="Test Idea", threshold=5.0)
        phase_metrics = PhaseMetrics(phase=Phase.RESEARCH)
        metrics.add_phase(Phase.RESEARCH, phase_metrics)
        assert Phase.RESEARCH.value in metrics.phases

    def test_complete(self):
        """Test completing evaluation."""
        metrics = EvaluationMetrics(topic="Test Idea", threshold=5.0)
        metrics.complete(final_score=6.5, eliminated=False)
        assert metrics.end_time is not None
        assert metrics.total_duration is not None
        assert metrics.final_score == 6.5
        assert metrics.eliminated is False

    def test_to_dict(self):
        """Test converting to dictionary."""
        metrics = EvaluationMetrics(topic="Test Idea", threshold=5.0)
        phase_metrics = PhaseMetrics(phase=Phase.RESEARCH)
        phase_metrics.start()
        phase_metrics.complete(api_calls=1)
        metrics.add_phase(Phase.RESEARCH, phase_metrics)
        metrics.complete(final_score=6.5, eliminated=False)
        
        data = metrics.to_dict()
        assert data["topic"] == "Test Idea"
        assert data["final_score"] == 6.5
        assert "phases" in data

    def test_save_json(self, tmp_path):
        """Test saving metrics to JSON."""
        metrics = EvaluationMetrics(topic="Test Idea", threshold=5.0)
        metrics.complete(final_score=6.5, eliminated=False)
        
        output_file = tmp_path / "metrics.json"
        metrics.save_json(output_file)
        
        assert output_file.exists()
        data = json.loads(output_file.read_text())
        assert data["topic"] == "Test Idea"
        assert data["final_score"] == 6.5


class TestPipelineMonitor:
    """Tests for PipelineMonitor."""

    def test_monitor_initialization(self):
        """Test monitor initialization."""
        monitor = PipelineMonitor("Test Idea", 5.0, verbose=False)
        assert monitor.metrics.topic == "Test Idea"
        assert monitor.metrics.threshold == 5.0
        assert monitor.verbose is False

    def test_start_phase(self):
        """Test starting a phase."""
        monitor = PipelineMonitor("Test Idea", 5.0, verbose=False)
        metrics = monitor.start_phase(Phase.RESEARCH)
        assert metrics.phase == Phase.RESEARCH
        assert metrics.status == Status.RUNNING
        assert Phase.RESEARCH.value in monitor.metrics.phases

    def test_complete_phase(self):
        """Test completing a phase."""
        monitor = PipelineMonitor("Test Idea", 5.0, verbose=False)
        monitor.start_phase(Phase.RESEARCH)
        monitor.complete_phase(Phase.RESEARCH, api_calls=1, tokens_used=1000)
        
        phase_metrics = monitor.metrics.phases[Phase.RESEARCH.value]
        assert phase_metrics.status == Status.COMPLETED
        assert phase_metrics.api_calls == 1

    def test_complete_evaluation(self, tmp_path):
        """Test completing evaluation."""
        monitor = PipelineMonitor("Test Idea", 5.0, verbose=False, output_dir=tmp_path)
        monitor.start_phase(Phase.RESEARCH)
        monitor.complete_phase(Phase.RESEARCH)
        monitor.complete_evaluation(final_score=6.5, eliminated=False)
        
        assert monitor.metrics.final_score == 6.5
        assert monitor.metrics.eliminated is False
        
        # Check metrics file was created
        metrics_dir = tmp_path / "metrics"
        assert metrics_dir.exists()
        metrics_files = list(metrics_dir.glob("*_metrics.json"))
        assert len(metrics_files) > 0

    def test_context_manager(self):
        """Test using monitor as context manager."""
        with PipelineMonitor("Test Idea", 5.0, verbose=False) as monitor:
            assert monitor is not None
            monitor.start_phase(Phase.RESEARCH)
            monitor.complete_phase(Phase.RESEARCH)

