"""
One-time migration script to move API credentials from plaintext files to OS keyring.
Securely deletes plaintext files after migration.
"""

import os
import logging
import secrets
from pathlib import Path
from credentials_manager import CredentialsManager

# Number of overwrite passes for secure file deletion
# 3 passes is sufficient for modern storage devices
SECURE_DELETE_PASSES = 3


def secure_delete_file(filepath: str) -> None:
    """
    Securely delete a file by overwriting with random data before deletion.
    
    Args:
        filepath: Path to the file to delete
    """
    if not os.path.exists(filepath):
        return
    
    try:
        # Get file size
        file_size = os.path.getsize(filepath)
        
        # Overwrite with random data (multiple passes)
        for _ in range(SECURE_DELETE_PASSES):
            with open(filepath, 'wb') as f:
                f.write(secrets.token_bytes(file_size))
                f.flush()
                os.fsync(f.fileno())
        
        # Delete the file
        os.remove(filepath)
        print(f"✓ Securely deleted: {filepath}")
    except Exception as e:
        print(f"✗ Error deleting {filepath}: {e}")
        raise


def migrate_credentials(force: bool = False) -> bool:
    """
    Migrate API credentials from plaintext files to OS keyring.
    
    Args:
        force: If True, migrate even if credentials already exist in keyring
        
    Returns:
        True if migration successful, False otherwise
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    print("\n" + "="*60)
    print("PowerTrader2 Credential Migration Script")
    print("="*60 + "\n")
    
    credentials_manager = CredentialsManager()
    
    # Check if credentials already exist in keyring
    if not force and credentials_manager.has_credentials():
        print("✓ Credentials already exist in keyring.")
        print("  Use --force to re-migrate from files.\n")
        return True
    
    # Look for plaintext credential files
    key_file = Path("r_key.txt")
    secret_file = Path("r_secret.txt")
    
    if not key_file.exists() or not secret_file.exists():
        print("✗ Plaintext credential files not found.")
        print(f"  Expected: {key_file.absolute()} and {secret_file.absolute()}")
        print("\n  Please ensure these files exist before running migration.")
        print("  If you're setting up for the first time, use the GUI instead.\n")
        return False
    
    try:
        # Read plaintext files
        print(f"Reading credentials from plaintext files...")
        with open(key_file, 'r', encoding='utf-8') as f:
            api_key = f.read().strip()
        with open(secret_file, 'r', encoding='utf-8') as f:
            api_secret = f.read().strip()
        
        if not api_key or not api_secret:
            print("✗ Credential files are empty.")
            return False
        
        print(f"✓ Read {len(api_key)} chars from {key_file}")
        print(f"✓ Read {len(api_secret)} chars from {secret_file}")
        
        # Store in keyring
        print("\nStoring credentials in OS keyring...")
        credentials_manager.store_api_key(api_key, api_secret)
        print("✓ Credentials stored successfully in keyring")
        
        # Verify stored credentials
        print("\nVerifying stored credentials...")
        retrieved_key, retrieved_secret = credentials_manager.retrieve_api_key()
        if retrieved_key == api_key and retrieved_secret == api_secret:
            print("✓ Verification successful")
        else:
            print("✗ Verification failed - retrieved credentials don't match!")
            return False
        
        # Securely delete plaintext files
        print("\nSecurely deleting plaintext files...")
        secure_delete_file(str(key_file))
        secure_delete_file(str(secret_file))
        
        print("\n" + "="*60)
        print("Migration completed successfully!")
        print("="*60)
        print("\nYour API credentials are now stored securely in the OS keyring.")
        print("The plaintext files have been securely deleted.\n")
        
        logger.info("Credential migration completed successfully")
        return True
        
    except Exception as e:
        print(f"\n✗ Migration failed: {e}")
        logger.error(f"Migration failed: {e}", exc_info=True)
        return False


def main():
    """Main entry point for the migration script."""
    import sys
    
    force = "--force" in sys.argv or "-f" in sys.argv
    
    if "--help" in sys.argv or "-h" in sys.argv:
        print("\nUsage: python migrate_credentials.py [--force]\n")
        print("Options:")
        print("  --force, -f    Force migration even if credentials exist in keyring")
        print("  --help, -h     Show this help message\n")
        return
    
    success = migrate_credentials(force=force)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
