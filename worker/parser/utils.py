# backend/worker/parser/utils.py
import os
import shutil
import subprocess
from git import Repo
from git.exc import GitCommandError, InvalidGitRepositoryError

def clone_repo(repo_url: str, dest_dir: str, branch: str = "main", depth: int = 1):
    """
    Clone a git repository using GitPython with subprocess fallback.
    
    Args:
        repo_url (str): The URL of the repository to clone
        dest_dir (str): Destination directory for the cloned repository
        branch (str): Branch to clone (default: 'main')
        depth (int): Depth for shallow clone (default: 1)
    
    Returns:
        str: Path to the cloned repository
    
    Raises:
        Exception: If both GitPython and subprocess git commands fail
    """
    # Remove destination directory if it exists
    if os.path.exists(dest_dir):
        try:
            shutil.rmtree(dest_dir)
        except OSError as e:
            raise Exception(f"Failed to remove existing directory '{dest_dir}': {e}")
    
    # Create destination directory
    try:
        os.makedirs(dest_dir, exist_ok=True)
    except OSError as e:
        raise Exception(f"Failed to create destination directory '{dest_dir}': {e}")
    
    # Try GitPython first
    try:
        Repo.clone_from(repo_url, dest_dir, branch=branch, depth=depth)
        return dest_dir
    except (GitCommandError, InvalidGitRepositoryError) as e:
        print(f"GitPython failed: {e}. Falling back to subprocess git command...")
    except Exception as e:
        print(f"GitPython failed with unexpected error: {e}. Falling back to subprocess git command...")
    
    # Fallback to subprocess git if GitPython fails
    try:
        subprocess.check_call(
            ["git", "clone", "--depth", str(depth), "-b", branch, repo_url, dest_dir],
            stderr=subprocess.STDOUT
        )
        return dest_dir
    except subprocess.CalledProcessError as e:
        # Clean up partial clone on failure
        if os.path.exists(dest_dir):
            shutil.rmtree(dest_dir)
        raise Exception(
            f"Failed to clone repository '{repo_url}' to '{dest_dir}' on branch '{branch}'. "
            f"Git command failed with exit code {e.returncode}. "
            f"Please check if the repository URL is valid and the branch exists."
        )
    except FileNotFoundError:
        # Clean up on failure
        if os.path.exists(dest_dir):
            shutil.rmtree(dest_dir)
        raise Exception(
            "Git command not found. Please ensure Git is installed and available in your PATH."
        )
