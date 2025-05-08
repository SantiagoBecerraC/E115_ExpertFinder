import pytest
import os
import json
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import subprocess
from utils.dvc_utils import DVCManager

@pytest.mark.unit
def test_dvc_manager_initialization():
    """Test DVCManager initialization."""
    # Mock Path.exists to return True for .git directory checks
    with patch('pathlib.Path.exists', return_value=True), \
         patch('pathlib.Path.mkdir'):
        
        # Initialize DVCManager
        dvc_manager = DVCManager()
        
        # Check basic properties
        assert dvc_manager.project_root is not None
        assert dvc_manager.db_path is not None
        assert isinstance(dvc_manager.dvc_file, str)

@pytest.mark.unit
def test_run_command():
    """Test the _run_command method."""
    # Mock subprocess.run
    mock_process = MagicMock()
    mock_process.stdout = "Command output"
    mock_process.stderr = ""
    
    with patch('subprocess.run', return_value=mock_process) as mock_run, \
         patch('pathlib.Path.exists', return_value=True), \
         patch('pathlib.Path.mkdir'):
        
        dvc_manager = DVCManager()
        
        # Test a successful command
        result = dvc_manager._run_command(['test', 'command'], "test description")
        
        # Verify subprocess.run was called with the right arguments
        mock_run.assert_called_once()
        args, kwargs = mock_run.call_args
        assert args[0] == ['test', 'command']
        assert kwargs['cwd'] == str(dvc_manager.project_root)
        assert kwargs['check'] is True
        assert kwargs['capture_output'] is True or (kwargs.get('stdout') is not None and kwargs.get('stderr') is not None)
        
        # Check the result
        assert result is True
        
        # Test with a failing command
        mock_run.reset_mock()
        mock_run.side_effect = subprocess.CalledProcessError(1, 'cmd', "Error output")
        
        result = dvc_manager._run_command(['failing', 'command'], "failing test")
        
        # Verify subprocess.run was called
        mock_run.assert_called_once()
        
        # Check the result of a failed command
        assert result is False

@pytest.mark.unit
def test_version_database():
    """Test the version_database method."""
    update_info = {
        'profiles_added': 100,
        'source': 'test'
    }
    
    with patch('pathlib.Path.exists', return_value=True), \
         patch('pathlib.Path.mkdir'), \
         patch.object(DVCManager, '_run_command', return_value=True) as mock_run:
        
        dvc_manager = DVCManager()
        
        # Call the version_database method
        result = dvc_manager.version_database(update_info)
        
        # Check it returned success
        assert result is True
        
        # Verify the right commands were run
        assert mock_run.call_count == 3
        commands = [call[0][0] for call in mock_run.call_args_list]
        
        # First command should be dvc add
        assert commands[0][0] == 'dvc'
        assert commands[0][1] == 'add'
        
        # Second command should be git add
        assert commands[1][0] == 'git'
        assert commands[1][1] == 'add'
        
        # Third command should be git commit
        assert commands[2][0] == 'git'
        assert commands[2][1] == 'commit'
        assert '-m' in commands[2]
        commit_message = commands[2][3]
        assert 'profiles' in commit_message
        assert 'test' in commit_message  # Source should be in commit message

@pytest.mark.unit
def test_restore_version():
    """Test the restore_version method."""
    test_commit = "abcd1234"
    
    with patch('pathlib.Path.exists', return_value=True), \
         patch('pathlib.Path.mkdir'), \
         patch.object(DVCManager, '_run_command', return_value=True) as mock_run:
        
        dvc_manager = DVCManager()
        
        # Call restore_version
        result = dvc_manager.restore_version(test_commit)
        
        # Check it returned success
        assert result is True
        
        # Verify the right commands were run
        assert mock_run.call_count == 2
        commands = [call[0][0] for call in mock_run.call_args_list]
        
        # First command should be git checkout
        assert commands[0][0] == 'git'
        assert commands[0][1] == 'checkout'
        assert test_commit in commands[0]  # Commit hash should be in command
        
        # Second command should be dvc checkout
        assert commands[1][0] == 'dvc'
        assert commands[1][1] == 'checkout'

@pytest.mark.unit
def test_get_version_history():
    """Test the get_version_history method."""
    # Mock subprocess.run to return a sample git log output
    mock_process = MagicMock()
    mock_process.stdout = (
        "abc123|2025-01-01 12:00:00 -0400|Version 1\n"
        "def456|2025-01-02 12:00:00 -0400|Version 2"
    )
    
    with patch('subprocess.run', return_value=mock_process), \
         patch('pathlib.Path.exists', return_value=True), \
         patch('pathlib.Path.mkdir'):
        
        dvc_manager = DVCManager()
        
        # Get version history
        history = dvc_manager.get_version_history(max_entries=2)
        
        # Check the structure and content of the history
        assert isinstance(history, list)
        assert len(history) == 2
        
        # Check first entry
        assert history[0]['commit_hash'] == 'abc123'
        assert '2025-01-01' in history[0]['date']
        assert history[0]['message'] == 'Version 1'
        
        # Check second entry
        assert history[1]['commit_hash'] == 'def456'
        assert '2025-01-02' in history[1]['date']
        assert history[1]['message'] == 'Version 2'

@pytest.mark.unit
def test_setup_remote():
    """Test the setup_remote method."""
    test_remote_url = "gs://test-bucket/dvc-store"
    
    # First case: remote doesn't exist yet
    with patch('pathlib.Path.exists', return_value=True), \
         patch('pathlib.Path.mkdir'), \
         patch('subprocess.run') as mock_run:
        
        # Mock list remotes - empty result
        mock_process_empty = MagicMock()
        mock_process_empty.stdout = ""
        
        # Set up sequence of return values
        mock_run.side_effect = [
            mock_process_empty,  # First call - list remotes
            MagicMock()  # Second call - add remote
        ]
        
        dvc_manager = DVCManager()
        
        # Set up the remote
        result = dvc_manager.setup_remote(test_remote_url)
        
        # Check result
        assert result is True
        
        # Verify commands
        assert mock_run.call_count == 2
        args_list = [call[0][0] for call in mock_run.call_args_list]
        
        # First call should check existing remotes
        assert args_list[0] == ['dvc', 'remote', 'list']
        
        # Second call should add the remote
        assert args_list[1][0:4] == ['dvc', 'remote', 'add', '-d']
        assert args_list[1][5] == test_remote_url
    
    # Second case: remote already exists
    with patch('pathlib.Path.exists', return_value=True), \
         patch('pathlib.Path.mkdir'), \
         patch('subprocess.run') as mock_run:
        
        # Mock list remotes - shows storage already exists
        mock_process_exists = MagicMock()
        mock_process_exists.stdout = "storage\ts3://already-exists"
        
        mock_run.return_value = mock_process_exists
        
        dvc_manager = DVCManager()
        
        # Try to set up the remote
        result = dvc_manager.setup_remote(test_remote_url)
        
        # Should return True but not add the remote
        assert result is True
        
        # Verify only the check command was run
        assert mock_run.call_count == 1
        args = mock_run.call_args[0][0]
        assert args == ['dvc', 'remote', 'list']
