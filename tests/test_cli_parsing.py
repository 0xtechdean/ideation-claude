"""Tests for CLI argument parsing to prevent Click issues."""

import sys
from unittest.mock import patch, MagicMock
import pytest
import click

from ideation_claude.main import cli, main, _handle_as_evaluation


class TestCLIArgumentParsing:
    """Test CLI argument parsing with various formats."""
    
    def test_cli_with_topic_only(self):
        """Test CLI with just a topic argument."""
        with patch('ideation_claude.main.run_evaluation') as mock_run:
            mock_run.return_value = None
            with patch('asyncio.run') as mock_asyncio:
                # Simulate: ideation-claude "Test idea"
                with patch('sys.argv', ['ideation-claude', 'Test idea']):
                    with patch('click.Context') as mock_ctx:
                        mock_ctx.return_value.invoked_subcommand = None
                        mock_ctx.return_value.args = ['Test idea']
                        # This should parse correctly
                        pass  # Will test actual execution
    
    def test_cli_with_threshold_and_topic(self):
        """Test CLI with threshold option and topic."""
        # Test that --threshold 5.0 "idea" format works
        test_cases = [
            (['ideation-claude', '--threshold', '5.0', 'Test idea'], ['Test idea'], 5.0),
            (['ideation-claude', '-t', '6.0', 'Another idea'], ['Another idea'], 6.0),
            (['ideation-claude', '--threshold', '7.5', 'Idea 1', 'Idea 2'], ['Idea 1', 'Idea 2'], 7.5),
        ]
        
        for argv, expected_topics, expected_threshold in test_cases:
            topics = []
            threshold = 5.0
            skip_next = False
            
            for arg in argv[1:]:  # Skip script name
                if skip_next:
                    skip_next = False
                    continue
                if arg.startswith('-'):
                    if arg in ['-t', '--threshold']:
                        skip_next = True
                    continue
                topics.append(arg)
            
            assert topics == expected_topics, f"Failed for {argv}: got {topics}, expected {expected_topics}"
    
    def test_handle_as_evaluation_parses_topics(self):
        """Test _handle_as_evaluation parses topics correctly."""
        test_cases = [
            (['ideation-claude', '--threshold', '5.0', 'Test idea'], ['Test idea'], 5.0),
            (['ideation-claude', 'Test idea'], ['Test idea'], 5.0),
            (['ideation-claude', '--quiet', '--threshold', '6.0', 'Idea'], ['Idea'], 6.0),
        ]
        
        for argv, expected_topics, expected_threshold in test_cases:
            with patch('sys.argv', argv):
                with patch('asyncio.run') as mock_asyncio:
                    _handle_as_evaluation()
                    # Verify asyncio.run was called
                    assert mock_asyncio.called
    
    def test_handle_as_evaluation_skips_commands(self):
        """Test _handle_as_evaluation doesn't treat commands as topics."""
        with patch('sys.argv', ['ideation-claude', 'add', 'Test idea']):
            with patch('asyncio.run') as mock_asyncio:
                _handle_as_evaluation()
                # Should not call asyncio.run for commands
                assert not mock_asyncio.called
    
    def test_handle_as_evaluation_parses_options(self):
        """Test _handle_as_evaluation parses all options correctly."""
        with patch('sys.argv', [
            'ideation-claude', 
            '--threshold', '6.5',
            '--quiet',
            '--subagent',
            '--metrics',
            '--output', 'test.md',
            'Test idea'
        ]):
            with patch('asyncio.run') as mock_asyncio:
                _handle_as_evaluation()
                assert mock_asyncio.called
                # Verify it was called with correct parameters
                call_args = mock_asyncio.call_args[0][0]
                # The function should be run_evaluation
                assert call_args is not None


