"""
Utility class for managing DVC operations for ChromaDB versioning.
"""

import os
import subprocess
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DVCManager:
    """
    Manages DVC operations for version controlling the ChromaDB database.
    Only versions the database after significant updates, not individual profile additions.
    """
    
    def __init__(self):
        """Initialize the DVC manager."""
        # Find project root (where .git is located)
        self.project_root = self._find_project_root()
        
        # ChromaDB path - default to project_root/chromadb
        # This should match the path in chroma_db_utils.py
        self.db_path = self.project_root / 'chromadb'
        self.dvc_file = f"{self.db_path.name}.dvc"
        
        # Make sure the path exists
        self.db_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize DVC if needed
        self._initialize_dvc()
    
    def _find_project_root(self) -> Path:
        """Find the project root directory (where .git is located)."""
        current_path = Path(__file__).resolve().parent
        
        # Go up the directory tree until we find .git
        while current_path != current_path.parent:
            if (current_path / '.git').exists():
                return current_path
            current_path = current_path.parent
        
        # If we didn't find .git, use the parent of the backend directory
        return Path(__file__).resolve().parent.parent.parent
    
    def _initialize_dvc(self):
        """Initialize DVC if not already initialized."""
        dvc_dir = self.project_root / '.dvc'
        
        if not dvc_dir.exists():
            logger.info("Initializing DVC repository...")
            self._run_command(['dvc', 'init'], "initialize DVC")
            
            # Add .dvc directory to git
            self._run_command(['git', 'add', '.dvc', '.dvcignore'], "add DVC to git")
            self._run_command(['git', 'commit', '-m', "Initialize DVC"], "commit DVC initialization")
    
    def _run_command(self, command, description):
        """Run a shell command and log the result."""
        try:
            result = subprocess.run(
                command, 
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                check=True
            )
            logger.info(f"Successfully {description}: {result.stdout}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to {description}: {e.stderr}")
            return False
    
    def setup_remote(self, remote_url=None):
        """
        Set up a remote storage for DVC.
        
        Args:
            remote_url (str): URL for the remote storage.
                              e.g., 'gs://your-bucket/dvc-store'
                              If None, will use the URL from environment variable DVC_REMOTE
        """
        if not remote_url:
            remote_url = os.environ.get('DVC_REMOTE')
            
        if not remote_url:
            logger.warning("No remote URL provided and DVC_REMOTE environment variable not set")
            return False
            
        # Check if remote already exists
        result = subprocess.run(
            ['dvc', 'remote', 'list'], 
            cwd=str(self.project_root),
            capture_output=True,
            text=True
        )
        
        if 'storage' in result.stdout:
            logger.info("Remote 'storage' already exists")
            return True
            
        # Add the remote
        return self._run_command(
            ['dvc', 'remote', 'add', '-d', 'storage', remote_url],
            f"add remote storage at {remote_url}"
        )
    
    def version_database(self, update_info=None):
        """
        Version the ChromaDB database using DVC.
        Should be called after significant database updates, not after each profile addition.
        
        Args:
            update_info (dict): Optional information about the update. 
                              e.g., {'profiles_added': 100, 'source': 'linkedin'}
        """
        if not self.db_path.exists():
            logger.warning(f"Database directory {self.db_path} does not exist")
            return False
        
        # Add database to DVC
        if not self._run_command(['dvc', 'add', str(self.db_path)], "add database to DVC"):
            return False
        
        # Create commit message
        if update_info is None:
            update_info = {}
            
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        profiles_added = update_info.get('profiles_added', 'unknown number of')
        source = update_info.get('source', 'various sources')
        
        commit_message = f"Update vector database with {profiles_added} profiles from {source} - {timestamp}"
        
        # Add to git and commit
        if not self._run_command(['git', 'add', self.dvc_file], "add DVC file to git"):
            return False
            
        if not self._run_command(['git', 'commit', '-m', commit_message], "commit database version"):
            return False
        
        # Push to remote (if configured)
        self._run_command(['dvc', 'push'], "push data to remote")
        
        return True
    
    def restore_version(self, commit_hash):
        """
        Restore the database to a specific version.
        
        Args:
            commit_hash (str): Git commit hash to restore to
        """
        # Checkout the specific version of the DVC file
        if not self._run_command(['git', 'checkout', commit_hash, self.dvc_file], f"checkout version {commit_hash}"):
            return False
        
        # Pull the data associated with that version
        if not self._run_command(['dvc', 'checkout'], "checkout DVC data"):
            return False
            
        return True
    
    def get_version_history(self, max_entries=10):
        """
        Get the version history of the database.
        
        Args:
            max_entries (int): Maximum number of entries to return
            
        Returns:
            List of dictionaries with commit hash, message, and date
        """
        try:
            result = subprocess.run(
                ['git', 'log', '--pretty=format:%H|%ad|%s', '--date=iso', '-n', str(max_entries), '--', self.dvc_file],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                check=True
            )
            
            history = []
            for line in result.stdout.split('\n'):
                if line.strip():
                    parts = line.split('|', 2)
                    if len(parts) == 3:
                        history.append({
                            'commit_hash': parts[0],
                            'date': parts[1],
                            'message': parts[2]
                        })
                        
            return history
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to get version history: {e.stderr}")
            return [] 