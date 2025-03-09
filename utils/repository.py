#!/usr/bin/env python3
import os
import shutil
import tempfile
import logging
import git
import time

logger = logging.getLogger("SAST_Agent.repository")

class Repository:
    """Class for repository operations"""
    
    def __init__(self, clone_timeout=300):
        """
        Initialize repository handler
        
        Args:
            clone_timeout (int): Timeout for clone operations in seconds
        """
        self.clone_timeout = clone_timeout
        self.temp_dirs = []
        
    def clone(self, repo_url, branch=None, depth=None):
        """
        Clone a Git repository
        
        Args:
            repo_url (str): URL of the repository to clone
            branch (str): Branch to clone (default: None for default branch)
            depth (int): Depth of history to clone (default: None for full history)
            
        Returns:
            str: Path to cloned repository or None if failed
        """
        temp_dir = tempfile.mkdtemp(prefix="sast_repo_")
        self.temp_dirs.append(temp_dir)
        logger.info(f"Cloning repository {repo_url} into {temp_dir}")
        
        start_time = time.time()
        
        try:
            # Prepare clone options
            clone_kwargs = {}
            if branch:
                clone_kwargs['branch'] = branch
            if depth:
                clone_kwargs['depth'] = depth
                
            # Monitor timeout
            remaining_timeout = self.clone_timeout - (time.time() - start_time)
            if remaining_timeout <= 0:
                raise TimeoutError("Clone operation timed out during setup")
                
            # Clone the repository with timeout monitoring
            process = None
            repo = git.Repo.clone_from(repo_url, temp_dir, **clone_kwargs)
            
            logger.info(f"Repository cloned successfully in {time.time() - start_time:.2f} seconds")
            return temp_dir
            
        except git.GitCommandError as e:
            logger.error(f"Git error cloning repository: {e}")
            self.cleanup(temp_dir)
            return None
        except TimeoutError as e:
            logger.error(f"Timeout cloning repository: {e}")
            self.cleanup(temp_dir)
            return None
        except Exception as e:
            logger.error(f"Error cloning repository: {e}")
            self.cleanup(temp_dir)
            return None
            
    def cleanup(self, repo_path=None):
        """
        Clean up temporary directories
        
        Args:
            repo_path (str): Specific repository path to clean up (default: None for all)
        """
        if repo_path:
            if os.path.exists(repo_path):
                logger.info(f"Cleaning up repository: {repo_path}")
                shutil.rmtree(repo_path, ignore_errors=True)
                if repo_path in self.temp_dirs:
                    self.temp_dirs.remove(repo_path)
        else:
            for temp_dir in self.temp_dirs[:]:  # Create a copy to avoid modification during iteration
                if os.path.exists(temp_dir):
                    logger.info(f"Cleaning up repository: {temp_dir}")
                    shutil.rmtree(temp_dir, ignore_errors=True)
                self.temp_dirs.remove(temp_dir)
                
    def __del__(self):
        """Clean up on object destruction"""
        self.cleanup()
