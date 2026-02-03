"""
Cross-platform atomic file operations for PowerTrader2.
Ensures data integrity during file writes.
"""

import os
import sys
import tempfile
import json
import logging
from typing import Any, Dict
from pathlib import Path
from filelock import FileLock


def atomic_write_json(path: str, data: Dict[str, Any], use_lock: bool = True) -> None:
    """
    Write JSON data to a file atomically across platforms.
    
    Uses temporary file + atomic rename to prevent corruption.
    Optionally uses file locking to prevent concurrent writes.
    
    Args:
        path: Target file path
        data: Data to write as JSON
        use_lock: Whether to use file locking (default: True)
        
    Raises:
        Exception: If write fails
    """
    logger = logging.getLogger(__name__)
    dir_path = os.path.dirname(path) or "."
    
    # Ensure directory exists
    os.makedirs(dir_path, exist_ok=True)
    
    lock_path = f"{path}.lock"
    lock = FileLock(lock_path, timeout=10) if use_lock else None
    
    try:
        if lock:
            with lock:
                _do_atomic_write(path, data, dir_path, logger)
        else:
            _do_atomic_write(path, data, dir_path, logger)
    except Exception as e:
        logger.error(f"Failed to write {path}: {e}")
        raise


def _do_atomic_write(path: str, data: Dict[str, Any], dir_path: str, logger: logging.Logger) -> None:
    """Internal helper to perform the actual atomic write."""
    # Write to temp file in same directory (ensures same filesystem)
    with tempfile.NamedTemporaryFile(
        mode='w',
        dir=dir_path,
        delete=False,
        encoding='utf-8',
        suffix='.tmp'
    ) as tmp:
        json.dump(data, tmp, indent=2)
        tmp.flush()
        os.fsync(tmp.fileno())  # Force write to disk
        tmp_path = tmp.name
    
    # Atomic rename (platform-specific handling)
    try:
        if sys.platform == "win32":
            # Windows: target must not exist for os.rename
            # Use backup strategy for existing files
            if os.path.exists(path):
                backup = f"{path}.bak"
                # Remove old backup if it exists
                if os.path.exists(backup):
                    os.remove(backup)
                # Move current file to backup
                os.rename(path, backup)
            # Move temp file to target
            os.rename(tmp_path, path)
            # Clean up backup after successful write
            backup = f"{path}.bak"
            if os.path.exists(backup):
                try:
                    os.remove(backup)
                except Exception:
                    pass  # Non-critical if backup cleanup fails
        else:
            # POSIX: os.replace is atomic
            os.replace(tmp_path, path)
        
        logger.debug(f"Atomically wrote {path}")
        
    except Exception as e:
        # Clean up temp file on failure
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass
        raise e


def atomic_read_json(path: str, use_lock: bool = True) -> Dict[str, Any]:
    """
    Read JSON data from a file with optional file locking.
    
    Args:
        path: File path to read from
        use_lock: Whether to use file locking (default: True)
        
    Returns:
        Parsed JSON data as dictionary
        
    Raises:
        FileNotFoundError: If file doesn't exist
        Exception: If read fails
    """
    logger = logging.getLogger(__name__)
    
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")
    
    lock_path = f"{path}.lock"
    lock = FileLock(lock_path, timeout=10) if use_lock else None
    
    try:
        if lock:
            with lock:
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        else:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Failed to read {path}: {e}")
        raise


def append_jsonl(path: str, obj: Dict[str, Any], use_lock: bool = True) -> None:
    """
    Append a JSON object to a JSONL (JSON Lines) file.
    
    Args:
        path: Target file path
        obj: Object to append as JSON
        use_lock: Whether to use file locking (default: True)
        
    Raises:
        Exception: If append fails
    """
    logger = logging.getLogger(__name__)
    dir_path = os.path.dirname(path) or "."
    
    # Ensure directory exists
    os.makedirs(dir_path, exist_ok=True)
    
    lock_path = f"{path}.lock"
    lock = FileLock(lock_path, timeout=10) if use_lock else None
    
    try:
        if lock:
            with lock:
                with open(path, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(obj) + '\n')
                    f.flush()
                    os.fsync(f.fileno())
        else:
            with open(path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(obj) + '\n')
                f.flush()
                os.fsync(f.fileno())
        
        logger.debug(f"Appended to {path}")
        
    except Exception as e:
        logger.error(f"Failed to append to {path}: {e}")
        raise