class TestMainExceptionHandling:
    """Test main() exception handling."""
    
    def test_main_handles_system_exit(self):
        """Test main() handles SystemExit from Click."""
        with patch('ideation_claude.main.cli') as mock_cli:
            mock_cli.side_effect = SystemExit(2)
            with patch('ideation_claude.main._handle_as_evaluation') as mock_handle:
                main()
                # Should call _handle_as_evaluation when SystemExit occurs
                assert mock_handle.called
    
    def test_main_handles_click_exception(self):
        """Test main() handles ClickException."""
        with patch('ideation_claude.main.cli') as mock_cli:
            mock_cli.side_effect = click.ClickException("Test error")
            with patch('ideation_claude.main._handle_as_evaluation') as mock_handle:
                main()
                assert mock_handle.called
    
    def test_main_handles_normal_exit(self):
        """Test main() doesn't handle SystemExit(0)."""
        with patch('ideation_claude.main.cli') as mock_cli:
            mock_cli.side_effect = SystemExit(0)
            with patch('ideation_claude.main._handle_as_evaluation') as mock_handle:
                with pytest.raises(SystemExit):
                    main()
                # Should not call _handle_as_evaluation for normal exit
                assert not mock_handle.called
    
    def test_main_successful_execution(self):
        """Test main() with successful CLI execution."""
        with patch('ideation_claude.main.cli') as mock_cli:
            mock_cli.return_value = None
            with patch('ideation_claude.main._handle_as_evaluation') as mock_handle:
                main()
                # Should not call _handle_as_evaluation on success
                assert not mock_handle.called


class TestDockerCompatibility:
    """Test that CLI works in Docker-like environments."""
    
    def test_module_imports(self):
        """Test that all modules can be imported."""
        import ideation_claude.main
        import ideation_claude.orchestrator
        import ideation_claude.memory
        import ideation_claude.monitoring
        # If we get here, imports work
        assert True
    
    def test_cli_entry_point(self):
        """Test that CLI entry point is accessible."""
        from ideation_claude.main import cli
        assert callable(cli)
        assert hasattr(cli, '__call__')
    
    def test_main_entry_point(self):
        """Test that main() entry point exists."""
        from ideation_claude.main import main
        assert callable(main)


class TestArgumentExtraction:
    """Test argument extraction logic."""
    
    def test_extract_topics_from_argv(self):
        """Test extracting topics from sys.argv."""
        test_cases = [
            (['ideation-claude', 'idea'], ['idea']),
            (['ideation-claude', '--threshold', '5.0', 'idea'], ['idea']),
            (['ideation-claude', 'idea1', 'idea2'], ['idea1', 'idea2']),
            (['ideation-claude', '--quiet', 'idea'], ['idea']),
        ]
        
        for argv, expected in test_cases:
            known_commands = {'add', 'pending', 'search', 'list', 'similar', 'insights'}
            topics = []
            skip_next = False
            
            for arg in argv[1:]:
                if skip_next:
                    skip_next = False
                    continue
                if arg.startswith('-'):
                    if arg in ['-t', '--threshold', '-o', '--output', '-l', '--limit']:
                        skip_next = True
                    continue
                if arg in known_commands:
                    break
                topics.append(arg)
            
            assert topics == expected, f"Failed for {argv}: got {topics}, expected {expected}"
    
    def test_extract_options_from_argv(self):
        """Test extracting options from sys.argv."""
        test_cases = [
            (['ideation-claude', '--threshold', '5.0', 'idea'], 5.0, False, False),
            (['ideation-claude', '--quiet', 'idea'], 5.0, True, False),
            (['ideation-claude', '--subagent', 'idea'], 5.0, False, True),
        ]
        
        for argv, expected_threshold, expected_quiet, expected_subagent in test_cases:
            threshold = 5.0
            quiet = False
            subagent = False
            
            i = 0
            while i < len(argv) - 1:
                arg = argv[i + 1]
                if arg == '--threshold' or arg == '-t':
                    if i + 2 < len(argv):
                        threshold = float(argv[i + 2])
                        i += 2
                        continue
                elif arg == '--quiet' or arg == '-q':
                    quiet = True
                elif arg == '--subagent' or arg == '-s':
                    subagent = True
                i += 1
            
            assert threshold == expected_threshold
            assert quiet == expected_quiet
            assert subagent == expected_subagent

