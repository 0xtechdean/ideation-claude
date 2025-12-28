"""Tests for Docker compatibility and build."""

import os
import subprocess
import pytest
from pathlib import Path


class TestDockerfileStructure:
    """Test Dockerfile structure and requirements."""
    
    def test_dockerfile_exists(self):
        """Test that Dockerfile exists."""
        dockerfile = Path(__file__).parent.parent / "Dockerfile"
        assert dockerfile.exists(), "Dockerfile should exist"
    
    def test_dockerfile_has_readme_copy(self):
        """Test that Dockerfile copies README.md."""
        dockerfile = Path(__file__).parent.parent / "Dockerfile"
        content = dockerfile.read_text()
        assert "COPY README.md" in content or "COPY README.md ./" in content, \
            "Dockerfile should copy README.md"
    
    def test_dockerfile_has_src_copy(self):
        """Test that Dockerfile copies src directory."""
        dockerfile = Path(__file__).parent.parent / "Dockerfile"
        content = dockerfile.read_text()
        assert "COPY src/" in content, "Dockerfile should copy src directory"
    
    def test_dockerfile_has_pyproject_copy(self):
        """Test that Dockerfile copies pyproject.toml."""
        dockerfile = Path(__file__).parent.parent / "Dockerfile"
        content = dockerfile.read_text()
        assert "COPY pyproject.toml" in content, "Dockerfile should copy pyproject.toml"
    
    def test_dockerfile_reinstalls_in_final_stage(self):
        """Test that Dockerfile reinstalls package in final stage."""
        dockerfile = Path(__file__).parent.parent / "Dockerfile"
        content = dockerfile.read_text()
        # Should have pip install in final stage
        lines = content.split('\n')
        final_stage_start = False
        has_reinstall = False
        
        for line in lines:
            if 'FROM python' in line and 'as builder' not in line:
                final_stage_start = True
            if final_stage_start and 'pip install' in line and '-e' in line:
                has_reinstall = True
        
        assert has_reinstall, "Dockerfile should reinstall package in final stage"


class TestDockerBuildRequirements:
    """Test that files required for Docker build exist."""
    
    def test_readme_exists(self):
        """Test that README.md exists (required by pyproject.toml)."""
        readme = Path(__file__).parent.parent / "README.md"
        assert readme.exists(), "README.md should exist for Docker build"
    
    def test_pyproject_exists(self):
        """Test that pyproject.toml exists."""
        pyproject = Path(__file__).parent.parent / "pyproject.toml"
        assert pyproject.exists(), "pyproject.toml should exist"
    
    def test_src_directory_exists(self):
        """Test that src directory exists."""
        src_dir = Path(__file__).parent.parent / "src"
        assert src_dir.exists() and src_dir.is_dir(), "src directory should exist"
    
    def test_main_module_exists(self):
        """Test that main module exists."""
        main_module = Path(__file__).parent.parent / "src" / "ideation_claude" / "main.py"
        assert main_module.exists(), "main.py should exist"


class TestDockerIgnore:
    """Test .dockerignore file."""
    
    def test_dockerignore_exists(self):
        """Test that .dockerignore exists."""
        dockerignore = Path(__file__).parent.parent / ".dockerignore"
        assert dockerignore.exists(), ".dockerignore should exist"
    
    def test_dockerignore_excludes_venv(self):
        """Test that .dockerignore excludes virtual environments."""
        dockerignore = Path(__file__).parent.parent / ".dockerignore"
        content = dockerignore.read_text()
        # Should exclude common venv patterns
        assert any(pattern in content for pattern in ['.venv', 'venv', '__pycache__']), \
            ".dockerignore should exclude virtual environments"


class TestModuleImports:
    """Test that modules can be imported (Docker compatibility)."""
    
    def test_main_module_import(self):
        """Test that main module can be imported."""
        try:
            from ideation_claude.main import cli, main
            assert callable(cli)
            assert callable(main)
        except ImportError as e:
            pytest.fail(f"Failed to import main module: {e}")
    
    def test_orchestrator_module_import(self):
        """Test that orchestrator module can be imported."""
        try:
            from ideation_claude.orchestrator import evaluate_idea, evaluate_ideas
            assert callable(evaluate_idea)
            assert callable(evaluate_ideas)
        except ImportError as e:
            pytest.fail(f"Failed to import orchestrator module: {e}")
    
    def test_memory_module_import(self):
        """Test that memory module can be imported."""
        try:
            from ideation_claude.memory import get_memory
            assert callable(get_memory)
        except ImportError as e:
            pytest.fail(f"Failed to import memory module: {e}")
    
    def test_monitoring_module_import(self):
        """Test that monitoring module can be imported."""
        try:
            from ideation_claude.monitoring import PipelineMonitor
            assert PipelineMonitor is not None
        except ImportError as e:
            pytest.fail(f"Failed to import monitoring module: {e}")


class TestPackageStructure:
    """Test package structure for Docker compatibility."""
    
    def test_package_has_init(self):
        """Test that package has __init__.py."""
        init_file = Path(__file__).parent.parent / "src" / "ideation_claude" / "__init__.py"
        assert init_file.exists(), "Package should have __init__.py"
    
    def test_entry_point_defined(self):
        """Test that entry point is defined in pyproject.toml."""
        pyproject = Path(__file__).parent.parent / "pyproject.toml"
        content = pyproject.read_text()
        assert 'ideation-claude' in content, "pyproject.toml should define ideation-claude entry point"
        assert 'ideation_claude.main:cli' in content, "Entry point should point to main:cli"

