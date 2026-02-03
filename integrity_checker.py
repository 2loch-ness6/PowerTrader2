"""
File integrity checker for PowerTrader2 model files.
Uses SHA-256 checksums to detect tampering.
"""

import hashlib
import json
import os
import logging
from pathlib import Path
from typing import Dict, List, Optional


class IntegrityError(Exception):
    """Raised when file integrity check fails."""
    pass


class IntegrityChecker:
    """Manages file integrity checks using SHA-256 checksums."""
    
    CHECKSUM_FILE = "model_checksums.json"
    
    def __init__(self, checksum_file: Optional[str] = None):
        """
        Initialize the integrity checker.
        
        Args:
            checksum_file: Optional custom path for checksum file
        """
        self.checksum_file = checksum_file or self.CHECKSUM_FILE
        self.logger = logging.getLogger(__name__)
    
    def _calculate_sha256(self, filepath: str) -> str:
        """
        Calculate SHA-256 hash of a file.
        
        Args:
            filepath: Path to the file
            
        Returns:
            Hex string of the SHA-256 hash
        """
        sha256_hash = hashlib.sha256()
        try:
            with open(filepath, "rb") as f:
                # Read in chunks to handle large files
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception as e:
            self.logger.error(f"Failed to calculate hash for {filepath}: {e}")
            raise
    
    def generate_checksums(self, directory: str, patterns: Optional[List[str]] = None) -> Dict[str, str]:
        """
        Generate SHA-256 hashes for all model files in a directory.
        
        Args:
            directory: Directory to scan for model files
            patterns: List of file patterns to match (e.g., ['*.json', '*.pkl'])
                     If None, defaults to common model file extensions
            
        Returns:
            Dictionary mapping relative file paths to their SHA-256 hashes
        """
        if patterns is None:
            patterns = ['*.json', '*.pkl', '*.joblib', '*.h5', '*.pt', '*.pth']
        
        checksums = {}
        directory_path = Path(directory)
        
        if not directory_path.exists():
            self.logger.warning(f"Directory does not exist: {directory}")
            return checksums
        
        for pattern in patterns:
            for filepath in directory_path.rglob(pattern):
                if filepath.is_file():
                    # Skip the checksum file itself
                    if filepath.name == self.CHECKSUM_FILE:
                        continue
                    
                    # Use relative path as key
                    relative_path = str(filepath.relative_to(directory_path))
                    try:
                        checksum = self._calculate_sha256(str(filepath))
                        checksums[relative_path] = checksum
                        self.logger.debug(f"Generated checksum for {relative_path}: {checksum[:16]}...")
                    except Exception as e:
                        self.logger.error(f"Failed to process {relative_path}: {e}")
        
        self.logger.info(f"Generated checksums for {len(checksums)} files in {directory}")
        return checksums
    
    def save_checksums(self, directory: str, checksums: Dict[str, str]) -> None:
        """
        Save checksums to a JSON file.
        
        Args:
            directory: Directory where checksum file should be saved
            checksums: Dictionary of file paths to checksums
        """
        checksum_path = Path(directory) / self.checksum_file
        try:
            with open(checksum_path, 'w', encoding='utf-8') as f:
                json.dump(checksums, f, indent=2, sort_keys=True)
            self.logger.info(f"Saved checksums to {checksum_path}")
        except Exception as e:
            self.logger.error(f"Failed to save checksums: {e}")
            raise
    
    def load_checksums(self, directory: str) -> Dict[str, str]:
        """
        Load checksums from a JSON file.
        
        Args:
            directory: Directory where checksum file is located
            
        Returns:
            Dictionary of file paths to checksums, or empty dict if file not found
        """
        checksum_path = Path(directory) / self.checksum_file
        if not checksum_path.exists():
            self.logger.warning(f"Checksum file not found: {checksum_path}")
            return {}
        
        try:
            with open(checksum_path, 'r', encoding='utf-8') as f:
                checksums = json.load(f)
            self.logger.info(f"Loaded {len(checksums)} checksums from {checksum_path}")
            return checksums
        except Exception as e:
            self.logger.error(f"Failed to load checksums: {e}")
            raise
    
    def verify_integrity(self, directory: str, patterns: Optional[List[str]] = None) -> bool:
        """
        Verify model files match stored checksums.
        
        Args:
            directory: Directory to verify
            patterns: List of file patterns to match
            
        Returns:
            True if all files match, False otherwise
            
        Raises:
            IntegrityError: If any file fails integrity check
        """
        stored_checksums = self.load_checksums(directory)
        if not stored_checksums:
            self.logger.warning(f"No stored checksums found for {directory}. Run generate_checksums first.")
            return True  # Don't fail if no checksums exist yet
        
        current_checksums = self.generate_checksums(directory, patterns)
        
        # Check for missing files
        missing_files = set(stored_checksums.keys()) - set(current_checksums.keys())
        if missing_files:
            error_msg = f"Missing files detected: {', '.join(sorted(missing_files))}"
            self.logger.error(error_msg)
            raise IntegrityError(error_msg)
        
        # Check for modified files
        mismatched_files = []
        for filepath, stored_checksum in stored_checksums.items():
            current_checksum = current_checksums.get(filepath)
            if current_checksum != stored_checksum:
                mismatched_files.append(filepath)
                self.logger.error(
                    f"Integrity check failed for {filepath}: "
                    f"expected {stored_checksum[:16]}..., got {current_checksum[:16] if current_checksum else 'None'}..."
                )
        
        if mismatched_files:
            error_msg = f"File integrity check failed for: {', '.join(sorted(mismatched_files))}"
            self.logger.error(error_msg)
            raise IntegrityError(error_msg)
        
        # Check for new files
        new_files = set(current_checksums.keys()) - set(stored_checksums.keys())
        if new_files:
            self.logger.warning(f"New files detected (not in checksum registry): {', '.join(sorted(new_files))}")
        
        self.logger.info(f"Integrity check passed for {len(stored_checksums)} files in {directory}")
        return True
    
    def update_checksums(self, directory: str, patterns: Optional[List[str]] = None) -> None:
        """
        Generate and save new checksums for a directory.
        
        Args:
            directory: Directory to update checksums for
            patterns: List of file patterns to match
        """
        checksums = self.generate_checksums(directory, patterns)
        self.save_checksums(directory, checksums)
        self.logger.info(f"Updated checksums for {directory}")
