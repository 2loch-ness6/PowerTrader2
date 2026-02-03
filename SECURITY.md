# Security Policy

## Overview

PowerTrader2 takes security seriously. This document outlines our security practices, how to report vulnerabilities, and best practices for users.

## Secure Credential Storage

### API Credentials

PowerTrader2 now supports secure credential storage using your operating system's keyring:

- **macOS**: Credentials are stored in the Keychain
- **Windows**: Credentials are stored in the Windows Credential Manager
- **Linux**: Credentials are stored in the Secret Service (GNOME Keyring, KWallet, etc.)

### Migration from Plaintext Files

If you're upgrading from an older version that used plaintext `r_key.txt` and `r_secret.txt` files:

1. Run the migration script:
   ```bash
   python migrate_credentials.py
   ```

2. The script will:
   - Read your existing credentials
   - Store them securely in the OS keyring
   - Securely overwrite and delete the plaintext files
   - Verify the migration was successful

3. Your credentials are now stored securely and encrypted by your operating system

### Best Practices

- ✅ **DO** use the OS keyring for credential storage (default)
- ✅ **DO** keep your system updated with security patches
- ✅ **DO** use strong passwords for your user account
- ✅ **DO** enable two-factor authentication on your Robinhood account
- ❌ **DON'T** share your API keys with anyone
- ❌ **DON'T** commit credential files to version control
- ❌ **DON'T** store credentials in plaintext (use the migration tool)

## File Integrity Checks

PowerTrader2 uses SHA-256 checksums to verify that model files haven't been tampered with:

- Model file checksums are automatically generated during training
- Files are verified before loading during each startup
- If tampering is detected, the system will refuse to load the affected files

### Rebuilding Checksums

If you need to rebuild checksums after legitimate model updates:

```bash
python pt_trainer.py --rebuild-checksums
```

## Rate Limiting

To prevent API rate limit violations and potential account suspension:

- API calls are automatically rate-limited to 60 calls per minute (configurable)
- HTTP 429 errors trigger exponential backoff
- After multiple failures, trading is automatically paused for 5 minutes

## Safe File Operations

All critical file writes use:

- Atomic write operations to prevent corruption
- File locking to prevent concurrent access
- Proper fsync to ensure data is written to disk
- Platform-specific handling for Windows and POSIX systems

## Reporting Security Vulnerabilities

If you discover a security vulnerability in PowerTrader2:

1. **DO NOT** open a public GitHub issue
2. Email the maintainer privately (see README for contact info)
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if applicable)

We will:
- Acknowledge receipt within 48 hours
- Provide a fix timeline estimate
- Credit you in the release notes (if desired)
- Notify users once a fix is available

## Security Audit Checklist

For users who want to audit the security of their PowerTrader2 installation:

- [ ] API credentials stored in OS keyring (not plaintext files)
- [ ] No `r_key.txt` or `r_secret.txt` files present
- [ ] Model file checksums verified on startup
- [ ] Rate limiting enabled and configured
- [ ] Logs reviewed regularly for suspicious activity
- [ ] System and dependencies kept up to date
- [ ] File permissions properly restricted (user-only access)
- [ ] No credentials in environment variables or shell history

## Secure Development Practices

For contributors:

- All new modules must handle credentials securely
- Never log credentials or API keys
- Use prepared statements for any database queries
- Validate and sanitize all user inputs
- Follow the principle of least privilege
- Review all third-party dependencies for vulnerabilities
- Run security scans before committing (see `gh-advisory-database` tool)

## Third-Party Dependencies

PowerTrader2 uses the following security-related libraries:

- `keyring`: OS-level credential storage
- `cryptography`: Encryption primitives
- `PyNaCl`: Cryptographic signing for Robinhood API
- `filelock`: Safe concurrent file access

We regularly monitor these dependencies for security updates.

## Security Updates

Security updates are released as soon as possible after vulnerabilities are discovered. Users should:

1. Watch the repository for security announcements
2. Update to the latest version immediately when security patches are released
3. Review the CHANGELOG for security-related changes

## Compliance

PowerTrader2 is designed for personal use. Users are responsible for ensuring their use of the software complies with:

- Robinhood's Terms of Service
- Local financial regulations
- Tax reporting requirements
- Data protection laws (if storing sensitive data)

## Disclaimer

**IMPORTANT**: This software places real trades automatically. You are responsible for:
- Everything it does to your money and account
- Keeping your API keys private
- Understanding the security implications of automated trading
- All gains or losses incurred

The maintainers are not responsible for:
- Any losses incurred
- Security breaches to your computer
- Misuse of the software
- Unauthorized access to your accounts

## Contact

For security concerns, contact the maintainer through the methods listed in the README.

---

Last updated: 2026-02-03
